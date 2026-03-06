"""State persistence and monitoring workflow for StrategyEntry."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.strategy.strategy_entry import StrategyEntry


class StateWorkflow:
    """Handle state snapshot and monitoring side effects."""

    def __init__(self, entry: "StrategyEntry") -> None:
        self.entry = entry

    def create_snapshot(self) -> Dict[str, Any]:
        """Create aggregate snapshots for persistence."""
        snapshot = {
            "target_aggregate": self.entry.target_aggregate.to_snapshot(),
            "position_aggregate": self.entry.position_aggregate.to_snapshot(),
            "current_dt": self.entry.current_dt,
        }
        if self.entry.combination_aggregate:
            snapshot["combination_aggregate"] = self.entry.combination_aggregate.to_snapshot()
        return snapshot

    def record_snapshot(self) -> None:
        """Push runtime snapshot to monitoring store."""
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
