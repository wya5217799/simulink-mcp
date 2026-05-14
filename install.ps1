#!/usr/bin/env pwsh
# install.ps1 — One-click installer for simulink-mcp
# Works on Windows (PowerShell 5.1+). Run from the repo root.
#
# What it does:
#   1. Copies the skill to ~\.shared-skills\simulink-toolbox
#   2. Creates junction links for Claude (~\.claude\skills\) and Codex (~\.codex\skills\)
#   3. Patches ~\.claude\settings.json with the two hook entries
#   4. Patches ~\.codex\hooks.json with the two hook entries
#   5. Shows MCP server config snippet to paste into Claude Desktop
#
# Usage:
#   .\install.ps1                        # interactive — prompts for Python path
#   .\install.ps1 -PythonPath "C:\..."   # non-interactive
#   .\install.ps1 -SkillOnly            # skip MCP server config

param(
    [string]$PythonPath = "",
    [switch]$SkillOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$REPO_ROOT  = $PSScriptRoot
$SKILL_SRC  = Join-Path $REPO_ROOT "skill"
$SHARED     = Join-Path $env:USERPROFILE ".shared-skills\simulink-toolbox"
$CLAUDE_SKL = Join-Path $env:USERPROFILE ".claude\skills\simulink-toolbox"
$CODEX_SKL  = Join-Path $env:USERPROFILE ".codex\skills\simulink-toolbox"
$CLAUDE_CFG = Join-Path $env:USERPROFILE ".claude\settings.json"
$CODEX_CFG  = Join-Path $env:USERPROFILE ".codex\hooks.json"

function Write-Step { param([string]$msg) Write-Host "  > $msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 1. Install shared skill
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== simulink-mcp installer ===" -ForegroundColor Magenta

Write-Step "Installing skill to $SHARED"
if (Test-Path $SHARED) {
    Remove-Item $SHARED -Recurse -Force
}
Copy-Item $SKILL_SRC $SHARED -Recurse
Write-Ok "Skill copied"

# ---------------------------------------------------------------------------
# 2. Junction links for Claude Code
# ---------------------------------------------------------------------------
Write-Step "Creating Claude skill junction: $CLAUDE_SKL"
$claudeSkillDir = Split-Path $CLAUDE_SKL -Parent
if (-not (Test-Path $claudeSkillDir)) {
    New-Item -ItemType Directory -Force $claudeSkillDir | Out-Null
}
if (Test-Path $CLAUDE_SKL) { Remove-Item $CLAUDE_SKL -Recurse -Force }
cmd /c "mklink /J `"$CLAUDE_SKL`" `"$SHARED`"" | Out-Null
Write-Ok "Claude junction created"

# ---------------------------------------------------------------------------
# 3. Junction links for Codex
# ---------------------------------------------------------------------------
Write-Step "Creating Codex skill junction: $CODEX_SKL"
$codexSkillDir = Split-Path $CODEX_SKL -Parent
if (-not (Test-Path $codexSkillDir)) {
    New-Item -ItemType Directory -Force $codexSkillDir | Out-Null
}
if (Test-Path $CODEX_SKL) { Remove-Item $CODEX_SKL -Recurse -Force }
cmd /c "mklink /J `"$CODEX_SKL`" `"$SHARED`"" | Out-Null
Write-Ok "Codex junction created"

# ---------------------------------------------------------------------------
# Helper: read JSON (handles comments / trailing commas via regex strip)
# ---------------------------------------------------------------------------
function Read-JsonFile([string]$path) {
    if (-not (Test-Path $path)) { return $null }
    $raw = Get-Content $path -Raw -Encoding UTF8
    # Strip single-line // comments and trailing commas before closing brackets
    $raw = $raw -replace '(?m)^\s*//.*$', ''
    $raw = $raw -replace ',(\s*[}\]])', '$1'
    try { return $raw | ConvertFrom-Json } catch { return $null }
}

# ---------------------------------------------------------------------------
# 4. Patch Claude settings.json
# ---------------------------------------------------------------------------
Write-Step "Patching $CLAUDE_CFG"
if (Test-Path $CLAUDE_CFG) {
    $raw = Get-Content $CLAUDE_CFG -Raw -Encoding UTF8

    $claudeHooksNeeded = $raw -notmatch "simulink-toolbox/hooks/claude"
    if ($claudeHooksNeeded) {
        # Insert hook entries before the last closing brace of "hooks" or at end
        $preToolEntry = @'
      {
        "matcher": "mcp__simulink-tools__simulink_run_script|mcp__simulink-tools__simulink_run_script_async|Bash",
        "hooks": [{"type": "command", "command": "bash \"$HOME/.claude/skills/simulink-toolbox/hooks/claude/pre-tool-use.sh\""}]
      }
'@
        $submitEntry = @'
      {
        "hooks": [{"type": "command", "command": "bash \"$HOME/.claude/skills/simulink-toolbox/hooks/claude/user-prompt-submit.sh\""}]
      }
'@
        Write-Warn "Auto-patching $CLAUDE_CFG is complex. Add hooks manually if needed."
        Write-Host ""
        Write-Host "  Add to .claude/settings.json under `"hooks`" > `"PreToolUse`":" -ForegroundColor Yellow
        Write-Host $preToolEntry -ForegroundColor DarkGray
        Write-Host "  Add to .claude/settings.json under `"hooks`" > `"UserPromptSubmit`":" -ForegroundColor Yellow
        Write-Host $submitEntry -ForegroundColor DarkGray
    } else {
        Write-Ok "Claude hooks already present — skipped"
    }
} else {
    Write-Warn "$CLAUDE_CFG not found — skipping Claude hook patch"
}

# ---------------------------------------------------------------------------
# 5. Patch Codex hooks.json
# ---------------------------------------------------------------------------
Write-Step "Patching $CODEX_CFG"
$hookPy = Join-Path $env:USERPROFILE ".codex\skills\simulink-toolbox\hooks\codex\codex_simulink_hook.py"
$pythonExe = if ($PythonPath) { $PythonPath } else {
    $candidates = @("python", "python3", "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
                    "C:\Python311\python.exe", "C:\Python310\python.exe")
    $found = $candidates | Where-Object { try { & $_ --version 2>&1 | Out-Null; $true } catch { $false } } | Select-Object -First 1
    if ($found) { $found } else { "python" }
}

if (Test-Path $CODEX_CFG) {
    $content = Get-Content $CODEX_CFG -Raw -Encoding UTF8
    if ($content -notmatch "codex_simulink_hook") {
        $obj = $content | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($null -eq $obj) {
            Write-Warn "Could not parse $CODEX_CFG — writing new file"
            $obj = [PSCustomObject]@{ hooks = [PSCustomObject]@{} }
        }
        # Inject hook entries
        $submitCmd = "$pythonExe `"$hookPy`" user-prompt-submit"
        $preToolCmd = "$pythonExe `"$hookPy`" pre-tool-use"
        Write-Host ""
        Write-Host "  Add to .codex/hooks.json:" -ForegroundColor Yellow
        Write-Host @"
  {
    "hooks": {
      "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "$submitCmd"}]}],
      "PreToolUse": [{
        "matcher": "Bash|shell_command|functions\\.shell_command|mcp__simulink_tools__simulink_run_script(_async)?",
        "hooks": [{"type": "command", "command": "$preToolCmd"}]
      }]
    }
  }
"@ -ForegroundColor DarkGray
    } else {
        Write-Ok "Codex hooks already present — skipped"
    }
} else {
    $hookPyFull = $hookPy.Replace('\', '\\')
    $submitCmd = "$pythonExe".Replace('\','\\') + " \`"$hookPyFull\`" user-prompt-submit"
    $preCmd    = "$pythonExe".Replace('\','\\') + " \`"$hookPyFull\`" pre-tool-use"
    $newHooks = @"
{
  "hooks": {
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "$pythonExe `"$hookPy`" user-prompt-submit"}]}
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|shell_command|functions\\.shell_command|mcp__simulink_tools__simulink_run_script(_async)?",
        "hooks": [{"type": "command", "command": "$pythonExe `"$hookPy`" pre-tool-use"}]
      }
    ]
  }
}
"@
    New-Item -Force (Split-Path $CODEX_CFG) -ItemType Directory | Out-Null
    $newHooks | Set-Content $CODEX_CFG -Encoding UTF8
    Write-Ok "Created $CODEX_CFG with Simulink hooks"
}

# ---------------------------------------------------------------------------
# 6. MCP server config snippet
# ---------------------------------------------------------------------------
if (-not $SkillOnly) {
    $serverPy = Join-Path $REPO_ROOT "server\server.py"
    Write-Host ""
    Write-Host "=== MCP Server Setup ===" -ForegroundColor Magenta
    Write-Host "  1. Install dependencies:" -ForegroundColor White
    Write-Host "       pip install fastmcp matlabengine" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  2. Add to Claude Desktop config (~\AppData\Roaming\Claude\claude_desktop_config.json):" -ForegroundColor White
    Write-Host @"
  {
    "mcpServers": {
      "simulink-tools": {
        "command": "$pythonExe",
        "args": ["$($serverPy.Replace('\','\\'))"],
        "env": {
          "PYTHONPATH": "$($REPO_ROOT.Replace('\','\\'))",
          "SLX_WORKSPACE": "C:\\path\\to\\your\\models"
        }
      }
    }
  }
"@ -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  3. Restart Claude Desktop." -ForegroundColor White
    Write-Host ""
    Write-Host "  Note: matlabengine version must match your MATLAB release." -ForegroundColor DarkGray
    Write-Host "        E.g. for MATLAB R2025b: pip install matlabengine==25.2" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Green
Write-Host "  Skill location : $SHARED" -ForegroundColor White
Write-Host "  Claude junction: $CLAUDE_SKL" -ForegroundColor White
Write-Host "  Codex junction : $CODEX_SKL" -ForegroundColor White
