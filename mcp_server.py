#!/usr/bin/env python3
"""
MCP server that auto-discovers and exposes all public functions in utils/*.py.
"""

import importlib
import inspect
import pathlib

from fastmcp import FastMCP

mcp = FastMCP("Tools")


def _make_json_wrapper(func):
    """Wrap a dict-returning function to return a JSON string for MCP."""
    import functools
    import json

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        return result

    # Preserve the original signature for MCP tool schema
    wrapper.__wrapped__ = func  # type: ignore[attr-defined]
    wrapper.__signature__ = inspect.signature(func)  # type: ignore
    return wrapper


def _discover_and_register() -> None:
    """
    Dynamically import all public functions from utils/*.py and
    register as MCP tools.
    """
    utils_dir = pathlib.Path(__file__).parent / "utils"

    for module_path in sorted(utils_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        namespace = module_path.stem
        module_name = f"utils.{namespace}"
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                qualified_name = f"{namespace}.{name}"
                wrapped = _make_json_wrapper(obj)
                mcp.tool(name=qualified_name)(wrapped)


_discover_and_register()


if __name__ == "__main__":
    import json
    import sys

    server_dir = pathlib.Path(__file__).parent.resolve()

    lm_studio_config = {
        "tools": {
            "command": "uv",
            "args": ["run", "python", "mcp_server.py"],
            "cwd": str(server_dir),
        }
    }

    print("LM Studio mcp.json config:", file=sys.stderr)
    print(json.dumps(lm_studio_config, indent=2), file=sys.stderr)
    print(file=sys.stderr)

    mcp.run(transport="stdio")
