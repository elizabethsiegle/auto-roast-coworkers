import io
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from transcript_parser import parse_transcript

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class DriveClient:
    def __init__(self, service=None, credentials_path: str = None,
                 token_path: str = "drive_token.json"):
        if service is not None:
            self.service = service
        elif credentials_path:
            try:
                self.service = self._build_service(credentials_path, token_path)
            except Exception:
                self.service = None
        else:
            self.service = None

    def _build_service(self, credentials_path: str, token_path: str):
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
        return build('drive', 'v3', credentials=creds)

    def _get_meet_recordings_folder_id(self) -> Optional[str]:
        try:
            results = self.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and name='Meet Recordings' and trashed=false",
                fields="files(id)",
                pageSize=1,
            ).execute()
            files = results.get('files', [])
            return files[0]['id'] if files else None
        except Exception:
            return None

    def _download_file_content(self, file_id: str) -> str:
        request = self.service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue().decode('utf-8', errors='replace')

    def get_meet_transcripts(self, days: int = 30) -> Dict[str, List[str]]:
        if self.service is None:
            return {}
        try:
            folder_id = self._get_meet_recordings_folder_id()
            if not folder_id:
                return {}
            cutoff = (
                datetime.now(timezone.utc) - timedelta(days=days)
            ).strftime('%Y-%m-%dT%H:%M:%SZ')
            query = (
                f"mimeType='text/plain' and '{folder_id}' in parents "
                f"and modifiedTime > '{cutoff}' and trashed=false"
            )
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
            ).execute()
            merged: Dict[str, List[str]] = {}
            for f in results.get('files', []):
                try:
                    content = self._download_file_content(f['id'])
                    parsed = parse_transcript(content, f['name'])
                    for speaker, lines in parsed.items():
                        merged.setdefault(speaker, []).extend(lines)
                except Exception:
                    continue
            return merged
        except Exception:
            return {}
