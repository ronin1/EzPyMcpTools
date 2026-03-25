"""Geographical location utilities using GeoNames.org Web UI."""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any

# fmt: off
_ISO_3166_ALPHA2: set[str] = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT",
    "AU", "AW", "AX", "AZ", "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI",
    "BJ", "BL", "BM", "BN", "BO", "BR", "BS", "BT", "BV", "BW", "BY", "BZ",
    "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO",
    "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO",
    "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM",
    "FO", "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL", "GM",
    "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM", "HN",
    "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS",
    "IT", "JE", "JM", "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KP",
    "KR", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS", "LT",
    "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK", "ML",
    "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX",
    "MY", "MZ", "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR",
    "NU", "NZ", "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM", "PN",
    "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW", "SA",
    "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN",
    "SO", "SR", "SS", "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF", "TG",
    "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW", "TZ",
    "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI", "VN",
    "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW",
}
# fmt: on

_SMALL_SENTINEL = "\x00"


class _GeoNamesParser(HTMLParser):
    """HTML parser for GeoNames search results.

    The country column HTML uses a consistent structure across all countries:
        <a>Country</a>, State/Province<small>Detail > ... > City</small>
    A sentinel character is injected when <small> opens so _parse_country
    can split the main text (country, state) from the detail text (city).
    """

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, Any]] = []
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.in_geo_span = False
        self._geo_field: str = ""
        self.current_td_content: list[str] = []
        self.current_row: dict[str, str] = {}
        self.td_index = 0
        self.tr_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            attrs_dict = dict(attrs)
            if attrs_dict.get("class") == "restable":
                self.in_table = True
        elif self.in_table and tag == "tr":
            self.in_tr = True
            self.tr_count += 1
            if self.tr_count > 2:
                self.current_row = {}
                self.td_index = 0
        elif self.in_tr and self.tr_count > 2 and tag == "td":
            self.in_td = True
            self.current_td_content = []
        elif self.in_td and tag == "small" and self.td_index in (1, 2):
            self.current_td_content.append(_SMALL_SENTINEL)
        elif self.in_td and tag == "span":
            cls = dict(attrs).get("class", "")
            if cls == "geo":
                self.in_geo_span = True
            elif self.in_geo_span and cls in ("latitude", "longitude"):
                self._geo_field = cls

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self.in_table = False
        elif tag == "tr":
            self.in_tr = False
            if self.tr_count > 2 and self.current_row:
                self.results.append(self._process_row(self.current_row))
        elif tag == "td":
            self.in_td = False
            self.in_geo_span = False
            self._geo_field = ""
            content = "".join(self.current_td_content).strip()
            if self.tr_count > 2:
                if self.td_index == 1:
                    self.current_row["name"] = content
                elif self.td_index == 2:
                    self.current_row["country"] = content
                elif self.td_index == 3:
                    self.current_row["feature_class"] = content
                elif self.td_index == 4:
                    self.current_row["latitude"] = content
                elif self.td_index == 5:
                    self.current_row["longitude"] = content
            self.td_index += 1
        elif tag == "span" and self._geo_field:
            self._geo_field = ""

    def handle_data(self, data: str) -> None:
        if not self.in_td:
            return
        if self._geo_field:
            self.current_row[f"_{self._geo_field}"] = data.strip()
        elif not self.in_geo_span:
            self.current_td_content.append(data)

    # ------------------------------------------------------------------
    # Row post-processing
    # ------------------------------------------------------------------

    def _process_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Process a raw row to extract additional fields and format data."""
        processed = row.copy()

        # --- feature_class: extract elevation & population, then clean up ---
        fc = processed.get("feature_class", "")

        elevation_match = re.search(r"elevation\s+(\d+m)", fc)
        if elevation_match:
            processed["elevation"] = elevation_match.group(1)
            fc = re.sub(r"\s*elevation\s+\d+m", "", fc).strip()

        population_match = re.search(r"population\s+([\d,]+)", fc)
        if population_match:
            processed["population"] = population_match.group(1).replace(",", "")
            fc = re.sub(r"\s*population\s+[\d,]+", "", fc).strip()

        processed["feature_class"] = fc

        # --- country column → country_name, state_province, city_town ---
        country_info = self._parse_country(processed.get("country", ""))
        processed.update(country_info)

        # --- decimal coordinates from structured <span class="geo"> ---
        raw_lat = processed.pop("_latitude", "")
        raw_lon = processed.pop("_longitude", "")
        if raw_lat:
            processed["latitude_decimal"] = float(raw_lat)
        if raw_lon:
            processed["longitude_decimal"] = float(raw_lon)

        # --- primary name: before the sentinel (<small> alternate names) ---
        raw_name = processed.get("name", "")
        if _SMALL_SENTINEL in raw_name:
            raw_name = raw_name.split(_SMALL_SENTINEL, 1)[0]
        if raw_name:
            parts = re.split(r"\s*\u00a0\s*|\s{2,}", raw_name)
            processed["name"] = parts[0].strip()
        else:
            processed["name"] = ""

        processed.pop("country", None)
        processed.pop("latitude", None)
        processed.pop("longitude", None)

        return processed

    @staticmethod
    def _parse_country(country_str: str) -> dict[str, Any]:
        """Parse the country column into country_name, state_province, city_town.

        The raw text contains a sentinel (\\x00) at the boundary where the
        <small> tag starts in the HTML:
            "Country , State\\x00Detail > ... > City"
        """
        result: dict[str, Any] = {
            "city_town": "",
            "state_province": "",
            "country_name": "",
        }
        if not country_str:
            return result

        # Split on sentinel into main ("Country , State") and detail ("City > ...")
        if _SMALL_SENTINEL in country_str:
            main_part, detail_part = country_str.split(_SMALL_SENTINEL, 1)
        else:
            main_part, detail_part = country_str, ""

        # Main part: "Country , State" or just "Country"
        pieces = [p.strip() for p in main_part.split(",", 1)]
        result["country_name"] = pieces[0]
        if len(pieces) > 1 and pieces[1]:
            result["state_province"] = pieces[1]

        # Detail part: "Region > SubRegion > City" - last segment is the city
        if detail_part:
            segments = [s.strip() for s in detail_part.split(">")]
            city = segments[-1]
            if city:
                result["city_town"] = city

        return result


def _is_admin_division(feature_class: str) -> bool:
    """Return True if the feature class describes an administrative division."""
    return "administrative division" in feature_class.lower()


def coordinates_by_name(name: str, country: str = "", limit: int = 3) -> dict[str, Any]:
    """Get coordinates for a geographical name.

    Args:
        name: The geographical name to search for (city, mountain, etc.)
        country: Optional ISO 3166-1 alpha-2 country code to narrow results
        limit: Maximum number of results to return (1-20, default 3)

    Returns:
        Dict with search results containing geographical information including
        coordinates, or error message if validation fails.
    """
    limit = max(1, min(20, limit))

    if country:
        country = country.strip().upper()
        if country not in _ISO_3166_ALPHA2:
            return {
                "error": (
                    f"Unknown country code '{country}'. "
                    "Must be a valid ISO 3166-1 alpha-2 code (e.g. US, GB, FR)."
                )
            }

    query: dict[str, str] = {"q": name}
    if country:
        query["country"] = country
    url = f"https://www.geonames.org/search.html?{urllib.parse.urlencode(query)}"

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GeoNamesTool/1.0)"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            html_content = response.read().decode("utf-8")

        parser = _GeoNamesParser()
        parser.feed(html_content)

        results = sorted(
            parser.results, key=lambda r: _is_admin_division(r.get("feature_class", ""))
        )[:limit]

        for r in results:
            has_coords = "latitude_decimal" in r and "longitude_decimal" in r
            if not has_coords:
                r["error"] = "coordinates could not be extracted for this result"

        if not results or all("error" in r for r in results):
            return {
                "error": f"No results with extractable coordinates for '{name}'"
                + (f" in country '{country}'" if country else ""),
            }

        result_query: dict[str, str] = {"name": name}
        if country:
            result_query["country"] = country

        return {
            "query": result_query,
            "results": results,
            "count": len(results),
        }

    except urllib.error.URLError as e:
        return {"error": f"Failed to fetch data from GeoNames: {e!s}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e!s}"}
