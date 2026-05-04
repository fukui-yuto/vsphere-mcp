from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _get_config_manager(host_obj: Any) -> Any | None:
    """Return host configManager or None."""
    cm = getattr(host_obj, "configManager", None)
    return cm


def register_networking_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_dvswitch_config(
        dvswitch_name: str,
    ) -> dict[str, Any]:
        """Get configuration details of a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch.
        """
        logger.info("get_dvswitch_config", dvswitch_name=dvswitch_name)

        items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
        dvs_obj = None
        dvs_config = None
        for item in items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                dvs_config = item.get("config")
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        result: dict[str, Any] = {
            "dvswitch_name": dvswitch_name,
        }

        if dvs_config:
            result["version"] = getattr(dvs_config, "productInfo", None) and dvs_config.productInfo.version
            result["maxMtu"] = getattr(dvs_config, "maxMtu", None)
            result["numPorts"] = getattr(dvs_config, "numPorts", None)

            uplink_names: list[str] = []
            if hasattr(dvs_config, "uplinkPortgroup") and dvs_config.uplinkPortgroup:
                for pg_ref in dvs_config.uplinkPortgroup:
                    try:
                        uplink_names.append(pg_ref.name)
                    except Exception:
                        uplink_names.append(str(pg_ref))
            result["uplinkPortgroups"] = uplink_names

            lacp_enabled = None
            if hasattr(dvs_config, "lacpGroupConfig") and dvs_config.lacpGroupConfig:
                lacp_enabled = True
            elif hasattr(dvs_config, "lacpApiVersion"):
                lacp_enabled = dvs_config.lacpApiVersion is not None
            result["lacpEnabled"] = lacp_enabled

            discovery = None
            if hasattr(dvs_config, "linkDiscoveryProtocolConfig") and dvs_config.linkDiscoveryProtocolConfig:
                ldp = dvs_config.linkDiscoveryProtocolConfig
                discovery = {
                    "protocol": getattr(ldp, "protocol", None),
                    "operation": getattr(ldp, "operation", None),
                }
            result["discoveryProtocol"] = discovery

        return result

    @mcp.tool()
    @handle_tool_errors
    def get_dvportgroup_config(
        portgroup_name: str,
    ) -> dict[str, Any]:
        """Get configuration of a Distributed Virtual Portgroup.

        Args:
            portgroup_name: Name of the DVS portgroup.
        """
        logger.info("get_dvportgroup_config", portgroup_name=portgroup_name)

        items = collect_properties(client, vim.dvs.DistributedVirtualPortgroup, ["name", "config"])
        pg_config = None
        found = False
        for item in items:
            if item.get("name") == portgroup_name:
                pg_config = item.get("config")
                found = True
                break
        if not found:
            return {"status": "error", "error": f"DVPortgroup '{portgroup_name}' not found"}

        result: dict[str, Any] = {
            "portgroup_name": portgroup_name,
        }

        if pg_config:
            result["numPorts"] = getattr(pg_config, "numPorts", None)
            result["type"] = getattr(pg_config, "type", None)

            default_port_config = getattr(pg_config, "defaultPortConfig", None)
            if default_port_config:
                vlan_info = None
                vlan = getattr(default_port_config, "vlan", None)
                if vlan:
                    if isinstance(vlan, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                        vlan_info = {"type": "VlanIdSpec", "vlanId": vlan.vlanId}
                    elif isinstance(vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                        ranges = []
                        for r in vlan.vlanId or []:
                            ranges.append({"start": r.start, "end": r.end})
                        vlan_info = {"type": "TrunkVlanSpec", "ranges": ranges}
                    else:
                        vlan_info = {"type": type(vlan).__name__}
                result["vlan"] = vlan_info

                security = getattr(default_port_config, "securityPolicy", None)
                if security:
                    result["securityPolicy"] = {
                        "allowPromiscuous": (
                            security.allowPromiscuous.value
                            if hasattr(security, "allowPromiscuous") and security.allowPromiscuous
                            else None
                        ),
                        "macChanges": (
                            security.macChanges.value
                            if hasattr(security, "macChanges") and security.macChanges
                            else None
                        ),
                        "forgedTransmits": (
                            security.forgedTransmits.value
                            if hasattr(security, "forgedTransmits") and security.forgedTransmits
                            else None
                        ),
                    }

                teaming = getattr(default_port_config, "uplinkTeamingPolicy", None)
                if teaming:
                    teaming_info: dict[str, Any] = {}
                    if hasattr(teaming, "policy") and teaming.policy:
                        teaming_info["policy"] = teaming.policy.value
                    if hasattr(teaming, "reversePolicy") and teaming.reversePolicy:
                        teaming_info["reversePolicy"] = teaming.reversePolicy.value
                    if hasattr(teaming, "notifySwitches") and teaming.notifySwitches:
                        teaming_info["notifySwitches"] = teaming.notifySwitches.value
                    if hasattr(teaming, "rollingOrder") and teaming.rollingOrder:
                        teaming_info["rollingOrder"] = teaming.rollingOrder.value
                    result["uplinkTeamingPolicy"] = teaming_info

        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_host_portgroup(
        host_name: str,
        portgroup_name: str,
        vswitch_name: str,
        vlan_id: int = 0,
    ) -> dict[str, Any]:
        """Add a standard portgroup to an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            portgroup_name: Name for the new portgroup.
            vswitch_name: Name of the vSwitch to attach to.
            vlan_id: VLAN ID (default 0 for no VLAN).
        """
        logger.info(
            "add_host_portgroup",
            host_name=host_name,
            portgroup_name=portgroup_name,
            vswitch_name=vswitch_name,
            vlan_id=vlan_id,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}

        spec = vim.host.PortGroup.Specification(
            name=portgroup_name,
            vswitchName=vswitch_name,
            vlanId=vlan_id,
            policy=vim.host.NetworkPolicy(),
        )
        net_system.AddPortGroup(portgrp=spec)

        return {
            "status": "success",
            "operation": "add_host_portgroup",
            "host_name": host_name,
            "portgroup_name": portgroup_name,
            "vswitch_name": vswitch_name,
            "vlan_id": vlan_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_host_portgroup(
        host_name: str,
        portgroup_name: str,
    ) -> dict[str, Any]:
        """Remove a standard portgroup from an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            portgroup_name: Name of the portgroup to remove.
        """
        logger.info(
            "remove_host_portgroup",
            host_name=host_name,
            portgroup_name=portgroup_name,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}

        net_system.RemovePortGroup(pgName=portgroup_name)

        return {
            "status": "success",
            "operation": "remove_host_portgroup",
            "host_name": host_name,
            "portgroup_name": portgroup_name,
        }
