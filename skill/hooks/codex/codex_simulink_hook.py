#!/usr/bin/env python3
"""Codex hook for the simulink-toolbox skill.

Supported events:
- UserPromptSubmit: inject Simulink MCP routing guidance when the prompt
  mentions Simulink/Simscape/Stateflow/.slx.
- PreToolUse: deny shell MATLAB bypasses (exit 2); warn on discouraged patterns
  inside named mcp__simulink_tools__ calls (exit 0, no permissionDecision).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[2]
MAP_DOC = SKILL_ROOT / "map.md"
SKILL_DOC = SKILL_ROOT / "SKILL.md"

SIMULINK_PROMPT_RE = re.compile(
    r"(?i)\b(simulink|simscape|stateflow|s-function|s函数)\b|\.slx\b|simulink-tools|\[force_sl\]"
)


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def emit_system_message(message: str) -> None:
    # Codex-local hooks already use systemMessage in ~/.codex/hooks.json.
    emit_json({"systemMessage": message})


def user_prompt_submit(data: dict[str, Any]) -> int:
    prompt = (
        data.get("prompt")
        or data.get("message")
        or data.get("user_prompt")
        or data.get("userPrompt")
        or ""
    )
    prompt = str(prompt)
    if not SIMULINK_PROMPT_RE.search(prompt):
        return 0

    message = (
        "[simulink-toolbox] Simulink mode ON.\n"
        "- Use named mcp__simulink_tools__ tools; do not bypass via shell matlab / .m / matlab.engine / routine find_system.\n"
        "- Active repository instructions and project overlays override this generic map.\n"
        "- Long-running script (build/sim > 60 s) -> simulink_run_script_async + simulink_poll_script.\n"
        "- Param discovery before placing -> simulink_library_lookup (cheap; 1 call replaces N retries).\n"
        f"- Plan each step as: goal -> exact MCP tool -> verification tool. Reference: {SKILL_DOC} (chains) + {MAP_DOC} (routing)."
    )
    emit_system_message(message)
    return 0


def tool_name(data: dict[str, Any]) -> str:
    return str(data.get("tool_name") or data.get("toolName") or "")


def tool_input(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get("tool_input")
    if value is None:
        value = data.get("toolInput")
    return value if isinstance(value, dict) else {}


def is_shell_tool(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in {"bash", "shell", "shell_command", "functions.shell_command"}
        or "shell_command" in lowered
    )


def is_simulink_run_script_tool(name: str) -> bool:
    # Covers both simulink_run_script and simulink_run_script_async (async is a suffix).
    return "simulink_run_script" in name.lower()


MATLAB_SHELL_PATTERNS = [
    (
        "direct MATLAB executable invocation",
        re.compile(r"(?is)(?:^|[;&|]\s*|&\s*)matlab(?:\.exe)?(?=\s|$)"),
    ),
    (
        "quoted MATLAB executable invocation",
        re.compile(r"(?is)(?:^|[;&|]\s*|&\s*)[\"'][^\"'\r\n]*\\matlab(?:\.exe)?[\"']"),
    ),
    (
        "cmd /c MATLAB invocation",
        re.compile(r"(?is)\bcmd(?:\.exe)?\s+/[ck]\s+[\"']?matlab(?:\.exe)?(?=\s|$)"),
    ),
    (
        "PowerShell MATLAB batch invocation",
        re.compile(r"(?is)\bpowershell(?:\.exe)?\b[^\r\n]*\bmatlab(?:\.exe)?\b[^\r\n]*(?:-batch|-r)\b"),
    ),
    (
        "Start-Process MATLAB invocation",
        re.compile(r"(?is)\bstart-process\b[^\r\n;&|]*\bmatlab(?:\.exe)?\b"),
    ),
    (
        "Python matlab.engine invocation",
        re.compile(r"(?is)\bpython(?:\d+(?:\.\d+)?)?(?:\.exe)?\b[^\r\n]*\bmatlab\.engine\b"),
    ),
]

RUN_SCRIPT_WARNING_PATTERNS = [
    (
        "find_system inside simulink_run_script",
        re.compile(r"(?is)\bfind_system\s*\("),
    ),
    (
        "direct .m script execution inside simulink_run_script",
        re.compile(r"(?is)^\s*(?:run\s*\(?\s*)?[\"']?[^\"'\r\n;]+\.m[\"']?\s*\)?\s*;?\s*$"),
    ),
]


def shell_violation(command: str) -> str | None:
    for reason, pattern in MATLAB_SHELL_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def run_script_warning(code_or_file: str) -> str | None:
    for reason, pattern in RUN_SCRIPT_WARNING_PATTERNS:
        if pattern.search(code_or_file):
            return reason
    return None


def deny(reason: str) -> int:
    message = (
        "[simulink-toolbox] blocked: "
        f"{reason}. Use the mcp__simulink_tools__ tool map instead: {MAP_DOC}"
    )
    emit_json(
        {
            "systemMessage": message,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            },
        }
    )
    return 2


def warn(reason: str) -> int:
    message = (
        "[simulink-toolbox] warning: "
        f"{reason}. This named MCP call is allowed, but use a more specific "
        f"mcp__simulink_tools__ tool from {MAP_DOC} when one covers the operation."
    )
    emit_json({"systemMessage": message})
    return 0


def pre_tool_use(data: dict[str, Any]) -> int:
    name = tool_name(data)
    inputs = tool_input(data)

    if is_shell_tool(name):
        command = str(inputs.get("command") or inputs.get("cmd") or "")
        reason = shell_violation(command)
        if reason:
            return deny(reason)
        return 0

    if is_simulink_run_script_tool(name):
        code_or_file = str(inputs.get("code_or_file") or "")
        reason = run_script_warning(code_or_file)
        if reason:
            return warn(reason)
        return 0

    return 0


def main() -> int:
    if len(sys.argv) < 2:
        return 0
    event = sys.argv[1].strip().lower()
    data = load_payload()
    if event in {"user-prompt-submit", "userpromptsubmit"}:
        return user_prompt_submit(data)
    if event in {"pre-tool-use", "pretooluse"}:
        return pre_tool_use(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
