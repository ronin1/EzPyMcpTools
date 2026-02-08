unexport VIRTUAL_ENV

.PHONY: setup user_info run test inspector

setup: user_info

user_info:
	@uv sync
	@uv run python -c "from utils.user_data import ensure_user_info; ensure_user_info()"

run:
	@uv run python mcp_server.py --transport http

test-ip:
	@uv run python utils.py ip_address.public_ipv4

test: test-ip

inspector:
	@npx @modelcontextprotocol/inspector