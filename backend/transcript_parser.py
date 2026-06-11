import re

_TIMESTAMP_RE = re.compile(r'^\d{2}:\d{2}:\d{2}')
_SPEAKER_RE = re.compile(r'^([A-Za-z][^:]{1,50}):\s+(.+)$')


def parse_transcript(content: str, filename: str) -> dict[str, list[str]]:
    """Parse .vtt or .txt transcript. Returns {speaker_name: [spoken_lines]}."""
    result: dict[str, list[str]] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('WEBVTT') or _TIMESTAMP_RE.match(line):
            continue
        match = _SPEAKER_RE.match(line)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            result.setdefault(speaker, []).append(text)
    return result
