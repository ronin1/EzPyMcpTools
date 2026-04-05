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


def test_text_words_count_edge_cases() -> None:
    # Empty string
    assert text_utils.words_count("")["words"] == 0

    # Multiple spaces
    assert text_utils.words_count("hello   world")["words"] == 2
    assert text_utils.words_count("  hello  world  ")["words"] == 2

    # Tabs and newlines
    assert text_utils.words_count("hello\tworld")["words"] == 2
    assert text_utils.words_count("hello\nworld")["words"] == 2
    assert text_utils.words_count("hello\r\nworld")["words"] == 2

    # Single word
    assert text_utils.words_count("single")["words"] == 1

    # Only spaces
    assert text_utils.words_count("   ")["words"] == 0

    # Non-string input (should return error dict)
    result = text_utils.words_count(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_characters_count_edge_cases() -> None:
    # Empty string
    chars = text_utils.characters_count("")["characters"]
    assert chars["with_spaces"] == 0
    assert chars["excluding_spaces"] == 0

    # Only spaces
    chars = text_utils.characters_count("   ")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 0

    # Mixed whitespace - note: excluding_spaces only removes literal spaces, not tabs/newlines
    chars = text_utils.characters_count("a b\tc\nd")["characters"]
    assert chars["with_spaces"] == 7  # a, space, b, tab, c, newline, d
    assert chars["excluding_spaces"] == 6  # a, b, tab, c, newline, d (only spaces removed)

    # Non-string input
    result = text_utils.characters_count(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_show_characters_edge_cases() -> None:
    # Empty string
    result = text_utils.show_characters("")
    assert result["word"] == ""
    assert result["characters"] == []

    # Single character
    result = text_utils.show_characters("x")
    assert result["word"] == "x"
    assert result["characters"] == ["x"]

    # Unicode characters
    result = text_utils.show_characters("你好")
    assert result["word"] == "你好"
    assert result["characters"] == ["你", "好"]

    # Emoji
    result = text_utils.show_characters("🎉")
    assert result["word"] == "🎉"
    assert result["characters"] == ["🎉"]

    # Non-string input
    result = text_utils.show_characters(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_base64_edge_cases() -> None:
    # Empty string
    encoded = text_utils.to_base64("")
    assert encoded["base64"] == ""
    decoded = text_utils.from_base64("")
    assert decoded["text"] == ""

    # Unicode
    original = "你好世界"
    encoded = text_utils.to_base64(original)
    decoded = text_utils.from_base64(encoded["base64"])
    assert decoded["text"] == original

    # Invalid base64 input - should return error (invalid characters)
    result = text_utils.from_base64("invalid!")
    assert "error" in result

    # Another invalid base64 test - characters outside base64 alphabet
    result = text_utils.from_base64("YWJjZ@")  # @ is not in base64 alphabet
    assert "error" in result

    # Non-string input
    result = text_utils.to_base64(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"

    result = text_utils.from_base64(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Invalid base64 string"
