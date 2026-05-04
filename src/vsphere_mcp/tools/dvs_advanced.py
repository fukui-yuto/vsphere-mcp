from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_dvs(client: Any, dvs_name: str) -> tuple[Any | None, Any | None]:
    """Return (dvs_obj, dvs_config) for the named DVSwitch, or (None, None) if not found."""
    items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
    for item in items:
        if item.get("name") == dvs_name:
            return item["_obj"], item.get("config")
    return None, None


def register_dvs_advanced_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_dvs_lacp(
        dvs_name: str,
        enabled: bool = True,
        mode: str = "active",
    ) -> dict[str, Any]:
        """Configure LACP (Link Aggregation Control Protocol) on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            enabled: Enable or disable LACP (default True).
            mode: LACP mode: "active" or "passive" (default "active").
        """
        logger.info("configure_dvs_lacp", dvs_name=dvs_name, enabled=enabled, mode=mode)

        valid_modes = ("active", "passive")
        if mode not in valid_modes:
            return {"status": "error", "error": f"mode must be one of: {', '.join(valid_modes)}"}

        dvs_obj, dvs_config = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        if enabled:
            lacp_spec = vim.dvs.VmwareDistributedVirtualSwitch.LacpGroupSpec(
                lacpGroupConfig=vim.dvs.VmwareDistributedVirtualSwitch.LacpGroupConfig(
                    mode=mode,
                ),
                operation="edit",
            )
            try:
                task = dvs_obj.UpdateDVSLacpGroupConfig_Task(lacpGroupSpec=[lacp_spec])
                result = wait_for_task(task)
            except Exception as e:
                return {"status": "error", "error": f"Failed to configure LACP: {e}"}
        else:
            # Disable LACP by updating the DVS config with lacpApiVersion set to None
            config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
                configVersion=dvs_config.configVersion if dvs_config else None,
                lacpApiVersion=None,
            )
            task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
            result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure LACP on DVSwitch")}

        return {
            "status": "success",
            "operation": "configure_dvs_lacp",
            "dvs_name": dvs_name,
            "enabled": enabled,
            "mode": mode,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_dvs_health(dvs_name: str) -> dict[str, Any]:
        """Get health check status for a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
        """
        logger.info("get_dvs_health", dvs_name=dvs_name)

        dvs_obj, _ = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        runtime = getattr(dvs_obj, "runtime", None)
        if runtime is None:
            return {
                "status": "success",
                "dvs_name": dvs_name,
                "message": "No runtime information available",
                "host_member_runtime": [],
            }

        host_runtimes = []
        for member_runtime in getattr(runtime, "hostMemberRuntime", None) or []:
            host_key = getattr(member_runtime, "host", None)
            host_name = None
            if host_key is not None:
                try:
                    host_name = host_key.name
                except Exception:
                    host_name = str(host_key)
            host_runtimes.append({
                "host": host_name,
                "status": getattr(member_runtime, "status", None),
                "statusDetail": getattr(member_runtime, "statusDetail", None),
            })

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "num_hosts": len(host_runtimes),
            "host_member_runtime": host_runtimes,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def enable_dvs_health_check(
        dvs_name: str,
        vlan_mtu_check: bool = True,
        teaming_check: bool = True,
        interval: int = 1,
    ) -> dict[str, Any]:
        """Enable health checking on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            vlan_mtu_check: Enable VLAN and MTU health check (default True).
            teaming_check: Enable teaming and failover health check (default True).
            interval: Health check interval in minutes (default 1).
        """
        logger.info(
            "enable_dvs_health_check",
            dvs_name=dvs_name,
            vlan_mtu_check=vlan_mtu_check,
            teaming_check=teaming_check,
            interval=interval,
        )

        dvs_obj, _ = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        health_check_config = [
            vim.dvs.VmwareDistributedVirtualSwitch.VlanMtuHealthCheckConfig(
                enable=vlan_mtu_check,
                interval=interval,
            ),
            vim.dvs.VmwareDistributedVirtualSwitch.TeamingHealthCheckConfig(
                enable=teaming_check,
                interval=interval,
            ),
        ]

        task = dvs_obj.UpdateDVSHealthCheckConfig_Task(healthCheckConfig=health_check_config)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure DVS health check")}

        return {
            "status": "success",
            "operation": "enable_dvs_health_check",
            "dvs_name": dvs_name,
            "vlan_mtu_check": vlan_mtu_check,
            "teaming_check": teaming_check,
            "interval": interval,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def migrate_vm_networking_to_dvs(
        vm_name: str,
        source_portgroup: str,
        target_dvportgroup: str,
    ) -> dict[str, Any]:
        """Migrate a VM NIC from a standard portgroup to a DVS portgroup.

        Args:
            vm_name: Name of the VM whose NIC will be migrated.
            source_portgroup: Name of the current standard portgroup the NIC is connected to.
            target_dvportgroup: Name of the target Distributed Virtual Portgroup to migrate to.
        """
        logger.info(
            "migrate_vm_networking_to_dvs",
            vm_name=vm_name,
            source_portgroup=source_portgroup,
            target_dvportgroup=target_dvportgroup,
        )

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        # Find the DVPortgroup object
        pg_items = collect_properties(client, vim.dvs.DistributedVirtualPortgroup, ["name", "config", "key"])
        dvpg_obj = None
        dvpg_key = None
        dvs_uuid = None
        for pg_item in pg_items:
            if pg_item.get("name") == target_dvportgroup:
                dvpg_obj = pg_item["_obj"]
                dvpg_key = pg_item.get("key")
                pg_config = pg_item.get("config")
                if pg_config is not None:
                    dvs_ref = getattr(pg_config, "distributedVirtualSwitch", None)
                    if dvs_ref is not None:
                        try:
                            dvs_uuid = dvs_ref.uuid
                        except Exception:
                            pass
                break
        if dvpg_obj is None:
            return {"status": "error", "error": f"DVPortgroup '{target_dvportgroup}' not found"}

        # Find NIC on source portgroup
        target_nic = None
        for dev in found.get("config.hardware.device") or []:
            if not hasattr(dev, "backing"):
                continue
            backing = dev.backing
            if isinstance(backing, vim.vm.device.VirtualEthernetCard.NetworkBackingInfo):
                if getattr(backing, "deviceName", None) == source_portgroup:
                    target_nic = dev
                    break

        if target_nic is None:
            return {
                "status": "error",
                "error": f"No NIC connected to portgroup '{source_portgroup}' found on VM '{vm_name}'",
            }

        # Build DVS backing
        port = vim.dvs.PortConnection(
            portgroupKey=dvpg_key,
            switchUuid=dvs_uuid,
        )
        new_backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(port=port)
        target_nic.backing = new_backing

        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=target_nic,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to migrate VM NIC to DVS portgroup")}

        return {
            "status": "success",
            "operation": "migrate_vm_networking_to_dvs",
            "vm_name": vm_name,
            "source_portgroup": source_portgroup,
            "target_dvportgroup": target_dvportgroup,
        }

    @mcp.tool()
    @handle_tool_errors
    def export_dvs_config(dvs_name: str) -> dict[str, Any]:
        """Export the configuration of a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
        """
        logger.info("export_dvs_config", dvs_name=dvs_name)

        dvs_obj, dvs_config = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        if dvs_config is None:
            return {"status": "error", "error": f"Configuration not available for DVSwitch '{dvs_name}'"}

        uplink_names: list[str] = []
        if hasattr(dvs_config, "uplinkPortgroup") and dvs_config.uplinkPortgroup:
            for pg_ref in dvs_config.uplinkPortgroup:
                try:
                    uplink_names.append(pg_ref.name)
                except Exception:
                    uplink_names.append(str(pg_ref))

        default_port_config: dict[str, Any] | None = None
        dpc = getattr(dvs_config, "defaultPortConfig", None)
        if dpc is not None:
            vlan = getattr(dpc, "vlan", None)
            vlan_info = None
            if vlan is not None:
                if isinstance(vlan, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
                    vlan_info = {"type": "VlanIdSpec", "vlanId": vlan.vlanId}
                elif isinstance(vlan, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                    ranges = [{"start": r.start, "end": r.end} for r in vlan.vlanId or []]
                    vlan_info = {"type": "TrunkVlanSpec", "ranges": ranges}
                else:
                    vlan_info = {"type": type(vlan).__name__}
            default_port_config = {"vlan": vlan_info}

        product_info = getattr(dvs_config, "productInfo", None)
        version = getattr(product_info, "version", None) if product_info else None

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "config": {
                "name": getattr(dvs_config, "name", dvs_name),
                "uuid": getattr(dvs_config, "uuid", None),
                "numPorts": getattr(dvs_config, "numPorts", None),
                "maxMtu": getattr(dvs_config, "maxMtu", None),
                "version": version,
                "uplinkPortgroups": uplink_names,
                "defaultPortConfig": default_port_config,
                "lacpApiVersion": getattr(dvs_config, "lacpApiVersion", None),
                "configVersion": getattr(dvs_config, "configVersion", None),
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def get_dvs_port_statistics(
        dvs_name: str,
        port_key: str | None = None,
    ) -> dict[str, Any]:
        """Get port statistics for a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            port_key: Specific port key to query, or None to retrieve statistics for all ports.
        """
        logger.info("get_dvs_port_statistics", dvs_name=dvs_name, port_key=port_key)

        dvs_obj, _ = _find_dvs(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        criteria = vim.dvs.PortCriteria()
        if port_key is not None:
            criteria.portKey = [port_key]

        ports = dvs_obj.FetchDVPorts(criteria=criteria)

        port_stats = []
        for port in ports or []:
            stats_entry: dict[str, Any] = {"key": port.key}

            state = getattr(port, "state", None)
            if state is not None:
                runtime_info = getattr(state, "runtimeInfo", None)
                if runtime_info is not None:
                    stats_obj = getattr(runtime_info, "stats", None)
                    if stats_obj is not None:
                        stats_entry["packetsIn"] = getattr(stats_obj, "packetsIn", None)
                        stats_entry["packetsOut"] = getattr(stats_obj, "packetsOut", None)
                        stats_entry["bytesIn"] = getattr(stats_obj, "bytesIn", None)
                        stats_entry["bytesOut"] = getattr(stats_obj, "bytesOut", None)
                        stats_entry["droppedPacketsIn"] = getattr(stats_obj, "droppedPacketsIn", None)
                        stats_entry["droppedPacketsOut"] = getattr(stats_obj, "droppedPacketsOut", None)

            port_stats.append(stats_entry)

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "port_key_filter": port_key,
            "num_ports": len(port_stats),
            "port_statistics": port_stats,
        }
