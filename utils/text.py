"""Accurate tool for text analysis and manipulation utilities."""

import re
from functools import lru_cache
from typing import Any

import snowballstemmer
import tiktoken
from mistral_common.tokens.tokenizers.base import SpecialTokenPolicy
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def _stem_word(word: str, algorithm: str) -> str | None:
    """Stem a word using the requested algorithm."""
    if algorithm.lower() != "snowball":
        return None
    stemmer = _get_snowball_stemmer("english")
    return stemmer.stemWord(word)


@lru_cache(maxsize=8)
def _get_snowball_stemmer(language: str) -> Any:
    """Return a cached Snowball stemmer instance for a language."""
    return snowballstemmer.stemmer(language)


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
    stem = _stem_word(word, algorithm)
    if stem is None:
        return {
            "word": word,
            "error": (
                f"Unsupported algorithm '{algorithm}'. Supported: snowball"
            ),
        }

    return {
        "word": word,
        "stem": stem,
        "algorithm": "snowball",
    }


def nlp_tokenize(
    text: str,
    algorithm: str = "snowball",
) -> dict[str, Any]:
    """Tokenize text into normalized stemmed words.

    This function:
      - normalizes case
      - removes punctuation/whitespace
      - removes common stop words
      - stems remaining words

    Args:
        text: Input text to tokenize.
        algorithm: Stemming algorithm (default: `snowball`).

    Returns:
        Dict containing original text, a `tokens` array of stemmed
        words, and `token_count` as total number of stemmed tokens.
        Returns an error dict for unsupported algorithms.
    """
    if algorithm.lower() != "snowball":
        return {
            "text": text,
            "error": (
                f"Unsupported algorithm '{algorithm}'. Supported: snowball"
            ),
        }

    raw_tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
    filtered_tokens = [
        tok for tok in raw_tokens if tok and tok not in _STOP_WORDS
    ]
    stems = [_stem_word(tok, algorithm) for tok in filtered_tokens]
    stemmed_tokens = [tok for tok in stems if tok]

    return {
        "text": text,
        "algorithm": "snowball",
        "tokens": stemmed_tokens,
        "token_count": len(stemmed_tokens),
    }


def llm_tokenize(
    text: str,
    algorithm: str = "mistral_v3",
) -> dict[str, Any]:
    """Tokenize text using Mistral or tiktoken tokenizers.

    Args:
        text: Input text to tokenize.
        algorithm: Tokenizer algorithm. Defaults to `mistral_v3`.
            - `mistral_*` values use `MistralTokenizer`.
            - other values use `tiktoken.get_encoding(...)`.

    Returns:
        Dict containing original text, tokenizer metadata, token ids,
        decoded token strings, and token count.
        Returns an error dict for unsupported encodings.
    """
    encoding_name = algorithm.strip() or "mistral_v3"

    if encoding_name.lower().startswith("mistral_"):
        mistral_factories = {
            "mistral_v1": MistralTokenizer.v1,
            "mistral_v2": MistralTokenizer.v2,
            "mistral_v3": MistralTokenizer.v3,
        }
        factory = mistral_factories.get(encoding_name.lower())
        if factory is None:
            return {
                "text": text,
                "error": (
                    f"Unsupported algorithm '{algorithm}'. "
                    "Supported mistral algorithms: "
                    "mistral_v1, mistral_v2, mistral_v3"
                ),
            }

        tokenizer = factory()
        base_tokenizer = tokenizer.instruct_tokenizer.tokenizer
        token_ids = base_tokenizer.encode(text, bos=False, eos=False)
        tokens = [
            base_tokenizer.decode(
                [token_id],
                special_token_policy=SpecialTokenPolicy.IGNORE,
            )
            for token_id in token_ids
        ]
        return {
            "text": text,
            "algorithm": encoding_name.lower(),
            "tokenizer_backend": "mistral_common",
            "tokens": tokens,
            "token_ids": token_ids,
            "token_count": len(token_ids),
        }

    try:
        enc = tiktoken.get_encoding(encoding_name)
    except ValueError:
        return {
            "text": text,
            "error": (
                f"Unsupported algorithm '{algorithm}'. "
                "Use a valid tiktoken encoding name."
            ),
            "available_algorithms": sorted(tiktoken.list_encoding_names()),
        }

    token_ids = enc.encode(text)
    tokens = [enc.decode([token_id]) for token_id in token_ids]
    return {
        "text": text,
        "algorithm": encoding_name,
        "tokenizer_backend": "tiktoken",
        "tokens": tokens,
        "token_ids": token_ids,
        "token_count": len(token_ids),
    }
