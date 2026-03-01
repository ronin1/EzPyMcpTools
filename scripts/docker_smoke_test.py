#!/usr/bin/env python3
"""Smoke-test all exposed tools through the Docker image."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    """Single dockerized tool test case."""

    name: str
    args: list[str]
    needs_user_data: bool = False


IMAGE = os.environ.get("EZPY_TOOLS_IMAGE", "ezpy-tools:alpine")
USER_DATA_PATH = os.path.abspath(
    os.environ.get("EZPY_USER_DATA", "./user.data.json")
)


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
    Case(
        "user_information__personal_data",
        [],
        needs_user_data=True,
    ),
    Case("weather__temperature_unit_for_country", ["US"]),
    Case(
        "weather__current_with_forecast",
        ["34.0522", "-118.2437"],
    ),
]


def run_case(case: Case) -> tuple[bool, str]:
    """Run one case and verify output is a JSON object."""
    cmd = ["docker", "run", "--rm"]
    if case.needs_user_data:
        cmd.extend(["-v", f"{USER_DATA_PATH}:/app/user.data.json:ro"])
    cmd.extend(["--entrypoint", "./tools", IMAGE, case.name, *case.args])

    result = subprocess.run(
        cmd,
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

    return True, "ok"


def main() -> int:
    """Run all smoke tests and print a summary."""
    if not os.path.exists(USER_DATA_PATH):
        print(
            f"ERROR: user data file not found: {USER_DATA_PATH}",
            file=sys.stderr,
        )
        return 2

    print(f"Image: {IMAGE}")
    print(f"User data: {USER_DATA_PATH}")
    print(f"Running {len(CASES)} dockerized tool checks...\n")

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
