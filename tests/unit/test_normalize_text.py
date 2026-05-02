from streaming.text_utils import normalize_text


def test_normalize_collapses_whitespace():
    assert normalize_text("hello\n\n  world\t") == "hello world"


def test_normalize_handles_none_and_empty():
    assert normalize_text(None) is None
    assert normalize_text("   ") is None


def test_normalize_keeps_punctuation():
    assert normalize_text("Breaking: news!") == "Breaking: news!"
