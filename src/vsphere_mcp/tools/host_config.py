from __future__ import annotations

from typing import Any

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm

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
        """Enable SSH on an ESXi host.

        [HIGH RISK] Requires confirm=True to execute.
        """
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
        """Disable SSH on an ESXi host.

        [HIGH RISK] Requires confirm=True to execute.
        """
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

        [MEDIUM RISK] Requires confirm=True to execute.
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
        cm = getattr(host_obj, "configManager", None)
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
