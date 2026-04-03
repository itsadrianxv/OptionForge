# Case: Refactor Coach Diagnoses Domain->Infrastructure Leakage

- Skill target: `ddd-refactor-coach`
- Real smell source:
  - `OptionsForge/src/strategy/domain/domain_service/selection/future_selection_service.py`
  - `combined-strategy/src/strategy/domain/domain_service/close_decision_service.py`
- Prompt:
  - "这些 domain service 现在直接依赖 infra helper，帮我按 DDD 想一下怎么收回来，但不要空谈。"
- Good response signs:
  - produces a `Hotspot Diagnosis`
  - marks the smell as a redline
  - proposes the smallest safe first slice
  - names a regression test for that slice
- Bad response signs:
  - jumps straight to a whole-module rewrite
  - stops at abstract DDD slogans
