from unittest.mock import patch
from slack_client import SlackClient


@patch('slack_client.WebClient')
def test_get_workspace_members_excludes_bots_and_deleted(MockWebClient):
    MockWebClient.return_value.users_list.return_value = {
        "members": [
            {"id": "U1", "is_bot": False, "deleted": False,
             "profile": {"display_name": "John Smith"}, "real_name": "John Smith"},
            {"id": "USLACKBOT", "is_bot": True, "deleted": False,
             "profile": {"display_name": "Slackbot"}, "real_name": "Slackbot"},
            {"id": "U2", "is_bot": False, "deleted": True,
             "profile": {"display_name": "Gone User"}, "real_name": "Gone User"},
            {"id": "U3", "is_bot": False, "deleted": False,
             "profile": {"display_name": "Jane Doe"}, "real_name": "Jane Doe"},
        ]
    }
    client = SlackClient("xoxp-fake")
    result = client.get_workspace_members()
    assert "John Smith" in result
    assert "Jane Doe" in result
    assert "Slackbot" not in result
    assert "Gone User" not in result


@patch('slack_client.WebClient')
def test_get_workspace_members_falls_back_to_real_name_when_display_name_empty(MockWebClient):
    MockWebClient.return_value.users_list.return_value = {
        "members": [
            {"id": "U1", "is_bot": False, "deleted": False,
             "profile": {"display_name": ""}, "real_name": "Jane No Display"},
        ]
    }
    client = SlackClient("xoxp-fake")
    result = client.get_workspace_members()
    assert "Jane No Display" in result


@patch('slack_client.WebClient')
def test_get_messages_by_user_returns_message_texts(MockWebClient):
    MockWebClient.return_value.search_messages.return_value = {
        "messages": {
            "matches": [
                {"text": "Let's circle back on this"},
                {"text": "Per my last email..."},
            ]
        }
    }
    client = SlackClient("xoxp-fake")
    result = client.get_messages_by_user("John Smith")
    assert "Let's circle back on this" in result
    assert "Per my last email..." in result
    MockWebClient.return_value.search_messages.assert_called_once_with(
        query="from:John Smith", count=100
    )


@patch('slack_client.WebClient')
def test_get_messages_by_user_returns_empty_list_when_no_matches(MockWebClient):
    MockWebClient.return_value.search_messages.return_value = {"messages": {"matches": []}}
    client = SlackClient("xoxp-fake")
    assert client.get_messages_by_user("Ghost") == []
