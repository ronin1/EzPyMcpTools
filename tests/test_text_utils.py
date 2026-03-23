"""Tests for text utilities."""

from __future__ import annotations

from utils import text as text_utils


def test_text_counts_and_character_split() -> None:
    assert text_utils.words_count("hello world")["words"] == 2
    chars = text_utils.characters_count("a b")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 2
    assert text_utils.show_characters("hi")["characters"] == ["h", "i"]
