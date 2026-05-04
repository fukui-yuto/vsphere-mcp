from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    find_vm_with_props,
    handle_tool_errors,
    require_confirm,
    wait_for_task,
)
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_vm_device_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_disk(vm_name: str, disk_label: str, delete_backing: bool = True) -> dict[str, Any]:
        """Remove a virtual disk from a VM.

        Args:
            vm_name: Name of the VM.
            disk_label: Label of the disk (e.g. 'Hard disk 1').
            delete_backing: If True (default), delete the VMDK file. If False, detach only (keep file for reattach).
        """
        logger.info("remove_disk", vm_name=vm_name, disk_label=disk_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        disk = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk) and dev.deviceInfo.label == disk_label:
                disk = dev
                break
        if disk is None:
            return {"status": "error", "error": f"Disk '{disk_label}' not found on VM '{vm_name}'"}

        spec_kwargs: dict[str, Any] = {
            "operation": vim.vm.device.VirtualDeviceSpec.Operation.remove,
            "device": disk,
        }
        if delete_backing:
            spec_kwargs["fileOperation"] = vim.vm.device.VirtualDeviceSpec.FileOperation.destroy
        disk_spec = vim.vm.device.VirtualDeviceSpec(**spec_kwargs)
        config_spec = vim.vm.ConfigSpec(deviceChange=[disk_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["disk_label"] = disk_label
        result["operation"] = "remove_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def expand_disk(vm_name: str, disk_label: str, new_size_gb: int) -> dict[str, Any]:
        """Expand a virtual disk to a new size. The new size must be larger than the current size."""
        logger.info("expand_disk", vm_name=vm_name, disk_label=disk_label, new_size_gb=new_size_gb)
        if new_size_gb <= 0:
            return {"status": "error", "error": "new_size_gb must be a positive integer"}
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        disk = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk) and dev.deviceInfo.label == disk_label:
                disk = dev
                break
        if disk is None:
            return {"status": "error", "error": f"Disk '{disk_label}' not found on VM '{vm_name}'"}

        current_size_kb = disk.capacityInKB
        new_size_kb = new_size_gb * 1024 * 1024
        if new_size_kb <= current_size_kb:
            current_gb = round(current_size_kb / (1024 * 1024), 2)
            return {
                "status": "error",
                "error": f"New size ({new_size_gb} GB) must be larger than current size ({current_gb} GB)",
            }

        disk.capacityInKB = new_size_kb
        disk_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=disk,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[disk_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["disk_label"] = disk_label
        result["new_size_gb"] = new_size_gb
        result["operation"] = "expand_disk"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_nic(vm_name: str, nic_label: str) -> dict[str, Any]:
        """Remove a network adapter from a VM. Example: nic_label='Network adapter 1'."""
        logger.info("remove_nic", vm_name=vm_name, nic_label=nic_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        nic = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
                nic = dev
                break
        if nic is None:
            return {"status": "error", "error": f"NIC '{nic_label}' not found on VM '{vm_name}'"}

        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=nic,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["nic_label"] = nic_label
        result["operation"] = "remove_nic"
        return result

    @mcp.tool()
    @handle_tool_errors
    def list_vm_controllers(vm_name: str) -> dict[str, Any]:
        """List all SCSI/IDE/SATA controllers on a VM with their connected devices."""
        logger.info("list_vm_controllers", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        controllers = []
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualController):
                connected = len(dev.device) if dev.device else 0
                controllers.append(
                    {
                        "type": type(dev).__name__,
                        "label": dev.deviceInfo.label,
                        "bus_number": dev.busNumber,
                        "connected_devices": connected,
                    }
                )
        return {"vm_name": vm_name, "controllers": controllers}

    @mcp.tool()
    @handle_tool_errors
    def get_vm_extra_config(vm_name: str, prefix: str | None = None) -> dict[str, Any]:
        """Get VM extraConfig key/value pairs. Optionally filter by key prefix."""
        logger.info("get_vm_extra_config", vm_name=vm_name, prefix=prefix)
        found = find_vm_with_props(client, vm_name, ["config.extraConfig"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        extra_config = found.get("config.extraConfig", [])
        entries = []
        for opt in extra_config:
            if prefix and not opt.key.startswith(prefix):
                continue
            entries.append({"key": opt.key, "value": opt.value})
        return {"vm_name": vm_name, "extra_config": entries}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_extra_config(vm_name: str, key: str, value: str) -> dict[str, Any]:
        """Set a VM extraConfig key/value pair."""
        logger.info("set_vm_extra_config", vm_name=vm_name, key=key, value=value)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        option = vim.option.OptionValue(key=key, value=value)
        config_spec = vim.vm.ConfigSpec(extraConfig=[option])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["key"] = key
        result["operation"] = "set_vm_extra_config"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_vm(vm_name: str, new_name: str) -> dict[str, Any]:
        """Rename a virtual machine."""
        logger.info("rename_vm", vm_name=vm_name, new_name=new_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        task = found["_obj"].Rename_Task(new_name)
        result = wait_for_task(task)
        result["old_name"] = vm_name
        result["new_name"] = new_name
        result["operation"] = "rename_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def unregister_vm(vm_name: str) -> dict[str, Any]:
        """Unregister a VM from the inventory without deleting its files. VM must be powered off."""
        logger.info("unregister_vm", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before unregistering"}

        found["_obj"].UnregisterVM()
        return {"status": "success", "vm_name": vm_name, "operation": "unregister_vm"}

    @mcp.tool()
    @handle_tool_errors
    def get_vm_console_url(vm_name: str) -> dict[str, Any]:
        """Acquire a WebMKS console ticket for a VM. May not work in all environments."""
        logger.info("get_vm_console_url", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        try:
            ticket = vm_obj.AcquireTicket("webmks")
            return {
                "vm_name": vm_name,
                "ticket": ticket.ticket,
                "host": ticket.host,
                "port": ticket.port,
                "cfg_file": ticket.cfgFile if hasattr(ticket, "cfgFile") else None,
                "ssl_thumbprint": ticket.sslThumbprint if hasattr(ticket, "sslThumbprint") else None,
            }
        except Exception as webmks_err:
            logger.debug("AcquireTicket(webmks) failed, trying AcquireMksTicket", error=str(webmks_err))
            try:
                ticket = vm_obj.AcquireMksTicket()
                return {
                    "vm_name": vm_name,
                    "ticket": ticket.ticket,
                    "host": ticket.host,
                    "port": ticket.port,
                    "cfg_file": ticket.cfgFile if hasattr(ticket, "cfgFile") else None,
                    "ssl_thumbprint": ticket.sslThumbprint if hasattr(ticket, "sslThumbprint") else None,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to acquire console ticket: {e}",
                }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_boot_options(
        vm_name: str,
        boot_delay_ms: int | None = None,
        enter_bios_setup: bool | None = None,
        boot_retry_enabled: bool | None = None,
        boot_retry_delay_ms: int | None = None,
        efi_secure_boot: bool | None = None,
    ) -> dict[str, Any]:
        """Set VM boot options such as boot delay, BIOS setup entry, retry, and EFI secure boot.

        Args:
            vm_name: Name of the VM.
            boot_delay_ms: Delay in ms before boot (e.g. 10000 for 10s). None to leave unchanged.
            enter_bios_setup: If True, VM enters BIOS/EFI setup on next boot.
            boot_retry_enabled: Enable automatic boot retry after failure.
            boot_retry_delay_ms: Delay in ms before boot retry (default 10000).
            efi_secure_boot: Enable/disable EFI Secure Boot (VM must use EFI firmware).
        """
        logger.info(
            "set_vm_boot_options",
            vm_name=vm_name,
            boot_delay_ms=boot_delay_ms,
            enter_bios_setup=enter_bios_setup,
        )
        if all(v is None for v in (boot_delay_ms, enter_bios_setup, boot_retry_enabled, boot_retry_delay_ms, efi_secure_boot)):
            return {
                "status": "error",
                "error": "At least one boot option parameter must be specified",
            }

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        boot_options = vim.vm.BootOptions()
        if boot_delay_ms is not None:
            boot_options.bootDelay = boot_delay_ms
        if enter_bios_setup is not None:
            boot_options.enterBIOSSetup = enter_bios_setup
        if boot_retry_enabled is not None:
            boot_options.bootRetryEnabled = boot_retry_enabled
        if boot_retry_delay_ms is not None:
            boot_options.bootRetryDelay = boot_retry_delay_ms
        if efi_secure_boot is not None:
            boot_options.efiSecureBootEnabled = efi_secure_boot

        config_spec = vim.vm.ConfigSpec(bootOptions=boot_options)
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_boot_options"
        return result

    @mcp.tool()
    @handle_tool_errors
    def list_vm_cddvd_drives(vm_name: str) -> dict[str, Any]:
        """List CD/DVD drives on a VM with ISO mount status and connected state."""
        logger.info("list_vm_cddvd_drives", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        drives = []
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualCdrom):
                backing = dev.backing
                iso_path = None
                backing_type = type(backing).__name__
                if isinstance(backing, vim.vm.device.VirtualCdrom.IsoBackingInfo):
                    iso_path = backing.fileName
                connectable = dev.connectable
                drives.append(
                    {
                        "label": dev.deviceInfo.label,
                        "key": dev.key,
                        "backing_type": backing_type,
                        "iso_path": iso_path,
                        "connected": connectable.connected if connectable else False,
                        "start_connected": connectable.startConnected if connectable else False,
                    }
                )
        return {"vm_name": vm_name, "cddvd_drives": drives}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def mount_vm_cdrom_iso(vm_name: str, cdrom_label: str, datastore_name: str, iso_path: str) -> dict[str, Any]:
        """Mount an ISO file to a VM CD/DVD drive. Example: cdrom_label='CD/DVD drive 1', iso_path='iso/ubuntu.iso'."""
        logger.info(
            "mount_vm_cdrom_iso",
            vm_name=vm_name,
            cdrom_label=cdrom_label,
            datastore_name=datastore_name,
            iso_path=iso_path,
        )
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        cdrom = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualCdrom) and dev.deviceInfo.label == cdrom_label:
                cdrom = dev
                break
        if cdrom is None:
            return {"status": "error", "error": f"CD/DVD drive '{cdrom_label}' not found on VM '{vm_name}'"}

        backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=f"[{datastore_name}] {iso_path}")
        cdrom.backing = backing
        connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            connected=True,
            startConnected=True,
            allowGuestControl=True,
        )
        cdrom.connectable = connectable

        cdrom_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=cdrom,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[cdrom_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["cdrom_label"] = cdrom_label
        result["iso_path"] = f"[{datastore_name}] {iso_path}"
        result["operation"] = "mount_vm_cdrom_iso"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="low")
    def disconnect_vm_cdrom(vm_name: str, cdrom_label: str) -> dict[str, Any]:
        """Disconnect a CD/DVD drive (switch to client device). cdrom_label example: 'CD/DVD drive 1'."""
        logger.info("disconnect_vm_cdrom", vm_name=vm_name, cdrom_label=cdrom_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        cdrom = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualCdrom) and dev.deviceInfo.label == cdrom_label:
                cdrom = dev
                break
        if cdrom is None:
            return {"status": "error", "error": f"CD/DVD drive '{cdrom_label}' not found on VM '{vm_name}'"}

        backing = vim.vm.device.VirtualCdrom.RemoteAtapiBackingInfo(deviceName="")
        cdrom.backing = backing
        connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            connected=False,
            startConnected=False,
            allowGuestControl=True,
        )
        cdrom.connectable = connectable

        cdrom_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=cdrom,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[cdrom_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["cdrom_label"] = cdrom_label
        result["operation"] = "disconnect_vm_cdrom"
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vm_video_card(vm_name: str) -> dict[str, Any]:
        """Get video card settings for a VM (video RAM, displays, 3D rendering)."""
        logger.info("get_vm_video_card", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        video_card = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualVideoCard):
                video_card = dev
                break
        if video_card is None:
            return {"status": "error", "error": f"No video card found on VM '{vm_name}'"}

        return {
            "vm_name": vm_name,
            "video_card": {
                "label": video_card.deviceInfo.label,
                "videoRamSizeInKB": video_card.videoRamSizeInKB,
                "numDisplays": video_card.numDisplays,
                "use3dRenderer": getattr(video_card, "use3dRenderer", None),
                "enable3DSupport": getattr(video_card, "enable3DSupport", None),
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def list_vm_disk_layout(vm_name: str) -> dict[str, Any]:
        """Get detailed disk layout for a VM: capacity, backing file, thin provisioning, disk mode."""
        logger.info("list_vm_disk_layout", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        disks = []
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                backing = dev.backing
                disk_info: dict[str, Any] = {
                    "label": dev.deviceInfo.label,
                    "capacityInKB": dev.capacityInKB,
                    "capacityInGB": round(dev.capacityInKB / (1024 * 1024), 2),
                }
                if backing is not None:
                    disk_info["fileName"] = getattr(backing, "fileName", None)
                    disk_info["thinProvisioned"] = getattr(backing, "thinProvisioned", None)
                    disk_info["diskMode"] = getattr(backing, "diskMode", None)
                    disk_info["eagerlyScrub"] = getattr(backing, "eagerlyScrub", None)
                disks.append(disk_info)
        return {"vm_name": vm_name, "disks": disks}

    @mcp.tool()
    @handle_tool_errors
    def list_vm_snapshots_disk_usage(vm_name: str) -> dict[str, Any]:
        """Get snapshot disk usage for a VM using layoutEx to find snapshot files and their sizes."""
        logger.info("list_vm_snapshots_disk_usage", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["layoutEx", "snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        layout_ex = found.get("layoutEx")
        if layout_ex is None:
            return {"vm_name": vm_name, "total_snapshot_bytes": 0, "snapshots": []}

        snap_info = found.get("snapshot")
        snapshot_names: dict[str, str] = {}
        if snap_info and hasattr(snap_info, "rootSnapshotList"):

            def _collect_names(tree: list[Any]) -> None:
                for s in tree:
                    snapshot_names[str(s.snapshot)] = s.name
                    if s.childSnapshotList:
                        _collect_names(s.childSnapshotList)

            _collect_names(snap_info.rootSnapshotList)

        file_size_map: dict[str, int] = {}
        for f in layout_ex.file or []:
            file_size_map[f.key] = f.size

        snapshots: list[dict[str, Any]] = []
        total_bytes = 0
        for snap_layout in layout_ex.snapshot or []:
            snap_key = str(snap_layout.key)
            snap_name = snapshot_names.get(snap_key, snap_key)
            snap_bytes = 0
            file_keys: list[int] = []
            if snap_layout.dataKey:
                file_keys.extend(snap_layout.dataKey)
            if hasattr(snap_layout, "memoryKey") and snap_layout.memoryKey:
                file_keys.append(snap_layout.memoryKey)
            for fk in file_keys:
                snap_bytes += file_size_map.get(fk, 0)
            total_bytes += snap_bytes
            snapshots.append(
                {
                    "name": snap_name,
                    "size_bytes": snap_bytes,
                    "size_mb": round(snap_bytes / (1024 * 1024), 2),
                }
            )

        return {
            "vm_name": vm_name,
            "total_snapshot_bytes": total_bytes,
            "total_snapshot_mb": round(total_bytes / (1024 * 1024), 2),
            "snapshots": snapshots,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def change_vm_nic_network(vm_name: str, nic_label: str, network_name: str) -> dict[str, Any]:
        """Change an existing NIC to a different network/portgroup. Example: nic_label='Network adapter 1'."""
        logger.info("change_vm_nic_network", vm_name=vm_name, nic_label=nic_label, network_name=network_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        nic = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
                nic = dev
                break
        if nic is None:
            return {"status": "error", "error": f"NIC '{nic_label}' not found on VM '{vm_name}'"}

        # Try standard network first
        backing = None
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

        nic.backing = backing
        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=nic,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["nic_label"] = nic_label
        result["network_name"] = network_name
        result["operation"] = "change_vm_nic_network"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def connect_disconnect_vm_nic(
        vm_name: str, nic_label: str, connected: bool, start_connected: bool | None = None
    ) -> dict[str, Any]:
        """Toggle a NIC connected state on a VM.

        Args:
            vm_name: Name of the VM.
            nic_label: Label of the NIC (e.g. 'Network adapter 1').
            connected: Whether to connect (True) or disconnect (False) the NIC now.
            start_connected: Whether to connect on VM power-on. If omitted, matches 'connected'.
        """
        logger.info("connect_disconnect_vm_nic", vm_name=vm_name, nic_label=nic_label, connected=connected)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        nic = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard) and dev.deviceInfo.label == nic_label:
                nic = dev
                break
        if nic is None:
            return {"status": "error", "error": f"NIC '{nic_label}' not found on VM '{vm_name}'"}

        if nic.connectable is None:
            nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic.connectable.connected = connected
        nic.connectable.startConnected = start_connected if start_connected is not None else connected

        nic_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=nic,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[nic_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["nic_label"] = nic_label
        result["connected"] = connected
        result["operation"] = "connect_disconnect_vm_nic"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_scsi_controller(vm_name: str, controller_type: str = "pvscsi") -> dict[str, Any]:
        """Add a SCSI/PVSCSI controller to a VM. controller_type: 'pvscsi', 'lsilogic', or 'lsilogicsas'."""
        logger.info("add_vm_scsi_controller", vm_name=vm_name, controller_type=controller_type)
        controller_map = {
            "pvscsi": vim.vm.device.ParaVirtualSCSIController,
            "lsilogic": vim.vm.device.VirtualLsiLogicController,
            "lsilogicsas": vim.vm.device.VirtualLsiLogicSASController,
        }
        if controller_type not in controller_map:
            return {
                "status": "error",
                "error": f"Invalid controller_type '{controller_type}'. Valid: {list(controller_map.keys())}",
            }

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        existing_bus_numbers: set[int] = set()
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                existing_bus_numbers.add(dev.busNumber)

        bus_number = 0
        while bus_number in existing_bus_numbers:
            bus_number += 1

        ctrl_cls = controller_map[controller_type]
        controller = ctrl_cls(
            busNumber=bus_number,
            sharedBus=vim.vm.device.VirtualSCSIController.Sharing.noSharing,
        )
        ctrl_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=controller,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[ctrl_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["controller_type"] = controller_type
        result["bus_number"] = bus_number
        result["operation"] = "add_vm_scsi_controller"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def upgrade_vm_hardware(vm_name: str, version: str | None = None) -> dict[str, Any]:
        """Upgrade virtual hardware version for a VM. VM must be powered off."""
        logger.info("upgrade_vm_hardware", vm_name=vm_name, version=version)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before upgrading hardware"}

        task = found["_obj"].UpgradeVM_Task(version=version)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["version"] = version
        result["operation"] = "upgrade_vm_hardware"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_cpu_hotadd(
        vm_name: str,
        cpu_hot_add: bool | None = None,
        memory_hot_add: bool | None = None,
    ) -> dict[str, Any]:
        """Enable or disable CPU and/or memory hot-add for a VM."""
        logger.info("set_vm_cpu_hotadd", vm_name=vm_name, cpu_hot_add=cpu_hot_add, memory_hot_add=memory_hot_add)
        if cpu_hot_add is None and memory_hot_add is None:
            return {
                "status": "error",
                "error": "At least one of cpu_hot_add or memory_hot_add must be specified",
            }

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        config_spec = vim.vm.ConfigSpec()
        if cpu_hot_add is not None:
            config_spec.cpuHotAddEnabled = cpu_hot_add
        if memory_hot_add is not None:
            config_spec.memoryHotAddEnabled = memory_hot_add

        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_cpu_hotadd"
        if cpu_hot_add is not None:
            result["cpu_hot_add"] = cpu_hot_add
        if memory_hot_add is not None:
            result["memory_hot_add"] = memory_hot_add
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_cores_per_socket(vm_name: str, cores_per_socket: int) -> dict[str, Any]:
        """Set the number of cores per socket for a VM."""
        logger.info("set_vm_cores_per_socket", vm_name=vm_name, cores_per_socket=cores_per_socket)
        if cores_per_socket < 1:
            return {"status": "error", "error": "cores_per_socket must be at least 1"}

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        config_spec = vim.vm.ConfigSpec(numCoresPerSocket=cores_per_socket)
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["cores_per_socket"] = cores_per_socket
        result["operation"] = "set_vm_cores_per_socket"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def change_vm_disk_mode(vm_name: str, disk_label: str, disk_mode: str) -> dict[str, Any]:
        """Change disk mode for a virtual disk.

        Args:
            vm_name: Name of the VM.
            disk_label: Label of the disk (e.g. 'Hard disk 1').
            disk_mode: One of 'persistent', 'independent_persistent', 'independent_nonpersistent'.
        """
        logger.info("change_vm_disk_mode", vm_name=vm_name, disk_label=disk_label, disk_mode=disk_mode)
        valid_modes = {"persistent", "independent_persistent", "independent_nonpersistent"}
        if disk_mode not in valid_modes:
            return {"status": "error", "error": f"Invalid disk_mode '{disk_mode}'. Valid: {sorted(valid_modes)}"}

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        disk = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk) and dev.deviceInfo.label == disk_label:
                disk = dev
                break
        if disk is None:
            return {"status": "error", "error": f"Disk '{disk_label}' not found on VM '{vm_name}'"}

        disk.backing.diskMode = disk_mode
        disk_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
            device=disk,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[disk_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["disk_label"] = disk_label
        result["disk_mode"] = disk_mode
        result["operation"] = "change_vm_disk_mode"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_vtpm(vm_name: str) -> dict[str, Any]:
        """Add a Virtual Trusted Platform Module (vTPM) device to a VM.

        The VM must use EFI firmware and must be powered off.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("add_vtpm", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before adding a vTPM"}

        tpm_device = vim.vm.device.VirtualTPM()
        tpm_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=tpm_device,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[tpm_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "add_vtpm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_secure_boot(vm_name: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable EFI Secure Boot for a VM.

        The VM firmware must be set to EFI. The VM should be powered off.

        Args:
            vm_name: Name of the VM.
            enabled: True to enable Secure Boot, False to disable.
        """
        logger.info("set_vm_secure_boot", vm_name=vm_name, enabled=enabled)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        boot_options = vim.vm.BootOptions(efiSecureBootEnabled=enabled)
        config_spec = vim.vm.ConfigSpec(firmware="efi", bootOptions=boot_options)
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["enabled"] = enabled
        result["operation"] = "set_vm_secure_boot"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_vm_vbs(vm_name: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable Virtualization Based Security (VBS) for a VM.

        VBS requires EFI firmware, Secure Boot, and compatible hardware. The VM must be powered off.

        Args:
            vm_name: Name of the VM.
            enabled: True to enable VBS, False to disable.
        """
        logger.info("configure_vm_vbs", vm_name=vm_name, enabled=enabled)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before configuring VBS"}

        flags = vim.vm.FlagInfo(vbsEnabled=enabled)
        config_spec = vim.vm.ConfigSpec(flags=flags)
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["enabled"] = enabled
        result["operation"] = "configure_vm_vbs"
        return result
