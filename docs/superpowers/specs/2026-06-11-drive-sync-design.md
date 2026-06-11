# Drive Sync — Design Spec

## Overview

Automatically sync Google Meet transcripts from Google Drive into the in-memory `transcripts` dict on page load, enriching roast evidence without any user action.

## Architecture

Five files are touched:

| File | Change |
|------|--------|
| `backend/drive_client.py` | New — `DriveClient` class |
| `backend/tests/test_drive_client.py` | New — tests with injected mock service |
| `backend/main.py` | Add `drive` instance + `GET /api/sync-transcripts` route |
| `frontend/src/api.js` | Add `syncTranscripts()` fetch wrapper |
| `frontend/src/App.jsx` | Call `syncTranscripts()` fire-and-forget in `useEffect` |

## Data Flow

1. Frontend fires `GET /api/sync-transcripts` fire-and-forget on page load (alongside `fetchCoworkers()`)
2. Backend `DriveClient.get_meet_transcripts(days=30)` searches Drive for `.txt` files in the "Meet Recordings" folder modified in the last 30 days
3. Each file is downloaded and passed through the existing `parse_transcript()`
4. All speaker lines are merged into the shared `transcripts: dict[str, list[str]]` dict
5. When `POST /api/roast` runs for a person, their transcript lines are already present

## DriveClient

```python
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveClient:
    def __init__(self, service=None, credentials_path: str = None,
                 token_path: str = "drive_token.json"):
        # injected service for tests; OAuth flow for real use; None if no credentials

    def get_meet_transcripts(self, days: int = 30) -> dict[str, list[str]]:
        # 1. Find the "Meet Recordings" folder ID in Drive
        # 2. Search for .txt files in that folder modified within `days`
        # 3. Download each file's content
        # 4. Run through parse_transcript()
        # 5. Merge results → {speaker: [lines]}
        # Returns {} on any failure or if service is None
```

Drive search query:
```
mimeType='text/plain' and modifiedTime > '{RFC3339_date}' and '{folder_id}' in parents
```

The "Meet Recordings" folder ID is looked up by name once per `get_meet_transcripts()` call. If the folder doesn't exist, returns `{}`.

## FastAPI Route

```python
drive = DriveClient(credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", ""),
                    token_path="drive_token.json")

@app.get("/api/sync-transcripts")
async def sync_transcripts():
    result = drive.get_meet_transcripts(days=30)
    total = 0
    for speaker, lines in result.items():
        transcripts.setdefault(speaker, []).extend(lines)
        total += len(lines)
    return {"status": "ok", "speakers_found": len(result), "lines_added": total}
```

## Frontend Changes

`api.js`:
```js
export async function syncTranscripts() {
  await fetch('/api/sync-transcripts')
}
```

`App.jsx` — updated `useEffect`:
```js
useEffect(() => {
  syncTranscripts()  // fire and forget — no await, no error handling
  fetchCoworkers()
    .then(setCoworkers)
    .catch(() => setError('Failed to load coworkers — is the backend running?'))
}, [])
```

No spinner or error is shown for sync failures — it's silent enrichment.

## OAuth

`DriveClient` uses a separate token file (`drive_token.json`) and scope (`drive.readonly`). First run opens a second browser OAuth popup (one for Gmail, one for Drive). Both use the same `credentials.json`.

## Error Handling

All Drive API failures are caught and return `{}` — the app degrades gracefully to manual transcript uploads if Drive is unavailable or unconfigured.

## Testing

`test_drive_client.py` uses an injected mock service (same pattern as `test_gmail_client.py`):
- `test_get_meet_transcripts_returns_parsed_speakers` — mock folder lookup + file list + file content → verify speaker dict
- `test_get_meet_transcripts_returns_empty_when_folder_not_found` — mock empty folder search → verify `{}`
- `test_get_meet_transcripts_returns_empty_when_service_is_none` — no service → verify `{}`
- `test_no_crash_with_empty_credentials_path` — `DriveClient(credentials_path="")` → `service is None`

## Out of Scope

- Zoom transcript sync
- Deduplication across multiple syncs (lines may accumulate if sync runs multiple times per session — acceptable for a demo)
- UI feedback for sync status
