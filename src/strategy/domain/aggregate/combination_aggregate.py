"""Combination aggregate with lifecycle and combination execution state."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from ..entity.combination import Combination
from ..event.event_types import (
    CombinationExecutionCompletedEvent,
    CombinationExecutionFailedEvent,
    CombinationExecutionStartedEvent,
    CombinationStatusChangedEvent,
    DomainEvent,
    ExecutionPhaseChangedEvent,
    ExecutionPreemptedEvent,
    LegExecutionBlockedEvent,
)
from ..value_object.combination import CombinationStatus
from ..value_object.trading.execution_state import (
    CombinationExecutionState,
    ExecutionAction,
    ExecutionMode,
    ExecutionPhase,
    ExecutionPriority,
    PositionExecutionState,
)


class CombinationAggregate:
    """Owns registered combinations and combination-level execution state."""

    def __init__(self) -> None:
        self._combinations: Dict[str, Combination] = {}
        self._symbol_index: Dict[str, Set[str]] = {}
        self._execution_states: Dict[str, CombinationExecutionState] = {}
        self._domain_events: List[DomainEvent] = []

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "combinations": {cid: combo.to_dict() for cid, combo in self._combinations.items()},
            "symbol_index": {symbol: list(cids) for symbol, cids in self._symbol_index.items()},
        }

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> "CombinationAggregate":
        obj = cls()
        for cid, combo_dict in snapshot.get("combinations", {}).items():
            obj._combinations[cid] = Combination.from_dict(combo_dict)
        for symbol, cids in snapshot.get("symbol_index", {}).items():
            obj._symbol_index[symbol] = set(cids)
        return obj

    def register_combination(self, combination: Combination) -> None:
        combination.validate()
        self._combinations[combination.combination_id] = combination
        for leg in combination.legs:
            self._symbol_index.setdefault(leg.vt_symbol, set()).add(combination.combination_id)

    def get_combination(self, combination_id: str) -> Optional[Combination]:
        return self._combinations.get(combination_id)

    def get_combinations_by_underlying(self, underlying: str) -> List[Combination]:
        return [combo for combo in self._combinations.values() if combo.underlying_vt_symbol == underlying]

    def get_active_combinations(self) -> List[Combination]:
        return [combo for combo in self._combinations.values() if combo.status != CombinationStatus.CLOSED]

    def get_combinations_by_symbol(self, vt_symbol: str) -> List[Combination]:
        combination_ids = self._symbol_index.get(vt_symbol, set())
        return [self._combinations[cid] for cid in combination_ids if cid in self._combinations]

    def get_execution_state(self, combination_id: str) -> CombinationExecutionState:
        return self._ensure_execution_state(combination_id)

    def get_all_execution_states(self) -> Dict[str, CombinationExecutionState]:
        return dict(self._execution_states)

    def dump_execution_states(self) -> Dict[str, CombinationExecutionState]:
        return dict(self._execution_states)

    def restore_execution_states(self, states: Dict[str, CombinationExecutionState]) -> None:
        self._execution_states = dict(states)

    def acquire_combination_intent(
        self,
        combination_id: str,
        intent_id: str,
        action: ExecutionAction,
        priority: ExecutionPriority = ExecutionPriority.OPEN_SIGNAL,
        execution_mode: ExecutionMode = ExecutionMode.ALL_LEGS_REQUIRED,
        reason: str = "",
    ) -> CombinationExecutionState:
        state = self._ensure_execution_state(combination_id)
        if state.phase.is_active:
            if priority <= state.priority:
                self._domain_events.append(
                    LegExecutionBlockedEvent(
                        scope="combination",
                        identifier=combination_id,
                        intent_id=intent_id,
                        blocked_by_intent_id=state.intent_id,
                        requested_action=action.value,
                        current_phase=state.phase.value,
                        incoming_priority=int(priority),
                        active_priority=int(state.priority),
                        reason=reason,
                    )
                )
                raise RuntimeError(f"combination execution blocked for {combination_id}")
            self._domain_events.append(
                ExecutionPreemptedEvent(
                    scope="combination",
                    identifier=combination_id,
                    previous_intent_id=state.intent_id,
                    new_intent_id=intent_id,
                    old_priority=int(state.priority),
                    new_priority=int(priority),
                    reason=reason,
                )
            )

        new_state = CombinationExecutionState(
            combination_id=combination_id,
            intent_id=intent_id,
            action=action,
            phase=ExecutionPhase.RESERVING_LEGS,
            priority=priority,
            execution_mode=execution_mode,
            reason=reason,
        )
        self._execution_states[combination_id] = new_state
        self._domain_events.append(
            CombinationExecutionStartedEvent(
                combination_id=combination_id,
                intent_id=intent_id,
                action=action.value,
                phase=new_state.phase.value,
            )
        )
        return new_state

    def attach_leg_intent(self, combination_id: str, vt_symbol: str, leg_intent_id: str) -> None:
        combination = self.get_combination(combination_id)
        if combination is None:
            raise KeyError(combination_id)
        if vt_symbol not in {leg.vt_symbol for leg in combination.legs}:
            raise ValueError(f"{vt_symbol} not in combination {combination_id}")

        state = self._ensure_execution_state(combination_id)
        state.leg_intents[vt_symbol] = leg_intent_id
        state.leg_phases.setdefault(vt_symbol, ExecutionPhase.RESERVED)
        state.mark_updated()

    def update_leg_phase(
        self,
        combination_id: str,
        vt_symbol: str,
        phase: ExecutionPhase,
    ) -> None:
        state = self._ensure_execution_state(combination_id)
        old_phase = state.phase
        state.leg_phases[vt_symbol] = phase
        state.phase = self._derive_phase(state)
        state.mark_updated()
        if old_phase != state.phase:
            self._domain_events.append(
                ExecutionPhaseChangedEvent(
                    scope="combination",
                    identifier=combination_id,
                    intent_id=state.intent_id,
                    old_phase=old_phase.value,
                    new_phase=state.phase.value,
                    reason=f"leg:{vt_symbol}",
                )
            )

        if state.phase == ExecutionPhase.COMPLETED:
            self._domain_events.append(
                CombinationExecutionCompletedEvent(
                    combination_id=combination_id,
                    intent_id=state.intent_id,
                    phase=state.phase.value,
                )
            )
        elif state.phase == ExecutionPhase.FAILED:
            self._domain_events.append(
                CombinationExecutionFailedEvent(
                    combination_id=combination_id,
                    intent_id=state.intent_id,
                    phase=state.phase.value,
                    reason=f"leg:{vt_symbol}",
                )
            )

    def request_combination_cancel(self, combination_id: str, reason: str = "") -> None:
        state = self._ensure_execution_state(combination_id)
        self._set_phase(state, ExecutionPhase.CANCELLING, reason or "cancel_requested")

    def preempt_combination(self, combination_id: str, new_intent_id: str, reason: str = "") -> None:
        state = self._ensure_execution_state(combination_id)
        state.preempted_by_intent_id = new_intent_id
        self._set_phase(state, ExecutionPhase.PREEMPTED, reason or "preempted")

    def sync_execution_states(
        self,
        position_execution_states: Dict[str, PositionExecutionState],
    ) -> None:
        for combination_id, state in list(self._execution_states.items()):
            combination = self._combinations.get(combination_id)
            if combination is None:
                continue
            changed = False
            for leg in combination.legs:
                leg_state = position_execution_states.get(leg.vt_symbol)
                if leg_state is None:
                    continue
                if state.leg_phases.get(leg.vt_symbol) != leg_state.phase:
                    state.leg_phases[leg.vt_symbol] = leg_state.phase
                    changed = True
            if changed:
                new_phase = self._derive_phase(state)
                if state.phase != new_phase:
                    self._set_phase(state, new_phase, "position_execution_sync")

    def sync_combination_status(
        self,
        vt_symbol: str,
        closed_vt_symbols: Set[str],
        position_execution_states: Optional[Dict[str, PositionExecutionState]] = None,
    ) -> None:
        combination_ids = self._symbol_index.get(vt_symbol, set())
        for cid in combination_ids:
            combination = self._combinations.get(cid)
            if combination is None:
                continue
            old_status = combination.status
            new_status = combination.update_status(closed_vt_symbols)
            if new_status is not None:
                self._domain_events.append(
                    CombinationStatusChangedEvent(
                        combination_id=combination.combination_id,
                        old_status=old_status.value,
                        new_status=new_status.value,
                        combination_type=combination.combination_type.value,
                    )
                )

        if position_execution_states:
            self.sync_execution_states(position_execution_states)

    def pop_domain_events(self) -> List[DomainEvent]:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def has_pending_events(self) -> bool:
        return len(self._domain_events) > 0

    def __repr__(self) -> str:
        total = len(self._combinations)
        active = len(self.get_active_combinations())
        return f"CombinationAggregate(total={total}, active={active})"

    def _ensure_execution_state(self, combination_id: str) -> CombinationExecutionState:
        state = self._execution_states.get(combination_id)
        if state is None:
            state = CombinationExecutionState(combination_id=combination_id)
            self._execution_states[combination_id] = state
        return state

    def _set_phase(
        self,
        state: CombinationExecutionState,
        phase: ExecutionPhase,
        reason: str,
    ) -> None:
        old_phase = state.phase
        if old_phase == phase:
            state.mark_updated()
            return
        state.phase = phase
        state.mark_updated()
        self._domain_events.append(
            ExecutionPhaseChangedEvent(
                scope="combination",
                identifier=state.combination_id,
                intent_id=state.intent_id,
                old_phase=old_phase.value,
                new_phase=phase.value,
                reason=reason,
            )
        )

    def _derive_phase(self, state: CombinationExecutionState) -> ExecutionPhase:
        if not state.leg_phases:
            return ExecutionPhase.RESERVING_LEGS

        phases = list(state.leg_phases.values())
        unique_phases = set(phases)

        if state.execution_mode == ExecutionMode.ALL_LEGS_REQUIRED and any(
            phase in {ExecutionPhase.FAILED, ExecutionPhase.PREEMPTED}
            for phase in phases
        ):
            if all(
                phase in {ExecutionPhase.COMPLETED, ExecutionPhase.FAILED, ExecutionPhase.PREEMPTED}
                for phase in phases
            ):
                return ExecutionPhase.FAILED
            return ExecutionPhase.DEGRADED

        if all(phase == ExecutionPhase.RESERVED for phase in phases):
            return ExecutionPhase.RESERVING_LEGS
        if all(phase == ExecutionPhase.COMPLETED for phase in phases):
            return ExecutionPhase.COMPLETED
        if any(phase == ExecutionPhase.CANCEL_PENDING for phase in phases):
            return ExecutionPhase.CANCELLING
        if any(phase == ExecutionPhase.PARTIAL_FILLED for phase in phases):
            return ExecutionPhase.PARTIAL
        if ExecutionPhase.COMPLETED in unique_phases and len(unique_phases) > 1:
            return ExecutionPhase.PARTIAL
        if any(
            phase in {
                ExecutionPhase.WORKING,
                ExecutionPhase.SUBMITTING,
                ExecutionPhase.RETRY_PENDING,
                ExecutionPhase.RESERVED,
            }
            for phase in phases
        ):
            return ExecutionPhase.ACTIVE
        if any(phase == ExecutionPhase.PREEMPTED for phase in phases):
            return ExecutionPhase.PREEMPTED
        if any(phase == ExecutionPhase.FAILED for phase in phases):
            return ExecutionPhase.FAILED
        return state.phase
