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

        operation: 'power_on', 'power_off', 'shutdown', 'reboot', 'suspend', 'reset'.
        """
        logger.info("batch_power_operation", vm_names=vm_names, operation=operation)
        valid_ops = {"power_on", "power_off", "shutdown", "reboot", "suspend", "reset"}
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
                    task = vm_obj.PowerOnVM_Task()
                    r = wait_for_task(task)
                elif operation == "power_off":
                    if power_state == "poweredOff":
                        results.append({"vm_name": name, "status": "already_powered_off"})
                        continue
                    task = vm_obj.PowerOffVM_Task()
                    r = wait_for_task(task)
                elif operation == "shutdown":
                    if power_state == "poweredOff":
                        results.append({"vm_name": name, "status": "already_powered_off"})
                        continue
                    vm_obj.ShutdownGuest()
                    r = {"status": "shutdown_initiated"}
                elif operation == "suspend":
                    if power_state != "poweredOn":
                        results.append({"vm_name": name, "status": "error", "error": "VM not powered on"})
                        continue
                    task = vm_obj.SuspendVM_Task()
                    r = wait_for_task(task)
                elif operation == "reset":
                    if power_state != "poweredOn":
                        results.append({"vm_name": name, "status": "error", "error": "VM not powered on"})
                        continue
                    task = vm_obj.ResetVM_Task()
                    r = wait_for_task(task)
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

        ok_statuses = {
            "success", "shutdown_initiated", "reboot_initiated",
            "already_powered_on", "already_powered_off",
            "suspend_initiated", "reset_initiated",
        }
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

    @mcp.tool()
    @handle_tool_errors
    def batch_get_vm_info(vm_names: list[str]) -> dict[str, Any]:
        """Get info for multiple VMs in one call using a single PropertyCollector fetch.

        Args:
            vm_names: List of VM names to retrieve info for.
        """
        logger.info("batch_get_vm_info", vm_names=vm_names)
        props = [
            "name",
            "runtime.powerState",
            "config.hardware.numCPU",
            "config.hardware.memoryMB",
            "config.guestFullName",
            "guest.ipAddress",
            "runtime.host",
            "config.template",
            "guest.hostName",
            "config.uuid",
            "config.files.vmPathName",
            "config.annotation",
            "summary.storage.committed",
            "summary.storage.uncommitted",
            "guest.toolsStatus",
        ]
        all_vms = collect_properties(client, vim.VirtualMachine, props)
        name_set = set(vm_names)
        vm_map = {}
        for item in all_vms:
            name = item.get("name")
            if name in name_set:
                vm_map[name] = item

        results: list[dict[str, Any]] = []
        for name in vm_names:
            found = vm_map.get(name)
            if found is None:
                results.append({"name": name, "status": "error", "error": "VM not found"})
                continue
            host_ref = found.get("runtime.host")
            committed = found.get("summary.storage.committed")
            uncommitted = found.get("summary.storage.uncommitted")
            results.append(
                {
                    "name": found.get("name"),
                    "power_state": str(found.get("runtime.powerState", "")),
                    "num_cpu": found.get("config.hardware.numCPU"),
                    "memory_mb": found.get("config.hardware.memoryMB"),
                    "guest_os": found.get("config.guestFullName"),
                    "ip_address": found.get("guest.ipAddress"),
                    "host": host_ref.name if host_ref else None,
                    "template": found.get("config.template", False),
                    "hostname": found.get("guest.hostName"),
                    "uuid": found.get("config.uuid"),
                    "path": found.get("config.files.vmPathName"),
                    "annotation": found.get("config.annotation"),
                    "storage": {
                        "committed_gb": round(committed / (1024**3), 2) if committed else 0,
                        "uncommitted_gb": round(uncommitted / (1024**3), 2) if uncommitted else 0,
                    },
                    "tools_status": str(found.get("guest.toolsStatus", "")),
                }
            )

        found_count = sum(1 for r in results if r.get("status") != "error")
        return {
            "total_requested": len(vm_names),
            "found": found_count,
            "not_found": len(vm_names) - found_count,
            "vms": results,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def batch_reconfigure_vms(
        vm_names: list[str],
        num_cpus: int | None = None,
        memory_mb: int | None = None,
    ) -> dict[str, Any]:
        """Reconfigure CPU and/or memory for multiple VMs in one call.

        Args:
            vm_names: List of VM names to reconfigure.
            num_cpus: Number of CPUs to set (optional).
            memory_mb: Memory in MB to set (optional).
        """
        logger.info("batch_reconfigure_vms", vm_names=vm_names, num_cpus=num_cpus, memory_mb=memory_mb)
        if num_cpus is None and memory_mb is None:
            return {"status": "error", "error": "At least one of num_cpus or memory_mb must be specified"}
        if num_cpus is not None and num_cpus < 1:
            return {"status": "error", "error": "num_cpus must be at least 1"}
        if memory_mb is not None and memory_mb < 4:
            return {"status": "error", "error": "memory_mb must be at least 4"}

        all_vms = collect_properties(client, vim.VirtualMachine, ["name"])
        vm_map = {item.get("name"): item for item in all_vms}

        results: list[dict[str, Any]] = []
        for name in vm_names:
            found = vm_map.get(name)
            if found is None:
                results.append({"vm_name": name, "status": "error", "error": "VM not found"})
                continue
            try:
                spec = vim.vm.ConfigSpec()
                if num_cpus is not None:
                    spec.numCPUs = num_cpus
                if memory_mb is not None:
                    spec.memoryMB = memory_mb
                task = found["_obj"].Reconfigure(spec=spec)
                r = wait_for_task(task)
                r["vm_name"] = name
                results.append(r)
            except Exception as e:
                results.append({"vm_name": name, "status": "error", "error": str(e)})

        succeeded = sum(1 for r in results if r.get("status") == "success")
        return {
            "operation": "batch_reconfigure_vms",
            "total": len(vm_names),
            "succeeded": succeeded,
            "failed": len(vm_names) - succeeded,
            "results": results,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def batch_migrate_vms(
        vm_names: list[str],
        target_host_name: str,
        target_datastore_name: str | None = None,
    ) -> dict[str, Any]:
        """Migrate (vMotion) multiple VMs to a target host and optionally a target datastore.

        Args:
            vm_names: List of VM names to migrate.
            target_host_name: Name of the destination ESXi host.
            target_datastore_name: Name of the destination datastore (optional).
        """
        logger.info(
            "batch_migrate_vms",
            vm_names=vm_names,
            target_host_name=target_host_name,
            target_datastore_name=target_datastore_name,
        )
        host_items = collect_properties(client, vim.HostSystem, ["name"])
        target_host = None
        for item in host_items:
            if item.get("name") == target_host_name:
                target_host = item["_obj"]
                break
        if target_host is None:
            return {"status": "error", "error": f"Target host '{target_host_name}' not found"}

        target_datastore = None
        if target_datastore_name is not None:
            ds_items = collect_properties(client, vim.Datastore, ["name"])
            for item in ds_items:
                if item.get("name") == target_datastore_name:
                    target_datastore = item["_obj"]
                    break
            if target_datastore is None:
                return {"status": "error", "error": f"Target datastore '{target_datastore_name}' not found"}

        all_vms = collect_properties(client, vim.VirtualMachine, ["name"])
        vm_map = {item.get("name"): item for item in all_vms}

        results: list[dict[str, Any]] = []
        for name in vm_names:
            found = vm_map.get(name)
            if found is None:
                results.append({"vm_name": name, "status": "error", "error": "VM not found"})
                continue
            try:
                relocate_spec = vim.vm.RelocateSpec(host=target_host)
                if target_datastore is not None:
                    relocate_spec.datastore = target_datastore
                task = found["_obj"].RelocateVM_Task(spec=relocate_spec)
                r = wait_for_task(task)
                r["vm_name"] = name
                results.append(r)
            except Exception as e:
                results.append({"vm_name": name, "status": "error", "error": str(e)})

        succeeded = sum(1 for r in results if r.get("status") == "success")
        return {
            "operation": "batch_migrate_vms",
            "target_host_name": target_host_name,
            "target_datastore_name": target_datastore_name,
            "total": len(vm_names),
            "succeeded": succeeded,
            "failed": len(vm_names) - succeeded,
            "results": results,
        }
