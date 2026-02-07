import json
import urllib.request


_IPINFO_URL = "https://ipinfo.io/json"


def my_public_ip_address() -> str:
    """Get your current public IP address, physical location, and ISP name.

    Queries ipinfo.io to retrieve the caller's public-facing
    network information.

    Returns:
        JSON string with `public_ip`, `physical_location`, and `isp_name`.
    """
    req = urllib.request.Request(_IPINFO_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    # ISP is in the "org" field, typically prefixed with AS number (e.g. "AS7018 AT&T")
    org = data.get("org", "")
    isp_name = org.split(" ", 1)[1] if " " in org else org

    result = {
        "public_ip": data.get("ip", ""),
        "physical_location": {
            "country": data.get("country", ""),
            "state_province": data.get("region", ""),
            "city": data.get("city", ""),
        },
        "isp_name": isp_name,
    }

    return json.dumps(result, indent=2)


def my_approximate_physical_location() -> str:
    """Get your current approximate physical location based on your public IP.

    Returns:
        JSON string with `country`, `state_province`, and `city`.
    """
    data = json.loads(my_public_ip_address())
    return json.dumps(data["physical_location"], indent=2)
