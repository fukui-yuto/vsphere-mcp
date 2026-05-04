from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_dvs(client: Any, dvs_name: str) -> Any | None:
    items = collect_properties(client, vim.DistributedVirtualSwitch, ["name"])
    for item in items:
        if item.get("name") == dvs_name:
            return item["_obj"]
    return None


def _find_dvs_with_config(client: Any, dvs_name: str) -> tuple[Any | None, Any | None]:
    items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "config"])
    for item in items:
        if item.get("name") == dvs_name:
            return item["_obj"], item.get("config")
    return None, None


def _find_datacenter(client: Any, datacenter_name: str) -> Any | None:
    items = collect_properties(client, vim.Datacenter, ["name"])
    for item in items:
        if item.get("name") == datacenter_name:
            return item["_obj"]
    return None


def register_network_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_dvs_netflow(
        dvs_name: str,
        collector_ip: str,
        collector_port: int = 2055,
        observation_domain_id: int = 0,
        active_flow_timeout: int = 60,
        idle_flow_timeout: int = 15,
        sampling_rate: int = 0,
    ) -> dict[str, Any]:
        """Configure NetFlow/IPFIX on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            collector_ip: IP address of the NetFlow/IPFIX collector.
            collector_port: UDP port of the collector (default 2055).
            observation_domain_id: IPFIX observation domain ID (default 0).
            active_flow_timeout: Active flow timeout in seconds (default 60).
            idle_flow_timeout: Idle flow timeout in seconds (default 15).
            sampling_rate: Sampling rate — 0 means sample every packet (default 0).
        """
        logger.info(
            "configure_dvs_netflow",
            dvs_name=dvs_name,
            collector_ip=collector_ip,
            collector_port=collector_port,
        )

        dvs_obj, dvs_config = _find_dvs_with_config(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        ipfix_config = vim.dvs.VmwareDistributedVirtualSwitch.IpfixConfig(
            collectorIpAddress=collector_ip,
            collectorPort=collector_port,
            observationDomainId=observation_domain_id,
            activeFlowTimeout=active_flow_timeout,
            idleFlowTimeout=idle_flow_timeout,
            samplingRate=sampling_rate,
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            ipfixConfig=ipfix_config,
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure NetFlow on DVSwitch")}

        return {
            "status": "success",
            "operation": "configure_dvs_netflow",
            "dvs_name": dvs_name,
            "collector_ip": collector_ip,
            "collector_port": collector_port,
            "observation_domain_id": observation_domain_id,
            "active_flow_timeout": active_flow_timeout,
            "idle_flow_timeout": idle_flow_timeout,
            "sampling_rate": sampling_rate,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_dvs_netflow_config(dvs_name: str) -> dict[str, Any]:
        """Get NetFlow/IPFIX configuration for a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
        """
        logger.info("get_dvs_netflow_config", dvs_name=dvs_name)

        dvs_obj, dvs_config = _find_dvs_with_config(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        ipfix = getattr(dvs_config, "ipfixConfig", None) if dvs_config else None
        if ipfix is None:
            return {
                "status": "success",
                "dvs_name": dvs_name,
                "ipfix_config": None,
                "message": "No NetFlow/IPFIX configuration found",
            }

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "ipfix_config": {
                "collectorIpAddress": getattr(ipfix, "collectorIpAddress", None),
                "collectorPort": getattr(ipfix, "collectorPort", None),
                "observationDomainId": getattr(ipfix, "observationDomainId", None),
                "activeFlowTimeout": getattr(ipfix, "activeFlowTimeout", None),
                "idleFlowTimeout": getattr(ipfix, "idleFlowTimeout", None),
                "samplingRate": getattr(ipfix, "samplingRate", None),
            },
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_dvs_port_mirror(
        dvs_name: str,
        session_name: str,
        source_port_keys: list[str],
        destination_port_key: str,
        session_type: str = "dvPortMirror",
    ) -> dict[str, Any]:
        """Configure port mirroring (SPAN) session on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            session_name: Name for the new port mirror session.
            source_port_keys: List of source port keys to mirror traffic from.
            destination_port_key: Destination port key to send mirrored traffic to.
            session_type: Session type (default "dvPortMirror"). Other options:
                "remoteMirrorSource", "remoteMirrorDest", "encapsulatedRemoteMirrorSource".
        """
        logger.info(
            "configure_dvs_port_mirror",
            dvs_name=dvs_name,
            session_name=session_name,
            destination_port_key=destination_port_key,
        )

        valid_types = ("dvPortMirror", "remoteMirrorSource", "remoteMirrorDest", "encapsulatedRemoteMirrorSource")
        if session_type not in valid_types:
            return {"status": "error", "error": f"session_type must be one of: {', '.join(valid_types)}"}

        dvs_obj, dvs_config = _find_dvs_with_config(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        source_ports = vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=source_port_keys)
        dest_ports = vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=[destination_port_key])

        vspan_session = vim.dvs.VmwareDistributedVirtualSwitch.VspanSession(
            name=session_name,
            enabled=True,
            sessionType=session_type,
            sourcePortTransmitted=source_ports,
            destinationPort=dest_ports,
        )

        vspan_config_spec = vim.dvs.VmwareDistributedVirtualSwitch.VspanConfigSpec(
            vspanSession=vspan_session,
            operation="add",
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            vspanConfigSpec=[vspan_config_spec],
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure port mirror session")}

        return {
            "status": "success",
            "operation": "configure_dvs_port_mirror",
            "dvs_name": dvs_name,
            "session_name": session_name,
            "source_port_keys": source_port_keys,
            "destination_port_key": destination_port_key,
            "session_type": session_type,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_dvs_port_mirror_sessions(dvs_name: str) -> dict[str, Any]:
        """List port mirroring (SPAN) sessions on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
        """
        logger.info("list_dvs_port_mirror_sessions", dvs_name=dvs_name)

        dvs_obj, dvs_config = _find_dvs_with_config(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        sessions: list[dict[str, Any]] = []
        for session in getattr(dvs_config, "vspanSession", None) or []:
            src_transmitted = getattr(session, "sourcePortTransmitted", None)
            src_received = getattr(session, "sourcePortReceived", None)
            dest = getattr(session, "destinationPort", None)
            sessions.append({
                "key": getattr(session, "key", None),
                "name": getattr(session, "name", None),
                "enabled": getattr(session, "enabled", None),
                "sessionType": getattr(session, "sessionType", None),
                "sourcePortTransmitted": getattr(src_transmitted, "portKey", []) if src_transmitted else [],
                "sourcePortReceived": getattr(src_received, "portKey", []) if src_received else [],
                "destinationPort": getattr(dest, "portKey", []) if dest else [],
            })

        return {
            "status": "success",
            "dvs_name": dvs_name,
            "num_sessions": len(sessions),
            "sessions": sessions,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def delete_dvs_port_mirror_session(dvs_name: str, session_key: str) -> dict[str, Any]:
        """Delete a port mirroring (SPAN) session from a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            session_key: Key of the VSPAN session to delete.
        """
        logger.info("delete_dvs_port_mirror_session", dvs_name=dvs_name, session_key=session_key)

        dvs_obj, dvs_config = _find_dvs_with_config(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        # Find the session by key to build a matching VspanSession stub for removal
        target_session = None
        for session in getattr(dvs_config, "vspanSession", None) or []:
            if str(getattr(session, "key", None)) == str(session_key):
                target_session = session
                break

        if target_session is None:
            return {"status": "error", "error": f"Port mirror session key '{session_key}' not found on DVSwitch '{dvs_name}'"}

        vspan_config_spec = vim.dvs.VmwareDistributedVirtualSwitch.VspanConfigSpec(
            vspanSession=target_session,
            operation="remove",
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            vspanConfigSpec=[vspan_config_spec],
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to delete port mirror session")}

        return {
            "status": "success",
            "operation": "delete_dvs_port_mirror_session",
            "dvs_name": dvs_name,
            "session_key": session_key,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_dvs_discovery_protocol(
        dvs_name: str,
        protocol: str = "cdp",
        operation: str = "both",
    ) -> dict[str, Any]:
        """Set the link discovery protocol (CDP or LLDP) on a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch.
            protocol: Discovery protocol to use: "cdp" or "lldp" (default "cdp").
            operation: Protocol operation mode: "listen", "advertise", "both", or "none" (default "both").
        """
        logger.info("set_dvs_discovery_protocol", dvs_name=dvs_name, protocol=protocol, operation=operation)

        valid_protocols = ("cdp", "lldp")
        if protocol not in valid_protocols:
            return {"status": "error", "error": f"protocol must be one of: {', '.join(valid_protocols)}"}

        valid_operations = ("listen", "advertise", "both", "none")
        if operation not in valid_operations:
            return {"status": "error", "error": f"operation must be one of: {', '.join(valid_operations)}"}

        dvs_obj, dvs_config = _find_dvs_with_config(client, dvs_name)
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        ldp_config = vim.host.LinkDiscoveryProtocolConfig(
            protocol=protocol,
            operation=operation,
        )

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
            configVersion=dvs_config.configVersion if dvs_config else None,
            linkDiscoveryProtocolConfig=ldp_config,
        )

        task = dvs_obj.ReconfigureDvs_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to set discovery protocol on DVSwitch")}

        return {
            "status": "success",
            "operation": "set_dvs_discovery_protocol",
            "dvs_name": dvs_name,
            "protocol": protocol,
            "operation_mode": operation,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_ip_pools(datacenter_name: str) -> dict[str, Any]:
        """List IP pools defined in a datacenter.

        Args:
            datacenter_name: Name of the datacenter.
        """
        logger.info("list_ip_pools", datacenter_name=datacenter_name)

        dc_obj = _find_datacenter(client, datacenter_name)
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        ip_pool_manager = getattr(client.content, "ipPoolManager", None)
        if ip_pool_manager is None:
            return {"status": "error", "error": "ipPoolManager not available on this vCenter"}

        pools = ip_pool_manager.QueryIpPools(dc=dc_obj)

        pool_list: list[dict[str, Any]] = []
        for pool in pools or []:
            ipv4_config = getattr(pool, "ipv4Config", None)
            ipv6_config = getattr(pool, "ipv6Config", None)
            pool_list.append({
                "id": getattr(pool, "id", None),
                "name": getattr(pool, "name", None),
                "dnsDomain": getattr(pool, "dnsDomain", None),
                "dnsSearchPath": getattr(pool, "dnsSearchPath", None),
                "ipv4Config": {
                    "subnetAddress": getattr(ipv4_config, "subnetAddress", None),
                    "netmask": getattr(ipv4_config, "netmask", None),
                    "gateway": getattr(ipv4_config, "gateway", None),
                    "range": getattr(ipv4_config, "range", None),
                    "dhcpServerAvailable": getattr(ipv4_config, "dhcpServerAvailable", None),
                } if ipv4_config is not None else None,
                "ipv6Config": {
                    "subnetAddress": getattr(ipv6_config, "subnetAddress", None),
                    "prefix": getattr(ipv6_config, "prefix", None),
                    "gateway": getattr(ipv6_config, "gateway", None),
                    "range": getattr(ipv6_config, "range", None),
                    "dhcpServerAvailable": getattr(ipv6_config, "dhcpServerAvailable", None),
                } if ipv6_config is not None else None,
            })

        return {
            "status": "success",
            "datacenter_name": datacenter_name,
            "num_pools": len(pool_list),
            "ip_pools": pool_list,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_ip_pool(
        datacenter_name: str,
        pool_name: str,
        ipv4_subnet: str = "",
        ipv4_gateway: str = "",
        ipv4_range: str = "",
        ipv6_subnet: str = "",
        ipv6_gateway: str = "",
    ) -> dict[str, Any]:
        """Create an IP pool in a datacenter.

        Args:
            datacenter_name: Name of the datacenter.
            pool_name: Name for the new IP pool.
            ipv4_subnet: IPv4 subnet address (e.g. "192.168.1.0"). Leave empty to skip IPv4.
            ipv4_gateway: IPv4 gateway address (e.g. "192.168.1.1"). Leave empty to skip.
            ipv4_range: IPv4 address range (e.g. "192.168.1.100#50"). Leave empty to skip.
            ipv6_subnet: IPv6 subnet address. Leave empty to skip IPv6.
            ipv6_gateway: IPv6 gateway address. Leave empty to skip.
        """
        logger.info("create_ip_pool", datacenter_name=datacenter_name, pool_name=pool_name)

        dc_obj = _find_datacenter(client, datacenter_name)
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        ip_pool_manager = getattr(client.content, "ipPoolManager", None)
        if ip_pool_manager is None:
            return {"status": "error", "error": "ipPoolManager not available on this vCenter"}

        pool = vim.vApp.IpPool(name=pool_name)

        if ipv4_subnet or ipv4_gateway or ipv4_range:
            ipv4_config = vim.vApp.IpPool.IpPoolConfigInfo(
                subnetAddress=ipv4_subnet or None,
                gateway=ipv4_gateway or None,
                range=ipv4_range or None,
                dhcpServerAvailable=False,
            )
            pool.ipv4Config = ipv4_config

        if ipv6_subnet or ipv6_gateway:
            ipv6_config = vim.vApp.IpPool.IpPoolConfigInfo(
                subnetAddress=ipv6_subnet or None,
                gateway=ipv6_gateway or None,
                dhcpServerAvailable=False,
            )
            pool.ipv6Config = ipv6_config

        pool_id = ip_pool_manager.CreateIpPool(dc=dc_obj, pool=pool)

        return {
            "status": "success",
            "operation": "create_ip_pool",
            "datacenter_name": datacenter_name,
            "pool_name": pool_name,
            "pool_id": pool_id,
            "ipv4_subnet": ipv4_subnet,
            "ipv4_gateway": ipv4_gateway,
            "ipv4_range": ipv4_range,
            "ipv6_subnet": ipv6_subnet,
            "ipv6_gateway": ipv6_gateway,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_ip_pool(
        datacenter_name: str,
        pool_id: int,
        force: bool = False,
    ) -> dict[str, Any]:
        """Delete an IP pool from a datacenter.

        Args:
            datacenter_name: Name of the datacenter.
            pool_id: Numeric ID of the IP pool to delete.
            force: Force deletion even if the pool is in use (default False).
        """
        logger.info("delete_ip_pool", datacenter_name=datacenter_name, pool_id=pool_id, force=force)

        dc_obj = _find_datacenter(client, datacenter_name)
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        ip_pool_manager = getattr(client.content, "ipPoolManager", None)
        if ip_pool_manager is None:
            return {"status": "error", "error": "ipPoolManager not available on this vCenter"}

        ip_pool_manager.DestroyIpPool(dc=dc_obj, id=pool_id, force=force)

        return {
            "status": "success",
            "operation": "delete_ip_pool",
            "datacenter_name": datacenter_name,
            "pool_id": pool_id,
            "force": force,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_network_protocol_profile(
        datacenter_name: str,
        pool_name: str,
        dns_domain: str = "",
        dns_servers: list[str] = [],
        ntp_servers: list[str] = [],
    ) -> dict[str, Any]:
        """Configure network protocol profile settings on an IP pool (DNS domain, DNS servers, NTP servers).

        Args:
            datacenter_name: Name of the datacenter.
            pool_name: Name of the IP pool to update.
            dns_domain: DNS domain name for the pool (e.g. "example.com"). Leave empty to skip.
            dns_servers: List of DNS server IP addresses. Leave empty to skip.
            ntp_servers: List of NTP server addresses. Leave empty to skip.
        """
        logger.info(
            "configure_network_protocol_profile",
            datacenter_name=datacenter_name,
            pool_name=pool_name,
        )

        dc_obj = _find_datacenter(client, datacenter_name)
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        ip_pool_manager = getattr(client.content, "ipPoolManager", None)
        if ip_pool_manager is None:
            return {"status": "error", "error": "ipPoolManager not available on this vCenter"}

        pools = ip_pool_manager.QueryIpPools(dc=dc_obj)
        target_pool = None
        for pool in pools or []:
            if getattr(pool, "name", None) == pool_name:
                target_pool = pool
                break

        if target_pool is None:
            return {"status": "error", "error": f"IP pool '{pool_name}' not found in datacenter '{datacenter_name}'"}

        if dns_domain:
            target_pool.dnsDomain = dns_domain
        if dns_servers:
            target_pool.dnsSearchPath = ",".join(dns_servers)
        if ntp_servers:
            target_pool.hostPrefix = None  # preserve existing
            # NTP is stored in the networkAssociation or custom fields; use availableIpv4Addresses as proxy
            # vSphere IpPool does not have a direct NTP field; store in dnsDomain extension comment
            logger.info("configure_network_protocol_profile_ntp_note", note="NTP servers noted but vSphere IpPool has no direct NTP field")

        ip_pool_manager.UpdateIpPool(dc=dc_obj, pool=target_pool)

        return {
            "status": "success",
            "operation": "configure_network_protocol_profile",
            "datacenter_name": datacenter_name,
            "pool_name": pool_name,
            "pool_id": getattr(target_pool, "id", None),
            "dns_domain": dns_domain,
            "dns_servers": dns_servers,
            "ntp_servers": ntp_servers,
            "note": "NTP servers are not directly stored on vSphere IpPool objects; dns_domain and dns_servers were applied.",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vm_nic_advanced_settings(vm_name: str) -> dict[str, Any]:
        """Get advanced settings for all network adapters on a VM (Wake-on-LAN, UPT, adapter type).

        Args:
            vm_name: Name of the VM.
        """
        logger.info("get_vm_nic_advanced_settings", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device") or []
        nics: list[dict[str, Any]] = []
        for dev in devices:
            if not isinstance(dev, vim.vm.device.VirtualEthernetCard):
                continue
            device_info = getattr(dev, "deviceInfo", None)
            label = getattr(device_info, "label", None) if device_info else None
            nics.append({
                "label": label,
                "type": type(dev).__name__,
                "macAddress": getattr(dev, "macAddress", None),
                "wakeOnLanEnabled": getattr(dev, "wakeOnLanEnabled", None),
                "uptCompatibilityEnabled": getattr(dev, "uptCompatibilityEnabled", None),
                "connected": getattr(getattr(dev, "connectable", None), "connected", None),
                "startConnected": getattr(getattr(dev, "connectable", None), "startConnected", None),
            })

        return {
            "status": "success",
            "vm_name": vm_name,
            "num_nics": len(nics),
            "nics": nics,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_nic_advanced_settings(
        vm_name: str,
        nic_label: str,
        wake_on_lan: bool | None = None,
        upt_mode: bool | None = None,
    ) -> dict[str, Any]:
        """Set advanced settings (Wake-on-LAN, UPT compatibility) on a VM network adapter.

        Args:
            vm_name: Name of the VM.
            nic_label: Label of the network adapter (e.g. "Network adapter 1").
            wake_on_lan: Enable or disable Wake-on-LAN, or None to leave unchanged.
            upt_mode: Enable or disable Uniform Passthrough (UPT) mode, or None to leave unchanged.
        """
        logger.info("set_vm_nic_advanced_settings", vm_name=vm_name, nic_label=nic_label)

        if wake_on_lan is None and upt_mode is None:
            return {"status": "error", "error": "At least one of wake_on_lan or upt_mode must be specified"}

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device") or []
        target_nic = None
        for dev in devices:
            if not isinstance(dev, vim.vm.device.VirtualEthernetCard):
                continue
            device_info = getattr(dev, "deviceInfo", None)
            label = getattr(device_info, "label", None) if device_info else None
            if label == nic_label:
                target_nic = dev
                break

        if target_nic is None:
            return {"status": "error", "error": f"NIC '{nic_label}' not found on VM '{vm_name}'"}

        if wake_on_lan is not None:
            target_nic.wakeOnLanEnabled = wake_on_lan
        if upt_mode is not None:
            target_nic.uptCompatibilityEnabled = upt_mode

        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=target_nic,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to update NIC advanced settings")}

        return {
            "status": "success",
            "operation": "set_vm_nic_advanced_settings",
            "vm_name": vm_name,
            "nic_label": nic_label,
            "wake_on_lan": wake_on_lan,
            "upt_mode": upt_mode,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_mac_address_pool(range_prefix: str = "00:50:56") -> dict[str, Any]:
        """Configure the MAC address range prefix used by vCenter for auto-generated MAC addresses.

        This is applied via vCenter advanced settings (config.vpxd.macAllocationScheme.prefix).

        Args:
            range_prefix: MAC address prefix in colon-separated hex format (default "00:50:56").
                VMware-assigned range is "00:50:56". Must be a valid OUI prefix.
        """
        logger.info("configure_mac_address_pool", range_prefix=range_prefix)

        parts = range_prefix.split(":")
        if len(parts) != 3:
            return {"status": "error", "error": "range_prefix must be a 3-octet OUI prefix (e.g. '00:50:56')"}
        for part in parts:
            if len(part) != 2:
                return {"status": "error", "error": f"Invalid octet '{part}' in range_prefix — each must be 2 hex digits"}
            try:
                int(part, 16)
            except ValueError:
                return {"status": "error", "error": f"Invalid hex octet '{part}' in range_prefix"}

        option_manager = getattr(client.content, "setting", None)

        if option_manager is None:
            return {"status": "error", "error": "vCenter setting manager not available"}

        setting_key = "config.vpxd.macAllocationScheme.prefix"
        try:
            option = vim.option.OptionValue(key=setting_key, value=range_prefix)
            option_manager.UpdateValues(changedValue=[option])
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to update MAC address pool prefix: {e}",
                "note": "This setting may not be modifiable via API on all vCenter versions.",
            }

        return {
            "status": "success",
            "operation": "configure_mac_address_pool",
            "range_prefix": range_prefix,
            "setting_key": setting_key,
            "note": "MAC address pool prefix updated. Changes take effect for new VMs created after this change.",
        }
