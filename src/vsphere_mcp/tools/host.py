from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.tools.power import _wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_host_obj(client: VSphereClient, host_name: str) -> vim.HostSystem | None:
    items = collect_properties(client, vim.HostSystem, ["name"])
    for item in items:
        if item.get("name") == host_name:
            return item["_obj"]
    return None


def register_host_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @require_confirm(danger_level="high")
    @handle_tool_errors
    def enter_maintenance_mode(
        host_name: str,
        timeout: int = 300,
        evacuate_powered_off_vms: bool = True,
    ) -> dict[str, Any]:
        """Put an ESXi host into maintenance mode. Running VMs will be migrated or shut down."""
        logger.info("enter_maintenance_mode", host_name=host_name)
        host = _find_host_obj(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host.EnterMaintenanceMode(timeout=timeout, evacuatePoweredOffVms=evacuate_powered_off_vms)
        result = _wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "enter_maintenance_mode"
        return result

    @mcp.tool()
    @require_confirm(danger_level="high")
    @handle_tool_errors
    def exit_maintenance_mode(
        host_name: str,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Take an ESXi host out of maintenance mode."""
        logger.info("exit_maintenance_mode", host_name=host_name)
        host = _find_host_obj(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host.ExitMaintenanceMode(timeout=timeout)
        result = _wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "exit_maintenance_mode"
        return result
