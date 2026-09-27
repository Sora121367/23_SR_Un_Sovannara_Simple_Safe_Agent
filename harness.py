

from pydantic import ValidationError

from schema import TOOL_SCHEMAS
from tools import TOOL_IMPLEMENTATIONS

# Action -> roles allowed to perform it.
# search_course and check_schedule are read-only and open to everyone.
# register_course is a write/sensitive action, only for admins.
PERMISSIONS = {
    "search_course":   {"student", "admin"},
    "check_schedule":  {"student", "admin"},
    "register_course": {"admin"},          # students CANNOT self-register in this policy
}

MAX_TOOL_CALLS = 6  # Safety: hard cap on tool calls per run, prevents infinite loops


class PermissionError_(Exception):
    """Raised internally when a role is not allowed to perform an action."""
    pass


def check_permission(tool_name: str, role: str) -> None:
    """
    Enforce permission in application code (not just in the prompt).
    Raises PermissionError_ if the role is not allowed to call this tool.
    """
    allowed_roles = PERMISSIONS.get(tool_name)
    if allowed_roles is None:
        raise PermissionError_(f"Unknown tool '{tool_name}' is not in the permission table (deny by default).")
    if role not in allowed_roles:
        raise PermissionError_(f"Role '{role}' is not permitted to call '{tool_name}'.")


def validate_input(tool_name: str, raw_args: dict) -> dict:
    """
    Basic input validation using the Pydantic schema for this tool.
    Returns validated/cleaned args as a dict, or raises pydantic.ValidationError.
    """
    schema_cls = TOOL_SCHEMAS.get(tool_name)
    if schema_cls is None:
        raise ValueError(f"No schema defined for tool '{tool_name}'.")
    validated = schema_cls(**raw_args)
    return validated.model_dump()


def execute_tool(tool_name: str, raw_args: dict, role: str, call_count: int) -> dict:
    """
    The single gate every tool call must pass through:
      1. iteration/tool-call limit check
      2. permission check
      3. input validation
      4. controlled execution (catch exceptions -> structured error)

    Returns a result dict that always has a "status" field ("ok" or "error").
    """
    # 1. Safety: max tool-call limit
    if call_count > MAX_TOOL_CALLS:
        return {
            "status": "error",
            "error_code": "MAX_TOOL_CALLS_EXCEEDED",
            "message": f"Stopped after reaching the maximum of {MAX_TOOL_CALLS} tool calls for this run.",
        }

    # 2. Permission control (application code, not just prompt)
    try:
        check_permission(tool_name, role)
    except PermissionError_ as e:
        return {"status": "error", "error_code": "PERMISSION_DENIED", "message": str(e)}

    # 3. Input validation
    try:
        clean_args = validate_input(tool_name, raw_args)
    except ValidationError as e:
        return {"status": "error", "error_code": "INVALID_INPUT", "message": str(e)}
    except ValueError as e:
        return {"status": "error", "error_code": "UNKNOWN_TOOL", "message": str(e)}

    # 4. Controlled execution
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if impl is None:
        return {"status": "error", "error_code": "UNKNOWN_TOOL", "message": f"No implementation for '{tool_name}'."}

    try:
        result = impl(**clean_args)
        return result
    except Exception as e: 
        return {"status": "error", "error_code": "TOOL_EXECUTION_FAILED", "message": str(e)}