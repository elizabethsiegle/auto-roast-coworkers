import json
from unittest.mock import MagicMock, patch
from roast_generator import RoastGenerator


def _mock_anthropic(MockAnthropic, response_text: str):
    mock_client = MockAnthropic.return_value
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return mock_client


@patch('roast_generator.anthropic.Anthropic')
def test_generate_returns_parsed_report(MockAnthropic):
    report = {
        "title": "The Complete Dossier on John Smith",
        "sections": [
            {"heading": "Meeting Behavior", "content": "John invented the phrase 'circle back.'"},
            {"heading": "Email Persona", "content": "His emails arrive in clusters of three."},
            {"heading": "Slack Presence", "content": "Online at all hours. Never responds."},
            {"heading": "Final Verdict", "content": "John is what happens when a calendar invite gains sentience."},
        ]
    }
    _mock_anthropic(MockAnthropic, json.dumps(report))
    gen = RoastGenerator("sk-fake")
    result = gen.generate("John Smith", ["let's sync", "circle back"])
    assert result["title"] == "The Complete Dossier on John Smith"
    assert len(result["sections"]) == 4
    assert result["sections"][0]["heading"] == "Meeting Behavior"


@patch('roast_generator.anthropic.Anthropic')
def test_generate_caps_evidence_at_50(MockAnthropic):
    _mock_anthropic(MockAnthropic, '{"title": "T", "sections": []}')
    gen = RoastGenerator("sk-fake")
    evidence = [f"message {i}" for i in range(100)]
    gen.generate("John", evidence)
    call_kwargs = MockAnthropic.return_value.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert user_content.count("- message ") == 50


@patch('roast_generator.anthropic.Anthropic')
def test_generate_uses_correct_model(MockAnthropic):
    _mock_anthropic(MockAnthropic, '{"title": "T", "sections": []}')
    gen = RoastGenerator("sk-fake")
    gen.generate("John", ["evidence"])
    call_kwargs = MockAnthropic.return_value.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6"
