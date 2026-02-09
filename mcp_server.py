#!/usr/bin/env python3
"""
MCP server that auto-discovers and exposes all public functions in utils/*.py.
"""

import importlib
import inspect
import pathlib

from fastmcp import FastMCP

mcp = FastMCP("Tools")


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

        ns_doc = (module.__doc__ or "").strip().split("\n")[0]

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                qualified_name = f"{namespace}__{name}"
                func_doc = (obj.__doc__ or "").strip()
                description = (
                    f"[{namespace}] {ns_doc}\n{func_doc}"
                    if ns_doc
                    else func_doc
                )
                mcp.tool(
                    name=qualified_name,
                    description=description,
                )(obj)


_discover_and_register()


if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        "-t",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="Transport protocol (default: stdio)",
    )
    args = parser.parse_args()

    server_dir = pathlib.Path(__file__).parent.resolve()

    lm_studio_config = {
        "tools": {
            "command": "uv",
            "args": ["run", "python", "mcp_server.py"],
            "cwd": str(server_dir),
        }
    }

    print(
        "LM Studio mcp.json config:",
        file=sys.stderr,
    )
    print(
        json.dumps(lm_studio_config, indent=2),
        file=sys.stderr,
    )
    print(file=sys.stderr)

    mcp.run(transport=args.transport)
