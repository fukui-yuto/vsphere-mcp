from __future__ import annotations

import functools
import inspect
import time
from typing import Any, Callable

from vsphere_mcp.logging import get_logger

logger = get_logger(__name__)


class VSphereToolError(Exception):
    """User-readable error from a vSphere tool."""


def require_confirm(danger_level: str = "medium") -> Callable[..., Any]:
    """Decorator for destructive operations. Requires confirm=True to execute."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, confirm: bool = False, **kwargs: Any) -> Any:
            if not confirm:
                return {
                    "status": "confirmation_required",
                    "danger_level": danger_level,
                    "tool": func.__name__,
                    "message": (f"This is a {danger_level}-risk operation. Re-call with confirm=True to execute."),
                    "args": {k: v for k, v in kwargs.items() if k != "confirm"},
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
            return result
        except VSphereToolError as e:
            duration_ms = round((time.time() - start) * 1000, 1)
            logger.warning(
                "tool_error",
                tool=func.__name__,
                duration_ms=duration_ms,
                error=str(e),
            )
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
            return {"status": "error", "error": f"{error_type}: {e}"}

    wrapper.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
    return wrapper
