from __future__ import annotations

from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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


def register_vcenter_services_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_health() -> dict[str, Any]:
        """Get the overall health status of the vCenter appliance."""
        logger.info("get_vcenter_health")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/health/system")
        resp.raise_for_status()
        status: str = resp.json()

        return {
            "overall_status": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_vcenter_services() -> dict[str, Any]:
        """List all vCenter appliance services with their current state and startup type."""
        logger.info("list_vcenter_services")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/services")
        resp.raise_for_status()
        raw: dict[str, Any] = resp.json()

        services: list[dict[str, Any]] = []
        for service_name, info in raw.items():
            services.append(
                {
                    "name": service_name,
                    "state": info.get("state"),
                    "startup_type": info.get("startup_type"),
                    "description": info.get("description", {}).get("default_message", ""),
                }
            )

        services.sort(key=lambda s: s["name"])
        return {"total": len(services), "services": services}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def restart_vcenter_service(service_name: str) -> dict[str, Any]:
        """Restart a vCenter appliance service.

        Args:
            service_name: Name of the service to restart (e.g. 'vsphere-ui', 'vpxd').
        """
        logger.info("restart_vcenter_service", service_name=service_name)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/appliance/services/{service_name}?action=restart"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "restart_vcenter_service",
            "service_name": service_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def start_vcenter_service(service_name: str) -> dict[str, Any]:
        """Start a stopped vCenter appliance service.

        Args:
            service_name: Name of the service to start (e.g. 'vsphere-ui', 'vpxd').
        """
        logger.info("start_vcenter_service", service_name=service_name)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/appliance/services/{service_name}?action=start"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "start_vcenter_service",
            "service_name": service_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def stop_vcenter_service(service_name: str) -> dict[str, Any]:
        """Stop a running vCenter appliance service.

        Args:
            service_name: Name of the service to stop (e.g. 'vsphere-ui', 'vpxd').
        """
        logger.info("stop_vcenter_service", service_name=service_name)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/appliance/services/{service_name}?action=stop"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "stop_vcenter_service",
            "service_name": service_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_backup_status() -> dict[str, Any]:
        """List recent vCenter appliance backup jobs and their status."""
        logger.info("get_vcenter_backup_status")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/recovery/backup/jobs")
        resp.raise_for_status()
        job_ids: list[str] = resp.json()

        jobs: list[dict[str, Any]] = []
        for job_id in job_ids:
            detail_resp = session.get(
                f"{base_url}/api/appliance/recovery/backup/jobs/{job_id}"
            )
            if detail_resp.ok:
                detail = detail_resp.json()
                jobs.append(
                    {
                        "job_id": job_id,
                        "state": detail.get("state"),
                        "start_time": detail.get("start_time"),
                        "end_time": detail.get("end_time"),
                        "messages": detail.get("messages", []),
                        "progress": detail.get("progress"),
                    }
                )
            else:
                jobs.append({"job_id": job_id})

        return {"total": len(jobs), "jobs": jobs}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def trigger_vcenter_backup(
        location: str,
        location_type: str = "SFTP",
        location_user: str = "",
        location_password: str = "",
        comment: str = "",
    ) -> dict[str, Any]:
        """Trigger a vCenter appliance backup job.

        Args:
            location: Destination URI for the backup (e.g. 'sftp://backup-server/path').
            location_type: Protocol for the backup target ('SFTP', 'FTP', 'FTPS', 'HTTP', 'HTTPS', 'NFS', 'SMB').
            location_user: Username for authenticating to the backup destination.
            location_password: Password for authenticating to the backup destination.
            comment: Optional comment to attach to the backup job.
        """
        logger.info(
            "trigger_vcenter_backup",
            location=location,
            location_type=location_type,
            comment=comment,
        )
        session, base_url = _get_rest_session(client)

        body: dict[str, Any] = {
            "location": location,
            "location_type": location_type,
            "parts": ["common"],
        }
        if location_user:
            body["location_user"] = location_user
        if location_password:
            body["location_password"] = location_password
        if comment:
            body["comment"] = comment

        resp = session.post(
            f"{base_url}/api/appliance/recovery/backup/jobs",
            json=body,
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()

        return {
            "status": "success",
            "operation": "trigger_vcenter_backup",
            "job_id": result.get("id"),
            "location": location,
            "location_type": location_type,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_system_version() -> dict[str, Any]:
        """Get vCenter appliance version, build number, and installation time."""
        logger.info("get_vcenter_system_version")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/system/version")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        return {
            "version": data.get("version"),
            "build": data.get("build"),
            "type": data.get("type"),
            "product": data.get("product"),
            "summary": data.get("summary"),
            "releasedate": data.get("releasedate"),
            "install_time": data.get("install_time"),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_disk_usage() -> dict[str, Any]:
        """Get disk usage information for vCenter appliance partitions."""
        logger.info("get_vcenter_disk_usage")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/system/storage")
        resp.raise_for_status()
        partitions: list[dict[str, Any]] = resp.json()

        formatted: list[dict[str, Any]] = []
        for partition in partitions:
            disk = partition.get("disk", "")
            filesystem = partition.get("filesystem", {})
            formatted.append(
                {
                    "disk": disk,
                    "partition": partition.get("partition", ""),
                    "mount_point": filesystem.get("mount_point", ""),
                    "total_kb": filesystem.get("capacity", {}).get("total"),
                    "used_kb": filesystem.get("capacity", {}).get("used"),
                    "available_kb": filesystem.get("capacity", {}).get("available"),
                    "use_percent": filesystem.get("capacity", {}).get("percent"),
                    "filesystem_type": filesystem.get("type"),
                }
            )

        return {"total_partitions": len(formatted), "partitions": formatted}

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_network_config() -> dict[str, Any]:
        """Get network interface configuration for the vCenter appliance."""
        logger.info("get_vcenter_network_config")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/appliance/networking/interfaces")
        resp.raise_for_status()
        raw: list[dict[str, Any]] = resp.json()

        interfaces: list[dict[str, Any]] = []
        for iface in raw:
            ipv4 = iface.get("ipv4", {})
            ipv6 = iface.get("ipv6", {})
            interfaces.append(
                {
                    "name": iface.get("name"),
                    "status": iface.get("status"),
                    "mac": iface.get("mac"),
                    "ipv4_mode": ipv4.get("mode"),
                    "ipv4_address": ipv4.get("address"),
                    "ipv4_prefix": ipv4.get("prefix"),
                    "ipv4_default_gateway": ipv4.get("default_gateway"),
                    "ipv6_enabled": ipv6.get("enabled"),
                    "ipv6_addresses": ipv6.get("addresses", []),
                }
            )

        return {"total": len(interfaces), "interfaces": interfaces}
