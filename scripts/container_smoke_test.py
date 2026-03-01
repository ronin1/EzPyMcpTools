#!/usr/bin/env python3
"""Smoke-test all exposed tools from inside the container."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True)
class Case:
    """Single in-container tool test case."""

    name: str
    args: list[str]


CASES: list[Case] = [
    Case("datetime__configured_timezone", []),
    Case("datetime__country_timezones", ["US"]),
    Case("datetime__current", ["PST"]),
    Case("ip_address__public_ipv4", []),
    Case("ip_address__approximate_physical_location", []),
    Case("math__add", ["1", "2"]),
    Case("math__subtract", ["10", "3"]),
    Case("math__multiply", ["3", "4"]),
    Case("math__divide", ["10", "2"]),
    Case("math__modulo", ["10", "3"]),
    Case("math__power", ["2", "8"]),
    Case("math__absolute", ["-5"]),
    Case("math__round_number", ["3.14159", "2"]),
    Case("math__ceil", ["2.1"]),
    Case("math__floor", ["2.9"]),
    Case("math__square_root", ["9"]),
    Case("math__factorial", ["5"]),
    Case("math__sin", ["30"]),
    Case("math__cos", ["60"]),
    Case("math__tan", ["45"]),
    Case("math__asin", ["0.5"]),
    Case("math__acos", ["0.5"]),
    Case("math__atan", ["1"]),
    Case("math__degrees_to_radians", ["180"]),
    Case("math__radians_to_degrees", ["3.1415926535"]),
    Case("math__hypotenuse", ["3", "4"]),
    Case("math__ln", ["2.718281828"]),
    Case("math__log", ["100", "10"]),
    Case("math__constants", []),
    Case("text__characters_count", ["hello world"]),
    Case("text__words_count", ["hello world from docker"]),
    Case("text__show_characters", ["hello"]),
    Case("text__word_stem", ["running"]),
    Case("text__nlp_tokenize", ["The running and running"]),
    Case("text__llm_tokenize", ["Hello world"]),
    Case("text__llm_tokenize", ["Hello world", "gpt2"]),
    Case("user_information__personal_data", []),
    Case("weather__temperature_unit_for_country", ["US"]),
    Case("weather__current_with_forecast", ["34.0522", "-118.2437"]),
]


def run_case(case: Case) -> tuple[bool, str]:
    """Run one case and verify output is a JSON object."""
    result = subprocess.run(
        ["uv", "run", "python", "utils.py", case.name, *case.args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip()

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return False, f"Non-JSON output: {exc}"

    if not isinstance(payload, dict):
        return False, "Output JSON is not an object"

    valid, reason = validate_payload(case.name, payload)
    if not valid:
        return False, reason

    return True, "ok"


def validate_payload(name: str, payload: dict[str, object]) -> tuple[bool, str]:
    """Validate minimum shape for key tool outputs."""
    if name == "user_information__personal_data":
        user_name = payload.get("name")
        if not user_name:
            return False, "missing `name` in personal_data output"

        if isinstance(user_name, dict):
            name_obj = cast(dict[str, object], user_name)
            first = str(name_obj.get("first", "")).strip()
            middle = str(name_obj.get("middle", "")).strip()
            last = str(name_obj.get("last", "")).strip()
            if not any([first, middle, last]):
                return False, "empty structured `name` object"
        elif not str(user_name).strip():
            return False, "empty `name` value"

        if "age" not in payload:
            return False, "missing `age` in personal_data output"

    if name == "text__show_characters":
        if payload.get("word") != "hello":
            return False, "unexpected `word` value for show_characters"
        if payload.get("characters") != ["h", "e", "l", "l", "o"]:
            return False, "unexpected `characters` array for show_characters"

    if name == "text__word_stem":
        if payload.get("word") != "running":
            return False, "unexpected `word` value for word_stem"
        if payload.get("stem") != "run":
            return False, "unexpected `stem` value for word_stem"

    if name == "text__nlp_tokenize":
        if payload.get("tokens") != ["run", "run"]:
            return False, "unexpected `tokens` value for nlp_tokenize"
        if payload.get("token_count") != 2:
            return False, "unexpected `token_count` value for nlp_tokenize"

    if name == "text__llm_tokenize":
        algorithm = payload.get("algorithm")
        if algorithm not in {"mistral_v3", "gpt2"}:
            return False, "unexpected `algorithm` value for llm_tokenize"
        backend = payload.get("tokenizer_backend")
        if algorithm == "mistral_v3" and backend != "mistral_common":
            return False, "unexpected backend for mistral llm_tokenize"
        if algorithm == "gpt2" and backend != "tiktoken":
            return False, "unexpected backend for tiktoken llm_tokenize"
        tokens = payload.get("tokens")
        token_ids = payload.get("token_ids")
        token_count = payload.get("token_count")
        if not isinstance(tokens, list) or not tokens:
            return False, "missing/empty `tokens` for llm_tokenize"
        if not isinstance(token_ids, list) or not token_ids:
            return False, "missing/empty `token_ids` for llm_tokenize"
        if token_count != len(tokens) or token_count != len(token_ids):
            return False, "invalid `token_count` for llm_tokenize"

    return True, "ok"


def main() -> int:
    """Run all smoke tests and print summary."""
    print(f"Running {len(CASES)} in-container tool checks...\n")

    passed = 0
    failed = 0
    for case in CASES:
        ok, detail = run_case(case)
        if ok:
            passed += 1
            print(f"[PASS] {case.name}")
        else:
            failed += 1
            print(f"[FAIL] {case.name}: {detail}")

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
