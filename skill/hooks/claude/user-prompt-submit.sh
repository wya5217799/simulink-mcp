#!/usr/bin/env bash
# UserPromptSubmit hook: Simulink keyword detection + 3-line MCP navigation injection
# Non-blocking: any failure → exit 0
set -uo pipefail

MAP_DOC="$HOME/.claude/skills/simulink-toolbox/map.md"
SKILL_DOC="$HOME/.claude/skills/simulink-toolbox/SKILL.md"

INPUT=$(cat)

if python3 -c "pass" 2>/dev/null; then PYTHON=python3; elif python -c "pass" 2>/dev/null; then PYTHON=python; else exit 0; fi
"$PYTHON" - <<'PYEOF' "$INPUT" "$MAP_DOC" "$SKILL_DOC" || true
import sys, json, os, re

raw = sys.argv[1] if len(sys.argv) > 1 else ""
map_doc = sys.argv[2] if len(sys.argv) > 2 else "~/.claude/skills/simulink-toolbox/map.md"
skill_doc = sys.argv[3] if len(sys.argv) > 3 else "~/.claude/skills/simulink-toolbox/SKILL.md"
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

prompt = data.get("prompt", "") or ""

PATTERN = re.compile(
    r'\b(simulink|simscape|stateflow|S-function|S函数)\b|\.slx\b|simulink-tools|\[FORCE_SL\]',
    re.IGNORECASE
)

if not PATTERN.search(prompt):
    sys.exit(0)

print("[simulink-toolbox] Simulink mode ON.")
print("1. Use named MCP tools. Active repository instructions/project overlays override this generic map.")
print("2. Avoid shell matlab/.m/find_system bypasses; use run_script only when no named MCP tool covers the operation.")
print("3. Long-running script (build/sim > 60 s) -> simulink_run_script_async + simulink_poll_script.")
print("4. Param discovery before placing -> simulink_library_lookup (cheap; 1 call replaces N retries).")
print(f"5. Reference: {skill_doc} (task-type chains + patterns) -> {map_doc} (routing).")

sys.exit(0)
PYEOF
