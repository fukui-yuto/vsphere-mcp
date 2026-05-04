from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_datacenter_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_datacenter(datacenter_name: str) -> dict[str, Any]:
        """Create a new datacenter in the root folder of the vCenter inventory."""
        logger.info("create_datacenter", datacenter_name=datacenter_name)
        root_folder = client.content.rootFolder
        root_folder.CreateDatacenter(name=datacenter_name)
        return {
            "status": "success",
            "operation": "create_datacenter",
            "datacenter_name": datacenter_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_datacenter(datacenter_name: str) -> dict[str, Any]:
        """Delete a datacenter and all objects within it permanently."""
        logger.info("delete_datacenter", datacenter_name=datacenter_name)
        datacenters = collect_properties(client, vim.Datacenter, ["name"])
        dc_obj = None
        for dc in datacenters:
            if dc.get("name") == datacenter_name:
                dc_obj = dc["_obj"]
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}
        task = dc_obj.Destroy_Task()
        result = wait_for_task(task)
        result["datacenter_name"] = datacenter_name
        result["operation"] = "delete_datacenter"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_datacenter(datacenter_name: str, new_name: str) -> dict[str, Any]:
        """Rename an existing datacenter.

        Args:
            datacenter_name: Current name of the datacenter.
            new_name: New name for the datacenter.
        """
        logger.info("rename_datacenter", datacenter_name=datacenter_name, new_name=new_name)
        datacenters = collect_properties(client, vim.Datacenter, ["name"])
        dc_obj = None
        for dc in datacenters:
            if dc.get("name") == datacenter_name:
                dc_obj = dc["_obj"]
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}
        task = dc_obj.Rename_Task(newName=new_name)
        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to rename datacenter")}
        return {
            "status": "success",
            "operation": "rename_datacenter",
            "old_name": datacenter_name,
            "new_name": new_name,
        }
