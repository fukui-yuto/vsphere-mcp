from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    handle_tool_errors,
    require_confirm,
    wait_for_task,
)
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_batch_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def batch_power_operation(
        vm_names: list[str],
        operation: str,
    ) -> dict[str, Any]:
        """Perform power operation on multiple VMs.

        operation: 'power_on', 'power_off', 'shutdown', 'reboot'.
        """
        logger.info("batch_power_operation", vm_names=vm_names, operation=operation)
        valid_ops = {"power_on", "power_off", "shutdown", "reboot"}
        if operation not in valid_ops:
            return {
                "status": "error",
                "error": f"Invalid operation '{operation}'. Must be one of: {valid_ops}",
            }

        all_vms = collect_properties(client, vim.VirtualMachine, ["name", "runtime.powerState"])
        vm_map = {item.get("name"): item for item in all_vms}

        results: list[dict[str, Any]] = []
        for name in vm_names:
            found = vm_map.get(name)
            if found is None:
                results.append({"vm_name": name, "status": "error", "error": "VM not found"})
                continue

            vm_obj = found["_obj"]
            power_state = str(found.get("runtime.powerState", ""))

            try:
                if operation == "power_on":
                    if power_state == "poweredOn":
                        results.append({"vm_name": name, "status": "already_powered_on"})
                        continue
                    task = vm_obj.PowerOn()
                    r = wait_for_task(task)
                elif operation == "power_off":
                    if power_state == "poweredOff":
                        results.append({"vm_name": name, "status": "already_powered_off"})
                        continue
                    task = vm_obj.PowerOff()
                    r = wait_for_task(task)
                elif operation == "shutdown":
                    if power_state == "poweredOff":
                        results.append({"vm_name": name, "status": "already_powered_off"})
                        continue
                    vm_obj.ShutdownGuest()
                    r = {"status": "shutdown_initiated"}
                elif operation == "reboot":
                    if power_state != "poweredOn":
                        results.append({"vm_name": name, "status": "error", "error": "VM not powered on"})
                        continue
                    vm_obj.RebootGuest()
                    r = {"status": "reboot_initiated"}
                r["vm_name"] = name
                results.append(r)
            except Exception as e:
                results.append({"vm_name": name, "status": "error", "error": str(e)})

        ok_statuses = {"success", "shutdown_initiated", "reboot_initiated", "already_powered_on", "already_powered_off"}
        succeeded = sum(1 for r in results if r.get("status") in ok_statuses)
        return {
            "operation": operation,
            "total": len(vm_names),
            "succeeded": succeeded,
            "failed": len(vm_names) - succeeded,
            "results": results,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def batch_create_snapshots(
        vm_names: list[str],
        snapshot_name: str,
        description: str = "",
        memory: bool = False,
        quiesce: bool = False,
    ) -> dict[str, Any]:
        """Create snapshots on multiple VMs simultaneously."""
        logger.info("batch_create_snapshots", vm_names=vm_names, snapshot_name=snapshot_name)
        all_vms = collect_properties(client, vim.VirtualMachine, ["name", "runtime.powerState"])
        vm_map = {item.get("name"): item for item in all_vms}

        results: list[dict[str, Any]] = []
        for name in vm_names:
            found = vm_map.get(name)
            if found is None:
                results.append({"vm_name": name, "status": "error", "error": "VM not found"})
                continue
            try:
                task = found["_obj"].CreateSnapshot(
                    name=snapshot_name,
                    description=description,
                    memory=memory,
                    quiesce=quiesce,
                )
                r = wait_for_task(task)
                r["vm_name"] = name
                r["snapshot_name"] = snapshot_name
                results.append(r)
            except Exception as e:
                results.append({"vm_name": name, "status": "error", "error": str(e)})

        succeeded = sum(1 for r in results if r.get("status") == "success")
        return {
            "snapshot_name": snapshot_name,
            "total": len(vm_names),
            "succeeded": succeeded,
            "failed": len(vm_names) - succeeded,
            "results": results,
        }
