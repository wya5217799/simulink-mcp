# simulink-mcp

**Simulink MCP tools + Claude/Codex skill** — give AI agents structured access to Simulink models via the MATLAB Engine for Python.

## What's inside

| Component | Path | What it does |
|---|---|---|
| **MCP Server** | `server/` | 30 FastMCP tools: model lifecycle, parameters, diagnostics, runtime, capture |
| **MATLAB Helpers** | `matlab/` | 32 `.m` scripts that implement each tool on the MATLAB side |
| **Claude/Codex Skill** | `skill/` | Routing guide (SKILL.md, map.md, patterns) + hooks that steer AI toward MCP tools |

---

## Quick install (Windows, one command)

```powershell
git clone https://github.com/wlin4480/simulink-mcp
cd simulink-mcp
.\install.ps1
```

The installer:
1. Copies the skill to `~\.shared-skills\simulink-toolbox`
2. Creates junction links for Claude Code (`~\.claude\skills\`) and Codex (`~\.codex\skills\`)
3. Wires the hooks in `~\.claude\settings.json` and `~\.codex\hooks.json`
4. Prints the MCP server config snippet to paste into Claude Desktop

---

## MCP server setup

### Prerequisites

- MATLAB R2022b or later with the Simulink toolbox
- Python 3.10+

### Install

`install.ps1` handles this automatically. To install manually:

```powershell
# 1. Install the server as a global CLI command (no path dependency)
pip install -e C:\path\to\simulink-mcp

# 2. Install matlabengine — version must match your MATLAB release
pip install matlabengine==25.2   # R2025b
pip install matlabengine==24.2   # R2024b
```

After `pip install -e`, the `simulink-mcp` command is available system-wide.
You can clone the repo anywhere and move it later without breaking Claude Desktop.

### Claude Desktop config

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "simulink-tools": {
      "command": "simulink-mcp",
      "env": {
        "SLX_WORKSPACE": "C:\\path\\to\\your\\models"
      }
    }
  }
}
```

Restart Claude Desktop. The server cold-starts in ~20 s on first tool call.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `SLX_WORKSPACE` | Current directory | Directory to search for `.slx` model files |
| `SLX_HELPERS_PATH` | Bundled `matlab/` | Override path to the MATLAB helper scripts |

---

## 32 MCP tools

### Model lifecycle
`simulink_load_model` · `simulink_create_model` · `simulink_close_model` · `simulink_loaded_models` · `simulink_model_status` · `simulink_save_model`

### Structure & discovery
`simulink_get_block_tree` · `simulink_explore_block` · `simulink_describe_block_ports` · `simulink_trace_port_connections` · `simulink_library_lookup`

### Parameters
`simulink_query_params` · `simulink_set_block_params` · `simulink_patch_and_verify`

### Build & wiring
`simulink_add_block` · `simulink_add_subsystem` · `simulink_connect_ports` · `simulink_delete_block`

### Diagnostics
`simulink_compile_diagnostics` · `simulink_step_diagnostics` · `simulink_solver_audit`

### Advanced
`simulink_block_workspace_dependency` · `simulink_powerlib_net_query`

### Script execution
`simulink_run_script` · `simulink_run_script_async` · `simulink_poll_script`

### Visual capture
`simulink_screenshot` · `simulink_capture_figure`

### Runtime
`simulink_workspace_set` · `simulink_run_window` · `simulink_runtime_reset` · `simulink_signal_snapshot`

---

## Skill: Claude Code + Codex

The `skill/` directory is the `simulink-toolbox` skill — loaded by Claude Code and Codex to route Simulink-related tasks to MCP tools instead of shell MATLAB calls.

After `install.ps1`, invoke with `/simulink-toolbox` in Claude Code, or any Simulink-related prompt triggers it automatically via hooks.

### Hooks

| Platform | File | Effect |
|---|---|---|
| Claude Code | `hooks/claude/user-prompt-submit.sh` | Injects routing reminder on Simulink keywords |
| Claude Code | `hooks/claude/pre-tool-use.sh` | Blocks `Bash` calls that invoke MATLAB directly |
| Codex | `hooks/codex/codex_simulink_hook.py` | Same + warns on `find_system` inside run_script |

### Patterns

| Pattern | When to use |
|---|---|
| `patterns/build-and-verify.md` | Building a new model from scratch |
| `patterns/debug-existing-model.md` | Diagnosing errors in an existing model |
| `patterns/trace-connectivity.md` | Tracing signal paths and port connections |
| `patterns/param-sweep.md` | Long-running parameter sweeps |

---

## Project structure

```
simulink-mcp/
├── install.ps1              # One-click installer (Windows)
├── requirements.txt
├── server/
│   ├── server.py            # FastMCP entry point
│   ├── simulink_tools.py    # All 30 tool implementations
│   ├── matlab_session.py    # MATLAB Engine session manager
│   └── exceptions.py
├── matlab/
│   └── slx_*.m              # 32 MATLAB helper scripts
└── skill/
    ├── SKILL.md             # Skill entry point
    ├── map.md               # Intent → tool routing table
    ├── INVARIANTS.md        # Design constraints
    ├── index.json           # Tool inventory
    ├── patterns/            # Step-by-step task patterns
    └── hooks/               # Claude + Codex hooks
```

---

## License

MIT
