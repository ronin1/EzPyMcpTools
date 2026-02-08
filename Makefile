unexport VIRTUAL_ENV

.PHONY: setup run test-ip inspector

setup:
	uv sync

run:
	uv run python mcp_server.py --transport http

test-ip:
	uv run python utils.py ip_address.public_ipv4

inspector:
	npx @modelcontextprotocol/inspector