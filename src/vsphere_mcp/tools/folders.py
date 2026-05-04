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
    max_depth = 50
    depth = 0
    while current and depth < max_depth:
        if hasattr(current, "name"):
            parts.append(current.name)
        parent = getattr(current, "parent", None)
        if parent is None or isinstance(current, vim.Datacenter):
            break
        current = parent
        depth += 1
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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_folder(folder_name: str, folder_type: str = "vm", force: bool = False) -> dict[str, Any]:
        """Delete a folder from the vSphere inventory. This operation is irreversible.

        If the folder contains child entities, deletion will be refused unless force=True.
        """
        logger.info("delete_folder", folder_name=folder_name, folder_type=folder_type, force=force)
        items = collect_properties(client, vim.Folder, ["name", "childType"])
        folder_obj = None
        for item in items:
            if item.get("name") != folder_name:
                continue
            child_types = [str(t) for t in (item.get("childType") or [])]
            type_match = {
                "vm": "VirtualMachine",
                "host": "ComputeResource",
                "network": "Network",
                "datastore": "Datastore",
            }
            expected = type_match.get(folder_type, folder_type)
            if any(expected in ct for ct in child_types) or folder_type == "any":
                folder_obj = item["_obj"]
                break
        if folder_obj is None:
            return {"status": "error", "error": f"Folder '{folder_name}' of type '{folder_type}' not found"}

        child_entities = getattr(folder_obj, "childEntity", []) or []
        if child_entities and not force:
            return {
                "status": "error",
                "error": (
                    f"Folder '{folder_name}' is not empty (contains {len(child_entities)} child entities). "
                    "Set force=True to delete a non-empty folder."
                ),
            }

        task = folder_obj.Destroy_Task()
        result = wait_for_task(task)
        result["folder_name"] = folder_name
        result["folder_type"] = folder_type
        result["operation"] = "delete_folder"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_folder(folder_name: str, new_name: str, folder_type: str = "vm") -> dict[str, Any]:
        """Rename a folder in the vSphere inventory."""
        logger.info("rename_folder", folder_name=folder_name, new_name=new_name, folder_type=folder_type)
        items = collect_properties(client, vim.Folder, ["name", "childType"])
        folder_obj = None
        for item in items:
            if item.get("name") != folder_name:
                continue
            child_types = [str(t) for t in (item.get("childType") or [])]
            type_match = {
                "vm": "VirtualMachine",
                "host": "ComputeResource",
                "network": "Network",
                "datastore": "Datastore",
            }
            expected = type_match.get(folder_type, folder_type)
            if any(expected in ct for ct in child_types) or folder_type == "any":
                folder_obj = item["_obj"]
                break
        if folder_obj is None:
            return {"status": "error", "error": f"Folder '{folder_name}' of type '{folder_type}' not found"}
        task = folder_obj.Rename_Task(newName=new_name)
        result = wait_for_task(task)
        result["folder_name"] = folder_name
        result["new_name"] = new_name
        result["folder_type"] = folder_type
        result["operation"] = "rename_folder"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def move_entity_to_folder(
        entity_type: str,
        entity_name: str,
        folder_name: str,
        folder_type: str = "vm",
    ) -> dict[str, Any]:
        """Move a vSphere entity (vm, host, datastore, network) into a target folder."""
        logger.info(
            "move_entity_to_folder",
            entity_type=entity_type,
            entity_name=entity_name,
            folder_name=folder_name,
        )
        from vsphere_mcp.utils.property_collector import collect_properties as _cp

        type_map: dict[str, Any] = {
            "vm": vim.VirtualMachine,
            "host": vim.HostSystem,
            "datastore": vim.Datastore,
            "network": vim.Network,
            "cluster": vim.ClusterComputeResource,
        }
        vim_type = type_map.get(entity_type)
        if vim_type is None:
            return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}

        entity_items = _cp(client, vim_type, ["name"])
        entity_obj = None
        for item in entity_items:
            if item.get("name") == entity_name:
                entity_obj = item["_obj"]
                break
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        folder_items = collect_properties(client, vim.Folder, ["name", "childType"])
        folder_obj = None
        for item in folder_items:
            if item.get("name") != folder_name:
                continue
            child_types = [str(t) for t in (item.get("childType") or [])]
            folder_type_map = {
                "vm": "VirtualMachine",
                "host": "ComputeResource",
                "network": "Network",
                "datastore": "Datastore",
            }
            expected = folder_type_map.get(folder_type, folder_type)
            if any(expected in ct for ct in child_types) or folder_type == "any":
                folder_obj = item["_obj"]
                break
        if folder_obj is None:
            return {"status": "error", "error": f"Folder '{folder_name}' of type '{folder_type}' not found"}

        task = folder_obj.MoveIntoFolder_Task(list=[entity_obj])
        result = wait_for_task(task)
        result["entity_type"] = entity_type
        result["entity_name"] = entity_name
        result["folder_name"] = folder_name
        result["operation"] = "move_entity_to_folder"
        return result
