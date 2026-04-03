"""Tests for text utilities."""

from __future__ import annotations

from utils import text as text_utils


def test_text_counts_and_character_split() -> None:
    assert text_utils.words_count("hello world")["words"] == 2
    chars = text_utils.characters_count("a b")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 2
    assert text_utils.show_characters("hi")["characters"] == ["h", "i"]


def test_text_base64_encoding() -> None:
    original = "hello world"
    encoded_result = text_utils.to_base64(original)
    assert "base64" in encoded_result

    decoded_result = text_utils.from_base64(encoded_result["base64"])
    assert decoded_result["text"] == original

    test_cases = ["", "a", "Hello, 世界!", "line1\nline2"]
    for tc in test_cases:
        result = text_utils.to_base64(tc)
        decoded = text_utils.from_base64(result["base64"])
        assert decoded["text"] == tc

    # Test decoding with missing padding (uneven bits)
    padding_test_cases = [
        ("a", "YQ"),  # 'a' -> 'YQ==' (missing 2 '=')
        ("ab", "YWI"),  # 'ab' -> 'YWIs' (missing 1 '=')
        ("abc", "YWJj"),  # 'abc' -> 'YWJj' (no padding needed)
    ]
    for original, encoded in padding_test_cases:
        decoded = text_utils.from_base64(encoded)
        assert decoded["text"] == original
