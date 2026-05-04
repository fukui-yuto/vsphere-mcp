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


def register_vm_devices_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_serial_port(
        vm_name: str,
        backing_type: str = "network",
        uri: str = "",
        direction: str = "server",
        file_path: str = "",
    ) -> dict[str, Any]:
        """Add a serial port to a VM.

        Args:
            vm_name: Name of the VM.
            backing_type: Backing type for the serial port. One of 'network', 'file', 'pipe'.
            uri: For backing_type='network', the URI to connect to (e.g. 'tcp://host:port').
            direction: For backing_type='network', connection direction. 'server' or 'client'.
            file_path: For backing_type='file' or 'pipe', the file/pipe path.
        """
        logger.info(
            "add_vm_serial_port",
            vm_name=vm_name,
            backing_type=backing_type,
        )
        valid_types = {"network", "file", "pipe"}
        if backing_type not in valid_types:
            return {
                "status": "error",
                "error": f"Invalid backing_type '{backing_type}'. Valid: {sorted(valid_types)}",
            }

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        serial_port = vim.vm.device.VirtualSerialPort()
        serial_port.yieldOnPoll = True

        if backing_type == "network":
            backing = vim.vm.device.VirtualSerialPort.URIBackingInfo()
            backing.serviceURI = uri
            backing.direction = direction
            serial_port.backing = backing
        elif backing_type == "file":
            backing = vim.vm.device.VirtualSerialPort.FileBackingInfo()
            backing.fileName = file_path
            serial_port.backing = backing
        else:  # pipe
            backing = vim.vm.device.VirtualSerialPort.PipeBackingInfo()
            backing.pipeName = file_path
            serial_port.backing = backing

        connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            connected=True,
            startConnected=True,
            allowGuestControl=True,
        )
        serial_port.connectable = connectable

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=serial_port,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["backing_type"] = backing_type
        result["operation"] = "add_vm_serial_port"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def remove_vm_serial_port(
        vm_name: str,
        device_label: str = "Serial port 1",
    ) -> dict[str, Any]:
        """Remove a serial port from a VM by its device label.

        Args:
            vm_name: Name of the VM.
            device_label: Label of the serial port device (e.g. 'Serial port 1').
        """
        logger.info("remove_vm_serial_port", vm_name=vm_name, device_label=device_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        target = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualSerialPort):
                label = getattr(getattr(dev, "deviceInfo", None), "label", None)
                if label == device_label:
                    target = dev
                    break
        if target is None:
            return {
                "status": "error",
                "error": f"Serial port '{device_label}' not found on VM '{vm_name}'",
            }

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=target,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["device_label"] = device_label
        result["operation"] = "remove_vm_serial_port"
        return result

    @mcp.tool()
    @handle_tool_errors
    def list_vm_serial_ports(vm_name: str) -> dict[str, Any]:
        """List all serial ports on a VM with backing type and connection info.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("list_vm_serial_ports", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        ports = []
        for dev in devices:
            if not isinstance(dev, vim.vm.device.VirtualSerialPort):
                continue
            label = getattr(getattr(dev, "deviceInfo", None), "label", None)
            backing = getattr(dev, "backing", None)
            backing_type = type(backing).__name__ if backing is not None else None
            connectable = getattr(dev, "connectable", None)

            entry: dict[str, Any] = {
                "label": label,
                "key": getattr(dev, "key", None),
                "backing_type": backing_type,
                "connected": getattr(connectable, "connected", None),
                "start_connected": getattr(connectable, "startConnected", None),
            }

            if isinstance(backing, vim.vm.device.VirtualSerialPort.URIBackingInfo):
                entry["uri"] = getattr(backing, "serviceURI", None)
                entry["direction"] = getattr(backing, "direction", None)
            elif isinstance(backing, vim.vm.device.VirtualSerialPort.FileBackingInfo):
                entry["file_path"] = getattr(backing, "fileName", None)
            elif isinstance(backing, vim.vm.device.VirtualSerialPort.PipeBackingInfo):
                entry["pipe_name"] = getattr(backing, "pipeName", None)

            ports.append(entry)

        return {"status": "success", "vm_name": vm_name, "serial_ports": ports}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_parallel_port(vm_name: str, file_path: str) -> dict[str, Any]:
        """Add a parallel port with file backing to a VM.

        Args:
            vm_name: Name of the VM.
            file_path: Path to the file to use as the parallel port backing.
        """
        logger.info("add_vm_parallel_port", vm_name=vm_name, file_path=file_path)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        backing = vim.vm.device.VirtualParallelPort.FileBackingInfo()
        backing.fileName = file_path

        parallel_port = vim.vm.device.VirtualParallelPort()
        parallel_port.backing = backing

        connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            connected=True,
            startConnected=True,
            allowGuestControl=True,
        )
        parallel_port.connectable = connectable

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=parallel_port,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["file_path"] = file_path
        result["operation"] = "add_vm_parallel_port"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def remove_vm_parallel_port(
        vm_name: str,
        device_label: str = "Parallel port 1",
    ) -> dict[str, Any]:
        """Remove a parallel port from a VM by its device label.

        Args:
            vm_name: Name of the VM.
            device_label: Label of the parallel port device (e.g. 'Parallel port 1').
        """
        logger.info("remove_vm_parallel_port", vm_name=vm_name, device_label=device_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        target = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualParallelPort):
                label = getattr(getattr(dev, "deviceInfo", None), "label", None)
                if label == device_label:
                    target = dev
                    break
        if target is None:
            return {
                "status": "error",
                "error": f"Parallel port '{device_label}' not found on VM '{vm_name}'",
            }

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=target,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["device_label"] = device_label
        result["operation"] = "remove_vm_parallel_port"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_usb_controller(vm_name: str, usb_type: str = "usb3") -> dict[str, Any]:
        """Add a USB controller to a VM.

        Args:
            vm_name: Name of the VM.
            usb_type: USB controller type. 'usb2' adds a VirtualUSBController (EHCI),
                      'usb3' adds a VirtualUSBXHCIController (xHCI). Default is 'usb3'.
        """
        logger.info("add_vm_usb_controller", vm_name=vm_name, usb_type=usb_type)
        valid_types = {"usb2", "usb3"}
        if usb_type not in valid_types:
            return {
                "status": "error",
                "error": f"Invalid usb_type '{usb_type}'. Valid: {sorted(valid_types)}",
            }

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        if usb_type == "usb2":
            controller = vim.vm.device.VirtualUSBController()
        else:
            controller = vim.vm.device.VirtualUSBXHCIController()

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=controller,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["usb_type"] = usb_type
        result["operation"] = "add_vm_usb_controller"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_usb_device(vm_name: str) -> dict[str, Any]:
        """Add a USB passthrough device to a VM.

        The VM must have a USB controller already attached.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("add_vm_usb_device", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        usb_controller_key = None
        for dev in devices:
            if isinstance(dev, (vim.vm.device.VirtualUSBController, vim.vm.device.VirtualUSBXHCIController)):
                usb_controller_key = dev.key
                break
        if usb_controller_key is None:
            return {
                "status": "error",
                "error": f"No USB controller found on VM '{vm_name}'. Add a USB controller first.",
            }

        usb_device = vim.vm.device.VirtualUSB()
        usb_device.controllerKey = usb_controller_key
        usb_device.connected = True

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=usb_device,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["usb_controller_key"] = usb_controller_key
        result["operation"] = "add_vm_usb_device"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def remove_vm_usb_device(vm_name: str, device_label: str) -> dict[str, Any]:
        """Remove a USB device from a VM by its device label.

        Args:
            vm_name: Name of the VM.
            device_label: Label of the USB device to remove (e.g. 'USB device 1').
        """
        logger.info("remove_vm_usb_device", vm_name=vm_name, device_label=device_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        target = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualUSB):
                label = getattr(getattr(dev, "deviceInfo", None), "label", None)
                if label == device_label:
                    target = dev
                    break
        if target is None:
            return {
                "status": "error",
                "error": f"USB device '{device_label}' not found on VM '{vm_name}'",
            }

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=target,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["device_label"] = device_label
        result["operation"] = "remove_vm_usb_device"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_floppy_drive(vm_name: str, image_path: str = "") -> dict[str, Any]:
        """Add a floppy drive to a VM, optionally with an image file backing.

        Args:
            vm_name: Name of the VM.
            image_path: Path to a floppy image file (e.g. '[datastore] path/to/image.flp').
                        If empty, a remote/client device backing is used instead.
        """
        logger.info("add_vm_floppy_drive", vm_name=vm_name, image_path=image_path)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        floppy = vim.vm.device.VirtualFloppy()

        if image_path:
            backing = vim.vm.device.VirtualFloppy.ImageBackingInfo()
            backing.fileName = image_path
            floppy.backing = backing
        else:
            backing = vim.vm.device.VirtualFloppy.RemoteDeviceBackingInfo()
            backing.deviceName = ""
            floppy.backing = backing

        connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            connected=bool(image_path),
            startConnected=bool(image_path),
            allowGuestControl=True,
        )
        floppy.connectable = connectable

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=floppy,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["image_path"] = image_path
        result["operation"] = "add_vm_floppy_drive"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def remove_vm_floppy_drive(
        vm_name: str,
        device_label: str = "Floppy drive 1",
    ) -> dict[str, Any]:
        """Remove a floppy drive from a VM by its device label.

        Args:
            vm_name: Name of the VM.
            device_label: Label of the floppy drive device (e.g. 'Floppy drive 1').
        """
        logger.info("remove_vm_floppy_drive", vm_name=vm_name, device_label=device_label)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        target = None
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualFloppy):
                label = getattr(getattr(dev, "deviceInfo", None), "label", None)
                if label == device_label:
                    target = dev
                    break
        if target is None:
            return {
                "status": "error",
                "error": f"Floppy drive '{device_label}' not found on VM '{vm_name}'",
            }

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=target,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["device_label"] = device_label
        result["operation"] = "remove_vm_floppy_drive"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_vm_shared_folders(
        vm_name: str,
        share_name: str,
        host_path: str,
        writable: bool = True,
    ) -> dict[str, Any]:
        """Configure an HGFS shared folder on a VM (requires VMware Tools).

        Args:
            vm_name: Name of the VM.
            share_name: Name to assign to the shared folder inside the guest.
            host_path: Absolute path on the host to share with the guest.
            writable: Whether the guest can write to the shared folder. Default True.
        """
        logger.info(
            "configure_vm_shared_folders",
            vm_name=vm_name,
            share_name=share_name,
            host_path=host_path,
            writable=writable,
        )
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        # HGFS shared folders are configured via VM extraConfig options
        extra_config = [
            vim.option.OptionValue(key="isolation.tools.hgfs.disable", value="FALSE"),
            vim.option.OptionValue(key="sharedFolder0.present", value="TRUE"),
            vim.option.OptionValue(key="sharedFolder0.enabled", value="TRUE"),
            vim.option.OptionValue(key="sharedFolder0.readAccess", value="TRUE"),
            vim.option.OptionValue(key="sharedFolder0.writeAccess", value=str(writable).upper()),
            vim.option.OptionValue(key="sharedFolder0.hostPath", value=host_path),
            vim.option.OptionValue(key="sharedFolder0.guestName", value=share_name),
            vim.option.OptionValue(key="sharedFolder.maxNum", value="1"),
        ]

        config_spec = vim.vm.ConfigSpec(extraConfig=extra_config)
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["share_name"] = share_name
        result["host_path"] = host_path
        result["writable"] = writable
        result["operation"] = "configure_vm_shared_folders"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_vm_nvme_controller(vm_name: str) -> dict[str, Any]:
        """Add an NVMe controller to a VM.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("add_vm_nvme_controller", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        existing_bus_numbers: set[int] = set()
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualNVMEController):
                existing_bus_numbers.add(dev.busNumber)

        bus_number = 0
        while bus_number in existing_bus_numbers:
            bus_number += 1

        controller = vim.vm.device.VirtualNVMEController()
        controller.busNumber = bus_number

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=controller,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].Reconfigure(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["bus_number"] = bus_number
        result["operation"] = "add_vm_nvme_controller"
        return result
