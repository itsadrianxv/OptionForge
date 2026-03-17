# Service Activation Runtime Composition Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lazy-imported runtime composition system driven solely by `service_activation`, then migrate workflows to consume runtime roles instead of hard-coded optional services.

**Architecture:** Add a new `src/strategy/runtime/` composition layer with registry, builder, runtime models, and per-capability providers. Keep the repository complete for template-repo users, but make startup import only enabled providers and have application workflows consume explicit runtime roles rather than `entry.xxx_service` attributes.

**Tech Stack:** Python 3.12, pytest, vn.py strategy host objects, TOML config loading, importlib-based lazy provider loading, dataclasses / typed runtime models.

---

## Preconditions

- Execute this plan in a dedicated git worktree before Task 1.

```powershell
git worktree add ..\option-strategy-runtime codex/service-activation-runtime
```

- Before changing code, capture the current targeted baseline:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/application/test_lifecycle_workflow.py tests/strategy/application/test_market_workflow_pipeline.py tests/main/config/test_config_loader_services.py -v
```

Expected: PASS for the current baseline tests.

- During execution, follow `@superpowers:test-driven-development` for every code task and `@superpowers:verification-before-completion` before claiming any milestone is done.

## File Structure

### New runtime files

- Create: `src/strategy/runtime/__init__.py`
  - Expose runtime package entrypoints.
- Create: `src/strategy/runtime/models.py`
  - Define `StrategyRuntime`, role groups, provider contribution models, and runtime kernel types.
- Create: `src/strategy/runtime/registry.py`
  - Define capability metadata and provider import paths as the single source of truth.
- Create: `src/strategy/runtime/builder.py`
  - Validate `service_activation`, order providers, lazy-import enabled providers, and merge contributions.
- Create: `src/strategy/runtime/providers/__init__.py`
  - Namespace package for capability providers.
- Convention: every provider module exports a single `PROVIDER` object exposing `.build(entry, full_config, kernel) -> CapabilityContribution`.
- Create: `src/strategy/runtime/providers/future_selection.py`
  - Build `universe.initializer` and `universe.rollover_checker`.
- Create: `src/strategy/runtime/providers/option_chain.py`
  - Build `open_pipeline.option_chain_loader`.
- Create: `src/strategy/runtime/providers/option_selector.py`
  - Build `open_pipeline.contract_selector`.
- Create: `src/strategy/runtime/providers/greeks_calculator.py`
  - Build `open_pipeline.greeks_enricher`.
- Create: `src/strategy/runtime/providers/pricing_engine.py`
  - Build `open_pipeline.pricing_enricher`.
- Create: `src/strategy/runtime/providers/portfolio_risk.py`
  - Build `open_pipeline.risk_evaluator` and `close_pipeline.risk_evaluator`.
- Create: `src/strategy/runtime/providers/position_sizing.py`
  - Build `open_pipeline.sizing_evaluator` and `close_pipeline.close_volume_planner`.
- Create: `src/strategy/runtime/providers/smart_order_executor.py`
  - Build `open_pipeline.execution_planner` and `close_pipeline.execution_planner`.
- Create: `src/strategy/runtime/providers/advanced_order_scheduler.py`
  - Build `open_pipeline.execution_scheduler` and `close_pipeline.execution_scheduler`.
- Create: `src/strategy/runtime/providers/delta_hedging.py`
  - Build `portfolio.rebalance_planner` for delta hedging.
- Create: `src/strategy/runtime/providers/vega_hedging.py`
  - Build `portfolio.rebalance_planner` for vega hedging.
- Create: `src/strategy/runtime/providers/monitoring.py`
  - Build snapshot sinks, trace sinks, and lifecycle cleanup hooks.
- Create: `src/strategy/runtime/providers/decision_observability.py`
  - Build in-memory trace sinks and journal updates.

### Modified core files

- Modify: `src/main/config/config_loader.py`
  - Stop injecting implicit service defaults; add strict manifest extraction helpers if needed by the builder.
- Modify: `src/strategy/strategy_entry.py`
  - Add `runtime` slot, remove static optional-service imports over time, and keep only fixed kernel state.
- Modify: `src/strategy/application/lifecycle_workflow.py`
  - Replace direct optional-service construction with runtime builder integration.
- Modify: `src/strategy/application/market_workflow.py`
  - Replace `entry.xxx_service` and `service_activation` branches with runtime role execution.
- Modify: `src/strategy/application/state_workflow.py`
  - Replace direct monitor writes with `snapshot_sinks`.
- Modify: `src/main/scaffold/catalog.py`
  - Source capability keys and dependency metadata from runtime registry instead of a second truth table.

### New and modified tests

- Create: `tests/strategy/runtime/__init__.py`
- Create: `tests/strategy/runtime/test_builder.py`
  - Validate manifest completeness, dependency/conflict handling, role collision handling, and lazy imports.
- Create: `tests/main/config/test_service_activation_manifest.py`
  - Validate strict `service_activation` parsing behavior.
- Create: `tests/strategy/application/test_lifecycle_runtime_builder.py`
  - Verify lifecycle startup builds runtime and runs hooks.
- Create: `tests/strategy/runtime/test_provider_observability.py`
  - Verify snapshot sinks and trace sinks.
- Create: `tests/strategy/runtime/test_provider_universe.py`
  - Verify future-selection and option-chain role contributions.
- Create: `tests/strategy/runtime/test_provider_decision_pipeline.py`
  - Verify selector, greeks, pricing, risk, sizing, and close-volume roles.
- Create: `tests/strategy/runtime/test_provider_execution_and_hedging.py`
  - Verify planner/scheduler roles and rebalance planner behavior.
- Create: `tests/strategy/test_runtime_import_boundaries.py`
  - AST-based regression tests proving `StrategyEntry` and `LifecycleWorkflow` no longer import optional providers directly.
- Create: `tests/main/scaffold/test_catalog_runtime_registry_sync.py`
  - Verify scaffold capability metadata follows runtime registry.
- Modify: `tests/strategy/application/test_market_workflow_pipeline.py`
  - Rebase workflow tests onto runtime roles.
- Modify: `tests/strategy/application/test_lifecycle_workflow.py`
  - Keep OMS snapshot tests passing after lifecycle refactor.
- Modify: `tests/main/scaffold/test_project_scaffold.py`
  - Keep generated `service_activation` expectations aligned with registry-derived metadata.

## Task 1: Add Runtime Skeleton And Builder Validation

**Files:**
- Create: `src/strategy/runtime/__init__.py`
- Create: `src/strategy/runtime/models.py`
- Create: `src/strategy/runtime/registry.py`
- Create: `src/strategy/runtime/builder.py`
- Create: `src/strategy/runtime/providers/__init__.py`
- Create: `tests/strategy/runtime/__init__.py`
- Create: `tests/strategy/runtime/test_builder.py`

- [ ] **Step 1: Write the failing builder validation tests**

```python
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.strategy.runtime.builder import StrategyRuntimeBuilder


def _entry() -> SimpleNamespace:
    return SimpleNamespace(logger=SimpleNamespace(info=lambda *a, **k: None))


def test_builder_rejects_unknown_capability() -> None:
    with pytest.raises(ValueError, match="unknown capability"):
        StrategyRuntimeBuilder().build(
            _entry(),
            {"service_activation": {"unknown_capability": True}},
        )


def test_builder_rejects_missing_manifest_keys() -> None:
    with pytest.raises(ValueError, match="missing capability keys"):
        StrategyRuntimeBuilder().build(
            _entry(),
            {"service_activation": {"option_chain": True}},
        )
```

- [ ] **Step 2: Run the new tests to confirm they fail**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_builder.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `src.strategy.runtime` or missing `StrategyRuntimeBuilder`.

- [ ] **Step 3: Implement the minimal runtime package, registry metadata, and builder validation path**

```python
@dataclass(frozen=True)
class CapabilitySpec:
    key: str
    provider_import_path: str
    requires: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    single_roles: tuple[str, ...] = ()
    multi_roles: tuple[str, ...] = ()


class StrategyRuntimeBuilder:
    def build(self, entry: Any, full_config: dict[str, Any]) -> StrategyRuntime:
        manifest = self._validate_manifest(full_config.get("service_activation"))
        enabled = tuple(key for key, active in manifest.items() if active)
        contributions = self._load_enabled_contributions(enabled, entry, full_config)
        return self._merge_contributions(enabled, contributions)
```

- [ ] **Step 4: Re-run the builder test file**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_builder.py -v
```

Expected: PASS for unknown-key and missing-key validation tests, plus any additional builder tests added during implementation.

- [ ] **Step 5: Commit the runtime skeleton**

```powershell
git add src/strategy/runtime/__init__.py src/strategy/runtime/models.py src/strategy/runtime/registry.py src/strategy/runtime/builder.py src/strategy/runtime/providers/__init__.py tests/strategy/runtime/__init__.py tests/strategy/runtime/test_builder.py
git commit -m "feat: 新增运行时装配骨架"
```

## Task 2: Make `service_activation` A Strict Manifest And Sync Scaffold Metadata

**Files:**
- Modify: `src/main/config/config_loader.py`
- Modify: `src/main/scaffold/catalog.py`
- Create: `tests/main/config/test_service_activation_manifest.py`
- Create: `tests/main/scaffold/test_catalog_runtime_registry_sync.py`
- Modify: `tests/main/scaffold/test_project_scaffold.py`

- [ ] **Step 1: Write failing tests for strict manifest parsing and runtime-registry sync**

```python
from __future__ import annotations

import pytest

from src.main.config.config_loader import ConfigLoader


def test_load_service_activation_manifest_rejects_non_bool_values() -> None:
    with pytest.raises(ValueError, match="must be boolean"):
        ConfigLoader.load_service_activation_manifest(
            {"service_activation": {"option_chain": "yes"}}
        )


def test_scaffold_catalog_service_activation_keys_follow_runtime_registry() -> None:
    from src.main.scaffold.catalog import SERVICE_ACTIVATION_KEYS
    from src.strategy.runtime.registry import CAPABILITY_REGISTRY

    assert tuple(CAPABILITY_REGISTRY.keys()) == SERVICE_ACTIVATION_KEYS
```

- [ ] **Step 2: Run only the new config and scaffold tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/main/config/test_service_activation_manifest.py tests/main/scaffold/test_catalog_runtime_registry_sync.py -v
```

Expected: FAIL with missing helper, missing registry export, or assertion mismatch against duplicated metadata.

- [ ] **Step 3: Add strict manifest extraction and replace duplicated scaffold truth tables**

```python
@staticmethod
def load_service_activation_manifest(config: dict[str, Any]) -> dict[str, bool]:
    raw = config.get("service_activation")
    if not isinstance(raw, dict):
        raise ValueError("[service_activation] must be a table")
    unknown = set(raw) - set(CAPABILITY_REGISTRY)
    missing = set(CAPABILITY_REGISTRY) - set(raw)
    if unknown or missing:
        raise ValueError("service_activation keys must exactly match runtime registry")
    return {key: _ensure_bool(raw[key]) for key in CAPABILITY_REGISTRY}
```

- [ ] **Step 4: Re-run targeted config and scaffold tests, then re-run existing scaffold generation tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/main/config/test_service_activation_manifest.py tests/main/config/test_config_loader_services.py tests/main/scaffold/test_catalog_runtime_registry_sync.py tests/main/scaffold/test_project_scaffold.py -v
```

Expected: PASS, with generated scaffold tests still producing the same `service_activation` shape.

- [ ] **Step 5: Commit the manifest and catalog sync**

```powershell
git add src/main/config/config_loader.py src/main/scaffold/catalog.py tests/main/config/test_service_activation_manifest.py tests/main/config/test_config_loader_services.py tests/main/scaffold/test_catalog_runtime_registry_sync.py tests/main/scaffold/test_project_scaffold.py
git commit -m "refactor: 统一服务激活清单来源"
```

## Task 3: Integrate Runtime Builder Into Strategy Host Lifecycle

**Files:**
- Modify: `src/strategy/strategy_entry.py`
- Modify: `src/strategy/application/lifecycle_workflow.py`
- Create: `tests/strategy/application/test_lifecycle_runtime_builder.py`
- Modify: `tests/strategy/application/test_lifecycle_workflow.py`

- [ ] **Step 1: Write failing lifecycle tests for runtime construction and hook execution**

```python
from __future__ import annotations

from types import SimpleNamespace

from src.strategy.application.lifecycle_workflow import LifecycleWorkflow


def test_on_init_builds_runtime_and_runs_init_hooks(monkeypatch) -> None:
    calls: list[str] = []
    runtime = SimpleNamespace(lifecycle=SimpleNamespace(init_hooks=[lambda: calls.append("init")]))
    entry = SimpleNamespace(
        logger=SimpleNamespace(info=lambda *a, **k: None),
        setting={"strategy_full_config": {"service_activation": {}}},
    )
    monkeypatch.setattr("src.strategy.application.lifecycle_workflow.build_runtime", lambda *a, **k: runtime)

    LifecycleWorkflow(entry).on_init()

    assert entry.runtime is runtime
    assert calls == ["init"]
```

- [ ] **Step 2: Run lifecycle tests and confirm they fail**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_lifecycle_workflow.py -v
```

Expected: FAIL because `entry.runtime` is never built and hook execution is not yet delegated.

- [ ] **Step 3: Add a runtime slot to `StrategyEntry` and delegate optional-capability setup to the builder**

```python
class StrategyEntry(StrategyTemplate):
    def __init__(...):
        ...
        self.runtime: StrategyRuntime | None = None


class LifecycleWorkflow:
    def on_init(self) -> None:
        full_config = self._load_full_config()
        self.entry.runtime = StrategyRuntimeBuilder().build(self.entry, full_config)
        for hook in self.entry.runtime.lifecycle.init_hooks:
            hook()
```

- [ ] **Step 4: Re-run the lifecycle-focused tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_lifecycle_workflow.py -v
```

Expected: PASS, while OMS snapshot behavior remains unchanged.

- [ ] **Step 5: Commit the lifecycle integration**

```powershell
git add src/strategy/strategy_entry.py src/strategy/application/lifecycle_workflow.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_lifecycle_workflow.py
git commit -m "refactor: 生命周期接入运行时装配"
```

## Task 4: Migrate Monitoring And Decision Observability To Runtime Sinks

**Files:**
- Create: `src/strategy/runtime/providers/monitoring.py`
- Create: `src/strategy/runtime/providers/decision_observability.py`
- Modify: `src/strategy/application/state_workflow.py`
- Modify: `src/strategy/application/market_workflow.py`
- Create: `tests/strategy/runtime/test_provider_observability.py`
- Modify: `tests/strategy/application/test_market_workflow_pipeline.py`

- [ ] **Step 1: Write failing tests for snapshot sinks and trace sinks**

```python
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.strategy.application.state_workflow import StateWorkflow


def test_state_workflow_writes_to_runtime_snapshot_sinks() -> None:
    sink = MagicMock()
    entry = SimpleNamespace(
        runtime=SimpleNamespace(state=SimpleNamespace(snapshot_sinks=[sink])),
        target_aggregate=MagicMock(),
        position_aggregate=MagicMock(),
        logger=MagicMock(),
    )

    StateWorkflow(entry).record_snapshot()

    sink.assert_called_once()
```

- [ ] **Step 2: Run observability tests and confirm the old direct-monitor path breaks them**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_observability.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: FAIL because `StateWorkflow` still requires `entry.monitor` and decision traces are not routed through runtime sinks.

- [ ] **Step 3: Implement monitoring and decision-observability providers, then update workflows to consume runtime sinks**

```python
def record_snapshot(self) -> None:
    sinks = getattr(getattr(self.entry.runtime, "state", None), "snapshot_sinks", [])
    for sink in sinks:
        sink(self.entry.target_aggregate, self.entry.position_aggregate, self.entry)


def _publish_trace(self, trace: DecisionTrace) -> None:
    for sink in self.entry.runtime.observability.trace_sinks:
        sink(trace.to_payload())
```

- [ ] **Step 4: Re-run the observability-focused tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_observability.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: PASS, with the decision journal and monitor writes both mediated by runtime sinks.

- [ ] **Step 5: Commit the observability migration**

```powershell
git add src/strategy/runtime/providers/monitoring.py src/strategy/runtime/providers/decision_observability.py src/strategy/application/state_workflow.py src/strategy/application/market_workflow.py tests/strategy/runtime/test_provider_observability.py tests/strategy/application/test_market_workflow_pipeline.py
git commit -m "refactor: 迁移监控与可观测性到运行时角色"
```

## Task 5: Migrate Universe Initialization And Option-Chain Loading

**Files:**
- Create: `src/strategy/runtime/providers/future_selection.py`
- Create: `src/strategy/runtime/providers/option_chain.py`
- Modify: `src/strategy/application/lifecycle_workflow.py`
- Modify: `src/strategy/application/market_workflow.py`
- Create: `tests/strategy/runtime/test_provider_universe.py`
- Modify: `tests/strategy/application/test_lifecycle_runtime_builder.py`

- [ ] **Step 1: Write failing tests for `universe.*` and `open_pipeline.option_chain_loader`**

```python
from __future__ import annotations

from types import SimpleNamespace


def test_future_selection_provider_contributes_initializer() -> None:
    from src.strategy.runtime.providers.future_selection import PROVIDER

    entry = SimpleNamespace(target_products=["IF"], logger=SimpleNamespace(info=lambda *a, **k: None))
    contribution = PROVIDER.build(entry, {"service_activation": {"future_selection": True}}, kernel=SimpleNamespace())

    assert contribution.universe.initializer is not None


def test_option_chain_provider_contributes_loader() -> None:
    from src.strategy.runtime.providers.option_chain import PROVIDER

    contribution = PROVIDER.build(SimpleNamespace(), {"service_activation": {"option_chain": True}}, kernel=SimpleNamespace())
    assert contribution.open_pipeline.option_chain_loader is not None
```

- [ ] **Step 2: Run the new universe tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_universe.py tests/strategy/application/test_lifecycle_runtime_builder.py -v
```

Expected: FAIL because provider modules do not exist yet and lifecycle still owns universe setup directly.

- [ ] **Step 3: Move future-selection and option-chain behavior behind provider contributions**

```python
if self.entry.runtime.universe.initializer is not None:
    self.entry.runtime.universe.initializer()

if self.entry.runtime.open_pipeline.option_chain_loader is not None:
    option_chain = self.entry.runtime.open_pipeline.option_chain_loader(vt_symbol, instrument, bar_data)
```

- [ ] **Step 4: Re-run the targeted universe tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_universe.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: PASS, with lifecycle and market workflow both using runtime roles instead of direct `future_selection_service` and `service_activation["option_chain"]`.

- [ ] **Step 5: Commit the universe and chain migration**

```powershell
git add src/strategy/runtime/providers/future_selection.py src/strategy/runtime/providers/option_chain.py src/strategy/application/lifecycle_workflow.py src/strategy/application/market_workflow.py tests/strategy/runtime/test_provider_universe.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_market_workflow_pipeline.py
git commit -m "refactor: 迁移选标与期权链装配角色"
```

## Task 6: Migrate Selector, Greeks, Pricing, Risk, And Sizing Roles

**Files:**
- Create: `src/strategy/runtime/providers/option_selector.py`
- Create: `src/strategy/runtime/providers/greeks_calculator.py`
- Create: `src/strategy/runtime/providers/pricing_engine.py`
- Create: `src/strategy/runtime/providers/portfolio_risk.py`
- Create: `src/strategy/runtime/providers/position_sizing.py`
- Modify: `src/strategy/application/market_workflow.py`
- Create: `tests/strategy/runtime/test_provider_decision_pipeline.py`
- Modify: `tests/strategy/application/test_market_workflow_pipeline.py`

- [ ] **Step 1: Write failing tests for the open/close decision roles**

```python
from __future__ import annotations

from types import SimpleNamespace


def test_position_sizing_provider_contributes_close_volume_planner() -> None:
    from src.strategy.runtime.providers.position_sizing import PROVIDER

    contribution = PROVIDER.build(
        SimpleNamespace(max_positions=5),
        {"service_activation": {"position_sizing": True}},
        kernel=SimpleNamespace(),
    )

    assert contribution.close_pipeline.close_volume_planner is not None


def test_portfolio_risk_provider_contributes_open_and_close_risk_roles() -> None:
    from src.strategy.runtime.providers.portfolio_risk import PROVIDER

    contribution = PROVIDER.build(
        SimpleNamespace(risk_thresholds=SimpleNamespace()),
        {"service_activation": {"portfolio_risk": True, "greeks_calculator": True}},
        kernel=SimpleNamespace(),
    )

    assert contribution.open_pipeline.risk_evaluator is not None
    assert contribution.close_pipeline.risk_evaluator is not None
```

- [ ] **Step 2: Run the decision-pipeline tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_decision_pipeline.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: FAIL because workflow still reads `entry.option_selector_service`, `entry.greeks_calculator`, `entry.pricing_engine`, and `entry.position_sizing_service`.

- [ ] **Step 3: Implement the decision-role providers and switch `MarketWorkflow` to explicit runtime role calls**

```python
selected_contract = None
if self.entry.runtime.open_pipeline.contract_selector is not None:
    selected_contract = self.entry.runtime.open_pipeline.contract_selector(signal, option_chain)

if self.entry.runtime.open_pipeline.greeks_enricher is not None:
    greeks_payload = self.entry.runtime.open_pipeline.greeks_enricher(option_chain, selected_contract)

if self.entry.runtime.close_pipeline.close_volume_planner is not None:
    close_payload = self.entry.runtime.close_pipeline.close_volume_planner(position)
```

- [ ] **Step 4: Re-run the decision-pipeline tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_decision_pipeline.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: PASS, with open and close traces populated from runtime roles rather than direct service attributes.

- [ ] **Step 5: Commit the decision-role migration**

```powershell
git add src/strategy/runtime/providers/option_selector.py src/strategy/runtime/providers/greeks_calculator.py src/strategy/runtime/providers/pricing_engine.py src/strategy/runtime/providers/portfolio_risk.py src/strategy/runtime/providers/position_sizing.py src/strategy/application/market_workflow.py tests/strategy/runtime/test_provider_decision_pipeline.py tests/strategy/application/test_market_workflow_pipeline.py
git commit -m "refactor: 迁移定价风控与仓位管线角色"
```

## Task 7: Migrate Execution Planner, Scheduler, And Hedging Rebalance Roles

**Files:**
- Create: `src/strategy/runtime/providers/smart_order_executor.py`
- Create: `src/strategy/runtime/providers/advanced_order_scheduler.py`
- Create: `src/strategy/runtime/providers/delta_hedging.py`
- Create: `src/strategy/runtime/providers/vega_hedging.py`
- Modify: `src/strategy/application/market_workflow.py`
- Create: `tests/strategy/runtime/test_provider_execution_and_hedging.py`
- Modify: `tests/strategy/runtime/test_builder.py`

- [ ] **Step 1: Write failing tests for planner/scheduler order and rebalance planner output**

```python
from __future__ import annotations

import pytest


def test_builder_rejects_multiple_rebalance_planners() -> None:
    from src.strategy.runtime.builder import StrategyRuntimeBuilder

    def build_manifest(**overrides):
        manifest = {
            "future_selection": False,
            "option_chain": False,
            "option_selector": False,
            "position_sizing": False,
            "pricing_engine": False,
            "greeks_calculator": False,
            "portfolio_risk": False,
            "smart_order_executor": False,
            "advanced_order_scheduler": False,
            "delta_hedging": False,
            "vega_hedging": False,
            "monitoring": False,
            "decision_observability": False,
        }
        manifest.update(overrides)
        return manifest

    with pytest.raises(ValueError, match="portfolio.rebalance_planner"):
        StrategyRuntimeBuilder().build(
            entry=SimpleNamespace(logger=SimpleNamespace(info=lambda *a, **k: None)),
            full_config={"service_activation": build_manifest(delta_hedging=True, vega_hedging=True)},
        )


def test_advanced_scheduler_wraps_execution_planner_output() -> None:
    from src.strategy.runtime.providers.advanced_order_scheduler import PROVIDER

    contribution = PROVIDER.build(
        SimpleNamespace(),
        {"service_activation": build_manifest(smart_order_executor=True, advanced_order_scheduler=True)},
        SimpleNamespace(),
    )

    assert contribution.open_pipeline.execution_scheduler is not None
```

- [ ] **Step 2: Run execution and hedging tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_execution_and_hedging.py tests/strategy/runtime/test_builder.py -v
```

Expected: FAIL because the provider modules are missing and `portfolio.rebalance_planner` is not yet part of the runtime flow.

- [ ] **Step 3: Implement execution providers and the portfolio rebalance planner integration**

```python
if self.entry.runtime.open_pipeline.execution_planner is not None:
    execution_plan = self.entry.runtime.open_pipeline.execution_planner(...)
if self.entry.runtime.open_pipeline.execution_scheduler is not None:
    execution_plan = self.entry.runtime.open_pipeline.execution_scheduler(execution_plan)

if self.entry.runtime.portfolio.rebalance_planner is not None:
    hedge_trace = self.entry.runtime.portfolio.rebalance_planner(...)
```

- [ ] **Step 4: Re-run the execution and hedging tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime/test_provider_execution_and_hedging.py tests/strategy/runtime/test_builder.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: PASS, with builder conflicts still enforced and execution scheduler / rebalance behavior visible through runtime roles.

- [ ] **Step 5: Commit the execution and hedging migration**

```powershell
git add src/strategy/runtime/providers/smart_order_executor.py src/strategy/runtime/providers/advanced_order_scheduler.py src/strategy/runtime/providers/delta_hedging.py src/strategy/runtime/providers/vega_hedging.py src/strategy/application/market_workflow.py tests/strategy/runtime/test_provider_execution_and_hedging.py tests/strategy/runtime/test_builder.py tests/strategy/application/test_market_workflow_pipeline.py
git commit -m "feat: 接通执行调度与对冲运行时角色"
```

## Task 8: Remove Legacy Optional-Service Paths And Lock Import Boundaries

**Files:**
- Modify: `src/strategy/strategy_entry.py`
- Modify: `src/strategy/application/lifecycle_workflow.py`
- Modify: `src/strategy/application/market_workflow.py`
- Create: `tests/strategy/test_runtime_import_boundaries.py`
- Modify: `tests/strategy/application/test_lifecycle_runtime_builder.py`
- Modify: `tests/strategy/application/test_market_workflow_pipeline.py`

- [ ] **Step 1: Write failing AST-based tests proving the old direct imports are gone**

```python
from __future__ import annotations

import ast
from pathlib import Path


def _imports(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_strategy_entry_no_longer_imports_optional_services() -> None:
    imports = _imports("src/strategy/strategy_entry.py")
    assert "src.strategy.domain.domain_service.selection.future_selection_service" not in imports
    assert "src.strategy.domain.domain_service.pricing.pricing_engine" not in imports
```

- [ ] **Step 2: Run the structural regression tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/test_runtime_import_boundaries.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: FAIL because direct optional imports and compatibility attributes still remain.

- [ ] **Step 3: Delete the legacy optional-service imports, attributes, and workflow fallbacks**

```python
class StrategyEntry(StrategyTemplate):
    def __init__(...):
        ...
        self.runtime: StrategyRuntime | None = None
        # remove self.future_selection_service / self.pricing_engine / self.monitor / self.service_activation fallbacks
```

- [ ] **Step 4: Re-run the structural regression tests**

Run:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/test_runtime_import_boundaries.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_market_workflow_pipeline.py -v
```

Expected: PASS, proving the application layer now depends only on runtime roles for optional capability behavior.

- [ ] **Step 5: Commit the legacy cleanup**

```powershell
git add src/strategy/strategy_entry.py src/strategy/application/lifecycle_workflow.py src/strategy/application/market_workflow.py tests/strategy/test_runtime_import_boundaries.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_market_workflow_pipeline.py
git commit -m "refactor: 删除旧的可选能力装配路径"
```

## Final Verification

After Task 8, run all targeted suites plus the full project suite before declaring success:

```powershell
python -m pytest -c config/pytest.ini tests/strategy/runtime -v
python -m pytest -c config/pytest.ini tests/strategy/application/test_lifecycle_workflow.py tests/strategy/application/test_lifecycle_runtime_builder.py tests/strategy/application/test_market_workflow_pipeline.py -v
python -m pytest -c config/pytest.ini tests/main/config/test_config_loader_services.py tests/main/config/test_service_activation_manifest.py tests/main/scaffold/test_catalog_runtime_registry_sync.py tests/main/scaffold/test_project_scaffold.py -v
python -m pytest -c config/pytest.ini
```

Expected:

- All runtime tests pass.
- Lifecycle and workflow integration tests pass.
- Config and scaffold tests still pass with registry-derived capability metadata.
- Full suite passes with no direct optional-service imports left in the strategy host path.

If the full suite uncovers unrelated pre-existing failures, capture them explicitly in the completion note before merging.
