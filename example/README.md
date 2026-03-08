# example

这里放的是“如何使用基础设施”的参考实现，不是框架主干代码。

包含三个示例：

- `ema_cross_example`：均线交叉，演示基础指标/信号契约
- `iv_rank_example`：IV Rank，演示如何利用统一期权链模型
- `delta_neutral_example`：Delta Neutral，演示如何输出组合偏好与调整信号

这些示例的目标是帮助你理解：

1. 指标服务如何返回 `IndicatorComputationResult`
2. 信号服务如何返回 `SignalDecision`
3. `strategy_contract.toml` 如何声明契约绑定与服务装配开关
