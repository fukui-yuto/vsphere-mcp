from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_vapp_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_vapps() -> dict[str, Any]:
        """List all vApps in the vCenter inventory."""
        logger.info("list_vapps")
        items = collect_properties(client, vim.VirtualApp, ["name", "vAppConfig", "summary"])
        vapps: list[dict[str, Any]] = []
        for item in items:
            vapp_config = item.get("vAppConfig")
            summary = item.get("summary")
            entry: dict[str, Any] = {
                "name": item.get("name"),
            }
            if vapp_config is not None:
                entry["product"] = (
                    vapp_config.product[0].name
                    if vapp_config.product
                    else None
                )
                entry["annotation"] = vapp_config.annotation if hasattr(vapp_config, "annotation") else None
            if summary is not None:
                entry["overall_status"] = str(summary.overallStatus) if hasattr(summary, "overallStatus") else None
                entry["num_cpu"] = summary.config.numCpu if hasattr(summary, "config") and summary.config else None
                entry["memory_mb"] = summary.config.memorySizeMB if hasattr(summary, "config") and summary.config else None
            vapps.append(entry)
        return {"total": len(vapps), "vapps": vapps}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def power_on_vapp(vapp_name: str) -> dict[str, Any]:
        """Power on a vApp.

        Args:
            vapp_name: Name of the vApp to power on.
        """
        logger.info("power_on_vapp", vapp_name=vapp_name)
        items = collect_properties(client, vim.VirtualApp, ["name"])
        vapp_obj = None
        for item in items:
            if item.get("name") == vapp_name:
                vapp_obj = item["_obj"]
                break
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}
        task = vapp_obj.PowerOnVApp_Task()
        result = wait_for_task(task)
        result["vapp_name"] = vapp_name
        result["operation"] = "power_on_vapp"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def power_off_vapp(vapp_name: str, force: bool = False) -> dict[str, Any]:
        """Power off a vApp.

        Args:
            vapp_name: Name of the vApp to power off.
            force: If True, force power off without graceful shutdown.
        """
        logger.info("power_off_vapp", vapp_name=vapp_name, force=force)
        items = collect_properties(client, vim.VirtualApp, ["name"])
        vapp_obj = None
        for item in items:
            if item.get("name") == vapp_name:
                vapp_obj = item["_obj"]
                break
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}
        task = vapp_obj.PowerOffVApp_Task(force=force)
        result = wait_for_task(task)
        result["vapp_name"] = vapp_name
        result["force"] = force
        result["operation"] = "power_off_vapp"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_vapp(vapp_name: str) -> dict[str, Any]:
        """Permanently delete a vApp and all its contents.

        Args:
            vapp_name: Name of the vApp to delete.
        """
        logger.info("delete_vapp", vapp_name=vapp_name)
        items = collect_properties(client, vim.VirtualApp, ["name"])
        vapp_obj = None
        for item in items:
            if item.get("name") == vapp_name:
                vapp_obj = item["_obj"]
                break
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}
        task = vapp_obj.Destroy_Task()
        result = wait_for_task(task)
        result["vapp_name"] = vapp_name
        result["operation"] = "delete_vapp"
        return result
