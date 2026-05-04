from __future__ import annotations

from typing import Any

import requests
import urllib3

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


def _get_rest_session(client: VSphereClient) -> tuple[requests.Session, str]:
    """Create a REST session using vSphere credentials."""
    settings = client._settings
    base_url = f"https://{settings.host}"
    session = requests.Session()
    session.verify = not settings.ignore_ssl
    resp = session.post(f"{base_url}/api/session", auth=(settings.user, settings.password))
    resp.raise_for_status()
    token = resp.json()
    session.headers.update({"vmware-api-session-id": token})
    return session, base_url


def _find_datacenter(client: VSphereClient, dc_name: str) -> Any | None:
    """Find a datacenter by name, or return the first one if dc_name is empty."""
    items = collect_properties(client, vim.Datacenter, ["name"])
    if not dc_name:
        return items[0]["_obj"] if items else None
    for item in items:
        if item.get("name") == dc_name:
            return item["_obj"]
    return None


def register_search_index_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def find_vm_by_ip(ip_address: str, datacenter_name: str = "") -> dict[str, Any]:
        """Find a virtual machine by its IP address using the vSphere SearchIndex.

        Args:
            ip_address: The IP address to search for (must be reported by VMware Tools).
            datacenter_name: Name of the datacenter to search in. Searches all if empty.
        """
        logger.info("find_vm_by_ip", ip_address=ip_address, datacenter_name=datacenter_name)

        dc = _find_datacenter(client, datacenter_name) if datacenter_name else None
        vm = client.content.searchIndex.FindByIp(datacenter=dc, ip=ip_address, vmSearch=True)

        if vm is None:
            return {"status": "success", "found": False, "ip_address": ip_address}

        name = getattr(vm, "name", None)
        moref = str(vm)
        runtime = getattr(vm, "runtime", None)
        power_state = getattr(runtime, "powerState", None)

        return {
            "status": "success",
            "found": True,
            "ip_address": ip_address,
            "name": name,
            "moref": moref,
            "power_state": str(power_state) if power_state is not None else None,
        }

    @mcp.tool()
    @handle_tool_errors
    def find_vm_by_uuid(
        uuid: str,
        instance_uuid: bool = False,
        datacenter_name: str = "",
    ) -> dict[str, Any]:
        """Find a virtual machine by its UUID using the vSphere SearchIndex.

        Args:
            uuid: The UUID to search for (BIOS UUID or instance UUID).
            instance_uuid: If True, search by instance UUID; if False, search by BIOS UUID (default False).
            datacenter_name: Name of the datacenter to search in. Searches all if empty.
        """
        logger.info("find_vm_by_uuid", uuid=uuid, instance_uuid=instance_uuid, datacenter_name=datacenter_name)

        dc = _find_datacenter(client, datacenter_name) if datacenter_name else None
        vm = client.content.searchIndex.FindByUuid(
            datacenter=dc, uuid=uuid, vmSearch=True, instanceUuid=instance_uuid
        )

        if vm is None:
            return {"status": "success", "found": False, "uuid": uuid}

        name = getattr(vm, "name", None)
        moref = str(vm)
        runtime = getattr(vm, "runtime", None)
        power_state = getattr(runtime, "powerState", None)

        return {
            "status": "success",
            "found": True,
            "uuid": uuid,
            "instance_uuid": instance_uuid,
            "name": name,
            "moref": moref,
            "power_state": str(power_state) if power_state is not None else None,
        }

    @mcp.tool()
    @handle_tool_errors
    def find_vm_by_dns_name(dns_name: str, datacenter_name: str = "") -> dict[str, Any]:
        """Find a virtual machine by its DNS name using the vSphere SearchIndex.

        Args:
            dns_name: The fully-qualified DNS name reported by VMware Tools.
            datacenter_name: Name of the datacenter to search in. Searches all if empty.
        """
        logger.info("find_vm_by_dns_name", dns_name=dns_name, datacenter_name=datacenter_name)

        dc = _find_datacenter(client, datacenter_name) if datacenter_name else None
        vm = client.content.searchIndex.FindByDnsName(datacenter=dc, dnsName=dns_name, vmSearch=True)

        if vm is None:
            return {"status": "success", "found": False, "dns_name": dns_name}

        name = getattr(vm, "name", None)
        moref = str(vm)
        runtime = getattr(vm, "runtime", None)
        power_state = getattr(runtime, "powerState", None)

        return {
            "status": "success",
            "found": True,
            "dns_name": dns_name,
            "name": name,
            "moref": moref,
            "power_state": str(power_state) if power_state is not None else None,
        }

    @mcp.tool()
    @handle_tool_errors
    def find_by_inventory_path(inventory_path: str) -> dict[str, Any]:
        """Find any inventory entity by its full inventory path using the vSphere SearchIndex.

        Args:
            inventory_path: Full inventory path, e.g. '/DatacenterName/vm/FolderName/VMName'.
        """
        logger.info("find_by_inventory_path", inventory_path=inventory_path)

        entity = client.content.searchIndex.FindByInventoryPath(inventoryPath=inventory_path)

        if entity is None:
            return {"status": "success", "found": False, "inventory_path": inventory_path}

        entity_type = type(entity).__name__
        name = getattr(entity, "name", None)
        moref = str(entity)

        return {
            "status": "success",
            "found": True,
            "inventory_path": inventory_path,
            "entity_type": entity_type,
            "name": name,
            "moref": moref,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_alarm_with_action(
        entity_type: str,
        entity_name: str,
        alarm_name: str,
        description: str,
        metric_id: str = "",
        operator: str = "isAbove",
        yellow_threshold: int = 80,
        red_threshold: int = 90,
        action_type: str = "email",
        action_target: str = "",
    ) -> dict[str, Any]:
        """Create an alarm with a notification action on a vSphere entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster').
            entity_name: Name of the entity to attach the alarm to.
            alarm_name: Name for the new alarm.
            description: Human-readable description for the alarm.
            metric_id: Metric key for threshold alarms (e.g. 'cpu.usage.average'). Empty for state alarm.
            operator: Comparison operator: 'isAbove' or 'isBelow' (default 'isAbove').
            yellow_threshold: Warning threshold value (default 80).
            red_threshold: Critical threshold value (default 90).
            action_type: Action type: 'email' or 'snmp' (default 'email').
            action_target: Email address or SNMP community for the action.
        """
        logger.info(
            "create_alarm_with_action",
            entity_type=entity_type,
            entity_name=entity_name,
            alarm_name=alarm_name,
            action_type=action_type,
        )

        type_map: dict[str, Any] = {
            "vm": vim.VirtualMachine,
            "host": vim.HostSystem,
            "datastore": vim.Datastore,
            "cluster": vim.ClusterComputeResource,
        }
        vim_type = type_map.get(entity_type)
        if vim_type is None:
            return {"status": "error", "error": f"Invalid entity_type '{entity_type}'. Valid: {sorted(type_map.keys())}"}

        items = collect_properties(client, vim_type, ["name"])
        entity_obj = None
        for item in items:
            if item.get("name") == entity_name:
                entity_obj = item["_obj"]
                break
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        if metric_id:
            operator_map: dict[str, Any] = {
                "isAbove": vim.alarm.MetricAlarmExpression.MetricOperator.isAbove,
                "isBelow": vim.alarm.MetricAlarmExpression.MetricOperator.isBelow,
            }
            vim_operator = operator_map.get(operator)
            if vim_operator is None:
                return {"status": "error", "error": f"Invalid operator '{operator}'. Valid: {list(operator_map.keys())}"}

            metric_ref = vim.PerformanceManager.MetricId(counterId=0, instance="")
            expression: Any = vim.alarm.MetricAlarmExpression(
                metric=metric_ref,
                operator=vim_operator,
                yellow=yellow_threshold,
                red=red_threshold,
            )
        else:
            expression = vim.alarm.AndAlarmExpression(expression=[])

        if action_type == "snmp":
            inner_action: Any = vim.action.SendSNMPAction()
        else:
            inner_action = vim.action.SendEmailAction(
                toList=action_target,
                ccList="",
                subject=f"Alarm: {alarm_name}",
                body="",
            )

        alarm_action = vim.alarm.AlarmTriggeringAction(
            action=inner_action,
            transitionSpecs=[
                vim.alarm.AlarmTriggeringAction.TransitionSpec(
                    startState=vim.ManagedEntity.Status.green,
                    finalState=vim.ManagedEntity.Status.yellow,
                    repeats=False,
                ),
                vim.alarm.AlarmTriggeringAction.TransitionSpec(
                    startState=vim.ManagedEntity.Status.yellow,
                    finalState=vim.ManagedEntity.Status.red,
                    repeats=False,
                ),
            ],
        )

        spec = vim.alarm.AlarmSpec(
            name=alarm_name,
            description=description,
            enabled=True,
            expression=expression,
            action=alarm_action,
            actionFrequency=0,
            setting=vim.alarm.AlarmSetting(toleranceRange=0, reportingFrequency=300),
        )

        alarm = client.content.alarmManager.CreateAlarm(entity=entity_obj, spec=spec)

        return {
            "status": "success",
            "operation": "create_alarm_with_action",
            "alarm_name": alarm_name,
            "alarm_moref": str(alarm),
            "entity_type": entity_type,
            "entity_name": entity_name,
            "action_type": action_type,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_event_history_collectors() -> dict[str, Any]:
        """List available event history collectors and recent event counts from the event manager."""
        logger.info("list_event_history_collectors")

        event_manager = client.content.eventManager

        latest_event = getattr(event_manager, "latestEvent", None)
        latest_event_info: dict[str, Any] | None = None
        if latest_event is not None:
            latest_event_info = {
                "key": getattr(latest_event, "key", None),
                "type": type(latest_event).__name__,
                "createdTime": str(getattr(latest_event, "createdTime", None)),
                "userName": getattr(latest_event, "userName", None),
                "message": getattr(latest_event, "fullFormattedMessage", None),
            }

        description = getattr(event_manager, "description", None)
        event_type_info: list[dict[str, Any]] = []
        if description is not None:
            for et in getattr(description, "eventInfo", None) or []:
                event_type_info.append({
                    "key": getattr(et, "key", None),
                    "description": getattr(et, "description", None),
                    "category": getattr(et, "category", None),
                })

        return {
            "status": "success",
            "num_event_types": len(event_type_info),
            "latest_event": latest_event_info,
            "message": "Use create_event_history_collector (via EventManager) to query historical events",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_topology() -> dict[str, Any]:
        """Get vCenter linked mode / multi-vCenter topology nodes via the REST API."""
        logger.info("get_vcenter_topology")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/topology/nodes")
        resp.raise_for_status()
        nodes: list[dict[str, Any]] = resp.json()

        result_nodes: list[dict[str, Any]] = []
        for node in nodes:
            result_nodes.append({
                "id": node.get("node"),
                "type": node.get("type"),
                "domain": node.get("domain"),
                "site_id": node.get("site_id"),
                "replication_partner": node.get("replication_partner"),
            })

        return {
            "status": "success",
            "num_nodes": len(result_nodes),
            "nodes": result_nodes,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_solution_users() -> dict[str, Any]:
        """List solution users (service accounts) registered in vCenter via the REST API."""
        logger.info("list_solution_users")

        session, base_url = _get_rest_session(client)

        try:
            resp = session.get(f"{base_url}/api/vcenter/identity/solution-users")
            resp.raise_for_status()
            users: list[Any] = resp.json()
        except Exception:
            return {
                "status": "error",
                "error": "solution-users REST endpoint not available on this vCenter version",
            }

        result_users: list[dict[str, Any]] = []
        if isinstance(users, list):
            for user in users:
                if isinstance(user, dict):
                    result_users.append({
                        "name": user.get("name") or user.get("username"),
                        "certificate": user.get("certificate"),
                        "description": user.get("description"),
                    })
                else:
                    result_users.append({"name": str(user)})

        return {
            "status": "success",
            "num_solution_users": len(result_users),
            "solution_users": result_users,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_full_datetime_config(host_name: str) -> dict[str, Any]:
        """Get the full date/time configuration including NTP and PTP settings for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_full_datetime_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        datetime_system = getattr(cm, "dateTimeSystem", None)
        if datetime_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        datetime_info = getattr(datetime_system, "dateTimeInfo", None)
        if datetime_info is None:
            return {"status": "error", "error": "dateTimeInfo not available"}

        ntp_config = getattr(datetime_info, "ntpConfig", None)
        ntp_servers: list[str] = []
        ntp_config_file: list[str] = []
        if ntp_config is not None:
            ntp_servers = list(getattr(ntp_config, "server", None) or [])
            ntp_config_file = list(getattr(ntp_config, "configFile", None) or [])

        service_config = getattr(datetime_info, "serviceConfig", None)
        service_info: dict[str, Any] | None = None
        if service_config is not None:
            service_info = {
                "serviceRunning": getattr(service_config, "serviceRunning", None),
                "policy": getattr(service_config, "policy", None),
            }

        return {
            "status": "success",
            "host_name": host_name,
            "time_zone": getattr(datetime_info, "timeZone", {}) and {
                "key": getattr(getattr(datetime_info, "timeZone", None), "key", None),
                "name": getattr(getattr(datetime_info, "timeZone", None), "name", None),
                "offset": getattr(getattr(datetime_info, "timeZone", None), "gmtOffset", None),
            },
            "ntp_servers": ntp_servers,
            "ntp_config_file": ntp_config_file,
            "ntp_service": service_info,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_time_method(
        host_name: str,
        method: str = "ntp",
        ntp_servers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Set the time synchronization method (NTP) for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            method: Time sync method: 'ntp' (default).
            ntp_servers: List of NTP server addresses to configure (e.g. ['pool.ntp.org']).
        """
        logger.info("set_host_time_method", host_name=host_name, method=method)

        valid_methods = ("ntp",)
        if method not in valid_methods:
            return {"status": "error", "error": f"Invalid method '{method}'. Valid: {valid_methods}"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        datetime_system = getattr(cm, "dateTimeSystem", None)
        if datetime_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        ntp_config = vim.host.NtpConfig(server=ntp_servers or [])
        config = vim.host.DateTimeConfig(ntpConfig=ntp_config)
        datetime_system.UpdateDateTimeConfig(config=config)

        return {
            "status": "success",
            "operation": "set_host_time_method",
            "host_name": host_name,
            "method": method,
            "ntp_servers": ntp_servers,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_appliance_access() -> dict[str, Any]:
        """Get shell, SSH, and DCUI access settings for the vCenter appliance."""
        logger.info("get_vcenter_appliance_access")

        session, base_url = _get_rest_session(client)

        results: dict[str, Any] = {}
        for endpoint, key in [
            ("/api/appliance/access/shell", "shell"),
            ("/api/appliance/access/ssh", "ssh"),
            ("/api/appliance/access/dcui", "dcui"),
        ]:
            try:
                resp = session.get(f"{base_url}{endpoint}")
                resp.raise_for_status()
                results[key] = resp.json()
            except Exception as e:
                results[key] = {"error": str(e)}

        return {
            "status": "success",
            "shell": results.get("shell"),
            "ssh": results.get("ssh"),
            "dcui": results.get("dcui"),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vcenter_appliance_access(
        shell_enabled: bool | None = None,
        ssh_enabled: bool | None = None,
        dcui_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Set shell, SSH, and/or DCUI access settings for the vCenter appliance.

        Args:
            shell_enabled: Enable or disable shell access. None leaves current setting.
            ssh_enabled: Enable or disable SSH access. None leaves current setting.
            dcui_enabled: Enable or disable DCUI access. None leaves current setting.
        """
        logger.info(
            "set_vcenter_appliance_access",
            shell_enabled=shell_enabled,
            ssh_enabled=ssh_enabled,
            dcui_enabled=dcui_enabled,
        )

        session, base_url = _get_rest_session(client)

        changed: dict[str, bool] = {}
        endpoint_map = [
            (shell_enabled, "/api/appliance/access/shell", "shell", {"enabled": None, "timeout": 0}),
            (ssh_enabled, "/api/appliance/access/ssh", "ssh", None),
            (dcui_enabled, "/api/appliance/access/dcui", "dcui", None),
        ]

        for value, endpoint, key, extra_body in endpoint_map:
            if value is None:
                continue
            if extra_body is not None:
                body: Any = dict(extra_body)
                body["enabled"] = value
            else:
                body = value
            resp = session.put(f"{base_url}{endpoint}", json=body)
            resp.raise_for_status()
            changed[key] = value

        if not changed:
            return {"status": "success", "message": "No changes requested", "changed": {}}

        return {
            "status": "success",
            "operation": "set_vcenter_appliance_access",
            "changed": changed,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_ntp_config() -> dict[str, Any]:
        """Get the NTP server configuration for the vCenter appliance."""
        logger.info("get_vcenter_ntp_config")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/appliance/ntp")
        resp.raise_for_status()
        servers: list[str] = resp.json()

        return {
            "status": "success",
            "ntp_servers": servers,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vcenter_ntp_config(
        servers: list[str],
        mode: str = "NTP",
    ) -> dict[str, Any]:
        """Set the NTP server configuration for the vCenter appliance.

        Args:
            servers: List of NTP server addresses (e.g. ['pool.ntp.org', '0.pool.ntp.org']).
            mode: Time sync mode. Currently only 'NTP' is supported (default 'NTP').
        """
        logger.info("set_vcenter_ntp_config", servers=servers, mode=mode)

        if not servers:
            return {"status": "error", "error": "At least one NTP server must be provided"}

        session, base_url = _get_rest_session(client)
        resp = session.put(f"{base_url}/api/appliance/ntp", json=servers)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "set_vcenter_ntp_config",
            "servers": servers,
            "mode": mode,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_proxy_config() -> dict[str, Any]:
        """Get the HTTP/HTTPS proxy configuration for the vCenter appliance."""
        logger.info("get_vcenter_proxy_config")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/appliance/networking/proxy")
        resp.raise_for_status()
        raw: dict[str, Any] = resp.json()

        proxies: list[dict[str, Any]] = []
        if isinstance(raw, dict):
            for protocol, config in raw.items():
                entry: dict[str, Any] = {"protocol": protocol}
                if isinstance(config, dict):
                    entry.update({
                        "server": config.get("server"),
                        "port": config.get("port"),
                        "enabled": config.get("enabled"),
                        "username": config.get("username"),
                    })
                proxies.append(entry)

        return {
            "status": "success",
            "proxies": proxies,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_dns_config() -> dict[str, Any]:
        """Get the DNS server configuration for the vCenter appliance."""
        logger.info("get_vcenter_dns_config")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/appliance/networking/dns/servers")
        resp.raise_for_status()
        raw: dict[str, Any] = resp.json()

        return {
            "status": "success",
            "mode": raw.get("mode"),
            "servers": raw.get("servers", []),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_network_health(host_name: str) -> dict[str, Any]:
        """Get network health information for an ESXi host, including NIC and DVS health.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_network_health", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        network_system = getattr(cm, "networkSystem", None)
        if network_system is None:
            return {"status": "error", "error": "networkSystem not available on this host"}

        net_config = getattr(network_system, "networkConfig", None)
        pnics: list[dict[str, Any]] = []
        if net_config is not None:
            for pnic in getattr(net_config, "pnic", None) or []:
                pnics.append({
                    "device": getattr(pnic, "device", None),
                    "mac": getattr(pnic, "mac", None),
                    "driver": getattr(pnic, "driver", None),
                    "linkSpeed": getattr(getattr(pnic, "linkSpeed", None), "speedMb", None),
                    "wakeOnLan": getattr(pnic, "wakeOnLanSupported", None),
                })

        # Check DVS health checks for this host
        dvs_health: list[dict[str, Any]] = []
        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "runtime"])
        for dvs_item in dvs_items:
            dvs_runtime = dvs_item.get("runtime")
            if dvs_runtime is None:
                continue
            for member_runtime in getattr(dvs_runtime, "hostMemberRuntime", None) or []:
                host_ref = getattr(member_runtime, "host", None)
                if host_ref is None:
                    continue
                try:
                    if host_ref._moId == host_obj._moId:
                        dvs_health.append({
                            "dvs_name": dvs_item.get("name"),
                            "status": getattr(member_runtime, "status", None),
                            "statusDetail": getattr(member_runtime, "statusDetail", None),
                        })
                except Exception:
                    continue

        return {
            "status": "success",
            "host_name": host_name,
            "num_pnics": len(pnics),
            "pnics": pnics,
            "dvs_health": dvs_health,
        }
