from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
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
    def create_dvswitch(
        datacenter_name: str,
        dvswitch_name: str,
        num_uplinks: int = 4,
        max_mtu: int = 1500,
        version: str | None = None,
    ) -> dict[str, Any]:
        """Create a new Distributed Virtual Switch in a datacenter.

        Args:
            datacenter_name: Name of the datacenter to create the DVSwitch in.
            dvswitch_name: Name for the new DVSwitch.
            num_uplinks: Number of uplink ports (default 4).
            max_mtu: Maximum MTU size (default 1500, max 9000).
            version: DVS version (e.g. "7.0.0"). Uses server default if not specified.
        """
        logger.info(
            "create_dvswitch",
            datacenter_name=datacenter_name,
            dvswitch_name=dvswitch_name,
            num_uplinks=num_uplinks,
            max_mtu=max_mtu,
        )
        if max_mtu < 1500 or max_mtu > 9000:
            return {"status": "error", "error": "max_mtu must be between 1500 and 9000"}
        if num_uplinks < 1 or num_uplinks > 32:
            return {"status": "error", "error": "num_uplinks must be between 1 and 32"}

        dc_items = collect_properties(client, vim.Datacenter, ["name", "networkFolder"])
        dc_obj = None
        network_folder = None
        for item in dc_items:
            if item.get("name") == datacenter_name:
                dc_obj = item["_obj"]
                network_folder = item.get("networkFolder")
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}
        if network_folder is None:
            return {"status": "error", "error": "networkFolder not available on this datacenter"}

        uplink_names = [f"uplink{i + 1}" for i in range(num_uplinks)]
        uplink_policy = vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy(
            uplinkPortName=uplink_names,
        )

        dvs_create_spec = vim.DistributedVirtualSwitch.CreateSpec()
        dvs_config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            name=dvswitch_name,
            maxMtu=max_mtu,
            uplinkPortPolicy=uplink_policy,
        )
        if version:
            dvs_config_spec.productInfo = vim.dvs.ProductSpec(version=version)
        dvs_create_spec.configSpec = dvs_config_spec

        task = network_folder.CreateDVS_Task(spec=dvs_create_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to create DVSwitch")}

        return {
            "status": "success",
            "operation": "create_dvswitch",
            "datacenter_name": datacenter_name,
            "dvswitch_name": dvswitch_name,
            "num_uplinks": num_uplinks,
            "max_mtu": max_mtu,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_dvportgroup(
        dvswitch_name: str,
        portgroup_name: str,
        vlan_id: int = 0,
        vlan_trunk_ranges: str | None = None,
        num_ports: int = 128,
        port_binding: str = "static",
        allow_promiscuous: bool = False,
        allow_mac_changes: bool = True,
        allow_forged_transmits: bool = True,
    ) -> dict[str, Any]:
        """Create a new Distributed Virtual Portgroup on a DVSwitch.

        Args:
            dvswitch_name: Name of the DVSwitch to add the portgroup to.
            portgroup_name: Name for the new portgroup.
            vlan_id: VLAN ID (0 for none, 1-4094 for specific VLAN). Mutually exclusive with vlan_trunk_ranges.
            vlan_trunk_ranges: VLAN trunk ranges (e.g. "100-200,300-400"). Mutually exclusive with vlan_id.
            num_ports: Number of ports (default 128).
            port_binding: Port binding type: "static" (earlyBinding), "dynamic" (lateBinding), or "ephemeral".
            allow_promiscuous: Allow promiscuous mode (default False).
            allow_mac_changes: Allow MAC address changes (default True).
            allow_forged_transmits: Allow forged transmits (default True).
        """
        logger.info(
            "create_dvportgroup",
            dvswitch_name=dvswitch_name,
            portgroup_name=portgroup_name,
            vlan_id=vlan_id,
            vlan_trunk_ranges=vlan_trunk_ranges,
            num_ports=num_ports,
            port_binding=port_binding,
        )
        if vlan_trunk_ranges and vlan_id != 0:
            return {"status": "error", "error": "Only one of vlan_id or vlan_trunk_ranges should be set"}
        if vlan_id < 0 or vlan_id > 4094:
            return {"status": "error", "error": "vlan_id must be between 0 and 4094"}
        binding_map = {"static": "earlyBinding", "dynamic": "lateBinding", "ephemeral": "ephemeral"}
        binding_type = binding_map.get(port_binding)
        if binding_type is None:
            return {"status": "error", "error": f"port_binding must be one of: {', '.join(binding_map.keys())}"}

        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name"])
        dvs_obj = None
        for item in dvs_items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        pg_spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec(
            name=portgroup_name,
            numPorts=num_ports,
            type=binding_type,
        )

        if vlan_trunk_ranges:
            trunk_vlan_ids = []
            for part in vlan_trunk_ranges.split(","):
                part = part.strip()
                if "-" in part:
                    start_s, end_s = part.split("-", 1)
                    trunk_vlan_ids.append(vim.NumericRange(start=int(start_s.strip()), end=int(end_s.strip())))
                else:
                    val = int(part)
                    trunk_vlan_ids.append(vim.NumericRange(start=val, end=val))
            vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec(vlanId=trunk_vlan_ids)
        else:
            vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec(vlanId=vlan_id)

        security_policy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy(
            allowPromiscuous=vim.BoolPolicy(value=allow_promiscuous),
            macChanges=vim.BoolPolicy(value=allow_mac_changes),
            forgedTransmits=vim.BoolPolicy(value=allow_forged_transmits),
        )
        pg_spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy(
            vlan=vlan_spec,
            securityPolicy=security_policy,
        )

        task = dvs_obj.AddDVPortgroup_Task(spec=[pg_spec])
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to create DVPortgroup")}

        return {
            "status": "success",
            "operation": "create_dvportgroup",
            "dvswitch_name": dvswitch_name,
            "portgroup_name": portgroup_name,
            "vlan_id": vlan_id,
            "vlan_trunk_ranges": vlan_trunk_ranges,
            "num_ports": num_ports,
            "port_binding": port_binding,
            "allow_promiscuous": allow_promiscuous,
            "allow_mac_changes": allow_mac_changes,
            "allow_forged_transmits": allow_forged_transmits,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_host_portgroup(
        host_name: str,
        portgroup_name: str,
        vswitch_name: str,
        vlan_id: int = 0,
        allow_promiscuous: bool | None = None,
        allow_mac_changes: bool | None = None,
        allow_forged_transmits: bool | None = None,
    ) -> dict[str, Any]:
        """Add a standard portgroup to an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            portgroup_name: Name for the new portgroup.
            vswitch_name: Name of the vSwitch to attach to.
            vlan_id: VLAN ID (default 0 for no VLAN).
            allow_promiscuous: Allow promiscuous mode, or None to use switch default.
            allow_mac_changes: Allow MAC address changes, or None to use switch default.
            allow_forged_transmits: Allow forged transmits, or None to use switch default.
        """
        logger.info(
            "add_host_portgroup",
            host_name=host_name,
            portgroup_name=portgroup_name,
            vswitch_name=vswitch_name,
            vlan_id=vlan_id,
        )
        if vlan_id < 0 or vlan_id > 4094:
            return {"status": "error", "error": "vlan_id must be between 0 and 4094"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}

        network_policy = vim.host.NetworkPolicy()
        if any(v is not None for v in (allow_promiscuous, allow_mac_changes, allow_forged_transmits)):
            sec_policy = vim.host.NetworkPolicy.SecurityPolicy()
            if allow_promiscuous is not None:
                sec_policy.allowPromiscuous = allow_promiscuous
            if allow_mac_changes is not None:
                sec_policy.macChanges = allow_mac_changes
            if allow_forged_transmits is not None:
                sec_policy.forgedTransmits = allow_forged_transmits
            network_policy.security = sec_policy

        spec = vim.host.PortGroup.Specification(
            name=portgroup_name,
            vswitchName=vswitch_name,
            vlanId=vlan_id,
            policy=network_policy,
        )
        net_system.AddPortGroup(portgrp=spec)

        return {
            "status": "success",
            "operation": "add_host_portgroup",
            "host_name": host_name,
            "portgroup_name": portgroup_name,
            "vswitch_name": vswitch_name,
            "vlan_id": vlan_id,
            "allow_promiscuous": allow_promiscuous,
            "allow_mac_changes": allow_mac_changes,
            "allow_forged_transmits": allow_forged_transmits,
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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_dvswitch(dvswitch_name: str) -> dict[str, Any]:
        """Destroy a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch to delete.
        """
        logger.info("delete_dvswitch", dvswitch_name=dvswitch_name)

        items = collect_properties(client, vim.DistributedVirtualSwitch, ["name"])
        dvs_obj = None
        for item in items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        task = dvs_obj.Destroy_Task()
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to delete DVSwitch")}

        return {
            "status": "success",
            "operation": "delete_dvswitch",
            "dvswitch_name": dvswitch_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_dvportgroup(portgroup_name: str) -> dict[str, Any]:
        """Destroy a Distributed Virtual Portgroup.

        Args:
            portgroup_name: Name of the DVS portgroup to delete.
        """
        logger.info("delete_dvportgroup", portgroup_name=portgroup_name)

        items = collect_properties(client, vim.dvs.DistributedVirtualPortgroup, ["name"])
        pg_obj = None
        for item in items:
            if item.get("name") == portgroup_name:
                pg_obj = item["_obj"]
                break
        if pg_obj is None:
            return {"status": "error", "error": f"DVPortgroup '{portgroup_name}' not found"}

        task = pg_obj.Destroy_Task()
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to delete DVPortgroup")}

        return {
            "status": "success",
            "operation": "delete_dvportgroup",
            "portgroup_name": portgroup_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def update_dvportgroup(
        portgroup_name: str,
        vlan_id: int | None = None,
        vlan_trunk_ranges: str | None = None,
        num_ports: int | None = None,
        allow_promiscuous: bool | None = None,
        allow_mac_changes: bool | None = None,
        allow_forged_transmits: bool | None = None,
    ) -> dict[str, Any]:
        """Update configuration of a Distributed Virtual Portgroup.

        Args:
            portgroup_name: Name of the DVS portgroup to update.
            vlan_id: New VLAN ID (0-4094), or None to leave unchanged. Mutually exclusive with vlan_trunk_ranges.
            vlan_trunk_ranges: VLAN trunk ranges (e.g. "100-200,300-400"), or None to leave unchanged.
                Mutually exclusive with vlan_id.
            num_ports: New number of ports, or None to leave unchanged.
            allow_promiscuous: Allow promiscuous mode, or None to leave unchanged.
            allow_mac_changes: Allow MAC address changes, or None to leave unchanged.
            allow_forged_transmits: Allow forged transmits, or None to leave unchanged.
        """
        logger.info("update_dvportgroup", portgroup_name=portgroup_name, vlan_id=vlan_id, num_ports=num_ports)

        items = collect_properties(client, vim.dvs.DistributedVirtualPortgroup, ["name", "config"])
        pg_obj = None
        pg_config = None
        for item in items:
            if item.get("name") == portgroup_name:
                pg_obj = item["_obj"]
                pg_config = item.get("config")
                break
        if pg_obj is None:
            return {"status": "error", "error": f"DVPortgroup '{portgroup_name}' not found"}

        if vlan_id is not None and vlan_trunk_ranges is not None:
            return {"status": "error", "error": "Only one of vlan_id or vlan_trunk_ranges should be set"}

        spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
        spec.configVersion = pg_config.configVersion if pg_config else None

        has_port_config = False
        vlan_spec = None
        if vlan_trunk_ranges is not None:
            trunk_vlan_ids = []
            for part in vlan_trunk_ranges.split(","):
                part = part.strip()
                if "-" in part:
                    start_s, end_s = part.split("-", 1)
                    trunk_vlan_ids.append(vim.NumericRange(start=int(start_s.strip()), end=int(end_s.strip())))
                else:
                    val = int(part)
                    trunk_vlan_ids.append(vim.NumericRange(start=val, end=val))
            vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec(vlanId=trunk_vlan_ids)
            has_port_config = True
        elif vlan_id is not None:
            vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec(vlanId=vlan_id)
            has_port_config = True

        security_policy = None
        if any(v is not None for v in (allow_promiscuous, allow_mac_changes, allow_forged_transmits)):
            security_kwargs: dict[str, Any] = {}
            if allow_promiscuous is not None:
                security_kwargs["allowPromiscuous"] = vim.BoolPolicy(value=allow_promiscuous)
            if allow_mac_changes is not None:
                security_kwargs["macChanges"] = vim.BoolPolicy(value=allow_mac_changes)
            if allow_forged_transmits is not None:
                security_kwargs["forgedTransmits"] = vim.BoolPolicy(value=allow_forged_transmits)
            security_policy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy(**security_kwargs)
            has_port_config = True

        if has_port_config:
            port_config_kwargs: dict[str, Any] = {}
            if vlan_spec is not None:
                port_config_kwargs["vlan"] = vlan_spec
            if security_policy is not None:
                port_config_kwargs["securityPolicy"] = security_policy
            spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy(
                **port_config_kwargs,
            )

        if num_ports is not None:
            spec.numPorts = num_ports

        task = pg_obj.ReconfigureDVPortgroup_Task(spec=spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to update DVPortgroup")}

        return {
            "status": "success",
            "operation": "update_dvportgroup",
            "portgroup_name": portgroup_name,
            "vlan_id": vlan_id,
            "vlan_trunk_ranges": vlan_trunk_ranges,
            "num_ports": num_ports,
            "allow_promiscuous": allow_promiscuous,
            "allow_mac_changes": allow_mac_changes,
            "allow_forged_transmits": allow_forged_transmits,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def update_dvswitch(
        dvswitch_name: str,
        max_mtu: int | None = None,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """Update configuration of a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch to update.
            max_mtu: New maximum MTU (1500-9000), or None to leave unchanged.
            new_name: New name for the DVSwitch, or None to leave unchanged.
        """
        logger.info("update_dvswitch", dvswitch_name=dvswitch_name, max_mtu=max_mtu, new_name=new_name)

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

        spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        spec.configVersion = dvs_config.configVersion if dvs_config else None

        if max_mtu is not None:
            spec.maxMtu = max_mtu

        if new_name is not None:
            spec.name = new_name

        task = dvs_obj.ReconfigureDvs_Task(spec=spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to update DVSwitch")}

        return {
            "status": "success",
            "operation": "update_dvswitch",
            "dvswitch_name": dvswitch_name,
            "max_mtu": max_mtu,
            "new_name": new_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_host_to_dvswitch(
        dvswitch_name: str,
        host_name: str,
        uplink_pnic_names: list[str],
    ) -> dict[str, Any]:
        """Add an ESXi host to a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch to add the host to.
            host_name: Name of the ESXi host to add.
            uplink_pnic_names: List of physical NIC device names to use as uplinks (e.g. ["vmnic0", "vmnic1"]).
        """
        logger.info(
            "add_host_to_dvswitch",
            dvswitch_name=dvswitch_name,
            host_name=host_name,
            uplink_pnic_names=uplink_pnic_names,
        )

        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
        dvs_obj = None
        dvs_config = None
        for item in dvs_items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                dvs_config = item.get("config")
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        pnic_specs = [vim.dvs.HostMember.PnicSpec(pnicDevice=p) for p in uplink_pnic_names]
        backing = vim.dvs.HostMember.PnicBacking(pnicSpec=pnic_specs)
        member_spec = vim.dvs.HostMember.ConfigSpec(
            host=host_obj,
            operation="add",
            backing=backing,
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            host=[member_spec],
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to add host to DVSwitch")}

        return {
            "status": "success",
            "operation": "add_host_to_dvswitch",
            "dvswitch_name": dvswitch_name,
            "host_name": host_name,
            "uplink_pnic_names": uplink_pnic_names,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_host_from_dvswitch(
        dvswitch_name: str,
        host_name: str,
    ) -> dict[str, Any]:
        """Remove an ESXi host from a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch to remove the host from.
            host_name: Name of the ESXi host to remove.
        """
        logger.info(
            "remove_host_from_dvswitch",
            dvswitch_name=dvswitch_name,
            host_name=host_name,
        )

        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
        dvs_obj = None
        dvs_config = None
        for item in dvs_items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                dvs_config = item.get("config")
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        member_spec = vim.dvs.HostMember.ConfigSpec(
            host=host_obj,
            operation="remove",
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            host=[member_spec],
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to remove host from DVSwitch")}

        return {
            "status": "success",
            "operation": "remove_host_from_dvswitch",
            "dvswitch_name": dvswitch_name,
            "host_name": host_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_dvswitch_ports(
        dvswitch_name: str,
        connected_only: bool = False,
    ) -> dict[str, Any]:
        """List ports on a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch.
            connected_only: If True, return only connected ports. Default False returns all ports.
        """
        logger.info("list_dvswitch_ports", dvswitch_name=dvswitch_name, connected_only=connected_only)

        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name"])
        dvs_obj = None
        for item in dvs_items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        criteria = vim.dvs.PortCriteria(connected=True) if connected_only else vim.dvs.PortCriteria()
        ports = dvs_obj.FetchDVPorts(criteria=criteria)

        port_list = []
        for port in ports or []:
            connected_entity = None
            state = None
            if port.connectee:
                try:
                    connected_entity = getattr(port.connectee, "connectedEntity", None)
                    if connected_entity is not None:
                        connected_entity = getattr(connected_entity, "name", str(connected_entity))
                except Exception:
                    connected_entity = str(port.connectee)
            if port.state:
                state = getattr(port.state, "runtimeInfo", None)
                if state is not None:
                    link_up = getattr(state, "linkUp", None)
                    state = {"linkUp": link_up}
            port_list.append({
                "key": port.key,
                "connected_entity": connected_entity,
                "state": state,
            })

        return {
            "status": "success",
            "dvswitch_name": dvswitch_name,
            "connected_only": connected_only,
            "num_ports": len(port_list),
            "ports": port_list,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_dvs_pvlan(
        dvswitch_name: str,
        primary_vlan_id: int,
        secondary_vlan_id: int,
        pvlan_type: str,
    ) -> dict[str, Any]:
        """Configure Private VLAN (PVLAN) on a Distributed Virtual Switch.

        Args:
            dvswitch_name: Name of the DVSwitch.
            primary_vlan_id: Primary VLAN ID (1-4094).
            secondary_vlan_id: Secondary VLAN ID (1-4094).
            pvlan_type: PVLAN port type: "promiscuous", "isolated", or "community".
        """
        logger.info(
            "configure_dvs_pvlan",
            dvswitch_name=dvswitch_name,
            primary_vlan_id=primary_vlan_id,
            secondary_vlan_id=secondary_vlan_id,
            pvlan_type=pvlan_type,
        )

        valid_pvlan_types = ("promiscuous", "isolated", "community")
        if pvlan_type not in valid_pvlan_types:
            return {"status": "error", "error": f"pvlan_type must be one of: {', '.join(valid_pvlan_types)}"}
        if not (1 <= primary_vlan_id <= 4094):
            return {"status": "error", "error": "primary_vlan_id must be between 1 and 4094"}
        if not (1 <= secondary_vlan_id <= 4094):
            return {"status": "error", "error": "secondary_vlan_id must be between 1 and 4094"}

        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
        dvs_obj = None
        dvs_config = None
        for item in dvs_items:
            if item.get("name") == dvswitch_name:
                dvs_obj = item["_obj"]
                dvs_config = item.get("config")
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvswitch_name}' not found"}

        pvlan_map_entry = vim.dvs.VmwareDistributedVirtualSwitch.PvlanMapEntry(
            primaryVlanId=primary_vlan_id,
            secondaryVlanId=secondary_vlan_id,
            pvlanType=pvlan_type,
        )
        pvlan_config_spec = vim.dvs.VmwareDistributedVirtualSwitch.PvlanConfigSpec(
            pvlanEntry=pvlan_map_entry,
            operation="add",
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            pvlanConfigSpec=[pvlan_config_spec],
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure PVLAN on DVSwitch")}

        return {
            "status": "success",
            "operation": "configure_dvs_pvlan",
            "dvswitch_name": dvswitch_name,
            "primary_vlan_id": primary_vlan_id,
            "secondary_vlan_id": secondary_vlan_id,
            "pvlan_type": pvlan_type,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_host_vswitch_nic_teaming(
        host_name: str,
        vswitch_name: str,
        active_nics: list[str],
        standby_nics: list[str] | None = None,
        policy: str = "loadbalance_srcid",
    ) -> dict[str, Any]:
        """Configure NIC teaming policy on a standard vSwitch on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            vswitch_name: Name of the standard vSwitch to configure.
            active_nics: List of NIC device names to set as active (e.g. ["vmnic0", "vmnic1"]).
            standby_nics: List of NIC device names to set as standby, or None for no standby NICs.
            policy: NIC teaming policy: "loadbalance_srcid", "loadbalance_ip", "loadbalance_srcmac",
                "failover_explicit" (default "loadbalance_srcid").
        """
        logger.info(
            "configure_host_vswitch_nic_teaming",
            host_name=host_name,
            vswitch_name=vswitch_name,
            active_nics=active_nics,
            standby_nics=standby_nics,
            policy=policy,
        )

        valid_policies = ("loadbalance_srcid", "loadbalance_ip", "loadbalance_srcmac", "failover_explicit")
        if policy not in valid_policies:
            return {"status": "error", "error": f"policy must be one of: {', '.join(valid_policies)}"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}

        nic_order = vim.host.NicOrderPolicy(
            activeNic=active_nics,
            standbyNic=standby_nics or [],
        )
        nic_teaming = vim.host.NetworkPolicy.NicTeamingPolicy(
            policy=policy,
            nicOrder=nic_order,
        )
        network_policy = vim.host.NetworkPolicy(nicTeaming=nic_teaming)

        vswitch_spec = vim.host.VirtualSwitch.Specification(policy=network_policy)
        net_system.UpdateVirtualSwitch(vswitchName=vswitch_name, spec=vswitch_spec)

        return {
            "status": "success",
            "operation": "configure_host_vswitch_nic_teaming",
            "host_name": host_name,
            "vswitch_name": vswitch_name,
            "active_nics": active_nics,
            "standby_nics": standby_nics,
            "policy": policy,
        }
