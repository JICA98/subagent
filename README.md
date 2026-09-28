# Subagent MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Standard](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io)
[![FastMCP](https://img.shields.io/badge/built%20with-FastMCP-purple.svg)](https://github.com/jlowin/fastmcp)

A Model Context Protocol (MCP) server that provides a unified gateway to orchestrate and delegate tasks to external subagent CLI runners (**Codex**, **AGY**, **CMD**, **OpenCode**, and **Pi**).

It enables LLM agents to spawn subagent coding sessions across specialized architectures (such as **GPT-6 Luna**, **Claude Sonnet/Opus 4.6**, **DeepSeek V4 Pro**, and **Gemini 3.8 Flash**), with real-time log streaming, synchronous/asynchronous execution, and full task lifecycle management.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────────┐
                      │            Any MCP Client                │
                      │ (Claude, Codex, Antigravity, OpenCode)   │
                      └────────────────────┬─────────────────────┘
                                           │ MCP (stdio)
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │          Subagent MCP Server             │
                      │  (FastMCP, server.py, Task Registry)     │
                      └────┬───────┬─────────┬─────────┬───────┬─┘
                           │       │         │         │       │
       ┌───────────────────┘       │         │         │       └──────────────────┐
       ▼                           ▼         ▼         ▼                          ▼
 ┌───────────┐               ┌─────────┐ ┌───────┐ ┌───────────┐            ┌───────────┐
 │ Codex CLI │               │ AGY CLI │ │CMD CLI│ │ OpenCode  │            │  Pi CLI   │
 │(GPT-6 Luna│               │(Claude, │ │(Deep- │ │(DeepSeek  │            │ (Stealth  │
 │ & Astra)  │               │ Gemini) │ │ Seek) │ │  Flash)   │            │  Alpha)   │
 └───────────┘               └─────────┘ └───────┘ └───────────┘            └───────────┘
       │                           │         │         │                          │
       └───────────────────────────┴────┬────┴─────────┴──────────────────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Real-time Disk Stream     │
                         │ /tmp/subagent_tasks/*.log   │
                         └─────────────────────────────┘
```

---

## Key Features

- **Multi-Model Routing**: Automatically maps model names and aliases to the proper CLI backend (e.g. `gpt-6-luna` &rarr; `codex exec`, `deepseek-v4-pro` &rarr; `cmd`, `sonnet-4.6` &rarr; `agy`).
- **Flexible Execution Modes**:
  - **Synchronous (`background=false`, default)**: Waits for the subagent to finish and returns the output directly, prepended with a metadata header containing the **Task ID**, status, and live log file path for independent verification.
  - **Asynchronous (`background=true`)**: Launches the process in the background and returns a unique `task_id` in milliseconds, preventing client timeouts during heavy operations.
- **Real-Time Live Logging**: Subprocess output streams directly to `/tmp/subagent_tasks/<task_id>.log` (customizable via `SUBAGENT_TASKS_DIR`) as it executes, enabling concurrent progress inspection.
- **Task Management Tool (`manage_task`)**: Inspect task status, peek at tailing output, terminate running processes, or flush logs to dedicated files for file-viewing tools.
- **Zero Hardcoded Paths**: Binary locations are dynamically discovered from `PATH`, user home directories, or customizable via environment variables (`SUBAGENT_CODEX_PATH`, `SUBAGENT_AGY_PATH`, etc.).

---

## Model Routing Matrix

| Model Identifier / Aliases | Target CLI Runner | Common Use Cases |
| :--- | :--- | :--- |
| `gpt-6-luna`, `gpt 6 luna`, `codex`, `luna` | **Codex CLI** (`codex exec`) | Autonomous code synthesis, deep debugging, sandbox-bypassed tool execution |
| `codex/<model>` *(e.g. `codex/gpt-6-astra`)* | **Codex CLI** (`codex exec`) | Any model hosted within the Codex ecosystem |
| `deepseek-v4-pro`, `deepseek` | **CMD CLI** (`cmd`) | High-reasoning algorithmic problems, mathematical logic |
| `claude-sonnet-4-6`, `sonnet-4.6` | **AGY CLI** (`agy`) | General software engineering, feature development, code refactoring |
| `claude-opus-4-6-thinking`, `opus-4.6` | **AGY CLI** (`agy`) | Architectural design, critical code review |
| `gemini-3.8-flash-high` / `medium` / `low` | **AGY CLI** (`agy`) | Fast high-throughput coding, large-context exploration |
| `gemini-3.7-flash-high` / `medium` / `low` | **AGY CLI** (`agy`) | Rapid iterative changes |
| `gpt-oss-120b-medium`, `gpt-oss` | **AGY CLI** (`agy`) | Open-source foundation models |
| `deepseek-v4-flash-free` | **OpenCode CLI** (`opencode`) | OpenCode free-tier model tasks |
| `muse-spark-1.3`, `muse-spark` | **OpenCode CLI** (`opencode`) | Lightweight coding snippets |
| `pi/stealth/ox-alpha`, `ox-alpha`, `pi` | **Pi CLI** (`pi`) | Terminal agent workflows |

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/JICA98/subagent.git
cd subagent
```

### 2. Set Up Virtual Environment & Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Verify Local CLI Backends (Optional)

The server automatically detects available CLIs from `PATH` and standard user directories (`~/.local/bin`, `~/.opencode/bin`, etc.). You only need to install the CLI runners you plan to use:

- **Codex CLI**: `codex` (installed at `~/.local/bin/codex` or in `PATH`)
- **AGY CLI**: `agy` (installed at `~/.local/bin/agy` or in `PATH`)
- **CMD CLI**: `cmd` (in `PATH` or npm prefix)
- **OpenCode CLI**: `opencode` (installed at `~/.opencode/bin/opencode` or in `PATH`)
- **Pi CLI**: `pi` (in `PATH`)

To override any binary path or the tasks directory, set environment variables:
```bash
export SUBAGENT_CODEX_PATH="/custom/path/to/codex"
export SUBAGENT_AGY_PATH="/custom/path/to/agy"
export SUBAGENT_TASKS_DIR="/custom/path/to/tasks"
```

---

## MCP Client Configuration Guide

Replace `/path/to/subagent` with the absolute path to your cloned `subagent` directory.

### 1. Claude Code CLI

Add directly to your global Claude Code configuration in `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "subagent": {
      "type": "stdio",
      "command": "/path/to/subagent/.venv/bin/python",
      "args": [
        "/path/to/subagent/server.py"
      ]
    }
  }
}
```

Or add via the Claude CLI:
```bash
claude mcp add subagent /path/to/subagent/.venv/bin/python /path/to/subagent/server.py
```

### 2. Claude Desktop

Add to your `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "subagent": {
      "command": "/path/to/subagent/.venv/bin/python",
      "args": [
        "/path/to/subagent/server.py"
      ]
    }
  }
}
```

### 3. Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.subagent]
command = "/path/to/subagent/.venv/bin/python"
args = ["/path/to/subagent/server.py"]
```

Or add via CLI:
```bash
codex mcp add subagent -- /path/to/subagent/.venv/bin/python /path/to/subagent/server.py
```

### 4. OpenCode CLI

Add to `~/.config/opencode/opencode.jsonc`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "subagent": {
      "type": "local",
      "command": [
        "/path/to/subagent/.venv/bin/python",
        "/path/to/subagent/server.py"
      ]
    }
  }
}
```

### 5. Grok Build CLI

Add via CLI:
```bash
grok mcp add subagent -- /path/to/subagent/.venv/bin/python /path/to/subagent/server.py
```

Or add to `~/.grok/config.toml`:
```toml
[mcp_servers.subagent]
command = "/path/to/subagent/.venv/bin/python"
args = ["/path/to/subagent/server.py"]
enabled = true
```

### 6. Standard / Generic MCP Clients

```json
{
  "mcpServers": {
    "subagent": {
      "command": "/path/to/subagent/.venv/bin/python",
      "args": [
        "/path/to/subagent/server.py"
      ],
      "timeout": 2700000
    }
  }
}
```

---

## Tools Exposed

### 1. `prompt`

Executes a prompt through the resolved subagent runner.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `prompt` | `string` | **Yes** | The prompt instruction to execute (newlines are sanitized). |
| `model` | `string` | No | Model identifier or alias (e.g. `'gpt-6-luna'`, `'sonnet-4.6'`). Defaults to active model or agy default. |
| `background` | `boolean` | No | Defaults to `false`. When `true`, spawns a background process and immediately returns the `task_id`. |

#### Example: Synchronous Call
```json
{
  "prompt": "Write a Python script to check website SSL certificate expiration",
  "model": "gpt-6-luna"
}
```

**Response Format**:
```text
[Task ID: task_20260927_222848_c390aa]
Runner: codex | Model: gpt-6-luna | Status: COMPLETED | Log: /tmp/subagent_tasks/task_20260927_222848_c390aa.log

<Output returned by the subagent>
```

#### Example: Background Call
```json
{
  "prompt": "Refactor database migrations and verify backwards compatibility",
  "model": "gpt-6-luna",
  "background": true
}
```

**Immediate Response**:
```text
Task started in background with ID: task_20260927_222922_e3d8bc
Runner: codex
Model: gpt-6-luna
Log file: /tmp/subagent_tasks/task_20260927_222922_e3d8bc.log
Status: RUNNING

Manage this task using:
- manage_task(action='peek', task_id='task_20260927_222922_e3d8bc') - View live output
- manage_task(action='status', task_id='task_20260927_222922_e3d8bc') - Check task status
- manage_task(action='write_output', task_id='task_20260927_222922_e3d8bc') - Write output to /tmp
- manage_task(action='wait', task_id='task_20260927_222922_e3d8bc') - Wait for completion
- manage_task(action='kill', task_id='task_20260927_222922_e3d8bc') - Cancel task
```

---

### 2. `review`

Specialized wrapper for code or document reviews.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `prompt` | `string` | **Yes** | Review prompt or code diff to analyze. |
| `model` | `string` | No | Defaults to `'sonnet-4.6'`. |
| `background` | `boolean` | No | Defaults to `false`. |

---

### 3. `manage_task`

Controls and inspects tasks across their lifecycle.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `action` | `string` | **Yes** | `'status'`, `'peek'`, `'write_output'`, `'kill'`, `'wait'`, `'list'`, or `'start'`. |
| `task_id` | `string` | *For most actions* | The ID of the task to manage. |
| `max_lines` | `integer` | No | Number of tail lines when `action='peek'` (default `50`). |
| `output_file` | `string` | No | Custom path to save output when `action='write_output'`. |
| `timeout` | `integer` | No | Maximum wait duration in seconds when `action='wait'` (default `60`). |
| `prompt` | `string` | *For start* | Prompt text when `action='start'`. |
| `model` | `string` | No | Model identifier when `action='start'`. |

#### Actions Reference:
- **`status`**: Returns task status (`RUNNING`, `COMPLETED`, `FAILED`, `KILLED`, `TIMEOUT`), execution duration, exit code, and log file path.
- **`peek`**: Returns the latest lines of task output in real time without blocking.
- **`write_output`**: Flushes output to `/tmp/subagent_tasks/<task_id>_output.txt` (or custom `output_file`) so agents can read it directly from disk.
- **`kill`**: Cancels and terminates a running task process.
- **`wait`**: Waits for a background task to complete and returns its output.
- **`list`**: Lists all active and past tasks.
- **`start`**: Convenience action to start a background task directly.

---

### 4. `model`

Sets or inspects the active session model default.

- `model()` &rarr; Returns current active model.
- `model(model_name="gpt-6-luna")` &rarr; Sets default model for subsequent prompt calls.

---

## Agent Skills Integration

A ready-to-use agent skill is included in [`skills/subagent/SKILL.md`](skills/subagent/SKILL.md).

To make it globally available across all agent conversations on your system:
```bash
mkdir -p ~/.agents/skills/subagent
cp skills/subagent/SKILL.md ~/.agents/skills/subagent/
```

Any agent with skills support will automatically discover the skill, know how to route models, and understand how to manage tasks via `manage_task`.

---

## Testing

Run unit and integration tests using pytest:

```bash
/path/to/subagent/.venv/bin/pytest test_server.py -v
```

All 10 test suites verify:
- Prompt newline sanitization
- Global model state handling
- Command building for all 5 CLI runners (Codex, AGY, CMD, OpenCode, Pi)
- Model alias resolution and reasoning effort flags
- Task lifecycle management (`status`, `peek`, `write_output`, `kill`, `wait`)
- Synchronous task ID and log path metadata reporting

---

## License

This project is licensed under the [MIT License](LICENSE).
