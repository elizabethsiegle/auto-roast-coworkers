# Transcript Upload Removal + Source Citations

**Date:** 2026-06-11

## Overview

Two independent UI/API changes:
1. Remove the manual transcript upload feature (replaced by Drive sync already running on load)
2. Add a source summary footer to each roast showing what data sources contributed

## Change 1: Remove Upload

**Backend:** Delete the `/api/upload-transcript` endpoint from `main.py`.

**Frontend:**
- Remove `UploadZone` component and its usage from `RoastPanel.jsx`
- Remove `onUpload` prop from `RoastPanel` and `handleUpload` from `App.jsx`
- Remove `uploadTranscript` export from `api.js`

The Drive sync (`/api/sync-transcripts`) already runs fire-and-forget on page load. The upload zone is redundant and confusing.

## Change 2: Source Citations Footer

**Backend:** In the `/api/roast` handler, count evidence items per source before passing to `RoastGenerator`. Append a `sources` field to the response dict returned to the client:

```json
{
  "title": "...",
  "sections": [...],
  "sources": { "slack": 12, "email": 5, "transcripts": 8 }
}
```

`RoastGenerator.generate()` is unchanged — sources are computed in the handler, not by Claude.

**Frontend:** Add a `Sources` footer component at the bottom of `RoastPanel`'s report view. Shows only sources with count > 0:

> **Sources** — Slack: 12 messages · Email: 5 threads · Transcripts: 8 lines

## Out of Scope

- Inline per-section citations (not requested)
- Changing the Claude prompt or roast structure
- Changing how Drive sync works
