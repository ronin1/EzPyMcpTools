"""Tests for IP address utilities."""

from __future__ import annotations

from utils import ip_address


def test_public_ipv4_uses_mock_source(ipinfo_source_url: str) -> None:
    payload = ip_address.public_ipv4(source_url=ipinfo_source_url)
    assert payload["public_ip"] == "203.0.113.42"
    assert payload["isp_name"] == "Example ISP"
    assert payload["physical_location"]["city"] == "Los Angeles"


def test_approximate_physical_location_uses_mock_source(
    ipinfo_source_url: str,
) -> None:
    payload = ip_address.approximate_physical_location(
        source_url=ipinfo_source_url
    )
    assert payload["country"] == "US"
    assert payload["state_province"] == "California"
    assert payload["city"] == "Los Angeles"
