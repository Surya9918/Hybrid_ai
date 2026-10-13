"""
AURA Companion - Typed Tool Registry & Idempotency Store
Manages tool definitions, argument validation, idempotency caching, and permission enforcement.
"""

import time
from typing import Any, Dict, List, Optional, Set, Tuple
from src.aura_runtime.tools.schema import (
    RiskCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ExecutionState,
)
from src.aura_runtime.tools.security import SecurityBoundary


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._idempotency_cache: Dict[str, ToolExecutionResult] = {}
        self._granted_permissions: Set[str] = set(SecurityBoundary.ALLOWED_PERMISSIONS)
        self._offline_mode: bool = False

    def set_offline_mode(self, offline: bool) -> None:
        self._offline_mode = offline

    def is_offline(self) -> bool:
        return self._offline_mode

    def set_permissions(self, permissions: List[str]) -> None:
        self._granted_permissions = set(permissions)

    def register_tool(self, tool: ToolDefinition) -> None:
        if not tool.name or not tool.name.strip():
            raise ValueError("Tool name cannot be empty")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def validate_request(self, request: ToolExecutionRequest) -> Tuple[bool, Optional[str]]:
        tool = self.get_tool(request.tool_name)
        if not tool:
            return False, f"Unknown tool '{request.tool_name}'"

        # Check offline restrictions
        if self._offline_mode and "network.web_search" in tool.required_permissions:
            return False, "Tool execution blocked: offline mode is strictly enforced."

        # Validate arguments against parameter schema
        schema = tool.parameters_schema
        required_props = schema.get("required", [])
        properties = schema.get("properties", {})

        for req in required_props:
            if req not in request.arguments:
                return False, f"Missing required parameter '{req}' for tool '{tool.name}'"

        for k, v in request.arguments.items():
            if k not in properties:
                # Reject unknown properties
                return False, f"Invalid argument '{k}' for tool '{tool.name}'"
            prop_def = properties[k]
            expected_type = prop_def.get("type")
            if expected_type == "string" and not isinstance(v, str):
                return False, f"Argument '{k}' must be a string, got {type(v).__name__}"
            elif expected_type == "integer" and not isinstance(v, int):
                return False, f"Argument '{k}' must be an integer, got {type(v).__name__}"
            elif expected_type == "boolean" and not isinstance(v, bool):
                return False, f"Argument '{k}' must be a boolean, got {type(v).__name__}"
            elif expected_type == "number" and not isinstance(v, (int, float)):
                return False, f"Argument '{k}' must be a number, got {type(v).__name__}"
            elif expected_type == "array" and not isinstance(v, list):
                return False, f"Argument '{k}' must be a list, got {type(v).__name__}"
            elif expected_type == "object" and not isinstance(v, dict):
                return False, f"Argument '{k}' must be a dictionary, got {type(v).__name__}"

        return True, None

    def check_permissions(self, request: ToolExecutionRequest) -> Tuple[bool, Optional[str]]:
        tool = self.get_tool(request.tool_name)
        if not tool:
            return False, f"Unknown tool '{request.tool_name}'"

        for perm in tool.required_permissions:
            if perm not in self._granted_permissions:
                return False, f"Permission denied: required permission '{perm}' is not granted."

        return True, None

    def requires_confirmation(self, request: ToolExecutionRequest) -> bool:
        tool = self.get_tool(request.tool_name)
        if not tool:
            return False
        return tool.risk_category == RiskCategory.HIGH_RISK_DESTRUCTIVE

    def get_idempotent_result(self, key: Optional[str]) -> Optional[ToolExecutionResult]:
        if key and key in self._idempotency_cache:
            return self._idempotency_cache[key]
        return None

    def store_idempotent_result(self, key: Optional[str], result: ToolExecutionResult) -> None:
        if key:
            self._idempotency_cache[key] = result
