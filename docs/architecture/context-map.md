# OptionsForge Context Map

## Scope

This map classifies the main path families used across OptionsForge and generated child repositories.

| Path family | Context role | May depend on | Must not depend on |
| --- | --- | --- | --- |
| `src/strategy/domain/**` | Domain model | standard library, domain siblings, domain ports, value objects | infrastructure, runtime assembly, bootstrap, web, vendor/framework types |
| `src/strategy/application/**` | Use-case orchestration | domain, explicit ports, DTO/VO, selected infrastructure implementations through composition | raw vendor payloads as durable contracts, web/bootstrap shortcuts for business rules |
| `src/strategy/infrastructure/**` | Adapters and integration | domain ports, application workflows, external systems | domain invariants implemented inline |
| `src/strategy/runtime/**` | Strategy runtime assembly | application, domain, infrastructure | new trading policy that should live deeper in the model |
| `src/main/**` | Process/bootstrap | configuration, runtime assembly, validation, process wiring | domain decisions hidden in startup or lifecycle hooks |
| `src/web/**` / `src/interface/**` | Outer interface | readers, projections, monitoring outputs, application entrypoints | domain policy encoded in route/controller/view glue |
| `src/backtesting/**` | Replay / simulation boundary | domain value objects, application services, backtest-specific adapters | production gateway logic copied into domain |
| `src/data_fetch/**` and other peripheral sources | External data boundary | adapters, parsers, integration helpers | domain model as a dumping ground for vendor schemas |

## Current Family Hotspots

### Real redline examples
- `OptionsForge/src/strategy/domain/domain_service/selection/future_selection_service.py`
  - Domain code imports `vnpy` types and an infrastructure contract helper.
- `combined-strategy/src/strategy/domain/domain_service/signal_service.py`
  - Domain code imports `infrastructure.utils.contract_helper`.
- `combined-strategy/src/strategy/domain/domain_service/close_decision_service.py`
  - Domain code reaches into infrastructure for contract parsing.

### Real grey-line examples
- `OptionsForge/src/strategy/strategy_entry.py`
  - Large entry object mixes composition, runtime state, and workflow delegation.
- `combined-strategy/src/strategy/application/strategy_engine.py`
  - Workflow object owns substantial runtime state and cross-cutting concerns.
- `OptionsForge/src/main/scaffold/generator.py`
  - Historical template pushed stateful services into newly generated strategy code.

## Mapping Rules For Child Repositories

Generated child repos may rename outer layers, but the mapping remains the same:
- `src/interface/**` is equivalent to `src/web/**`
- repository-specific data acquisition folders remain peripheral boundaries
- `src/strategy/**` remains the architectural core and must keep the same dependency directions

## Decision Shortcut

When unsure where code belongs:
1. If it enforces a trading invariant, it is domain.
2. If it sequences domain decisions across ports, it is application.
3. If it talks to vendors, files, databases, or transports, it is infrastructure.
4. If it only boots processes, renders output, or wires runtime objects, it is outer-layer code.
