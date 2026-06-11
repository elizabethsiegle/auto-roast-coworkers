# Roast Coworkers — Design Spec

## Overview

A private web app that ingests Slack messages, Gmail threads, and meeting transcripts for a given coworker, then uses Claude to generate a funny, satirical roast report about them. Built for personal use and a demo video.

## Stack

- **Backend**: Python + FastAPI
- **Frontend**: React (Vite) served in development via Vite dev server, in production via Express
- **AI**: Claude API (`claude-sonnet-4-6`)
- **Auth**: Personal API tokens stored in `.env` (Slack user token, Gmail credentials JSON)

## Architecture

```
frontend/          React + Vite
  src/
    App.jsx        Root — sidebar + main panel layout
    Sidebar.jsx    List of detected coworkers
    RoastPanel.jsx Roast report display + upload zone
    api.js         Fetch wrappers for backend endpoints

backend/           FastAPI
  main.py          App entry point, route definitions
  slack_client.py  Slack Web API — fetch messages by person
  gmail_client.py  Gmail API — fetch threads by sender/recipient
  transcript_parser.py  Parse .txt / .vtt meeting transcript uploads
  roast_generator.py    Assemble dossier → call Claude → return report
  .env             SLACK_TOKEN, GOOGLE_CREDENTIALS_PATH
```

## Data Flow

1. On page load, `GET /coworkers` — backend scans recent Slack members and Gmail contacts, returns deduplicated list of names
2. User clicks a coworker → `POST /roast { name }`:
   - `slack_client` pulls recent messages from/about that person
   - `gmail_client` fetches recent threads involving them
   - `transcript_parser` includes any previously uploaded transcript evidence
   - All evidence assembled into a dossier `{ name, evidence: [str] }`
   - Dossier sent to `roast_generator`, which calls Claude and returns structured report
3. Optional: user drags a `.txt` or `.vtt` file onto the upload zone → `POST /upload-transcript` → parsed and stored in memory for the session

## Roast Report Structure

Claude returns a JSON object:

```json
{
  "title": "The Complete Dossier on Karen from Marketing",
  "sections": [
    { "heading": "Meeting Behavior", "content": "..." },
    { "heading": "Email Persona", "content": "..." },
    { "heading": "Slack Presence", "content": "..." },
    { "heading": "Final Verdict", "content": "..." }
  ]
}
```

Each section is 2–3 sentences with a one-liner punch. Tone: comedy writer, satirical, not mean-spirited.

## Claude Prompt Design

System prompt establishes the persona: a sharp comedy writer doing a roast, not a bully. Instructed to:
- Find communication patterns (reply-all abuse, emoji overuse, "per my last email" energy)
- Ground jokes in actual evidence from the dossier
- Keep each section punchy — no padding

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/coworkers` | List of detected people across sources |
| POST | `/roast` | Generate roast for `{ name }` |
| POST | `/upload-transcript` | Upload `.txt` or `.vtt` file |

## UI Layout

- **Left sidebar**: scrollable list of coworker names; click to select
- **Main panel**: selected coworker's roast report rendered with section cards; spinner while generating
- **Upload zone**: drag-and-drop area at bottom of main panel for transcript files

## Data Sources & Setup

- **Slack**: Create a Slack app in your workspace, install it, copy the user token to `SLACK_TOKEN` in `.env`
- **Gmail**: Create a Google Cloud project, enable Gmail API, download `credentials.json`, set `GOOGLE_CREDENTIALS_PATH` in `.env`
- **Meeting transcripts**: Drag and drop Zoom `.vtt` or Google Meet `.txt` exports — no API needed

## What's Out of Scope

- Multi-user support / auth
- Persisted reports (session-only)
- Sending or sharing the roast to anyone
- Real-time Slack/email streaming
