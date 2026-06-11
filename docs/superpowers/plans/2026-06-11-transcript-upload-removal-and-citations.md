# Transcript Upload Removal + Source Citations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the manual transcript upload feature and add a source summary footer to roast reports showing how many Slack messages, emails, and transcript lines contributed.

**Architecture:** Two independent changes — backend cleans up the upload endpoint and enriches the roast response with source counts; frontend removes upload UI and renders a Sources footer using those counts.

**Tech Stack:** FastAPI (Python), React + Vite (JSX), pytest, Anthropic SDK

---

## Files

- Modify: `backend/main.py` — remove `/api/upload-transcript`, add source counting to `/api/roast`
- Modify: `backend/tests/test_main.py` — remove upload test, add sources assertion
- Modify: `frontend/src/api.js` — remove `uploadTranscript`
- Modify: `frontend/src/App.jsx` — remove `handleUpload` and `onUpload` prop
- Modify: `frontend/src/components/RoastPanel.jsx` — remove `UploadZone`, add `Sources` footer component

---

## Task 1: Backend — remove upload endpoint and add source counts to roast

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/tests/test_main.py`

- [ ] **Step 1: Update the roast test to assert sources field**

In `backend/tests/test_main.py`, replace `test_post_roast_calls_all_sources_and_returns_report` with:

```python
def test_post_roast_calls_all_sources_and_returns_report(client):
    c, mock_slack, mock_gmail, mock_roast, _ = client
    response = c.post("/api/roast", json={"name": "John Smith"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Complete Dossier on John Smith"
    assert data["sources"] == {"slack": 2, "email": 1, "transcripts": 0}
    mock_slack.get_messages_by_user.assert_called_once_with("John Smith")
    mock_gmail.get_messages_from_sender.assert_called_once_with("John Smith")
```

Also delete the entire `test_upload_transcript_stores_speaker_lines` test function (lines 51–64).

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd backend && python -m pytest tests/test_main.py::test_post_roast_calls_all_sources_and_returns_report -v
```

Expected: FAIL — `KeyError: 'sources'`

- [ ] **Step 3: Update `main.py` — remove upload endpoint and add source counts**

Replace the `transcripts` dict declaration and both affected endpoints in `main.py`. The full updated section (replace from `transcripts: dict` through the end of the file):

```python
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
    slack_msgs = slack.get_messages_by_user(request.name)
    email_msgs = gmail.get_messages_from_sender(request.name)
    transcript_lines = transcripts.get(request.name, [])

    evidence = slack_msgs + email_msgs + transcript_lines
    try:
        result = roast_gen.generate(request.name, evidence)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    result["sources"] = {
        "slack": len(slack_msgs),
        "email": len(email_msgs),
        "transcripts": len(transcript_lines),
    }
    return result


@app.get("/api/sync-transcripts")
async def sync_transcripts():
    result = drive.get_meet_transcripts(days=30)
    total = 0
    for speaker, lines in result.items():
        transcripts.setdefault(speaker, []).extend(lines)
        total += len(lines)
    return {"status": "ok", "speakers_found": len(result), "lines_added": total}
```

- [ ] **Step 4: Run all backend tests**

```bash
cd backend && python -m pytest tests/test_main.py -v
```

Expected: all tests PASS, `test_upload_transcript_stores_speaker_lines` no longer exists

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_main.py
git commit -m "feat: remove upload endpoint, add source counts to roast response"
```

---

## Task 2: Frontend — remove upload UI and add Sources footer

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/RoastPanel.jsx`

- [ ] **Step 1: Remove `uploadTranscript` from `api.js`**

Delete lines 22–31 (the `uploadTranscript` function). Final `api.js`:

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

export async function syncTranscripts() {
  await fetch('/api/sync-transcripts')
}
```

- [ ] **Step 2: Remove upload wiring from `App.jsx`**

Remove the `uploadTranscript` import and `handleUpload` function, and drop `onUpload` from the `RoastPanel` usage. Final `App.jsx`:

```jsx
import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import RoastPanel from './components/RoastPanel'
import { fetchCoworkers, fetchRoast, syncTranscripts } from './api'

export default function App() {
  const [coworkers, setCoworkers] = useState([])
  const [selected, setSelected] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    syncTranscripts()
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

  return (
    <div className="app">
      <Sidebar coworkers={coworkers} selected={selected} onSelect={handleSelect} />
      <RoastPanel
        selected={selected}
        report={report}
        loading={loading}
        error={error}
      />
    </div>
  )
}
```

- [ ] **Step 3: Rewrite `RoastPanel.jsx` — remove UploadZone, add Sources footer**

Replace the full file content:

```jsx
export default function RoastPanel({ selected, report, loading, error }) {
  return (
    <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
        {!selected && <EmptyState />}
        {selected && loading && <Spinner name={selected} />}
        {selected && error && <ErrorMessage message={error} />}
        {selected && report && !loading && <Report report={report} />}
      </div>
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
      {(report.sections || []).map(section => (
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
      <Sources sources={report.sources} />
    </div>
  )
}

function Sources({ sources }) {
  if (!sources) return null
  const items = [
    sources.slack > 0 && `Slack: ${sources.slack} messages`,
    sources.email > 0 && `Email: ${sources.email} threads`,
    sources.transcripts > 0 && `Transcripts: ${sources.transcripts} lines`,
  ].filter(Boolean)
  if (items.length === 0) return null
  return (
    <div style={{
      marginTop: '8px',
      padding: '12px 16px',
      borderTop: '1px solid #2a2a2a',
      color: '#555',
      fontSize: '12px',
    }}>
      <span style={{ color: '#444', fontWeight: '600', marginRight: '8px' }}>Sources</span>
      {items.join(' · ')}
    </div>
  )
}
```

- [ ] **Step 4: Verify the app works**

Start the backend (port 8000) and frontend (port 5173), open the app, select a coworker, and confirm:
- No upload zone at the bottom
- Sources footer appears at the bottom of the roast with non-zero counts

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api.js frontend/src/App.jsx frontend/src/components/RoastPanel.jsx
git commit -m "feat: remove upload UI, add sources footer to roast report"
```
