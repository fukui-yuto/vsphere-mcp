from __future__ import annotations

import time
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)

TASK_POLL_INTERVAL = 0.5
TASK_TIMEOUT_SEC = 300


def _find_vm_with_props(
    client: VSphereClient, vm_name: str, extra_props: list[str] | None = None
) -> dict[str, Any] | None:
    """Find a VM by name and return its object ref + requested properties."""
    props = ["name", "runtime.powerState"] + (extra_props or [])
    items = collect_properties(client, vim.VirtualMachine, props)
    for item in items:
        if item.get("name") == vm_name:
            return item
    return None


def _wait_for_task(task: vim.Task, timeout: int = TASK_TIMEOUT_SEC) -> dict[str, Any]:
    """Wait for a vSphere task to complete with polling and timeout."""
    start = time.time()
    while task.info.state in (vim.TaskInfo.State.queued, vim.TaskInfo.State.running):
        if time.time() - start > timeout:
            return {"status": "error", "message": f"Task timed out after {timeout}s"}
        time.sleep(TASK_POLL_INTERVAL)
    if task.info.state == vim.TaskInfo.State.success:
        return {"status": "success"}
    error_msg = str(task.info.error) if task.info.error else "Unknown error"
    return {"status": "error", "message": error_msg}


def register_power_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @require_confirm(danger_level="low")
    @handle_tool_errors
    def power_on_vm(vm_name: str) -> dict[str, Any]:
        """Power on a virtual machine."""
        logger.info("power_on_vm", vm_name=vm_name)
        found = _find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) == "poweredOn":
            return {"status": "already_powered_on", "vm_name": vm_name}
        task = found["_obj"].PowerOn()
        result = _wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "power_on"
        return result

    @mcp.tool()
    @require_confirm(danger_level="medium")
    @handle_tool_errors
    def power_off_vm(vm_name: str) -> dict[str, Any]:
        """Force power off a virtual machine. This is equivalent to pulling the power cord."""
        logger.info("power_off_vm", vm_name=vm_name)
        found = _find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) == "poweredOff":
            return {"status": "already_powered_off", "vm_name": vm_name}
        task = found["_obj"].PowerOff()
        result = _wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "power_off"
        return result

    @mcp.tool()
    @require_confirm(danger_level="medium")
    @handle_tool_errors
    def shutdown_vm(vm_name: str) -> dict[str, Any]:
        """Gracefully shut down a virtual machine via VMware Tools guest OS shutdown."""
        logger.info("shutdown_vm", vm_name=vm_name)
        found = _find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) == "poweredOff":
            return {"status": "already_powered_off", "vm_name": vm_name}
        found["_obj"].ShutdownGuest()
        return {"status": "shutdown_initiated", "vm_name": vm_name, "operation": "shutdown"}

    @mcp.tool()
    @require_confirm(danger_level="medium")
    @handle_tool_errors
    def reboot_vm(vm_name: str) -> dict[str, Any]:
        """Reboot a virtual machine via VMware Tools guest OS reboot."""
        logger.info("reboot_vm", vm_name=vm_name)
        found = _find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOn":
            return {"status": "error", "error": f"VM '{vm_name}' is not powered on"}
        found["_obj"].RebootGuest()
        return {"status": "reboot_initiated", "vm_name": vm_name, "operation": "reboot"}
