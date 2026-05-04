from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    find_host_by_name,
    find_vm_with_props,
    handle_tool_errors,
    require_confirm,
    wait_for_task,
)

logger = get_logger(__name__)


def register_migration_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def migrate_vm(vm_name: str, target_host: str) -> dict[str, Any]:
        """Migrate (vMotion) a virtual machine to a different ESXi host."""
        logger.info("migrate_vm", vm_name=vm_name, target_host=target_host)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        host = find_host_by_name(client, target_host)
        if host is None:
            return {"status": "error", "error": f"Host '{target_host}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOn":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered on for vMotion"}
        relocate_spec = vim.vm.RelocateSpec(host=host)
        task = found["_obj"].Relocate(spec=relocate_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["target_host"] = target_host
        result["operation"] = "migrate_vm"
        return result
