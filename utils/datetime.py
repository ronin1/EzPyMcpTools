"""Date and time utilities."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

# Common abbreviation -> IANA timezone mapping.
# Many abbreviations are ambiguous (e.g. CST = US Central,
# China Standard, or Cuba Standard). This maps to the most
# commonly expected IANA zone for each.
_ABBREV_TO_IANA: dict[str, str] = {
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "AKST": "America/Anchorage",
    "AKDT": "America/Anchorage",
    "HST": "Pacific/Honolulu",
    "AST": "America/Puerto_Rico",
    "NST": "America/St_Johns",
    "NDT": "America/St_Johns",
    "GMT": "Europe/London",
    "UTC": "UTC",
    "BST": "Europe/London",
    "CET": "Europe/Paris",
    "CEST": "Europe/Paris",
    "EET": "Europe/Bucharest",
    "EEST": "Europe/Bucharest",
    "WET": "Europe/Lisbon",
    "WEST": "Europe/Lisbon",
    "IST": "Asia/Kolkata",
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",
    "CST_CN": "Asia/Shanghai",
    "HKT": "Asia/Hong_Kong",
    "SGT": "Asia/Singapore",
    "PHT": "Asia/Manila",
    "ICT": "Asia/Bangkok",
    "WIB": "Asia/Jakarta",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "ACST": "Australia/Adelaide",
    "ACDT": "Australia/Adelaide",
    "AWST": "Australia/Perth",
    "NZST": "Pacific/Auckland",
    "NZDT": "Pacific/Auckland",
}


def _resolve_timezone(
    time_zone: str,
) -> ZoneInfo | None:
    """Resolve a timezone string to a ZoneInfo object.

    Accepts IANA names (contains '/') or common
    abbreviations (e.g. PST, EST, JST). Returns None
    if the timezone cannot be resolved.
    """
    if not time_zone:
        return None

    # IANA format (contains a slash, e.g. "America/New_York")
    if "/" in time_zone:
        try:
            return ZoneInfo(time_zone)
        except (KeyError, ValueError):
            return None

    # Try abbreviation lookup (case-insensitive)
    upper = time_zone.upper()
    iana = _ABBREV_TO_IANA.get(upper)
    if iana:
        return ZoneInfo(iana)

    # Try as-is in case it's a valid IANA key (e.g. "UTC")
    if time_zone in available_timezones():
        return ZoneInfo(time_zone)

    return None


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
        time_zone: IANA name (e.g. "America/New_York") or common
                   abbreviation (e.g. "PST", "EST", "JST"). If
                   blank, the system's local timezone is used.

    Returns:
        Dict with `date_time` (containing `value` in AM/PM format,
        `iso8601`, and `unix_timestamp`) and `timezone` (containing
        IANA `name`, `code` abbreviation, and `utc_offset`).
    """
    if time_zone:
        tz = _resolve_timezone(time_zone)
        if tz is None:
            return {
                "error": (
                    f"Unknown timezone: '{time_zone}'. "
                    "Use an IANA name (e.g. "
                    "'America/New_York') or a common "
                    "abbreviation (e.g. 'PST', 'EST')."
                )
            }
    else:
        tz = datetime.now().astimezone().tzinfo

    now = datetime.now(tz)
    iana_name = tz.key if hasattr(tz, "key") else str(tz)

    return {
        "date_time": {
            "value": now.strftime("%Y-%m-%d %I:%M:%S %p"),
            "iso8601": now.isoformat(),
            "unix_timestamp": now.timestamp(),
        },
        "timezone": {
            "name": iana_name,
            "code": now.strftime("%Z"),
            "utc_offset": now.strftime("%z"),
        },
    }


def _get_local_iana_timezone() -> str:
    """Get the local IANA timezone name.

    Detection order:
      1. TZ environment variable
      2. /etc/localtime symlink (macOS & most Linux)
      3. /etc/timezone file (Debian/Ubuntu)
      4. timedatectl (systemd-based Linux)
      5. Fallback to abbreviation
    """
    import os
    import time

    # 1. TZ env var
    tz_env = os.environ.get("TZ", "")
    if tz_env:
        return tz_env

    # 2. /etc/localtime symlink (macOS + many Linux)
    link = "/etc/localtime"
    if os.path.islink(link):
        target = os.path.realpath(link)
        marker = "/zoneinfo/"
        if marker in target:
            return target.split(marker, 1)[1]

    # 3. /etc/timezone (Debian/Ubuntu)
    tz_file = "/etc/timezone"
    if os.path.isfile(tz_file):
        with open(tz_file, encoding="utf-8") as f:
            tz = f.read().strip()
            if tz:
                return tz

    # 4. timedatectl (systemd-based Linux)
    import subprocess

    try:
        r = subprocess.run(
            ["timedatectl", "show", "-p", "Timezone", "--value"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except OSError:
        pass

    # 5. Fallback to abbreviation
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
