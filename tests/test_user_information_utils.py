"""Tests for user information utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils import user_information


def test_personal_data_uses_fallback_name(
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
                "addresss": ["123 Main St"],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(user_information, "_CONFIG_PATH", config)
    monkeypatch.setattr(user_information, "_get_username", lambda: "jane")
    monkeypatch.setattr(user_information, "_get_full_name", lambda: "Jane Doe")

    payload = user_information.personal_data()
    assert payload["name"] == "jane"
    assert payload["long_name"] == "Jane Doe"
    assert isinstance(payload["age"], int)


def test_personal_data_missing_required_fields_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = tmp_path / "user.data.json"
    config.write_text(
        json.dumps({"email": "jane@example.com"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(user_information, "_CONFIG_PATH", config)

    with pytest.raises(FileNotFoundError):
        user_information.personal_data()
