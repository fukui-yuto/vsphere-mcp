from __future__ import annotations

import functools
import inspect
import time
from typing import Any, Callable

from vsphere_mcp.logging import SENSITIVE_KEYS, get_logger
from vsphere_mcp.metrics import record_tool_call

logger = get_logger(__name__)


class VSphereToolError(Exception):
    """User-readable error from a vSphere tool."""


def require_confirm(danger_level: str = "medium") -> Callable[..., Any]:
    """Decorator for destructive operations. Requires confirm=True to execute."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, confirm: bool = False, **kwargs: Any) -> Any:
            if not confirm:
                from vsphere_mcp.i18n import msg

                return {
                    "status": "confirmation_required",
                    "danger_level": danger_level,
                    "tool": func.__name__,
                    "message": msg("confirmation_required", danger_level=danger_level),
                    "args": {
                        k: ("***MASKED***" if any(s in k.lower() for s in SENSITIVE_KEYS) else v)
                        for k, v in kwargs.items()
                        if k != "confirm"
                    },
                }
            return func(*args, **kwargs)

        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        confirm_param = inspect.Parameter(
            "confirm",
            inspect.Parameter.KEYWORD_ONLY,
            default=False,
            annotation=bool,
        )
        params.append(confirm_param)
        wrapper.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]

        original_doc = func.__doc__ or ""
        wrapper.__doc__ = f"{original_doc}\n\n[{danger_level.upper()} RISK] Requires confirm=True to execute."

        return wrapper

    return decorator


def handle_tool_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that catches vSphere exceptions and returns user-readable errors with duration."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from vsphere_mcp.rbac import get_rbac_policy

        policy = get_rbac_policy()
        if not policy.is_allowed(func.__name__):
            return {
                "status": "error",
                "error": f"Tool '{func.__name__}' is not allowed by RBAC policy",
            }

        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = round((time.time() - start) * 1000, 1)
            logger.info(
                "tool_completed",
                tool=func.__name__,
                duration_ms=duration_ms,
                status="success",
            )
            record_tool_call(func.__name__, "success", duration_ms / 1000)
            return result
        except VSphereToolError as e:
            duration_ms = round((time.time() - start) * 1000, 1)
            logger.warning(
                "tool_error",
                tool=func.__name__,
                duration_ms=duration_ms,
                error=str(e),
            )
            record_tool_call(func.__name__, "error", duration_ms / 1000)
            return {"status": "error", "error": str(e)}
        except Exception as e:
            duration_ms = round((time.time() - start) * 1000, 1)
            error_type = type(e).__name__
            logger.error(
                "tool_unexpected_error",
                tool=func.__name__,
                duration_ms=duration_ms,
                error_type=error_type,
                error=str(e),
            )
            record_tool_call(func.__name__, "error", duration_ms / 1000)
            return {"status": "error", "error": f"{error_type}: {e}"}

    wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
    return wrapper


TASK_POLL_INTERVAL = 0.5
TASK_TIMEOUT_SEC = 300


def find_vm_with_props(client: Any, vm_name: str, extra_props: list[str] | None = None) -> dict[str, Any] | None:
    """Find a VM by name and return its object ref + requested properties."""
    from pyVmomi import vim

    from vsphere_mcp.utils.property_collector import collect_properties

    props = ["name", "runtime.powerState"] + (extra_props or [])
    items = collect_properties(client, vim.VirtualMachine, props)
    for item in items:
        if item.get("name") == vm_name:
            return item
    return None


def find_host_by_name(client: Any, host_name: str) -> Any | None:
    """Find an ESXi host by name and return its managed object."""
    from pyVmomi import vim

    from vsphere_mcp.utils.property_collector import collect_properties

    items = collect_properties(client, vim.HostSystem, ["name"])
    for item in items:
        if item.get("name") == host_name:
            return item["_obj"]
    return None


def wait_for_task(task: Any, timeout: int = TASK_TIMEOUT_SEC) -> dict[str, Any]:
    """Wait for a vSphere task to complete with polling and timeout."""
    from pyVmomi import vim

    start = time.time()
    while task.info.state in (vim.TaskInfo.State.queued, vim.TaskInfo.State.running):
        if time.time() - start > timeout:
            try:
                task.CancelTask()
            except Exception:
                pass
            return {"status": "error", "message": f"Task timed out after {timeout}s"}
        time.sleep(TASK_POLL_INTERVAL)
    if task.info.state == vim.TaskInfo.State.success:
        return {"status": "success"}
    error_msg = str(task.info.error) if task.info.error else "Unknown error"
    return {"status": "error", "message": error_msg}
