"""State workflow for snapshot creation and runtime snapshot sinks."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.strategy.strategy_entry import StrategyEntry


class StateWorkflow:
    """Builds strategy snapshots and dispatches optional snapshot sinks."""

    def __init__(self, entry: "StrategyEntry") -> None:
        self.entry = entry

    def create_snapshot(self) -> Dict[str, Any]:
        snapshot = {
            "target_aggregate": self.entry.target_aggregate.to_snapshot(),
            "position_aggregate": self.entry.position_aggregate.to_snapshot(),
            "current_dt": self.entry.current_dt,
        }
        if self.entry.combination_aggregate:
            snapshot["combination_aggregate"] = self.entry.combination_aggregate.to_snapshot()

        runtime = getattr(self.entry, "runtime", None)
        state_roles = getattr(runtime, "state", None)
        snapshot_dumpers = tuple(getattr(state_roles, "snapshot_dumpers", ()) or ())
        for dumper in snapshot_dumpers:
            try:
                extra = dumper(
                    self.entry.target_aggregate,
                    self.entry.position_aggregate,
                    self.entry.combination_aggregate,
                    self.entry,
                )
                if isinstance(extra, dict):
                    snapshot.update(extra)
            except Exception as exc:
                self.entry.logger.error(f"execution snapshot dump failed: {exc}")

        return snapshot

    def record_snapshot(self) -> None:
        runtime = getattr(self.entry, "runtime", None)
        state_roles = getattr(runtime, "state", None)
        snapshot_sinks = tuple(getattr(state_roles, "snapshot_sinks", ()) or ())
        if not snapshot_sinks or not self.entry.target_aggregate:
            return

        for sink in snapshot_sinks:
            try:
                sink(
                    self.entry.target_aggregate,
                    self.entry.position_aggregate,
                    self.entry,
                )
            except Exception as exc:
                self.entry.logger.error(f"snapshot sink failed: {exc}")
