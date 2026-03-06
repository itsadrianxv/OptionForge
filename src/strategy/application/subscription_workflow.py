"""Subscription management workflow for StrategyEntry."""

from __future__ import annotations

from datetime import datetime
import time
from typing import Dict, Set, TYPE_CHECKING

from ..infrastructure.subscription.subscription_mode_engine import (
    SubscriptionModeEngine,
    SubscriptionRuntimeContext,
)

if TYPE_CHECKING:
    from src.strategy.strategy_entry import StrategyEntry


class SubscriptionWorkflow:
    """Own all subscription mode state transitions and reconciliation."""

    def __init__(self, entry: "StrategyEntry") -> None:
        self.entry = entry

    def init_subscription_management(self) -> None:
        """Initialize subscription engine state from config."""
        cfg = dict(self.entry.subscription_config or {})
        if not cfg:
            cfg = {"enabled": False}

        self.entry.subscription_config = cfg
        self.entry.subscription_engine = SubscriptionModeEngine(cfg)
        self.entry.subscription_enabled = bool(cfg.get("enabled", True))
        self.entry.subscription_trigger_events = {
            str(item).strip()
            for item in (cfg.get("trigger_events", []) or [])
            if str(item).strip()
        }
        self.entry.subscription_refresh_sec = max(1, int(cfg.get("refresh_sec", 15) or 15))
        self.entry._last_subscription_refresh_ts = time.time()

        if self.entry.subscription_enabled:
            enabled_modes = cfg.get("enabled_modes", []) or []
            self.entry.logger.info(f"订阅模式引擎已启用: modes={enabled_modes}")
        else:
            self.entry.logger.info("订阅模式引擎已禁用")

    def should_trigger_subscription(self, trigger: str) -> bool:
        """Check whether current trigger should run reconciliation."""
        if not self.entry.subscription_enabled:
            return False
        if not self.entry.subscription_trigger_events:
            return True
        return trigger in self.entry.subscription_trigger_events

    def register_signal_temporary_symbol(self, vt_symbol: str) -> None:
        """Record temporary symbols raised by trading signals."""
        if not vt_symbol:
            return
        signal_cfg = self.entry.subscription_config.get("signal_driven_temporary", {}) if self.entry.subscription_config else {}
        ttl_sec = int(signal_cfg.get("ttl_sec", 180) or 180)
        if ttl_sec <= 0:
            return
        self.entry._signal_temp_symbols[vt_symbol] = time.time() + ttl_sec

    def collect_active_signal_symbols(self, now_ts: float) -> Set[str]:
        """Collect non-expired temporary signal symbols."""
        active: Set[str] = set()
        for symbol, expiry_ts in list(self.entry._signal_temp_symbols.items()):
            if expiry_ts <= now_ts:
                self.entry._signal_temp_symbols.pop(symbol, None)
                continue
            active.add(symbol)
        return active

    def collect_position_symbols(self) -> Set[str]:
        """Collect symbols that currently hold positions."""
        result: Set[str] = set()

        if self.entry.account_gateway:
            try:
                for position in self.entry.account_gateway.get_all_positions() or []:
                    vt_symbol = str(getattr(position, "vt_symbol", "") or "")
                    volume = float(getattr(position, "volume", 0) or 0)
                    if vt_symbol and abs(volume) > 0:
                        result.add(vt_symbol)
            except Exception:
                pass

        if self.entry.position_aggregate:
            try:
                for position in self.entry.position_aggregate.get_active_positions():
                    vt_symbol = str(getattr(position, "vt_symbol", "") or "")
                    if vt_symbol:
                        result.add(vt_symbol)
            except Exception:
                pass

        return result

    def collect_pending_order_symbols(self) -> Set[str]:
        """Collect symbols that currently have active pending orders."""
        result: Set[str] = set()
        if not self.entry.position_aggregate:
            return result

        try:
            for order in self.entry.position_aggregate.get_all_pending_orders():
                is_active = bool(getattr(order, "is_active", True))
                vt_symbol = str(getattr(order, "vt_symbol", "") or "")
                if is_active and vt_symbol:
                    result.add(vt_symbol)
        except Exception:
            pass

        return result

    def get_active_contract_map(self) -> Dict[str, str]:
        """Map product code to active contract symbol."""
        mapping: Dict[str, str] = {}
        if not self.entry.target_aggregate:
            return mapping

        for product in self.entry.target_products:
            vt_symbol = self.entry.target_aggregate.get_active_contract(product)
            if vt_symbol:
                mapping[str(product).upper()] = vt_symbol
        return mapping

    def get_last_price(self, vt_symbol: str) -> float:
        """Get latest last_price from market gateway."""
        if not self.entry.market_gateway:
            return 0.0
        tick = self.entry.market_gateway.get_tick(vt_symbol)
        if not tick:
            return 0.0
        try:
            return float(getattr(tick, "last_price", 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    def subscribe_symbol(self, vt_symbol: str) -> bool:
        """Subscribe symbol and track it in runtime set."""
        if not self.entry.market_gateway or not vt_symbol:
            return False
        ok = self.entry.market_gateway.subscribe(vt_symbol)
        if ok:
            self.entry.subscribed_symbols.add(vt_symbol)
        return ok

    def unsubscribe_symbol(self, vt_symbol: str) -> bool:
        """Unsubscribe symbol and remove it from runtime set."""
        if not self.entry.market_gateway or not vt_symbol:
            return False
        ok = self.entry.market_gateway.unsubscribe(vt_symbol)
        if ok and vt_symbol in self.entry.subscribed_symbols:
            self.entry.subscribed_symbols.remove(vt_symbol)
        return ok

    def reconcile_subscriptions(self, trigger: str) -> None:
        """Resolve target subscription list and sync with gateway."""
        if not self.entry.subscription_engine or not self.entry.market_gateway:
            return
        if not self.should_trigger_subscription(trigger):
            return

        all_contracts = self.entry.market_gateway.get_all_contracts()
        if not all_contracts:
            return

        valid_symbols = {
            str(getattr(c, "vt_symbol", "") or "")
            for c in all_contracts
            if str(getattr(c, "vt_symbol", "") or "")
        }

        now_dt = datetime.now()
        now_ts = time.time()
        signal_symbols = self.collect_active_signal_symbols(now_ts)

        context = SubscriptionRuntimeContext(
            now=now_dt,
            all_contracts=all_contracts,
            configured_products=self.entry.target_products,
            configured_contracts=sorted(self.entry.base_configured_vt_symbols),
            active_contracts_by_product=self.get_active_contract_map(),
            position_symbols=self.collect_position_symbols(),
            pending_order_symbols=self.collect_pending_order_symbols(),
            signal_symbols=signal_symbols,
            existing_subscriptions=set(self.entry.subscribed_symbols),
            get_tick=lambda symbol: self.entry.market_gateway.get_tick(symbol),
            get_last_price=self.get_last_price,
        )
        decision = self.entry.subscription_engine.resolve(context)
        if not decision.enabled:
            return

        target_symbols = {s for s in decision.target_symbols if s in valid_symbols}

        dry_run = bool(self.entry.subscription_config.get("dry_run", False))
        auto_unsubscribe = bool(self.entry.subscription_config.get("auto_unsubscribe", True))
        stale_ttl_sec = max(0, int(self.entry.subscription_config.get("stale_ttl_sec", 300) or 300))
        detail_log = bool(self.entry.subscription_config.get("log_decision_detail", True))

        to_subscribe = sorted(target_symbols - self.entry.subscribed_symbols)
        for symbol in to_subscribe:
            if dry_run:
                continue
            self.subscribe_symbol(symbol)

        for symbol in target_symbols:
            self.entry._stale_unsubscribe_since.pop(symbol, None)

        stale_candidates = sorted(self.entry.subscribed_symbols - target_symbols)
        for symbol in stale_candidates:
            first_seen = self.entry._stale_unsubscribe_since.setdefault(symbol, now_ts)
            if not auto_unsubscribe:
                continue
            if stale_ttl_sec > 0 and (now_ts - first_seen) < stale_ttl_sec:
                continue
            if dry_run:
                continue
            if self.unsubscribe_symbol(symbol):
                self.entry._stale_unsubscribe_since.pop(symbol, None)

        for symbol in list(self.entry._stale_unsubscribe_since.keys()):
            if symbol not in self.entry.subscribed_symbols:
                self.entry._stale_unsubscribe_since.pop(symbol, None)

        if detail_log:
            self.entry.logger.info(
                f"订阅重算[{trigger}] modes={decision.effective_modes} "
                f"target={len(target_symbols)} subscribed={len(self.entry.subscribed_symbols)} "
                f"add={len(to_subscribe)} remove_candidates={len(stale_candidates)}"
            )
            for warning in decision.warnings:
                self.entry.logger.warning(f"订阅模式告警: {warning}")
