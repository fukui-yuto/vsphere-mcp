from __future__ import annotations

import functools
from typing import Any, Callable


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
                    "message": f"This is a {danger_level}-risk operation. Re-call with confirm=True to execute.",
                    "args": {k: v for k, v in kwargs.items() if k != "confirm"},
                }
            return func(*args, **kwargs)

        # Preserve the original function's annotations but add confirm
        import inspect

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
