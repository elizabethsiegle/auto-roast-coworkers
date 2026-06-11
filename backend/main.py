import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from slack_client import SlackClient
from gmail_client import GmailClient
from drive_client import DriveClient
from roast_generator import RoastGenerator

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
