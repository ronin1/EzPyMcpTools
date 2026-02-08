#!/usr/bin/env python3
"""CLI entry point that auto-discovers public functions from utils/*.py modules."""

import importlib
import inspect
import pathlib
import sys


def _discover_functions() -> dict[str, callable]:
    """Dynamically import all public functions from utils/*.py modules."""
    functions = {}
    utils_dir = pathlib.Path(__file__).parent / "utils"

    for module_path in sorted(utils_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        module_name = f"utils.{module_path.stem}"
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                functions[name] = obj

    return functions


if __name__ == "__main__":
    functions = _discover_functions()

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <function_name> [args...]")
        print(f"\nAvailable functions:")
        for name, func in functions.items():
            sig = inspect.signature(func)
            doc = (func.__doc__ or "").strip().split("\n")[0]
            module = func.__module__.replace("utils.", "")
            print(f"  {name}{sig}  [{module}]")
            if doc:
                print(f"    {doc}")
        sys.exit(0)

    func_name = sys.argv[1]
    func_args = sys.argv[2:]

    if func_name not in functions:
        print(f"Error: Unknown function '{func_name}'")
        print(f"Available functions: {', '.join(functions)}")
        sys.exit(1)

    import json

    result = functions[func_name](*func_args)
    print(json.dumps(result, indent=2))
