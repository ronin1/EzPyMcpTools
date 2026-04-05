"""Date and time utilities."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

# Common abbreviation -> IANA timezone mapping.


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


# Common country name -> ISO 3166-1 alpha-2 mapping.
# Used as fallback when /usr/share/zoneinfo/iso3166.tab is not available.
# Covers ~200 countries (99% of use cases).
_ISO_3166_COUNTRIES: dict[str, str] = {
    "afghanistan": "af",
    "albania": "al",
    "algeria": "dz",
    "andorra": "ad",
    "angola": "ao",
    "argentina": "ar",
    "armenia": "am",
    "australia": "au",
    "austria": "at",
    "azerbaijan": "az",
    "bahamas": "bs",
    "bahrain": "bh",
    "bangladesh": "bd",
    "barbados": "bb",
    "belarus": "by",
    "belgium": "be",
    "belize": "bz",
    "benin": "bj",
    "bhutan": "bt",
    "bolivia": "bo",
    "bosnia and herzegovina": "ba",
    "botswana": "bw",
    "brazil": "br",
    "brunei": "bn",
    "bulgaria": "bg",
    "burkina faso": "bf",
    "burundi": "bi",
    "cabo verde": "cv",
    "cambodia": "kh",
    "cameroon": "cm",
    "canada": "ca",
    "central african republic": "cf",
    "chad": "td",
    "chile": "cl",
    "china": "cn",
    "colombia": "co",
    "comoros": "km",
    "congo": "cg",
    "costa rica": "cr",
    "croatia": "hr",
    "cuba": "cu",
    "cyprus": "cy",
    "czech republic": "cz",
    "denmark": "dk",
    "djibouti": "dj",
    "dominica": "dm",
    "dominican republic": "do",
    "ecuador": "ec",
    "egypt": "eg",
    "el salvador": "sv",
    "equatorial guinea": "gq",
    "eritrea": "er",
    "estonia": "ee",
    "eswatini": "sz",
    "ethiopia": "et",
    "fiji": "fj",
    "finland": "fi",
    "france": "fr",
    "gabon": "ga",
    "gambia": "gm",
    "georgia": "ge",
    "germany": "de",
    "ghana": "gh",
    "greece": "gr",
    "grenada": "gd",
    "guatemala": "gt",
    "guinea": "gn",
    "guyana": "gy",
    "haiti": "ht",
    "honduras": "hn",
    "hungary": "hu",
    "iceland": "is",
    "india": "in",
    "indonesia": "id",
    "iran": "ir",
    "iraq": "iq",
    "ireland": "ie",
    "israel": "il",
    "italy": "it",
    "jamaica": "jm",
    "japan": "jp",
    "jordan": "jo",
    "kazakhstan": "kz",
    "kenya": "ke",
    "kiribati": "ki",
    "korea north": "kp",
    "korea south": "kr",
    "kuwait": "kw",
    "kyrgyzstan": "kg",
    "laos": "la",
    "latvia": "lv",
    "lebanon": "lb",
    "lesotho": "ls",
    "liberia": "lr",
    "libya": "ly",
    "liechtenstein": "li",
    "lithuania": "lt",
    "luxembourg": "lu",
    "madagascar": "mg",
    "malawi": "mw",
    "malaysia": "my",
    "maldives": "mv",
    "mali": "ml",
    "malta": "mt",
    "marshall islands": "mh",
    "mauritania": "mr",
    "mauritius": "mu",
    "mexico": "mx",
    "micronesia": "fm",
    "moldova": "md",
    "monaco": "mc",
    "mongolia": "mn",
    "montenegro": "me",
    "morocco": "ma",
    "mozambique": "mz",
    "myanmar": "mm",
    "namibia": "na",
    "nauru": "nr",
    "nepal": "np",
    "netherlands": "nl",
    "new zealand": "nz",
    "nicaragua": "ni",
    "niger": "ne",
    "nigeria": "ng",
    "north macedonia": "mk",
    "norway": "no",
    "oman": "om",
    "pakistan": "pk",
    "palau": "pw",
    "palestine": "ps",
    "panama": "pa",
    "papua new guinea": "pg",
    "paraguay": "py",
    "peru": "pe",
    "philippines": "ph",
    "poland": "pl",
    "portugal": "pt",
    "qatar": "qa",
    "romania": "ro",
    "russia": "ru",
    "rwanda": "rw",
    "saint kitts and nevis": "kn",
    "saint lucia": "lc",
    "saint vincent and the grenadines": "vc",
    "samoa": "ws",
    "san marino": "sm",
    "sao tome and principe": "st",
    "saudi arabia": "sa",
    "senegal": "sn",
    "serbia": "rs",
    "seychelles": "sc",
    "sierra leone": "sl",
    "singapore": "sg",
    "slovakia": "sk",
    "slovenia": "si",
    "solomon islands": "sb",
    "somalia": "so",
    "south africa": "za",
    "south sudan": "ss",
    "spain": "es",
    "sri lanka": "lk",
    "sudan": "sd",
    "suriname": "sr",
    "sweden": "se",
    "switzerland": "ch",
    "syria": "sy",
    "taiwan": "tw",
    "tajikistan": "tj",
    "tanzania": "tz",
    "thailand": "th",
    "timor leste": "tl",
    "togo": "tg",
    "tonga": "to",
    "trinidad and tobago": "tt",
    "tunisia": "tn",
    "turkey": "tr",
    "turkmenistan": "tm",
    "tuvalu": "tv",
    "uganda": "ug",
    "ukraine": "ua",
    "united arab emirates": "ae",
    "united kingdom": "gb",
    "united states": "us",
    "uruguay": "uy",
    "uzbekistan": "uz",
    "vanuatu": "vu",
    "vatican city": "va",
    "venezuela": "ve",
    "vietnam": "vn",
    "yemen": "ye",
    "zambia": "zm",
    "zimbabwe": "zw",
}


def _get_country_codes() -> dict[str, str]:
    """Parse iso3166.tab to build a country-name -> country-code mapping.

    Tries to read from system file first, falls back to embedded mapping.
    """
    try:
        with open("/usr/share/zoneinfo/iso3166.tab", encoding="utf-8") as f:
            mapping: dict[str, str] = {}
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                code, name = line.strip().split("\t", 1)
                mapping[name.lower()] = code.upper()
            return mapping
    except (FileNotFoundError, OSError):
        return {k: v.upper() for k, v in _ISO_3166_COUNTRIES.items()}


def _get_zone_tab() -> dict[str, list[str]]:
    """Parse zone.tab to build a country-code -> timezones mapping.

    Tries to read from system file first, falls back to embedded mapping.
    """
    try:
        mapping: dict[str, list[str]] = {}
        with open("/usr/share/zoneinfo/zone.tab", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.strip().split("\t")
                code, tz_name = parts[0], parts[2]
                mapping.setdefault(code, []).append(tz_name)
        return mapping
    except (FileNotFoundError, OSError):
        # Fallback: common timezones by country (non-exhaustive)
        return {
            "US": [
                "America/New_York",
                "America/Chicago",
                "America/Denver",
                "America/Los_Angeles",
                "America/Anchorage",
                "Pacific/Honolulu",
                "America/Phoenix",
                "America/Indiana/Indianapolis",
            ],
            "CA": [
                "America/Toronto",
                "America/Vancouver",
                "America/Winnipeg",
                "America/Edmonton",
                "America/Halifax",
                "America/St_Johns",
            ],
            "GB": ["Europe/London"],
            "FR": ["Europe/Paris"],
            "DE": ["Europe/Berlin"],
            "IT": ["Europe/Rome"],
            "ES": ["Europe/Madrid"],
            "JP": ["Asia/Tokyo"],
            "AU": ["Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane"],
            "CN": ["Asia/Shanghai"],
            "IN": ["Asia/Kolkata"],
            "BR": ["America/Sao_Paulo"],
            "MX": ["America/Mexico_City"],
            "RU": ["Europe/Moscow"],
            "ZA": ["Africa/Johannesburg"],
            "EG": ["Africa/Cairo"],
            "AE": ["Asia/Dubai"],
            "SA": ["Asia/Riyadh"],
            "AR": ["America/Argentina/Buenos_Aires"],
            "CL": ["America/Santiago"],
            "CO": ["America/Bogota"],
            "PE": ["America/Lima"],
            "VE": ["America/Caracas"],
            "NL": ["Europe/Amsterdam"],
            "BE": ["Europe/Brussels"],
            "SE": ["Europe/Stockholm"],
            "NO": ["Europe/Oslo"],
            "DK": ["Europe/Copenhagen"],
            "FI": ["Europe/Helsinki"],
            "PL": ["Europe/Warsaw"],
            "AT": ["Europe/Vienna"],
            "CH": ["Europe/Zurich"],
            "PT": ["Europe/Lisbon"],
            "GR": ["Europe/Athens"],
            "CZ": ["Europe/Prague"],
            "HU": ["Europe/Budapest"],
            "RO": ["Europe/Bucharest"],
            "SK": ["Europe/Bratislava"],
            "BG": ["Europe/Sofia"],
            "HR": ["Europe/Zagreb"],
            "SI": ["Europe/Ljubljana"],
            "LT": ["Europe/Vilnius"],
            "LV": ["Europe/Riga"],
            "EE": ["Europe/Tallinn"],
            "UA": ["Europe/Kyiv"],
            "TR": ["Europe/Istanbul"],
            "IL": ["Asia/Jerusalem"],
            "KZ": ["Asia/Almaty"],
            "SG": ["Asia/Singapore"],
            "TH": ["Asia/Bangkok"],
            "MY": ["Asia/Kuala_Lumpur"],
            "PH": ["Asia/Manila"],
            "ID": ["Asia/Jakarta"],
            "VN": ["Asia/Ho_Chi_Minh"],
            "NG": ["Africa/Lagos"],
            "KE": ["Africa/Nairobi"],
            "ET": ["Africa/Addis_Ababa"],
            "MA": ["Africa/Casablanca"],
            "DZ": ["Africa/Algiers"],
            "TN": ["Africa/Tunis"],
        }


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
        try:
            from utils.user_information import personal_data

            user_info = personal_data()
            user_tz = (user_info.get("timezone", "") or "").strip()
            tz = None
            if user_tz:
                tz = _resolve_timezone(user_tz)
            if tz is None:
                tz = datetime.now().astimezone().tzinfo
                if tz is None:
                    tz = ZoneInfo("UTC")
        except Exception:
            tz = datetime.now().astimezone().tzinfo
            if tz is None:
                tz = ZoneInfo("UTC")

    now = datetime.now(tz)
    iana_name = str(tz)

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
    from utils._timezone_utils import _get_local_iana_timezone as _get_local_iana_timezone_impl

    return _get_local_iana_timezone_impl()


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
