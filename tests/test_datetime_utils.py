"""Tests for datetime utilities."""

from __future__ import annotations

from utils import datetime as dt_utils


def test_current_with_timezone_abbreviation() -> None:
    payload = dt_utils.current("PST")
    assert "error" not in payload
    assert payload["timezone"]["name"] == "America/Los_Angeles"


def test_current_invalid_timezone_returns_error() -> None:
    payload = dt_utils.current("NOT_A_REAL_TZ")
    assert "error" in payload


def test_configured_timezone_shape() -> None:
    payload = dt_utils.configured_timezone()
    assert isinstance(payload["timezone_name"], str)
    assert payload["timezone_name"]


def test_country_timezones_for_us() -> None:
    payload = dt_utils.country_timezones("US")
    assert payload["country_code"] == "US"
    assert payload["count"] >= 1
    assert isinstance(payload["timezones"], list)
