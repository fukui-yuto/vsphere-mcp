from __future__ import annotations

from typing import Any

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import require_confirm
from vsphere_mcp.tools.power import _find_vm_with_props, _wait_for_task

logger = get_logger(__name__)


def register_lifecycle_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @require_confirm(danger_level="critical")
    def delete_vm(vm_name: str) -> dict[str, Any]:
        """Delete a virtual machine permanently. The VM must be powered off first."""
        logger.info("delete_vm", vm_name=vm_name)
        found = _find_vm_with_props(client, vm_name)
        if found is None:
            return {"error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"error": f"VM '{vm_name}' must be powered off before deletion"}
        task = found["_obj"].Destroy()
        result = _wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "delete_vm"
        return result
