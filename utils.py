#!/usr/bin/env python3
"""
CLI entry point that auto-discovers public functions from utils/*.py modules.
"""

import importlib
import inspect
import pathlib
import sys
from collections.abc import Callable
from typing import Any


def _discover_functions() -> tuple[
    dict[str, dict[str, Callable[..., Any]]],
    dict[str, str],
]:
    """Dynamically import all public functions from
    utils/*.py modules.

    Returns:
        Tuple of:
          - Nested dict: {namespace: {func_name: callable}}
          - Module docs: {namespace: docstring}
    """
    result: dict[str, dict[str, Callable[..., Any]]] = {}
    docs: dict[str, str] = {}
    utils_dir = pathlib.Path(__file__).parent / "utils"

    for module_path in sorted(utils_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        ns = module_path.stem
        module_name = f"utils.{ns}"
        module = importlib.import_module(module_name)

        funcs: dict[str, Callable[..., Any]] = {}
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") and obj.__module__ == module.__name__:
                funcs[name] = obj

        if funcs:
            result[ns] = funcs
            docs[ns] = (module.__doc__ or "").strip().split("\n")[0]

    return result, docs


def _print_namespace_functions(
    ns: str,
    funcs: dict[str, Callable[..., Any]],
) -> None:
    """Print all functions in a namespace with signatures
    and docstrings."""
    for name, func in funcs.items():
        sig = inspect.signature(func)
        doc = (
            (func.__doc__ or "").strip().split("\n")[0]  # type: ignore
        )
        print(f"  [func] {ns}__{name}{sig}")
        if doc:
            print(f"         {doc}")
        print()


def main() -> None:
    """CLI entry point."""
    import json

    namespaces, ns_docs = _discover_functions()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "ls"

    # --- ls command ---
    if cmd == "ls":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        if target:
            if target not in namespaces:
                print(f"Error: Unknown namespace '{target}'")
                print("Available: " + ", ".join(namespaces))
                sys.exit(1)
            desc = ns_docs.get(target, "")
            print(f"[{target}]" + (f"  {desc}" if desc else ""))
            print()
            _print_namespace_functions(target, namespaces[target])
        else:
            print(f"Run: '{cmd} ls <namespace>' to see functions information.")
            print("Available namespaces:\n")
            for ns in namespaces:
                desc = ns_docs.get(ns, "")
                print(f"  [{ns}]")
                if desc:
                    print(f"    {desc}")
                print()
        sys.exit(0)

    # --- function call ---
    qualified_name = cmd
    func_args = sys.argv[2:]

    if "__" not in qualified_name:
        print("Error: Use <namespace__function> format, e.g. datetime__current")
        print("Available namespaces: " + ", ".join(namespaces))
        sys.exit(1)

    namespace, func_name = qualified_name.split("__", 1)

    if namespace not in namespaces:
        print(f"Error: Unknown namespace '{namespace}'")
        print("Available namespaces: " + ", ".join(namespaces))
        sys.exit(1)

    if func_name not in namespaces[namespace]:
        print(f"Error: Unknown function '{func_name}' in '{namespace}'")
        print("Available functions: " + ", ".join(namespaces[namespace]))
        sys.exit(1)

    func = namespaces[namespace][func_name]
    sig = inspect.signature(func)
    typed_args: list[Any] = []
    for arg, param in zip(
        func_args,
        sig.parameters.values(),
        strict=False,
    ):
        hint = param.annotation
        if hint in (int, float):
            typed_args.append(hint(arg))
        else:
            typed_args.append(arg)

    result = func(*typed_args)  # type: ignore
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
