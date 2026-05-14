# Pattern: Debug Existing Model (诊断已有模型)

**适用场景**：模型已存在但出现编译错误、仿真异常、参数疑问、信号路由问题。这是最高频的日常任务——不是新建，而是排查。

## 标准诊断流程

```
1. simulink_load_model          打开 .slx（若未加载）
2. simulink_explore_block       快速了解顶层结构和关键 block
3. simulink_compile_diagnostics 找出所有编译期错误/警告
4. simulink_solver_audit        检查 solver 配置（步长/精度）
5. simulink_query_params        查可疑 block 的当前参数值
6. simulink_patch_and_verify    原子修复参数并立即验证
7. simulink_step_diagnostics    运行期问题：单步诊断
8. simulink_trace_port_connections 信号路由问题：精确追单端口
```

## 按症状选入口

| 症状 | 首选工具 | 次选工具 |
|---|---|---|
| 编译报错（Error/Warning） | `simulink_compile_diagnostics` | `simulink_explore_block` 定位 block |
| 仿真结果异常（值不对） | `simulink_step_diagnostics` | `simulink_query_params` 检查参数 |
| Solver 不收敛 / 步长警告 | `simulink_solver_audit` | `simulink_compile_diagnostics` |
| 信号断线 / 端口悬空 | `simulink_trace_port_connections` | `simulink_describe_block_ports` |
| 参数名/值存疑 | `simulink_query_params` | `simulink_patch_and_verify` 修复 |
| 不知道模型里有什么 | `simulink_get_block_tree` | `simulink_explore_block` |

## 修复参数的选择

```
单个参数有疑问 → simulink_query_params 先读当前值
确认需要改 → simulink_patch_and_verify (改+验证一步完成)
多个参数需批量改 → set_block_params × N → compile_diagnostics
```

## 信号追溯

```
不知道某信号从哪里来/去哪里 → simulink_trace_port_connections (精确追单端口)
想先看 block 整体端口概况 → simulink_explore_block (快速概览)
怀疑某端口未连接 → simulink_describe_block_ports → trace_port_connections
```

## 迭代修复节奏

```
compile_diagnostics              获取完整错误清单
→ 逐错处理：
    query_params(suspicious_block) 确认当前值
    patch_and_verify(fix)          修复并立即验证
    step_diagnostics               若有运行期问题
→ compile_diagnostics              确认全部错误已消除
→ run_script 前最终编译验证
```

## 禁止行为

- 不要手拆 `.slx` XML 来查连线或 SID（高成本绕路）
- 不要用 `find_system` 猜 block 路径，用 `get_block_tree` / `explore_block`
- 不要跳过 compile_diagnostics 直接跑仿真验证修复是否成功
- 不要同时改多个参数再一起验证——一个参数一个 `patch_and_verify`，错误定位更精确
- 不要假设 block 参数名，用 `query_params(param_names=[...])` 先校验名称是否合法；返回的 missing_params 字段为空表示参数名存在
