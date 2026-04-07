from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExitIntent:
    """策略无关的退出意图。"""

    subject_key: str
    reason_code: str
    priority: int
    scope_key: str = ""
    override_price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_key": self.subject_key,
            "reason_code": self.reason_code,
            "priority": int(self.priority),
            "scope_key": self.scope_key,
            "override_price": self.override_price,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExitIntent":
        return cls(
            subject_key=str(payload.get("subject_key", "") or ""),
            reason_code=str(payload.get("reason_code", "") or ""),
            priority=int(payload.get("priority", 0) or 0),
            scope_key=str(payload.get("scope_key", "") or ""),
            override_price=payload.get("override_price"),
            metadata=dict(payload.get("metadata", {}) or {}),
        )
