# Pattern: Trace Connectivity (追线 / 查路径)

## 黄金规则

**禁止手拆 XML / 解析 .slx 文件内部结构。** Simulink .slx 是二进制 ZIP 格式，手动解析极易出错（SID 映射、端口 index 偏移）。

## 标准追线流程

```
目标：找到 block B 的上游信号源

1. simulink_loaded_models          确认模型已加载
2. simulink_get_block_tree         获取模型层级，定位 block 路径
3. simulink_explore_block(B)       整体概览：B 的类型、参数、端口连接
   → 若概览已足够定位问题，止步于此
4. simulink_describe_block_ports(B) 列出 B 的所有端口名称和方向
5. simulink_trace_port_connections(B, port=1) 精确追溯：单端口路径追踪
   → 仅在需要精确定位时才用；不要每次都直接跳到这步
```

## 查路径决策

| 目标 | 工具 |
|---|---|
| 找 block 在模型中的路径 | `simulink_get_block_tree` |
| 查 block 的参数和类型 | `simulink_explore_block` |
| 查 block 有几个端口 | `simulink_describe_block_ports` |
| 追溯某端口的上游/下游 | `simulink_trace_port_connections` |
| 查悬空 / 断线端口 | `simulink_compile_diagnostics` |

## 禁止行为

- **不要** `find_system(model, 'BlockType', ...)` 猜路径
- **不要** 解压 .slx / 读取内部 XML 文件
- **不要** 假设端口编号从 0 开始（Simulink 端口从 **1** 起）
- **不要** 直接用 block 类型名称字符串（先 `explore_block` 确认）

## 历史教训

Apr 19 `.slx → XML → SID 映射` 绕路事件：试图通过解析 XML 获取 SID 来定位信号路径，最终因 SID 格式不稳定耗费大量时间。正确做法 3 步搞定：`get_block_tree → explore_block → trace_port_connections`。
