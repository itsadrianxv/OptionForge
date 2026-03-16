from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.strategy.application.event_bridge import EventBridge
from src.strategy.application.lifecycle_workflow import LifecycleWorkflow
from src.strategy.domain.aggregate.position_aggregate import PositionAggregate
from src.strategy.domain.entity.order import Order, OrderStatus
from src.strategy.domain.value_object.trading.order_instruction import Direction, Offset


def test_sync_live_oms_snapshot_reconciles_existing_position_state() -> None:
    aggregate = PositionAggregate()
    position = aggregate.create_position(
        option_vt_symbol="IO2506-C-3800.CFFEX",
        underlying_vt_symbol="IF2506.CFFEX",
        signal="bootstrap",
        target_volume=2,
    )
    position.add_fill(1, 10.0, datetime(2026, 1, 2, 9, 30, 0))

    pending_order = Order(
        vt_orderid="CTP.order-1",
        vt_symbol="IO2506-C-3800.CFFEX",
        direction=Direction.LONG,
        offset=Offset.OPEN,
        volume=2,
        price=10.0,
        status=OrderStatus.SUBMITTING,
        traded=0,
    )
    aggregate.add_pending_order(pending_order)

    entry = SimpleNamespace(
        account_gateway=SimpleNamespace(
            get_all_positions=lambda: [
                SimpleNamespace(
                    vt_symbol="IO2506-C-3800.CFFEX",
                    direction=SimpleNamespace(value="long"),
                    volume=2,
                    frozen=0,
                    price=10.0,
                    pnl=0.0,
                )
            ]
        ),
        order_gateway=SimpleNamespace(
            get_all_active_orders=lambda: [
                SimpleNamespace(
                    vt_orderid="CTP.order-1",
                    vt_symbol="IO2506-C-3800.CFFEX",
                    direction=SimpleNamespace(value="long"),
                    offset=SimpleNamespace(value="open"),
                    price=10.0,
                    volume=2,
                    traded=1,
                    status=SimpleNamespace(value="parttraded"),
                )
            ],
            get_all_trades=lambda: [
                SimpleNamespace(
                    vt_tradeid="CTP.trade-1",
                    vt_orderid="CTP.order-1",
                    vt_symbol="IO2506-C-3800.CFFEX",
                    direction=SimpleNamespace(value="long"),
                    offset=SimpleNamespace(value="open"),
                    price=10.1,
                    volume=1,
                    datetime=datetime(2026, 1, 2, 9, 31, 0),
                )
            ],
        ),
        position_aggregate=aggregate,
        combination_aggregate=None,
        strategy_name="demo",
        logger=MagicMock(),
        _publish_domain_events=lambda: None,
        _reconcile_subscriptions=lambda trigger: None,
    )
    entry.event_bridge = EventBridge(entry)

    workflow = LifecycleWorkflow(entry)
    workflow._sync_live_oms_snapshot()

    synced_position = aggregate.get_position("IO2506-C-3800.CFFEX")
    synced_order = aggregate.get_pending_order("CTP.order-1")

    assert synced_position is not None
    assert synced_position.volume == 2
    assert synced_order is not None
    assert synced_order.traded == 1
    assert synced_order.status == OrderStatus.PARTTRADED


def test_sync_live_oms_snapshot_warns_when_nothing_is_available() -> None:
    event_bridge = SimpleNamespace(
        on_position=MagicMock(),
        on_order=MagicMock(),
        on_trade=MagicMock(),
    )
    entry = SimpleNamespace(
        account_gateway=SimpleNamespace(get_all_positions=lambda: []),
        order_gateway=SimpleNamespace(
            get_all_active_orders=lambda: [],
            get_all_trades=lambda: [],
        ),
        event_bridge=event_bridge,
        logger=MagicMock(),
    )

    workflow = LifecycleWorkflow(entry)
    workflow._sync_live_oms_snapshot()

    entry.logger.warning.assert_called_once()
    event_bridge.on_position.assert_not_called()
    event_bridge.on_order.assert_not_called()
    event_bridge.on_trade.assert_not_called()
