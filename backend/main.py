import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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
