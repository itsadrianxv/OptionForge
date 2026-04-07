from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ExitPreemptState:
    """某个退出原因在某个 scope 下的通用抢占状态。"""

    reason_code: str
    condition_active: bool = False
    inflight: bool = False
    pending: bool = False
    pending_reason: str = ""
    updated_at: datetime | None = None

    @property
    def locked(self) -> bool:
        return self.condition_active or self.inflight or self.pending

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason_code": self.reason_code,
            "condition_active": self.condition_active,
            "inflight": self.inflight,
            "pending": self.pending,
            "pending_reason": self.pending_reason,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExitPreemptState":
        return cls(
            reason_code=str(payload.get("reason_code", "") or ""),
            condition_active=bool(payload.get("condition_active", False)),
            inflight=bool(payload.get("inflight", False)),
            pending=bool(payload.get("pending", False)),
            pending_reason=str(payload.get("pending_reason", "") or ""),
            updated_at=payload.get("updated_at"),
        )

    @classmethod
    def empty(cls, reason_code: str = "") -> "ExitPreemptState":
        return cls(reason_code=str(reason_code or ""))
