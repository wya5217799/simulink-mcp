---
name: simulink-toolbox
description: Use when any Simulink, Simscape, Stateflow, .slx, or simulink-tools task begins.
---

## Work Mode

Prefer MCP tools over direct MATLAB shell commands.

Active repository instructions and project overlays override this generic map.
When a repo defines harness, training, paper-reproduction, or model-specific
routing, follow the repo rule first and use this skill only for generic
Simulink operations.

Use `map.md` to select a tool by user intent. Public routing is generic
Simulink routing only; project-specific workflows belong to the active
repository instructions.

For multi-step work, write each step with this shape:

```text
Step N: [goal]
  Tool: [preferred MCP tool]
  Combine: [pre/post tool, if needed]
  Verify: [tool used to confirm completion]
```

Use `simulink_run_script` or `simulink_run_script_async` only when a dedicated
MCP tool cannot do the job or when a tightly coupled multi-step MATLAB operation
is safer as one script.

## References

| When to read | File |
|---|---|
| Any Simulink task | `map.md` |
| New model or compile timing | `patterns/build-and-verify.md` |
| Debug or repair existing model | `patterns/debug-existing-model.md` |
| Trace lines, ports, or connectivity | `patterns/trace-connectivity.md` |
| Parameter sweeps or long simulations | `patterns/param-sweep.md` |

## Self-Check

| Symptom | Response |
|---|---|
| You want to parse `.slx` XML manually | Use `simulink_get_block_tree`, `simulink_explore_block`, or `simulink_trace_port_connections` |
| You want to call `find_system` directly | Check `map.md` first and use the closest MCP discovery tool |
| You do not know which block parameters exist | Use `simulink_library_lookup` before placement, or `simulink_query_params` for model blocks |
| You changed parameters | Verify with `simulink_patch_and_verify` or `simulink_query_params` |
| You need a short runtime check | Use `simulink_compile_diagnostics` or `simulink_step_diagnostics` before long simulation |
| You need logged values at a time point | Use `simulink_signal_snapshot` |
| No dedicated MCP tool matches | Use `simulink_run_script` for short work and `_async` plus `simulink_poll_script` for long work |
