# Pattern: Build & Verify (从零到可编译)

## 标准流程

```
1. simulink_create_model        新建空 .slx
2. simulink_library_lookup      确认库块定义（参数/端口）
3. simulink_add_block × ≤3      每批不超过 3 个 block
4. simulink_describe_block_ports 每批后确认已放置 block 的端口元信息
5. simulink_describe_block_ports 确认端口编号（从 1 起）
6. simulink_connect_ports       连线
7. simulink_query_params        用 param_names=[...] 校验参数名；返回的 missing_params 字段为空表示参数名存在
8. simulink_set_block_params    设置参数值
9. simulink_compile_diagnostics 每 ≥3 次结构变更后必跑
10. simulink_screenshot         记录当前模型状态
```

## Compile 触发规则

| 条件 | 工具 | 强制？ |
|---|---|---|
| ≥3 次结构改 (add/delete block) | `simulink_compile_diagnostics` | **必须** |
| 任何端口变更 (add_subsystem, connect) | `simulink_compile_diagnostics` | **必须** |
| ≥5 次参数改 | `simulink_compile_diagnostics` | 强烈建议 |
| 单个参数原子修改 | `simulink_patch_and_verify` | 推荐替代 compile |
| 任何 run_script 前 | `simulink_compile_diagnostics` | **必须** |

## patch_and_verify vs set_block_params

```
单个参数改动 → simulink_patch_and_verify  (原子操作，自带验证)
批量改动 (≥2个参数) → set_block_params × N → preflight → compile
```

## 验证工具链

```
simulink_library_lookup     快速结构预检 (~1s)，放置 block 前用
simulink_compile_diagnostics 完整编译 (~5-30s，依模型大小)
simulink_solver_audit        solver 配置专项检查
simulink_step_diagnostics    单步运行期诊断
```

## 节奏示例

```
add_block(A) → add_block(B) → add_block(C) → describe_block_ports(A/B/C)
→ connect_ports
→ compile_diagnostics
→ set_block_params(A) → set_block_params(B) → patch_and_verify(C)
→ query_params(param_names=[...])
→ compile_diagnostics
→ run_script only if no named MCP tool covers the operation
```

## 常见错误预防

| 错误 | 预防动作 |
|---|---|
| block 路径不存在 | 先用 `get_block_tree` 确认路径格式 |
| 端口索引错 | 先用 `describe_block_ports` 拿准确编号 |
| 参数名拼写错 | 先用 `query_params(param_names=[...])` 校验；返回的 missing_params 字段为空表示参数名存在 |
| 编译错误堆积 | 每批 ≤3 个 block 后预检 |

## 禁止行为

- 不要一次加 10+ 个 block 再编译
- 不要假设 block type 名称（如 `simulink/Gain`），用工具确认
- 不要手写 MATLAB 脚本做建模，除非工具明确不支持该操作
- 不要跳过 compile_diagnostics 直接 run_script
- 不要用 compile 替代 patch_and_verify 做单参数验证（太重）
- 不要积累大量改动后才做第一次 compile（错误难定位）
- 不要用已废弃的批量建模工具做 codegen/build pipeline，建模始终用 `add_block + connect_ports`
