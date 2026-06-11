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
