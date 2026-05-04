from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

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
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_snapshot(
        vm_name: str,
        name: str,
        description: str = "",
        memory: bool = False,
        quiesce: bool = False,
    ) -> dict[str, Any]:
        """Create a snapshot of a virtual machine."""
        logger.info("create_snapshot", vm_name=vm_name, snapshot_name=name)
        found = find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        quiesce_warning = None
        if quiesce and memory:
            quiesce_warning = (
                "quiesce is ignored when memory=True; "
                "the snapshot will include memory but the guest filesystem will not be quiesced"
            )
            logger.warning("create_snapshot: quiesce ignored because memory=True", vm_name=vm_name)
        task = found["_obj"].CreateSnapshot(name=name, description=description, memory=memory, quiesce=quiesce)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["snapshot_name"] = name
        result["operation"] = "create_snapshot"
        if quiesce_warning:
            result["warning"] = quiesce_warning
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def revert_snapshot(
        vm_name: str, snapshot_name: str, suppress_power_on: bool = False
    ) -> dict[str, Any]:
        """Revert a virtual machine to a named snapshot."""
        logger.info("revert_snapshot", vm_name=vm_name, snapshot_name=snapshot_name)
        found = find_vm_with_props(client, vm_name, ["snapshot"])
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
        task = snap.RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["snapshot_name"] = snapshot_name
        result["operation"] = "revert_snapshot"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_snapshot(
        vm_name: str,
        snapshot_name: str,
        remove_children: bool = False,
        consolidate: bool = True,
    ) -> dict[str, Any]:
        """Remove a snapshot from a virtual machine."""
        logger.info("remove_snapshot", vm_name=vm_name, snapshot_name=snapshot_name)
        found = find_vm_with_props(client, vm_name, ["snapshot"])
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
        task = snap.RemoveSnapshot_Task(removeChildren=remove_children, consolidate=consolidate)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["snapshot_name"] = snapshot_name
        result["operation"] = "remove_snapshot"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_all_snapshots(vm_name: str) -> dict[str, Any]:
        """Remove all snapshots from a virtual machine at once.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("remove_all_snapshots", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
            return {"status": "error", "error": f"No snapshots found for VM '{vm_name}'"}
        task = found["_obj"].RemoveAllSnapshots_Task()
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "remove_all_snapshots"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_snapshot(
        vm_name: str,
        snapshot_name: str,
        new_name: str | None = None,
        new_description: str | None = None,
    ) -> dict[str, Any]:
        """Rename a snapshot and/or update its description.

        Args:
            vm_name: Name of the VM.
            snapshot_name: Current name of the snapshot.
            new_name: New name for the snapshot (optional).
            new_description: New description for the snapshot (optional).
        """
        logger.info("rename_snapshot", vm_name=vm_name, snapshot_name=snapshot_name)
        if not new_name and new_description is None:
            return {"status": "error", "error": "At least new_name or new_description must be specified"}
        found = find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
            return {"status": "error", "error": f"No snapshots found for VM '{vm_name}'"}
        snap = _find_snapshot_by_name(snap_info.rootSnapshotList, snapshot_name)
        if snap is None:
            return {"status": "error", "error": f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'"}
        snap.RenameSnapshot(name=new_name or snapshot_name, description=new_description)
        return {
            "status": "success",
            "vm_name": vm_name,
            "operation": "rename_snapshot",
            "old_name": snapshot_name,
            "new_name": new_name or snapshot_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def revert_to_current_snapshot(
        vm_name: str, suppress_power_on: bool = False
    ) -> dict[str, Any]:
        """Revert a VM to its current (most recent) snapshot.

        Args:
            vm_name: Name of the VM.
            suppress_power_on: If True, prevent the VM from powering on after revert.
        """
        logger.info("revert_to_current_snapshot", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "currentSnapshot"):
            return {"status": "error", "error": f"No current snapshot found for VM '{vm_name}'"}
        task = found["_obj"].RevertToCurrentSnapshot_Task(suppressPowerOn=suppress_power_on)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "revert_to_current_snapshot"
        return result
