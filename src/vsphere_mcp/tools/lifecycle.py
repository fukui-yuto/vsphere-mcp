from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_lifecycle_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_vm(vm_name: str) -> dict[str, Any]:
        """Delete a virtual machine permanently. The VM must be powered off first."""
        logger.info("delete_vm", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before deletion"}
        task = found["_obj"].Destroy()
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "delete_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def clone_vm(
        vm_name: str,
        clone_name: str,
        power_on: bool = False,
    ) -> dict[str, Any]:
        """Clone an existing virtual machine."""
        logger.info("clone_vm", vm_name=vm_name, clone_name=clone_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = found["_obj"]
        # Get the VM's folder for placement
        folder = vm_obj.parent
        relocate_spec = vim.vm.RelocateSpec()
        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
        )
        if hasattr(folder, "CloneVM_Task"):
            task = folder.CloneVM_Task(vm_obj, name=clone_name, spec=clone_spec)
        else:
            task = vm_obj.Clone(folder=folder, name=clone_name, spec=clone_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["clone_name"] = clone_name
        result["operation"] = "clone_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def deploy_from_template(
        template_name: str,
        vm_name: str,
        power_on: bool = False,
    ) -> dict[str, Any]:
        """Deploy a new VM from a template."""
        logger.info("deploy_from_template", template_name=template_name, vm_name=vm_name)
        found = find_vm_with_props(client, template_name)
        if found is None:
            return {"status": "error", "error": f"Template '{template_name}' not found"}
        template_obj = found["_obj"]
        folder = template_obj.parent
        relocate_spec = vim.vm.RelocateSpec()
        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
        )
        task = template_obj.Clone(folder=folder, name=vm_name, spec=clone_spec)
        result = wait_for_task(task)
        result["template_name"] = template_name
        result["vm_name"] = vm_name
        result["operation"] = "deploy_from_template"
        return result
