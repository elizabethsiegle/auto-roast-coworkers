from transcript_parser import parse_transcript


def test_parse_vtt_extracts_speaker_lines():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:05.000
John Smith: This is a great idea, we should schedule a follow-up

00:00:06.000 --> 00:00:10.000
Jane Doe: Per my last email, I already covered this

00:00:11.000 --> 00:00:15.000
John Smith: Sure but let's circle back offline"""

    result = parse_transcript(vtt, "meeting.vtt")

    assert "John Smith" in result
    assert len(result["John Smith"]) == 2
    assert "This is a great idea" in result["John Smith"][0]
    assert "Jane Doe" in result
    assert "Per my last email" in result["Jane Doe"][0]


def test_parse_txt_extracts_speaker_lines():
    txt = """John Smith: This is a great idea
Jane Doe: Per my last email, I already covered this
John Smith: Sure but let's circle back offline"""

    result = parse_transcript(txt, "meeting.txt")

    assert "John Smith" in result
    assert len(result["John Smith"]) == 2
    assert "Jane Doe" in result


def test_vtt_ignores_non_speaker_lines():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:05.000
Some line without a speaker prefix

00:00:06.000 --> 00:00:10.000
Jane Doe: This should be captured"""

    result = parse_transcript(vtt, "meeting.vtt")

    assert "Jane Doe" in result
    assert len(result) == 1


def test_empty_content_returns_empty_dict():
    assert parse_transcript("", "meeting.vtt") == {}


def test_preserves_punctuation_in_speaker_lines():
    txt = "John Smith: What's the ROI on this, Karen? It's... complicated."
    result = parse_transcript(txt, "notes.txt")
    assert result["John Smith"][0] == "What's the ROI on this, Karen? It's... complicated."


def test_does_not_capture_non_name_prefixes():
    txt = """TODO: fix this later
Note: this is important
John Smith: actual speaker line"""
    result = parse_transcript(txt, "notes.txt")
    assert "TODO" not in result
    assert "Note" not in result
    assert "John Smith" in result
