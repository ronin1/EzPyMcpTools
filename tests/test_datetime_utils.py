"""Tests for datetime utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils import datetime as dt_utils
from utils import user_information


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


def test_current_uses_user_configured_timezone(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = tmp_path / "user.data.json"
    config.write_text(
        json.dumps(
            {
                "birthday": "1990-01-31",
                "email": "jane@example.com",
                "phone": "+1-555-123-4567",
                "addresses": ["123 Main St"],
                "timezone": "America/Chicago",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(user_information, "_CONFIG_PATH", config)
    monkeypatch.setattr(user_information, "_get_username", lambda: "jane")
    monkeypatch.setattr(user_information, "_get_full_name", lambda: "Jane Doe")

    payload = dt_utils.current()
    assert "error" not in payload
    from utils.user_information import personal_data

    user_info = personal_data()
    resolved_user_tz = dt_utils._resolve_timezone(user_info["timezone"])
    assert resolved_user_tz is not None
    iana_name = str(resolved_user_tz)
    assert payload["timezone"]["name"] == iana_name


def test_current_with_system_fallback_when_user_data_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Test that datetime.current() works even when user.data.json is missing
    config = tmp_path / "user.data.json"
    # Don't create the file - simulate missing file
    monkeypatch.setattr(user_information, "_CONFIG_PATH", config)
    monkeypatch.setattr(user_information, "_get_username", lambda: "testuser")
    monkeypatch.setattr(user_information, "_get_full_name", lambda: "Test User")

    # Should not raise an exception and should return valid timezone data
    payload = dt_utils.current()
    assert "error" not in payload
    assert "date_time" in payload
    assert "timezone" in payload
    assert isinstance(payload["timezone"]["name"], str)


def test_current_with_invalid_user_data_timezone(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Test fallback when user.data.json has invalid timezone
    config = tmp_path / "user.data.json"
    config.write_text(
        json.dumps(
            {
                "birthday": "1990-01-31",
                "email": "jane@example.com",
                "phone": "+1-555-123-4567",
                "addresses": ["123 Main St"],
                "timezone": "Invalid/Timezone",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(user_information, "_CONFIG_PATH", config)
    monkeypatch.setattr(user_information, "_get_username", lambda: "jane")
    monkeypatch.setattr(user_information, "_get_full_name", lambda: "Jane Doe")

    # Should fall back to system timezone detection
    payload = dt_utils.current()
    assert "error" not in payload
    assert "date_time" in payload
    assert "timezone" in payload


def test_country_timezones_invalid_country() -> None:
    payload = dt_utils.country_timezones("XX")  # Invalid country code
    assert "error" in payload


def test_country_timezones_lowercase() -> None:
    payload = dt_utils.country_timezones("us")  # lowercase
    assert payload["country_code"] == "US"
    assert payload["count"] >= 1
    assert isinstance(payload["timezones"], list)


def test_configured_timezone_returns_string() -> None:
    payload = dt_utils.configured_timezone()
    assert isinstance(payload, dict)
    assert "timezone_name" in payload
    assert isinstance(payload["timezone_name"], str)
    assert len(payload["timezone_name"]) > 0


def _detect_country_code_from_locale_returns_string() -> None:
    # This is tested indirectly through country_timezones
    # but we can test the function directly if needed
    from utils.datetime import _detect_country_code_from_locale

    result = _detect_country_code_from_locale()
    assert isinstance(result, str)
