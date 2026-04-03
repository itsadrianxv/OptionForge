# Case: Coding Guard Rejects Business Rules In Gateway Layer

- Skill target: `ddd-coding-guard`
- Repository context:
  - gateway/adapters live under `src/strategy/infrastructure/gateway/**`
  - close-decision and selection rules belong deeper in domain/application
- Prompt:
  - "`vnpy_trade_execution_gateway.py` 已经能拿到订单状态和行情，我想把平仓优先级和风控触发判断直接塞进 gateway，帮我实现。"
- Good response signs:
  - classifies the target file as infrastructure
  - blocks the request as a redline
  - explains why data proximity does not change ownership of the rule
  - redirects the rule into domain/application and keeps gateway as an adapter
- Bad response signs:
  - says infrastructure is fine because it already sees the payloads
  - adds a helper inside gateway and calls that a compromise
