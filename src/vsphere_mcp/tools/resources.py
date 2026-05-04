from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_resource_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_resources(
        vm_name: str,
        num_cpu: int | None = None,
        memory_mb: int | None = None,
    ) -> dict[str, Any]:
        """Change CPU and/or memory for a VM. VM may need to be powered off for changes to take effect."""
        logger.info("set_vm_resources", vm_name=vm_name, num_cpu=num_cpu, memory_mb=memory_mb)
        if num_cpu is None and memory_mb is None:
            return {"status": "error", "error": "At least one of num_cpu or memory_mb must be specified"}
        if num_cpu is not None and num_cpu < 1:
            return {"status": "error", "error": "num_cpu must be at least 1"}
        if memory_mb is not None and memory_mb < 4:
            return {"status": "error", "error": "memory_mb must be at least 4"}
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        spec = vim.vm.ConfigSpec()
        if num_cpu is not None:
            spec.numCPUs = num_cpu
        if memory_mb is not None:
            spec.memoryMB = memory_mb
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_resources"
        if num_cpu is not None:
            result["num_cpu"] = num_cpu
        if memory_mb is not None:
            result["memory_mb"] = memory_mb
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_disk(
        vm_name: str,
        size_gb: int,
        thin_provisioned: bool = True,
    ) -> dict[str, Any]:
        """Add a new virtual disk to a VM."""
        logger.info("add_disk", vm_name=vm_name, size_gb=size_gb)
        if size_gb < 1:
            return {"status": "error", "error": "size_gb must be at least 1"}
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        # Find SCSI controller
        devices = found.get("config.hardware.device", [])
        controller = None
        unit_number = 0
        existing_units: set[int] = set()
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
            if isinstance(dev, vim.vm.device.VirtualDisk):
                existing_units.add(dev.unitNumber)
        if controller is None:
            return {"status": "error", "error": "No SCSI controller found on VM"}

        # Find available unit number (skip 7, reserved for controller)
        while unit_number in existing_units or unit_number == 7:
            unit_number += 1

        backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
            diskMode="persistent",
            thinProvisioned=thin_provisioned,
        )
        disk = vim.vm.device.VirtualDisk(
            backing=backing,
            controllerKey=controller.key,
            unitNumber=unit_number,
            capacityInKB=size_gb * 1024 * 1024,
        )
        disk_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            fileOperation=vim.vm.device.VirtualDeviceSpec.FileOperation.create,
            device=disk,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[disk_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["size_gb"] = size_gb
        result["operation"] = "add_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_nic(
        vm_name: str,
        network_name: str,
    ) -> dict[str, Any]:
        """Add a new network adapter to a VM."""
        logger.info("add_nic", vm_name=vm_name, network_name=network_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
            deviceName=network_name,
        )
        nic = vim.vm.device.VirtualVmxnet3(
            backing=backing,
            addressType="generated",
        )
        nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            startConnected=True,
            allowGuestControl=True,
            connected=True,
        )
        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=nic,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["network_name"] = network_name
        result["operation"] = "add_nic"
        return result
