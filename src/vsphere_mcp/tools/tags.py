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
