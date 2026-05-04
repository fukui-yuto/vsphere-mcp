from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_host_profile_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_host_profiles() -> dict[str, Any]:
        """List all host profiles defined in vCenter."""
        logger.info("list_host_profiles")
        manager = client.content.hostProfileManager
        if manager is None:
            return {"status": "error", "error": "Host profile manager not available"}
        raw_profiles = getattr(manager, "profile", None) or []
        profiles: list[dict[str, Any]] = []
        for profile in raw_profiles:
            config = getattr(profile, "config", None)
            entry: dict[str, Any] = {
                "name": config.name if config and hasattr(config, "name") else None,
                "description": config.annotation if config and hasattr(config, "annotation") else None,
                "created_time": str(profile.createdTime) if hasattr(profile, "createdTime") and profile.createdTime else None,
                "modified_time": str(profile.modifiedTime) if hasattr(profile, "modifiedTime") and profile.modifiedTime else None,
            }
            profiles.append(entry)
        return {"total": len(profiles), "host_profiles": profiles}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def check_host_profile_compliance(host_name: str, profile_name: str) -> dict[str, Any]:
        """Check whether a host is compliant with a given host profile.

        Args:
            host_name: Name of the ESXi host to check.
            profile_name: Name of the host profile to check against.
        """
        logger.info("check_host_profile_compliance", host_name=host_name, profile_name=profile_name)
        manager = client.content.hostProfileManager
        if manager is None:
            return {"status": "error", "error": "Host profile manager not available"}

        raw_profiles = getattr(manager, "profile", None) or []
        profile_obj = None
        for profile in raw_profiles:
            config = getattr(profile, "config", None)
            if config and getattr(config, "name", None) == profile_name:
                profile_obj = profile
                break
        if profile_obj is None:
            return {"status": "error", "error": f"Host profile '{profile_name}' not found"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        task = profile_obj.CheckProfileCompliance_Task(entity=[host_obj])
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["profile_name"] = profile_name
        result["operation"] = "check_host_profile_compliance"
        return result
