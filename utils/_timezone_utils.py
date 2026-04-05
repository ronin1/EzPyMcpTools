"""Timezone utility functions."""

from __future__ import annotations

import os
import time


def _get_local_iana_timezone() -> str:
    """Get the local IANA timezone name.

    Detection order:
      1. TZ environment variable
      2. /etc/localtime symlink (macOS & most Linux)
      3. /etc/timezone file (Debian/Ubuntu)
      4. timedatectl (systemd-based Linux)
      5. Fallback to abbreviation
    """
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
        try:
            with open(tz_file, encoding="utf-8") as f:
                tz = f.read().strip()
                if tz:
                    return tz
        except (OSError, PermissionError):
            pass

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
    except (OSError, subprocess.TimeoutExpired):
        pass

    # 5. Fallback to abbreviation
    return time.tzname[0]
