"""
AURA Companion - Tool Schema & Definitions
Typed schemas, risk classification, and lifecycle events for the agentic execution engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RiskCategory(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK_MUTATING = "LOW_RISK_MUTATING"
    HIGH_RISK_DESTRUCTIVE = "HIGH_RISK_DESTRUCTIVE"


class ExecutionState(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    CONTEXT_RESOLVED = "CONTEXT_RESOLVED"
    INTENT_CLASSIFIED = "INTENT_CLASSIFIED"
    PLAN_CREATED = "PLAN_CREATED"
    ARGUMENTS_VALIDATED = "ARGUMENTS_VALIDATED"
    PERMISSION_CHECKED = "PERMISSION_CHECKED"
    AWAITING_CONFIRMATION_IF_REQUIRED = "AWAITING_CONFIRMATION_IF_REQUIRED"
    EXECUTING = "EXECUTING"
    VERIFYING_RESULT = "VERIFYING_RESULT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str]
    risk_category: RiskCategory
    timeout_seconds: float = 10.0
    cancellable: bool = True
    safe_to_retry: bool = False
    max_retries: int = 0
    idempotent: bool = False
    audit_required: bool = True
    handler: Optional[Callable[..., Any]] = None


@dataclass
class ToolExecutionRequest:
    request_id: str
    tool_name: str
    arguments: Dict[str, Any]
    idempotency_key: Optional[str] = None
    user_confirmed: bool = False
    is_cancelled: bool = False


@dataclass
class ToolExecutionResult:
    request_id: str
    tool_name: str
    success: bool
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    execution_time_ms: float = 0.0
    verified: bool = False
    state: ExecutionState = ExecutionState.COMPLETED
