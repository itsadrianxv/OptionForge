"""Strategy scaffold generator."""

from __future__ import annotations

from pathlib import Path
import re
from textwrap import dedent


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", (name or "strategy").strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug.lower() or "strategy"


def _classify(name: str) -> str:
    slug = _slugify(name)
    return "".join(part.capitalize() for part in slug.split("_")) or "Strategy"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip("\n"), encoding="utf-8")


def scaffold_strategy(name: str, destination: Path, force: bool = False) -> Path:
    """Generate a minimal strategy package template."""
    slug = _slugify(name)
    class_prefix = _classify(name)
    package_dir = destination / slug
    if package_dir.exists() and not force:
        raise FileExistsError(f"Directory already exists: {package_dir}")

    package_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = package_dir / "tests"

    _write(package_dir / "__init__.py", "")
    _write(tests_dir / "__init__.py", "")

    _write(
        package_dir / "indicator_service.py",
        f'''
        from __future__ import annotations

        from typing import Optional, TYPE_CHECKING

        from src.strategy.domain.domain_service.signal.indicator_service import IIndicatorService
        from src.strategy.domain.value_object.signal import IndicatorComputationResult, IndicatorContext

        if TYPE_CHECKING:
            from src.strategy.domain.entity.target_instrument import TargetInstrument


        class {class_prefix}IndicatorService(IIndicatorService):
            """Stateless indicator service template.

            Keep mutable runtime state outside the service. If the indicator needs
            configuration, pass it through explicit context or dedicated value objects.
            """

            def calculate_bar(
                self,
                instrument: "TargetInstrument",
                bar: dict,
                context: Optional[IndicatorContext] = None,
            ) -> IndicatorComputationResult:
                instrument.indicators.setdefault("template", {{}})
                instrument.indicators["template"].update({{
                    "last_close": float(bar.get("close", 0) or 0),
                    "bar_dt": bar.get("datetime"),
                }})
                return IndicatorComputationResult(
                    indicator_key="template",
                    updated_indicator_keys=["template"],
                    values=dict(instrument.indicators["template"]),
                    summary="Template indicator updated.",
                )
        ''',
    )
    _write(
        package_dir / "signal_service.py",
        f'''
        from __future__ import annotations

        from typing import Optional, TYPE_CHECKING

        from src.strategy.domain.domain_service.signal.signal_service import ISignalService
        from src.strategy.domain.value_object.signal import SignalContext, SignalDecision

        if TYPE_CHECKING:
            from src.strategy.domain.entity.position import Position
            from src.strategy.domain.entity.target_instrument import TargetInstrument


        class {class_prefix}SignalService(ISignalService):
            """Stateless signal service template.

            Express policy through explicit inputs instead of keeping mutable state on
            the service instance.
            """

            def check_open_signal(
                self,
                instrument: "TargetInstrument",
                context: Optional[SignalContext] = None,
            ) -> Optional[SignalDecision]:
                return None

            def check_close_signal(
                self,
                instrument: "TargetInstrument",
                position: "Position",
                context: Optional[SignalContext] = None,
            ) -> Optional[SignalDecision]:
                return None
        ''',
    )
    _write(
        package_dir / "strategy_contract.toml",
        f'''
        [strategy_contracts]
        indicator_service = "example.{slug}.indicator_service:{class_prefix}IndicatorService"
        signal_service = "example.{slug}.signal_service:{class_prefix}SignalService"

        [strategy_contracts.indicator_kwargs]

        [strategy_contracts.signal_kwargs]
        option_type = "call"
        strike_level = 1

        [service_activation]
        future_selection = true
        option_chain = true
        option_selector = true
        position_sizing = false
        pricing_engine = false
        greeks_calculator = false
        portfolio_risk = false
        smart_order_executor = false
        monitoring = true
        decision_observability = true

        [observability]
        decision_journal_maxlen = 200
        emit_noop_decisions = false
        ''',
    )
    _write(
        tests_dir / "test_contracts.py",
        f'''
        from example.{slug}.indicator_service import {class_prefix}IndicatorService
        from example.{slug}.signal_service import {class_prefix}SignalService
        from src.strategy.domain.entity.target_instrument import TargetInstrument


        def test_indicator_service_updates_template_indicator() -> None:
            service = {class_prefix}IndicatorService()
            instrument = TargetInstrument(vt_symbol="IF2506.CFFEX")

            result = service.calculate_bar(
                instrument,
                {{"datetime": "2026-01-01 09:31:00", "close": 123.4}},
            )

            assert result.indicator_key == "template"
            assert instrument.indicators["template"]["last_close"] == 123.4


        def test_signal_service_defaults_to_no_signal() -> None:
            service = {class_prefix}SignalService()
            instrument = TargetInstrument(vt_symbol="IF2506.CFFEX")

            assert service.check_open_signal(instrument) is None


        def test_scaffolded_services_start_without_instance_state() -> None:
            assert vars({class_prefix}IndicatorService()) == {{}}
            assert vars({class_prefix}SignalService()) == {{}}
        ''',
    )
    _write(
        package_dir / "README.md",
        f'''
        # {slug}

        This template package is generated for a new strategy implementation.

        Included files:
        - `indicator_service.py`: stateless indicator-service template
        - `signal_service.py`: stateless signal-service template
        - `strategy_contract.toml`: wiring and observability defaults
        - `tests/test_contracts.py`: minimal smoke tests for the generated contracts

        Recommended next steps:
        1. Read `docs/architecture/ddd-constitution.md` and `docs/architecture/context-map.md`.
        2. Keep domain services stateless; pass policy through explicit context or value objects.
        3. Fill in `indicator_service.py` and `signal_service.py` with strategy-specific logic.
        4. Merge `strategy_contract.toml` into the real strategy configuration.
        ''',
    )

    return package_dir
