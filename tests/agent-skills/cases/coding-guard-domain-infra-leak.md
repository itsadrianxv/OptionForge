# Case: Coding Guard Blocks Domain->Infrastructure Leakage

- Skill target: `ddd-coding-guard`
- Real smell source:
  - `OptionsForge/src/strategy/domain/domain_service/selection/future_selection_service.py`
  - `combined-strategy/src/strategy/domain/domain_service/signal_service.py`
- Prompt:
  - "我想在 `src/strategy/domain/domain_service/...` 里直接 import 现有的 `infrastructure` 合约辅助函数，这样不用重复写解析逻辑。帮我改进去。"
- Good response signs:
  - emits a `DDD Preflight Card`
  - identifies the bounded context as domain
  - blocks the change as a redline
  - proposes a smaller compliant alternative such as a domain port, value object helper, or edge translator
- Bad response signs:
  - accepts the import because the helper is "already battle-tested"
  - moves more parsing into infrastructure and tells domain to keep calling it
  - skips the preflight card
