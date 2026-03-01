"""Tests for weather utilities."""

from __future__ import annotations

from utils import weather


def test_current_with_forecast_uses_mock_source(
    weather_source_url: str,
) -> None:
    payload = weather.current_with_forecast(
        34.0522,
        -118.2437,
        source_url=weather_source_url,
    )
    assert payload["location"] == "Los Angeles CA"
    assert payload["current"]["conditions"] == "Sunny"
    assert len(payload["forecast"]) >= 2


def test_temperature_unit_for_country_supports_alpha2_and_alpha3() -> None:
    assert weather.temperature_unit_for_country("US")["default_unit"] == (
        "fahrenheit"
    )
    assert weather.temperature_unit_for_country("USA")["default_unit"] == (
        "fahrenheit"
    )
    assert weather.temperature_unit_for_country("FR")["default_unit"] == (
        "celsius"
    )
