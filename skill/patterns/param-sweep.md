# Pattern: Param Sweep (参数扫描 + 抓图)

## 标准流程

```
1. simulink_query_params(block, params)                      锁定基线参数值
2. simulink_query_params(block, param_names=[sweep_param]) 检查参数名；返回的 missing_params 字段为空表示参数名存在
3. 构造脚本字符串 (内联于 simulink_run_script_async 调用参数中，不写外部文件)
4. simulink_run_script_async(script)      异步启动长时仿真
5. simulink_poll_script(job_id)           轮询状态 (每 5-10s)
6. simulink_capture_figure(fig_handle)    抓取每次仿真结果图
7. simulink_screenshot()                  最终状态截图留档
```

## run_script vs run_script_async 选择

| 场景 | 工具 | 原因 |
|---|---|---|
| 单次快速查询 (<5s) | `simulink_run_script` | 同步简单 |
| 单次仿真 (<30s) | `simulink_run_script` | 同步等结果 |
| 参数扫描 / 长仿真 (>30s) | `simulink_run_script_async` + `poll_script` | 避免超时 |
| 批量多次仿真 | `simulink_run_script_async` × N | 可并行 |

## 参数扫描脚本模板

```matlab
% 1. 锁定基线 (已通过 query_params 确认)
baseline_K = 1.0;

% 2. 扫描范围
K_values = [0.5, 1.0, 2.0, 5.0];
results = struct();

% 3. 循环仿真
for i = 1:length(K_values)
    set_param('model/Gain', 'Gain', num2str(K_values(i)));
    sim_out = sim('model', 'StopTime', '10');
    results(i).K = K_values(i);
    results(i).y_final = sim_out.yout{1}.Values.Data(end);
end

% 4. 保存结果
save('results/sweep_results.mat', 'results');
```

## 禁止行为

- 不要用 `simulink_run_script` 跑 >30s 的仿真（会超时报错）
- 不要在扫描前跳过 `query_params` 基线锁定（避免参数漂移）
- 不要忽略 `poll_script` 返回的 error 字段（仿真可能静默失败）
- `run_script_async` 是合法执行路径，但不是默认一上来就用的工具——短查询优先用 `run_script`
