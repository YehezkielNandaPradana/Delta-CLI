# delta/agent/runtime/lifecycle.py
from enum import Enum
from typing import Set, Dict, List

class LifecycleState(str, Enum):
    OBSERVE = "OBSERVE"
    UNDERSTAND = "UNDERSTAND"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    DEBUG = "DEBUG"
    REVIEW = "REVIEW"
    REFLECT = "REFLECT"
    FINISH = "FINISH"
    FAILED = "FAILED"

class AgentLifecycleEngine:
    VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
        LifecycleState.OBSERVE: {LifecycleState.UNDERSTAND, LifecycleState.FAILED},
        LifecycleState.UNDERSTAND: {LifecycleState.PLAN, LifecycleState.FAILED},
        LifecycleState.PLAN: {LifecycleState.EXECUTE, LifecycleState.FAILED},
        LifecycleState.EXECUTE: {LifecycleState.VERIFY, LifecycleState.FAILED},
        LifecycleState.VERIFY: {LifecycleState.REVIEW, LifecycleState.DEBUG, LifecycleState.FAILED},
        LifecycleState.DEBUG: {LifecycleState.PLAN, LifecycleState.EXECUTE, LifecycleState.FAILED},
        LifecycleState.REVIEW: {LifecycleState.REFLECT, LifecycleState.PLAN, LifecycleState.FAILED},
        LifecycleState.REFLECT: {LifecycleState.FINISH, LifecycleState.FAILED},
        LifecycleState.FINISH: set(),
        LifecycleState.FAILED: set()
    }

    def __init__(self, initial_state: LifecycleState = LifecycleState.OBSERVE):
        self.current_state = initial_state
        self.history: List[LifecycleState] = [initial_state]

    def can_transition(self, target: LifecycleState) -> bool:
        allowed = self.VALID_TRANSITIONS.get(self.current_state, set())
        return target in allowed

    def transition(self, target: LifecycleState):
        if not self.can_transition(target):
            raise ValueError(f"Illegal lifecycle transition from {self.current_state.value} to {target.value}")
        self.current_state = target
        self.history.append(target)
