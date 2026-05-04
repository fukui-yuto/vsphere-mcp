from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.tools.power import _find_vm_with_props, _wait_for_task

logger = get_logger(__name__)


def _find_snapshot_by_name(snapshot_list: list[Any], name: str) -> vim.vm.Snapshot | None:
    for snap in snapshot_list:
        if snap.name == name:
            return snap.snapshot
        if snap.childSnapshotList:
            found = _find_snapshot_by_name(snap.childSnapshotList, name)
            if found:
                return found
    return None


def register_snapshot_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @require_confirm(danger_level="medium")
    @handle_tool_errors
    def create_snapshot(
        vm_name: str,
        name: str,
        description: str = "",
        memory: bool = False,
        quiesce: bool = False,
    ) -> dict[str, Any]:
        """Create a snapshot of a virtual machine."""
        logger.info("create_snapshot", vm_name=vm_name, snapshot_name=name)
        found = _find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        task = found["_obj"].CreateSnapshot(name=name, description=description, memory=memory, quiesce=quiesce)
        result = _wait_for_task(task)
        result["vm_name"] = vm_name
        result["snapshot_name"] = name
        result["operation"] = "create_snapshot"
        return result

    @mcp.tool()
    @require_confirm(danger_level="high")
    @handle_tool_errors
    def revert_snapshot(vm_name: str, snapshot_name: str) -> dict[str, Any]:
        """Revert a virtual machine to a named snapshot."""
        logger.info("revert_snapshot", vm_name=vm_name, snapshot_name=snapshot_name)
        found = _find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
            return {"status": "error", "error": f"No snapshots found for VM '{vm_name}'"}
        snap = _find_snapshot_by_name(snap_info.rootSnapshotList, snapshot_name)
        if snap is None:
            return {
                "status": "error",
                "error": f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'",
            }
        task = snap.RevertToSnapshot_Task()
        result = _wait_for_task(task)
        result["vm_name"] = vm_name
        result["snapshot_name"] = snapshot_name
        result["operation"] = "revert_snapshot"
        return result

    @mcp.tool()
    @require_confirm(danger_level="high")
    @handle_tool_errors
    def remove_snapshot(
        vm_name: str,
        snapshot_name: str,
        remove_children: bool = False,
    ) -> dict[str, Any]:
        """Remove a snapshot from a virtual machine."""
        logger.info("remove_snapshot", vm_name=vm_name, snapshot_name=snapshot_name)
        found = _find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
            return {"status": "error", "error": f"No snapshots found for VM '{vm_name}'"}
        snap = _find_snapshot_by_name(snap_info.rootSnapshotList, snapshot_name)
        if snap is None:
            return {
                "status": "error",
                "error": f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'",
            }
        task = snap.RemoveSnapshot_Task(removeChildren=remove_children)
        result = _wait_for_task(task)
        result["vm_name"] = vm_name
        result["snapshot_name"] = snapshot_name
        result["operation"] = "remove_snapshot"
        return result
