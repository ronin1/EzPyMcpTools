"""Date and time utilities."""
from datetime import datetime
from zoneinfo import ZoneInfo

import json


def _get_country_codes() -> dict[str, str]:
    """Parse iso3166.tab to build a country-name -> country-code mapping."""
    mapping = {}
    with open("/usr/share/zoneinfo/iso3166.tab") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            code, name = line.strip().split("\t", 1)
            mapping[name.lower()] = code
    return mapping


def _get_zone_tab() -> dict[str, list[str]]:
    """Parse zone.tab to build a country-code -> timezones mapping."""
    mapping: dict[str, list[str]] = {}
    with open("/usr/share/zoneinfo/zone.tab") as f:
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

    loc = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
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


def get_current_datetime(time_zone: str = "") -> str:
    """Get the current date and time in JSON format.

    Args:
        time_zone: IANA time zone name (e.g. "America/New_York", "Asia/Tokyo").
                   If blank, the system's local timezone is used.

    Returns:
        JSON string with `current_date_time` in ISO 8601 format and
        `timezone` metadata.
    """
    if time_zone:
        tz = ZoneInfo(time_zone)
    else:
        tz = datetime.now().astimezone().tzinfo

    now = datetime.now(tz)

    result = {
        "current_date_time": now.isoformat(),
        "timezone": {
            "name": time_zone if time_zone else str(tz),
            "utc_offset": now.strftime("%z"),
        },
    }

    return json.dumps(result, indent=2)


def configured_timezone() -> str:
    """Get the currently configured timezone.

    Returns:
        JSON string with the currently configured timezone.
    """
    return get_timezones()


def get_timezones(country_code: str = "") -> str:
    """Get all timezones for a country.

    Args:
        country_code: ISO 3166 country code (e.g. "US", "JP", "VN").
                      If blank, detects from system locale.

    Returns:
        JSON string with the country code and its timezones.
    """
    if not country_code:
        country_code = _detect_country_code_from_locale()
        if not country_code:
            return json.dumps({"error": "Could not detect country from locale."})

    country_code = country_code.upper()

    zone_tab = _get_zone_tab()
    if country_code not in zone_tab:
        return json.dumps(
            {"error": f"Unknown country code: '{country_code}'"},
            indent=2,
        )

    timezones = zone_tab[country_code]
    country_name = _get_country_name(country_code)

    result = {
        "country": country_name,
        "country_code": country_code,
        "timezones": sorted(timezones),
        "count": len(timezones),
    }

    return json.dumps(result, indent=2)
