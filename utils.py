#!/usr/bin/env python3
"""CLI entry point that auto-discovers public functions from utils/*.py modules."""

import importlib
import inspect
import pathlib
import sys


def _discover_functions() -> dict[str, dict[str, callable]]:
    """Dynamically import all public functions from utils/*.py modules.

    Returns:
        Nested dict: {namespace: {function_name: callable}}
    """
    namespaces: dict[str, dict[str, callable]] = {}
    utils_dir = pathlib.Path(__file__).parent / "utils"

    for module_path in sorted(utils_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        namespace = module_path.stem
        module_name = f"utils.{namespace}"
        module = importlib.import_module(module_name)

        funcs = {}
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                funcs[name] = obj

        if funcs:
            namespaces[namespace] = funcs

    return namespaces


if __name__ == "__main__":
    namespaces = _discover_functions()

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <namespace.function> [args...]")
        print(f"\nAvailable functions:")
        for ns, funcs in namespaces.items():
            print(f"\n  [{ns}]")
            for name, func in funcs.items():
                sig = inspect.signature(func)
                doc = (func.__doc__ or "").strip().split("\n")[0]
                print(f"    {ns}.{name}{sig}")
                if doc:
                    print(f"      {doc}")
        sys.exit(0)

    qualified_name = sys.argv[1]
    func_args = sys.argv[2:]

    if "." not in qualified_name:
        print(f"Error: Use <namespace.function> format, e.g. datetime.get_current_datetime")
        print(f"Available namespaces: {', '.join(namespaces)}")
        sys.exit(1)

    namespace, func_name = qualified_name.split(".", 1)

    if namespace not in namespaces:
        print(f"Error: Unknown namespace '{namespace}'")
        print(f"Available namespaces: {', '.join(namespaces)}")
        sys.exit(1)

    if func_name not in namespaces[namespace]:
        print(f"Error: Unknown function '{func_name}' in '{namespace}'")
        print(f"Available functions: {', '.join(namespaces[namespace])}")
        sys.exit(1)

    import json

    result = namespaces[namespace][func_name](*func_args)
    print(json.dumps(result, indent=2))
