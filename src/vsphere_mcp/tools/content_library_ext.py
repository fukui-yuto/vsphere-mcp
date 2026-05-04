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


def register_content_library_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_subscribed_library(
        name: str,
        subscription_url: str,
        datastore_id: str,
        on_demand: bool = True,
        username: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        """Create a subscribed content library that syncs from a remote subscription URL.

        Args:
            name: Name of the new subscribed library.
            subscription_url: URL of the remote library subscription endpoint.
            datastore_id: Managed object ID of the backing datastore.
            on_demand: If True, library items are downloaded only when needed.
            username: Optional username for authenticated subscription sources.
            password: Optional password for authenticated subscription sources.
        """
        logger.info(
            "create_subscribed_library",
            name=name,
            subscription_url=subscription_url,
            datastore_id=datastore_id,
            on_demand=on_demand,
        )
        session, base_url = _get_rest_session(client)

        subscription_info: dict[str, Any] = {
            "subscription_url": subscription_url,
            "on_demand": on_demand,
            "automatic_sync_enabled": not on_demand,
        }
        if username is not None:
            subscription_info["authentication_method"] = "BASIC"
            subscription_info["user_name"] = username
            subscription_info["password"] = password
        else:
            subscription_info["authentication_method"] = "NONE"

        body = {
            "name": name,
            "type": "SUBSCRIBED",
            "storage_backings": [
                {
                    "type": "DATASTORE",
                    "datastore_id": datastore_id,
                }
            ],
            "subscription_info": subscription_info,
        }

        resp = session.post(f"{base_url}/api/content/subscribed-library", json=body)
        resp.raise_for_status()
        library_id: str = resp.json()

        return {
            "status": "success",
            "operation": "create_subscribed_library",
            "library_id": library_id,
            "name": name,
            "subscription_url": subscription_url,
            "datastore_id": datastore_id,
            "on_demand": on_demand,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def publish_library(library_id: str) -> dict[str, Any]:
        """Publish a local content library so it can be subscribed to by other vCenters.

        Args:
            library_id: ID of the local content library to publish.
        """
        logger.info("publish_library", library_id=library_id)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/content/local-library/{library_id}?action=publish"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "publish_library",
            "library_id": library_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_library_subscription_info(library_id: str) -> dict[str, Any]:
        """Get subscription details for a subscribed content library.

        Args:
            library_id: ID of the subscribed content library.
        """
        logger.info("get_library_subscription_info", library_id=library_id)
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/content/subscribed-library/{library_id}")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        sub_info = data.get("subscription_info", {})
        return {
            "library_id": library_id,
            "name": data.get("name"),
            "subscription_url": sub_info.get("subscription_url"),
            "on_demand": sub_info.get("on_demand"),
            "automatic_sync_enabled": sub_info.get("automatic_sync_enabled"),
            "authentication_method": sub_info.get("authentication_method"),
            "last_sync_time": data.get("last_sync_time"),
            "creation_time": data.get("creation_time"),
            "last_modified_time": data.get("last_modified_time"),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_library_subscription(
        library_id: str,
        on_demand: bool | None = None,
        automatic_sync: bool | None = None,
    ) -> dict[str, Any]:
        """Update subscription settings for a subscribed content library.

        Args:
            library_id: ID of the subscribed content library to update.
            on_demand: If True, items are downloaded only when needed. If False, all items are pre-downloaded.
            automatic_sync: If True, the library automatically syncs on a schedule.
        """
        logger.info(
            "update_library_subscription",
            library_id=library_id,
            on_demand=on_demand,
            automatic_sync=automatic_sync,
        )
        session, base_url = _get_rest_session(client)

        subscription_info: dict[str, Any] = {}
        if on_demand is not None:
            subscription_info["on_demand"] = on_demand
        if automatic_sync is not None:
            subscription_info["automatic_sync_enabled"] = automatic_sync

        body: dict[str, Any] = {}
        if subscription_info:
            body["subscription_info"] = subscription_info

        resp = session.patch(
            f"{base_url}/api/content/subscribed-library/{library_id}",
            json=body,
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "update_library_subscription",
            "library_id": library_id,
            "updated": subscription_info,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def sync_library_item(library_id: str, item_id: str) -> dict[str, Any]:
        """Sync a single item in a subscribed content library.

        Args:
            library_id: ID of the subscribed content library containing the item.
            item_id: ID of the library item to synchronize.
        """
        logger.info("sync_library_item", library_id=library_id, item_id=item_id)
        session, base_url = _get_rest_session(client)

        resp = session.post(
            f"{base_url}/api/content/subscribed-library/{library_id}/item/{item_id}?action=sync"
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "sync_library_item",
            "library_id": library_id,
            "item_id": item_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_library_item(
        library_id: str,
        name: str,
        item_type: str = "ovf",
        description: str = "",
    ) -> dict[str, Any]:
        """Create an empty item in a content library.

        Args:
            library_id: ID of the content library in which to create the item.
            name: Name of the new library item.
            item_type: Type of the library item (e.g. 'ovf', 'iso', 'vm-template').
            description: Optional description for the library item.
        """
        logger.info(
            "create_library_item",
            library_id=library_id,
            name=name,
            item_type=item_type,
        )
        session, base_url = _get_rest_session(client)

        body = {
            "library_id": library_id,
            "name": name,
            "type": item_type,
            "description": description,
        }

        resp = session.post(f"{base_url}/api/content/library/item", json=body)
        resp.raise_for_status()
        item_id: str = resp.json()

        return {
            "status": "success",
            "operation": "create_library_item",
            "item_id": item_id,
            "library_id": library_id,
            "name": name,
            "type": item_type,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="low")
    def update_library_item_metadata(
        item_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update the metadata (name, description) of a content library item.

        Args:
            item_id: ID of the library item to update.
            name: New name for the library item.
            description: New description for the library item.
        """
        logger.info("update_library_item_metadata", item_id=item_id, name=name)
        session, base_url = _get_rest_session(client)

        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description

        resp = session.patch(f"{base_url}/api/content/library/item/{item_id}", json=body)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "update_library_item_metadata",
            "item_id": item_id,
            "updated": body,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_library_item_files(item_id: str) -> dict[str, Any]:
        """List all files contained in a content library item.

        Args:
            item_id: ID of the content library item.
        """
        logger.info("get_library_item_files", item_id=item_id)
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/content/library/item/{item_id}/file")
        resp.raise_for_status()
        raw_files: list[dict[str, Any]] = resp.json()

        files: list[dict[str, Any]] = []
        for f in raw_files:
            checksum_info = f.get("checksum_info", {})
            files.append(
                {
                    "name": f.get("name"),
                    "size": f.get("size"),
                    "version": f.get("version"),
                    "checksum_algorithm": checksum_info.get("algorithm"),
                    "checksum_value": checksum_info.get("checksum"),
                    "cached": f.get("cached"),
                }
            )

        return {
            "item_id": item_id,
            "total": len(files),
            "files": files,
        }
