#!/usr/bin/env bash
# PreToolUse hook: block Bash-layer matlab/.m calls; MCP tools are always allowed
# Non-blocking on python failure; exit 2 = deny
set -uo pipefail

MAP_DOC="$HOME/.claude/skills/simulink-toolbox/map.md"
SKILL_DOC="$HOME/.claude/skills/simulink-toolbox/SKILL.md"  # used in user-prompt-submit.sh

INPUT=$(cat)

if python3 -c "pass" 2>/dev/null; then PYTHON=python3; elif python -c "pass" 2>/dev/null; then PYTHON=python; else exit 0; fi
"$PYTHON" - <<'PYEOF' "$INPUT" "$MAP_DOC"
import sys, json, re

raw = sys.argv[1] if len(sys.argv) > 1 else ""
map_doc = sys.argv[2] if len(sys.argv) > 2 else "~/.claude/skills/simulink-toolbox/map.md"
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

tool_name  = data.get("tool_name", "") or ""
tool_input = data.get("tool_input", {}) or {}

# MCP simulink tools are always allowed (run_script* included)
DENY_TOOLS = set()

# Deny patterns: Bash-layer MATLAB escape paths.
# Each pattern matches only when matlab is invoked as an executable, NOT as a
# substring in file paths, grep terms, or other arguments.
# Ported from codex_simulink_hook.py MATLAB_SHELL_PATTERNS (keep in sync).
MATLAB_SHELL_PATTERNS = [
    ("direct MATLAB executable invocation",
     re.compile(r"(?is)(?:^|[;&|]\s*|&\s*)matlab(?:\.exe)?(?=\s|$)")),
    ("quoted MATLAB executable invocation",
     re.compile(r"(?is)(?:^|[;&|]\s*|&\s*)[\"'][^\"'\r\n]*[/\\]matlab(?:\.exe)?[\"']")),
    ("cmd /c MATLAB invocation",
     re.compile(r"(?is)\bcmd(?:\.exe)?\s+/[ck]\s+[\"']?matlab(?:\.exe)?(?=\s|$)")),
    ("PowerShell MATLAB batch invocation",
     re.compile(r"(?is)\bpowershell(?:\.exe)?\b[^\r\n]*\bmatlab(?:\.exe)?\b[^\r\n]*(?:-batch|-r)\b")),
    ("Start-Process MATLAB invocation",
     re.compile(r"(?is)\bstart-process\b[^\r\n;&|]*\bmatlab(?:\.exe)?\b")),
    ("Python matlab.engine invocation",
     re.compile(r"(?is)\bpython(?:\d+(?:\.\d+)?)?(?:\.exe)?\b[^\r\n]*\bmatlab\.engine\b")),
]

def shell_violation(cmd):
    for reason, pattern in MATLAB_SHELL_PATTERNS:
        if pattern.search(cmd):
            return reason
    return None

cmd = tool_input.get("command", "") or ""
in_deny = (tool_name in DENY_TOOLS) or (tool_name == "Bash" and shell_violation(cmd) is not None)

if not in_deny:
    sys.exit(0)

reason = shell_violation(cmd) or "blocked tool"
print(
    f"[simulink-toolbox] blocked: {reason}. Use MCP tool instead.\n"
    f"Check map.md for alternatives: {map_doc}",
    file=sys.stderr
)
sys.exit(2)
PYEOF
