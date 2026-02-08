#!/usr/bin/env python3
"""
CLI entry point that auto-discovers public functions from utils/*.py modules.
"""

import importlib
import inspect
import pathlib
import sys


def _discover_functions() -> dict[str, dict[str, callable]]:  # type: ignore
    """Dynamically import all public functions from utils/*.py modules.

    Returns:
        Nested dict: {namespace: {function_name: callable}}
    """
    result: dict[str, dict[str, callable]] = {}  # type: ignore
    utils_dir = pathlib.Path(__file__).parent / "utils"

    for module_path in sorted(utils_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        ns = module_path.stem
        module_name = f"utils.{ns}"
        module = importlib.import_module(module_name)

        funcs = {}
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                funcs[name] = obj

        if funcs:
            result[ns] = funcs

    return result


def main() -> None:
    """CLI entry point."""
    import json

    namespaces = _discover_functions()

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <namespace.function> [args...]")
        print("\nAvailable functions:")
        for ns, funcs in namespaces.items():
            print(f"\n  [{ns}]")
            for name, func in funcs.items():
                sig = inspect.signature(func)
                doc = (func.__doc__ or ""  # type: ignore
                       ).strip().split("\n")[0]
                print(f"    {ns}.{name}{sig}")
                if doc:
                    print(f"      {doc}")
        sys.exit(0)

    qualified_name = sys.argv[1]
    func_args = sys.argv[2:]

    if "." not in qualified_name:
        print(
            "Error: Use <namespace.function> format,"
            " e.g. datetime.current"
        )
        print(
            f"Available namespaces: "
            f"{', '.join(namespaces)}"
        )
        sys.exit(1)

    namespace, func_name = qualified_name.split(".", 1)

    if namespace not in namespaces:
        print(f"Error: Unknown namespace '{namespace}'")
        print(
            f"Available namespaces: "
            f"{', '.join(namespaces)}"
        )
        sys.exit(1)

    if func_name not in namespaces[namespace]:
        print(
            f"Error: Unknown function "
            f"'{func_name}' in '{namespace}'"
        )
        print(
            f"Available functions: "
            f"{', '.join(namespaces[namespace])}"
        )
        sys.exit(1)

    func = namespaces[namespace][func_name]
    sig = inspect.signature(func)
    typed_args = []
    for arg, param in zip(func_args, sig.parameters.values()):
        hint = param.annotation
        if hint in (int, float):
            typed_args.append(hint(arg))
        else:
            typed_args.append(arg)

    result = func(*typed_args)  # type: ignore
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
