unexport VIRTUAL_ENV

# OLLAMA_MODEL ?= mistral-small3.2:latest
OLLAMA_MODEL ?= qwen3-vl:8b
#OLLAMA_MODEL ?= llama4:16x17b

.PHONY: setup py_req user_info run test mcp_config config inspector

setup: py_req user_info mcp_config

py_req:
	@python3 -c "import sys; v=sys.version_info; exit(0 if v >= (3,12) else 1)" 2>/dev/null \
		|| (echo "Error: Python 3.12+ is required." && exit 1)
	@command -v uv >/dev/null 2>&1 \
		|| (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "Python 3.12+ and uv are ready."

user_info:
	@uv sync
	@uv run python -c "from utils.user_data import ensure_user_info; ensure_user_info()"

setup_ollama:
	@ollama pull $(OLLAMA_MODEL)

run_mcp:
	@uv run watchfiles "uv run python mcp_server.py --transport http" . --filter python

run:
	@(ollama serve &)
	@echo "Running MCP server with model: $(OLLAMA_MODEL)"
	@mcphost --model 'ollama:$(OLLAMA_MODEL)'

test_ip:
	@uv run python utils.py ip_address.public_ipv4

test: test_ip

mcp_config:
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "py_tools": {'
	@echo '      "command": "uv",'
	@echo '      "args": ["run", "python", "mcp_server.py"],'
	@echo '      "cwd": "$(CURDIR)"'
	@echo '    }'
	@echo '  }'
	@echo '}'

config:
	@set -a; [ -f .env ] && . ./.env; set +a; \
		PWD="$(CURDIR)" envsubst < lmstudio.cfg.json

inspector:
	@npx @modelcontextprotocol/inspector