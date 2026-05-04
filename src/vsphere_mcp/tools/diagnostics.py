from __future__ import annotations

from typing import Any

import requests
import urllib3
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
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


def register_diagnostics_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def generate_support_bundle() -> dict[str, Any]:
        """Generate a vCenter appliance support bundle."""
        logger.info("generate_support_bundle")
        session, base_url = _get_rest_session(client)

        resp = session.post(f"{base_url}/api/appliance/support-bundle")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json() if resp.content else {}

        return {
            "status": "success",
            "operation": "generate_support_bundle",
            "result": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def generate_host_support_bundle(host_name: str) -> dict[str, Any]:
        """Generate an ESXi vm-support bundle for the specified host.

        Args:
            host_name: Name of the ESXi host for which to generate the support bundle.
        """
        logger.info("generate_host_support_bundle", host_name=host_name)

        items = collect_properties(client, vim.HostSystem, ["name"])
        host_obj = None
        for item in items:
            if item.get("name") == host_name:
                host_obj = item["_obj"]
                break
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        diag_manager = client.content.diagnosticManager
        if diag_manager is None:
            return {"status": "error", "error": "diagnosticManager not available"}

        task = diag_manager.GenerateLogBundles_Task(includeDefault=True, host=[host_obj])
        result = wait_for_task(task)
        if result.get("status") != "success":
            return result
        return {
            "status": "success",
            "operation": "generate_host_support_bundle",
            "host_name": host_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_ceip_status() -> dict[str, Any]:
        """Get the Customer Experience Improvement Program (CEIP) participation status."""
        logger.info("get_ceip_status")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/telemetry")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json() if resp.content else {}

        return {
            "status": "success",
            "ceip_enabled": data.get("level") != "NONE" if isinstance(data, dict) else data,
            "raw": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_ceip_status(enabled: bool) -> dict[str, Any]:
        """Set the Customer Experience Improvement Program (CEIP) participation status.

        Args:
            enabled: True to enable CEIP participation, False to disable.
        """
        logger.info("set_ceip_status", enabled=enabled)
        session, base_url = _get_rest_session(client)

        body = {"level": "BASIC" if enabled else "NONE"}
        resp = session.put(f"{base_url}/api/appliance/telemetry", json=body)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "set_ceip_status",
            "enabled": enabled,
        }

    @mcp.tool()
    @handle_tool_errors
    def validate_syslog_forwarding() -> dict[str, Any]:
        """Test syslog forwarding configuration to verify remote log hosts are reachable."""
        logger.info("validate_syslog_forwarding")
        session, base_url = _get_rest_session(client)

        resp = session.post(f"{base_url}/api/appliance/logging/forwarding?action=test")
        resp.raise_for_status()
        data: Any = resp.json() if resp.content else []

        results: list[dict[str, Any]] = []
        if isinstance(data, list):
            for entry in data:
                results.append(
                    {
                        "hostname": entry.get("hostname") if isinstance(entry, dict) else str(entry),
                        "state": entry.get("state") if isinstance(entry, dict) else None,
                        "message": entry.get("message") if isinstance(entry, dict) else None,
                    }
                )

        return {
            "status": "success",
            "total": len(results),
            "results": results,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_deployment_type() -> dict[str, Any]:
        """Get vCenter deployment type and installation information."""
        logger.info("get_vcenter_deployment_type")
        session, base_url = _get_rest_session(client)

        for path in ("/api/vcenter/deployment", "/api/vcenter/deployment/info"):
            resp = session.get(f"{base_url}{path}")
            if resp.ok:
                data: dict[str, Any] = resp.json() if resp.content else {}
                return {
                    "status": "success",
                    "deployment_type": data.get("deployment_type"),
                    "deployment_size": data.get("deployment_size"),
                    "state": data.get("state"),
                    "raw": data,
                }

        return {"status": "error", "error": "Unable to retrieve vCenter deployment info"}

    # --- Extension Management Tools ---

    @mcp.tool()
    @handle_tool_errors
    def list_extensions() -> dict[str, Any]:
        """List all registered vCenter extensions and plugins."""
        logger.info("list_extensions")
        ext_manager = client.content.extensionManager
        if ext_manager is None:
            return {"status": "error", "error": "extensionManager not available"}

        extensions: list[dict[str, Any]] = []
        for ext in ext_manager.extensionList or []:
            extensions.append(
                {
                    "key": ext.key,
                    "version": ext.version if hasattr(ext, "version") else None,
                    "description": (
                        ext.description.label
                        if hasattr(ext, "description") and ext.description and hasattr(ext.description, "label")
                        else None
                    ),
                    "company": ext.company if hasattr(ext, "company") else None,
                    "last_heartbeat_time": (
                        str(ext.lastHeartbeatTime)
                        if hasattr(ext, "lastHeartbeatTime") and ext.lastHeartbeatTime
                        else None
                    ),
                }
            )

        return {"status": "success", "total": len(extensions), "extensions": extensions}

    @mcp.tool()
    @handle_tool_errors
    def get_extension_info(extension_key: str) -> dict[str, Any]:
        """Get detailed information about a specific vCenter extension.

        Args:
            extension_key: The unique key identifying the extension (e.g. 'com.example.plugin').
        """
        logger.info("get_extension_info", extension_key=extension_key)
        ext_manager = client.content.extensionManager
        if ext_manager is None:
            return {"status": "error", "error": "extensionManager not available"}

        ext = ext_manager.FindExtension(extensionKey=extension_key)
        if ext is None:
            return {"status": "error", "error": f"Extension '{extension_key}' not found"}

        return {
            "status": "success",
            "key": ext.key,
            "version": ext.version if hasattr(ext, "version") else None,
            "description": (
                ext.description.label
                if hasattr(ext, "description") and ext.description and hasattr(ext.description, "label")
                else None
            ),
            "summary": (
                ext.description.summary
                if hasattr(ext, "description") and ext.description and hasattr(ext.description, "summary")
                else None
            ),
            "company": ext.company if hasattr(ext, "company") else None,
            "type": ext.type if hasattr(ext, "type") else None,
            "subject_name": ext.subjectName if hasattr(ext, "subjectName") else None,
            "last_heartbeat_time": (
                str(ext.lastHeartbeatTime)
                if hasattr(ext, "lastHeartbeatTime") and ext.lastHeartbeatTime
                else None
            ),
            "server": [
                {
                    "url": s.url if hasattr(s, "url") else None,
                    "type": s.type if hasattr(s, "type") else None,
                    "company": s.company if hasattr(s, "company") else None,
                }
                for s in (ext.server or [])
            ]
            if hasattr(ext, "server") and ext.server
            else [],
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def register_extension(
        key: str,
        version: str,
        description: str = "",
        company: str = "",
        server_url: str = "",
    ) -> dict[str, Any]:
        """Register a new vCenter extension/plugin.

        Args:
            key: Unique extension key (e.g. 'com.example.myplugin').
            version: Extension version string (e.g. '1.0.0').
            description: Human-readable description of the extension.
            company: Company name associated with the extension.
            server_url: Optional URL for the extension server endpoint.
        """
        logger.info("register_extension", key=key, version=version)
        ext_manager = client.content.extensionManager
        if ext_manager is None:
            return {"status": "error", "error": "extensionManager not available"}

        desc = vim.Description()
        desc.label = description or key
        desc.summary = description or key

        extension = vim.Extension()
        extension.key = key
        extension.version = version
        extension.description = desc
        if company:
            extension.company = company

        if server_url:
            server_info = vim.Extension.ServerInfo()
            server_info.url = server_url
            server_info.type = "HTTPS"
            server_info.company = company or ""
            server_info.description = desc
            server_info.adminEmail = []
            extension.server = [server_info]
        else:
            extension.server = []

        extension.client = []
        extension.taskList = []
        extension.eventList = []
        extension.faultList = []
        extension.privilegeList = []

        ext_manager.RegisterExtension(extension=extension)

        return {
            "status": "success",
            "operation": "register_extension",
            "key": key,
            "version": version,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def unregister_extension(extension_key: str) -> dict[str, Any]:
        """Unregister (remove) a vCenter extension/plugin.

        Args:
            extension_key: The unique key of the extension to remove.
        """
        logger.info("unregister_extension", extension_key=extension_key)
        ext_manager = client.content.extensionManager
        if ext_manager is None:
            return {"status": "error", "error": "extensionManager not available"}

        ext = ext_manager.FindExtension(extensionKey=extension_key)
        if ext is None:
            return {"status": "error", "error": f"Extension '{extension_key}' not found"}

        ext_manager.UnregisterExtension(extensionKey=extension_key)

        return {
            "status": "success",
            "operation": "unregister_extension",
            "extension_key": extension_key,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_extension(
        extension_key: str,
        version: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """Update metadata for an existing vCenter extension.

        Args:
            extension_key: The unique key of the extension to update.
            version: New version string. If empty, keeps the existing version.
            description: New description text. If empty, keeps the existing description.
        """
        logger.info("update_extension", extension_key=extension_key, version=version)
        ext_manager = client.content.extensionManager
        if ext_manager is None:
            return {"status": "error", "error": "extensionManager not available"}

        ext = ext_manager.FindExtension(extensionKey=extension_key)
        if ext is None:
            return {"status": "error", "error": f"Extension '{extension_key}' not found"}

        if version:
            ext.version = version
        if description:
            if not hasattr(ext, "description") or ext.description is None:
                ext.description = vim.Description()
            ext.description.label = description
            ext.description.summary = description

        ext_manager.UpdateExtension(extension=ext)

        return {
            "status": "success",
            "operation": "update_extension",
            "extension_key": extension_key,
            "version": ext.version,
        }
