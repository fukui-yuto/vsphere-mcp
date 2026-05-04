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


def register_content_library_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_content_libraries() -> dict[str, Any]:
        """List all content libraries in vCenter."""
        logger.info("list_content_libraries")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/content/library")
        resp.raise_for_status()
        library_ids: list[str] = resp.json()

        libraries: list[dict[str, Any]] = []
        for lib_id in library_ids:
            detail_resp = session.get(f"{base_url}/api/content/library/{lib_id}")
            if detail_resp.ok:
                detail = detail_resp.json()
                libraries.append(
                    {
                        "id": lib_id,
                        "name": detail.get("name"),
                        "type": detail.get("type"),
                        "description": detail.get("description", ""),
                        "storage_backings": detail.get("storage_backings", []),
                    }
                )
            else:
                libraries.append({"id": lib_id})

        return {"total": len(libraries), "libraries": libraries}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_local_content_library(
        name: str,
        datastore_id: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a local content library backed by a datastore.

        Args:
            name: Name of the new content library.
            datastore_id: Managed object ID of the backing datastore.
            description: Optional description for the library.
        """
        logger.info("create_local_content_library", name=name, datastore_id=datastore_id)
        session, base_url = _get_rest_session(client)

        body = {
            "create_spec": {
                "name": name,
                "description": description,
                "type": "LOCAL",
                "storage_backings": [
                    {
                        "type": "DATASTORE",
                        "datastore_id": datastore_id,
                    }
                ],
            }
        }

        resp = session.post(f"{base_url}/api/content/local-library", json=body)
        resp.raise_for_status()
        library_id: str = resp.json()

        return {
            "status": "success",
            "operation": "create_local_content_library",
            "library_id": library_id,
            "name": name,
            "datastore_id": datastore_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_content_library(library_id: str) -> dict[str, Any]:
        """Delete a content library and all its items.

        Args:
            library_id: ID of the content library to delete.
        """
        logger.info("delete_content_library", library_id=library_id)
        session, base_url = _get_rest_session(client)

        resp = session.delete(f"{base_url}/api/content/local-library/{library_id}")
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_content_library",
            "library_id": library_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_library_items(library_id: str) -> dict[str, Any]:
        """List all items in a content library.

        Args:
            library_id: ID of the content library.
        """
        logger.info("list_library_items", library_id=library_id)
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/content/library/item?library_id={library_id}")
        resp.raise_for_status()
        item_ids: list[str] = resp.json()

        items: list[dict[str, Any]] = []
        for item_id in item_ids:
            detail_resp = session.get(f"{base_url}/api/content/library/item/{item_id}")
            if detail_resp.ok:
                detail = detail_resp.json()
                items.append(
                    {
                        "id": item_id,
                        "name": detail.get("name"),
                        "type": detail.get("type"),
                        "description": detail.get("description", ""),
                        "size": detail.get("size"),
                        "cached": detail.get("cached"),
                        "creation_time": detail.get("creation_time"),
                        "last_modified_time": detail.get("last_modified_time"),
                    }
                )
            else:
                items.append({"id": item_id})

        return {"library_id": library_id, "total": len(items), "items": items}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_library_item(item_id: str) -> dict[str, Any]:
        """Delete an item from a content library.

        Args:
            item_id: ID of the library item to delete.
        """
        logger.info("delete_library_item", item_id=item_id)
        session, base_url = _get_rest_session(client)

        resp = session.delete(f"{base_url}/api/content/library/item/{item_id}")
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_library_item",
            "item_id": item_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def deploy_vm_from_library_item(
        item_id: str,
        vm_name: str,
        datacenter_id: str | None = None,
        resource_pool_id: str | None = None,
        folder_id: str | None = None,
        datastore_id: str | None = None,
    ) -> dict[str, Any]:
        """Deploy a virtual machine from an OVF library item.

        Args:
            item_id: ID of the OVF library item to deploy.
            vm_name: Name to assign to the deployed VM.
            datacenter_id: Optional managed object ID of the target datacenter.
            resource_pool_id: Optional managed object ID of the target resource pool.
            folder_id: Optional managed object ID of the target VM folder.
            datastore_id: Optional managed object ID of the target datastore.
        """
        logger.info("deploy_vm_from_library_item", item_id=item_id, vm_name=vm_name)
        session, base_url = _get_rest_session(client)

        deployment_spec: dict[str, Any] = {
            "name": vm_name,
            "accept_all_EULA": True,
        }

        target: dict[str, Any] = {}
        if datacenter_id is not None:
            target["datacenter_id"] = datacenter_id
        if resource_pool_id is not None:
            target["resource_pool_id"] = resource_pool_id
        if folder_id is not None:
            target["folder_id"] = folder_id
        if datastore_id is not None:
            deployment_spec["default_datastore_id"] = datastore_id

        body = {
            "deployment_spec": deployment_spec,
            "target": target,
        }

        resp = session.post(
            f"{base_url}/api/vcenter/ovf/library-item/{item_id}?action=deploy",
            json=body,
        )
        resp.raise_for_status()
        result_data: dict[str, Any] = resp.json()

        return {
            "status": "success",
            "operation": "deploy_vm_from_library_item",
            "item_id": item_id,
            "vm_name": vm_name,
            "result": result_data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def sync_subscribed_library(library_id: str) -> dict[str, Any]:
        """Trigger a synchronization of a subscribed content library.

        Args:
            library_id: ID of the subscribed library to synchronize.
        """
        logger.info("sync_subscribed_library", library_id=library_id)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/content/subscribed-library/{library_id}?action=sync"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "sync_subscribed_library",
            "library_id": library_id,
        }
