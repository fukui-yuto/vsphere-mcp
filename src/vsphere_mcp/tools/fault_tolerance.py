from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_ft_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enable_fault_tolerance(vm_name: str, host_name: str) -> dict[str, Any]:
        """Enable Fault Tolerance for a VM by creating a secondary VM on the specified host.

        Args:
            vm_name: Name of the primary VM to protect with FT.
            host_name: Name of the ESXi host where the secondary VM will be created.
        """
        logger.info("enable_fault_tolerance", vm_name=vm_name, host_name=host_name)
        found = find_vm_with_props(client, vm_name, ["config.ftInfo"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = found["_obj"].CreateSecondaryVM_Task(host=host_obj)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["host_name"] = host_name
        result["operation"] = "enable_fault_tolerance"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def disable_fault_tolerance(vm_name: str) -> dict[str, Any]:
        """Disable Fault Tolerance for a VM.

        Args:
            vm_name: Name of the VM to disable FT for.
        """
        logger.info("disable_fault_tolerance", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.ftInfo"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        task = found["_obj"].TurnOffFaultToleranceForVM_Task()
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "disable_fault_tolerance"
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_fault_tolerance_info(vm_name: str) -> dict[str, Any]:
        """Get Fault Tolerance configuration and status for a VM.

        Args:
            vm_name: Name of the VM to query FT info for.
        """
        logger.info("get_fault_tolerance_info", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.ftInfo", "runtime.faultToleranceState"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        ft_info = found.get("config.ftInfo")
        ft_state = found.get("runtime.faultToleranceState")

        info: dict[str, Any] = {
            "vm_name": vm_name,
            "ft_enabled": ft_info is not None,
            "ft_state": str(ft_state) if ft_state is not None else None,
        }

        if ft_info is not None:
            info["instance_uuids"] = list(ft_info.instanceUuids) if hasattr(ft_info, "instanceUuids") and ft_info.instanceUuids else []
            info["role"] = ft_info.role if hasattr(ft_info, "role") else None
            info["config_paths"] = list(ft_info.configPaths) if hasattr(ft_info, "configPaths") and ft_info.configPaths else []

        return info
