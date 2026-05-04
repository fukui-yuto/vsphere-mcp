from __future__ import annotations

from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

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


def register_appliance_health_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_overview() -> dict[str, Any]:
        """Get health status for all vCenter appliance subsystems."""
        logger.info("get_appliance_health_overview")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "health": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_memory() -> dict[str, Any]:
        """Get memory health status of the vCenter appliance."""
        logger.info("get_appliance_health_memory")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/mem")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "status": "success",
            "memory_health": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_cpu() -> dict[str, Any]:
        """Get CPU load health status of the vCenter appliance."""
        logger.info("get_appliance_health_cpu")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/load")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "status": "success",
            "cpu_load_health": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_storage() -> dict[str, Any]:
        """Get storage health status of the vCenter appliance."""
        logger.info("get_appliance_health_storage")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/storage")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "status": "success",
            "storage_health": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_database() -> dict[str, Any]:
        """Get database storage health status of the vCenter appliance."""
        logger.info("get_appliance_health_database")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/database-storage")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "status": "success",
            "database_storage_health": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_swap() -> dict[str, Any]:
        """Get swap health status of the vCenter appliance."""
        logger.info("get_appliance_health_swap")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/swap")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "status": "success",
            "swap_health": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_health_softwarepackages() -> dict[str, Any]:
        """Get software packages health status of the vCenter appliance."""
        logger.info("get_appliance_health_softwarepackages")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/software-packages")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "status": "success",
            "software_packages_health": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_monitoring_data(
        stat_id: str = "",
        interval: str = "HOURS2",
    ) -> dict[str, Any]:
        """Get appliance monitoring metrics.

        Args:
            stat_id: Optional monitoring statistic ID to filter results (e.g. 'mem.total').
                     Leave empty to list all available monitoring items.
            interval: Time interval for data collection. One of: MINUTES30, HOURS2,
                      HOURS24, DAYS7 (default HOURS2).
        """
        logger.info("get_appliance_monitoring_data", stat_id=stat_id, interval=interval)
        session, base_url = _get_rest_session(client)

        params: dict[str, str] = {}
        if stat_id:
            params["stat_id"] = stat_id
        if interval:
            params["interval"] = interval

        resp = session.get(f"{base_url}/api/appliance/monitoring", params=params)
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "stat_id": stat_id,
            "interval": interval,
            "data": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_system_time() -> dict[str, Any]:
        """Get the current system time of the vCenter appliance."""
        logger.info("get_appliance_system_time")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/system/time")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        return {
            "status": "success",
            "system_time": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_timezone() -> dict[str, Any]:
        """Get the configured timezone of the vCenter appliance."""
        logger.info("get_appliance_timezone")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/system/time/timezone")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "timezone": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_uptime() -> dict[str, Any]:
        """Get the uptime of the vCenter appliance in seconds."""
        logger.info("get_appliance_uptime")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/system/uptime")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "uptime_seconds": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def shutdown_reboot_appliance(
        action: str = "reboot",
        reason: str = "",
        delay: int = 0,
    ) -> dict[str, Any]:
        """Shutdown or reboot the vCenter appliance.

        Args:
            action: Action to perform — "reboot" (default) or "shutdown".
            reason: Human-readable reason for the action, included in audit logs.
            delay: Delay in minutes before the action is performed (default 0).
        """
        logger.info("shutdown_reboot_appliance", action=action, reason=reason, delay=delay)

        valid_actions = ("reboot", "shutdown")
        if action not in valid_actions:
            return {
                "status": "error",
                "error": f"action must be one of: {', '.join(valid_actions)}",
            }

        session, base_url = _get_rest_session(client)

        body: dict[str, Any] = {"delay": delay}
        if reason:
            body["reason"] = reason

        if action == "reboot":
            endpoint = f"{base_url}/api/appliance/shutdown/reboot"
        else:
            endpoint = f"{base_url}/api/appliance/shutdown/poweroff"

        resp = session.post(endpoint, json=body)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "shutdown_reboot_appliance",
            "action": action,
            "delay_minutes": delay,
            "reason": reason,
        }
