from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm
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
