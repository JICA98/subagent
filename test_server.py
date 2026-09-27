import os
import pytest
from server import (
    sanitize_prompt,
    set_model,
    get_model,
    build_command,
    CMD_PATH,
    AGY_PATH,
    OPENCODE_PATH,
    PI_PATH,
    CODEX_PATH,
    TASKS_DIR,
    SubagentTask,
    _TASKS,
    manage_task,
)

def test_sanitize_prompt():
    raw = "Hello\nworld!\r\nThis is a multiline\nprompt."
    expected = "Hello world!  This is a multiline prompt."
    assert sanitize_prompt(raw) == expected

def test_model_state():
    set_model(None)
    assert get_model() is None
    
    msg = set_model("gemini-1.5-pro")
    assert get_model() == "gemini-1.5-pro"
    assert "gemini-1.5-pro" in msg

def test_build_command_default_agy():
    set_model(None)
    cmd_no_model = build_command("Test prompt")
    assert cmd_no_model == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "-p", "Test prompt"]

    set_model("claude-3-5-sonnet")
    cmd_with_model = build_command("Test prompt")
    assert cmd_with_model == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "claude-3-5-sonnet", "-p", "Test prompt"]

    cmd_sonnet = build_command("Review prompt", override_model="sonnet-4.6")
    assert cmd_sonnet == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "claude-sonnet-4-6", "-p", "Review prompt"]

    cmd_gemini_38 = build_command("Test prompt", override_model="gemini-3.8-flash")
    assert cmd_gemini_38 == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "gemini-3.8-flash-high", "-p", "Test prompt"]

    cmd_gemini_38_high = build_command("Test prompt", override_model="gemini-3.8-flash-high")
    assert cmd_gemini_38_high == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "gemini-3.8-flash-high", "-p", "Test prompt"]

    cmd_gemini_38_med = build_command("Test prompt", override_model="gemini-3.8-flash-medium")
    assert cmd_gemini_38_med == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "gemini-3.8-flash-medium", "-p", "Test prompt"]

    cmd_gemini_37 = build_command("Test prompt", override_model="gemini-3.7-flash")
    assert cmd_gemini_37 == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "gemini-3.7-flash-high", "-p", "Test prompt"]

    cmd_gemini_37_med = build_command("Test prompt", override_model="gemini-3.7-flash-medium")
    assert cmd_gemini_37_med == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "gemini-3.7-flash-medium", "-p", "Test prompt"]

    cmd_opus = build_command("Deep prompt", override_model="opus-4.6")
    assert cmd_opus == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "claude-opus-4-6-thinking", "-p", "Deep prompt"]

def test_build_command_deepseek_cmd():
    set_model(None)

    cmd_deepseek = build_command("Deepseek test prompt", override_model="deepseek-v4-pro")
    assert cmd_deepseek == [CMD_PATH, "--dangerously-skip-permissions", "--model", "deepseek-v4-pro", "-p", "Deepseek test prompt"]

    cmd_deepseek_alias = build_command("Deepseek test prompt", override_model="deepseek")
    assert cmd_deepseek_alias == [CMD_PATH, "--dangerously-skip-permissions", "--model", "deepseek-v4-pro", "-p", "Deepseek test prompt"]

    set_model("deepseek-v4-pro")
    cmd_global_deepseek = build_command("Global model prompt")
    assert cmd_global_deepseek == [CMD_PATH, "--dangerously-skip-permissions", "--model", "deepseek-v4-pro", "-p", "Global model prompt"]

    # Override back to non-deepseek model
    cmd_override_non_deepseek = build_command("Override prompt", override_model="sonnet-4.6")
    assert cmd_override_non_deepseek == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "claude-sonnet-4-6", "-p", "Override prompt"]

    set_model(None)

def test_build_command_opencode():
    set_model(None)

    cmd_opencode_deepseek = build_command("Test OpenCode", override_model="deepseek-v4-flash-free")
    assert cmd_opencode_deepseek == [OPENCODE_PATH, "run", "-m", "opencode/deepseek-v4-flash-free", "--auto", "Test OpenCode"]

    cmd_opencode_muse = build_command("Test Muse", override_model="muse-spark-1.3")
    assert cmd_opencode_muse == [OPENCODE_PATH, "run", "-m", "opencode/muse-spark-1.2-contributor-free", "--auto", "Test Muse"]

    cmd_opencode_muse_alias = build_command("Test Muse", override_model="muse-spark")
    assert cmd_opencode_muse_alias == [OPENCODE_PATH, "run", "-m", "opencode/muse-spark-1.2-contributor-free", "--auto", "Test Muse"]

    set_model("deepseek-v4-flash-free")
    cmd_global_opencode = build_command("Global opencode prompt")
    assert cmd_global_opencode == [OPENCODE_PATH, "run", "-m", "opencode/deepseek-v4-flash-free", "--auto", "Global opencode prompt"]
    set_model(None)

def test_build_command_pi():
    set_model(None)

    cmd_pi = build_command("Test pi", override_model="pi/stealth/ox-alpha")
    assert cmd_pi == [PI_PATH, "--mode", "text", "--no-session", "--model", "stealth/ox-alpha", "-p", "Test pi"]

    cmd_pi_alias = build_command("Test pi", override_model="ox-alpha")
    assert cmd_pi_alias == [PI_PATH, "--mode", "text", "--no-session", "--model", "stealth/ox-alpha", "-p", "Test pi"]

    set_model("pi")
    cmd_global_pi = build_command("Global pi prompt")
    assert cmd_global_pi == [PI_PATH, "--mode", "text", "--no-session", "--model", "stealth/ox-alpha", "-p", "Global pi prompt"]

    # Override back to agy
    cmd_override_agy = build_command("Override to agy", override_model="sonnet-4.6")
    assert cmd_override_agy == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "claude-sonnet-4-6", "-p", "Override to agy"]

    set_model(None)

def test_build_command_codex():
    set_model(None)

    # gpt-6-luna routes to codex
    cmd_luna = build_command("Test luna prompt", override_model="gpt-6-luna")
    assert cmd_luna == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-luna", "--", "Test luna prompt"]

    # aliases
    cmd_luna_space = build_command("Test space alias", override_model="gpt 6 luna")
    assert cmd_luna_space == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-luna", "--", "Test space alias"]

    cmd_codex = build_command("Test codex alias", override_model="codex")
    assert cmd_codex == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-luna", "--", "Test codex alias"]

    cmd_short_luna = build_command("Test short luna", override_model="luna")
    assert cmd_short_luna == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-luna", "--", "Test short luna"]

    # codex/<model> prefix
    cmd_codex_astra = build_command("Test astra", override_model="codex/gpt-6-astra")
    assert cmd_codex_astra == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-astra", "--", "Test astra"]

    # reasoning effort with codex
    cmd_effort = build_command("Test effort", override_model="gpt-6-luna", effort="high")
    assert cmd_effort == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-luna", "-c", 'model_reasoning_effort="high"', "--", "Test effort"]

    # global model set to gpt-6-luna
    set_model("gpt-6-luna")
    cmd_global_codex = build_command("Global codex prompt")
    assert cmd_global_codex == [CODEX_PATH, "exec", "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check", "-m", "gpt-6-luna", "--", "Global codex prompt"]

    # override back to agy
    cmd_override_agy = build_command("Override to agy", override_model="sonnet-4.6")
    assert cmd_override_agy == [AGY_PATH, "--dangerously-skip-permissions", "--print-timeout", "45m", "--model", "claude-sonnet-4-6", "-p", "Override to agy"]

    set_model(None)

@pytest.mark.anyio
async def test_subagent_task_lifecycle_and_manage_task(tmp_path):
    test_id = "task_test_123"
    log_file = os.path.join(TASKS_DIR, f"{test_id}.log")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("Line 1: started\nLine 2: processing\nLine 3: finished\n")

    task = SubagentTask(
        task_id=test_id,
        prompt="Test prompt",
        runner="codex",
        model="gpt-6-luna",
        cmd=["echo", "test"],
        log_file=log_file,
    )
    _TASKS[test_id] = task

    # Test peek
    peek_res = await manage_task(action="peek", task_id=test_id, max_lines=2)
    assert "Line 2: processing" in peek_res
    assert "Line 3: finished" in peek_res
    assert "Line 1: started" not in peek_res

    # Test status
    status_res = await manage_task(action="status", task_id=test_id)
    assert test_id in status_res
    assert "codex" in status_res
    assert "gpt-6-luna" in status_res
    assert log_file in status_res

    # Test write_output to /tmp designated folder
    out_res = await manage_task(action="write_output", task_id=test_id)
    expected_out = os.path.join(TASKS_DIR, f"{test_id}_output.txt")
    assert expected_out in out_res
    assert os.path.exists(expected_out)
    with open(expected_out, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Line 1: started\nLine 2: processing\nLine 3: finished\n" == content

    # Test custom output_file
    custom_out = os.path.join(str(tmp_path), "custom_dest.txt")
    out_custom_res = await manage_task(action="write_output", task_id=test_id, output_file=custom_out)
    assert custom_out in out_custom_res
    assert os.path.exists(custom_out)

    # Test list
    list_res = await manage_task(action="list")
    assert test_id in list_res

    # Test kill
    kill_res = await manage_task(action="kill", task_id=test_id)
    assert "killed successfully" in kill_res
    assert task.status == "KILLED"

    # Cleanup
    _TASKS.pop(test_id, None)
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(expected_out):
        os.remove(expected_out)

@pytest.mark.anyio
async def test_execute_task_background_and_wait():
    from server import execute_task
    res = await execute_task(
        ["bash", "-c", "echo lineA; sleep 0.1; echo lineB"],
        "prompt background",
        "gpt-6-luna",
        background=True,
    )
    assert "Task started in background with ID:" in res
    tid = res.split("ID: ")[1].split()[0]

    status_out = await manage_task(action="status", task_id=tid)
    assert tid in status_out
    assert "RUNNING" in status_out or "COMPLETED" in status_out

    wait_out = await manage_task(action="wait", task_id=tid, timeout=5)
    assert "lineB" in wait_out
    assert "COMPLETED" in wait_out

    write_out = await manage_task(action="write_output", task_id=tid)
    assert "Task output successfully written" in write_out
    expected_out = os.path.join(TASKS_DIR, f"{tid}_output.txt")
    assert os.path.exists(expected_out)
    with open(expected_out, "r", encoding="utf-8") as f:
        content = f.read()
    assert "lineA" in content
    assert "lineB" in content

    # Cleanup
    _TASKS.pop(tid, None)
    log_file = os.path.join(TASKS_DIR, f"{tid}.log")
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(expected_out):
        os.remove(expected_out)

@pytest.mark.anyio
async def test_execute_task_sync_returns_task_id_and_output():
    from server import execute_task
    res = await execute_task(
        ["bash", "-c", "echo sync_test_line"],
        "prompt sync",
        "gpt-6-luna",
        background=False,
    )
    assert "[Task ID: task_" in res
    assert "Runner: bash" in res
    assert "Model: gpt-6-luna" in res
    assert "Status: COMPLETED" in res
    assert f"Log: {TASKS_DIR}/task_" in res
    assert "sync_test_line" in res

    tid = res.split("[Task ID: ")[1].split("]")[0]
    assert tid in _TASKS
    assert _TASKS[tid].status == "COMPLETED"

    # Cleanup
    _TASKS.pop(tid, None)
    log_file = os.path.join(TASKS_DIR, f"{tid}.log")
    if os.path.exists(log_file):
        os.remove(log_file)


