from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_datastore(client: VSphereClient, ds_name: str) -> Any | None:
    items = collect_properties(client, vim.Datastore, ["name"])
    for item in items:
        if item.get("name") == ds_name:
            return item["_obj"]
    return None


def _get_vsom(client: VSphereClient) -> Any:
    """Get vStorageObjectManager from content."""
    return client.content.vStorageObjectManager


def register_fcd_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_fcd(
        datastore_name: str,
        name: str,
        size_mb: int,
        keep_after_delete_vm: bool = True,
    ) -> dict[str, Any]:
        """Create a First Class Disk (FCD / Improved Virtual Disk) on a datastore.

        FCDs are independent virtual disks managed by vCenter independently of any VM.
        They can be attached to VMs, snapshotted, and cloned without a VM lifecycle dependency.

        Args:
            datastore_name: Name of the datastore on which to create the FCD.
            name: Display name for the new FCD.
            size_mb: Size of the FCD in megabytes.
            keep_after_delete_vm: If True, the disk persists when an attached VM is deleted (default True).
        """
        logger.info("create_fcd", datastore_name=datastore_name, name=name, size_mb=size_mb)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        backing_spec = vim.vslm.CreateSpec.DiskFileBackingSpec(
            datastore=ds_obj,
            provisioningType="thin",
        )
        spec = vim.vslm.CreateSpec(
            name=name,
            capacityInMB=size_mb,
            backingSpec=backing_spec,
            keepAfterDeleteVm=keep_after_delete_vm,
        )

        task = vsom.CreateDisk_Task(spec=spec)
        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to create FCD")}

        fcd_obj = getattr(task.info, "result", None)
        fcd_id = None
        if fcd_obj is not None:
            fcd_id = getattr(getattr(fcd_obj, "config", None), "id", None)
            if fcd_id is not None:
                fcd_id = getattr(fcd_id, "id", str(fcd_id))

        return {
            "status": "success",
            "operation": "create_fcd",
            "name": name,
            "datastore_name": datastore_name,
            "size_mb": size_mb,
            "fcd_id": fcd_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_fcd(datastore_name: str, fcd_id: str) -> dict[str, Any]:
        """Delete a First Class Disk (FCD) permanently from a datastore.

        This operation is irreversible. The FCD must not be attached to any VM
        before deletion.

        Args:
            datastore_name: Name of the datastore hosting the FCD.
            fcd_id: The FCD UUID/ID string.
        """
        logger.info("delete_fcd", datastore_name=datastore_name, fcd_id=fcd_id)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        task = vsom.DeleteVStorageObject_Task(id=fcd_id_obj, datastore=ds_obj)
        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to delete FCD")}

        return {
            "status": "success",
            "operation": "delete_fcd",
            "fcd_id": fcd_id,
            "datastore_name": datastore_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_fcds(datastore_name: str) -> dict[str, Any]:
        """List all First Class Disks (FCDs) on a datastore.

        Returns basic metadata for each FCD including its ID, name, and capacity.

        Args:
            datastore_name: Name of the datastore to list FCDs from.
        """
        logger.info("list_fcds", datastore_name=datastore_name)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        try:
            id_list = vsom.ListVStorageObject(datastore=ds_obj) or []
        except Exception as exc:
            return {"status": "error", "error": f"Failed to list FCDs: {exc}"}

        fcds = []
        for fcd_id_obj in id_list:
            try:
                fcd_obj = vsom.RetrieveVStorageObject(id=fcd_id_obj, datastore=ds_obj)
                config = getattr(fcd_obj, "config", None)
                name = getattr(config, "name", None) if config else None
                capacity = getattr(config, "capacityInMB", None) if config else None
                obj_id = getattr(getattr(config, "id", None), "id", None) if config else None
                fcds.append({
                    "fcd_id": obj_id or str(fcd_id_obj),
                    "name": name,
                    "capacity_mb": capacity,
                })
            except Exception as exc:
                fcds.append({"fcd_id": str(fcd_id_obj), "error": str(exc)})

        return {
            "status": "success",
            "datastore_name": datastore_name,
            "fcd_count": len(fcds),
            "fcds": fcds,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_fcd_info(datastore_name: str, fcd_id: str) -> dict[str, Any]:
        """Get detailed metadata for a specific First Class Disk (FCD).

        Returns the FCD configuration including name, capacity, backing type,
        and creation time if available.

        Args:
            datastore_name: Name of the datastore hosting the FCD.
            fcd_id: The FCD UUID/ID string.
        """
        logger.info("get_fcd_info", datastore_name=datastore_name, fcd_id=fcd_id)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        try:
            fcd_obj = vsom.RetrieveVStorageObject(id=fcd_id_obj, datastore=ds_obj)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to retrieve FCD: {exc}"}

        config = getattr(fcd_obj, "config", None)
        if config is None:
            return {"status": "error", "error": "FCD config not available"}

        backing = getattr(config, "backing", None)
        backing_info: dict[str, Any] = {}
        if backing is not None:
            backing_info = {
                "type": type(backing).__name__,
                "file_path": getattr(backing, "filePath", None),
                "provisioning_type": getattr(backing, "provisioningType", None),
                "datastore": getattr(getattr(backing, "datastore", None), "name", None),
            }

        return {
            "status": "success",
            "fcd_id": fcd_id,
            "datastore_name": datastore_name,
            "name": getattr(config, "name", None),
            "capacity_mb": getattr(config, "capacityInMB", None),
            "keep_after_delete_vm": getattr(config, "keepAfterDeleteVm", None),
            "create_time": str(ct) if (ct := getattr(config, "createTime", None)) is not None else None,
            "backing": backing_info,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def clone_fcd(
        datastore_name: str,
        fcd_id: str,
        new_name: str,
        dest_datastore_name: str = "",
    ) -> dict[str, Any]:
        """Clone a First Class Disk (FCD) to create a new independent copy.

        The clone can be placed on the same datastore or a different one.

        Args:
            datastore_name: Name of the source datastore.
            fcd_id: The source FCD UUID/ID string.
            new_name: Name for the cloned FCD.
            dest_datastore_name: Destination datastore name. Uses source datastore if empty.
        """
        logger.info("clone_fcd", datastore_name=datastore_name, fcd_id=fcd_id, new_name=new_name)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        if dest_datastore_name:
            dest_ds_obj = _find_datastore(client, dest_datastore_name)
            if dest_ds_obj is None:
                return {"status": "error", "error": f"Destination datastore '{dest_datastore_name}' not found"}
        else:
            dest_ds_obj = ds_obj
            dest_datastore_name = datastore_name

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        backing_spec = vim.vslm.CloneSpec.DiskFileBackingSpec(
            datastore=dest_ds_obj,
        )
        spec = vim.vslm.CloneSpec(
            name=new_name,
            backingSpec=backing_spec,
        )

        try:
            task = vsom.CloneVStorageObject_Task(id=fcd_id_obj, datastore=ds_obj, spec=spec)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initiate FCD clone: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to clone FCD")}

        clone_obj = getattr(task.info, "result", None)
        clone_id = None
        if clone_obj is not None:
            clone_id = getattr(getattr(clone_obj, "config", None), "id", None)
            if clone_id is not None:
                clone_id = getattr(clone_id, "id", str(clone_id))

        return {
            "status": "success",
            "operation": "clone_fcd",
            "source_fcd_id": fcd_id,
            "new_name": new_name,
            "dest_datastore_name": dest_datastore_name,
            "clone_fcd_id": clone_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def relocate_fcd(
        datastore_name: str,
        fcd_id: str,
        dest_datastore_name: str,
    ) -> dict[str, Any]:
        """Relocate a First Class Disk (FCD) to a different datastore (Storage vMotion for FCDs).

        The FCD is moved while preserving its ID. Any VMs with the FCD attached
        will continue to use it after relocation.

        Args:
            datastore_name: Name of the current (source) datastore.
            fcd_id: The FCD UUID/ID string.
            dest_datastore_name: Name of the destination datastore.
        """
        logger.info("relocate_fcd", datastore_name=datastore_name, fcd_id=fcd_id, dest_datastore_name=dest_datastore_name)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        dest_ds_obj = _find_datastore(client, dest_datastore_name)
        if dest_ds_obj is None:
            return {"status": "error", "error": f"Destination datastore '{dest_datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        backing_spec = vim.vslm.RelocateSpec.DiskFileBackingSpec(
            datastore=dest_ds_obj,
        )
        spec = vim.vslm.RelocateSpec(backingSpec=backing_spec)

        try:
            task = vsom.RelocateVStorageObject_Task(id=fcd_id_obj, datastore=ds_obj, spec=spec)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initiate FCD relocation: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to relocate FCD")}

        return {
            "status": "success",
            "operation": "relocate_fcd",
            "fcd_id": fcd_id,
            "source_datastore": datastore_name,
            "dest_datastore": dest_datastore_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_fcd_snapshot(
        datastore_name: str,
        fcd_id: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a point-in-time snapshot of a First Class Disk (FCD).

        FCD snapshots are independent of VM snapshots and track the disk state
        at a specific point in time.

        Args:
            datastore_name: Name of the datastore hosting the FCD.
            fcd_id: The FCD UUID/ID string.
            description: Optional description for the snapshot.
        """
        logger.info("create_fcd_snapshot", datastore_name=datastore_name, fcd_id=fcd_id)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        try:
            task = vsom.VStorageObjectCreateSnapshot_Task(
                id=fcd_id_obj,
                datastore=ds_obj,
                description=description,
            )
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initiate FCD snapshot: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to create FCD snapshot")}

        snap_result = getattr(task.info, "result", None)
        snap_id = None
        if snap_result is not None:
            snap_id = getattr(snap_result, "id", str(snap_result))

        return {
            "status": "success",
            "operation": "create_fcd_snapshot",
            "fcd_id": fcd_id,
            "datastore_name": datastore_name,
            "description": description,
            "snapshot_id": snap_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def delete_fcd_snapshot(
        datastore_name: str,
        fcd_id: str,
        snapshot_id: str,
    ) -> dict[str, Any]:
        """Delete a snapshot of a First Class Disk (FCD).

        Args:
            datastore_name: Name of the datastore hosting the FCD.
            fcd_id: The FCD UUID/ID string.
            snapshot_id: The snapshot ID to delete.
        """
        logger.info("delete_fcd_snapshot", datastore_name=datastore_name, fcd_id=fcd_id, snapshot_id=snapshot_id)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        snap_id_obj = vim.vslm.ID(id=snapshot_id)
        try:
            task = vsom.DeleteSnapshot_Task(
                id=fcd_id_obj,
                datastore=ds_obj,
                snapshotId=snap_id_obj,
            )
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initiate FCD snapshot deletion: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to delete FCD snapshot")}

        return {
            "status": "success",
            "operation": "delete_fcd_snapshot",
            "fcd_id": fcd_id,
            "datastore_name": datastore_name,
            "snapshot_id": snapshot_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_fcd_snapshots(datastore_name: str, fcd_id: str) -> dict[str, Any]:
        """Get snapshot information for a First Class Disk (FCD).

        Returns all snapshots associated with the FCD, including their IDs,
        descriptions, and creation times.

        Args:
            datastore_name: Name of the datastore hosting the FCD.
            fcd_id: The FCD UUID/ID string.
        """
        logger.info("get_fcd_snapshots", datastore_name=datastore_name, fcd_id=fcd_id)

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        vsom = _get_vsom(client)
        if vsom is None:
            return {"status": "error", "error": "vStorageObjectManager not available on this vCenter"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)
        try:
            snap_info = vsom.RetrieveSnapshotInfo(id=fcd_id_obj, datastore=ds_obj)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to retrieve FCD snapshot info: {exc}"}

        snapshots = []
        for snap in getattr(snap_info, "snapshots", None) or []:
            snap_id_val = getattr(snap, "id", None)
            snapshots.append({
                "snapshot_id": getattr(snap_id_val, "id", str(snap_id_val)) if snap_id_val else None,
                "description": getattr(snap, "description", None),
                "create_time": str(ct) if (ct := getattr(snap, "createTime", None)) is not None else None,
            })

        return {
            "status": "success",
            "fcd_id": fcd_id,
            "datastore_name": datastore_name,
            "snapshot_count": len(snapshots),
            "snapshots": snapshots,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def attach_detach_fcd(
        vm_name: str,
        datastore_name: str,
        fcd_id: str,
        action: str = "attach",
        controller_key: int = -1,
        unit_number: int = -1,
    ) -> dict[str, Any]:
        """Attach or detach a First Class Disk (FCD) to/from a VM.

        When attaching, the FCD is added as a virtual disk to the VM. When detaching,
        it is removed from the VM but the disk data is preserved.

        Args:
            vm_name: Name of the target VM.
            datastore_name: Name of the datastore hosting the FCD.
            fcd_id: The FCD UUID/ID string.
            action: Either "attach" or "detach" (default "attach").
            controller_key: SCSI controller key for attach. Use -1 to auto-select (default -1).
            unit_number: Unit number on the controller for attach. Use -1 to auto-select (default -1).
        """
        logger.info("attach_detach_fcd", vm_name=vm_name, fcd_id=fcd_id, action=action)

        if action not in ("attach", "detach"):
            return {"status": "error", "error": "action must be 'attach' or 'detach'"}

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = found["_obj"]

        ds_obj = _find_datastore(client, datastore_name)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        fcd_id_obj = vim.vslm.ID(id=fcd_id)

        if action == "attach":
            kwargs: dict[str, Any] = {"diskId": fcd_id_obj, "datastore": ds_obj}
            if controller_key >= 0:
                kwargs["controllerKey"] = controller_key
            if unit_number >= 0:
                kwargs["unitNumber"] = unit_number
            try:
                task = vm_obj.AttachDisk_Task(**kwargs)
            except Exception as exc:
                return {"status": "error", "error": f"Failed to initiate FCD attach: {exc}"}
        else:
            try:
                task = vm_obj.DetachDisk_Task(diskId=fcd_id_obj)
            except Exception as exc:
                return {"status": "error", "error": f"Failed to initiate FCD detach: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", f"Failed to {action} FCD")}

        return {
            "status": "success",
            "operation": f"{action}_fcd",
            "vm_name": vm_name,
            "fcd_id": fcd_id,
            "datastore_name": datastore_name,
        }
