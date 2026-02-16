"""Current user's personal information utilities."""

import json
import pathlib
import subprocess
from datetime import date
from typing import Any


def _get_full_name() -> str:
    """Get the current Unix full name of the current user."""
    result = subprocess.run(
        ["id", "-F"],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    return result.stdout.strip()


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
        if data.get(field):
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
        f for f in _REQUIRED_FIELDS if f not in existing or not existing[f]
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
        Dict with `name`, `long_name`, `birthday`, `age`,
        `email`, `phone`, and `addresss`.
    """
    info: dict[str, Any] = {
        "name": _get_username(),
        "long_name": _get_full_name(),
    }

    if not _CONFIG_PATH.exists():
        missing = _REQUIRED_FIELDS
    else:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        missing = [f for f in _REQUIRED_FIELDS if f not in data or not data[f]]

    if missing:
        raise FileNotFoundError(
            f"{_CONFIG_PATH} is missing or incomplete. "
            f"Run 'make user_info' to set it up. "
            f"Missing fields: {', '.join(missing)}"
        )

    with open(_CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)

    info.update(data)
    info["age"] = _compute_age(str(info["birthday"]))
    return info
