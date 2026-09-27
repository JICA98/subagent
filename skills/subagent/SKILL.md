---
name: subagent
description: >-
  Use this skill whenever you need to execute prompts or delegate coding tasks to external subagent CLI runners
  (Codex with GPT-6 Luna, DeepSeek V4 Pro via cmd, Claude Sonnet/Opus via agy, Gemini 3.8 Flash via agy,
  DeepSeek Flash/Muse Spark via opencode, or Pi agents) via the subagent MCP server. Covers model routing,
  synchronous execution with task ID reporting, background tasks, and task management via manage_task.
---

# Subagent MCP Server Skill

This skill teaches agents how to leverage the `subagent` Model Context Protocol (MCP) server to delegate coding, reviewing, and research tasks to local CLI runners (`codex`, `agy`, `cmd`, `opencode`, and `pi`).

---

## 1. When to Use Subagents

Delegate to a subagent when:
- You need a dedicated agent session to work on a specialized task without cluttering the current context window.
- You need a specific model architecture (e.g., **GPT-6 Luna** via Codex, **DeepSeek V4 Pro** via cmd, **Claude Sonnet 4.6** or **Gemini 3.8 Flash** via agy).
- You want independent verification of long-running workflows with complete transcript logs.

---

## 2. Model Capabilities & Automatic Routing

The `subagent` MCP server automatically resolves model identifiers and routes them to the appropriate underlying CLI runner:

| Model Identifier / Aliases | Runner | Best For |
| :--- | :--- | :--- |
| `gpt-6-luna`, `gpt 6 luna`, `codex`, `luna`, `codex/<model>` | **Codex CLI** (`codex exec`) | Complex code synthesis, tool-driven coding, autonomous debugging with Codex sandbox bypass |
| `deepseek-v4-pro`, `deepseek` | **CMD CLI** (`cmd`) | DeepSeek reasoning, algorithmic tasks |
| `claude-sonnet-4-6`, `sonnet-4.6`, `claude-sonnet-4.6` | **AGY CLI** (`agy`) | General coding, high-quality code reviews, refactoring |
| `claude-opus-4-6-thinking`, `opus-4.6` | **AGY CLI** (`agy`) | Deep architectural reasoning, hard edge cases |
| `gemini-3.8-flash-high`, `gemini-3.8-flash`, `gemini-3.8` | **AGY CLI** (`agy`) | Fast high-throughput coding tasks, large context |
| `gemini-3.7-flash-high`, `gemini-3.7-flash` | **AGY CLI** (`agy`) | Fast exploration |
| `gpt-oss-120b-medium`, `gpt-oss` | **AGY CLI** (`agy`) | Open-source LLM tasks |
| `deepseek-v4-flash-free`, `opencode` | **OpenCode CLI** (`opencode`) | OpenCode free-tier tasks |
| `muse-spark-1.3`, `muse-spark` | **OpenCode CLI** (`opencode`) | Lightweight coding snippets |
| `pi/stealth/ox-alpha`, `ox-alpha`, `pi` | **Pi CLI** (`pi`) | Terminal coding agent |

---

## 3. Tools Exposed by `subagent` MCP

### A. `prompt`
Executes a prompt through the subagent CLI runner.

**Parameters**:
- `prompt` (string, required): The prompt text to execute (newlines are automatically sanitized).
- `model` (string, optional): Model identifier (e.g. `'gpt-6-luna'`, `'sonnet-4.6'`).
- `background` (boolean, optional, default: `false`):
  - `false`: Waits synchronously until completion, returning the output prepended with `[Task ID: ...]`, runner, status, and log path.
  - `true`: Launches asynchronously in the background and immediately returns a `task_id`.

**Example Synchronous Call**:
```json
{
  "prompt": "Implement binary search in Python with unit tests",
  "model": "gpt-6-luna"
}
```

**Returned Header**:
```text
[Task ID: task_20260927_222848_c390aa]
Runner: codex | Model: gpt-6-luna | Status: COMPLETED | Log: /tmp/subagent_tasks/task_20260927_222848_c390aa.log

<Output content>
```

---

### B. `review`
Specialized tool for code or document review.

**Parameters**:
- `prompt` (string, required): Review instructions or code to inspect.
- `model` (string, optional, default: `'sonnet-4.6'`): Review model.
- `background` (boolean, optional, default: `false`).

---

### C. `manage_task`
Inspects, controls, and exports tasks.

**Parameters**:
- `action` (string, required): One of `'peek'`, `'status'`, `'write_output'`, `'kill'`, `'list'`, `'wait'`, `'start'`.
- `task_id` (string, optional): Required for `peek`, `status`, `write_output`, `kill`, `wait`.
- `output_file` (string, optional): Custom file path when `action="write_output"`.
- `max_lines` (integer, optional, default: 50): Number of tail lines when `action="peek"`.
- `timeout` (integer, optional, default: 60): Timeout seconds when `action="wait"`.

**Actions Guide**:
1. **`action="status"`**: Check if task is `RUNNING`, `COMPLETED`, `FAILED`, or `KILLED`, along with execution duration and exit code.
2. **`action="peek"`**: Look at the latest output lines without blocking.
3. **`action="write_output"`**: Flushes task output to `/tmp/subagent_tasks/<task_id>_output.txt` (or custom `output_file`) so the agent can read the file directly using file tools.
4. **`action="kill"`**: Cancels and kills a running task.
5. **`action="wait"`**: Waits for a background task to finish.
6. **`action="list"`**: Lists all tracked tasks.

---

### D. `model`
Sets or gets the global default active model for the session.

- Call `model()` with no arguments to get current model.
- Call `model(model_name="gpt-6-luna")` to set default model for subsequent calls.

---

## 4. Verification and Log Inspection

Every subagent task streams live output directly to disk:
```text
/tmp/subagent_tasks/<task_id>.log
```

Even while a task is running, an agent can:
1. Call `manage_task(action="peek", task_id="<task_id>")` to check progress.
2. Read `/tmp/subagent_tasks/<task_id>.log` directly using file viewing tools (`view_file`).
3. Call `manage_task(action="write_output", task_id="<task_id>")` to save a permanent snapshot to `/tmp/subagent_tasks/<task_id>_output.txt`.

---

## 5. Recommended Agent Workflow

1. **Short Tasks (< 30 seconds)**:
   Call `prompt(prompt="...", model="gpt-6-luna")`. Receive the output directly along with the `Task ID`.
2. **Long-Running or Heavy Tasks**:
   Call `prompt(prompt="...", model="gpt-6-luna", background=true)`.
   - Receive the `task_id` immediately.
   - Proceed with other work or check status using `manage_task(action="peek", task_id="...")`.
   - Wait when ready via `manage_task(action="wait", task_id="...")`.
3. **Independent Verification**:
   Inspect the log file at `/tmp/subagent_tasks/<task_id>.log` to verify hook execution, tool calls, and model reasoning.
