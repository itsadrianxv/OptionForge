# ema_cross_example

演示最基础的“指标契约 + 信号契约”接法。

- 指标：计算 EMA 快慢线
- 开仓：快线上穿慢线时输出 `SignalDecision(action="open")`
- 平仓：快线下穿慢线时输出 `SignalDecision(action="close")`

适合拿来做自定义策略的最小起点。
