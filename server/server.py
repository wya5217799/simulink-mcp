"""server/server.py — FastMCP entry point for the standalone simulink-mcp server.

Registers 33 generic Simulink tools. Start with:
    python -m server.server

Or add to claude_desktop_config.json:
    "simulink-tools": {
        "command": "python",
        "args": ["-m", "server.server"],
        "env": {
            "PYTHONPATH": "/path/to/simulink-mcp",
            "SLX_WORKSPACE": "/path/to/your/models"
        }
    }
"""

import sys
import os
from pathlib import Path

# Ensure the package root is on sys.path when run as __main__
_pkg_root = Path(__file__).resolve().parents[1]
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from fastmcp import FastMCP
from server.simulink_tools import (
    # Model lifecycle
    simulink_load_model,
    simulink_create_model,
    simulink_close_model,
    simulink_loaded_models,
    # Save / status
    simulink_model_status,
    simulink_save_model,
    # Structure viewing
    simulink_get_block_tree,
    simulink_describe_block_ports,
    simulink_trace_port_connections,
    simulink_explore_block,
    # Parameter operations
    simulink_query_params,
    simulink_set_block_params,
    simulink_library_lookup,
    # Modeling operations
    simulink_add_block,
    simulink_add_subsystem,
    simulink_connect_ports,
    simulink_delete_block,
    # Diagnostics
    simulink_compile_diagnostics,
    simulink_step_diagnostics,
    simulink_solver_audit,
    # Advanced
    simulink_patch_and_verify,
    simulink_block_workspace_dependency,
    simulink_powerlib_net_query,
    # Escape hatch
    simulink_run_script,
    simulink_run_script_async,
    simulink_poll_script,
    # Visual capture
    simulink_screenshot,
    simulink_capture_figure,
    # General runtime
    simulink_workspace_set,
    simulink_run_window,
    simulink_runtime_reset,
    simulink_signal_snapshot,
    # Health check
    simulink_ping,
)

mcp = FastMCP(
    "simulink-tools",
    instructions=(
        "Generic Simulink MCP tools (33 total) for Claude and Codex. "
        "Use simulink_library_lookup to discover block parameters before placing. "
        "Use simulink_run_script for build scripts (prefix output lines with 'RESULT: ' to surface them). "
        "Use simulink_query_params for reading params (1 or N blocks, all or selected params). "
        "Use simulink_connect_ports for all connection operations (name addressing only). "
        "Use simulink_explore_block to get ports + source/sink connections in one call. "
        "Use simulink_model_status before saving or closing when dirty state matters. "
        "Use simulink_signal_snapshot for logged/ToWorkspace/block-output values. "
        "Use simulink_workspace_set and simulink_run_window for runtime control. "
        "All tools share one MATLAB engine (lazy-started on first call, ~20s cold start). "
        "Set SLX_WORKSPACE env var to point at a directory containing your .slx files."
    ),
)

PUBLIC_TOOLS = [
    simulink_load_model,
    simulink_create_model,
    simulink_close_model,
    simulink_loaded_models,
    simulink_model_status,
    simulink_save_model,
    simulink_get_block_tree,
    simulink_describe_block_ports,
    simulink_trace_port_connections,
    simulink_explore_block,
    simulink_query_params,
    simulink_set_block_params,
    simulink_library_lookup,
    simulink_add_block,
    simulink_add_subsystem,
    simulink_connect_ports,
    simulink_delete_block,
    simulink_compile_diagnostics,
    simulink_step_diagnostics,
    simulink_solver_audit,
    simulink_patch_and_verify,
    simulink_block_workspace_dependency,
    simulink_powerlib_net_query,
    simulink_run_script,
    simulink_run_script_async,
    simulink_poll_script,
    simulink_screenshot,
    simulink_capture_figure,
    simulink_workspace_set,
    simulink_run_window,
    simulink_runtime_reset,
    simulink_signal_snapshot,
    simulink_ping,
]

for tool in PUBLIC_TOOLS:
    mcp.add_tool(tool)

def main() -> None:
    """CLI entry point — called by ``simulink-mcp`` console script."""
    mcp.run()


if __name__ == "__main__":
    main()
