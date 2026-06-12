import re

_TIMESTAMP_RE = re.compile(r'^\d{2}:\d{2}:\d{2}')
_SPEAKER_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 '\-\.]{0,49}):\s+(.+)$")

# Common markers that look like speaker names but aren't
_MARKERS = {'TODO', 'FIXME', 'NOTE', 'Note', 'FYI', 'INFO', 'WARN', 'WARNING', 'ERROR', 'DEPRECATED'}


def _is_likely_speaker_name(name: str) -> bool:
    """Check if a name looks like a speaker name (not a marker, and either has space or mixed case)."""
    if name in _MARKERS:
        return False
    return ' ' in name or not name.isupper()


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
            if _is_likely_speaker_name(speaker):
                result.setdefault(speaker, []).append(text)
    return result
