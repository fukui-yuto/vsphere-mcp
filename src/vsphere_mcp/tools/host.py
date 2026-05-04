from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

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
        task = host.ShutdownHost_Task(force=force)
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
        task = host.RebootHost_Task(force=force)
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
        task = host.DisconnectHost_Task()
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "disconnect_host"
        return result

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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_host_to_cluster(
        cluster_name: str,
        host_name_or_ip: str,
        username: str,
        password: str,
        ssl_thumbprint: str | None = None,
    ) -> dict[str, Any]:
        """Add an ESXi host to a cluster in vCenter."""
        logger.info("add_host_to_cluster", cluster_name=cluster_name, host_name_or_ip=host_name_or_ip)
        items = collect_properties(client, vim.ClusterComputeResource, ["name"])
        cluster_obj = None
        for item in items:
            if item.get("name") == cluster_name:
                cluster_obj = item["_obj"]
                break
        if cluster_obj is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}
        spec = vim.host.ConnectSpec(
            hostName=host_name_or_ip,
            userName=username,
            password=password,
            sslThumbprint=ssl_thumbprint or "",
            force=True,
        )
        task = cluster_obj.AddHost_Task(spec=spec, asConnected=True)
        result = wait_for_task(task)
        result["cluster_name"] = cluster_name
        result["host_name_or_ip"] = host_name_or_ip
        result["operation"] = "add_host_to_cluster"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def remove_host(host_name: str) -> dict[str, Any]:
        """Remove a host from vCenter inventory."""
        logger.info("remove_host", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host_obj.Destroy_Task()
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["operation"] = "remove_host"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def move_host_to_cluster(
        host_name: str,
        target_cluster: str,
    ) -> dict[str, Any]:
        """Move a standalone ESXi host into a cluster."""
        logger.info("move_host_to_cluster", host_name=host_name, target_cluster=target_cluster)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        items = collect_properties(client, vim.ClusterComputeResource, ["name"])
        cluster_obj = None
        for item in items:
            if item.get("name") == target_cluster:
                cluster_obj = item["_obj"]
                break
        if cluster_obj is None:
            return {"status": "error", "error": f"Cluster '{target_cluster}' not found"}
        task = cluster_obj.MoveHostInto_Task(host=host_obj, resourcePool=None)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["target_cluster"] = target_cluster
        result["operation"] = "move_host_to_cluster"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_standalone_host(
        datacenter_name: str,
        host_name: str,
        username: str,
        password: str,
        ssl_thumbprint: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Add a standalone ESXi host to a datacenter's host folder.

        Args:
            datacenter_name: Name of the datacenter to add the host to.
            host_name: Hostname or IP address of the ESXi host.
            username: Username for connecting to the ESXi host.
            password: Password for connecting to the ESXi host.
            ssl_thumbprint: SSL thumbprint of the host (optional, for certificate verification).
            force: If True, force the addition even if the host is managed elsewhere.
        """
        logger.info("add_standalone_host", datacenter_name=datacenter_name, host_name=host_name)
        dc_items = collect_properties(client, vim.Datacenter, ["name", "hostFolder"])
        datacenter_obj = None
        for item in dc_items:
            if item.get("name") == datacenter_name:
                datacenter_obj = item["_obj"]
                break
        if datacenter_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        host_folder = datacenter_obj.hostFolder
        spec = vim.host.ConnectSpec(
            hostName=host_name,
            userName=username,
            password=password,
            sslThumbprint=ssl_thumbprint or "",
            force=force,
        )
        task = host_folder.AddStandaloneHost_Task(spec=spec, addConnected=True)
        result = wait_for_task(task)
        result["datacenter_name"] = datacenter_name
        result["host_name"] = host_name
        result["operation"] = "add_standalone_host"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_host(host_name: str, new_name: str) -> dict[str, Any]:
        """Rename an ESXi host in vCenter inventory.

        Args:
            host_name: Current name of the host.
            new_name: New name for the host.
        """
        logger.info("rename_host", host_name=host_name, new_name=new_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        task = host_obj.Rename_Task(newName=new_name)
        result = wait_for_task(task)
        result["host_name"] = host_name
        result["new_name"] = new_name
        result["operation"] = "rename_host"
        return result
