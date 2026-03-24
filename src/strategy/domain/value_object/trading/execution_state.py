from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum


class ExecutionAction(Enum):
    OPEN = "open"
    CLOSE = "close"
    ROLL_OUT = "roll_out"
    ROLL_IN = "roll_in"
    HEDGE = "hedge"
    OPEN_COMBO = "open_combo"
    CLOSE_COMBO = "close_combo"
    ROLL_COMBO = "roll_combo"
    REBALANCE = "rebalance"


class ExecutionMode(Enum):
    ALL_LEGS_REQUIRED = "all_legs_required"
    BEST_EFFORT = "best_effort"


class ExecutionPhase(Enum):
    IDLE = "idle"
    RESERVED = "reserved"
    RESERVING_LEGS = "reserving_legs"
    SUBMITTING = "submitting"
    WORKING = "working"
    PARTIAL_FILLED = "partial_filled"
    CANCEL_PENDING = "cancel_pending"
    RETRY_PENDING = "retry_pending"
    ACTIVE = "active"
    PARTIAL = "partial"
    CANCELLING = "cancelling"
    DEGRADED = "degraded"
    COMPLETED = "completed"
    FAILED = "failed"
    PREEMPTED = "preempted"

    @property
    def is_terminal(self) -> bool:
        return self in {
            ExecutionPhase.IDLE,
            ExecutionPhase.COMPLETED,
            ExecutionPhase.FAILED,
            ExecutionPhase.PREEMPTED,
        }

    @property
    def is_active(self) -> bool:
        return not self.is_terminal


class ExecutionPriority(IntEnum):
    OPEN_SIGNAL = 10
    REBALANCE = 20
    TAKE_PROFIT = 30
    AV = 40
    HEDGE = 50
    MANUAL_CLOSE = 60
    RISK = 70


@dataclass
class PositionExecutionState:
    vt_symbol: str
    intent_id: str = ""
    action: ExecutionAction | None = None
    phase: ExecutionPhase = ExecutionPhase.IDLE
    priority: ExecutionPriority = ExecutionPriority.OPEN_SIGNAL
    requested_volume: int = 0
    filled_volume: int = 0
    active_order_ids: set[str] = field(default_factory=set)
    cancel_requested_order_ids: set[str] = field(default_factory=set)
    parent_combination_id: str = ""
    preempted_by_intent_id: str = ""
    reason: str = ""
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_updated(self) -> None:
        self.updated_at = datetime.now()

    @property
    def remaining_volume(self) -> int:
        return max(0, self.requested_volume - self.filled_volume)

    @property
    def is_busy(self) -> bool:
        return self.phase.is_active


@dataclass
class CombinationExecutionState:
    combination_id: str
    intent_id: str = ""
    action: ExecutionAction | None = None
    phase: ExecutionPhase = ExecutionPhase.IDLE
    priority: ExecutionPriority = ExecutionPriority.OPEN_SIGNAL
    leg_intents: dict[str, str] = field(default_factory=dict)
    leg_phases: dict[str, ExecutionPhase] = field(default_factory=dict)
    blocked_legs: set[str] = field(default_factory=set)
    preempted_by_intent_id: str = ""
    execution_mode: ExecutionMode = ExecutionMode.ALL_LEGS_REQUIRED
    reason: str = ""
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_updated(self) -> None:
        self.updated_at = datetime.now()

    @property
    def is_busy(self) -> bool:
        return self.phase.is_active
