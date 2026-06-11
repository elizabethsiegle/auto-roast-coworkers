# Drive Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-sync Google Meet transcripts from Drive into the in-memory `transcripts` dict on page load, so roast evidence includes meeting content without any manual upload.

**Architecture:** A new `DriveClient` class (same pattern as `GmailClient`) searches the Drive "Meet Recordings" folder for `.txt` files modified in the last 30 days, downloads each, and runs them through the existing `parse_transcript()`. A new `GET /api/sync-transcripts` FastAPI route merges results into `transcripts`. The frontend fires this endpoint fire-and-forget in the existing `useEffect` on page load.

**Tech Stack:** `google-api-python-client` (already installed, includes Drive v3), `googleapiclient.http.MediaIoBaseDownload` for file download, Python `io.BytesIO`, React `useEffect`

---

## File Map

**Backend (`backend/`)**
- `drive_client.py` — New. `DriveClient` with `drive.readonly` scope, `get_meet_transcripts(days)` method, `_download_file_content(file_id)` helper (extracted for testability)
- `main.py` — Add `from drive_client import DriveClient`, module-level `drive` instance, `GET /api/sync-transcripts` route
- `tests/test_drive_client.py` — New. 4 tests using injected mock service
- `tests/test_main.py` — Update fixture to mock `main.drive`; add 1 new test; update 3 existing tests from 4-tuple to 5-tuple destructuring

**Frontend (`frontend/src/`)**
- `api.js` — Add `syncTranscripts()` export
- `App.jsx` — Import `syncTranscripts`; call fire-and-forget in `useEffect`

---

## Task 1: DriveClient

**Files:**
- Create: `backend/drive_client.py`
- Create: `backend/tests/test_drive_client.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_drive_client.py`:
```python
from unittest.mock import MagicMock, patch
from drive_client import DriveClient


def test_no_crash_with_empty_credentials_path():
    client = DriveClient(credentials_path="")
    assert client.service is None


def test_get_meet_transcripts_returns_empty_when_service_is_none():
    client = DriveClient(credentials_path="")
    assert client.get_meet_transcripts() == {}


def test_get_meet_transcripts_returns_empty_when_folder_not_found():
    svc = MagicMock()
    svc.files().list().execute.return_value = {"files": []}
    client = DriveClient(service=svc)
    assert client.get_meet_transcripts() == {}


def test_get_meet_transcripts_parses_transcript_files():
    svc = MagicMock()
    svc.files().list().execute.side_effect = [
        {"files": [{"id": "folder-123"}]},
        {"files": [{"id": "file-456", "name": "transcript.txt"}]},
    ]
    client = DriveClient(service=svc)
    transcript_text = "John Smith: Let's circle back on this\nJane Doe: Per my last email"
    with patch.object(client, '_download_file_content', return_value=transcript_text):
        result = client.get_meet_transcripts()
    assert "John Smith" in result
    assert "Jane Doe" in result
    assert result["John Smith"] == ["Let's circle back on this"]
    assert result["Jane Doe"] == ["Per my last email"]
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd /path/to/roast-coworkers/backend && source .venv/bin/activate && pytest tests/test_drive_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'drive_client'`

- [ ] **Step 3: Implement drive_client.py**

Create `backend/drive_client.py`:
```python
import io
import os
from datetime import datetime, timedelta, timezone

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

    def _get_meet_recordings_folder_id(self) -> str | None:
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

    def get_meet_transcripts(self, days: int = 30) -> dict[str, list[str]]:
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
            merged: dict[str, list[str]] = {}
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
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest tests/test_drive_client.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Run full test suite — confirm nothing broken**

```bash
pytest tests/ -v
```

Expected: All 21 existing tests + 4 new = 25 pass.

- [ ] **Step 6: Commit**

```bash
git add backend/drive_client.py backend/tests/test_drive_client.py
git commit -m "feat: DriveClient — search Meet Recordings folder, download and parse transcripts"
```

---

## Task 2: FastAPI sync-transcripts route

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/tests/test_main.py`

- [ ] **Step 1: Write failing test**

Replace the entire `backend/tests/test_main.py` with the version below. Changes: fixture adds `mock_drive`, yields a 5-tuple; three existing tests updated to 5-tuple destructuring; one new test added.

```python
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    import main

    mock_slack = MagicMock()
    mock_gmail = MagicMock()
    mock_roast = MagicMock()
    mock_drive = MagicMock()

    monkeypatch.setattr(main, 'slack', mock_slack)
    monkeypatch.setattr(main, 'gmail', mock_gmail)
    monkeypatch.setattr(main, 'roast_gen', mock_roast)
    monkeypatch.setattr(main, 'drive', mock_drive)
    monkeypatch.setattr(main, 'transcripts', {})

    mock_slack.get_workspace_members.return_value = ["Jane Doe", "John Smith"]
    mock_slack.get_messages_by_user.return_value = ["Let's sync up", "Circle back on this"]
    mock_gmail.get_messages_from_sender.return_value = ["As per my email"]
    mock_drive.get_meet_transcripts.return_value = {}
    mock_roast.generate.return_value = {
        "title": "The Complete Dossier on John Smith",
        "sections": [{"heading": "Meeting Behavior", "content": "John invented syncing up."}]
    }

    with TestClient(main.app) as c:
        yield c, mock_slack, mock_gmail, mock_roast, mock_drive


def test_get_coworkers_returns_sorted_members(client):
    c, _, _, _, _ = client
    response = c.get("/api/coworkers")
    assert response.status_code == 200
    assert response.json()["coworkers"] == ["Jane Doe", "John Smith"]


def test_post_roast_calls_all_sources_and_returns_report(client):
    c, mock_slack, mock_gmail, mock_roast, _ = client
    response = c.post("/api/roast", json={"name": "John Smith"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Complete Dossier on John Smith"
    mock_slack.get_messages_by_user.assert_called_once_with("John Smith")
    mock_gmail.get_messages_from_sender.assert_called_once_with("John Smith")


def test_upload_transcript_stores_speaker_lines(client):
    c, _, _, _, _ = client
    vtt = b"""WEBVTT

00:00:01.000 --> 00:00:05.000
John Smith: Let's take this offline and circle back"""

    response = c.post(
        "/api/upload-transcript",
        data={"name": "John Smith"},
        files={"file": ("meeting.vtt", vtt, "text/vtt")}
    )
    assert response.status_code == 200
    assert response.json()["lines_added"] == 1


def test_sync_transcripts_merges_speaker_lines(client):
    c, _, _, _, mock_drive = client
    mock_drive.get_meet_transcripts.return_value = {
        "John Smith": ["Let's circle back on this", "Sounds like a plan"],
    }
    response = c.get("/api/sync-transcripts")
    assert response.status_code == 200
    data = response.json()
    assert data["speakers_found"] == 1
    assert data["lines_added"] == 2
    mock_drive.get_meet_transcripts.assert_called_once_with(days=30)
```

- [ ] **Step 2: Run tests — confirm new test fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_main.py::test_sync_transcripts_merges_speaker_lines -v
```

Expected: `AttributeError` — `main` has no attribute `drive`

- [ ] **Step 3: Update main.py**

Add the import and instance after the existing imports/instances, and add the new route. The full updated `backend/main.py`:

```python
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from slack_client import SlackClient
from gmail_client import GmailClient
from drive_client import DriveClient
from roast_generator import RoastGenerator
from transcript_parser import parse_transcript

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

slack = SlackClient(os.getenv("SLACK_TOKEN", ""))
gmail = GmailClient(credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", ""))
drive = DriveClient(credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", ""),
                    token_path="drive_token.json")
roast_gen = RoastGenerator(os.getenv("ANTHROPIC_API_KEY", ""))

transcripts: dict[str, list[str]] = {}


class RoastRequest(BaseModel):
    name: str


@app.get("/api/coworkers")
async def get_coworkers():
    members = set(slack.get_workspace_members())
    members.update(gmail.get_recent_senders())
    return {"coworkers": sorted(members)}


@app.post("/api/roast")
async def roast(request: RoastRequest):
    evidence: list[str] = []
    evidence.extend(slack.get_messages_by_user(request.name))
    evidence.extend(gmail.get_messages_from_sender(request.name))
    evidence.extend(transcripts.get(request.name, []))
    try:
        return roast_gen.generate(request.name, evidence)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/upload-transcript")
async def upload_transcript(name: str = Form(...), file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode()
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    lines_by_speaker = parse_transcript(text, file.filename)
    lines = lines_by_speaker.get(name, [])
    transcripts.setdefault(name, []).extend(lines)
    return {"status": "ok", "lines_added": len(lines)}


@app.get("/api/sync-transcripts")
async def sync_transcripts():
    result = drive.get_meet_transcripts(days=30)
    total = 0
    for speaker, lines in result.items():
        transcripts.setdefault(speaker, []).extend(lines)
        total += len(lines)
    return {"status": "ok", "speakers_found": len(result), "lines_added": total}
```

- [ ] **Step 4: Run tests — confirm all pass**

```bash
pytest tests/ -v
```

Expected: 26 tests pass (25 from Task 1 + 1 new).

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_main.py
git commit -m "feat: GET /api/sync-transcripts — auto-populate transcripts from Drive on page load"
```

---

## Task 3: Frontend — fire-and-forget sync on page load

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Add syncTranscripts to api.js**

Add this function to the end of `frontend/src/api.js`:

```js
export async function syncTranscripts() {
  await fetch('/api/sync-transcripts')
}
```

- [ ] **Step 2: Update App.jsx useEffect**

In `frontend/src/App.jsx`, change line 4 to add the import:
```jsx
import { fetchCoworkers, fetchRoast, uploadTranscript, syncTranscripts } from './api'
```

Replace the `useEffect` (lines 13–17) with:
```jsx
useEffect(() => {
  syncTranscripts()
  fetchCoworkers()
    .then(setCoworkers)
    .catch(() => setError('Failed to load coworkers — is the backend running?'))
}, [])
```

`syncTranscripts()` is intentionally not awaited — the transcript enrichment happens in the background and the coworker list loads independently.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.js frontend/src/App.jsx
git commit -m "feat: fire-and-forget Drive transcript sync on page load"
```

---

## Task 4: First-run OAuth note

On first run after this change, the backend will open **two** browser OAuth popups — one for Gmail (`token.json`) and one for Drive (`drive_token.json`). Both use the same `credentials.json`.

If you already have a `token.json` from the Gmail OAuth, you only need to complete the Drive popup. The Gmail token is unaffected.

- [ ] **Step 1: Verify Drive OAuth scope is added to Google Cloud Console**

In Google Cloud Console → **APIs & Services** → **Credentials** → your OAuth client → confirm `drive.readonly` scope is added to the consent screen. If not:

1. Go to **APIs & Services** → **OAuth consent screen** → **Edit App**
2. Under **Scopes** → **Add or Remove Scopes** → search "Drive" → add `.../auth/drive.readonly`
3. Save

- [ ] **Step 2: Start the backend and complete Drive OAuth**

```bash
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```

A browser tab opens for Drive authorization. Approve it. `drive_token.json` is created. The backend finishes loading.

- [ ] **Step 3: Verify sync works**

With the frontend running (`cd frontend && npm run dev`), open `http://localhost:5173`. In the backend terminal you should see no errors. Call the endpoint directly to confirm:

```bash
curl http://localhost:8000/api/sync-transcripts
```

Expected: `{"status":"ok","speakers_found":<N>,"lines_added":<N>}` — N will be 0 if no Meet transcripts exist in Drive from the last 30 days, which is fine.
