from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_datacenter_by_name(client: VSphereClient, datacenter_name: str) -> Any | None:
    """Find a datacenter object by name."""
    items = collect_properties(client, vim.Datacenter, ["name"])
    for item in items:
        if item.get("name") == datacenter_name:
            return item["_obj"]
    return None


def _find_host_by_name(client: VSphereClient, host_name: str) -> Any | None:
    """Find an ESXi host managed object by name."""
    items = collect_properties(client, vim.HostSystem, ["name"])
    for item in items:
        if item.get("name") == host_name:
            return item["_obj"]
    return None


def register_vm_ops_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def query_vmotion_compatibility(vm_name: str, target_host: str) -> dict[str, Any]:
        """Check vMotion compatibility between a VM and a target ESXi host.

        Queries the vSphere provisioning checker to identify any compatibility
        issues that would prevent a live migration (vMotion) to the target host.

        Args:
            vm_name: Name of the VM to check.
            target_host: Name of the target ESXi host.
        """
        logger.info("query_vmotion_compatibility", vm_name=vm_name, target_host=target_host)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        host_obj = _find_host_by_name(client, target_host)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{target_host}' not found"}

        checker = getattr(client.content, "vmProvisioningChecker", None)
        if checker is None:
            return {"status": "error", "error": "vmProvisioningChecker not available on this vCenter"}

        task = checker.CheckMigrate_Task(
            vm=found["_obj"],
            host=host_obj,
            testType=["sourceTests", "destinationTests", "compatibilityTests"],
        )
        task_result = wait_for_task(task)
        if task_result.get("status") != "success":
            return task_result

        issues: list[dict[str, Any]] = []
        raw_result = getattr(task.info, "result", None)
        if raw_result:
            for check_result in raw_result:
                for warning in getattr(check_result, "warning", []) or []:
                    issues.append({"severity": "warning", "message": str(warning.msg) if hasattr(warning, "msg") else str(warning)})
                for error in getattr(check_result, "error", []) or []:
                    issues.append({"severity": "error", "message": str(error.msg) if hasattr(error, "msg") else str(error)})

        return {
            "status": "success",
            "vm_name": vm_name,
            "target_host": target_host,
            "compatible": len([i for i in issues if i["severity"] == "error"]) == 0,
            "issues": issues,
            "issue_count": len(issues),
        }

    @mcp.tool()
    @handle_tool_errors
    def check_migrate(vm_name: str, target_host: str = "", target_datastore: str = "") -> dict[str, Any]:
        """Check migration feasibility for a VM to a target host and/or datastore.

        Uses the vCenter provisioning checker to validate that the planned
        migration would succeed, returning any warnings or blocking errors.

        Args:
            vm_name: Name of the VM to check migration for.
            target_host: Name of the target ESXi host (optional).
            target_datastore: Name of the target datastore (optional).
        """
        logger.info("check_migrate", vm_name=vm_name, target_host=target_host, target_datastore=target_datastore)

        if not target_host and not target_datastore:
            return {"status": "error", "error": "At least one of target_host or target_datastore must be specified"}

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        checker = getattr(client.content, "vmProvisioningChecker", None)
        if checker is None:
            return {"status": "error", "error": "vmProvisioningChecker not available on this vCenter"}

        kwargs: dict[str, Any] = {"vm": found["_obj"]}

        if target_host:
            host_obj = _find_host_by_name(client, target_host)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{target_host}' not found"}
            kwargs["host"] = host_obj

        if target_datastore:
            ds_items = collect_properties(client, vim.Datastore, ["name"])
            ds_obj = next((d["_obj"] for d in ds_items if d.get("name") == target_datastore), None)
            if ds_obj is None:
                return {"status": "error", "error": f"Datastore '{target_datastore}' not found"}
            kwargs["datastore"] = ds_obj

        task = checker.CheckMigrate_Task(**kwargs)
        task_result = wait_for_task(task)
        if task_result.get("status") != "success":
            return task_result

        warnings: list[str] = []
        errors: list[str] = []
        raw_result = getattr(task.info, "result", None)
        if raw_result:
            for check_result in raw_result:
                for w in getattr(check_result, "warning", []) or []:
                    warnings.append(str(w.msg) if hasattr(w, "msg") else str(w))
                for e in getattr(check_result, "error", []) or []:
                    errors.append(str(e.msg) if hasattr(e, "msg") else str(e))

        return {
            "status": "success",
            "vm_name": vm_name,
            "target_host": target_host or None,
            "target_datastore": target_datastore or None,
            "feasible": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def standby_guest(vm_name: str) -> dict[str, Any]:
        """Put the guest OS of a virtual machine into standby (sleep) mode.

        Requires VMware Tools to be installed and running in the guest.

        Args:
            vm_name: Name of the VM whose guest OS should enter standby.
        """
        logger.info("standby_guest", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, ["guest.toolsRunningStatus", "runtime.powerState"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOn":
            return {"status": "error", "error": f"VM '{vm_name}' is not powered on"}

        tools_status = found.get("guest.toolsRunningStatus", "")
        if str(tools_status) != "guestToolsRunning":
            return {
                "status": "error",
                "error": f"VMware Tools is not running on VM '{vm_name}'. Standby requires VMware Tools.",
            }

        found["_obj"].StandbyGuest()
        return {
            "status": "success",
            "vm_name": vm_name,
            "operation": "standby_guest",
            "message": "Guest standby initiated",
        }

    @mcp.tool()
    @handle_tool_errors
    def acquire_vmrc_ticket(vm_name: str, ticket_type: str = "vmrc") -> dict[str, Any]:
        """Acquire a remote console ticket for a virtual machine.

        Returns a ticket that can be used to open a VMware Remote Console (VMRC)
        or WebMKS session to the VM's console.

        Args:
            vm_name: Name of the VM to acquire a ticket for.
            ticket_type: Type of ticket to acquire. Common values: 'vmrc', 'webmks', 'mks'.
        """
        logger.info("acquire_vmrc_ticket", vm_name=vm_name, ticket_type=ticket_type)

        valid_types = {"vmrc", "webmks", "mks"}
        if ticket_type not in valid_types:
            return {
                "status": "error",
                "error": f"ticket_type must be one of: {', '.join(sorted(valid_types))}",
            }

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        ticket = found["_obj"].AcquireTicket(ticketType=ticket_type)
        return {
            "status": "success",
            "vm_name": vm_name,
            "ticket_type": ticket_type,
            "ticket": getattr(ticket, "ticket", None),
            "host": getattr(ticket, "host", None),
            "port": getattr(ticket, "port", None),
            "ssl_thumbprint": getattr(ticket, "sslThumbprint", None),
            "cf_ticket": getattr(ticket, "cfgFile", None),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vm_disk_chain_info(vm_name: str) -> dict[str, Any]:
        """Get the disk backing chain (snapshot parent chain) for all virtual disks of a VM.

        Walks the backing.parent chain for each VirtualDisk to reveal the full
        delta/snapshot chain from the current disk back to the base VMDK.

        Args:
            vm_name: Name of the VM to inspect disk chains for.
        """
        logger.info("get_vm_disk_chain_info", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        disk_chains: list[dict[str, Any]] = []

        for dev in devices:
            if not isinstance(dev, vim.vm.device.VirtualDisk):
                continue

            label = dev.deviceInfo.label if dev.deviceInfo else None
            chain: list[dict[str, Any]] = []
            backing = getattr(dev, "backing", None)
            depth = 0

            while backing is not None and depth < 32:
                entry: dict[str, Any] = {
                    "depth": depth,
                    "file_name": getattr(backing, "fileName", None),
                    "datastore": getattr(getattr(backing, "datastore", None), "name", None),
                    "disk_mode": getattr(backing, "diskMode", None),
                    "thin_provisioned": getattr(backing, "thinProvisioned", None),
                    "content_id": getattr(backing, "contentId", None),
                    "change_id": getattr(backing, "changeId", None),
                }
                chain.append(entry)
                backing = getattr(backing, "parent", None)
                depth += 1

            disk_chains.append({
                "label": label,
                "capacity_kb": dev.capacityInKB,
                "chain_depth": len(chain),
                "chain": chain,
            })

        return {
            "status": "success",
            "vm_name": vm_name,
            "disk_count": len(disk_chains),
            "disks": disk_chains,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def shrink_vm_disk(vm_name: str, disk_path: str) -> dict[str, Any]:
        """Shrink a thin-provisioned virtual disk to reclaim unused space.

        Reclaims zero-filled blocks in the VMDK, reducing the file size on the
        datastore. The disk_path must be a datastore path such as
        '[datastore] vm/vm.vmdk'.

        Args:
            vm_name: Name of the VM owning the disk (informational).
            disk_path: Datastore path of the VMDK to shrink (e.g. '[ds] vm/disk.vmdk').
        """
        logger.info("shrink_vm_disk", vm_name=vm_name, disk_path=disk_path)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        task = vdm.ShrinkVirtualDisk_Task(name=disk_path, copy=False)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["disk_path"] = disk_path
        result["operation"] = "shrink_vm_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def defragment_vm_disk(disk_path: str, datacenter_name: str = "") -> dict[str, Any]:
        """Defragment a virtual disk to consolidate free space.

        Defragmentation reorganises the blocks within a VMDK without changing its
        provisioned size. Specify a datacenter name when the path would be
        ambiguous across datacenters.

        Args:
            disk_path: Datastore path of the VMDK to defragment (e.g. '[ds] vm/disk.vmdk').
            datacenter_name: Optional datacenter name to scope the disk lookup.
        """
        logger.info("defragment_vm_disk", disk_path=disk_path, datacenter_name=datacenter_name)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        dc_obj = None
        if datacenter_name:
            dc_obj = _find_datacenter_by_name(client, datacenter_name)
            if dc_obj is None:
                return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        task = vdm.DefragmentVirtualDisk_Task(name=disk_path, datacenter=dc_obj)
        result = wait_for_task(task)
        result["disk_path"] = disk_path
        result["datacenter_name"] = datacenter_name or None
        result["operation"] = "defragment_vm_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def inflate_vm_disk(disk_path: str, datacenter_name: str = "") -> dict[str, Any]:
        """Inflate a thin-provisioned virtual disk to eagerly zeroed thick format.

        Converting thin to thick (eager zeroed) pre-allocates all space on the
        datastore and improves performance. This operation cannot be reversed
        without a Storage vMotion.

        Args:
            disk_path: Datastore path of the VMDK to inflate (e.g. '[ds] vm/disk.vmdk').
            datacenter_name: Optional datacenter name to scope the disk lookup.
        """
        logger.info("inflate_vm_disk", disk_path=disk_path, datacenter_name=datacenter_name)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        dc_obj = None
        if datacenter_name:
            dc_obj = _find_datacenter_by_name(client, datacenter_name)
            if dc_obj is None:
                return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        task = vdm.InflateVirtualDisk_Task(name=disk_path, datacenter=dc_obj)
        result = wait_for_task(task)
        result["disk_path"] = disk_path
        result["datacenter_name"] = datacenter_name or None
        result["operation"] = "inflate_vm_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def zero_fill_vm_disk(disk_path: str, datacenter_name: str = "") -> dict[str, Any]:
        """Zero-fill a virtual disk, overwriting all blocks with zeros.

        Zero-filling is required before shrinking a thick disk to reclaim space.
        This is a long-running, data-intensive operation.

        Args:
            disk_path: Datastore path of the VMDK to zero-fill (e.g. '[ds] vm/disk.vmdk').
            datacenter_name: Optional datacenter name to scope the disk lookup.
        """
        logger.info("zero_fill_vm_disk", disk_path=disk_path, datacenter_name=datacenter_name)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        dc_obj = None
        if datacenter_name:
            dc_obj = _find_datacenter_by_name(client, datacenter_name)
            if dc_obj is None:
                return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        task = vdm.ZeroFillVirtualDisk_Task(name=disk_path, datacenter=dc_obj)
        result = wait_for_task(task)
        result["disk_path"] = disk_path
        result["datacenter_name"] = datacenter_name or None
        result["operation"] = "zero_fill_vm_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    def query_compatible_hosts_for_vm(vm_name: str) -> dict[str, Any]:
        """Find all ESXi hosts that are compatible with a VM for placement or migration.

        Checks each available host against the provisioning checker and returns a
        list of compatible hosts along with any per-host warnings.

        Args:
            vm_name: Name of the VM to find compatible hosts for.
        """
        logger.info("query_compatible_hosts_for_vm", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        checker = getattr(client.content, "vmProvisioningChecker", None)
        if checker is None:
            return {"status": "error", "error": "vmProvisioningChecker not available on this vCenter"}

        host_items = collect_properties(client, vim.HostSystem, ["name", "runtime.connectionState"])
        compatible_hosts: list[dict[str, Any]] = []
        incompatible_hosts: list[dict[str, Any]] = []

        for host_item in host_items:
            host_name = host_item.get("name", "")
            connection_state = str(host_item.get("runtime.connectionState", ""))
            if connection_state != "connected":
                continue

            host_obj = host_item["_obj"]
            try:
                task = checker.CheckMigrate_Task(vm=found["_obj"], host=host_obj)
                task_result = wait_for_task(task)
                if task_result.get("status") != "success":
                    incompatible_hosts.append({"host": host_name, "reason": task_result.get("message", "Task failed")})
                    continue

                errors: list[str] = []
                warnings: list[str] = []
                raw_result = getattr(task.info, "result", None)
                if raw_result:
                    for check_result in raw_result:
                        for w in getattr(check_result, "warning", []) or []:
                            warnings.append(str(w.msg) if hasattr(w, "msg") else str(w))
                        for e in getattr(check_result, "error", []) or []:
                            errors.append(str(e.msg) if hasattr(e, "msg") else str(e))

                if errors:
                    incompatible_hosts.append({"host": host_name, "errors": errors, "warnings": warnings})
                else:
                    compatible_hosts.append({"host": host_name, "warnings": warnings})
            except Exception as exc:
                incompatible_hosts.append({"host": host_name, "reason": str(exc)})

        return {
            "status": "success",
            "vm_name": vm_name,
            "compatible_count": len(compatible_hosts),
            "incompatible_count": len(incompatible_hosts),
            "compatible_hosts": compatible_hosts,
            "incompatible_hosts": incompatible_hosts,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_scheduled_power_operation(
        vm_name: str,
        operation: str = "powerOn",
        schedule_time: str = "",
    ) -> dict[str, Any]:
        """Schedule a power operation (power on/off, suspend, reset) for a virtual machine.

        Creates a one-time scheduled task in vCenter that will perform the
        specified power operation at the given time.

        Args:
            vm_name: Name of the VM to schedule the operation for.
            operation: Power operation to perform. One of: 'powerOn', 'powerOff', 'suspend', 'reset'.
            schedule_time: ISO 8601 datetime string for when to run the operation
                          (e.g. '2026-06-01T03:00:00'). Defaults to now + 5 minutes if empty.
        """
        logger.info("create_scheduled_power_operation", vm_name=vm_name, operation=operation, schedule_time=schedule_time)

        valid_operations = {"powerOn", "powerOff", "suspend", "reset"}
        if operation not in valid_operations:
            return {
                "status": "error",
                "error": f"operation must be one of: {', '.join(sorted(valid_operations))}",
            }

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        stm = getattr(client.content, "scheduledTaskManager", None)
        if stm is None:
            return {"status": "error", "error": "scheduledTaskManager not available on this vCenter"}

        if schedule_time:
            try:
                run_at = datetime.fromisoformat(schedule_time)
                if run_at.tzinfo is None:
                    run_at = run_at.replace(tzinfo=timezone.utc)
            except ValueError:
                return {
                    "status": "error",
                    "error": f"schedule_time '{schedule_time}' is not a valid ISO 8601 datetime string",
                }
        else:
            run_at = datetime.now(tz=timezone.utc) + timedelta(minutes=5)

        operation_map = {
            "powerOn": vim.vm.PowerOnAction,
            "powerOff": vim.vm.PowerOffAction,
            "suspend": vim.vm.SuspendAction,
            "reset": vim.vm.ResetAction,
        }
        action_class = operation_map[operation]

        scheduler = vim.scheduler.OnceTaskScheduler(runAt=run_at)
        task_name = f"scheduled_{operation}_{vm_name}_{run_at.strftime('%Y%m%dT%H%M%S')}"
        spec = vim.scheduler.ScheduledTaskSpec(
            name=task_name,
            description=f"Scheduled {operation} for VM '{vm_name}'",
            enabled=True,
            scheduler=scheduler,
            action=action_class(),
            notification="",
        )

        scheduled_task = stm.CreateScheduledTask(obj=found["_obj"], spec=spec)
        return {
            "status": "success",
            "vm_name": vm_name,
            "operation": operation,
            "schedule_time": run_at.isoformat(),
            "task_name": task_name,
            "scheduled_task_ref": str(scheduled_task) if scheduled_task else None,
        }
