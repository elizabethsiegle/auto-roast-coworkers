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
