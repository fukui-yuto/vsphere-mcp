from __future__ import annotations

import datetime
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def _get_config_manager(host_obj: Any) -> Any | None:
    """Return host configManager or None."""
    cm = getattr(host_obj, "configManager", None)
    return cm


def register_host_config_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_host_vswitches(host_name: str) -> dict[str, Any]:
        """Get the list of standard vSwitches on an ESXi host."""
        logger.info("get_host_vswitches", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_info = net_system.networkInfo
        vswitches = (net_info.vswitch if net_info else None) or []
        result = []
        for vs in vswitches:
            result.append(
                {
                    "name": vs.name,
                    "numPorts": vs.numPorts,
                    "mtu": vs.mtu,
                    "pnicKeys": list(vs.pnic) if vs.pnic else [],
                }
            )
        return {"status": "success", "host_name": host_name, "vswitches": result}

    @mcp.tool()
    @handle_tool_errors
    def get_host_vmkernel_adapters(host_name: str) -> dict[str, Any]:
        """Get the list of VMkernel adapters on an ESXi host."""
        logger.info("get_host_vmkernel_adapters", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_info = net_system.networkInfo
        vnics = (net_info.vnic if net_info else None) or []
        result = []
        for vnic in vnics:
            result.append(
                {
                    "device": vnic.device,
                    "portgroup": vnic.portgroup,
                    "ipAddress": vnic.spec.ip.ipAddress if vnic.spec and vnic.spec.ip else None,
                    "subnetMask": vnic.spec.ip.subnetMask if vnic.spec and vnic.spec.ip else None,
                    "mac": vnic.spec.mac if vnic.spec else None,
                }
            )
        return {"status": "success", "host_name": host_name, "vmkernel_adapters": result}

    @mcp.tool()
    @handle_tool_errors
    def get_host_portgroups(host_name: str) -> dict[str, Any]:
        """Get the list of standard switch port groups on an ESXi host."""
        logger.info("get_host_portgroups", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_info = net_system.networkInfo
        portgroups = (net_info.portgroup if net_info else None) or []
        result = []
        for pg in portgroups:
            result.append(
                {
                    "name": pg.spec.name if pg.spec else None,
                    "vswitchName": pg.spec.vswitchName if pg.spec else None,
                    "vlanId": pg.spec.vlanId if pg.spec else None,
                }
            )
        return {"status": "success", "host_name": host_name, "portgroups": result}

    @mcp.tool()
    @handle_tool_errors
    def get_host_physical_nics(host_name: str) -> dict[str, Any]:
        """Get the list of physical NICs on an ESXi host."""
        logger.info("get_host_physical_nics", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_info = net_system.networkInfo
        pnics = (net_info.pnic if net_info else None) or []
        result = []
        for pnic in pnics:
            link_speed = None
            if pnic.linkSpeed:
                link_speed = {
                    "speedMb": pnic.linkSpeed.speedMb,
                    "duplex": pnic.linkSpeed.duplex,
                }
            ip_info = None
            if hasattr(pnic, "spec") and pnic.spec and hasattr(pnic.spec, "ip") and pnic.spec.ip:
                ip_info = {
                    "ipAddress": pnic.spec.ip.ipAddress,
                    "subnetMask": pnic.spec.ip.subnetMask,
                }
            result.append(
                {
                    "device": pnic.device,
                    "driver": pnic.driver,
                    "mac": pnic.mac,
                    "linkSpeed": link_speed,
                    "ip": ip_info,
                }
            )
        return {"status": "success", "host_name": host_name, "physical_nics": result}

    @mcp.tool()
    @handle_tool_errors
    def list_host_services(host_name: str) -> dict[str, Any]:
        """Get the list of services on an ESXi host."""
        logger.info("list_host_services", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        service_system = cm.serviceSystem
        if service_system is None:
            return {"status": "error", "error": "serviceSystem not available"}
        services = service_system.serviceInfo.service or []
        result = []
        for svc in services:
            result.append(
                {
                    "key": svc.key,
                    "label": svc.label,
                    "running": svc.running,
                    "policy": svc.policy,
                }
            )
        return {"status": "success", "host_name": host_name, "services": result}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def start_stop_host_service(
        host_name: str,
        service_id: str,
        action: str,
    ) -> dict[str, Any]:
        """Start or stop a service on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            service_id: The service key (e.g. 'TSM-SSH').
            action: 'start' or 'stop'.
        """
        logger.info(
            "start_stop_host_service",
            host_name=host_name,
            service_id=service_id,
            action=action,
        )
        if action not in ("start", "stop"):
            return {"status": "error", "error": "action must be 'start' or 'stop'"}
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        service_system = cm.serviceSystem
        if service_system is None:
            return {"status": "error", "error": "serviceSystem not available"}
        if action == "start":
            service_system.StartService(id=service_id)
        else:
            service_system.StopService(id=service_id)
        return {
            "status": "success",
            "host_name": host_name,
            "service_id": service_id,
            "action": action,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_firewall_rules(host_name: str) -> dict[str, Any]:
        """Get the list of firewall rulesets on an ESXi host."""
        logger.info("list_host_firewall_rules", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        firewall_system = cm.firewallSystem
        if firewall_system is None:
            return {"status": "error", "error": "firewallSystem not available"}
        rulesets = firewall_system.firewallInfo.ruleset or []
        result = []
        for rs in rulesets:
            allowed_hosts = None
            if rs.allowedHosts:
                allowed_hosts = {
                    "allIp": rs.allowedHosts.allIp,
                    "ipAddress": list(rs.allowedHosts.ipAddress) if rs.allowedHosts.ipAddress else [],
                    "ipNetwork": [
                        {"network": n.network, "prefixLength": n.prefixLength}
                        for n in (rs.allowedHosts.ipNetwork or [])
                    ],
                }
            result.append(
                {
                    "key": rs.key,
                    "label": rs.label,
                    "required": rs.required,
                    "enabled": rs.enabled,
                    "allowedHosts": allowed_hosts,
                }
            )
        return {"status": "success", "host_name": host_name, "firewall_rules": result}

    @mcp.tool()
    @handle_tool_errors
    def get_host_dns_config(host_name: str) -> dict[str, Any]:
        """Get the DNS configuration of an ESXi host."""
        logger.info("get_host_dns_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        dns = net_system.dnsConfig
        if dns is None:
            return {"status": "error", "error": "dnsConfig not available"}
        return {
            "status": "success",
            "host_name": host_name,
            "dns": {
                "address": list(dns.address) if dns.address else [],
                "domainName": dns.domainName,
                "hostName": dns.hostName,
                "searchDomain": list(dns.searchDomain) if dns.searchDomain else [],
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_ntp_config(host_name: str) -> dict[str, Any]:
        """Get the NTP configuration of an ESXi host."""
        logger.info("get_host_ntp_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        dt_system = cm.dateTimeSystem
        if dt_system is None:
            return {"status": "error", "error": "dateTimeSystem not available"}
        dt_info = dt_system.dateTimeInfo
        if dt_info is None:
            return {"status": "error", "error": "dateTimeInfo not available"}
        ntp_servers = []
        if dt_info.ntpConfig and dt_info.ntpConfig.server:
            ntp_servers = list(dt_info.ntpConfig.server)
        time_zone = None
        if dt_info.timeZone:
            time_zone = dt_info.timeZone.key if hasattr(dt_info.timeZone, "key") else str(dt_info.timeZone)
        return {
            "status": "success",
            "host_name": host_name,
            "ntp": {
                "servers": ntp_servers,
                "timeZone": time_zone,
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_routing_config(host_name: str) -> dict[str, Any]:
        """Get the routing configuration of an ESXi host."""
        logger.info("get_host_routing_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        ip_route = net_system.ipRouteConfig
        default_gw = None
        if ip_route and hasattr(ip_route, "defaultGateway"):
            default_gw = ip_route.defaultGateway
        routing_table = []
        net_info = net_system.networkInfo
        if net_info and hasattr(net_info, "routeTableInfo") and net_info.routeTableInfo:
            for route in net_info.routeTableInfo.ipRoute or []:
                entry = {
                    "network": route.network if hasattr(route, "network") else None,
                    "prefixLength": route.prefixLength if hasattr(route, "prefixLength") else None,
                    "gateway": route.gateway if hasattr(route, "gateway") else None,
                    "deviceName": route.deviceName if hasattr(route, "deviceName") else None,
                }
                routing_table.append(entry)
        result: dict[str, Any] = {
            "status": "success",
            "host_name": host_name,
            "routing": {
                "defaultGateway": default_gw,
            },
        }
        if routing_table:
            result["routing"]["routeTable"] = routing_table
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_host_hardware_health(host_name: str) -> dict[str, Any]:
        """Get hardware health information of an ESXi host."""
        logger.info("get_host_hardware_health", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        runtime = getattr(host_obj, "runtime", None)
        if runtime is None:
            return {"status": "error", "error": "Host runtime not available (host may be disconnected)"}
        health_runtime = runtime.healthSystemRuntime
        if health_runtime is None:
            return {"status": "error", "error": "healthSystemRuntime not available"}
        sensors = []
        if health_runtime.systemHealthInfo and health_runtime.systemHealthInfo.numericSensorInfo:
            for s in health_runtime.systemHealthInfo.numericSensorInfo:
                sensors.append(
                    {
                        "name": s.name,
                        "currentReading": s.currentReading,
                        "unitModifier": s.unitModifier,
                        "sensorType": s.sensorType,
                        "baseUnits": s.baseUnits,
                    }
                )
        cpu_status = []
        mem_status = []
        hw_status = health_runtime.hardwareStatusInfo
        if hw_status:
            if hw_status.cpuStatusInfo:
                for cpu in hw_status.cpuStatusInfo:
                    cpu_status.append(
                        {
                            "name": cpu.name if hasattr(cpu, "name") else None,
                            "status": cpu.status.key if hasattr(cpu, "status") and cpu.status else None,
                        }
                    )
            if hw_status.memoryStatusInfo:
                for mem in hw_status.memoryStatusInfo:
                    mem_status.append(
                        {
                            "name": mem.name if hasattr(mem, "name") else None,
                            "status": mem.status.key if hasattr(mem, "status") and mem.status else None,
                        }
                    )
        result: dict[str, Any] = {
            "status": "success",
            "host_name": host_name,
            "health": {
                "sensors": sensors,
            },
        }
        if cpu_status:
            result["health"]["cpuStatus"] = cpu_status
        if mem_status:
            result["health"]["memoryStatus"] = mem_status
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enable_esxi_ssh(host_name: str) -> dict[str, Any]:
        """Enable SSH on an ESXi host by starting the TSM-SSH service."""
        logger.info("enable_esxi_ssh", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        service_system = cm.serviceSystem
        if service_system is None:
            return {"status": "error", "error": "serviceSystem not available"}
        service_system.StartService(id="TSM-SSH")
        return {
            "status": "success",
            "host_name": host_name,
            "service_id": "TSM-SSH",
            "action": "started",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def disable_esxi_ssh(host_name: str) -> dict[str, Any]:
        """Disable SSH on an ESXi host by stopping the TSM-SSH service."""
        logger.info("disable_esxi_ssh", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        service_system = cm.serviceSystem
        if service_system is None:
            return {"status": "error", "error": "serviceSystem not available"}
        service_system.StopService(id="TSM-SSH")
        return {
            "status": "success",
            "host_name": host_name,
            "service_id": "TSM-SSH",
            "action": "stopped",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_syslog_config(host_name: str) -> dict[str, Any]:
        """Get syslog configuration of an ESXi host."""
        logger.info("get_host_syslog_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        advanced_option = cm.advancedOption
        if advanced_option is None:
            return {"status": "error", "error": "advancedOption not available"}
        log_host_opts = advanced_option.QueryOptions(name="Syslog.global.logHost")
        log_dir_opts = advanced_option.QueryOptions(name="Syslog.global.logDir")
        log_host = log_host_opts[0].value if log_host_opts else None
        log_dir = log_dir_opts[0].value if log_dir_opts else None
        return {
            "status": "success",
            "host_name": host_name,
            "syslog": {
                "logHost": log_host,
                "logDir": log_dir,
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_power_policy(host_name: str) -> dict[str, Any]:
        """Get power management policy of an ESXi host."""
        logger.info("get_host_power_policy", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        power_system = cm.powerSystem
        if power_system is None:
            return {"status": "error", "error": "powerSystem not available"}
        info = power_system.info
        if info is None:
            return {"status": "error", "error": "powerSystem info not available"}
        current_policy = info.currentPolicy
        if current_policy is None:
            return {"status": "error", "error": "currentPolicy not available"}
        return {
            "status": "success",
            "host_name": host_name,
            "power_policy": {
                "key": current_policy.key,
                "name": current_policy.name,
                "shortName": current_policy.shortName,
                "description": current_policy.description,
            },
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_power_policy(host_name: str, policy_key: int) -> dict[str, Any]:
        """Set power management policy on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            policy_key: The power policy key to set.
        """
        logger.info("set_host_power_policy", host_name=host_name, policy_key=policy_key)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        power_system = cm.powerSystem
        if power_system is None:
            return {"status": "error", "error": "powerSystem not available"}
        power_system.ConfigurePowerPolicy(key=policy_key)
        return {
            "status": "success",
            "host_name": host_name,
            "policy_key": policy_key,
            "message": "Power policy updated",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_lockdown_mode(host_name: str) -> dict[str, Any]:
        """Get lockdown mode of an ESXi host."""
        logger.info("get_host_lockdown_mode", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        host_access_manager = cm.hostAccessManager
        if host_access_manager is None:
            return {"status": "error", "error": "hostAccessManager not available"}
        lockdown_mode = host_access_manager.lockdownMode
        return {
            "status": "success",
            "host_name": host_name,
            "lockdown_mode": str(lockdown_mode),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_certificate_info(host_name: str) -> dict[str, Any]:
        """Get SSL certificate details of an ESXi host."""
        logger.info("get_host_certificate_info", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        cert_manager = cm.certificateManager
        if cert_manager is None:
            return {"status": "error", "error": "certificateManager not available on this host"}
        cert_info = cert_manager.certificateInfo
        if cert_info is None:
            return {"status": "error", "error": "certificateInfo not available"}
        return {
            "status": "success",
            "host_name": host_name,
            "certificate": {
                "issuer": cert_info.issuer,
                "subject": cert_info.subject,
                "notBefore": str(cert_info.notBefore),
                "notAfter": str(cert_info.notAfter),
                "status": cert_info.status,
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_time_config(host_name: str) -> dict[str, Any]:
        """Get the current date and time of an ESXi host."""
        logger.info("get_host_time_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        dt_system = cm.dateTimeSystem
        if dt_system is None:
            return {"status": "error", "error": "dateTimeSystem not available"}
        current_time = dt_system.QueryDateTime()
        return {
            "status": "success",
            "host_name": host_name,
            "current_time": str(current_time),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_vswitch(
        host_name: str,
        vswitch_name: str,
        num_ports: int = 128,
        mtu: int = 1500,
    ) -> dict[str, Any]:
        """Create a standard vSwitch on an ESXi host."""
        logger.info("create_vswitch", host_name=host_name, vswitch_name=vswitch_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        spec = vim.host.VirtualSwitch.Specification(numPorts=num_ports, mtu=mtu)
        net_system.AddVirtualSwitch(vswitchName=vswitch_name, spec=spec)
        return {
            "status": "success",
            "host_name": host_name,
            "vswitch_name": vswitch_name,
            "num_ports": num_ports,
            "mtu": mtu,
            "operation": "create_vswitch",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_vswitch(
        host_name: str,
        vswitch_name: str,
    ) -> dict[str, Any]:
        """Remove a standard vSwitch from an ESXi host."""
        logger.info("remove_vswitch", host_name=host_name, vswitch_name=vswitch_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_system.RemoveVirtualSwitch(vswitchName=vswitch_name)
        return {
            "status": "success",
            "host_name": host_name,
            "vswitch_name": vswitch_name,
            "operation": "remove_vswitch",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def update_vswitch(
        host_name: str,
        vswitch_name: str,
        num_ports: int | None = None,
        mtu: int | None = None,
    ) -> dict[str, Any]:
        """Update settings of an existing standard vSwitch on an ESXi host."""
        logger.info("update_vswitch", host_name=host_name, vswitch_name=vswitch_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_info = net_system.networkInfo
        vswitches = (net_info.vswitch if net_info else None) or []
        current_vs = None
        for vs in vswitches:
            if vs.name == vswitch_name:
                current_vs = vs
                break
        if current_vs is None:
            return {"status": "error", "error": f"vSwitch '{vswitch_name}' not found on host '{host_name}'"}
        new_num_ports = num_ports if num_ports is not None else current_vs.numPorts
        new_mtu = mtu if mtu is not None else current_vs.mtu
        # Preserve existing spec (bridge/uplink/policy) to avoid losing configuration
        spec = current_vs.spec if current_vs.spec else vim.host.VirtualSwitch.Specification()
        spec.numPorts = new_num_ports
        spec.mtu = new_mtu
        net_system.UpdateVirtualSwitch(vswitchName=vswitch_name, spec=spec)
        return {
            "status": "success",
            "host_name": host_name,
            "vswitch_name": vswitch_name,
            "num_ports": new_num_ports,
            "mtu": new_mtu,
            "operation": "update_vswitch",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_vmkernel_adapter(
        host_name: str,
        portgroup_name: str,
        ip_address: str | None = None,
        subnet_mask: str | None = None,
        dhcp: bool = False,
        mtu: int | None = None,
    ) -> dict[str, Any]:
        """Add a VMkernel adapter to an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            portgroup_name: Name of the portgroup to attach to.
            ip_address: Static IP address (required when dhcp=False).
            subnet_mask: Subnet mask (required when dhcp=False).
            dhcp: Use DHCP for IP configuration (default False).
            mtu: MTU size (e.g. 9000 for jumbo frames). If omitted, uses default.
        """
        logger.info("add_vmkernel_adapter", host_name=host_name, portgroup_name=portgroup_name)
        if not dhcp and (not ip_address or not subnet_mask):
            return {
                "status": "error",
                "error": "ip_address and subnet_mask are required when dhcp=False",
            }
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        ip_config = vim.host.IpConfig(dhcp=dhcp)
        if not dhcp:
            ip_config.ipAddress = ip_address
            ip_config.subnetMask = subnet_mask
        spec = vim.host.VirtualNic.Specification(ip=ip_config)
        if mtu is not None:
            spec.mtu = mtu
        result_device = net_system.AddVirtualNic(portgroup=portgroup_name, nic=spec)
        return {
            "status": "success",
            "host_name": host_name,
            "portgroup_name": portgroup_name,
            "device": result_device,
            "dhcp": dhcp,
            "operation": "add_vmkernel_adapter",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_vmkernel_adapter(
        host_name: str,
        device_name: str,
    ) -> dict[str, Any]:
        """Remove a VMkernel adapter from an ESXi host (e.g. 'vmk1')."""
        logger.info("remove_vmkernel_adapter", host_name=host_name, device_name=device_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        net_system.RemoveVirtualNic(device=device_name)
        return {
            "status": "success",
            "host_name": host_name,
            "device_name": device_name,
            "operation": "remove_vmkernel_adapter",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_host_dns_config(
        host_name: str,
        dns_servers: list[str],
        hostname: str | None = None,
        domain: str | None = None,
        search_domains: list[str] | None = None,
        dhcp: bool = False,
    ) -> dict[str, Any]:
        """Set DNS configuration on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            dns_servers: List of DNS server IP addresses.
            hostname: Hostname (preserves current if omitted).
            domain: Domain name (preserves current if omitted).
            search_domains: DNS search domains (preserves current if omitted).
            dhcp: Use DHCP for DNS (default False).
        """
        logger.info("set_host_dns_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        net_system = cm.networkSystem
        if net_system is None:
            return {"status": "error", "error": "networkSystem not available"}
        # Preserve existing values for unspecified fields
        current_dns = net_system.networkInfo.dnsConfig if net_system.networkInfo else None
        dns_config = vim.host.DnsConfig(
            dhcp=dhcp,
            address=dns_servers,
            hostName=hostname or (current_dns.hostName if current_dns else ""),
            domainName=domain or (current_dns.domainName if current_dns else ""),
            searchDomain=search_domains or (current_dns.searchDomain if current_dns else []),
        )
        net_system.UpdateDnsConfig(config=dns_config)
        return {
            "status": "success",
            "host_name": host_name,
            "dns_servers": dns_servers,
            "hostname": hostname,
            "domain": domain,
            "operation": "set_host_dns_config",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_host_ntp_servers(
        host_name: str,
        ntp_servers: list[str],
    ) -> dict[str, Any]:
        """Set NTP servers on an ESXi host."""
        logger.info("set_host_ntp_servers", host_name=host_name, ntp_servers=ntp_servers)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        date_time_system = cm.dateTimeSystem
        if date_time_system is None:
            return {"status": "error", "error": "dateTimeSystem not available"}
        config = vim.host.DateTimeConfig(ntpConfig=vim.host.NtpConfig(server=ntp_servers))
        date_time_system.UpdateDateTimeConfig(config=config)
        return {
            "status": "success",
            "host_name": host_name,
            "ntp_servers": ntp_servers,
            "operation": "set_host_ntp_servers",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_host_syslog_target(
        host_name: str,
        log_host: str,
    ) -> dict[str, Any]:
        """Set the syslog remote target on an ESXi host."""
        logger.info("set_host_syslog_target", host_name=host_name, log_host=log_host)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        advanced_option = cm.advancedOption
        if advanced_option is None:
            return {"status": "error", "error": "advancedOption not available"}
        advanced_option.UpdateOptions(
            changedValue=[vim.option.OptionValue(key="Syslog.global.logHost", value=log_host)]
        )
        return {
            "status": "success",
            "host_name": host_name,
            "log_host": log_host,
            "operation": "set_host_syslog_target",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def set_host_lockdown_mode(
        host_name: str,
        mode: str,
    ) -> dict[str, Any]:
        """Set the lockdown mode of an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            mode: 'disabled', 'normal', or 'strict'.
        """
        logger.info("set_host_lockdown_mode", host_name=host_name, mode=mode)
        mode_map = {
            "disabled": vim.host.HostAccessManager.LockdownMode.lockdownDisabled,
            "normal": vim.host.HostAccessManager.LockdownMode.lockdownNormal,
            "strict": vim.host.HostAccessManager.LockdownMode.lockdownStrict,
        }
        if mode not in mode_map:
            return {"status": "error", "error": f"mode must be one of: {list(mode_map.keys())}"}
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        host_access_manager = cm.hostAccessManager
        if host_access_manager is None:
            return {"status": "error", "error": "hostAccessManager not available"}
        vim_mode = mode_map[mode]
        try:
            host_access_manager.ChangeLockdownMode(mode=vim_mode)
        except Exception as e:
            return {"status": "error", "error": f"ChangeLockdownMode failed: {e}"}
        return {
            "status": "success",
            "host_name": host_name,
            "mode": mode,
            "operation": "set_host_lockdown_mode",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enable_host_firewall_ruleset(
        host_name: str,
        ruleset_id: str,
    ) -> dict[str, Any]:
        """Enable a firewall ruleset on an ESXi host."""
        logger.info("enable_host_firewall_ruleset", host_name=host_name, ruleset_id=ruleset_id)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        firewall_system = cm.firewallSystem
        if firewall_system is None:
            return {"status": "error", "error": "firewallSystem not available"}
        firewall_system.EnableRuleset(id=ruleset_id)
        return {
            "status": "success",
            "host_name": host_name,
            "ruleset_id": ruleset_id,
            "operation": "enable_host_firewall_ruleset",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def disable_host_firewall_ruleset(
        host_name: str,
        ruleset_id: str,
    ) -> dict[str, Any]:
        """Disable a firewall ruleset on an ESXi host."""
        logger.info("disable_host_firewall_ruleset", host_name=host_name, ruleset_id=ruleset_id)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        firewall_system = cm.firewallSystem
        if firewall_system is None:
            return {"status": "error", "error": "firewallSystem not available"}
        firewall_system.DisableRuleset(id=ruleset_id)
        return {
            "status": "success",
            "host_name": host_name,
            "ruleset_id": ruleset_id,
            "operation": "disable_host_firewall_ruleset",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_host_service_policy(
        host_name: str,
        service_id: str,
        policy: str,
    ) -> dict[str, Any]:
        """Set the startup policy for a service on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            service_id: The service key (e.g. 'TSM-SSH').
            policy: 'on', 'off', or 'automatic'.
        """
        logger.info("set_host_service_policy", host_name=host_name, service_id=service_id, policy=policy)
        if policy not in ("on", "off", "automatic"):
            return {"status": "error", "error": "policy must be 'on', 'off', or 'automatic'"}
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        service_system = cm.serviceSystem
        if service_system is None:
            return {"status": "error", "error": "serviceSystem not available"}
        service_system.UpdateServicePolicy(id=service_id, policy=policy)
        return {
            "status": "success",
            "host_name": host_name,
            "service_id": service_id,
            "policy": policy,
            "operation": "set_host_service_policy",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def sync_host_time(host_name: str) -> dict[str, Any]:
        """Synchronize the clock on an ESXi host to the current UTC time."""
        logger.info("sync_host_time", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        date_time_system = cm.dateTimeSystem
        if date_time_system is None:
            return {"status": "error", "error": "dateTimeSystem not available"}
        try:
            date_time_system.UpdateDateTime(dateTime=datetime.datetime.now(datetime.timezone.utc))
        except Exception as e:
            return {"status": "error", "error": f"UpdateDateTime failed: {e}"}
        return {
            "status": "success",
            "host_name": host_name,
            "operation": "sync_host_time",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def refresh_host_ca_certificates(host_name: str) -> dict[str, Any]:
        """Refresh CA certificates and CRLs on an ESXi host."""
        logger.info("renew_host_certificate", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        cm = _get_config_manager(host_obj)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        cert_manager = cm.certificateManager
        if cert_manager is None:
            return {"status": "error", "error": "certificateManager not available on this host"}
        try:
            task = cert_manager.RefreshCACertificatesAndCRLs_Task()
            result = wait_for_task(task)
        except Exception as e:
            return {"status": "error", "error": f"RefreshCACertificatesAndCRLs_Task failed: {e}"}
        result["host_name"] = host_name
        result["operation"] = "refresh_host_ca_certificates"
        return result
