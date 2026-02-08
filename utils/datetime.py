"""Date and time utilities."""
from datetime import datetime
from zoneinfo import ZoneInfo


def _get_country_codes() -> dict[str, str]:
    """Parse iso3166.tab to build a country-name -> country-code mapping."""
    mapping = {}
    with open("/usr/share/zoneinfo/iso3166.tab", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            code, name = line.strip().split("\t", 1)
            mapping[name.lower()] = code
    return mapping


def _get_zone_tab() -> dict[str, list[str]]:
    """Parse zone.tab to build a country-code -> timezones mapping."""
    mapping: dict[str, list[str]] = {}
    with open("/usr/share/zoneinfo/zone.tab", "r", encoding="utf-8") as f:
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


def current(time_zone: str = "") -> dict:
    """Get the current date and time.

    Args:
        time_zone: IANA time zone name (e.g. "America/New_York", "Asia/Tokyo").
                   If blank, the system's local timezone is used.

    Returns:
        Dict with `current_date_time` in ISO 8601 format and
        `timezone` metadata.
    """
    tz = ZoneInfo(time_zone) \
        if time_zone else datetime.now().astimezone().tzinfo
    now = datetime.now(tz)

    return {
        "date_time": {
            "value": now.strftime("%Y-%m-%d %I:%M:%S %p"),
            "iso8601": now.isoformat(),
            "unix_timestamp": now.timestamp(),
        },
        "timezone": {
            "name": time_zone if time_zone else str(tz),
            "utc_offset": now.strftime("%z"),
        },
    }


def configured_timezone() -> dict:
    """Get the currently configured timezone.

    Returns:
        Dict with the currently configured timezone.
    """
    return all_timezones()


def all_timezones(country_code: str = "") -> dict:
    """Get all timezones for a country.

    Args:
        country_code: ISO 3166 country code (e.g. "US", "JP", "VN").
                      If blank, detects from system locale.

    Returns:
        Dict with the country code and its timezones.
    """
    if not country_code:
        country_code = _detect_country_code_from_locale()
        if not country_code:
            return {"error": "Could not detect country from locale."}

    country_code = country_code.upper()

    zone_tab = _get_zone_tab()
    if country_code not in zone_tab:
        return {"error": f"Unknown country code: '{country_code}'"}

    timezones = zone_tab[country_code]
    country_name = _get_country_name(country_code)

    return {
        "country": country_name,
        "country_code": country_code,
        "timezones": sorted(timezones),
        "count": len(timezones),
    }
