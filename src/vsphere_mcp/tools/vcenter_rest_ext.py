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


def register_vcenter_rest_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_content_registries() -> dict[str, Any]:
        """List Harbor container registries registered with vCenter.

        Returns all Harbor registry instances configured in the vCenter content registry.
        """
        logger.info("list_content_registries")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/content/registries/harbor")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"total": len(data), "registries": data}

    @mcp.tool()
    @handle_tool_errors
    def get_datastore_default_policy(datastore_id: str) -> dict[str, Any]:
        """Get the default storage policy for a datastore.

        Args:
            datastore_id: Managed object ID of the datastore (e.g. 'datastore-10').
        """
        logger.info("get_datastore_default_policy", datastore_id=datastore_id)
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/datastore/{datastore_id}/default-policy")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return {"datastore_id": datastore_id, "default_policy": data}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def mount_iso_to_vm_rest(vm_id: str, library_item_id: str) -> dict[str, Any]:
        """Mount an ISO image from a content library item to a VM's CD-ROM via REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
            library_item_id: ID of the content library item containing the ISO.
        """
        logger.info("mount_iso_to_vm_rest", vm_id=vm_id, library_item_id=library_item_id)
        session, base_url = _get_rest_session(client)
        body = {"vm": vm_id, "library_item_id": library_item_id}
        resp = session.post(f"{base_url}/api/vcenter/iso/image", json=body)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        return {
            "status": "success",
            "operation": "mount_iso_to_vm_rest",
            "vm_id": vm_id,
            "library_item_id": library_item_id,
            "result": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def unmount_iso_from_vm_rest(vm_id: str, cdrom_key: str) -> dict[str, Any]:
        """Unmount an ISO image from a VM's CD-ROM via REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
            cdrom_key: Key identifying the CD-ROM device to unmount.
        """
        logger.info("unmount_iso_from_vm_rest", vm_id=vm_id, cdrom_key=cdrom_key)
        session, base_url = _get_rest_session(client)
        body = {"vm": vm_id, "cdrom": cdrom_key}
        resp = session.post(f"{base_url}/api/vcenter/iso/image?action=unmount", json=body)
        resp.raise_for_status()
        return {
            "status": "success",
            "operation": "unmount_iso_from_vm_rest",
            "vm_id": vm_id,
            "cdrom_key": cdrom_key,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_hvc_links() -> dict[str, Any]:
        """List Hybrid Linked Mode (HVC) links between vCenter instances."""
        logger.info("get_hvc_links")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/hvc/links")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"total": len(data), "hvc_links": data}

    @mcp.tool()
    @handle_tool_errors
    def list_consumption_domains() -> dict[str, Any]:
        """List consumption domain zones configured in vCenter."""
        logger.info("list_consumption_domains")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/consumption-domains/zones")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"total": len(data), "zones": data}

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_system_config() -> dict[str, Any]:
        """Get vCenter deployment and system configuration information."""
        logger.info("get_vcenter_system_config")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/deployment")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return {"deployment_info": data}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def deploy_vm_from_library_template(
        template_library_item_id: str,
        name: str,
        placement: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Deploy a new VM from a VM template stored in a content library.

        Args:
            template_library_item_id: ID of the VM template library item.
            name: Name for the newly deployed VM.
            placement: Optional placement spec dict (e.g. {'resource_pool': 'resgroup-10', 'folder': 'group-v5'}).
        """
        logger.info(
            "deploy_vm_from_library_template",
            template_library_item_id=template_library_item_id,
            name=name,
        )
        session, base_url = _get_rest_session(client)
        body: dict[str, Any] = {
            "name": name,
            "placement": placement or {},
        }
        resp = session.post(
            f"{base_url}/api/vcenter/vm-template/library-items/{template_library_item_id}?action=deploy",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        return {
            "status": "success",
            "operation": "deploy_vm_from_library_template",
            "template_library_item_id": template_library_item_id,
            "name": name,
            "result": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vm_guest_power_state_rest(vm_id: str) -> dict[str, Any]:
        """Get the guest OS power state for a VM via REST API.

        Args:
            vm_id: Managed object ID of the VM (e.g. 'vm-123').
        """
        logger.info("get_vm_guest_power_state_rest", vm_id=vm_id)
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/vm/{vm_id}/guest/power")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return {"vm_id": vm_id, "guest_power_state": data}

    @mcp.tool()
    @handle_tool_errors
    def get_storage_policy_entity_compliance(entities: list[str] | None = None) -> dict[str, Any]:
        """Get storage policy compliance status for VM entities.

        Args:
            entities: Optional list of VM managed object IDs to filter results.
        """
        logger.info("get_storage_policy_entity_compliance", entity_count=len(entities or []))
        session, base_url = _get_rest_session(client)
        params: dict[str, Any] = {}
        if entities:
            params["vms"] = entities
        resp = session.get(
            f"{base_url}/api/vcenter/storage/policies/entities/compliance",
            params=params,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return {"compliance_data": data}

    @mcp.tool()
    @handle_tool_errors
    def list_vcenter_networks_rest(filter_type: str = "") -> dict[str, Any]:
        """List networks visible in vCenter via REST API.

        Args:
            filter_type: Optional network type filter (e.g. 'STANDARD_PORTGROUP', 'DISTRIBUTED_PORTGROUP', 'OPAQUE_NETWORK').
        """
        logger.info("list_vcenter_networks_rest", filter_type=filter_type)
        session, base_url = _get_rest_session(client)
        params: dict[str, Any] = {}
        if filter_type:
            params["filter.types"] = filter_type
        resp = session.get(f"{base_url}/api/vcenter/network", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"total": len(data), "networks": data}
