"""Current user's personal information utilities."""

import json
import os
import pathlib
import pwd
import subprocess
from datetime import date
from typing import Any


def _get_full_name() -> str:
    """Get the current user's full name across macOS/Linux.

    Preference order:
      1) POSIX account GECOS field
      2) macOS `id -F`
      3) Linux `getent passwd <user>` GECOS field
      4) Fallback to username
    """
    # 1) POSIX account metadata (works in most Unix environments,
    # including Alpine).
    try:
        gecos = pwd.getpwuid(os.getuid()).pw_gecos.split(",", 1)[0].strip()
        if gecos:
            return gecos
    except (KeyError, OSError, AttributeError):
        pass

    # 2) macOS full name.
    try:
        result = subprocess.run(
            ["id", "-F"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except OSError:
        pass

    # 3) Linux NSS database lookup as fallback.
    user = ""
    try:
        user = _get_username()
        result = subprocess.run(
            ["getent", "passwd", user],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(":")
            if len(parts) >= 5:
                full_name = parts[4].split(",", 1)[0].strip()
                if full_name:
                    return full_name
    except (OSError, subprocess.CalledProcessError):
        pass

    # 4) Last resort.
    if user:
        return user
    try:
        return _get_username()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _get_username() -> str:
    """Get the current Unix username."""
    result = subprocess.run(
        ["id", "-un"],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    return result.stdout.strip()


def _compute_age(birthday: str) -> int:
    """Compute age from a birthday string (YYYY-MM-DD)."""
    born = date.fromisoformat(birthday)
    today = date.today()
    return (
        today.year
        - born.year
        - ((today.month, today.day) < (born.month, born.day))
    )


_CONFIG_PATH = pathlib.Path(__file__).parent.parent / "user.data.json"
_REQUIRED_FIELDS = ["birthday", "email", "phone", "addresss"]


def _is_missing(field: str, value: Any) -> bool:
    """Return True if a required field value is missing/invalid."""
    if field == "name":
        if isinstance(value, dict):
            first = str(value.get("first", "")).strip()
            last = str(value.get("last", "")).strip()
            middle = str(value.get("middle", "")).strip()
            return not any([first, middle, last])
        return not str(value or "").strip()

    if field == "addresss":
        if not isinstance(value, list):
            return True
        return not any(str(item).strip() for item in value)

    return not value


def _ask_user(
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prompt the user for required personal info fields.

    Args:
        existing: Previously saved data (if any). Only missing
                  fields will be prompted.

    Returns:
        Complete dict with all required fields filled in.
    """
    data: dict[str, Any] = dict(existing) if existing else {}

    for field in _REQUIRED_FIELDS:
        if not _is_missing(field, data.get(field)):
            continue

        if field == "addresss":
            print(
                f"\n{field} (enter one address per line, blank line to stop):"
            )
            addresses: list[str] = []
            while True:
                addr = input("  address> ").strip()
                if not addr:
                    if not addresses:
                        print("  (at least one address required)")
                        continue
                    break
                addresses.append(addr)
            data[field] = addresses
        elif field == "birthday":
            while True:
                val = input(f"\n{field} (YYYY-MM-DD): ").strip()
                try:
                    date.fromisoformat(val)
                    data[field] = val
                    break
                except ValueError:
                    print("  Invalid date format. Use YYYY-MM-DD.")
        else:
            val = input(f"\n{field}: ").strip()
            data[field] = val

    return data


def _ensure_user_info() -> None:
    """Create or update user.data.json interactively.

    If the file doesn't exist or is missing required fields,
    prompt the user to fill them in.
    """
    existing: dict[str, Any] = {}
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            existing = json.load(f)

    missing = [
        f
        for f in _REQUIRED_FIELDS
        if f not in existing or _is_missing(f, existing.get(f))
    ]

    if not missing:
        print(f"{_CONFIG_PATH} already has all required fields.")
        return

    print("Setting up user.data.json...")
    if existing:
        print(f"Missing fields: {', '.join(missing)}")

    data = _ask_user(existing)

    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"\nSaved to {_CONFIG_PATH}")


def personal_data() -> dict[str, Any]:
    """Get current user's personal data.

    Returns:
        Dict with `name`, `long_name`, `birthday`, `age`, `email`,
        `phone`, and `addresss`.
    """
    if not _CONFIG_PATH.exists():
        missing = _REQUIRED_FIELDS
        data: dict[str, Any] = {}
    else:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        missing = [
            f
            for f in _REQUIRED_FIELDS
            if f not in data or _is_missing(f, data.get(f))
        ]

    if missing:
        raise FileNotFoundError(
            f"{_CONFIG_PATH} is missing or incomplete. "
            f"Run 'make user_info' to set it up. "
            f"Missing fields: {', '.join(missing)}"
        )

    raw_name = data.get("name")
    if _is_missing("name", raw_name):
        resolved_name: Any = _get_username()
        resolved_long_name = _get_full_name()
    else:
        resolved_name = raw_name
        if isinstance(raw_name, dict):
            first = str(raw_name.get("first", "")).strip()
            middle = str(raw_name.get("middle", "")).strip()
            last = str(raw_name.get("last", "")).strip()
            joined = " ".join(
                part for part in [first, middle, last] if part
            ).strip()
            resolved_long_name = joined or _get_full_name()
        else:
            resolved_long_name = str(raw_name).strip() or _get_full_name()

    info: dict[str, Any] = {
        "name": resolved_name,
        "long_name": resolved_long_name,
    }
    info.update(data)
    # Preserve computed/normalized identity fields over raw file values.
    info["name"] = resolved_name
    info["long_name"] = resolved_long_name
    info["age"] = _compute_age(str(info["birthday"]))
    return info
