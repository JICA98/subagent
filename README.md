# Subagent MCP Server

A Model Context Protocol (MCP) server written in Python using FastMCP, designed to execute subagent CLI commands (`agy` / `cmd` / `opencode` / `pi` / `codex`) via stdio.

## Overview

The `subagent` MCP server provides a lightweight gateway for MCP clients to invoke subagent CLI runners. It processes prompt requests by sanitizing newlines and executing `codex`, `agy`, `cmd`, `opencode`, or `pi` depending on the selected model:
- `gpt-6-luna` / `codex` routes automatically to `codex`
- `deepseek-v4-pro` routes automatically to `cmd`
- `deepseek-v4-flash-free` and `muse-spark-1.3` route automatically to `opencode`
- `pi/<provider>/<model>` models (e.g. `pi/stealth/ox-alpha`) route automatically to `pi`
- All other models route to `agy`

## Background Execution & Task Management

CLI runners (such as `codex exec`, `agy`, `cmd`, etc.) run as multi-step agentic sessions that think, run tools, and evaluate prompts; they do **not** return final text immediately. 

To prevent MCP client timeouts on long-running tasks, the server supports:
- **Immediate Task IDs**: Pass `background=True` to `prompt()` or `review()`, or call `manage_task(action="start", prompt="...")` to launch a task asynchronously and receive a `task_id` right away.
- **Designated `/tmp` Output Directory**: Every task continuously streams real-time stdout and stderr into `/tmp/subagent_tasks/<task_id>.log`.
- **`manage_task` Tool**: Allows agents to inspect, control, and extract outputs at any point.

## Tools Exposed

- **`prompt`**: Accepts a string `prompt`, an optional `model` override, and an optional `background: bool = False` flag.
  - When `background=False` (default): Executes synchronously and returns the output text prepended with `[Task ID: <task_id>]`, runner, model, status, and log file path (`/tmp/subagent_tasks/<task_id>.log`) so calling agents can independently verify and inspect the full subagent session logs.
  - When `background=True`: Starts the task in the background and immediately returns a `task_id` with management instructions.
- **`review`**: Accepts a string `prompt`, an optional `model` parameter (defaults to `"sonnet-4.6"`), and an optional `background: bool = False` flag.

- **`manage_task`**: Manages subagent background and foreground tasks:
  - `action="peek"`: Peeks at the latest output lines of a running or completed task (`max_lines` controls line count, default 50).
  - `action="status"`: Checks current status (`RUNNING`, `COMPLETED`, `FAILED`, `KILLED`, `TIMEOUT`), execution duration, exit code, and log file path.
  - `action="write_output"`: Flushes/writes the task's output to the designated directory `/tmp/subagent_tasks/<task_id>_output.txt` (or custom `output_file`), enabling agents to read the file directly from disk via file viewing tools.
  - `action="kill"`: Cancels and terminates a running task subprocess.
  - `action="list"`: Lists all tracked tasks with their status, model, runner, and log paths.
  - `action="wait"`: Waits for a running task to complete (up to `timeout` seconds, default 60).
  - `action="start"`: Launches a new background task with `prompt` and optional `model`.
- **`model`**: Sets or gets the default active model for subsequent prompt tool calls.
  - Calling `model()` without arguments returns the current active model state.
  - Calling `model(model_name="<model>")` sets the active model.

### Model Capabilities & Automatic Routing

Both `prompt` and `review` tools advertise supported models in their MCP parameter descriptions:
- `gpt-6-luna` / `gpt 6 luna` / `codex` / `luna`: GPT-6 Luna (automatically routes to `codex`)
- `codex/<model>`: Routes any model to `codex` (e.g. `codex/gpt-6-astra`, `codex/gpt-6-sol`)
- `deepseek-v4-pro` / `deepseek`: DeepSeek V4 Pro (automatically routes to `cmd`)
- `claude-sonnet-4-6` / `sonnet-4.6`: Claude Sonnet 4.6 (Thinking) (routes to `agy`)
- `claude-opus-4-6-thinking` / `opus-4.6`: Claude Opus 4.6 (Thinking) (routes to `agy`)
- `gemini-3.8-flash-high` / `medium` / `low` / `gemini-3.8-flash`: Gemini 3.8 Flash (routes to `agy`)
- `gemini-3.7-flash-high` / `medium` / `low` / `gemini-3.7-flash`: Gemini 3.7 Flash (routes to `agy`)
- `gpt-oss-120b-medium`: GPT-OSS 120B (Medium) (routes to `agy`)
- `deepseek-v4-flash-free`: DeepSeek V4 Flash Free (routes to `opencode`)
- `muse-spark-1.3` / `muse-spark`: Muse Spark 1.3 (routes to `opencode`)
- `pi/stealth/ox-alpha` / `ox-alpha`: Pi coding agent via stealth ox-alpha (routes to `pi`; any `pi/<provider>/<model>` identifier works)

## MCP Client Configuration

### Standard MCP Client (JSON Settings)

Add the following JSON snippet to your MCP client settings file:

```json
{
  "mcpServers": {
    "subagent": {
      "command": "/home/jica/subagent/.venv/bin/python",
      "args": [
        "/home/jica/subagent/server.py"
      ],
      "timeout": 2700000
    }
  }
}
```

### Grok Build CLI

Add the server via CLI:

```bash
grok mcp add subagent -- /home/jica/subagent/.venv/bin/python /home/jica/subagent/server.py
```

Or add directly to `~/.grok/config.toml`:

```toml
[mcp_servers.subagent]
command = "/home/jica/subagent/.venv/bin/python"
args = ["/home/jica/subagent/server.py"]
enabled = true
```

### OpenCode CLI

Configured in `~/.config/opencode/opencode.jsonc`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "subagent": {
      "type": "local",
      "command": [
        "/home/jica/subagent/.venv/bin/python",
        "/home/jica/subagent/server.py"
      ]
    }
  }
}
```

### Codex CLI

Configured in `~/.codex/config.toml`:

```toml
[mcp_servers.subagent]
command = "/home/jica/subagent/.venv/bin/python"
args = ["/home/jica/subagent/server.py"]
```

## Testing

Run unit test verification:

```bash
/home/jica/subagent/.venv/bin/pytest /home/jica/subagent/test_server.py -v
```
