# Install Instruction

Use this to install as LMStudio MCP Server
```json
{
  "mcpServers": {
    "tools": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "~/ai/tools"
    }
  }
}
```

To test individual tool:
```sh
# print help & all available commands (what the MCP will see too)
./utils.py

# test a specific command
./utils.py get_current_datetime
```
