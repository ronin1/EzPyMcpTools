unexport VIRTUAL_ENV

.PHONY: run test-ip inspector

run:
	uv run python mcp_server.py --transport http

test-ip:
	uv run python utils.py my_public_ip_address

inspector:
	npx @modelcontextprotocol/inspector