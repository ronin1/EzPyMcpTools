"""Accurate tool for text analysis and manipulation utilities."""

import base64
from typing import Any


def words_count(text: str) -> dict[str, Any]:
    """Count the number of words in a text string.

    Args:
        text: The input text to count words in.

    Returns:
        Dict with `words` as the word count.
    """
    if not isinstance(text, str):
        return {"error": "Input must be a string"}
    return {"words": len(text.split())}


def characters_count(text: str) -> dict[str, Any]:
    """Count the number of characters in a text string.

    Args:
        text: The input text to count characters in.

    Returns:
        Dict with `characters.with_spaces` (total characters) and
        `characters.excluding_spaces` (characters without spaces).
    """
    if not isinstance(text, str):
        return {"error": "Input must be a string"}
    return {
        "characters": {
            "with_spaces": len(text),
            "excluding_spaces": len(text.replace(" ", "")),
        },
    }


def show_characters(word: str) -> dict[str, Any]:
    """Show each character from an input word/string.

    Args:
        word: The input word/string to split into characters.

    Returns:
        Dict with the original `word` and a `characters` array.
    """
    if not isinstance(word, str):
        return {"error": "Input must be a string"}
    return {
        "word": word,
        "characters": list(word),
    }


def to_base64(text: str) -> dict[str, Any]:
    """Convert text to base64 encoded string.

    Args:
        text: The input text to encode.

    Returns:
        Dict with `base64` as the encoded string.
    """
    encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    return {"base64": encoded}


def from_base64(base64_str: str) -> dict[str, Any]:
    """Convert base64 encoded string back to text.

    Args:
        base64_str: The base64 encoded string to decode.

    Returns:
        Dict with `text` as the decoded string.
    """
    try:
        padding = "=" * (-len(base64_str) % 4)
        decoded = base64.b64decode(base64_str + padding).decode("utf-8")
        return {"text": decoded}
    except Exception:
        return {"error": "Invalid base64 string"}
