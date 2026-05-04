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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_host_profile(reference_host: str, profile_name: str, description: str = "") -> dict[str, Any]:
        """Create a host profile from a reference ESXi host.

        Args:
            reference_host: Name of the ESXi host to use as reference.
            profile_name: Name for the new host profile.
            description: Optional description / annotation for the profile.
        """
        logger.info("create_host_profile", reference_host=reference_host, profile_name=profile_name)
        manager = client.content.hostProfileManager
        if manager is None:
            return {"status": "error", "error": "Host profile manager not available"}

        host_obj = find_host_by_name(client, reference_host)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{reference_host}' not found"}

        create_spec = vim.profile.host.HostProfileHostBasedConfigSpec(
            host=host_obj,
            name=profile_name,
            annotation=description,
        )
        profile_obj = manager.CreateProfile(createSpec=create_spec)
        config = getattr(profile_obj, "config", None)
        return {
            "status": "success",
            "operation": "create_host_profile",
            "profile_name": config.name if config and hasattr(config, "name") else profile_name,
            "reference_host": reference_host,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_host_profile(profile_name: str) -> dict[str, Any]:
        """Delete a host profile by name.

        Args:
            profile_name: Name of the host profile to delete.
        """
        logger.info("delete_host_profile", profile_name=profile_name)
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

        profile_obj.DestroyProfile()
        return {
            "status": "success",
            "operation": "delete_host_profile",
            "profile_name": profile_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def apply_host_profile(host_name: str, profile_name: str) -> dict[str, Any]:
        """Apply a host profile to an ESXi host.

        Args:
            host_name: Name of the ESXi host to apply the profile to.
            profile_name: Name of the host profile to apply.
        """
        logger.info("apply_host_profile", host_name=host_name, profile_name=profile_name)
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

        execute_result = profile_obj.ExecuteHostProfile(
            host=host_obj,
            deferredParam=[],
        )
        config_spec = getattr(execute_result, "configSpec", None)
        if config_spec is None:
            return {"status": "error", "error": "ExecuteHostProfile did not return a configSpec"}

        task = manager.ApplyHostConfig_Task(host=host_obj, configSpec=config_spec)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["profile_name"] = profile_name
        result["operation"] = "apply_host_profile"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def associate_host_with_profile(host_name: str, profile_name: str) -> dict[str, Any]:
        """Associate an ESXi host with a host profile.

        Args:
            host_name: Name of the ESXi host to associate.
            profile_name: Name of the host profile to associate with.
        """
        logger.info("associate_host_with_profile", host_name=host_name, profile_name=profile_name)
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

        profile_obj.AssociateProfile(hosts=[host_obj])
        return {
            "status": "success",
            "operation": "associate_host_with_profile",
            "host_name": host_name,
            "profile_name": profile_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def export_host_profile(profile_name: str) -> dict[str, Any]:
        """Export a host profile as serialized profile data.

        Args:
            profile_name: Name of the host profile to export.
        """
        logger.info("export_host_profile", profile_name=profile_name)
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

        exported_data = manager.ExportProfile(profile=profile_obj)
        return {
            "status": "success",
            "operation": "export_host_profile",
            "profile_name": profile_name,
            "profile_data": str(exported_data) if exported_data is not None else None,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remediate_host_profile(host_name: str, profile_name: str) -> dict[str, Any]:
        """Remediate an ESXi host to comply with a host profile.

        Args:
            host_name: Name of the ESXi host to remediate.
            profile_name: Name of the host profile to remediate against.
        """
        logger.info("remediate_host_profile", host_name=host_name, profile_name=profile_name)
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

        execute_result = profile_obj.ExecuteHostProfile(
            host=host_obj,
            deferredParam=[],
        )
        config_spec = getattr(execute_result, "configSpec", None)
        if config_spec is None:
            return {"status": "error", "error": "ExecuteHostProfile did not return a configSpec"}

        task = manager.ApplyHostConfig_Task(host=host_obj, configSpec=config_spec)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["profile_name"] = profile_name
        result["operation"] = "remediate_host_profile"
        return result
