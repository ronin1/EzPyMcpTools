"""Current user's personal information utilities."""
import json
import pathlib
import subprocess
from datetime import date


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
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def personal_information() -> dict:
    """Get current user's personal information."""
    info: dict[str, object] = {
        "name": _get_username(),
        "long_name": _get_full_name(),
    }
    # load from ./user_info.log
    config_path = pathlib.Path(__file__).parent.parent / "user_info.log"
    required_fields = ["birthday", "email", "phone", "addresss"]

    if not config_path.exists():
        raise FileNotFoundError(
            f"{config_path} not found. "
            f"Create it as a JSON file with these fields: "
            f"{', '.join(required_fields)}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    info.update(data)
    info["age"] = _compute_age(str(info["birthday"]))
    return info
