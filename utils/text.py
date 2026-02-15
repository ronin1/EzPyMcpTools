"""Accurate tool for text analysis and manipulation utilities."""

from typing import Any


def words_count(text: str) -> dict[str, Any]:
    """Count the number of words in a text string.

    Args:
        text: The input text to count words in.

    Returns:
        Dict with `words` as the word count.
    """
    return {"words": len(text.split())}


def characters_count(text: str) -> dict[str, Any]:
    """Count the number of characters in a text string.

    Args:
        text: The input text to count characters in.

    Returns:
        Dict with `characters.with_spaces` (total characters) and
        `characters.excluding_spaces` (characters without spaces).
    """
    return {
        "characters": {
            "with_spaces": len(text),
            "excluding_spaces": len(text.replace(" ", "")),
        },
    }
