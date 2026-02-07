#!/usr/bin/env python3
"""MCP server that auto-discovers and exposes all public functions from utils/*.py."""

import importlib
import inspect
import pathlib

from fastmcp import FastMCP

mcp = FastMCP("Tools")

# Mount mcp-server-everything (reference MCP server with sample tools)
everything_config = {
    "mcpServers": {
        "default": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-everything"],
        }
    }
}
everything_proxy = FastMCP.as_proxy(everything_config, name="Everything")
mcp.mount(everything_proxy, prefix="everything")


def _discover_and_register() -> None:
    """Dynamically import all public functions from utils/*.py and register as MCP tools."""
    utils_dir = pathlib.Path(__file__).parent / "utils"

    for module_path in sorted(utils_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        module_name = f"utils.{module_path.stem}"
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                mcp.tool()(obj)


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
