import os
import shutil
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict
from fastmcp import FastMCP, Context

mcp = FastMCP("subagent")

_CURRENT_MODEL: Optional[str] = None
import tempfile

TASKS_DIR = os.environ.get("SUBAGENT_TASKS_DIR") or os.path.join(tempfile.gettempdir(), "subagent_tasks")
os.makedirs(TASKS_DIR, exist_ok=True)

def _resolve_binary(name: str, fallback_paths: list[str]) -> str:
    env_override = os.environ.get(f"SUBAGENT_{name.upper()}_PATH")
    if env_override:
        return env_override
    which_path = shutil.which(name)
    if which_path:
        return which_path
    for p in fallback_paths:
        expanded = os.path.expanduser(p)
        if os.path.exists(expanded) and os.access(expanded, os.X_OK):
            return expanded
    return os.path.expanduser(fallback_paths[0]) if fallback_paths else name

AGY_PATH = _resolve_binary("agy", ["~/.local/bin/agy"])
CMD_PATH = _resolve_binary("cmd", ["~/.local/bin/cmd"])
OPENCODE_PATH = _resolve_binary("opencode", ["~/.opencode/bin/opencode", "~/.local/bin/opencode"])
PI_PATH = _resolve_binary("pi", ["~/.local/bin/pi"])
CODEX_PATH = _resolve_binary("codex", ["~/.local/bin/codex"])


def sanitize_prompt(prompt: str) -> str:
    cleaned = prompt.replace("\r\n", "  ").replace("\n", " ").replace("\r", " ")
    return cleaned.strip()

def get_model() -> Optional[str]:
    return _CURRENT_MODEL

def set_model(model_name: Optional[str]) -> str:
    global _CURRENT_MODEL
    if not model_name:
        _CURRENT_MODEL = None
        return "Active model reset to default."
    _CURRENT_MODEL = model_name
    return f"Active model set to '{_CURRENT_MODEL}'."

MODEL_ALIASES = {
    "deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek": "deepseek-v4-pro",
    "sonnet-4.6": "claude-sonnet-4-6",
    "sonnet-4-6": "claude-sonnet-4-6",
    "claude-sonnet-4.6": "claude-sonnet-4-6",
    "opus-4.6": "claude-opus-4-6-thinking",
    "opus-4-6": "claude-opus-4-6-thinking",
    "claude-opus-4.6": "claude-opus-4-6-thinking",
    "gemini-3.8-flash": "gemini-3.8-flash-high",
    "gemini-3.8-flash-high": "gemini-3.8-flash-high",
    "gemini-3.8-flash-medium": "gemini-3.8-flash-medium",
    "gemini-3.8-flash-low": "gemini-3.8-flash-low",
    "gemini-3.8": "gemini-3.8-flash-high",
    "gemini-3.7-flash": "gemini-3.7-flash-high",
    "gemini-3.7-flash-high": "gemini-3.7-flash-high",
    "gemini-3.7-flash-medium": "gemini-3.7-flash-medium",
    "gemini-3.7-flash-low": "gemini-3.7-flash-low",
    "gpt-oss": "gpt-oss-120b-medium",
    "opencode": "opencode/deepseek-v4-flash-free",
    "deepseek-v4-flash-free": "opencode/deepseek-v4-flash-free",
    "deepseek-flash-free": "opencode/deepseek-v4-flash-free",
    "deepseek-v4-flash": "opencode/deepseek-v4-flash-free",
    "opencode/deepseek-v4-flash-free": "opencode/deepseek-v4-flash-free",
    "muse-spark-1.3": "opencode/muse-spark-1.2-contributor-free",
    "muse-spark": "opencode/muse-spark-1.2-contributor-free",
    "muse-1.3": "opencode/muse-spark-1.2-contributor-free",
    "opencode/muse-spark-1.3": "opencode/muse-spark-1.2-contributor-free",
    "opencode/muse-spark-1.2-contributor-free": "opencode/muse-spark-1.2-contributor-free",
    "pi": "pi/stealth/ox-alpha",
    "ox-alpha": "pi/stealth/ox-alpha",
    "codex": "gpt-6-luna",
    "gpt-6-luna": "gpt-6-luna",
    "gpt 6 luna": "gpt-6-luna",
    "gpt-6": "gpt-6-luna",
    "gpt 6": "gpt-6-luna",
    "gpt6-luna": "gpt-6-luna",
    "gpt6": "gpt-6-luna",
    "luna": "gpt-6-luna",
    "codex/gpt-6-luna": "gpt-6-luna",
    "gpt-6-astra": "gpt-6-astra",
    "astra": "gpt-6-astra",
    "gpt-6-sol": "gpt-6-sol",
    "sol": "gpt-6-sol",
    "gpt-5.6-luna": "gpt-5.6-luna",
    "gpt-5.6-sol": "gpt-5.6-sol",
    "gpt-5.6-terra": "gpt-5.6-terra",
}

def resolve_model_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    cleaned = name.strip()
    return MODEL_ALIASES.get(cleaned.lower(), cleaned)

def build_command(
    sanitized_prompt: str,
    override_model: Optional[str] = None,
    effort: Optional[str] = None,
) -> list[str]:
    raw_target = override_model if override_model is not None else _CURRENT_MODEL
    target_model = resolve_model_name(raw_target)

    is_opencode = bool(
        target_model
        and (
            target_model.startswith("opencode/")
            or target_model.startswith("opencode-go/")
        )
    )
    # pi models use 'pi/<provider>/<model>' (e.g. 'pi/stealth/ox-alpha');
    # the remainder after 'pi/' maps directly to pi's --model flag.
    is_pi = bool(target_model and target_model.startswith("pi/"))
    is_cmd = bool(
        target_model
        and not is_opencode
        and not is_pi
        and ("deepseek-v4-pro" in target_model.lower() or target_model.lower() == "deepseek")
    )
    is_codex = bool(
        target_model
        and not is_opencode
        and not is_pi
        and not is_cmd
        and (
            target_model.startswith("codex/")
            or target_model.lower() == "codex"
            or target_model.lower().startswith("gpt-6")
            or target_model.lower().startswith("gpt-5.6")
            or "luna" in target_model.lower()
            or "astra" in target_model.lower()
        )
    )

    if is_opencode:
        return [OPENCODE_PATH, "run", "-m", target_model, "--auto", sanitized_prompt]
    elif is_pi:
        cmd = [PI_PATH, "--mode", "text", "--no-session"]
        cmd.extend(["--model", target_model[len("pi/"):]] if len(target_model) > 3 else [])
        cmd.extend(["-p", sanitized_prompt])
        return cmd
    elif is_cmd:
        cmd = [CMD_PATH, "--dangerously-skip-permissions"]
    elif is_codex:
        model_name = target_model[len("codex/"):] if target_model.startswith("codex/") else target_model
        if model_name.lower() == "codex" or not model_name:
            model_name = "gpt-6-luna"
        cmd = [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check"]
        if model_name:
            cmd.extend(["-m", model_name])
        if effort:
            cmd.extend(["-c", f'model_reasoning_effort="{effort}"'])
        cmd.extend(["--", sanitized_prompt])
        return cmd
    else:
        cmd = [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m"]

    if target_model:
        cmd.extend(["--model", target_model])
        target_effort = effort or ("high" if "gemini" in target_model.lower() and not ("high" in target_model.lower() or "low" in target_model.lower() or "medium" in target_model.lower()) else None)
        if target_effort:
            cmd.extend(["--effort", target_effort])
    elif effort:
        cmd.extend(["--effort", effort])

    cmd.extend(["-p", sanitized_prompt])
    return cmd

class SubagentTask:
    def __init__(
        self,
        task_id: str,
        prompt: str,
        runner: str,
        model: Optional[str],
        cmd: list[str],
        log_file: str,
    ):
        self.task_id = task_id
        self.prompt = prompt
        self.runner = runner
        self.model = model
        self.cmd = cmd
        self.log_file = log_file
        self.output_file: Optional[str] = None
        self.status = "RUNNING"  # RUNNING, COMPLETED, FAILED, KILLED, TIMEOUT
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.exit_code: Optional[int] = None
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.error: Optional[str] = None
        self.asyncio_task: Optional[asyncio.Task] = None

    def elapsed_seconds(self) -> float:
        end = self.completed_at or datetime.now()
        return (end - self.created_at).total_seconds()

    def read_output(self, max_lines: Optional[int] = None) -> str:
        if not os.path.exists(self.log_file):
            return ""
        try:
            with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                if max_lines is None:
                    return f.read()
                lines = f.readlines()
                return "".join(lines[-max_lines:])
        except Exception as e:
            return f"Error reading log file: {str(e)}"

    def write_output_file(self, target_path: Optional[str] = None) -> str:
        if not target_path:
            target_path = os.path.join(TASKS_DIR, f"{self.task_id}_output.txt")
        self.output_file = target_path
        content = self.read_output()
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return target_path

    def kill(self) -> bool:
        if self.status != "RUNNING":
            return False
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
            try:
                self.proc.kill()
            except Exception:
                pass
        self.status = "KILLED"
        self.completed_at = datetime.now()
        self.error = "Task was killed by user."
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[Task {self.task_id} killed at {datetime.now().isoformat()}]\n")
        except Exception:
            pass
        return True

_TASKS: Dict[str, SubagentTask] = {}

async def _run_task_worker(task: SubagentTask, timeout: int = 2700):
    try:
        with open(task.log_file, "w", encoding="utf-8") as f_out:
            proc = await asyncio.create_subprocess_exec(
                *task.cmd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=f_out,
                stderr=asyncio.subprocess.STDOUT,
            )
            task.proc = proc
            try:
                await asyncio.wait_for(proc.wait(), timeout=timeout)
                if task.status != "KILLED":
                    task.exit_code = proc.returncode
                    task.completed_at = datetime.now()
                    if proc.returncode == 0:
                        task.status = "COMPLETED"
                    else:
                        task.status = "FAILED"
                        task.error = f"Process exited with code {proc.returncode}"
            except asyncio.TimeoutError:
                task.status = "TIMEOUT"
                task.completed_at = datetime.now()
                task.error = f"Execution timed out after {timeout} seconds."
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    with open(task.log_file, "a", encoding="utf-8") as f_log:
                        f_log.write(f"\n[Error: Execution timed out after {timeout} seconds.]\n")
                except Exception:
                    pass
    except Exception as e:
        task.status = "FAILED"
        task.completed_at = datetime.now()
        task.error = str(e)
        try:
            with open(task.log_file, "a", encoding="utf-8") as f_log:
                f_log.write(f"\n[Execution error: {str(e)}]\n")
        except Exception:
            pass

async def execute_task(
    cmd: list[str],
    prompt_text: str,
    model_name: Optional[str],
    background: bool = False,
    ctx: Optional[Context] = None,
    timeout: int = 2700,
) -> str:
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    runner = os.path.basename(cmd[0])
    log_file = os.path.join(TASKS_DIR, f"{task_id}.log")

    task = SubagentTask(
        task_id=task_id,
        prompt=prompt_text,
        runner=runner,
        model=model_name,
        cmd=cmd,
        log_file=log_file,
    )
    _TASKS[task_id] = task

    if background:
        task.asyncio_task = asyncio.create_task(_run_task_worker(task, timeout=timeout))
        if ctx:
            await ctx.info(f"Subagent ({runner}) started background task {task_id}.")
        return (
            f"Task started in background with ID: {task_id}\n"
            f"Runner: {runner}\n"
            f"Model: {model_name or 'default'}\n"
            f"Log file: {log_file}\n"
            f"Status: RUNNING\n\n"
            f"Manage this task using:\n"
            f"- manage_task(action='peek', task_id='{task_id}') - View live output\n"
            f"- manage_task(action='status', task_id='{task_id}') - Check task status\n"
            f"- manage_task(action='write_output', task_id='{task_id}') - Write output to /tmp for reading\n"
            f"- manage_task(action='wait', task_id='{task_id}') - Wait for completion\n"
            f"- manage_task(action='kill', task_id='{task_id}') - Cancel task"
        )
    else:
        if ctx:
            await ctx.info(f"Subagent ({runner}) executing prompt: {prompt_text[:60]}...")
        await _run_task_worker(task, timeout=timeout)
        output = task.read_output()
        meta = (
            f"[Task ID: {task.task_id}]\n"
            f"Runner: {runner} | Model: {model_name or 'default'} | Status: {task.status} | Log: {task.log_file}\n\n"
        )
        if task.status == "FAILED":
            return f"{meta}Error executing {runner} (exit code {task.exit_code}):\n{output}"
        elif task.status == "TIMEOUT":
            return f"{meta}Error: Subagent {runner} execution timed out after {timeout} seconds (45 minutes)."
        return f"{meta}{output}"


@mcp.tool()
async def prompt(
    prompt: str,
    model: Optional[str] = None,
    background: bool = False,
    ctx: Context = None,
) -> str:
    """Passes a prompt string to the subagent CLI runner after stripping all newlines.

    Args:
        prompt: The prompt text string to execute.
        model: Optional model identifier to override for this prompt call.
               Available models include:
               - 'gpt-6-luna' / 'gpt 6 luna' / 'codex': GPT-6 Luna (automatically routes to codex)
               - 'deepseek-v4-pro' / 'deepseek': DeepSeek V4 Pro (automatically routes to cmd)
               - 'claude-sonnet-4-6' / 'sonnet-4.6': Claude Sonnet 4.6 (Thinking)
               - 'claude-opus-4-6-thinking' / 'opus-4.6': Claude Opus 4.6 (Thinking)
               - 'gemini-3.8-flash-high' / 'medium' / 'low' / 'gemini-3.8-flash': Gemini 3.8 Flash
               - 'gemini-3.7-flash-high' / 'medium' / 'low' / 'gemini-3.7-flash': Gemini 3.7 Flash
               - 'gpt-oss-120b-medium': GPT-OSS 120B (Medium)
               - 'deepseek-v4-flash-free': DeepSeek V4 Flash Free (automatically routes to opencode)
               - 'muse-spark-1.3' / 'muse-spark': Muse Spark 1.3 (automatically routes to opencode)
               - 'pi/stealth/ox-alpha' / 'ox-alpha': Pi agent with stealth ox-alpha (automatically routes to pi; any 'pi/<provider>/<model>' works)
               Any valid model identifier can be passed.
        background: If True, launches the task in the background and immediately returns a task_id.
                    Use manage_task to peek, check status, write output to /tmp, or kill.
                    If False (default), waits synchronously for completion.
    """
    sanitized = sanitize_prompt(prompt)
    if not sanitized:
        return "Error: Prompt cannot be empty."

    cmd = build_command(sanitized, override_model=model)
    raw_target = model if model is not None else _CURRENT_MODEL
    target_model = resolve_model_name(raw_target)
    return await execute_task(cmd, sanitized, target_model, background=background, ctx=ctx)

@mcp.tool()
async def review(
    prompt: str,
    model: Optional[str] = "sonnet-4.6",
    background: bool = False,
    ctx: Context = None,
) -> str:
    """Passes a review prompt string to the subagent CLI runner.

    Args:
        prompt: The code or document review prompt string to execute.
        model: Model identifier to use for review (defaults to 'sonnet-4.6').
               Available models include:
               - 'gpt-6-luna' / 'gpt 6 luna' / 'codex': GPT-6 Luna (automatically routes to codex)
               - 'deepseek-v4-pro' / 'deepseek': DeepSeek V4 Pro (automatically routes to cmd)
               - 'claude-sonnet-4-6' / 'sonnet-4.6': Claude Sonnet 4.6 (Thinking)
               - 'claude-opus-4-6-thinking' / 'opus-4.6': Claude Opus 4.6 (Thinking)
               - 'gemini-3.8-flash-high' / 'medium' / 'low' / 'gemini-3.8-flash': Gemini 3.8 Flash
               - 'gemini-3.7-flash-high' / 'medium' / 'low' / 'gemini-3.7-flash': Gemini 3.7 Flash
               - 'gpt-oss-120b-medium': GPT-OSS 120B (Medium)
               - 'deepseek-v4-flash-free': DeepSeek V4 Flash Free (automatically routes to opencode)
               - 'muse-spark-1.3' / 'muse-spark': Muse Spark 1.3 (automatically routes to opencode)
               - 'pi/stealth/ox-alpha' / 'ox-alpha': Pi agent with stealth ox-alpha (automatically routes to pi; any 'pi/<provider>/<model>' works)
               Any valid model identifier can be passed.
        background: If True, launches the review task in the background and immediately returns a task_id.
                    Use manage_task to peek, check status, write output to /tmp, or kill.
                    If False (default), waits synchronously for completion.
    """
    sanitized = sanitize_prompt(prompt)
    if not sanitized:
        return "Error: Prompt cannot be empty."

    selected_model = model.strip() if model and model.strip() else "sonnet-4.6"
    cmd = build_command(sanitized, override_model=selected_model)
    target_model = resolve_model_name(selected_model)
    return await execute_task(cmd, sanitized, target_model, background=background, ctx=ctx)

@mcp.tool()
async def manage_task(
    action: str,
    task_id: Optional[str] = None,
    output_file: Optional[str] = None,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_lines: int = 50,
    timeout: int = 60,
    ctx: Context = None,
) -> str:
    """Manages subagent background and foreground tasks.

    Actions:
        - 'peek': View recent output lines of a running or completed task.
        - 'status': Check the current status, execution duration, and log path of a task.
        - 'write_output': Writes the current task output to a file in the designated /tmp folder
                          (defaults to /tmp/subagent_tasks/<task_id>_output.txt or custom output_file)
                          so agents can read it directly from disk.
        - 'kill': Terminate/cancel a running task.
        - 'list': List all tracked tasks and their status.
        - 'wait': Wait for a running task to complete (up to timeout seconds).
        - 'start': Start a new prompt task in the background.

    Args:
        action: 'peek', 'status', 'write_output', 'kill', 'list', 'wait', or 'start'.
        task_id: The ID of the task to manage (required for peek, status, write_output, kill, wait).
        output_file: Optional path to write output to when action='write_output'.
        prompt: Prompt string when action='start'.
        model: Optional model identifier when action='start'.
        max_lines: Number of trailing output lines to return when action='peek' (default 50).
        timeout: Timeout in seconds when action='wait' (default 60).
    """
    act = action.strip().lower()

    if act == "list":
        if not _TASKS:
            return "No tasks tracked."
        lines = ["Tracked Tasks:"]
        for tid, t in sorted(_TASKS.items(), key=lambda item: item[1].created_at, reverse=True):
            elapsed = f"{t.elapsed_seconds():.1f}s"
            lines.append(
                f"- ID: {t.task_id} | Status: {t.status} | Runner: {t.runner} | "
                f"Model: {t.model or 'default'} | Elapsed: {elapsed} | Log: {t.log_file}"
            )
        return "\n".join(lines)

    if act in ("start", "run"):
        if not prompt or not prompt.strip():
            return "Error: 'prompt' argument is required to start a task."
        sanitized = sanitize_prompt(prompt)
        cmd = build_command(sanitized, override_model=model)
        raw_target = model if model is not None else _CURRENT_MODEL
        target_model = resolve_model_name(raw_target)
        return await execute_task(cmd, sanitized, target_model, background=True, ctx=ctx)

    if not task_id:
        return f"Error: task_id is required for action '{action}'."

    task = _TASKS.get(task_id)
    if not task:
        matches = [t for tid, t in _TASKS.items() if task_id in tid]
        if len(matches) == 1:
            task = matches[0]

    if not task:
        log_candidate = os.path.join(TASKS_DIR, f"{task_id}.log") if not task_id.endswith(".log") else os.path.join(TASKS_DIR, task_id)
        if os.path.exists(log_candidate):
            if act in ("peek", "tail"):
                with open(log_candidate, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    tail = "".join(lines[-max_lines:]) if lines else "(empty)"
                    return f"[{task_id}] (from disk log: {log_candidate})\n--- Recent Output (last {max_lines} lines) ---\n{tail}"
            elif act in ("write_output", "output"):
                dest = output_file or os.path.join(TASKS_DIR, f"{task_id}_output.txt")
                shutil.copyfile(log_candidate, dest)
                file_size = os.path.getsize(dest)
                return f"Task output written to {dest} ({file_size} bytes)."
            elif act in ("status", "info"):
                file_size = os.path.getsize(log_candidate)
                return f"Task ID: {task_id}\nLog File: {log_candidate} ({file_size} bytes)\nNote: Found on disk from previous session."
        return f"Error: Task '{task_id}' not found."

    if act in ("status", "info"):
        elapsed = f"{task.elapsed_seconds():.1f}s"
        details = [
            f"Task ID: {task.task_id}",
            f"Status: {task.status}",
            f"Runner: {task.runner}",
            f"Model: {task.model or 'default'}",
            f"Created At: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Elapsed: {elapsed}",
            f"Log File: {task.log_file}",
        ]
        if task.completed_at:
            details.append(f"Completed At: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if task.exit_code is not None:
            details.append(f"Exit Code: {task.exit_code}")
        if task.error:
            details.append(f"Error: {task.error}")
        if task.output_file:
            details.append(f"Designated Output File: {task.output_file}")

        snippet = task.read_output(max_lines=5).strip()
        if snippet:
            details.append(f"\nRecent Output Snippet:\n{snippet}")
        return "\n".join(details)

    elif act in ("peek", "tail"):
        output = task.read_output(max_lines=max_lines)
        header = (
            f"[{task.task_id}] Status: {task.status} | Runner: {task.runner} | "
            f"Log: {task.log_file}\n"
            f"--- Recent Output (last {max_lines} lines) ---\n"
        )
        if not output.strip():
            return header + "(No output recorded yet)"
        return header + output

    elif act in ("write_output", "output"):
        dest_path = task.write_output_file(output_file)
        file_size = os.path.getsize(dest_path)
        with open(dest_path, "r", encoding="utf-8", errors="replace") as f:
            line_count = sum(1 for _ in f)
        return (
            f"Task output successfully written to designated file:\n"
            f"Path: {dest_path}\n"
            f"Size: {file_size} bytes ({line_count} lines)\n"
            f"Task Status: {task.status}\n\n"
            f"You can now read this file directly from '{dest_path}'."
        )

    elif act in ("kill", "cancel", "stop"):
        if task.status != "RUNNING":
            return f"Task '{task.task_id}' is already {task.status} (cannot kill)."
        task.kill()
        return f"Task '{task.task_id}' has been killed successfully. Output preserved at {task.log_file}."

    elif act == "wait":
        if task.status in ("COMPLETED", "FAILED", "KILLED", "TIMEOUT"):
            return (
                f"Task '{task.task_id}' finished with status '{task.status}'.\n"
                f"Log file: {task.log_file}\n\n"
                f"{task.read_output(max_lines=max_lines)}"
            )
        if task.asyncio_task:
            try:
                await asyncio.wait_for(asyncio.shield(task.asyncio_task), timeout=timeout)
            except asyncio.TimeoutError:
                return (
                    f"Wait timed out after {timeout} seconds. Task '{task.task_id}' is still {task.status}.\n"
                    f"Log file: {task.log_file}\n"
                    f"Use manage_task(action='peek', task_id='{task.task_id}') to inspect progress."
                )
        return (
            f"Task '{task.task_id}' finished with status '{task.status}'.\n"
            f"Log file: {task.log_file}\n\n"
            f"{task.read_output(max_lines=max_lines)}"
        )
    else:
        return (
            f"Error: Unknown action '{action}'. "
            f"Supported actions are 'peek', 'status', 'write_output', 'kill', 'list', 'wait', 'start'."
        )

@mcp.tool()
def model(model_name: Optional[str] = None) -> str:
    """Sets or gets the active model to be used for subsequent prompt tool calls."""
    if model_name is not None and model_name.strip() != "":
        return set_model(model_name.strip())
    
    current = get_model()
    if current:
        return f"Current active model: '{current}'"
    return "Current active model: default (none specified)"

if __name__ == "__main__":
    mcp.run(transport="stdio")
