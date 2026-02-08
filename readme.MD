# Easy Python MCP Tools

- An easy way to create a bunch of custom tools for an MCP server.
- Currently, this project is used as a local MCP server for LmStudio; primarily for use with OpenSource models.
- It allows you to write plain Python scripts & those will show up as proper agent tools (with name space & instructions).
- This code has not be tested outside of MacOS (it should work ok on Linux, forget Windows).

## But Why?

- Although local OSS Models performance is not as good as hosted Comercial models of today; they are about as good as hosted comercial model of 1-2 years ago.  1-2 years from now, OSS models will be on-par with the best comercial models of today. So will the hardware that you can guy to run these models that sits on your desk.
- The one thing that OOS Models get you that comercial models don't are: Complete Privacy & Security. It also costs you nonthing but electricity to run on your own hardware.
- Comercial models has all the tooling built in. For something as simple as, asking for the current time. An OSS model can't do it without you, giving it the tools to fetch time.
- This is what this project aims to do: Make tool creation simple & empower OSS models to make it useful; but with total Privacy & Security. The data never leaves your machine.
- Try asking the question `What's the current time?` Before you enable these tools. The LLM can't answer. After enabling this tool, you can even ask things like: `What's the current time in Hawaii?`

## General Setup

After pulling this project from GitHub:

- Ensure that you have Python12+ installed
- In your console, run `make setup`, this will install all required python packages & propmpt you for your basic personal information & save it under `./user.data.json`
- Don't worry, `*.data.json` & `*.log` files are already in `.gitignore` & will never be checked in (on accident or on purpose)
- `make setup` will also call `make mcp_config` which prints the required configuration for LmStudio & OLLAMA.

## Install Instruction

### LmStudio

- Goto [lmstudio.ai](https://lmstudio.ai) & Downlaod the UI tool
- Use any model that supports tool use. Currently (Feb 7th, 2026), the author's favorite model is [Mistral 3](https://lmstudio.ai/models/ministral) or [Gema 3](https://lmstudio.ai/models/gemma-3) provided that you have enough VRAM. Any model with tool use would work
- Once the model finish download, load it up in a new chat & click on the 🔨 (hammer icon) to configure a custom MCP server & paste in the mcp configuration from `make setup` (or `make mcp_config`); should look like this:

```json
{
  "mcpServers": {
    "py_tools": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "cwd": "~/{repo-dir}/tools"
    }
  }
}
```

## Writing a new Tool

This is as simple as:

- creating a new `{name_space}.py` file under `./utils/` folder
- Inside of this python script, any public function will show up as an MCP tool with `{name_space}.{function_name}`
- Function can take any length of input, as long as it's basic types. It can return `None` or `dict` (any variation of `Dict[K, V]`). See `./utils/` for details.
- You can test these tools directly (without running an MCP server) using `./tools` command
- You can also run the MCP server over HTTP protocol by running `make run`
- All available Python debugger should work with `./utils.py` or `./tools` symlink

### To test individual tool

```sh
./tools
# print help & all available commands (what the MCP will see too)
Usage: python ./tools <namespace.function> [args...]

Available functions:

  [datetime]
    datetime.all_timezones(country_code: str = '') -> dict
      Get all timezones for a country.
    datetime.configured_timezone() -> dict
      Get the currently configured timezone.
    datetime.current(time_zone: str = '') -> dict
      Get the current date and time.

  [ip_address]
    ip_address.approximate_physical_location() -> dict
      Get your current approximate physical location based on your public IP.
    ip_address.public_ipv4() -> dict
      Get current user's public IPv4 address, physical location, and ISP name.

# etc...

# test a specific command
./tools get_current_datetime
```

`./tools` is a symlink file to `./utils.py`
