"""策略入口的领域事件桥接工作流。"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from vnpy.event.engine import Event
from vnpy.trader.object import OrderData, PositionData, TradeData

from ..domain.event.event_types import (
    CombinationStatusChangedEvent,
    EVENT_STRATEGY_ALERT,
    ManualCloseDetectedEvent,
    ManualOpenDetectedEvent,
    PositionClosedEvent,
    RiskLimitExceededEvent,
    StrategyAlertData,
)

if TYPE_CHECKING:
    from src.strategy.strategy_entry import StrategyEntry


class EventBridge:
    """将聚合根事件桥接到外部 VnPy 事件引擎。"""

    def __init__(self, entry: "StrategyEntry") -> None:
        self.entry = entry

    def on_order(self, order: OrderData) -> None:
        """处理订单推送并更新持仓聚合根。"""
        if not self.entry.position_aggregate:
            return
        order_data = {
            "vt_orderid": order.vt_orderid,
            "vt_symbol": order.vt_symbol,
            "direction": order.direction.value if hasattr(order.direction, "value") else str(order.direction),
            "offset": order.offset.value if hasattr(order.offset, "value") else str(order.offset),
            "price": order.price,
            "volume": order.volume,
            "traded": order.traded,
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        }
        self.entry.position_aggregate.update_from_order(order_data)
        self.entry._publish_domain_events()
        self.entry._reconcile_subscriptions("on_order")

    def on_trade(self, trade: TradeData) -> None:
        """处理成交推送并更新持仓聚合根。"""
        if not self.entry.position_aggregate:
            return
        trade_data = {
            "vt_tradeid": trade.vt_tradeid,
            "vt_orderid": trade.vt_orderid,
            "vt_symbol": trade.vt_symbol,
            "direction": trade.direction.value if hasattr(trade.direction, "value") else str(trade.direction),
            "offset": trade.offset.value if hasattr(trade.offset, "value") else str(trade.offset),
            "price": trade.price,
            "volume": trade.volume,
            "datetime": trade.datetime,
        }
        self.entry.position_aggregate.update_from_trade(trade_data)
        self.entry._publish_domain_events()
        self.entry._reconcile_subscriptions("on_trade")

    def process_position_event(self, event: Event) -> None:
        """处理封装后的持仓事件。"""
        self.on_position(event.data)

    def on_position(self, position: PositionData) -> None:
        """处理持仓推送并触发手动操作检测。"""
        if not self.entry.position_aggregate:
            return
        position_data = {
            "vt_symbol": position.vt_symbol,
            "direction": position.direction.value if hasattr(position.direction, "value") else str(position.direction),
            "volume": position.volume,
            "frozen": position.frozen,
            "price": position.price,
            "pnl": position.pnl,
        }
        self.entry.position_aggregate.update_from_position(position_data)
        self.entry._publish_domain_events()
        self.entry._reconcile_subscriptions("on_position")

    def publish_domain_events(self) -> None:
        """弹出领域事件并发布策略告警事件。"""
        if not self.entry.position_aggregate:
            return

        events = self.entry.position_aggregate.pop_domain_events()
        if not events:
            return

        event_engine = None
        if hasattr(self.entry, "strategy_engine") and hasattr(self.entry.strategy_engine, "event_engine"):
            event_engine = self.entry.strategy_engine.event_engine

        for domain_event in events:
            # 日志记录
            self.entry.logger.debug(f"领域事件: {domain_event.event_name} - {domain_event}")

            # 通过领域事件驱动组合状态同步
            if isinstance(domain_event, PositionClosedEvent):
                self.entry._sync_combination_status_on_position_closed(
                    domain_event=domain_event,
                    event_engine=event_engine,
                )

            # 发布到事件引擎（飞书等订阅者会收到）
            if event_engine:
                if isinstance(domain_event, (ManualCloseDetectedEvent, ManualOpenDetectedEvent)):
                    alert_type = "manual_close" if isinstance(domain_event, ManualCloseDetectedEvent) else "manual_open"
                    alert_data = StrategyAlertData.from_domain_event(
                        event=domain_event,
                        strategy_name=self.entry.strategy_name,
                        alert_type=alert_type,
                        message=f"{domain_event.event_name}: {domain_event.vt_symbol} x{domain_event.volume}"
                    )
                    vnpy_event = Event(type=EVENT_STRATEGY_ALERT, data=alert_data)
                    event_engine.put(vnpy_event)

                elif isinstance(domain_event, RiskLimitExceededEvent):
                    alert_data = StrategyAlertData.from_domain_event(
                        event=domain_event,
                        strategy_name=self.entry.strategy_name,
                        alert_type="risk_limit",
                        message=f"风控限额超标: {domain_event.limit_type} {domain_event.current_volume}/{domain_event.limit_volume}"
                    )
                    vnpy_event = Event(type=EVENT_STRATEGY_ALERT, data=alert_data)
                    event_engine.put(vnpy_event)

    def sync_combination_status_on_position_closed(
        self,
        domain_event: PositionClosedEvent,
        event_engine: Optional[Any],
    ) -> None:
        """在持仓平仓后同步组合聚合根状态。"""
        if not self.entry.position_aggregate or not self.entry.combination_aggregate:
            return

        closed_vt_symbols = self.entry.position_aggregate.get_closed_vt_symbols()
        self.entry.combination_aggregate.sync_combination_status(
            vt_symbol=domain_event.vt_symbol,
            closed_vt_symbols=closed_vt_symbols,
        )

        combination_events = self.entry.combination_aggregate.pop_domain_events()
        for combination_event in combination_events:
            self.entry.logger.debug(
                f"组合领域事件: {combination_event.event_name} - {combination_event}"
            )
            if event_engine and isinstance(
                combination_event, CombinationStatusChangedEvent
            ):
                alert_data = StrategyAlertData(
                    strategy_name=self.entry.strategy_name,
                    alert_type="combination_status",
                    message=(
                        f"组合状态变更: {combination_event.combination_id} "
                        f"{combination_event.old_status} -> {combination_event.new_status}"
                    ),
                    timestamp=combination_event.timestamp,
                    extra={
                        "combination_id": combination_event.combination_id,
                        "combination_type": combination_event.combination_type,
                        "old_status": combination_event.old_status,
                        "new_status": combination_event.new_status,
                    },
                )
                vnpy_event = Event(type=EVENT_STRATEGY_ALERT, data=alert_data)
                event_engine.put(vnpy_event)
