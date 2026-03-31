# TEST MATRIX

## Smoke

- Verification profile: `focus.smoke`
- Notes: smoke uses the same selectors as full mode, plus keyword filters.
- Selectors:
  - `tests/main/focus`
  - `tests/main/validation`
  - `tests/main/scaffold`
  - `tests/strategy/application/test_market_workflow_pipeline.py`
  - `tests/strategy/runtime/test_builder.py`
  - `tests/main/focus/test_agent_assets.py`
  - `tests/main/validation/test_service.py`
  - `tests/strategy/runtime/test_provider_universe.py`
  - `tests/strategy/runtime/test_provider_decision_pipeline.py`
  - `tests/strategy/domain/test_position_execution_state_machine.py`
  - `tests/strategy/domain/test_combination_execution_state_machine.py`
  - `tests/strategy/application/test_execution_state_hooks.py`
  - `tests/strategy/runtime/test_provider_execution_and_hedging.py`
  - `tests/strategy/runtime/test_provider_observability.py`
  - `tests/web/test_monitor_logging.py`
- Keyword filters:
  - Exclude test nodes whose names contain `property`.
  - Exclude test nodes whose names contain `pbt`.

## Full

- Verification profile: `focus.full`
- Selectors:
  - `tests/main/focus`
  - `tests/main/validation`
  - `tests/main/scaffold`
  - `tests/strategy/application/test_market_workflow_pipeline.py`
  - `tests/strategy/runtime/test_builder.py`
  - `tests/main/focus/test_agent_assets.py`
  - `tests/main/validation/test_service.py`
  - `tests/strategy/runtime/test_provider_universe.py`
  - `tests/strategy/runtime/test_provider_decision_pipeline.py`
  - `tests/strategy/domain/test_position_execution_state_machine.py`
  - `tests/strategy/domain/test_combination_execution_state_machine.py`
  - `tests/strategy/application/test_execution_state_hooks.py`
  - `tests/strategy/runtime/test_provider_execution_and_hedging.py`
  - `tests/strategy/runtime/test_provider_observability.py`
  - `tests/web/test_monitor_logging.py`

## Skipped Packs

- `backtest`: missing dependency `chinese_calendar`
