# matlab/ — General Simulink Helper Scripts

These `.m` scripts implement the backend for the 30 generic MCP tools.
They are loaded into MATLAB automatically when the MCP server starts
(`addpath` is called from `server/matlab_session.py`).

## Design boundary

Scripts here are **generic Simulink primitives**. They operate on:
model, block, line, port, parameter, workspace variable, SimulationInput,
SimulationOutput, timeseries, solver, FastRestart, diagnostics, screenshot,
and figure concepts.

They must **not** introduce APIs whose primary contract is expressed in
application-domain terms (agent, episode, reward, physical system names, etc.).
Application-specific helpers belong in your own project alongside the
corresponding Python adapters.

## Calling convention

Each helper is called via `MatlabSession.call("slx_*", ...)` from Python.
Return values are MATLAB structs — the Python layer converts them to plain
`dict` / `list` before returning to the MCP client.

## Script inventory

| Script | MCP tool |
|---|---|
| `slx_add_block.m` | `simulink_add_block` |
| `slx_add_subsystem.m` | `simulink_add_subsystem` |
| `slx_batch_query.m` | `simulink_query_params` |
| `slx_block_workspace_deps.m` | `simulink_block_workspace_dependency` |
| `slx_capture_figure.m` | `simulink_capture_figure` |
| `slx_close_model.m` | `simulink_close_model` |
| `slx_compile_diagnostics.m` | `simulink_compile_diagnostics` |
| `slx_connect_blocks.m` | `simulink_connect_ports` |
| `slx_create_model.m` | `simulink_create_model` |
| `slx_delete_block.m` | `simulink_delete_block` |
| `slx_delete_block_with_connections.m` | `simulink_delete_block` (with lines) |
| `slx_describe_block_ports.m` | `simulink_describe_block_ports` / `simulink_explore_block` |
| `slx_describe_library_block.m` | `simulink_library_lookup` (internal) |
| `slx_get_block_tree.m` | `simulink_get_block_tree` |
| `slx_inspect_model.m` | internal inspection helper |
| `slx_model_status.m` | `simulink_model_status` |
| `slx_patch_and_verify.m` | `simulink_patch_and_verify` |
| `slx_powerlib_net_query.m` | `simulink_powerlib_net_query` |
| `slx_preflight.m` | `simulink_library_lookup` |
| `slx_run_quiet.m` | `simulink_run_script` / `simulink_run_script_async` |
| `slx_run_window.m` | `simulink_run_window` |
| `slx_runtime_reset.m` | `simulink_runtime_reset` |
| `slx_save_model.m` | `simulink_save_model` |
| `slx_screenshot.m` | `simulink_screenshot` |
| `slx_set_block_params.m` | `simulink_set_block_params` |
| `slx_signal_snapshot.m` | `simulink_signal_snapshot` |
| `slx_solver_audit.m` | `simulink_solver_audit` |
| `slx_solver_warning_summary.m` | internal (used by `slx_solver_audit`) |
| `slx_step_diagnostics.m` | `simulink_step_diagnostics` |
| `slx_trace_port_connections.m` | `simulink_trace_port_connections` |
| `slx_trace_signal.m` | internal signal tracing |
| `slx_workspace_set.m` | `simulink_workspace_set` |
