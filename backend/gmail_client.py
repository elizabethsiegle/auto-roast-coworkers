import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    def __init__(self, service=None, credentials_path: str = None, token_path: str = "token.json"):
        if service is not None:
            self.service = service
        elif credentials_path:
            self.service = self._build_service(credentials_path, token_path)
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
        return build('gmail', 'v1', credentials=creds)

    def get_recent_senders(self, max_results: int = 200) -> list[str]:
        if self.service is None:
            return []
        try:
            results = self.service.users().messages().list(
                userId='me', maxResults=max_results, labelIds=['INBOX']
            ).execute()
            names: set[str] = set()
            for msg in results.get('messages', []):
                try:
                    detail = self.service.users().messages().get(
                        userId='me', id=msg['id'], format='metadata',
                        metadataHeaders=['From']
                    ).execute()
                    for header in detail.get('payload', {}).get('headers', []):
                        if header['name'] == 'From':
                            name = header['value'].split('<')[0].strip().strip('"')
                            if name:
                                names.add(name)
                except Exception:
                    continue
            return list(names)
        except Exception:
            return []

    def get_messages_from_sender(self, name: str, max_results: int = 50) -> list[str]:
        if self.service is None:
            return []
        try:
            results = self.service.users().messages().list(
                userId='me', q=name, maxResults=max_results
            ).execute()
            snippets = []
            for msg in results.get('messages', []):
                try:
                    detail = self.service.users().messages().get(
                        userId='me', id=msg['id'], format='metadata'
                    ).execute()
                    snippet = detail.get('snippet', '')
                    if snippet:
                        snippets.append(snippet)
                except Exception:
                    continue
            return snippets
        except Exception:
            return []
