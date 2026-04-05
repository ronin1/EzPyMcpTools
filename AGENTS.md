# AGENTS.md

This is a Python MCP server project that auto-discovers and exposes utility functions as MCP tools.

## Project Overview

- **Purpose**: MCP server providing LLM-accessible tools (datetime, IP lookup, math, user info, etc.)
- **Runtime**: Python 3.12+
- **Package Manager**: uv
- **Transport**: stdio (default), http, sse
- **Key Files**:
  - `mcp_server.py` - MCP server entry point
  - `utils.py` - CLI tool discovery and invocation
  - `utils/` - Namespace modules with public functions as MCP tools
  - `tests/` - pytest test suite

---

## Build/Lint/Test Commands

### Setup
```bash
make setup          # Install deps, create user.data.json, print MCP config
make py_req         # Check Python 3.12+ and install uv
```

### Running the Server
```bash
# MCP server with stdio transport (default for LmStudio/Ollama)
uv run python mcp_server.py

# MCP server with HTTP transport
uv run python mcp_server.py --transport http

# Watch mode for development (auto-restart on changes)
make run_mcp
```

### Testing Tools Directly
```bash
# List all namespaces
./tools

# List functions in a namespace
./tools ls datetime

# Run a specific tool
./tools datetime__current pdt
./tools ip_address__public_ipv4
```

### Linting & Formatting
```bash
# Full lint pipeline (isort, black, ruff, ty, ruff format)
make lint

# Individual linters
uv run isort . --profile black --line-length 100
uv run black . --line-length 100
uv run ruff check --fix .
uv run ty check .
uv run ruff format .

# Single file
uv run ruff check --fix path/to/file.py
uv run ruff format path/to/file.py
```

### Testing
```bash
# Run all tests (requires user.data.json)
make test

# Run tests in Docker (uses user.data.json.example)
make docker-test

# Run pytest directly
uv run pytest -q tests

# Run a single test file
uv run pytest tests/test_datetime_utils.py

# Run a single test function
uv run pytest tests/test_datetime_utils.py::test_current_with_timezone_abbreviation -v

# Run with verbose output
uv run pytest -v tests/
```

### Docker
```bash
make docker-build     # Build Docker image (requires user.data.json)
make docker-test      # Build and run tests in Docker
```

---

## Code Style Guidelines

### General
- **Line Length**: 100 characters (hard limit)
- **Python Version**: 3.12+
- **Encoding**: UTF-8 (`encoding="utf-8"` on all file operations)
- **Future Imports**: `from __future__ import annotations` in all modules

### Formatting
- **Formatter**: black with line-length 100
- **Import Sorting**: isort with black profile
- **Quotes**: Double quotes (`"`) for strings
- **Indentation**: Spaces (4 spaces standard, 8 for continuation)

### Type Annotations
- Use `ty` for type checking
- Return types must be annotated on all public functions
- Use `dict[str, Any]` for dict returns rather than `Dict`
- Use `list[T]` syntax (Python 3.9+ generic syntax)
- Union types: prefer `X | None` over `Optional[X]`

### Naming Conventions
- **Modules/Files**: lowercase_with_underscores (`datetime.py`)
- **Public Functions**: lowercase_with_underscores (`get_current_time`)
- **Private Functions**: _underscore_lowercase_with_underscores (`_get_data`)
- **Classes**: PascalCase (`MyClass`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **Private**: Leading underscore (`_helper_function`)
- **Namespace prefix**: Functions are prefixed with `{namespace}__` for MCP tool names

### Imports
- Standard library first, then third-party, then local
- Explicit imports (no `import *`)
- isort will auto-sort; run before committing

### Error Handling
- Functions return error dicts with `"error"` key rather than raising for expected failures
- Use specific exception types
- Always chain exceptions with `from exc` when re-raising
- Timeouts on subprocess calls (5s standard)

### Docstrings
- Module-level docstring required for each `utils/*.py`
- Use Google-style docstrings for functions
- Include Args/Returns sections for public functions

### File Structure
```
utils/
  __init__.py
  datetime.py      # Date/time utilities
  geo_location.py  # Geographical location utilities
  ip_address.py    # IP lookup utilities
  math.py          # Calculator utilities
  text.py          # Text utilities
  user_information.py  # User data utilities
  weather.py       # Weather utilities
```

### Writing New Tools
1. Create `utils/{namespace}.py`
2. Add module docstring
3. Write public functions with type annotations and docstrings
4. Functions must return `dict` or `None`
5. Private helpers prefixed with `_`
6. Add tests in `tests/test_{namespace}_utils.py`

### VS Code Settings
- Formatter: charliermarsh.ruff
- Format on save enabled
- Ruff code actions on save (fix all, organize imports)
- Editor ruler at 100 columns

### CI Requirements
- All PRs run `make lint` and `make docker-test`
- Lint auto-fixes are auto-committed back to PR branches
- **On each change**: run `make lint && make test && make docker-test` to ensure all checks pass
