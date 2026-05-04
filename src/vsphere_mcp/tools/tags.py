from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    find_vm_with_props,
    handle_tool_errors,
    require_confirm,
    wait_for_task,
)
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_tag_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vm_annotation(vm_name: str) -> dict[str, Any]:
        """Get the annotation (notes) for a virtual machine."""
        logger.info("get_vm_annotation", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.annotation"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        return {
            "vm_name": vm_name,
            "annotation": found.get("config.annotation", ""),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="low")
    def set_vm_annotation(vm_name: str, annotation: str) -> dict[str, Any]:
        """Set the annotation (notes) for a virtual machine."""
        logger.info("set_vm_annotation", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        spec = vim.vm.ConfigSpec()
        spec.annotation = annotation
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_annotation"
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_custom_attributes() -> dict[str, Any]:
        """List all custom attribute definitions in vCenter."""
        logger.info("get_custom_attributes")
        content = client.content
        custom_fields = content.customFieldsManager
        if not custom_fields:
            return {"total": 0, "attributes": []}

        attrs = []
        for field in custom_fields.field or []:
            attrs.append(
                {
                    "key": field.key,
                    "name": field.name,
                    "managed_object_type": (str(field.managedObjectType) if field.managedObjectType else "any"),
                }
            )
        return {"total": len(attrs), "attributes": attrs}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_custom_attribute(
        attribute_name: str,
        entity_type: str | None = None,
    ) -> dict[str, Any]:
        """Create a custom attribute definition.

        Args:
            attribute_name: Name of the custom attribute.
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster'). None for all types.
        """
        logger.info("create_custom_attribute", attribute_name=attribute_name, entity_type=entity_type)
        content = client.content
        custom_fields = content.customFieldsManager
        if not custom_fields:
            return {"status": "error", "error": "Custom fields manager not available"}

        type_map: dict[str, Any] = {
            "vm": vim.VirtualMachine,
            "host": vim.HostSystem,
            "datastore": vim.Datastore,
            "cluster": vim.ClusterComputeResource,
        }

        vim_type = None
        if entity_type:
            vim_type = type_map.get(entity_type)
            if vim_type is None:
                return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}

        field = custom_fields.AddFieldDefinition(name=attribute_name, moType=vim_type)

        return {
            "status": "success",
            "operation": "create_custom_attribute",
            "attribute_name": attribute_name,
            "key": field.key,
            "entity_type": entity_type or "all",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="low")
    def set_custom_attribute_value(
        entity_type: str,
        entity_name: str,
        attribute_name: str,
        value: str,
    ) -> dict[str, Any]:
        """Set a custom attribute value on an entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster').
            entity_name: Name of the entity.
            attribute_name: Name of the custom attribute.
            value: Value to set.
        """
        logger.info(
            "set_custom_attribute_value",
            entity_type=entity_type,
            entity_name=entity_name,
            attribute_name=attribute_name,
        )
        content = client.content
        custom_fields = content.customFieldsManager
        if not custom_fields:
            return {"status": "error", "error": "Custom fields manager not available"}

        type_map: dict[str, Any] = {
            "vm": vim.VirtualMachine,
            "host": vim.HostSystem,
            "datastore": vim.Datastore,
            "cluster": vim.ClusterComputeResource,
        }
        vim_type = type_map.get(entity_type)
        if vim_type is None:
            return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}

        items = collect_properties(client, vim_type, ["name"])
        entity = None
        for item in items:
            if item.get("name") == entity_name:
                entity = item["_obj"]
                break
        if entity is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        field_key = None
        for field in custom_fields.field or []:
            if field.name == attribute_name:
                field_key = field.key
                break
        if field_key is None:
            return {"status": "error", "error": f"Custom attribute '{attribute_name}' not found"}

        custom_fields.SetField(entity=entity, key=field_key, value=value)

        return {
            "status": "success",
            "operation": "set_custom_attribute_value",
            "entity_type": entity_type,
            "entity_name": entity_name,
            "attribute_name": attribute_name,
            "value": value,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_entity_custom_attribute_values(
        entity_type: str,
        entity_name: str,
    ) -> dict[str, Any]:
        """Get all custom attribute values on an entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster').
            entity_name: Name of the entity.
        """
        logger.info(
            "get_entity_custom_attribute_values",
            entity_type=entity_type,
            entity_name=entity_name,
        )
        content = client.content
        custom_fields = content.customFieldsManager

        type_map: dict[str, Any] = {
            "vm": vim.VirtualMachine,
            "host": vim.HostSystem,
            "datastore": vim.Datastore,
            "cluster": vim.ClusterComputeResource,
        }
        vim_type = type_map.get(entity_type)
        if vim_type is None:
            return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}

        items = collect_properties(client, vim_type, ["name", "customValue"])
        entity_item = None
        for item in items:
            if item.get("name") == entity_name:
                entity_item = item
                break
        if entity_item is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        key_to_name: dict[int, str] = {}
        if custom_fields:
            for field in custom_fields.field or []:
                key_to_name[field.key] = field.name

        custom_values: list[dict[str, Any]] = []
        for cv in entity_item.get("customValue", []) or []:
            custom_values.append(
                {
                    "attribute_name": key_to_name.get(cv.key, f"key_{cv.key}"),
                    "key": cv.key,
                    "value": cv.value,
                }
            )

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "total": len(custom_values),
            "custom_attributes": custom_values,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_custom_attribute(attribute_name: str) -> dict[str, Any]:
        """Delete a custom attribute definition from vCenter.

        Args:
            attribute_name: Name of the custom attribute definition to delete.
        """
        logger.info("delete_custom_attribute", attribute_name=attribute_name)
        content = client.content
        custom_fields = content.customFieldsManager
        if not custom_fields:
            return {"status": "error", "error": "Custom fields manager not available"}

        field_key = None
        for field in custom_fields.field or []:
            if field.name == attribute_name:
                field_key = field.key
                break
        if field_key is None:
            return {"status": "error", "error": f"Custom attribute '{attribute_name}' not found"}

        custom_fields.RemoveCustomFieldDef(key=field_key)
        return {
            "status": "success",
            "operation": "delete_custom_attribute",
            "attribute_name": attribute_name,
            "key": field_key,
        }
