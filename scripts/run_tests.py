#!/usr/bin/env python3
"""Run project tests locally or inside Docker."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _run_local_tests(project_root: Path) -> int:
    """Run pytest locally using the project environment."""
    cmd = ["uv", "run", "pytest", "-q", "tests"]
    result = subprocess.run(
        cmd,
        cwd=project_root,
        check=False,
    )
    return result.returncode


def _run_docker_tests(project_root: Path) -> int:
    """Run pytest in the Docker image."""
    image = os.environ.get("EZPY_TOOLS_IMAGE", "ezpy-tools:alpine")
    user_data = Path(
        os.environ.get("EZPY_USER_DATA", str(project_root / "user.data.json"))
    ).resolve()
    if not user_data.exists():
        print(f"ERROR: user data file not found: {user_data}", file=sys.stderr)
        return 2

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{user_data}:/app/user.data.json:ro",
        "--entrypoint",
        "uv",
        image,
        "run",
        "pytest",
        "-q",
        "tests",
    ]
    result = subprocess.run(
        cmd,
        cwd=project_root,
        check=False,
    )
    return result.returncode


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("local", "docker"),
        default="local",
        help="Test runtime target.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    if args.mode == "docker":
        return _run_docker_tests(project_root)
    return _run_local_tests(project_root)


if __name__ == "__main__":
    raise SystemExit(main())
