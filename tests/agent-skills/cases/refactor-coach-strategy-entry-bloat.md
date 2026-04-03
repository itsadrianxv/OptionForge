# Case: Refactor Coach Handles Strategy Entry Bloat

- Skill target: `ddd-refactor-coach`
- Real smell source:
  - `OptionsForge/src/strategy/strategy_entry.py`
  - `combined-strategy/src/strategy/application/strategy_engine.py`
- Prompt:
  - "`StrategyEntry` / `strategy_engine` 越来越大，我想把它们重构得更像 DDD。请给我一个可执行的分步路线。"
- Good response signs:
  - labels the hotspot as a grey-line cluster, not a single bug
  - separates runtime assembly, workflow orchestration, and domain policy concerns
  - proposes small slices instead of one large move
  - ends with a `DDD Debt Delta`
- Bad response signs:
  - says "split the file" without deciding boundaries
  - ignores runtime-state ownership
