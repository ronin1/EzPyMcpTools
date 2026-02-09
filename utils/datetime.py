"""Date and time utilities."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def _get_country_codes() -> dict[str, str]:
    """Parse iso3166.tab to build a country-name -> country-code mapping."""
    mapping = {}
    with open("/usr/share/zoneinfo/iso3166.tab", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            code, name = line.strip().split("\t", 1)
            mapping[name.lower()] = code
    return mapping


def _get_zone_tab() -> dict[str, list[str]]:
    """Parse zone.tab to build a country-code -> timezones mapping."""
    mapping: dict[str, list[str]] = {}
    with open("/usr/share/zoneinfo/zone.tab", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            code, tz_name = parts[0], parts[2]
            mapping.setdefault(code, []).append(tz_name)
    return mapping


def _detect_country_code_from_locale() -> str:
    """Detect country code from the system locale."""
    import locale

    loc: str = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    # Locale is like "en_US" — extract the country code part
    if "_" in loc:
        return loc.split("_")[1][:2].upper()
    return ""


def _get_country_name(code: str) -> str:
    """Look up a country name by its ISO 3166 code."""
    country_codes = _get_country_codes()
    for name, c in country_codes.items():
        if c == code:
            return name.title()
    return ""


def current(time_zone: str = "") -> dict[str, Any]:
    """Get the current date and time.

    Args:
        time_zone: IANA time zone name (e.g. "America/New_York",
                   "Asia/Tokyo"). If blank, the system's local
                   timezone is used.

    Returns:
        Dict with `date_time` (containing `value` in AM/PM format,
        `iso8601`, and `unix_timestamp`) and `timezone` (containing
        IANA `name`, `code` abbreviation, and `utc_offset`).
    """
    tz = (
        ZoneInfo(time_zone) if time_zone else datetime.now().astimezone().tzinfo
    )
    now = datetime.now(tz)

    return {
        "date_time": {
            "value": now.strftime("%Y-%m-%d %I:%M:%S %p"),
            "iso8601": now.isoformat(),
            "unix_timestamp": now.timestamp(),
        },
        "timezone": {
            "name": _get_local_iana_timezone(),
            "code": time_zone if time_zone else str(tz),
            "utc_offset": now.strftime("%z"),
        },
    }


def _get_local_iana_timezone() -> str:
    """Get the local IANA timezone name."""
    import os
    import time

    # Check TZ env var first
    tz_env = os.environ.get("TZ", "")
    if tz_env:
        return tz_env

    # macOS: read /etc/localtime symlink
    link = "/etc/localtime"
    if os.path.islink(link):
        target = os.path.realpath(link)
        # e.g. /usr/share/zoneinfo/America/Los_Angeles
        marker = "/zoneinfo/"
        if marker in target:
            return target.split(marker, 1)[1]

    # Fallback to abbreviation
    return time.tzname[0]


def configured_timezone() -> dict[str, str]:
    """Get the currently configured local timezone.

    Returns:
        Dict with `timezone_name` as the IANA timezone
        identifier (e.g. "America/Los_Angeles").
    """
    return {"timezone_name": _get_local_iana_timezone()}


def country_timezones(country_code: str = "") -> dict[str, Any]:
    """Get all timezones for a country.

    Args:
        country_code: ISO 3166 country code (e.g. "US", "JP",
                      "VN"). If blank, detects from system locale.

    Returns:
        Dict with `country`, `country_code`, `count`, and
        `timezones` list (each with IANA `name`, `code`
        abbreviation, and `utc_offset`).
    """
    if not country_code:
        country_code = _detect_country_code_from_locale()
        if not country_code:
            return {"error": "Could not detect country from locale."}

    country_code = country_code.upper()

    zone_tab = _get_zone_tab()
    if country_code not in zone_tab:
        return {"error": f"Unknown country code: '{country_code}'"}

    tz_names = zone_tab[country_code]
    country_name = _get_country_name(country_code)

    timezones: list[dict[str, str]] = []
    for name in sorted(tz_names):
        tz = ZoneInfo(name)
        now = datetime.now(tz)
        timezones.append(
            {
                "name": name,
                "code": now.strftime("%Z"),
                "utc_offset": now.strftime("%z"),
            }
        )

    return {
        "country": country_name,
        "country_code": country_code,
        "timezones": timezones,
        "count": len(timezones),
    }
