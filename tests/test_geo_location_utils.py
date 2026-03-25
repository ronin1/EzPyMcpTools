"""Tests for geographical location utilities."""

from __future__ import annotations

from utils import geo_location as geo_location_utils
from utils.geo_location import (
    _ISO_3166_ALPHA2,
    _SMALL_SENTINEL,
    _GeoNamesParser,
    _is_admin_division,
)


def test_coordinates_by_name_invalid_country() -> None:
    """Test coordinates_by_name rejects unknown country codes."""
    result = geo_location_utils.coordinates_by_name("London", "XX")
    assert "error" in result
    assert "Unknown country code" in result["error"]

    result = geo_location_utils.coordinates_by_name("London", "ZZ")
    assert "error" in result
    assert "Unknown country code" in result["error"]


def test_coordinates_by_name_wrong_length_country() -> None:
    """Test that single-char and 3-char codes are rejected."""
    result = geo_location_utils.coordinates_by_name("London", "U")
    assert "error" in result

    result = geo_location_utils.coordinates_by_name("London", "USA")
    assert "error" in result


def test_coordinates_by_name_country_optional() -> None:
    """Test that country can be omitted entirely."""
    result = geo_location_utils.coordinates_by_name("Disneyland, CA")
    assert "error" not in result
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) >= 1
    assert "country" not in result["query"]


def test_coordinates_by_name_default_limit() -> None:
    """Test that coordinates_by_name defaults to 3 results."""
    result = geo_location_utils.coordinates_by_name("London", "US")
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) <= 3


def test_coordinates_by_name_custom_limit() -> None:
    """Test that coordinates_by_name respects custom limit."""
    result = geo_location_utils.coordinates_by_name("London", "US", limit=1)
    assert "results" in result
    assert len(result["results"]) <= 1


def test_coordinates_by_name_limit_clamped() -> None:
    """Test that limit is clamped between 1 and 20."""
    result_low = geo_location_utils.coordinates_by_name("London", "US", limit=0)
    assert "results" in result_low
    assert len(result_low["results"]) <= 1

    result_high = geo_location_utils.coordinates_by_name("London", "US", limit=100)
    assert "results" in result_high
    assert len(result_high["results"]) <= 20


def test_parse_country_with_detail() -> None:
    """Test _parse_country splits country, state, and city via sentinel."""
    raw = f"United States , California{_SMALL_SENTINEL}Orange"
    result = _GeoNamesParser._parse_country(raw)
    assert result["country_name"] == "United States"
    assert result["state_province"] == "California"
    assert result["city_town"] == "Orange"
    assert "country_code" not in result


def test_parse_country_with_hierarchy() -> None:
    """Test _parse_country handles multi-level detail (e.g. France)."""
    raw = f"France , Île-de-France{_SMALL_SENTINEL}Paris Department > Paris > Paris"
    result = _GeoNamesParser._parse_country(raw)
    assert result["country_name"] == "France"
    assert result["state_province"] == "Île-de-France"
    assert result["city_town"] == "Paris"


def test_parse_country_no_detail() -> None:
    """Test _parse_country when there is no <small> detail (e.g. Japan, Tokyo)."""
    raw = "Japan , Tokyo"
    result = _GeoNamesParser._parse_country(raw)
    assert result["country_name"] == "Japan"
    assert result["state_province"] == "Tokyo"
    assert result["city_town"] == ""


def test_population_stripped_from_feature_class() -> None:
    """Test that population is extracted and removed from feature_class."""
    parser = _GeoNamesParser()
    row = {
        "name": "Springfield",
        "country": f"United States , Illinois{_SMALL_SENTINEL}Springfield",
        "feature_class": "seat of a first-order administrative division population 114,230",
        "latitude": "N 39° 47' 59\"",
        "longitude": "W 89° 39' 18\"",
    }
    processed = parser._process_row(row)
    assert processed["population"] == "114230"
    assert "population" not in processed.get("feature_class", "")


def test_lax_ca_us() -> None:
    """Test known lookup: LAX, CA with country US prefers airport over admin division."""
    result = geo_location_utils.coordinates_by_name("LAX, CA", "US", limit=1)
    assert "results" in result
    assert len(result["results"]) == 1
    first = result["results"][0]
    assert first["name"] == "Los Angeles International Airport"
    assert first["feature_class"] == "airport"
    assert first["state_province"] == "California"
    assert "latitude_decimal" in first
    assert "longitude_decimal" in first


def test_disneyland_ca_no_country() -> None:
    """Test known lookup: Disneyland, CA without country."""
    result = geo_location_utils.coordinates_by_name("Disneyland, CA", limit=1)
    assert "results" in result
    assert len(result["results"]) == 1
    first = result["results"][0]
    assert first["name"] == "Disneyland"
    assert first["city_town"] == "Orange"
    assert "country_code" not in first
    assert "latitude_decimal" in first
    assert "longitude_decimal" in first


def test_admin_division_detection() -> None:
    """Test that _is_admin_division correctly classifies feature classes."""
    assert _is_admin_division("seat of a second-order administrative division")
    assert _is_admin_division("seat of a first-order administrative division")
    assert not _is_admin_division("airport")
    assert not _is_admin_division("amusement park")
    assert not _is_admin_division("capital of a political entity")
    assert not _is_admin_division("populated place")


def test_iso_country_code_set_is_complete() -> None:
    """Sanity-check that the ISO set contains well-known codes."""
    for code in ("US", "GB", "FR", "DE", "JP", "CN", "AU", "CA", "BR", "IN"):
        assert code in _ISO_3166_ALPHA2
