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
    assert data["sources"] == {"slack": 2, "email": 1, "transcripts": 0}
    mock_slack.get_messages_by_user.assert_called_once_with("John Smith")
    mock_gmail.get_messages_from_sender.assert_called_once_with("John Smith")


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
