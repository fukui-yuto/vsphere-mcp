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
        num_cores_per_socket: int | None = None,
    ) -> dict[str, Any]:
        """Change CPU and/or memory for a VM. VM may need to be powered off for changes to take effect.

        Args:
            vm_name: Name of the VM.
            num_cpu: Number of vCPUs (optional).
            memory_mb: Memory size in MB (optional).
            num_cores_per_socket: Number of cores per socket (optional). Allows changing CPU topology.
        """
        logger.info("set_vm_resources", vm_name=vm_name, num_cpu=num_cpu, memory_mb=memory_mb)
        if num_cpu is None and memory_mb is None and num_cores_per_socket is None:
            return {"status": "error", "error": "At least one of num_cpu, memory_mb, or num_cores_per_socket must be specified"}
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
        if num_cores_per_socket is not None:
            spec.numCoresPerSocket = num_cores_per_socket
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
        disk_mode: str = "persistent",
        datastore_name: str | None = None,
        controller_type: str | None = None,
    ) -> dict[str, Any]:
        """Add a new virtual disk to a VM.

        Args:
            vm_name: Name of the VM.
            size_gb: Disk size in GB.
            thin_provisioned: Use thin provisioning (default True). False = thick eager zeroed.
            disk_mode: Disk mode: 'persistent' (default), 'independent_persistent', or 'independent_nonpersistent'.
            datastore_name: Target datastore name (optional). If None, uses same as VM.
            controller_type: Controller type to use: 'scsi', 'nvme', or None (auto-detect first available).
        """
        logger.info("add_disk", vm_name=vm_name, size_gb=size_gb)
        if size_gb < 1:
            return {"status": "error", "error": "size_gb must be at least 1"}
        valid_modes = ("persistent", "independent_persistent", "independent_nonpersistent")
        if disk_mode not in valid_modes:
            return {"status": "error", "error": f"disk_mode must be one of: {', '.join(valid_modes)}"}
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        # Find appropriate controller
        devices = found.get("config.hardware.device", [])
        controller = None
        unit_number = 0
        existing_units: set[int] = set()

        if controller_type == "nvme":
            for dev in devices:
                if isinstance(dev, vim.vm.device.VirtualNVMEController):
                    controller = dev
                    break
            if controller is None:
                return {"status": "error", "error": "No NVMe controller found on VM"}
        elif controller_type == "scsi" or controller_type is None:
            for dev in devices:
                if isinstance(dev, vim.vm.device.VirtualSCSIController):
                    controller = dev
                    break
            if controller is None and controller_type == "scsi":
                return {"status": "error", "error": "No SCSI controller found on VM"}
            # Fallback to NVMe if no SCSI found
            if controller is None:
                for dev in devices:
                    if isinstance(dev, vim.vm.device.VirtualNVMEController):
                        controller = dev
                        break
            if controller is None:
                return {"status": "error", "error": "No SCSI or NVMe controller found on VM"}
        else:
            return {"status": "error", "error": f"controller_type must be 'scsi', 'nvme', or None"}

        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk) and dev.controllerKey == controller.key:
                existing_units.add(dev.unitNumber)

        # Find available unit number (skip 7 for SCSI, reserved for controller)
        skip_unit = 7 if isinstance(controller, vim.vm.device.VirtualSCSIController) else -1
        while unit_number in existing_units or unit_number == skip_unit:
            unit_number += 1

        backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
            diskMode=disk_mode,
            thinProvisioned=thin_provisioned,
            eagerlyScrub=not thin_provisioned,
        )
        if datastore_name:
            backing.fileName = f"[{datastore_name}]"
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
        adapter_type: str = "vmxnet3",
        mac_address: str | None = None,
        start_connected: bool = True,
    ) -> dict[str, Any]:
        """Add a new network adapter to a VM.

        Args:
            vm_name: Name of the VM.
            network_name: Name of the network or DVS portgroup.
            adapter_type: NIC type: 'vmxnet3' (default), 'e1000e', 'e1000', 'sriov', or 'vmxnet2'.
            mac_address: Manual MAC address (optional). If None, auto-generated.
            start_connected: Whether NIC is connected at power-on (default True).
        """
        logger.info("add_nic", vm_name=vm_name, network_name=network_name, adapter_type=adapter_type)
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

        adapter_map: dict[str, type] = {
            "vmxnet3": vim.vm.device.VirtualVmxnet3,
            "e1000e": vim.vm.device.VirtualE1000e,
            "e1000": vim.vm.device.VirtualE1000,
            "vmxnet2": vim.vm.device.VirtualVmxnet2,
            "sriov": vim.vm.device.VirtualSriovEthernetCard,
        }
        nic_class = adapter_map.get(adapter_type.lower())
        if nic_class is None:
            return {
                "status": "error",
                "error": f"Unknown adapter_type '{adapter_type}'. Valid: {', '.join(adapter_map.keys())}",
            }

        nic = nic_class(
            backing=backing,
            addressType="manual" if mac_address else "generated",
        )
        if mac_address:
            nic.macAddress = mac_address
        nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            startConnected=start_connected,
            allowGuestControl=True,
            connected=start_connected,
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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_cpu_allocation(
        vm_name: str,
        reservation_mhz: int | None = None,
        limit_mhz: int | None = None,
        shares_level: str | None = None,
        shares_value: int | None = None,
    ) -> dict[str, Any]:
        """Set CPU reservation, limit, and/or shares for a VM.

        Args:
            vm_name: Name of the VM.
            reservation_mhz: CPU reservation in MHz (minimum guaranteed CPU).
            limit_mhz: CPU limit in MHz (-1 for unlimited).
            shares_level: Shares level: 'low', 'normal', 'high', or 'custom'.
            shares_value: Shares value (required when shares_level is 'custom').
        """
        logger.info(
            "set_vm_cpu_allocation",
            vm_name=vm_name,
            reservation_mhz=reservation_mhz,
            limit_mhz=limit_mhz,
            shares_level=shares_level,
            shares_value=shares_value,
        )
        if reservation_mhz is None and limit_mhz is None and shares_level is None:
            return {"status": "error", "error": "At least one of reservation_mhz, limit_mhz, or shares_level must be specified"}
        valid_levels = {"low", "normal", "high", "custom"}
        if shares_level is not None and shares_level not in valid_levels:
            return {"status": "error", "error": f"shares_level must be one of: {valid_levels}"}
        if shares_level == "custom" and shares_value is None:
            return {"status": "error", "error": "shares_value is required when shares_level is 'custom'"}
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        alloc = vim.ResourceAllocationInfo()
        if reservation_mhz is not None:
            alloc.reservation = reservation_mhz
        if limit_mhz is not None:
            alloc.limit = limit_mhz
        if shares_level is not None:
            level_map = {
                "low": vim.SharesInfo.Level.low,
                "normal": vim.SharesInfo.Level.normal,
                "high": vim.SharesInfo.Level.high,
                "custom": vim.SharesInfo.Level.custom,
            }
            shares = vim.SharesInfo(level=level_map[shares_level])
            if shares_level == "custom":
                shares.shares = shares_value
            alloc.shares = shares

        spec = vim.vm.ConfigSpec()
        spec.cpuAllocation = alloc
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_cpu_allocation"
        if reservation_mhz is not None:
            result["reservation_mhz"] = reservation_mhz
        if limit_mhz is not None:
            result["limit_mhz"] = limit_mhz
        if shares_level is not None:
            result["shares_level"] = shares_level
        if shares_value is not None:
            result["shares_value"] = shares_value
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_memory_allocation(
        vm_name: str,
        reservation_mb: int | None = None,
        limit_mb: int | None = None,
        shares_level: str | None = None,
        shares_value: int | None = None,
    ) -> dict[str, Any]:
        """Set memory reservation, limit, and/or shares for a VM.

        Args:
            vm_name: Name of the VM.
            reservation_mb: Memory reservation in MB (minimum guaranteed memory).
            limit_mb: Memory limit in MB (-1 for unlimited).
            shares_level: Shares level: 'low', 'normal', 'high', or 'custom'.
            shares_value: Shares value (required when shares_level is 'custom').
        """
        logger.info(
            "set_vm_memory_allocation",
            vm_name=vm_name,
            reservation_mb=reservation_mb,
            limit_mb=limit_mb,
            shares_level=shares_level,
            shares_value=shares_value,
        )
        if reservation_mb is None and limit_mb is None and shares_level is None:
            return {"status": "error", "error": "At least one of reservation_mb, limit_mb, or shares_level must be specified"}
        valid_levels = {"low", "normal", "high", "custom"}
        if shares_level is not None and shares_level not in valid_levels:
            return {"status": "error", "error": f"shares_level must be one of: {valid_levels}"}
        if shares_level == "custom" and shares_value is None:
            return {"status": "error", "error": "shares_value is required when shares_level is 'custom'"}
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        alloc = vim.ResourceAllocationInfo()
        if reservation_mb is not None:
            alloc.reservation = reservation_mb
        if limit_mb is not None:
            alloc.limit = limit_mb
        if shares_level is not None:
            level_map = {
                "low": vim.SharesInfo.Level.low,
                "normal": vim.SharesInfo.Level.normal,
                "high": vim.SharesInfo.Level.high,
                "custom": vim.SharesInfo.Level.custom,
            }
            shares = vim.SharesInfo(level=level_map[shares_level])
            if shares_level == "custom":
                shares.shares = shares_value
            alloc.shares = shares

        spec = vim.vm.ConfigSpec()
        spec.memoryAllocation = alloc
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_memory_allocation"
        if reservation_mb is not None:
            result["reservation_mb"] = reservation_mb
        if limit_mb is not None:
            result["limit_mb"] = limit_mb
        if shares_level is not None:
            result["shares_level"] = shares_level
        if shares_value is not None:
            result["shares_value"] = shares_value
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_memory_hotadd(vm_name: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable memory hot-add for a VM. VM must be powered off.

        Args:
            vm_name: Name of the VM.
            enabled: True to enable memory hot-add, False to disable.
        """
        logger.info("set_vm_memory_hotadd", vm_name=vm_name, enabled=enabled)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = str(found.get("runtime.powerState", ""))
        if power_state != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off to change memory hot-add setting (current state: {power_state})"}

        spec = vim.vm.ConfigSpec()
        spec.memoryHotAddEnabled = enabled
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_memory_hotadd"
        result["memory_hot_add_enabled"] = enabled
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_latency_sensitivity(vm_name: str, level: str) -> dict[str, Any]:
        """Set the latency sensitivity level for a VM.

        Args:
            vm_name: Name of the VM.
            level: Latency sensitivity level: 'low', 'normal', 'medium', or 'high'.
        """
        logger.info("set_vm_latency_sensitivity", vm_name=vm_name, level=level)
        valid_levels = {"low", "normal", "medium", "high"}
        if level not in valid_levels:
            return {"status": "error", "error": f"level must be one of: {valid_levels}"}
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        level_map = {
            "low": vim.LatencySensitivity.SensitivityLevel.low,
            "normal": vim.LatencySensitivity.SensitivityLevel.normal,
            "medium": vim.LatencySensitivity.SensitivityLevel.medium,
            "high": vim.LatencySensitivity.SensitivityLevel.high,
        }
        spec = vim.vm.ConfigSpec()
        spec.latencySensitivity = vim.LatencySensitivity(level=level_map[level])
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_latency_sensitivity"
        result["level"] = level
        return result
