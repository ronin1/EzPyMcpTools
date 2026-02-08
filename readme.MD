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
./tools

# test a specific command
./tools get_current_datetime
```

`./tools` is a symlink file to `./utils.py`
