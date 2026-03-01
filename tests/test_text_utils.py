"""Tests for text utilities."""

from __future__ import annotations

from utils import text as text_utils


def test_text_counts_and_character_split() -> None:
    assert text_utils.words_count("hello world")["words"] == 2
    chars = text_utils.characters_count("a b")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 2
    assert text_utils.show_characters("hi")["characters"] == ["h", "i"]


def test_nlp_tokenize_and_stemming() -> None:
    stem = text_utils.word_stem("running")
    assert stem["stem"] == "run"
    nlp = text_utils.nlp_tokenize("The running and running")
    assert nlp["tokens"] == ["run", "run"]
    assert nlp["token_count"] == 2


def test_llm_tokenize_gpt2_path() -> None:
    payload = text_utils.llm_tokenize("Hello world", algorithm="gpt2")
    assert payload["tokenizer_backend"] == "tiktoken"
    assert payload["token_count"] == len(payload["tokens"])
    assert payload["token_count"] == len(payload["token_ids"])


def test_llm_tokenize_gpt2_case_insensitive() -> None:
    payload = text_utils.llm_tokenize("Hello world", algorithm="GPT2")
    assert payload["tokenizer_backend"] == "tiktoken"
    assert payload["algorithm"] == "gpt2"
