from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)

DATASTORE_DETAIL_PROPS = [
    "name",
    "summary.type",
    "summary.capacity",
    "summary.freeSpace",
    "summary.accessible",
    "summary.maintenanceMode",
    "summary.url",
    "host",
    "vm",
]


def _format_datastore_detail(data: dict[str, Any]) -> dict[str, Any]:
    capacity = data.get("summary.capacity")
    free = data.get("summary.freeSpace")
    hosts = data.get("host", [])
    vms = data.get("vm", [])
    return {
        "name": data.get("name"),
        "type": data.get("summary.type"),
        "capacity_gb": round(capacity / (1024**3), 2) if capacity else 0,
        "free_gb": round(free / (1024**3), 2) if free else 0,
        "used_gb": round((capacity - free) / (1024**3), 2) if capacity and free else 0,
        "usage_percent": round((1 - free / capacity) * 100, 1) if capacity and free else 0,
        "accessible": data.get("summary.accessible"),
        "maintenance_mode": data.get("summary.maintenanceMode"),
        "url": data.get("summary.url"),
        "num_hosts": len(hosts) if hosts else 0,
        "num_vms": len(vms) if vms else 0,
    }


def register_storage_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_datastore_info(datastore_name: str) -> dict[str, Any]:
        """Get detailed information for a specific datastore including host and VM counts."""
        logger.info("get_datastore_info", datastore_name=datastore_name)
        items = collect_properties(client, vim.Datastore, DATASTORE_DETAIL_PROPS)
        for item in items:
            if item.get("name") == datastore_name:
                return _format_datastore_detail(item)
        return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

    @mcp.tool()
    @handle_tool_errors
    def get_storage_summary() -> dict[str, Any]:
        """Get overall storage summary across all datastores."""
        logger.info("get_storage_summary")
        items = collect_properties(client, vim.Datastore, DATASTORE_DETAIL_PROPS)
        datastores = [_format_datastore_detail(item) for item in items]

        total_capacity = sum(d["capacity_gb"] for d in datastores)
        total_free = sum(d["free_gb"] for d in datastores)
        total_used = sum(d["used_gb"] for d in datastores)

        return {
            "total_datastores": len(datastores),
            "total_capacity_gb": round(total_capacity, 2),
            "total_free_gb": round(total_free, 2),
            "total_used_gb": round(total_used, 2),
            "overall_usage_percent": (round((total_used / total_capacity) * 100, 1) if total_capacity else 0),
            "datastores": datastores,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_storage_devices(host_name: str) -> dict[str, Any]:
        """List SCSI LUNs and HBAs on an ESXi host."""
        logger.info("list_host_storage_devices", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}
        device_info = storage_system.storageDeviceInfo
        if device_info is None:
            return {"status": "error", "error": "storageDeviceInfo not available"}
        scsi_luns = []
        for lun in device_info.scsiLun or []:
            scsi_luns.append(
                {
                    "deviceName": lun.deviceName,
                    "displayName": lun.displayName,
                    "capacityInKB": lun.capacity.block * lun.capacity.blockSize // 1024 if lun.capacity else None,
                    "vendor": lun.vendor,
                    "model": lun.model,
                    "lunType": lun.lunType,
                }
            )
        hbas = []
        for hba in device_info.hostBusAdapter or []:
            hbas.append(
                {
                    "device": hba.device,
                    "model": hba.model,
                    "driver": hba.driver,
                    "status": hba.status,
                }
            )
        return {
            "status": "success",
            "host_name": host_name,
            "scsi_luns": scsi_luns,
            "host_bus_adapters": hbas,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_multipath_info(host_name: str) -> dict[str, Any]:
        """List multipath policies for LUNs on an ESXi host."""
        logger.info("list_host_multipath_info", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}
        device_info = storage_system.storageDeviceInfo
        if device_info is None:
            return {"status": "error", "error": "storageDeviceInfo not available"}
        multipath_info = device_info.multipathInfo
        if multipath_info is None:
            return {"status": "error", "error": "multipathInfo not available"}
        luns = []
        for lun in multipath_info.lun or []:
            policy_name = None
            if lun.policy:
                policy_name = lun.policy.policy
            luns.append(
                {
                    "lun_id": lun.id,
                    "policy": policy_name,
                    "path_count": len(lun.path) if lun.path else 0,
                }
            )
        return {
            "status": "success",
            "host_name": host_name,
            "multipath_luns": luns,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rescan_host_storage(host_name: str) -> dict[str, Any]:
        """Rescan all HBAs and VMFS on an ESXi host to discover new storage."""
        logger.info("rescan_host_storage", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}
        storage_system.RescanAllHba()
        storage_system.RescanVmfs()
        return {
            "status": "success",
            "host_name": host_name,
            "message": "HBA and VMFS rescan completed",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def mount_nfs_datastore(
        host_name: str,
        datastore_name: str,
        remote_host: str,
        remote_path: str,
        access_mode: str = "readWrite",
        nfs_type: str = "NFS",
    ) -> dict[str, Any]:
        """Mount an NFS datastore on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            datastore_name: Local name for the NFS datastore.
            remote_host: NFS server hostname or IP address.
            remote_path: Exported path on the NFS server.
            access_mode: Access mode: "readWrite" or "readOnly" (default "readWrite").
            nfs_type: NFS version type: "NFS" for v3 or "NFS41" for v4.1 (default "NFS").
        """
        valid_nfs_types = ("NFS", "NFS41")
        if nfs_type not in valid_nfs_types:
            return {"status": "error", "error": f"nfs_type must be one of: {', '.join(valid_nfs_types)}"}

        logger.info(
            "mount_nfs_datastore",
            host_name=host_name,
            datastore_name=datastore_name,
            remote_host=remote_host,
            remote_path=remote_path,
            access_mode=access_mode,
            nfs_type=nfs_type,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}

        spec = vim.host.NasVolume.Specification(
            remoteHost=remote_host,
            remotePath=remote_path,
            localPath=datastore_name,
            accessMode=access_mode,
            type=nfs_type,
        )
        storage_system.CreateNasDatastore(spec=spec)

        return {
            "status": "success",
            "operation": "mount_nfs_datastore",
            "host_name": host_name,
            "datastore_name": datastore_name,
            "remote_host": remote_host,
            "remote_path": remote_path,
            "access_mode": access_mode,
            "nfs_type": nfs_type,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def unmount_datastore(host_name: str, datastore_name: str) -> dict[str, Any]:
        """Unmount a datastore from an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            datastore_name: Name of the datastore to unmount.
        """
        logger.info("unmount_datastore", host_name=host_name, datastore_name=datastore_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}

        items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        ds_info = ds_obj.info
        if isinstance(ds_info, vim.host.VmfsDatastoreInfo):
            vmfs_uuid = ds_info.vmfs.uuid
            storage_system.UnmountVmfsVolume(vmfsUuid=vmfs_uuid)
            unmount_type = "VMFS"
        else:
            # NAS or other datastore types: use RemoveDatastore
            storage_system.RemoveDatastore(datastore=ds_obj)
            unmount_type = "NAS"

        return {
            "status": "success",
            "operation": "unmount_datastore",
            "host_name": host_name,
            "datastore_name": datastore_name,
            "unmount_type": unmount_type,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_datastore(datastore_name: str, new_name: str) -> dict[str, Any]:
        """Rename a datastore.

        Args:
            datastore_name: Current name of the datastore.
            new_name: New name for the datastore.
        """
        logger.info("rename_datastore", datastore_name=datastore_name, new_name=new_name)

        items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        task = ds_obj.Rename_Task(newName=new_name)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to rename datastore")}

        return {
            "status": "success",
            "operation": "rename_datastore",
            "old_name": datastore_name,
            "new_name": new_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def refresh_datastore(datastore_name: str) -> dict[str, Any]:
        """Refresh a datastore to update its storage information.

        Args:
            datastore_name: Name of the datastore to refresh.
        """
        logger.info("refresh_datastore", datastore_name=datastore_name)

        items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        ds_obj.RefreshDatastore()

        return {
            "status": "success",
            "operation": "refresh_datastore",
            "datastore_name": datastore_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enter_datastore_maintenance_mode(datastore_name: str) -> dict[str, Any]:
        """Put a datastore into maintenance mode.

        Args:
            datastore_name: Name of the datastore to enter maintenance mode.
        """
        logger.info("enter_datastore_maintenance_mode", datastore_name=datastore_name)

        items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        try:
            result = ds_obj.DatastoreEnterMaintenanceMode()
            # The API returns a StoragePlacementResult which may contain a task
            task = getattr(result, "task", None)
            if task is not None:
                task_result = wait_for_task(task)
                if task_result["status"] != "success":
                    return {
                        "status": "error",
                        "error": task_result.get("message", "Failed to enter datastore maintenance mode"),
                    }
        except Exception as e:
            return {"status": "error", "error": f"Failed to enter datastore maintenance mode: {e}"}

        return {
            "status": "success",
            "operation": "enter_datastore_maintenance_mode",
            "datastore_name": datastore_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def exit_datastore_maintenance_mode(datastore_name: str) -> dict[str, Any]:
        """Take a datastore out of maintenance mode.

        Args:
            datastore_name: Name of the datastore to exit maintenance mode.
        """
        logger.info("exit_datastore_maintenance_mode", datastore_name=datastore_name)

        items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        task = ds_obj.DatastoreExitMaintenanceMode_Task()
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to exit datastore maintenance mode")}

        return {
            "status": "success",
            "operation": "exit_datastore_maintenance_mode",
            "datastore_name": datastore_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_multipath_policy(
        host_name: str,
        lun_uuid: str,
        policy: str,
        preferred_path: str | None = None,
    ) -> dict[str, Any]:
        """Set the multipath policy for a LUN on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            lun_uuid: UUID of the LUN to configure.
            policy: Multipath policy: "rr" (Round Robin), "fixed" (Fixed), or "mru" (Most Recently Used).
            preferred_path: Preferred path name for the "fixed" policy (optional). Ignored for other policies.
        """
        logger.info("set_multipath_policy", host_name=host_name, lun_uuid=lun_uuid, policy=policy)

        policy_map = {
            "rr": "VMW_PSP_RR",
            "fixed": "VMW_PSP_FIXED",
            "mru": "VMW_PSP_MRU",
        }
        mapped_policy = policy_map.get(policy)
        if mapped_policy is None:
            return {"status": "error", "error": f"policy must be one of: {', '.join(policy_map.keys())}"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}

        try:
            if policy == "fixed":
                policy_obj = vim.host.MultipathInfo.FixedLogicalUnitPolicy(policy=mapped_policy)
                if preferred_path is not None:
                    policy_obj.prefer = preferred_path
            else:
                policy_obj = vim.host.MultipathInfo.LogicalUnitPolicy(policy=mapped_policy)
            storage_system.SetMultipathLunPolicy(lunId=lun_uuid, policy=policy_obj)
        except Exception as e:
            return {"status": "error", "error": f"Failed to set multipath policy: {e}"}

        return {
            "status": "success",
            "operation": "set_multipath_policy",
            "host_name": host_name,
            "lun_uuid": lun_uuid,
            "policy": policy,
            "mapped_policy": mapped_policy,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_datastore_hosts(datastore_name: str) -> dict[str, Any]:
        """List all ESXi hosts that have a datastore mounted.

        Args:
            datastore_name: Name of the datastore.
        """
        logger.info("list_datastore_hosts", datastore_name=datastore_name)

        items = collect_properties(client, vim.Datastore, ["name", "host"])
        for item in items:
            if item.get("name") == datastore_name:
                host_mounts = item.get("host", [])
                host_names = []
                for mount in host_mounts or []:
                    try:
                        host_names.append(mount.key.name)
                    except Exception:
                        host_names.append(str(mount.key))
                return {
                    "status": "success",
                    "datastore_name": datastore_name,
                    "hosts": host_names,
                    "num_hosts": len(host_names),
                }
        return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}
