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

logger = get_logger(__name__)


def register_vm_device_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_disk(vm_name: str, disk_label: str) -> dict[str, Any]:
        """Remove a virtual disk from a VM and delete its backing file. Example: disk_label='Hard disk 1'."""
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

        disk_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            fileOperation=vim.vm.device.VirtualDeviceSpec.FileOperation.destroy,
            device=disk,
        )
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
    ) -> dict[str, Any]:
        """Set VM boot options such as boot delay and BIOS setup entry."""
        logger.info(
            "set_vm_boot_options",
            vm_name=vm_name,
            boot_delay_ms=boot_delay_ms,
            enter_bios_setup=enter_bios_setup,
        )
        if boot_delay_ms is None and enter_bios_setup is None:
            return {
                "status": "error",
                "error": "At least one of boot_delay_ms or enter_bios_setup must be specified",
            }

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        boot_options = vim.vm.BootOptions()
        if boot_delay_ms is not None:
            boot_options.bootDelay = boot_delay_ms
        if enter_bios_setup is not None:
            boot_options.enterBIOSSetup = enter_bios_setup

        config_spec = vim.vm.ConfigSpec(bootOptions=boot_options)
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "set_vm_boot_options"
        if boot_delay_ms is not None:
            result["boot_delay_ms"] = boot_delay_ms
        if enter_bios_setup is not None:
            result["enter_bios_setup"] = enter_bios_setup
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
