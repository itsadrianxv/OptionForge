# RED Baseline 2026-04-03

These notes capture the pre-skill state that motivated the DDD guardrail work.

## Observed repository smells

### Redlines already present
- `OptionsForge/src/strategy/domain/domain_service/selection/future_selection_service.py`
  - imports `vnpy.trader.object.ContractData`
  - imports `src.strategy.infrastructure.parsing.contract_helper.ContractHelper`
- `combined-strategy/src/strategy/domain/domain_service/signal_service.py`
  - imports `...infrastructure.utils.contract_helper.ContractHelper`
- `combined-strategy/src/strategy/domain/domain_service/close_decision_service.py`
  - reaches into infrastructure for contract parsing

### Grey lines already present
- `OptionsForge/src/strategy/strategy_entry.py`
  - large entry object with broad assembly/runtime concerns
- `combined-strategy/src/strategy/application/strategy_engine.py`
  - large workflow/state owner with cross-cutting responsibilities
- `OptionsForge/src/main/scaffold/generator.py`
  - emitted stateful domain-service templates by default

## Rationalizations this suite is meant to block

- "The helper already exists in infrastructure, so domain can just import it."
- "Gateway/bootstrap code already has the data, so put the trading rule there."
- "A temporary coordinator will make the refactor easier."
- "Keeping policy on the service instance is the simplest template for new repos."
- "This hotspot is so messy that the only reasonable move is a full rewrite."

## Baseline caveat

v1 stores repo-local RED evidence as concrete hotspot notes and prompt fixtures. A fully automated agent-harness replay has not been added yet.
