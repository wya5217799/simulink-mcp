# simulink-toolbox: Intent -> Tool Map

Tool inventory source: `index.json`. This file routes generic Simulink user
intent only. Project-specific harness, training, paper-reproduction, and
model-specific workflows belong to repository instructions or project overlays.

---

## Frequent Tools

| Tool | Use For | Not For | Verify? |
|---|---|---|---|
| `simulink_load_model` | Open an existing `.slx` into MATLAB | Creating a new model | No |
| `simulink_get_block_tree` | Browse model hierarchy | Reading parameter values | No |
| `simulink_explore_block` | Inspect one block's type, params, ports, and nearby connections | Full-model traversal | No |
| `simulink_library_lookup` | Discover library block parameters/defaults before placement | Model-level verification | No |
| `simulink_query_params` | Read current block parameters | Writing parameters | No |
| `simulink_patch_and_verify` | Write parameters and immediately verify readback/update | Initial compile diagnosis | Yes |
| `simulink_compile_diagnostics` | Compile/update and report errors or warnings | Modifying the model | Yes |
| `simulink_step_diagnostics` | Short controlled runtime diagnosis | Full long simulation | Yes |
| `simulink_signal_snapshot` | Read logged, ToWorkspace, or temporary block-output values | Domain-specific interpretation | No |
| `simulink_run_script` / `_async` | Escape hatch for unsupported or tightly coupled MATLAB operations | Default model inspection or patching | No |

---

## discover - Model Structure And Paths

- `simulink_loaded_models` - list models loaded in the MATLAB session. NOT: list files on disk.
- `simulink_model_status` - inspect loaded, dirty, file, solver, StopTime, and FastRestart state.
- `simulink_get_block_tree` - get model or subsystem hierarchy. NOT: read parameter values.
- `simulink_explore_block` - inspect one block deeply. NOT: replace full-model traversal.

## construct - Models, Subsystems, Blocks

- `simulink_create_model` - create a new empty model. NOT: open an existing `.slx`.
- `simulink_load_model` - load an existing model. NOT: create a model.
- `simulink_close_model` - close a loaded model. NOT: delete the file.
- `simulink_save_model` - save a loaded model or save to a target path.
- `simulink_add_block` - add one library block to a model. Confirm library paths first.
- `simulink_add_subsystem` - add a subsystem container. NOT: add a normal block.

## wire - Lines, Ports, Connectivity

- `simulink_describe_block_ports` - list block port names, directions, and connection metadata.
- `simulink_trace_port_connections` - trace one port's upstream/downstream signal chain.
- `simulink_connect_ports` - connect ports by name addressing. Port numbering is 1-based.

## modify - Parameters And Deletion

- `simulink_set_block_params` - set block parameters. Verify with `simulink_query_params` or `simulink_patch_and_verify`.
- `simulink_delete_block` - delete a block, optionally with attached lines. Confirm the path first.

## query - Parameters And Values

- `simulink_query_params` - read one or many blocks' parameters. Use `param_names` to validate expected names.
- `simulink_signal_snapshot` - read logged, ToWorkspace, or temporary block-output values at one time point.

## verify - Compile And Configuration

- `simulink_compile_diagnostics` - update/compile and return structured diagnostics.
- `simulink_solver_audit` - inspect solver configuration and related suspects.
- `simulink_patch_and_verify` - write parameter edits, read them back, and optionally run update/smoke simulation.

## diagnose - Runtime And Connectivity Faults

- `simulink_step_diagnostics` - run a short window and classify warnings/errors.
- `simulink_compile_diagnostics` - use for compile-time failures.
- `simulink_trace_port_connections` - use for missing, wrong, or ambiguous wiring.

## workspace - Base Workspace Variables

- `simulink_workspace_set` - set MATLAB base-workspace variables in one structured call. NOT: set block mask parameters.

## runtime - Controlled Simulation

- `simulink_runtime_reset` - reset FastRestart/runtime state without project semantics.
- `simulink_run_window` - run a model over a StartTime/StopTime window.

## capture - Images

- `simulink_screenshot` - capture a Simulink canvas. NOT: capture MATLAB figures.
- `simulink_capture_figure` - capture MATLAB figure windows. NOT: capture Simulink diagrams.

## execute - MATLAB Script Escape Hatch

- `simulink_run_script` - run a short MATLAB script synchronously.
- `simulink_run_script_async` - run a long MATLAB script asynchronously.
- `simulink_poll_script` - poll an async script job.

Use script execution only when at least one condition is true:

1. No dedicated MCP tool covers the operation.
2. The operation is a tightly coupled multi-step MATLAB workflow.
3. A Simulink API is required and the public MCP surface does not expose it.

Do not use script execution for routine model discovery, parameter reads,
parameter writes, compile diagnostics, screenshots, or signal snapshots.

---

## Pitfalls

1. Do not parse `.slx` XML for routine structure or connectivity; use discovery and trace tools.
2. Do not guess block type names; use `simulink_library_lookup` first.
3. Do not assume port numbering starts at 0; Simulink port addressing here is 1-based.
4. Do not run long simulations synchronously; use `_async` and poll.
5. Do not set parameters without readback when correctness matters.
6. Do not leave many models open in one MATLAB session; close models when done.
