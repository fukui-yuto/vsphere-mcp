from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_dvs(client: VSphereClient, dvs_name: str) -> tuple[Any, Any] | tuple[None, None]:
    """Find a DVS by name. Returns (dvs_obj, config) or (None, None)."""
    items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
    for item in items:
        if item.get("name") == dvs_name:
            return item["_obj"], item.get("config")
    return None, None


def register_nioc_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_dvs_nioc_config(dvs_name: str) -> dict[str, Any]:
        """Get Network I/O Control (NIOC) configuration on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the Distributed Virtual Switch.
        """
        logger.info("get_dvs_nioc_config", dvs_name=dvs_name)

        dvs_obj, dvs_config = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        nioc_enabled = getattr(dvs_obj, "networkResourceManagementEnabled", None)

        traffic_configs: list[dict[str, Any]] = []
        if dvs_config is not None:
            for tc in getattr(dvs_config, "infrastructureTrafficResourceConfig", None) or []:
                alloc = getattr(tc, "allocationInfo", None)
                shares_info = None
                if alloc is not None:
                    shares = getattr(alloc, "shares", None)
                    shares_info = {
                        "level": getattr(shares, "level", None),
                        "shares": getattr(shares, "shares", None),
                    } if shares is not None else None
                traffic_configs.append({
                    "key": getattr(tc, "key", None),
                    "allocationInfo": {
                        "limit": getattr(alloc, "limit", None),
                        "reservation": getattr(alloc, "reservation", None),
                        "shares": shares_info,
                    } if alloc is not None else None,
                })

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "networkResourceManagementEnabled": nioc_enabled,
            "infrastructureTrafficResourceConfig": traffic_configs,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enable_disable_dvs_nioc(dvs_name: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable Network I/O Control (NIOC) on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the Distributed Virtual Switch.
            enabled: True to enable NIOC, False to disable it.
        """
        logger.info("enable_disable_dvs_nioc", dvs_name=dvs_name, enabled=enabled)

        dvs_obj, _ = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        dvs_obj.EnableNetworkResourceManagement(enable=enabled)

        return {
            "status": "success",
            "operation": "enable_disable_dvs_nioc",
            "dvs_name": dvs_name,
            "enabled": enabled,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_dvs_nioc_resource_pools(dvs_name: str) -> dict[str, Any]:
        """List Network I/O Control resource pools on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the Distributed Virtual Switch.
        """
        logger.info("list_dvs_nioc_resource_pools", dvs_name=dvs_name)

        dvs_obj, dvs_config = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        pools: list[dict[str, Any]] = []
        for tc in getattr(dvs_config, "infrastructureTrafficResourceConfig", None) or []:
            alloc = getattr(tc, "allocationInfo", None)
            shares = getattr(alloc, "shares", None) if alloc is not None else None
            pools.append({
                "key": getattr(tc, "key", None),
                "allocationInfo": {
                    "limit": getattr(alloc, "limit", None),
                    "reservation": getattr(alloc, "reservation", None),
                    "shares": {
                        "level": getattr(shares, "level", None),
                        "shares": getattr(shares, "shares", None),
                    } if shares is not None else None,
                } if alloc is not None else None,
            })

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "total": len(pools),
            "resource_pools": pools,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_dvs_nioc_resource_pool(
        dvs_name: str,
        resource_key: str,
        shares_level: str = "normal",
        shares_value: int | None = None,
        limit: int = -1,
        reservation: int = 0,
    ) -> dict[str, Any]:
        """Configure a Network I/O Control resource pool on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the Distributed Virtual Switch.
            resource_key: Traffic resource key, e.g. "management", "vmotion", "vsan",
                "virtualMachine", "nfs", "iscsi", "hbr", "vdp", "backupNfc".
            shares_level: Shares allocation level: "low", "normal", "high", or "custom".
            shares_value: Custom shares value (only used when shares_level is "custom").
            limit: Maximum bandwidth in Mbps (-1 for unlimited, default -1).
            reservation: Reserved bandwidth in Mbps (default 0).
        """
        logger.info(
            "configure_dvs_nioc_resource_pool",
            dvs_name=dvs_name,
            resource_key=resource_key,
            shares_level=shares_level,
            limit=limit,
            reservation=reservation,
        )

        valid_levels = ("low", "normal", "high", "custom")
        if shares_level not in valid_levels:
            return {"status": "error", "error": f"shares_level must be one of: {', '.join(valid_levels)}"}

        dvs_obj, dvs_config = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        shares_info = vim.SharesInfo(level=shares_level)
        if shares_level == "custom" and shares_value is not None:
            shares_info.shares = shares_value

        alloc_info = vim.dvs.NetworkResourcePool.AllocationInfo(
            limit=limit,
            reservation=reservation,
            shares=shares_info,
        )
        resource_pool_config = vim.dvs.NetworkResourcePool.ConfigSpec(
            key=resource_key,
            allocationInfo=alloc_info,
        )

        dvs_obj.UpdateNetworkResourcePool(configSpec=[resource_pool_config])

        return {
            "status": "success",
            "operation": "configure_dvs_nioc_resource_pool",
            "dvs_name": dvs_name,
            "resource_key": resource_key,
            "shares_level": shares_level,
            "shares_value": shares_value,
            "limit": limit,
            "reservation": reservation,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_nioc_network_allocation(
        vm_name: str,
        nic_label: str,
        reservation: int = 0,
        limit: int = -1,
        shares_level: str = "normal",
    ) -> dict[str, Any]:
        """Set per-VM NIC bandwidth allocation for Network I/O Control.

        Args:
            vm_name: Name of the VM.
            nic_label: Device label of the network adapter (e.g. "Network adapter 1").
            reservation: Reserved bandwidth in Mbps (default 0).
            limit: Maximum bandwidth in Mbps (-1 for unlimited, default -1).
            shares_level: Shares allocation level: "low", "normal", "high", or "custom".
        """
        logger.info(
            "set_vm_nioc_network_allocation",
            vm_name=vm_name,
            nic_label=nic_label,
            reservation=reservation,
            limit=limit,
            shares_level=shares_level,
        )

        valid_levels = ("low", "normal", "high", "custom")
        if shares_level not in valid_levels:
            return {"status": "error", "error": f"shares_level must be one of: {', '.join(valid_levels)}"}

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        nic_device = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                label = getattr(getattr(dev, "deviceInfo", None), "label", None)
                if label == nic_label:
                    nic_device = dev
                    break

        if nic_device is None:
            return {
                "status": "error",
                "error": f"NIC with label '{nic_label}' not found on VM '{vm_name}'",
            }

        shares_info = vim.SharesInfo(level=shares_level)
        resource_alloc = vim.ResourceAllocationInfo(
            reservation=reservation,
            limit=limit,
            shares=shares_info,
        )
        nic_device.resourceAllocation = resource_alloc

        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=nic_device,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to set NIC bandwidth allocation")}

        return {
            "status": "success",
            "operation": "set_vm_nioc_network_allocation",
            "vm_name": vm_name,
            "nic_label": nic_label,
            "reservation": reservation,
            "limit": limit,
            "shares_level": shares_level,
        }
