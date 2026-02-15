"""Weather forecast utilities (US only, via weather.gov)."""

import re
import subprocess
import urllib.request
from typing import Any

_NWS_URL = "https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}"

_USER_AGENT = "python-mcp-tools/1.0"

# Countries that officially use Fahrenheit.
# Keyed by alpha-2; alpha-3 mapped below.
_FAHRENHEIT_ALPHA2 = {
    "US",  # United States
    "BS",  # Bahamas
    "KY",  # Cayman Islands
    "LR",  # Liberia
    "PW",  # Palau
    "FM",  # Micronesia
    "MH",  # Marshall Islands
}

# ISO 3166-1 alpha-3 → alpha-2 for Fahrenheit countries.
_ALPHA3_TO_ALPHA2: dict[str, str] = {
    "USA": "US",
    "BHS": "BS",
    "CYM": "KY",
    "LBR": "LR",
    "PLW": "PW",
    "FSM": "FM",
    "MHL": "MH",
}


# ── temperature helpers ──────────────────────────────


def _f_to_c(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius, rounded."""
    return round((fahrenheit - 32) * 5 / 9, 1)


def _prefer_celsius() -> bool:
    """Check if the system prefers Celsius.

    On macOS, reads AppleTemperatureUnit first, then
    falls back to AppleMeasurementUnits, then locale.
    """
    try:
        r = subprocess.run(
            [
                "defaults",
                "read",
                "NSGlobalDomain",
                "AppleTemperatureUnit",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if r.returncode == 0:
            return r.stdout.strip() == "Celsius"

        r = subprocess.run(
            [
                "defaults",
                "read",
                "NSGlobalDomain",
                "AppleMeasurementUnits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if r.returncode == 0:
            return r.stdout.strip() == "Centimeters"
    except OSError:
        pass

    import locale

    loc = locale.getlocale()[0] or ""
    if "_" in loc:
        country = loc.split("_")[1][:2].upper()
        return country not in _FAHRENHEIT_ALPHA2
    return False


def _convert_temp_str(text: str, celsius: bool) -> str:
    """Replace °F values with °C in a string."""
    if not celsius:
        return text

    def _repl(m: re.Match[str]) -> str:
        return f"{_f_to_c(float(m.group(1)))}°C"

    return re.sub(r"(-?\d+)\s*°F", _repl, text)


def _extract_temp_number(text: str) -> float | None:
    """Pull the first integer from a temperature string."""
    m = re.search(r"(-?\d+)", text)
    return float(m.group(1)) if m else None


# ── HTML helpers ─────────────────────────────────────


def _strip_tags(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    for entity, char in (
        ("&deg;", "°"),
        ("&#176;", "°"),
        ("&amp;", "&"),
        ("&nbsp;", " "),
    ):
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


def _html_to_markdown(html: str) -> str:
    """Basic HTML-to-Markdown conversion for weather page.

    Strips scripts/styles, converts headings, paragraphs,
    line breaks, and table rows into readable Markdown text.
    """
    text = re.sub(
        r"<(script|style)[^>]*>.*?</\1>",
        "",
        html,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"<h[1-6][^>]*>(.*?)</h[1-6]>",
        r"\n## \1\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"</tr>", "\n", text)
    text = re.sub(r"</td>", " | ", text)
    text = re.sub(r"<li[^>]*>", "- ", text)
    text = re.sub(r"<[^>]+>", "", text)
    for entity, char in (
        ("&deg;", "°"),
        ("&#176;", "°"),
        ("&amp;", "&"),
        ("&nbsp;", " "),
    ):
        text = text.replace(entity, char)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ── page extraction ──────────────────────────────────


def _find(pattern: str, html: str) -> str:
    """Search HTML for pattern, return group(1) stripped."""
    m = re.search(pattern, html, re.DOTALL)
    return _strip_tags(m.group(1)) if m else ""


def _parse_current(html: str) -> dict[str, Any]:
    """Extract current conditions from NWS page HTML."""
    current: dict[str, Any] = {}

    temp = _find(
        r'class="myforecast-current-lrg"[^>]*>(.*?)</p>',
        html,
    )
    if temp:
        current["temperature"] = temp

    # Conditions text (e.g. "Showers", "Partly Cloudy")
    # is in "myforecast-current" (without -lrg / -sm)
    cond = _find(
        r'class="myforecast-current"[^>]*>(.*?)</p>',
        html,
    )
    if cond and cond != "NA":
        current["conditions"] = cond

    # Detail table (humidity, wind, pressure, etc.)
    detail_m = re.search(
        r'id="current_conditions_detail"[^>]*>(.*?)</div>',
        html,
        re.DOTALL,
    )
    if detail_m:
        rows = re.findall(
            r"<tr>(.*?)</tr>",
            detail_m.group(1),
            re.DOTALL,
        )
        for row in rows:
            cells = re.findall(
                r"<td[^>]*>(.*?)</td>",
                row,
                re.DOTALL,
            )
            if len(cells) >= 2:
                key = _strip_tags(cells[0])
                val = _strip_tags(cells[1])
                if key:
                    k = key.lower().replace(" ", "_")
                    current[k] = val

    return current


def _parse_forecast(html: str) -> list[dict[str, str]]:
    """Extract forecast periods from NWS page HTML."""
    periods: list[dict[str, str]] = []

    tombstones = re.findall(
        r'class="tombstone-container"[^>]*>(.*?)</div>',
        html,
        re.DOTALL,
    )

    for tomb in tombstones:
        period: dict[str, str] = {}

        name = _find(r'class="period-name"[^>]*>(.*?)</p>', tomb)
        if name:
            period["name"] = name

        summary = _find(r'class="short-desc"[^>]*>(.*?)</p>', tomb)
        if summary:
            period["summary"] = summary

        temp = _find(r'class="temp[^"]*"[^>]*>(.*?)</p>', tomb)
        if temp:
            period["temperature"] = temp

        # img alt has the best detailed description
        alt_m = re.search(r'<img[^>]+alt="([^"]*)"', tomb, re.DOTALL)
        if alt_m:
            period["detail"] = alt_m.group(1)

        if period.get("name"):
            periods.append(period)

    return periods


# ── public function ──────────────────────────────────


def current_with_forecast(
    latitude: float,
    longitude: float,
    unit: str = "",
) -> dict[str, Any]:
    """Get current weather and forecast for a US location.

    Queries the National Weather Service forecast page and
    parses the HTML response. Only works for US coordinates.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        unit: Temperature unit — "c", "celsius", "f", or
              "fahrenheit". If blank, uses system settings.

    Returns:
        Dict with `location`, `current` conditions, `forecast`
        periods, and `unit` (celsius or fahrenheit).
    """
    url = _NWS_URL.format(lat=latitude, lon=longitude)
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"error": f"Failed to fetch weather: {e}"}

    # Convert to markdown as intermediate representation
    markdown = _html_to_markdown(html)

    # Check if the page returned usable data
    if not markdown or "forecast" not in markdown.lower():
        return {
            "error": (
                "No forecast data found. Coordinates may "
                "be outside the US or invalid."
            )
        }

    # Extract location
    location = _find(r'<h2 class="panel-title"[^>]*>(.*?)</h2>', html)

    # Resolve temperature unit
    norm = unit.strip().lower()
    if norm in ("c", "celsius"):
        celsius = True
    elif norm in ("f", "fahrenheit"):
        celsius = False
    else:
        celsius = _prefer_celsius()

    current = _parse_current(html)
    forecast = _parse_forecast(html)

    # Convert temperatures if needed
    if celsius:
        if "temperature" in current:
            current["temperature"] = _convert_temp_str(
                current["temperature"], celsius=True
            )
        for period in forecast:
            if "temperature" in period:
                period["temperature"] = _convert_temp_str(
                    period["temperature"], celsius=True
                )
            if "detail" in period:
                period["detail"] = _convert_temp_str(
                    period["detail"], celsius=True
                )

    return {
        "location": location,
        "current": current,
        "forecast": forecast,
        "unit": "celsius" if celsius else "fahrenheit",
    }


def temperature_unit_for_country(
    country_code: str,
) -> dict[str, str]:
    """Get the default temperature unit for a country.

    Args:
        country_code: ISO 3166-1 alpha-2 (e.g. "US") or
              alpha-3 (e.g. "USA") country code.
              Case insensitive.

    Returns:
        Dict with `country_code` and `default_unit`
        ("celsius" or "fahrenheit").
    """
    upper = country_code.strip().upper()

    # Normalize alpha-3 to alpha-2
    if len(upper) == 3:
        upper = _ALPHA3_TO_ALPHA2.get(upper, upper)

    unit = "fahrenheit" if upper in _FAHRENHEIT_ALPHA2 else "celsius"
    return {
        "country_code": upper,
        "default_unit": unit,
    }
