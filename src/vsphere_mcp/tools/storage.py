from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors
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
