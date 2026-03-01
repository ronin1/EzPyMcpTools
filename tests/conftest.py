"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def fixture_dir() -> Path:
    """Return path to static test fixture directory."""
    return PROJECT_ROOT / "scripts" / "fixtures"


@pytest.fixture
def ipinfo_source_url(fixture_dir: Path) -> str:
    """Return file:// URL for mocked ipinfo payload."""
    return (fixture_dir / "ipinfo.mock.json").as_uri()


@pytest.fixture
def weather_source_url(fixture_dir: Path) -> str:
    """Return file:// URL for mocked weather HTML."""
    return (fixture_dir / "weather.mock.html").as_uri()
