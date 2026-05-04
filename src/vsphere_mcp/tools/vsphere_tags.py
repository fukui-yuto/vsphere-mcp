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


def register_vsphere_tag_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_tag_category(
        name: str,
        description: str = "",
        cardinality: str = "SINGLE",
        associable_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a vSphere tag category.

        Args:
            name: Name for the tag category.
            description: Optional description for the category.
            cardinality: 'SINGLE' (one tag per object) or 'MULTIPLE' (multiple tags per object).
            associable_types: List of object types this category can be associated with
                              (e.g. ['VirtualMachine', 'HostSystem']). None or empty means all types.
        """
        logger.info("create_tag_category", name=name, cardinality=cardinality)

        valid_cardinalities = {"SINGLE", "MULTIPLE"}
        if cardinality not in valid_cardinalities:
            return {"status": "error", "error": f"Invalid cardinality '{cardinality}'. Valid: {sorted(valid_cardinalities)}"}

        session, base_url = _get_rest_session(client)
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "cardinality": cardinality,
            "associable_types": associable_types if associable_types else [],
        }
        resp = session.post(f"{base_url}/api/cis/tagging/category", json=payload)
        resp.raise_for_status()
        category_id = resp.json()

        return {
            "status": "success",
            "operation": "create_tag_category",
            "category_id": category_id,
            "name": name,
            "cardinality": cardinality,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_tag_categories() -> dict[str, Any]:
        """List all vSphere tag categories with their details."""
        logger.info("list_tag_categories")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/cis/tagging/category")
        resp.raise_for_status()
        category_ids: list[str] = resp.json()

        categories = []
        for cat_id in category_ids:
            detail_resp = session.get(f"{base_url}/api/cis/tagging/category/{cat_id}")
            if detail_resp.ok:
                detail = detail_resp.json()
                categories.append({
                    "id": cat_id,
                    "name": detail.get("name"),
                    "description": detail.get("description", ""),
                    "cardinality": detail.get("cardinality"),
                    "associable_types": detail.get("associable_types", []),
                })

        return {
            "total": len(categories),
            "categories": categories,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_tag_category(category_id: str) -> dict[str, Any]:
        """Delete a vSphere tag category by ID. This also deletes all tags in the category.

        Args:
            category_id: The ID of the tag category to delete.
        """
        logger.info("delete_tag_category", category_id=category_id)

        session, base_url = _get_rest_session(client)
        resp = session.delete(f"{base_url}/api/cis/tagging/category/{category_id}")
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_tag_category",
            "category_id": category_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_tag(
        name: str,
        category_id: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a vSphere tag in a category.

        Args:
            name: Name for the tag.
            category_id: ID of the category this tag belongs to.
            description: Optional description for the tag.
        """
        logger.info("create_tag", name=name, category_id=category_id)

        session, base_url = _get_rest_session(client)
        payload = {
            "name": name,
            "category_id": category_id,
            "description": description,
        }
        resp = session.post(f"{base_url}/api/cis/tagging/tag", json=payload)
        resp.raise_for_status()
        tag_id = resp.json()

        return {
            "status": "success",
            "operation": "create_tag",
            "tag_id": tag_id,
            "name": name,
            "category_id": category_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_tags() -> dict[str, Any]:
        """List all vSphere tags with their details."""
        logger.info("list_tags")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/cis/tagging/tag")
        resp.raise_for_status()
        tag_ids: list[str] = resp.json()

        tags = []
        for tag_id in tag_ids:
            detail_resp = session.get(f"{base_url}/api/cis/tagging/tag/{tag_id}")
            if detail_resp.ok:
                detail = detail_resp.json()
                tags.append({
                    "id": tag_id,
                    "name": detail.get("name"),
                    "description": detail.get("description", ""),
                    "category_id": detail.get("category_id"),
                })

        return {
            "total": len(tags),
            "tags": tags,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_tag(tag_id: str) -> dict[str, Any]:
        """Delete a vSphere tag by ID.

        Args:
            tag_id: The ID of the tag to delete.
        """
        logger.info("delete_tag", tag_id=tag_id)

        session, base_url = _get_rest_session(client)
        resp = session.delete(f"{base_url}/api/cis/tagging/tag/{tag_id}")
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_tag",
            "tag_id": tag_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def attach_tag(
        tag_id: str,
        entity_type: str,
        entity_id: str,
    ) -> dict[str, Any]:
        """Attach a vSphere tag to an entity.

        Args:
            tag_id: ID of the tag to attach.
            entity_type: Type of the entity (e.g. 'VirtualMachine', 'HostSystem',
                         'Datastore', 'ClusterComputeResource').
            entity_id: Managed object reference ID of the entity (e.g. 'vm-42').
        """
        logger.info("attach_tag", tag_id=tag_id, entity_type=entity_type, entity_id=entity_id)

        session, base_url = _get_rest_session(client)
        payload = {
            "tag_id": tag_id,
            "object_id": {
                "type": entity_type,
                "id": entity_id,
            },
        }
        resp = session.post(
            f"{base_url}/api/cis/tagging/tag-association?action=attach",
            json=payload,
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "attach_tag",
            "tag_id": tag_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def detach_tag(
        tag_id: str,
        entity_type: str,
        entity_id: str,
    ) -> dict[str, Any]:
        """Detach a vSphere tag from an entity.

        Args:
            tag_id: ID of the tag to detach.
            entity_type: Type of the entity (e.g. 'VirtualMachine', 'HostSystem',
                         'Datastore', 'ClusterComputeResource').
            entity_id: Managed object reference ID of the entity (e.g. 'vm-42').
        """
        logger.info("detach_tag", tag_id=tag_id, entity_type=entity_type, entity_id=entity_id)

        session, base_url = _get_rest_session(client)
        payload = {
            "tag_id": tag_id,
            "object_id": {
                "type": entity_type,
                "id": entity_id,
            },
        }
        resp = session.post(
            f"{base_url}/api/cis/tagging/tag-association?action=detach",
            json=payload,
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "detach_tag",
            "tag_id": tag_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_attached_tags(entity_type: str, entity_id: str) -> dict[str, Any]:
        """List all tags attached to a vSphere entity.

        Args:
            entity_type: Type of the entity (e.g. 'VirtualMachine', 'HostSystem',
                         'Datastore', 'ClusterComputeResource').
            entity_id: Managed object reference ID of the entity (e.g. 'vm-42').
        """
        logger.info("list_attached_tags", entity_type=entity_type, entity_id=entity_id)

        session, base_url = _get_rest_session(client)
        payload = {
            "object_id": {
                "type": entity_type,
                "id": entity_id,
            },
        }
        resp = session.post(
            f"{base_url}/api/cis/tagging/tag-association?action=list-attached-tags",
            json=payload,
        )
        resp.raise_for_status()
        tag_ids: list[str] = resp.json()

        tags = []
        for tag_id in tag_ids:
            detail_resp = session.get(f"{base_url}/api/cis/tagging/tag/{tag_id}")
            if detail_resp.ok:
                detail = detail_resp.json()
                tags.append({
                    "id": tag_id,
                    "name": detail.get("name"),
                    "category_id": detail.get("category_id"),
                    "description": detail.get("description", ""),
                })

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total": len(tags),
            "tags": tags,
        }
