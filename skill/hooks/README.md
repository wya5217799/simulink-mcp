# simulink-toolbox hooks

Platform-specific hook implementations. Run `install.ps1` from the repo root — it wires everything automatically.

## What the hooks do

| Hook | Event | Action |
|---|---|---|
| `claude/user-prompt-submit.sh` | UserPromptSubmit | Injects MCP-first routing note when prompt mentions Simulink/.slx |
| `claude/pre-tool-use.sh` | PreToolUse | Blocks Bash-layer MATLAB shell calls (exit 2 = deny) |
| `codex/codex_simulink_hook.py` | UserPromptSubmit + PreToolUse | Same as Claude but for Codex, plus run_script warnings |

## Manual wiring (if not using install.ps1)

## Shared root

The canonical skill is installed at:

```text
%USERPROFILE%\.shared-skills\simulink-toolbox
```

Both platform installs are junctions to this shared root:

```text
%USERPROFILE%\.codex\skills\simulink-toolbox   -> junction
%USERPROFILE%\.claude\skills\simulink-toolbox  -> junction
```

## Codex hook subfolder: hooks\codex\

**File:** `hooks\codex\codex_simulink_hook.py`

Wired in `%USERPROFILE%\.codex\hooks.json` via:

```json
"command": "python \"%USERPROFILE%\\.codex\\skills\\simulink-toolbox\\hooks\\codex\\codex_simulink_hook.py\" user-prompt-submit"
```

and

```json
"command": "python \"%USERPROFILE%\\.codex\\skills\\simulink-toolbox\\hooks\\codex\\codex_simulink_hook.py\" pre-tool-use"
```

Active events:

- `UserPromptSubmit`: when the prompt mentions Simulink, Simscape, Stateflow,
  `.slx`, `simulink-tools`, or `[FORCE_SL]`, inject a short MCP-first routing
  reminder through `systemMessage`.
- `PreToolUse`: block (exit 2) shell escape paths that call MATLAB directly, use
  Python `matlab.engine`, or bypass the tool map. Warn (exit 0, non-blocking) on
  `find_system` and direct `.m` execution inside `simulink_run_script`.

Manual smoke test:

```powershell
$p = 'python'
$s = "$env:USERPROFILE\.codex\skills\simulink-toolbox\hooks\codex\codex_simulink_hook.py"
@{ prompt = 'check this Simulink .slx model' } | ConvertTo-Json -Compress | & $p $s user-prompt-submit
@{ tool_name = 'functions.shell_command'; tool_input = @{ command = 'matlab -batch "disp(1)"' } } | ConvertTo-Json -Compress | & $p $s pre-tool-use
```

Rollback: remove the simulink-toolbox entries from `%USERPROFILE%\.codex\hooks.json`.

## Claude hook subfolder: hooks\claude\

**Files:**

- `hooks\claude\pre-tool-use.sh`
- `hooks\claude\user-prompt-submit.sh`

Wired in `%USERPROFILE%\.claude\settings.json` via:

```json
"command": "bash \"$HOME/.claude/skills/simulink-toolbox/hooks/claude/pre-tool-use.sh\""
```

and

```json
"command": "bash \"$HOME/.claude/skills/simulink-toolbox/hooks/claude/user-prompt-submit.sh\""
```

Active events:

- `UserPromptSubmit`: same as Codex — injects MCP routing reminder on Simulink
  keywords.
- `PreToolUse`: blocks Bash-layer MATLAB escape paths (same deny patterns as
  Codex). Does **not** emit the `find_system` / `.m` warn-on-run_script check
  that the Codex hook has — that gap is intentional (Claude's tool permissions
  already gate MCP calls).

Manual smoke test:

```powershell
echo '{"prompt":"inspect this Simulink .slx model"}' | bash "$HOME/.claude/skills/simulink-toolbox/hooks/claude/user-prompt-submit.sh"
echo '{"tool_name":"Bash","tool_input":{"command":"matlab -batch \"disp(1)\""}}' | bash "$HOME/.claude/skills/simulink-toolbox/hooks/claude/pre-tool-use.sh"
```

## Consistency check

```powershell
python "$env:USERPROFILE\.shared-skills\simulink-toolbox\validate_consistency.py"
python "$env:USERPROFILE\.shared-skills\simulink-toolbox\validate_layout.py"
```

Both must exit `0`.
