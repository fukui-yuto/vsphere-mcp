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


def register_appliance_update_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_appliance_update_pending() -> dict[str, Any]:
        """Get pending updates available for the vCenter appliance."""
        logger.info("get_appliance_update_pending")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/update/pending")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "pending_updates": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_update_staged() -> dict[str, Any]:
        """Get information about the currently staged vCenter appliance update."""
        logger.info("get_appliance_update_staged")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/update/staged")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "staged_update": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def stage_appliance_update(version: str) -> dict[str, Any]:
        """Stage a pending vCenter appliance update for installation.

        Staging downloads and validates the update without applying it. Run
        get_appliance_update_pending first to obtain the version identifier.

        Args:
            version: Version string of the update to stage (e.g. '8.0.2.00100').
        """
        logger.info("stage_appliance_update", version=version)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/appliance/update/pending/{version}?action=stage"
        )
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        return {
            "status": "success",
            "operation": "stage_appliance_update",
            "version": version,
            "result": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_dns_domains() -> dict[str, Any]:
        """Get the DNS search domains configured on the vCenter appliance."""
        logger.info("get_appliance_dns_domains")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/networking/dns/domains")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "dns_search_domains": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_dns_hostname() -> dict[str, Any]:
        """Get the hostname configured on the vCenter appliance."""
        logger.info("get_appliance_dns_hostname")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/networking/dns/hostname")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "hostname": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_appliance_firewall_rules() -> dict[str, Any]:
        """Get inbound firewall rules configured on the vCenter appliance."""
        logger.info("get_appliance_firewall_rules")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/networking/firewall/inbound")
        resp.raise_for_status()
        data = resp.json()

        return {
            "status": "success",
            "firewall_inbound_rules": data,
        }
