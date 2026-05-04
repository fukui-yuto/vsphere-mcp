from __future__ import annotations

from typing import Any

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm

logger = get_logger(__name__)


def register_host_config_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_host_vswitches(host_name: str) -> dict[str, Any]:
        """Get the list of standard vSwitches on an ESXi host."""
        logger.info("get_host_vswitches", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            net_system = host_obj.configManager.networkSystem
            if net_system is None:
                return {"status": "error", "error": "networkSystem not available"}
            vswitches = net_system.networkInfo.vswitch or []
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get vSwitches: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_vmkernel_adapters(host_name: str) -> dict[str, Any]:
        """Get the list of VMkernel adapters on an ESXi host."""
        logger.info("get_host_vmkernel_adapters", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            net_system = host_obj.configManager.networkSystem
            if net_system is None:
                return {"status": "error", "error": "networkSystem not available"}
            vnics = net_system.networkInfo.vnic or []
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get VMkernel adapters: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_portgroups(host_name: str) -> dict[str, Any]:
        """Get the list of standard switch port groups on an ESXi host."""
        logger.info("get_host_portgroups", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            net_system = host_obj.configManager.networkSystem
            if net_system is None:
                return {"status": "error", "error": "networkSystem not available"}
            portgroups = net_system.networkInfo.portgroup or []
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get port groups: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_physical_nics(host_name: str) -> dict[str, Any]:
        """Get the list of physical NICs on an ESXi host."""
        logger.info("get_host_physical_nics", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            net_system = host_obj.configManager.networkSystem
            if net_system is None:
                return {"status": "error", "error": "networkSystem not available"}
            pnics = net_system.networkInfo.pnic or []
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get physical NICs: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def list_host_services(host_name: str) -> dict[str, Any]:
        """Get the list of services on an ESXi host."""
        logger.info("list_host_services", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            service_system = host_obj.configManager.serviceSystem
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get services: {e}"}

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
        try:
            service_system = host_obj.configManager.serviceSystem
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to {action} service '{service_id}': {e}"}

    @mcp.tool()
    @handle_tool_errors
    def list_host_firewall_rules(host_name: str) -> dict[str, Any]:
        """Get the list of firewall rulesets on an ESXi host."""
        logger.info("list_host_firewall_rules", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            firewall_system = host_obj.configManager.firewallSystem
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get firewall rules: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_dns_config(host_name: str) -> dict[str, Any]:
        """Get the DNS configuration of an ESXi host."""
        logger.info("get_host_dns_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            net_system = host_obj.configManager.networkSystem
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get DNS config: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_ntp_config(host_name: str) -> dict[str, Any]:
        """Get the NTP configuration of an ESXi host."""
        logger.info("get_host_ntp_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            dt_system = host_obj.configManager.dateTimeSystem
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get NTP config: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_routing_config(host_name: str) -> dict[str, Any]:
        """Get the routing configuration of an ESXi host."""
        logger.info("get_host_routing_config", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            net_system = host_obj.configManager.networkSystem
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get routing config: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def get_host_hardware_health(host_name: str) -> dict[str, Any]:
        """Get hardware health information of an ESXi host."""
        logger.info("get_host_hardware_health", host_name=host_name)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}
        try:
            health_runtime = host_obj.runtime.healthSystemRuntime
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
        except Exception as e:
            return {"status": "error", "error": f"Failed to get hardware health: {e}"}
