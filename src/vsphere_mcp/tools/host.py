from __future__ import annotations

from typing import Any

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_host_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enter_maintenance_mode(
        host_name: str,
        timeout: int = 300,
        evacuate_powered_off_vms: bool = True,
    ) -> dict[str, Any]:
        """Put an ESXi host into maintenance mode. Running VMs will be migrated or shut down."""
        logger.info("enter_maintenance_mode", host_name=host_name)
        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host.EnterMaintenanceMode(timeout=timeout, evacuatePoweredOffVms=evacuate_powered_off_vms)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "enter_maintenance_mode"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def exit_maintenance_mode(
        host_name: str,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Take an ESXi host out of maintenance mode."""
        logger.info("exit_maintenance_mode", host_name=host_name)
        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host.ExitMaintenanceMode(timeout=timeout)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "exit_maintenance_mode"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def shutdown_host(host_name: str, force: bool = False) -> dict[str, Any]:
        """Shut down an ESXi host. Host should be in maintenance mode first."""
        logger.info("shutdown_host", host_name=host_name, force=force)
        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        if not host.runtime.inMaintenanceMode and not force:
            return {
                "status": "error",
                "error": f"Host '{host_name}' is not in maintenance mode. Set force=True to override.",
            }
        task = host.Shutdown_Task(force=force)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "shutdown_host"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def reboot_host(host_name: str, force: bool = False) -> dict[str, Any]:
        """Reboot an ESXi host. Host should be in maintenance mode first."""
        logger.info("reboot_host", host_name=host_name, force=force)
        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        if not host.runtime.inMaintenanceMode and not force:
            return {
                "status": "error",
                "error": f"Host '{host_name}' is not in maintenance mode. Set force=True to override.",
            }
        task = host.Reboot_Task(force=force)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "reboot_host"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def disconnect_host(host_name: str) -> dict[str, Any]:
        """Disconnect an ESXi host from vCenter."""
        logger.info("disconnect_host", host_name=host_name)
        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        host.Disconnect()
        return {"status": "success", "host_name": host_name, "operation": "disconnect_host"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def reconnect_host(host_name: str) -> dict[str, Any]:
        """Reconnect a disconnected ESXi host to vCenter."""
        logger.info("reconnect_host", host_name=host_name)
        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host.ReconnectHost_Task()
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "reconnect_host"
        return result
