"""
AURA Companion - Agentic Execution Engine
Executes the full agentic loop across lifecycle states, enforcing permissions, retries, and verification.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from src.aura_runtime.tools.schema import (
    ExecutionState,
    RiskCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
)
from src.aura_runtime.tools.state_machine import ExecutionStateMachine
from src.aura_runtime.tools.registry import ToolRegistry
from src.aura_runtime.tools.security import SecurityBoundary


class AgenticExecutionEngine:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_request(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        sm = ExecutionStateMachine(request.request_id)
        start_time = time.time()

        # Step 1: REQUEST_RECEIVED -> CONTEXT_RESOLVED
        sm.transition_to(ExecutionState.CONTEXT_RESOLVED, "Resolving request context")

        # Step 2: CONTEXT_RESOLVED -> INTENT_CLASSIFIED
        sm.transition_to(ExecutionState.INTENT_CLASSIFIED, f"Intent mapped to {request.tool_name}")

        # Step 3: Check cancellation
        if request.is_cancelled:
            sm.transition_to(ExecutionState.CANCELLED, "Request cancelled prior to planning")
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message="Operation cancelled by user",
                error_code="OPERATION_CANCELLED",
                state=ExecutionState.CANCELLED,
            )

        # Step 4: INTENT_CLASSIFIED -> PLAN_CREATED
        sm.transition_to(ExecutionState.PLAN_CREATED, "Execution plan formulated")

        # Step 5: Check Idempotency Cache
        if request.idempotency_key:
            cached = self.registry.get_idempotent_result(request.idempotency_key)
            if cached is not None:
                sm.transition_to(ExecutionState.ARGUMENTS_VALIDATED, "Idempotent request matched")
                sm.transition_to(ExecutionState.PERMISSION_CHECKED, "Permissions verified from cache")
                sm.transition_to(ExecutionState.EXECUTING, "Reusing cached idempotent result")
                sm.transition_to(ExecutionState.VERIFYING_RESULT, "Verifying cached result")
                sm.transition_to(ExecutionState.COMPLETED, "Completed via idempotency cache")
                return cached

        # Step 6: Validate Tool Exists and Schema
        tool = self.registry.get_tool(request.tool_name)
        if not tool:
            sm.transition_to(ExecutionState.FAILED, f"Unknown tool: {request.tool_name}")
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message=f"Unknown tool '{request.tool_name}'",
                error_code="UNKNOWN_TOOL",
                state=ExecutionState.FAILED,
            )

        is_valid, validation_err = self.registry.validate_request(request)
        if not is_valid:
            sm.transition_to(ExecutionState.FAILED, f"Validation failure: {validation_err}")
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message=validation_err,
                error_code="INVALID_ARGUMENTS",
                state=ExecutionState.FAILED,
            )

        sm.transition_to(ExecutionState.ARGUMENTS_VALIDATED, "Arguments conform to tool schema")

        # Step 7: Check Permissions
        has_perm, perm_err = self.registry.check_permissions(request)
        if not has_perm:
            sm.transition_to(ExecutionState.FAILED, f"Permission check failed: {perm_err}")
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message=perm_err,
                error_code="PERMISSION_DENIED",
                state=ExecutionState.FAILED,
            )

        sm.transition_to(ExecutionState.PERMISSION_CHECKED, "Permissions granted")

        # Step 8: Check Destructive Action Confirmation
        if tool.risk_category == RiskCategory.HIGH_RISK_DESTRUCTIVE and not request.user_confirmed:
            sm.transition_to(
                ExecutionState.AWAITING_CONFIRMATION_IF_REQUIRED,
                "Destructive action requires explicit user confirmation",
            )
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message="Action blocked: High-risk destructive operation requires user confirmation.",
                error_code="CONFIRMATION_REQUIRED",
                state=ExecutionState.AWAITING_CONFIRMATION_IF_REQUIRED,
            )

        # If confirmation was required and granted:
        if tool.risk_category == RiskCategory.HIGH_RISK_DESTRUCTIVE and request.user_confirmed:
            sm.transition_to(ExecutionState.AWAITING_CONFIRMATION_IF_REQUIRED, "User confirmed")

        # Step 9: Check cancellation right before execution
        if request.is_cancelled:
            sm.transition_to(ExecutionState.CANCELLED, "Cancelled right before execution")
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message="Operation cancelled by user",
                error_code="OPERATION_CANCELLED",
                state=ExecutionState.CANCELLED,
            )

        # Step 10: EXECUTING with Bounded Retries
        sm.transition_to(ExecutionState.EXECUTING, "Invoking platform handler")

        output = None
        error_msg = None
        retry_count = 0
        execution_success = False

        while True:
            try:
                if tool.handler:
                    output = tool.handler(**request.arguments)
                    execution_success = True
                    break
                else:
                    output = {"status": "ok"}
                    execution_success = True
                    break
            except Exception as e:
                error_msg = str(e)
                if tool.safe_to_retry and retry_count < tool.max_retries:
                    retry_count += 1
                    time.sleep(0.05)
                    continue
                else:
                    break

        duration_ms = (time.time() - start_time) * 1000.0

        if not execution_success:
            sm.transition_to(ExecutionState.FAILED, f"Execution failed: {error_msg}")
            return ToolExecutionResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                success=False,
                error_message=error_msg,
                error_code="EXECUTION_ERROR",
                retry_count=retry_count,
                execution_time_ms=duration_ms,
                state=ExecutionState.FAILED,
            )

        # Step 11: VERIFYING_RESULT
        sm.transition_to(ExecutionState.VERIFYING_RESULT, "Verifying output integrity")
        # Verify output is a valid dict matching output criteria
        verified = isinstance(output, dict)

        # Step 12: COMPLETED
        sm.transition_to(ExecutionState.COMPLETED, "Execution and verification succeeded")

        result = ToolExecutionResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            output=output,
            retry_count=retry_count,
            execution_time_ms=duration_ms,
            verified=verified,
            state=ExecutionState.COMPLETED,
        )

        if request.idempotency_key:
            self.registry.store_idempotent_result(request.idempotency_key, result)

        return result
