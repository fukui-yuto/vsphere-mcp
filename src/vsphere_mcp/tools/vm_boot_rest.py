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


def register_vm_boot_rest_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vm_boot_device_order(vm_id: str) -> dict[str, Any]:
        """Get the boot device order for a VM via the REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
        """
        logger.info("get_vm_boot_device_order", vm_id=vm_id)
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/vm/{vm_id}/hardware/boot/device")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {
            "vm_id": vm_id,
            "total": len(data),
            "boot_device_order": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_boot_device_order(vm_id: str, devices: list[dict[str, str]]) -> dict[str, Any]:
        """Set the boot device order for a VM via the REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
            devices: Ordered list of boot device dicts. Each entry should have a 'type' field
                     (e.g. 'CDROM', 'DISK', 'ETHERNET', 'FLOPPY') and optionally device-specific fields.
        """
        logger.info("set_vm_boot_device_order", vm_id=vm_id, device_count=len(devices))
        if not devices:
            return {"status": "error", "error": "devices list must not be empty"}
        session, base_url = _get_rest_session(client)
        resp = session.put(
            f"{base_url}/api/vcenter/vm/{vm_id}/hardware/boot/device",
            json=devices,
        )
        resp.raise_for_status()
        return {
            "status": "success",
            "operation": "set_vm_boot_device_order",
            "vm_id": vm_id,
            "devices": devices,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def install_vm_tools(vm_id: str) -> dict[str, Any]:
        """Initiate VMware Tools installation on a VM via the REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
        """
        logger.info("install_vm_tools", vm_id=vm_id)
        session, base_url = _get_rest_session(client)
        resp = session.post(f"{base_url}/api/vcenter/vm/{vm_id}/tools?action=install")
        resp.raise_for_status()
        return {
            "status": "success",
            "operation": "install_vm_tools",
            "vm_id": vm_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def upgrade_vm_tools_rest(vm_id: str) -> dict[str, Any]:
        """Upgrade VMware Tools on a VM via the REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
        """
        logger.info("upgrade_vm_tools_rest", vm_id=vm_id)
        session, base_url = _get_rest_session(client)
        resp = session.post(f"{base_url}/api/vcenter/vm/{vm_id}/tools?action=upgrade")
        resp.raise_for_status()
        return {
            "status": "success",
            "operation": "upgrade_vm_tools_rest",
            "vm_id": vm_id,
        }
