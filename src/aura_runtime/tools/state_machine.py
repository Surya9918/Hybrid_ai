"""
AURA Companion - Execution Lifecycle State Machine
Explicit state machine managing transitions, verification, cancellation, and observers.
"""

from typing import Any, Callable, Dict, List, Optional
from src.aura_runtime.tools.schema import ExecutionState, ToolExecutionRequest, ToolExecutionResult


class ExecutionStateMachine:
    VALID_TRANSITIONS = {
        ExecutionState.REQUEST_RECEIVED: [
            ExecutionState.CONTEXT_RESOLVED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.CONTEXT_RESOLVED: [
            ExecutionState.INTENT_CLASSIFIED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.INTENT_CLASSIFIED: [
            ExecutionState.PLAN_CREATED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.PLAN_CREATED: [
            ExecutionState.ARGUMENTS_VALIDATED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.ARGUMENTS_VALIDATED: [
            ExecutionState.PERMISSION_CHECKED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.PERMISSION_CHECKED: [
            ExecutionState.AWAITING_CONFIRMATION_IF_REQUIRED,
            ExecutionState.EXECUTING,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.AWAITING_CONFIRMATION_IF_REQUIRED: [
            ExecutionState.EXECUTING,
            ExecutionState.CANCELLED,
            ExecutionState.FAILED,
        ],
        ExecutionState.EXECUTING: [
            ExecutionState.VERIFYING_RESULT,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.VERIFYING_RESULT: [
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        ],
        ExecutionState.COMPLETED: [],
        ExecutionState.FAILED: [],
        ExecutionState.CANCELLED: [],
    }

    def __init__(self, request_id: str):
        self.request_id = request_id
        self._current_state = ExecutionState.REQUEST_RECEIVED
        self._history: List[ExecutionState] = [ExecutionState.REQUEST_RECEIVED]
        self._observers: List[Callable[[ExecutionState, str], None]] = []

    @property
    def current_state(self) -> ExecutionState:
        return self._current_state

    def add_observer(self, callback: Callable[[ExecutionState, str], None]) -> None:
        self._observers.append(callback)

    def transition_to(self, new_state: ExecutionState, reason: str = "") -> bool:
        if new_state not in self.VALID_TRANSITIONS.get(self._current_state, []):
            raise ValueError(
                f"Invalid state transition from {self._current_state} to {new_state} for request {self.request_id}"
            )
        self._current_state = new_state
        self._history.append(new_state)
        for observer in self._observers:
            try:
                observer(new_state, reason)
            except Exception:
                pass
        return True

    def get_history(self) -> List[ExecutionState]:
        return list(self._history)
