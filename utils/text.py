"""Accurate tool for text analysis and manipulation utilities."""

from typing import Any

import snowballstemmer


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


def show_characters(word: str) -> dict[str, Any]:
    """Show each character from an input word/string.

    Args:
        word: The input word/string to split into characters.

    Returns:
        Dict with the original `word` and a `characters` array.
    """
    return {
        "word": word,
        "characters": list(word),
    }


def word_stem(
    word: str,
    algorithm: str = "snowball",
) -> dict[str, Any]:
    """Return a stemmed form of a word.

    Args:
        word: Input word to stem.
        algorithm: Stemming algorithm to use. Defaults to
            `snowball`.

    Returns:
        Dict with original `word` and its `stem`.
        Returns an error dict for unsupported algorithms.
    """
    if algorithm.lower() != "snowball":
        return {
            "word": word,
            "error": (
                f"Unsupported algorithm '{algorithm}'. Supported: snowball"
            ),
        }

    stemmer = snowballstemmer.stemmer("english")
    stem = stemmer.stemWord(word)
    return {
        "word": word,
        "stem": stem,
        "algorithm": "snowball",
    }
