from unittest.mock import MagicMock
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
