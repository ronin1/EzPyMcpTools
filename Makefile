unexport VIRTUAL_ENV

# OLLAMA_MODEL ?= mistral-small3.2:latest
OLLAMA_MODEL ?= qwen3-vl:8b
#OLLAMA_MODEL ?= llama4:16x17b

.PHONY: setup py_req user_info run test test_user_info mcp_config config inspector lint docker-build docker-test

setup: py_req user_info test_user_info mcp_config

py_req:
	@python3 -c "import sys; v=sys.version_info; exit(0 if v >= (3,12) else 1)" 2>/dev/null \
		|| (echo "Error: Python 3.12+ is required." && exit 1)
	@command -v uv >/dev/null 2>&1 \
		|| (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "Python 3.12+ and uv are ready."

user_info:
	@uv sync
	@uv run python -c "from utils.user_information import _ensure_user_info; _ensure_user_info()"

setup_ollama:
	@ollama pull $(OLLAMA_MODEL)

run_mcp:
	@uv run watchfiles "uv run python mcp_server.py --transport http" . --filter python

run_ollama:
	@(ollama serve &)
	@echo "Running MCP server with model: $(OLLAMA_MODEL)"
	@mcphost --model 'ollama:$(OLLAMA_MODEL)'

test_ip:
	@uv run python utils.py ip_address__public_ipv4

test_user_info:
	@uv run python -c "from utils.user_information import personal_data; d = personal_data(); assert d.get('name'), 'missing name in personal_data'"

test: user_info
	@python3 scripts/container_smoke_test.py

mcp_config:
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "ezpy_tools": {'
	@echo '      "command": "uv",'
	@echo '      "args": ["run", "python", "mcp_server.py"],'
	@echo '      "cwd": "$(CURDIR)"'
	@echo '    }'
	@echo '  }'
	@echo '}'

config:
	@set -a; [ -f .env ] && . ./.env; set +a; \
		PWD="$(CURDIR)" envsubst < lmstudio.cfg.json

lint:
	@uv run isort . --profile black --line-length 80
	@uv run black . --line-length 80
	@uv run ruff check --fix .
	@uv run ty check .
	@uv run ruff format .

inspector:
	@npx @modelcontextprotocol/inspector

docker-build: user_info
	@docker build -t ezpy-tools:alpine .

docker-test: docker-build
	@docker run --rm \
		-v "$(CURDIR)/user.data.json:/app/user.data.json:ro" \
		--entrypoint python \
		ezpy-tools:alpine \
		scripts/container_smoke_test.py