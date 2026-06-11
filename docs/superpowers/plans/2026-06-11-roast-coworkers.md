# Roast Coworkers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web app that ingests your own Slack, Gmail, and meeting transcript data, then uses Claude to generate funny satirical roast reports about the coworkers who appear in it.

**Architecture:** FastAPI backend handles Slack/Gmail API calls and Claude roast generation; React (Vite) frontend displays a coworker sidebar and roast report panel; Express serves the production build and proxies `/api/*` to FastAPI.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, slack-sdk, google-api-python-client, google-auth-oauthlib, anthropic, React 18, Vite, Express 4, http-proxy-middleware

---

## File Map

**Backend (`backend/`)**
- `main.py` — FastAPI app, CORS, route definitions, module-level client instances
- `slack_client.py` — Slack Web API: list workspace members, search messages by username
- `gmail_client.py` — Gmail API: OAuth flow + token refresh, list senders, fetch snippets
- `transcript_parser.py` — Parse `.vtt` / `.txt` meeting files into `{speaker: [lines]}`
- `roast_generator.py` — Assemble evidence dossier, call Claude, return structured JSON report
- `requirements.txt`
- `.env.example`
- `tests/__init__.py`
- `tests/conftest.py` — Set env vars to empty strings so main.py imports without crashing
- `tests/test_transcript_parser.py`
- `tests/test_slack_client.py`
- `tests/test_gmail_client.py`
- `tests/test_roast_generator.py`
- `tests/test_main.py`

**Frontend (`frontend/`)**
- `package.json`
- `vite.config.js` — proxy `/api` → `http://localhost:8000`
- `index.html`
- `src/main.jsx` — React entry point
- `src/App.jsx` — Root: fetches coworkers, manages selected/report/loading state
- `src/api.js` — Fetch wrappers for all three backend endpoints
- `src/index.css` — Global dark-theme styles
- `src/components/Sidebar.jsx` — Scrollable coworker list
- `src/components/RoastPanel.jsx` — Report display, spinner, upload zone

**Production server (`server/`)**
- `package.json`
- `index.js` — Express: serves `frontend/dist/`, proxies `/api/*` to FastAPI

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/tests/__init__.py`
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/vite.config.js`
- Create: `server/package.json`

- [ ] **Step 1: Create backend directory and requirements.txt**

```bash
mkdir -p backend/tests
```

Create `backend/requirements.txt`:
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
pydantic==2.7.1
slack-sdk==3.27.2
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.128.0
anthropic==0.28.0
python-multipart==0.0.9
pytest==8.2.0
httpx==0.27.0
```

- [ ] **Step 2: Install backend dependencies**

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 3: Create .env.example and tests/__init__.py**

Create `backend/.env.example`:
```
SLACK_TOKEN=xoxp-your-slack-user-token-here
GOOGLE_CREDENTIALS_PATH=credentials.json
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Copy it: `cp backend/.env.example backend/.env` — fill in real values.

Create `backend/tests/__init__.py` (empty).

- [ ] **Step 4: Scaffold React frontend with Vite**

```bash
npm create vite@latest frontend -- --template react && cd frontend && npm install
```

Expected: `frontend/src/App.jsx`, `frontend/index.html`, etc. exist.

- [ ] **Step 5: Configure Vite proxy**

Replace `frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

- [ ] **Step 6: Set up Express production server**

```bash
mkdir server && cd server && npm init -y && npm install express http-proxy-middleware
```

- [ ] **Step 7: Commit scaffold**

```bash
git add backend/ frontend/ server/
git commit -m "chore: project scaffolding — backend, frontend, server"
```

---

## Task 2: Transcript Parser

**Files:**
- Create: `backend/transcript_parser.py`
- Create: `backend/tests/test_transcript_parser.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_transcript_parser.py`:
```python
from transcript_parser import parse_transcript


def test_parse_vtt_extracts_speaker_lines():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:05.000
John Smith: This is a great idea, we should schedule a follow-up

00:00:06.000 --> 00:00:10.000
Jane Doe: Per my last email, I already covered this

00:00:11.000 --> 00:00:15.000
John Smith: Sure but let's circle back offline"""

    result = parse_transcript(vtt, "meeting.vtt")

    assert "John Smith" in result
    assert len(result["John Smith"]) == 2
    assert "This is a great idea" in result["John Smith"][0]
    assert "Jane Doe" in result
    assert "Per my last email" in result["Jane Doe"][0]


def test_parse_txt_extracts_speaker_lines():
    txt = """John Smith: This is a great idea
Jane Doe: Per my last email, I already covered this
John Smith: Sure but let's circle back offline"""

    result = parse_transcript(txt, "meeting.txt")

    assert "John Smith" in result
    assert len(result["John Smith"]) == 2
    assert "Jane Doe" in result


def test_vtt_ignores_non_speaker_lines():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:05.000
Some line without a speaker prefix

00:00:06.000 --> 00:00:10.000
Jane Doe: This should be captured"""

    result = parse_transcript(vtt, "meeting.vtt")

    assert "Jane Doe" in result
    assert len(result) == 1


def test_empty_content_returns_empty_dict():
    assert parse_transcript("", "meeting.vtt") == {}


def test_preserves_punctuation_in_speaker_lines():
    txt = "John Smith: What's the ROI on this, Karen? It's... complicated."
    result = parse_transcript(txt, "notes.txt")
    assert result["John Smith"][0] == "What's the ROI on this, Karen? It's... complicated."
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_transcript_parser.py -v
```

Expected: `ModuleNotFoundError: No module named 'transcript_parser'`

- [ ] **Step 3: Implement transcript_parser.py**

Create `backend/transcript_parser.py`:
```python
import re

_TIMESTAMP_RE = re.compile(r'^\d{2}:\d{2}:\d{2}')
_SPEAKER_RE = re.compile(r'^([A-Za-z][^:]{1,50}):\s+(.+)$')


def parse_transcript(content: str, filename: str) -> dict[str, list[str]]:
    """Parse .vtt or .txt transcript. Returns {speaker_name: [spoken_lines]}."""
    result: dict[str, list[str]] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('WEBVTT') or _TIMESTAMP_RE.match(line):
            continue
        match = _SPEAKER_RE.match(line)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            result.setdefault(speaker, []).append(text)
    return result
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest tests/test_transcript_parser.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/transcript_parser.py backend/tests/test_transcript_parser.py
git commit -m "feat: transcript parser for .vtt and .txt meeting files"
```

---

## Task 3: Slack Client

**Files:**
- Create: `backend/slack_client.py`
- Create: `backend/tests/test_slack_client.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_slack_client.py`:
```python
from unittest.mock import patch
from slack_client import SlackClient


@patch('slack_client.WebClient')
def test_get_workspace_members_excludes_bots_and_deleted(MockWebClient):
    MockWebClient.return_value.users_list.return_value = {
        "members": [
            {"id": "U1", "is_bot": False, "deleted": False,
             "profile": {"display_name": "John Smith"}, "real_name": "John Smith"},
            {"id": "USLACKBOT", "is_bot": True, "deleted": False,
             "profile": {"display_name": "Slackbot"}, "real_name": "Slackbot"},
            {"id": "U2", "is_bot": False, "deleted": True,
             "profile": {"display_name": "Gone User"}, "real_name": "Gone User"},
            {"id": "U3", "is_bot": False, "deleted": False,
             "profile": {"display_name": "Jane Doe"}, "real_name": "Jane Doe"},
        ]
    }
    client = SlackClient("xoxp-fake")
    result = client.get_workspace_members()
    assert "John Smith" in result
    assert "Jane Doe" in result
    assert "Slackbot" not in result
    assert "Gone User" not in result


@patch('slack_client.WebClient')
def test_get_workspace_members_falls_back_to_real_name_when_display_name_empty(MockWebClient):
    MockWebClient.return_value.users_list.return_value = {
        "members": [
            {"id": "U1", "is_bot": False, "deleted": False,
             "profile": {"display_name": ""}, "real_name": "Jane No Display"},
        ]
    }
    client = SlackClient("xoxp-fake")
    result = client.get_workspace_members()
    assert "Jane No Display" in result


@patch('slack_client.WebClient')
def test_get_messages_by_user_returns_message_texts(MockWebClient):
    MockWebClient.return_value.search_messages.return_value = {
        "messages": {
            "matches": [
                {"text": "Let's circle back on this"},
                {"text": "Per my last email..."},
            ]
        }
    }
    client = SlackClient("xoxp-fake")
    result = client.get_messages_by_user("John Smith")
    assert "Let's circle back on this" in result
    assert "Per my last email..." in result
    MockWebClient.return_value.search_messages.assert_called_once_with(
        query="from:John Smith", count=100
    )


@patch('slack_client.WebClient')
def test_get_messages_by_user_returns_empty_list_when_no_matches(MockWebClient):
    MockWebClient.return_value.search_messages.return_value = {"messages": {"matches": []}}
    client = SlackClient("xoxp-fake")
    assert client.get_messages_by_user("Ghost") == []
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest tests/test_slack_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'slack_client'`

- [ ] **Step 3: Implement slack_client.py**

Create `backend/slack_client.py`:
```python
from slack_sdk import WebClient


class SlackClient:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def get_workspace_members(self) -> list[str]:
        response = self.client.users_list()
        return [
            user["profile"]["display_name"] or user["real_name"]
            for user in response["members"]
            if not user["is_bot"]
            and not user["deleted"]
            and user["id"] != "USLACKBOT"
        ]

    def get_messages_by_user(self, username: str, limit: int = 100) -> list[str]:
        response = self.client.search_messages(query=f"from:{username}", count=limit)
        matches = response.get("messages", {}).get("matches", [])
        return [match["text"] for match in matches]
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest tests/test_slack_client.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/slack_client.py backend/tests/test_slack_client.py
git commit -m "feat: Slack client — list workspace members, search messages by username"
```

---

## Task 4: Gmail Client

**Files:**
- Create: `backend/gmail_client.py`
- Create: `backend/tests/test_gmail_client.py`

`GmailClient` accepts an injected `service` for testability and guards against empty `credentials_path` so `main.py` can import cleanly in tests.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_gmail_client.py`:
```python
from unittest.mock import MagicMock, call
from gmail_client import GmailClient


def _mock_message(msg_id: str, from_header: str, snippet: str) -> dict:
    return {
        "id": msg_id,
        "snippet": snippet,
        "payload": {"headers": [{"name": "From", "value": from_header}]},
    }


def test_get_recent_senders_extracts_names():
    svc = MagicMock()
    svc.users().messages().list().execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}]
    }
    svc.users().messages().get().execute.side_effect = [
        _mock_message("1", "John Smith <john@example.com>", "s1"),
        _mock_message("2", "Jane Doe <jane@example.com>", "s2"),
    ]
    client = GmailClient(service=svc)
    result = client.get_recent_senders()
    assert "John Smith" in result
    assert "Jane Doe" in result


def test_get_recent_senders_deduplicates():
    svc = MagicMock()
    svc.users().messages().list().execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}]
    }
    svc.users().messages().get().execute.side_effect = [
        _mock_message("1", "John Smith <john@example.com>", "m1"),
        _mock_message("2", "John Smith <john@example.com>", "m2"),
    ]
    client = GmailClient(service=svc)
    result = client.get_recent_senders()
    assert result.count("John Smith") == 1


def test_get_messages_from_sender_returns_snippets():
    svc = MagicMock()
    svc.users().messages().list().execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}]
    }
    svc.users().messages().get().execute.side_effect = [
        _mock_message("1", "John Smith <j@e.com>", "As per my previous email"),
        _mock_message("2", "John Smith <j@e.com>", "Circling back on this"),
    ]
    client = GmailClient(service=svc)
    result = client.get_messages_from_sender("John Smith")
    assert "As per my previous email" in result
    assert "Circling back on this" in result


def test_get_messages_from_sender_returns_empty_when_no_messages():
    svc = MagicMock()
    svc.users().messages().list().execute.return_value = {}
    client = GmailClient(service=svc)
    assert client.get_messages_from_sender("Ghost") == []


def test_no_crash_with_empty_credentials_path():
    client = GmailClient(credentials_path="")
    assert client.service is None
    assert client.get_recent_senders() == []
    assert client.get_messages_from_sender("anyone") == []
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest tests/test_gmail_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'gmail_client'`

- [ ] **Step 3: Implement gmail_client.py**

Create `backend/gmail_client.py`:
```python
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
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results, labelIds=['INBOX']
        ).execute()
        names: set[str] = set()
        for msg in results.get('messages', []):
            detail = self.service.users().messages().get(
                userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['From']
            ).execute()
            for header in detail.get('payload', {}).get('headers', []):
                if header['name'] == 'From':
                    name = header['value'].split('<')[0].strip().strip('"')
                    if name:
                        names.add(name)
        return list(names)

    def get_messages_from_sender(self, name: str, max_results: int = 50) -> list[str]:
        if self.service is None:
            return []
        results = self.service.users().messages().list(
            userId='me', q=name, maxResults=max_results
        ).execute()
        snippets = []
        for msg in results.get('messages', []):
            detail = self.service.users().messages().get(
                userId='me', id=msg['id'], format='metadata'
            ).execute()
            snippet = detail.get('snippet', '')
            if snippet:
                snippets.append(snippet)
        return snippets
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest tests/test_gmail_client.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/gmail_client.py backend/tests/test_gmail_client.py
git commit -m "feat: Gmail client — OAuth flow, list senders, fetch message snippets"
```

---

## Task 5: Roast Generator

**Files:**
- Create: `backend/roast_generator.py`
- Create: `backend/tests/test_roast_generator.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_roast_generator.py`:
```python
import json
from unittest.mock import MagicMock, patch
from roast_generator import RoastGenerator


def _mock_anthropic(MockAnthropic, response_text: str):
    mock_client = MockAnthropic.return_value
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return mock_client


@patch('roast_generator.anthropic.Anthropic')
def test_generate_returns_parsed_report(MockAnthropic):
    report = {
        "title": "The Complete Dossier on John Smith",
        "sections": [
            {"heading": "Meeting Behavior", "content": "John invented the phrase 'circle back.'"},
            {"heading": "Email Persona", "content": "His emails arrive in clusters of three."},
            {"heading": "Slack Presence", "content": "Online at all hours. Never responds."},
            {"heading": "Final Verdict", "content": "John is what happens when a calendar invite gains sentience."},
        ]
    }
    _mock_anthropic(MockAnthropic, json.dumps(report))
    gen = RoastGenerator("sk-fake")
    result = gen.generate("John Smith", ["let's sync", "circle back"])
    assert result["title"] == "The Complete Dossier on John Smith"
    assert len(result["sections"]) == 4
    assert result["sections"][0]["heading"] == "Meeting Behavior"


@patch('roast_generator.anthropic.Anthropic')
def test_generate_caps_evidence_at_50(MockAnthropic):
    _mock_anthropic(MockAnthropic, '{"title": "T", "sections": []}')
    gen = RoastGenerator("sk-fake")
    evidence = [f"message {i}" for i in range(100)]
    gen.generate("John", evidence)
    call_kwargs = MockAnthropic.return_value.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert user_content.count("- message ") == 50


@patch('roast_generator.anthropic.Anthropic')
def test_generate_uses_correct_model(MockAnthropic):
    _mock_anthropic(MockAnthropic, '{"title": "T", "sections": []}')
    gen = RoastGenerator("sk-fake")
    gen.generate("John", ["evidence"])
    call_kwargs = MockAnthropic.return_value.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6"
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
pytest tests/test_roast_generator.py -v
```

Expected: `ModuleNotFoundError: No module named 'roast_generator'`

- [ ] **Step 3: Implement roast_generator.py**

Create `backend/roast_generator.py`:
```python
import json
import anthropic

SYSTEM_PROMPT = (
    "You are a sharp comedy writer at a work roast event. "
    "Write a funny, satirical roast report about a coworker based on their actual communications.\n\n"
    "Rules:\n"
    "- Be satirical and punchy — like a roast, not a performance review\n"
    "- Ground every joke in actual evidence from the data provided\n"
    "- Each section is 2-3 sentences with a killer one-liner\n"
    "- Focus on patterns: catchphrases, response times, meeting habits, email quirks\n"
    "- Never be cruel or target personal characteristics — only work behavior\n\n"
    "Return ONLY valid JSON with no markdown fencing:\n"
    '{"title": "The Complete Dossier on [Name]", '
    '"sections": ['
    '{"heading": "Meeting Behavior", "content": "..."}, '
    '{"heading": "Email Persona", "content": "..."}, '
    '{"heading": "Slack Presence", "content": "..."}, '
    '{"heading": "Final Verdict", "content": "..."}'
    ']}'
)


class RoastGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, name: str, evidence: list[str]) -> dict:
        capped = evidence[:50]
        evidence_text = "\n".join(f"- {e}" for e in capped)
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Generate a roast report for {name}.\n\n"
                    f"Evidence from their communications:\n{evidence_text}"
                )
            }]
        )
        return json.loads(message.content[0].text)
```

- [ ] **Step 4: Run tests — confirm they pass**

```bash
pytest tests/test_roast_generator.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/roast_generator.py backend/tests/test_roast_generator.py
git commit -m "feat: roast generator — Claude-powered satirical report builder"
```

---

## Task 6: FastAPI Routes

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/main.py`
- Create: `backend/tests/test_main.py`

- [ ] **Step 1: Create conftest.py**

Create `backend/tests/conftest.py`:
```python
import os

os.environ.setdefault("SLACK_TOKEN", "")
os.environ.setdefault("GOOGLE_CREDENTIALS_PATH", "")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
```

- [ ] **Step 2: Write failing tests**

Create `backend/tests/test_main.py`:
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

    monkeypatch.setattr(main, 'slack', mock_slack)
    monkeypatch.setattr(main, 'gmail', mock_gmail)
    monkeypatch.setattr(main, 'roast_gen', mock_roast)
    monkeypatch.setattr(main, 'transcripts', {})

    mock_slack.get_workspace_members.return_value = ["Jane Doe", "John Smith"]
    mock_slack.get_messages_by_user.return_value = ["Let's sync up", "Circle back on this"]
    mock_gmail.get_messages_from_sender.return_value = ["As per my email"]
    mock_roast.generate.return_value = {
        "title": "The Complete Dossier on John Smith",
        "sections": [{"heading": "Meeting Behavior", "content": "John invented syncing up."}]
    }

    with TestClient(main.app) as c:
        yield c, mock_slack, mock_gmail, mock_roast


def test_get_coworkers_returns_sorted_members(client):
    c, _, _, _ = client
    response = c.get("/api/coworkers")
    assert response.status_code == 200
    assert response.json()["coworkers"] == ["Jane Doe", "John Smith"]


def test_post_roast_calls_all_sources_and_returns_report(client):
    c, mock_slack, mock_gmail, mock_roast = client
    response = c.post("/api/roast", json={"name": "John Smith"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Complete Dossier on John Smith"
    mock_slack.get_messages_by_user.assert_called_once_with("John Smith")
    mock_gmail.get_messages_from_sender.assert_called_once_with("John Smith")


def test_upload_transcript_stores_speaker_lines(client):
    c, _, _, _ = client
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
```

- [ ] **Step 3: Run tests — confirm they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 4: Implement main.py**

Create `backend/main.py`:
```python
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from slack_client import SlackClient
from gmail_client import GmailClient
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
roast_gen = RoastGenerator(os.getenv("ANTHROPIC_API_KEY", ""))

transcripts: dict[str, list[str]] = {}


class RoastRequest(BaseModel):
    name: str


@app.get("/api/coworkers")
async def get_coworkers():
    return {"coworkers": sorted(slack.get_workspace_members())}


@app.post("/api/roast")
async def roast(request: RoastRequest):
    evidence: list[str] = []
    evidence.extend(slack.get_messages_by_user(request.name))
    evidence.extend(gmail.get_messages_from_sender(request.name))
    evidence.extend(transcripts.get(request.name, []))
    return roast_gen.generate(request.name, evidence)


@app.post("/api/upload-transcript")
async def upload_transcript(name: str = Form(...), file: UploadFile = File(...)):
    content = await file.read()
    lines_by_speaker = parse_transcript(content.decode(), file.filename)
    lines = lines_by_speaker.get(name, [])
    transcripts.setdefault(name, []).extend(lines)
    return {"status": "ok", "lines_added": len(lines)}
```

- [ ] **Step 5: Run tests — confirm they pass**

```bash
pytest tests/test_main.py -v
```

Expected: 3 tests pass.

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All 20 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/tests/conftest.py backend/tests/test_main.py
git commit -m "feat: FastAPI routes — /api/coworkers, /api/roast, /api/upload-transcript"
```

---

## Task 7: React App Scaffold + api.js

**Files:**
- Modify: `frontend/src/main.jsx`
- Create: `frontend/src/api.js`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Replace main.jsx**

Replace `frontend/src/main.jsx`:
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 2: Create api.js**

Create `frontend/src/api.js`:
```js
export async function fetchCoworkers() {
  const res = await fetch('/api/coworkers')
  if (!res.ok) throw new Error('Failed to fetch coworkers')
  const data = await res.json()
  return data.coworkers
}

export async function fetchRoast(name) {
  const res = await fetch('/api/roast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to generate roast')
  return res.json()
}

export async function uploadTranscript(name, file) {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('file', file)
  const res = await fetch('/api/upload-transcript', {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error('Failed to upload transcript')
  return res.json()
}
```

- [ ] **Step 3: Write App.jsx**

Replace `frontend/src/App.jsx`:
```jsx
import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import RoastPanel from './components/RoastPanel'
import { fetchCoworkers, fetchRoast, uploadTranscript } from './api'

export default function App() {
  const [coworkers, setCoworkers] = useState([])
  const [selected, setSelected] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchCoworkers()
      .then(setCoworkers)
      .catch(() => setError('Failed to load coworkers — is the backend running?'))
  }, [])

  async function handleSelect(name) {
    setSelected(name)
    setReport(null)
    setError(null)
    setLoading(true)
    try {
      const result = await fetchRoast(name)
      setReport(result)
    } catch {
      setError('Failed to generate roast. Check the backend logs.')
    } finally {
      setLoading(false)
    }
  }

  async function handleUpload(file) {
    if (!selected) return
    try {
      await uploadTranscript(selected, file)
    } catch {
      setError('Failed to upload transcript.')
    }
  }

  return (
    <div className="app">
      <Sidebar coworkers={coworkers} selected={selected} onSelect={handleSelect} />
      <RoastPanel
        selected={selected}
        report={report}
        loading={loading}
        error={error}
        onUpload={handleUpload}
      />
    </div>
  )
}
```

- [ ] **Step 4: Write index.css**

Replace `frontend/src/index.css`:
```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #0f0f0f;
  color: #e8e8e8;
  height: 100vh;
  overflow: hidden;
}

.app {
  display: flex;
  height: 100vh;
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: React app scaffold, api.js, global dark styles"
```

---

## Task 8: Sidebar Component

**Files:**
- Create: `frontend/src/components/Sidebar.jsx`

- [ ] **Step 1: Create components directory and Sidebar.jsx**

```bash
mkdir -p frontend/src/components
```

Create `frontend/src/components/Sidebar.jsx`:
```jsx
export default function Sidebar({ coworkers, selected, onSelect }) {
  return (
    <aside style={{
      width: '240px',
      minWidth: '240px',
      background: '#1a1a1a',
      borderRight: '1px solid #2a2a2a',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '20px 16px 12px',
        fontSize: '11px',
        fontWeight: '600',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: '#555',
      }}>
        Your Coworkers
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {coworkers.length === 0 && (
          <div style={{ padding: '12px 16px', color: '#444', fontSize: '13px' }}>
            Loading...
          </div>
        )}
        {coworkers.map(name => (
          <button
            key={name}
            onClick={() => onSelect(name)}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '10px 16px',
              background: selected === name ? '#252525' : 'transparent',
              color: selected === name ? '#fff' : '#aaa',
              border: 'none',
              borderLeft: selected === name ? '3px solid #e63946' : '3px solid transparent',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'all 0.1s',
            }}
          >
            {name}
          </button>
        ))}
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Start the dev server and verify the sidebar renders**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173`. Sidebar should show "Loading..." with no JS console errors. (Backend does not need to be running for this check.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Sidebar.jsx
git commit -m "feat: Sidebar component — coworker list with selection highlight"
```

---

## Task 9: RoastPanel Component

**Files:**
- Create: `frontend/src/components/RoastPanel.jsx`

- [ ] **Step 1: Create RoastPanel.jsx**

Create `frontend/src/components/RoastPanel.jsx`:
```jsx
import { useRef } from 'react'

export default function RoastPanel({ selected, report, loading, error, onUpload }) {
  const fileInputRef = useRef(null)

  function handleDrop(e) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) onUpload(file)
  }

  return (
    <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
        {!selected && <EmptyState />}
        {selected && loading && <Spinner name={selected} />}
        {selected && error && <ErrorMessage message={error} />}
        {selected && report && !loading && <Report report={report} />}
      </div>

      {selected && (
        <UploadZone
          selectedName={selected}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".vtt,.txt"
            style={{ display: 'none' }}
            onChange={e => { const f = e.target.files[0]; if (f) onUpload(f) }}
          />
        </UploadZone>
      )}
    </main>
  )
}

function EmptyState() {
  return (
    <div style={{ color: '#444', fontSize: '15px', marginTop: '80px', textAlign: 'center' }}>
      Select a coworker to generate their roast report.
    </div>
  )
}

function Spinner({ name }) {
  return (
    <div style={{ textAlign: 'center', marginTop: '80px' }}>
      <div style={{ fontSize: '32px', marginBottom: '16px' }}>⚙️</div>
      <div style={{ color: '#777', fontSize: '14px' }}>Digging up dirt on {name}...</div>
    </div>
  )
}

function ErrorMessage({ message }) {
  return (
    <div style={{
      background: '#1e0a0a',
      border: '1px solid #4a1a1a',
      borderRadius: '8px',
      padding: '16px',
      color: '#ff6b6b',
      fontSize: '14px',
      marginTop: '40px',
    }}>
      {message}
    </div>
  )
}

function Report({ report }) {
  return (
    <div>
      <h1 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '32px', color: '#fff', lineHeight: 1.3 }}>
        {report.title}
      </h1>
      {report.sections.map(section => (
        <div key={section.heading} style={{
          background: '#1a1a1a',
          border: '1px solid #2a2a2a',
          borderRadius: '10px',
          padding: '24px',
          marginBottom: '16px',
        }}>
          <div style={{
            fontSize: '11px',
            fontWeight: '600',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#e63946',
            marginBottom: '10px',
          }}>
            {section.heading}
          </div>
          <p style={{ fontSize: '15px', lineHeight: 1.65, color: '#ddd' }}>
            {section.content}
          </p>
        </div>
      ))}
    </div>
  )
}

function UploadZone({ selectedName, onDrop, onClick, children }) {
  return (
    <div
      onDrop={onDrop}
      onDragOver={e => e.preventDefault()}
      onClick={onClick}
      style={{
        borderTop: '1px solid #2a2a2a',
        padding: '14px 40px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        color: '#555',
        fontSize: '13px',
        cursor: 'pointer',
      }}
      onMouseEnter={e => e.currentTarget.style.background = '#141414'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <span style={{ fontSize: '16px' }}>📎</span>
      Drop a meeting transcript (.vtt or .txt) to add evidence for {selectedName}
      {children}
    </div>
  )
}
```

- [ ] **Step 2: Verify the full UI with the dev server running**

In `App.jsx`, temporarily add these lines after the `useEffect` to test the report layout without the backend:
```jsx
// TEMP: add below useEffect, remove after verifying
// useEffect(() => {
//   setSelected("Test Person")
//   setReport({
//     title: "The Complete Dossier on Test Person",
//     sections: [
//       { heading: "Meeting Behavior", content: "They type 'per my last email' in their sleep." },
//       { heading: "Final Verdict", content: "A cautionary tale." }
//     ]
//   })
// }, [])
```

Uncomment, check the UI, then remove the temp code.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/RoastPanel.jsx
git commit -m "feat: RoastPanel — report cards, spinner, drag-and-drop transcript upload"
```

---

## Task 10: Express Production Server

**Files:**
- Create: `server/index.js`
- Modify: `server/package.json`

- [ ] **Step 1: Create server/index.js**

Create `server/index.js`:
```js
const express = require('express')
const path = require('path')
const { createProxyMiddleware } = require('http-proxy-middleware')

const app = express()
const PORT = process.env.PORT || 3000
const API_URL = process.env.API_URL || 'http://localhost:8000'

app.use('/api', createProxyMiddleware({ target: API_URL, changeOrigin: true }))
app.use(express.static(path.join(__dirname, '../frontend/dist')))
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/dist/index.html'))
})

app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`))
```

- [ ] **Step 2: Update server/package.json with start script**

Replace `server/package.json`:
```json
{
  "name": "roast-coworkers-server",
  "version": "1.0.0",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.19.2",
    "http-proxy-middleware": "^3.0.0"
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add server/
git commit -m "feat: Express production server — serves frontend build, proxies /api to FastAPI"
```

---

## Task 11: Full Integration Run

**Files:** None — verification only.

- [ ] **Step 1: Confirm backend/.env is filled in**

All three values must be real:
```
SLACK_TOKEN=xoxp-...
GOOGLE_CREDENTIALS_PATH=credentials.json
ANTHROPIC_API_KEY=sk-ant-...
```

- [ ] **Step 2: Start the FastAPI backend**

```bash
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```

On first run, a browser window opens for Gmail OAuth. Authenticate → `token.json` is created. Subsequent runs skip OAuth.

- [ ] **Step 3: Start the React frontend**

In a second terminal:
```bash
cd frontend && npm run dev
```

Open `http://localhost:5173`. The sidebar should populate with Slack workspace members.

- [ ] **Step 4: Generate a roast**

Click any coworker in the sidebar. The spinner appears ("Digging up dirt..."), then the 4-section roast report renders.

- [ ] **Step 5: Upload a transcript**

Drag a `.vtt` or `.txt` file onto the upload zone at the bottom. Click the same coworker — the transcript content is now included in the evidence dossier.

- [ ] **Step 6: Run full test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: All 20 tests pass.

- [ ] **Step 7: Final commit**

```bash
git add -A && git commit -m "chore: verified full integration — Slack, Gmail, Claude roast generation, transcript upload"
```
