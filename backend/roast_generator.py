import json
import anthropic

SYSTEM_PROMPT = (
    "You are a sharp comedy writer at a work roast event. "
    "Write a funny, satirical roast report about a coworker based on their actual communications.\n\n"
    "Rules:\n"
    "- Be satirical and punchy — like a roast, not a performance review\n"
    "- Ground every joke in actual evidence from the data provided\n"
    "- Each section is 2-3 sentences with a killer one-liner\n"
    "- Focus on patterns: catchphrases, response times, meeting habits, email quirks\n"
    "- Never be cruel or target personal characteristics — only work behavior\n\n"
    "Return ONLY valid JSON with no markdown fencing:\n"
    '{"title": "The Complete Dossier on [Name]", '
    '"sections": ['
    '{"heading": "Meeting Behavior", "content": "..."}, '
    '{"heading": "Email Persona", "content": "..."}, '
    '{"heading": "Slack Presence", "content": "..."}, '
    '{"heading": "Final Verdict", "content": "..."}'
    ']}'
)


class RoastGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, name: str, evidence: list[str]) -> dict:
        capped = evidence[:50]
        evidence_text = "\n".join(f"- {e}" for e in capped)
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Generate a roast report for {name}.\n\n"
                    f"Evidence from their communications:\n{evidence_text}"
                )
            }]
        )
        if not message.content or not hasattr(message.content[0], 'text'):
            raise ValueError("Unexpected response structure from Claude API")
        text = message.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text
            text = text.rsplit('```', 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude returned invalid JSON: {e}") from e
