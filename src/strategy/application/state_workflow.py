"""策略入口的状态持久化与监控工作流。"""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.strategy.strategy_entry import StrategyEntry


class StateWorkflow:
    """处理状态快照与监控记录。"""

    def __init__(self, entry: "StrategyEntry") -> None:
        self.entry = entry

    def create_snapshot(self) -> Dict[str, Any]:
        """创建用于持久化的聚合快照。"""
        snapshot = {
            "target_aggregate": self.entry.target_aggregate.to_snapshot(),
            "position_aggregate": self.entry.position_aggregate.to_snapshot(),
            "current_dt": self.entry.current_dt,
        }
        if self.entry.combination_aggregate:
            snapshot["combination_aggregate"] = self.entry.combination_aggregate.to_snapshot()
        return snapshot

    def record_snapshot(self) -> None:
        """将运行时快照写入监控存储。"""
        if not self.entry.monitor or not self.entry.target_aggregate:
            return
        try:
            self.entry.monitor.record_snapshot(
                self.entry.target_aggregate,
                self.entry.position_aggregate,
                self.entry,
            )
        except Exception as e:
            self.entry.logger.error(f"记录快照失败: {e}")
