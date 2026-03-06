"""策略入口的行情编排工作流。"""

from __future__ import annotations

from datetime import date
import time
from typing import Any, Dict, List, TYPE_CHECKING

from vnpy.trader.object import BarData, TickData

from ..domain.value_object.selection.selection import MarketData as SelectionMarketData
from ..infrastructure.parsing.contract_helper import ContractHelper

if TYPE_CHECKING:
    from src.strategy.strategy_entry import StrategyEntry


class MarketWorkflow:
    """协调行情回调与 K 线处理流程。"""

    def __init__(self, entry: "StrategyEntry") -> None:
        self.entry = entry

    def on_tick(self, tick: TickData) -> None:
        """处理逐笔行情推送，启用管道时转发给 K 线管道。"""
        if self.entry.bar_pipeline:
            self.entry.bar_pipeline.handle_tick(tick)

    def on_bars(self, bars: Dict[str, BarData]) -> None:
        """处理 K 线回调，包含换月检查与主流程分发。"""
        self.entry.last_bars.update(bars)

        if self.entry.target_aggregate and not self.entry.warming_up:
            first_bar = next(iter(bars.values()))
            current_dt = first_bar.datetime
            rollover_changed = False

            # 每日换月检查 (14:50)
            if current_dt.hour == 14 and current_dt.minute == 50:
                if not self.entry.rollover_check_done:
                    self.entry.logger.info(f"触发每日换月检查: {current_dt}")
                    if self.entry.target_aggregate and self.entry.market_gateway:
                        for product in self.entry.target_products:
                            try:
                                current_vt = self.entry.target_aggregate.get_active_contract(product)
                                if not current_vt:
                                    continue

                                all_contracts = self.entry.market_gateway.get_all_contracts()
                                product_contracts = [
                                    c for c in all_contracts
                                    if ContractHelper.is_contract_of_product(c, product)
                                ]
                                if not product_contracts:
                                    continue

                                market_data = self.build_future_market_data(product_contracts)
                                dominant = self.entry.future_selection_service.select_dominant_contract(
                                    product_contracts,
                                    current_dt.date(),
                                    market_data=market_data,
                                    log_func=self.entry.logger.info,
                                )
                                if dominant and dominant.vt_symbol != current_vt:
                                    new_vt = dominant.vt_symbol
                                    self.entry.logger.info(
                                        f"品种 {product} 换月: {current_vt} -> {new_vt}"
                                    )
                                    self.entry.target_aggregate.set_active_contract(product, new_vt)
                                    self.entry.target_aggregate.get_or_create_instrument(new_vt)
                                    self.entry._subscribe_symbol(new_vt)
                                    rollover_changed = True
                            except Exception as e:
                                self.entry.logger.error(f"品种 {product} 换月检查失败: {e}")
                    self.entry.rollover_check_done = True
            else:
                self.entry.rollover_check_done = False

            # 定期补漏检查
            self.entry.universe_check_interval += 1
            if self.entry.universe_check_interval >= self.entry.universe_check_threshold:
                self.entry.universe_check_interval = 0
                self.entry._validate_universe()

            if rollover_changed:
                self.entry._reconcile_subscriptions("on_rollover")

        if self.entry.bar_pipeline:
            self.entry.bar_pipeline.handle_bars(bars)
        else:
            self.entry._process_bars(bars)

        # 周期性自动保存 (非回测模式)
        if self.entry.auto_save_service and not self.entry.warming_up:
            self.entry.auto_save_service.maybe_save(self.entry._create_snapshot)

        if not self.entry.warming_up:
            now_ts = time.time()
            if now_ts - self.entry._last_subscription_refresh_ts >= self.entry.subscription_refresh_sec:
                self.entry._last_subscription_refresh_ts = now_ts
                self.entry._reconcile_subscriptions("timer")

    def process_bars(self, bars: Dict[str, BarData]) -> None:
        """处理 K 线更新并编排信号检查流程。"""
        if not self.entry.target_aggregate:
            return

        for vt_symbol, bar in bars.items():
            bar_data = {
                "datetime": bar.datetime,
                "open": bar.open_price,
                "high": bar.high_price,
                "low": bar.low_price,
                "close": bar.close_price,
                "volume": bar.volume,
            }
            self.entry.current_dt = bar.datetime

            try:
                # 1. 更新行情数据
                instrument = self.entry.target_aggregate.update_bar(vt_symbol, bar_data)

                # 2. 计算指标
                try:
                    self.entry.indicator_service.calculate_bar(instrument, bar_data)
                except Exception as e:
                    self.entry.logger.error(f"指标计算失败 [{vt_symbol}]: {e}")
                    continue

                # 3. 检查开仓信号
                try:
                    open_signal = self.entry.signal_service.check_open_signal(instrument)
                    if open_signal:
                        self.entry.logger.info(f"检测到开仓信号 [{vt_symbol}]: {open_signal}")
                        self.entry._register_signal_temporary_symbol(vt_symbol)
                        # 待实现: 完整开仓逻辑
                        # 1. 调用 OptionSelectorService 选择期权合约
                        # 2. 调用 PositionSizingService 计算仓位
                        # 3. 调用 VnpyTradeExecutionGateway 下单
                        # 4. 在 PositionAggregate 中创建持仓记录
                        self.entry.logger.info(f"执行开仓: {vt_symbol}, 信号: {open_signal}")
                except Exception as e:
                    self.entry.logger.error(f"开仓信号检查失败 [{vt_symbol}]: {e}")

                # 4. 检查平仓信号
                try:
                    positions = self.entry.position_aggregate.get_positions_by_underlying(vt_symbol)
                    for position in positions:
                        close_signal = self.entry.signal_service.check_close_signal(
                            instrument, position
                        )
                        if close_signal:
                            self.entry.logger.info(
                                f"检测到平仓信号 [{position.vt_symbol}]: {close_signal}"
                            )
                            # 待实现: 完整平仓逻辑
                            # 1. 调用 PositionSizingService 计算平仓量
                            # 2. 调用 VnpyTradeExecutionGateway 下单
                            self.entry.logger.info(f"执行平仓: {position.vt_symbol}, 信号: {close_signal}")
                except Exception as e:
                    self.entry.logger.error(f"平仓信号检查失败 [{vt_symbol}]: {e}")

            except Exception as e:
                self.entry.logger.error(f"处理 K 线更新失败 [{vt_symbol}]: {e}")

        # 5. 记录快照
        self.entry._record_snapshot()

    def validate_universe(self) -> None:
        """确保每个配置品种都有可用主力合约。"""
        if not self.entry.target_aggregate or not self.entry.market_gateway:
            return

        for product in self.entry.target_products:
            existing = self.entry.target_aggregate.get_active_contract(product)
            if existing:
                continue

            try:
                all_contracts = self.entry.market_gateway.get_all_contracts()
                product_contracts = [
                    c for c in all_contracts
                    if ContractHelper.is_contract_of_product(c, product)
                ]
                if not product_contracts:
                    self.entry.logger.warning(f"品种 {product} 未找到可用合约")
                    continue

                market_data = self.build_future_market_data(product_contracts)
                dominant = self.entry.future_selection_service.select_dominant_contract(
                    product_contracts, date.today(), market_data=market_data, log_func=self.entry.logger.info
                )
                if dominant:
                    vt_symbol = dominant.vt_symbol
                    self.entry.target_aggregate.set_active_contract(product, vt_symbol)
                    self.entry.target_aggregate.get_or_create_instrument(vt_symbol)
                    self.entry._subscribe_symbol(vt_symbol)
                    self.entry.logger.info(f"品种 {product} 主力合约: {vt_symbol}")
            except Exception as e:
                self.entry.logger.error(f"品种 {product} 主力合约初始化失败: {e}")

    def build_future_market_data(self, contracts: List[Any]) -> Dict[str, SelectionMarketData]:
        """基于行情网关逐笔数据构建主力选择所需行情映射。"""
        if not self.entry.market_gateway:
            return {}

        data: Dict[str, SelectionMarketData] = {}
        for contract in contracts:
            vt_symbol = getattr(contract, "vt_symbol", "")
            if not vt_symbol:
                continue

            tick = self.entry.market_gateway.get_tick(vt_symbol)
            if tick is None:
                continue

            try:
                volume = float(getattr(tick, "volume", 0) or 0)
                open_interest = float(getattr(tick, "open_interest", 0) or 0)
            except (TypeError, ValueError):
                continue

            if volume != volume or open_interest != open_interest:
                continue

            data[vt_symbol] = SelectionMarketData(
                vt_symbol=vt_symbol,
                volume=int(volume),
                open_interest=open_interest,
            )

        return data
