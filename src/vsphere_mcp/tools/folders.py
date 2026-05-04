from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _build_folder_path(folder_obj: Any) -> str:
    """Walk parent chain to build a folder path string."""
    parts: list[str] = []
    current = folder_obj
    while current:
        if hasattr(current, "name"):
            parts.append(current.name)
        parent = getattr(current, "parent", None)
        if parent is None or isinstance(current, vim.Datacenter):
            break
        current = parent
    parts.reverse()
    return "/".join(parts)


def _find_folder_by_name(client: Any, folder_name: str) -> Any | None:
    """Find a folder by name and return its managed object."""
    items = collect_properties(client, vim.Folder, ["name"])
    for item in items:
        if item.get("name") == folder_name:
            return item["_obj"]
    return None


def register_folder_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_folders() -> dict[str, Any]:
        """List all folders in the vSphere inventory with their types and paths."""
        logger.info("list_folders")
        items = collect_properties(client, vim.Folder, ["name", "childType"])
        folders = []
        for item in items:
            child_type = item.get("childType", [])
            type_names = [str(t) for t in child_type] if child_type else []
            path = _build_folder_path(item["_obj"])
            folders.append(
                {
                    "name": item.get("name"),
                    "child_type": type_names,
                    "path": path,
                }
            )
        return {"total": len(folders), "folders": folders}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_folder(parent_folder_name: str, folder_name: str) -> dict[str, Any]:
        """Create a new folder under the specified parent folder."""
        logger.info("create_folder", parent_folder_name=parent_folder_name, folder_name=folder_name)
        parent = _find_folder_by_name(client, parent_folder_name)
        if parent is None:
            return {"status": "error", "error": f"Parent folder '{parent_folder_name}' not found"}

        new_folder = parent.CreateFolder(folder_name)
        return {
            "status": "success",
            "folder_name": folder_name,
            "parent_folder": parent_folder_name,
            "operation": "create_folder",
            "path": _build_folder_path(new_folder),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def move_vm_to_folder(vm_name: str, folder_name: str) -> dict[str, Any]:
        """Move a VM into a specified folder."""
        logger.info("move_vm_to_folder", vm_name=vm_name, folder_name=folder_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        folder = _find_folder_by_name(client, folder_name)
        if folder is None:
            return {"status": "error", "error": f"Folder '{folder_name}' not found"}

        task = folder.MoveIntoFolder_Task([found["_obj"]])
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["folder_name"] = folder_name
        result["operation"] = "move_vm_to_folder"
        return result
