from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from vsphere_mcp.logging import get_logger

logger = get_logger(__name__)

# Default: all tools allowed
DEFAULT_POLICY: dict[str, Any] = {
    "version": 1,
    "default_action": "allow",
    "denied_tools": [],
    "allowed_tools": [],
}


class RBACPolicy:
    """Simple tool-level access control policy."""

    def __init__(self, policy_file: str | None = None) -> None:
        self._policy = DEFAULT_POLICY.copy()
        if policy_file:
            self._load(policy_file)

    def _load(self, path: str) -> None:
        p = Path(path)
        if p.is_file():
            try:
                self._policy = json.loads(p.read_text())
                logger.info("rbac_policy_loaded", path=path)
            except Exception as e:
                logger.warning("rbac_policy_load_failed", path=path, error=str(e))

    def is_allowed(self, tool_name: str) -> bool:
        """Check whether a tool is allowed by the current policy."""
        denied = self._policy.get("denied_tools", [])
        if tool_name in denied:
            return False

        allowed = self._policy.get("allowed_tools", [])
        if allowed:
            return tool_name in allowed

        return self._policy.get("default_action", "allow") == "allow"

    @property
    def policy(self) -> dict[str, Any]:
        """Return a copy of the current policy."""
        return self._policy.copy()


_rbac_policy: RBACPolicy | None = None


def get_rbac_policy() -> RBACPolicy:
    """Return the singleton RBAC policy, loading from VSPHERE_RBAC_POLICY env var."""
    global _rbac_policy
    if _rbac_policy is None:
        policy_file = os.environ.get("VSPHERE_RBAC_POLICY")
        _rbac_policy = RBACPolicy(policy_file)
    return _rbac_policy
