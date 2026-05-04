from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

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

        # Try standard network first
        backing: Any = None
        std_nets = collect_properties(client, vim.Network, ["name"])
        for net in std_nets:
            if net.get("name") == network_name:
                net_obj = net["_obj"]
                backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
                    deviceName=network_name,
                    network=net_obj,
                )
                break

        # Fall back to DVS portgroup
        if backing is None:
            dvs_pgs = collect_properties(
                client,
                vim.dvs.DistributedVirtualPortgroup,
                ["name", "key", "config.distributedVirtualSwitch"],
            )
            for pg in dvs_pgs:
                if pg.get("name") == network_name:
                    pg_obj = pg["_obj"]
                    backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(
                        port=vim.dvs.PortConnection(
                            portgroupKey=pg_obj.key,
                            switchUuid=pg_obj.config.distributedVirtualSwitch.uuid,
                        )
                    )
                    break

        if backing is None:
            return {
                "status": "error",
                "error": f"Network '{network_name}' not found (checked standard and DVS portgroups)",
            }

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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_cd_drive(vm_name: str, iso_path: str | None = None) -> dict[str, Any]:
        """Add a CD/DVD drive to a VM.

        Args:
            vm_name: Name of the VM.
            iso_path: Datastore path to ISO (e.g. '[ds] iso/file.iso'), or None for empty drive.
        """
        logger.info("add_vm_cd_drive", vm_name=vm_name, iso_path=iso_path)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])

        # Find IDE or SATA controller
        controller = None
        for dev in devices:
            if isinstance(dev, (vim.vm.device.VirtualIDEController, vim.vm.device.VirtualAHCIController)):
                controller = dev
                break
        if controller is None:
            return {"status": "error", "error": "No IDE or SATA controller found on VM"}

        # Find available unit number on the controller
        used_units: set[int] = set()
        for dev in devices:
            if hasattr(dev, "controllerKey") and dev.controllerKey == controller.key:
                used_units.add(dev.unitNumber)
        # IDE controllers support units 0 and 1; SATA up to 30 — find first unused slot
        max_units = 2 if isinstance(controller, vim.vm.device.VirtualIDEController) else 30
        unit_number = 0
        for u in range(max_units):
            if u not in used_units:
                unit_number = u
                break

        if iso_path:
            backing: Any = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)
        else:
            backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo(deviceName="", exclusive=False)

        cdrom = vim.vm.device.VirtualCdrom(
            backing=backing,
            controllerKey=controller.key,
            unitNumber=unit_number,
            connectable=vim.vm.device.VirtualDevice.ConnectInfo(
                startConnected=bool(iso_path),
                connected=bool(iso_path),
                allowGuestControl=True,
            ),
        )
        cdrom_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=cdrom,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[cdrom_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["iso_path"] = iso_path
        result["operation"] = "add_vm_cd_drive"
        return result
