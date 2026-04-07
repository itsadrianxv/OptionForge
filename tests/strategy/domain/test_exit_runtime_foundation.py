from __future__ import annotations

from src.strategy.domain.aggregate.position_aggregate import PositionAggregate
from src.strategy.domain.entity.order import Order, OrderOwnershipScope
from src.strategy.domain.value_object.trading import Direction, Offset


def test_order_ownership_scope_defaults_to_managed_for_short_open() -> None:
    order = Order(
        vt_orderid="ORDER-1",
        vt_symbol="IO2506-C-3800.CFFEX",
        direction=Direction.SHORT,
        offset=Offset.OPEN,
        volume=1,
    )

    assert order.ownership_scope == OrderOwnershipScope.MANAGED_ACTIONABLE
    assert order.is_strategy_actionable is True
    assert order.is_observed_external is False


def test_order_ownership_scope_defaults_to_observed_for_non_managed_shape() -> None:
    order = Order(
        vt_orderid="ORDER-2",
        vt_symbol="IO2506-C-3800.CFFEX",
        direction=Direction.LONG,
        offset=Offset.OPEN,
        volume=1,
    )

    assert order.ownership_scope == OrderOwnershipScope.OBSERVED_EXTERNAL
    assert order.is_strategy_actionable is False
    assert order.is_observed_external is True


def test_exit_intent_requires_higher_priority_to_replace_existing_intent() -> None:
    aggregate = PositionAggregate()

    created = aggregate.ensure_exit_intent(
        subject_key="IO2506-C-3800.CFFEX",
        reason_code="guarded_exit",
        priority=50,
        scope_key="underlying:IF2506.CFFEX",
        override_price=10.5,
        metadata={"source": "guard"},
    )

    rejected = aggregate.ensure_exit_intent(
        subject_key="IO2506-C-3800.CFFEX",
        reason_code="lower_exit",
        priority=40,
        scope_key="underlying:IF2506.CFFEX",
    )

    replaced = aggregate.ensure_exit_intent(
        subject_key="IO2506-C-3800.CFFEX",
        reason_code="higher_exit",
        priority=80,
        scope_key="underlying:IF2506.CFFEX",
    )

    intent = aggregate.get_exit_intent("IO2506-C-3800.CFFEX")

    assert created is True
    assert rejected is False
    assert replaced is True
    assert intent is not None
    assert intent.reason_code == "higher_exit"
    assert intent.priority == 80
    assert intent.scope_key == "underlying:IF2506.CFFEX"


def test_position_aggregate_snapshot_roundtrip_preserves_exit_intents() -> None:
    aggregate = PositionAggregate()
    aggregate.ensure_exit_intent(
        subject_key="IO2506-C-3800.CFFEX",
        reason_code="portfolio_exit",
        priority=70,
        scope_key="portfolio:default",
        metadata={"attempt": 1},
    )

    restored = PositionAggregate.from_snapshot(aggregate.to_snapshot())
    intent = restored.get_exit_intent("IO2506-C-3800.CFFEX")

    assert intent is not None
    assert intent.reason_code == "portfolio_exit"
    assert intent.priority == 70
    assert intent.scope_key == "portfolio:default"
    assert intent.metadata == {"attempt": 1}
