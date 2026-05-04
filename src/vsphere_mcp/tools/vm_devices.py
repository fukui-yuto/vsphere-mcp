from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

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
