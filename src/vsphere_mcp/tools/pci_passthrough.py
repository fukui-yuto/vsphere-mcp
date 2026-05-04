from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_pci_passthrough_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_host_pci_devices(
        host_name: str,
        passthrough_only: bool = False,
    ) -> dict[str, Any]:
        """List PCI devices on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            passthrough_only: If True, return only devices with passthrough enabled. Default False returns all PCI devices.
        """
        logger.info("list_host_pci_devices", host_name=host_name, passthrough_only=passthrough_only)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        hw = getattr(host_obj, "hardware", None)
        pci_devices = getattr(hw, "pciDevice", None) or []

        passthru_info_map: dict[str, Any] = {}
        cfg = getattr(host_obj, "config", None)
        if cfg is not None:
            for pt in getattr(cfg, "pciPassthruInfo", None) or []:
                passthru_info_map[pt.id] = pt

        result_list = []
        for dev in pci_devices:
            pt = passthru_info_map.get(dev.id)
            passthru_capable = pt is not None
            passthru_enabled = getattr(pt, "passthruEnabled", False) if pt is not None else False

            if passthrough_only and not passthru_enabled:
                continue

            result_list.append({
                "id": dev.id,
                "vendorName": getattr(dev, "vendorName", None),
                "deviceName": getattr(dev, "deviceName", None),
                "classId": getattr(dev, "classId", None),
                "passthruCapable": passthru_capable,
                "passthruEnabled": passthru_enabled,
            })

        return {
            "status": "success",
            "host_name": host_name,
            "passthrough_only": passthrough_only,
            "num_devices": len(result_list),
            "pci_devices": result_list,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def enable_pci_passthrough(
        host_name: str,
        device_id: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Enable or disable PCI passthrough for a device on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            device_id: PCI device ID (e.g. "0000:03:00.0").
            enabled: True to enable passthrough, False to disable (default True).

        Note: A host reboot is required for this change to take effect.
        """
        logger.info("enable_pci_passthrough", host_name=host_name, device_id=device_id, enabled=enabled)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}
        pci_passthru_system = getattr(cm, "pciPassthruSystem", None)
        if pci_passthru_system is None:
            return {"status": "error", "error": "pciPassthruSystem not available on this host"}

        config = vim.host.PciPassthruConfig(id=device_id, passthruEnabled=enabled)
        pci_passthru_system.UpdatePassthruConfig(config=[config])

        return {
            "status": "success",
            "operation": "enable_pci_passthrough",
            "host_name": host_name,
            "device_id": device_id,
            "enabled": enabled,
            "message": "Host reboot required for this change to take effect",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_pci_passthrough_to_vm(
        vm_name: str,
        device_id: str,
        host_name: str,
    ) -> dict[str, Any]:
        """Add a PCI passthrough device to a VM.

        Args:
            vm_name: Name of the VM to add the PCI device to.
            device_id: PCI device ID on the host (e.g. "0000:03:00.0").
            host_name: Name of the ESXi host that owns the PCI device.
        """
        logger.info("add_pci_passthrough_to_vm", vm_name=vm_name, device_id=device_id, host_name=host_name)

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        # Retrieve host system ID for backing
        host_system_id = ""
        cfg = getattr(host_obj, "config", None)
        if cfg is not None:
            host_system_id = getattr(cfg, "host", "") or ""
        # Fallback: use host managed object reference value
        if not host_system_id:
            try:
                host_system_id = host_obj._moId  # type: ignore[attr-defined]
            except Exception:
                host_system_id = ""

        backing = vim.vm.device.VirtualPCIPassthrough.DeviceBackingInfo(
            id=device_id,
            systemId=host_system_id,
        )
        pci_device = vim.vm.device.VirtualPCIPassthrough(backing=backing)

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=pci_device,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to add PCI passthrough device to VM")}

        return {
            "status": "success",
            "operation": "add_pci_passthrough_to_vm",
            "vm_name": vm_name,
            "device_id": device_id,
            "host_name": host_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_pci_device_from_vm(
        vm_name: str,
        device_label: str,
    ) -> dict[str, Any]:
        """Remove a PCI passthrough device from a VM by its device label.

        Args:
            vm_name: Name of the VM.
            device_label: Label of the PCI device to remove (e.g. "PCI device 1").
        """
        logger.info("remove_pci_device_from_vm", vm_name=vm_name, device_label=device_label)

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = getattr(found.get("config.hardware.device"), "__iter__", None)
        target_device = None
        if devices is not None:
            for dev in found.get("config.hardware.device") or []:
                if isinstance(dev, vim.vm.device.VirtualPCIPassthrough):
                    label = getattr(getattr(dev, "deviceInfo", None), "label", None)
                    if label == device_label:
                        target_device = dev
                        break

        if target_device is None:
            return {
                "status": "error",
                "error": f"PCI passthrough device '{device_label}' not found on VM '{vm_name}'",
            }

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.remove,
            device=target_device,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to remove PCI device from VM")}

        return {
            "status": "success",
            "operation": "remove_pci_device_from_vm",
            "vm_name": vm_name,
            "device_label": device_label,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_sriov_nics(host_name: str) -> dict[str, Any]:
        """List SR-IOV capable NICs on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("list_host_sriov_nics", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cfg = getattr(host_obj, "config", None)
        if cfg is None:
            return {"status": "error", "error": "config not available on this host"}
        network_cfg = getattr(cfg, "network", None)
        if network_cfg is None:
            return {"status": "error", "error": "network config not available on this host"}

        nics = []
        for pnic in getattr(network_cfg, "pnic", None) or []:
            sriov_capable = getattr(pnic, "sriovCapable", False)
            nics.append({
                "device": getattr(pnic, "device", None),
                "driver": getattr(pnic, "driver", None),
                "mac": getattr(pnic, "mac", None),
                "sriovCapable": sriov_capable,
                "numVirtualFunction": getattr(pnic, "numVirtualFunction", None),
                "numVirtualFunctionSupported": getattr(pnic, "numVirtualFunctionSupported", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "num_nics": len(nics),
            "nics": nics,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_gpu_devices(host_name: str) -> dict[str, Any]:
        """List GPU (display controller) PCI devices on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("list_host_gpu_devices", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        hw = getattr(host_obj, "hardware", None)
        pci_devices = getattr(hw, "pciDevice", None) or []

        # classId 0x0300 = Display controller (GPU)
        GPU_CLASS_ID = 0x0300
        gpus = []
        for dev in pci_devices:
            class_id = getattr(dev, "classId", None)
            if class_id is not None and (class_id & 0xFF00) == GPU_CLASS_ID:
                gpus.append({
                    "id": dev.id,
                    "deviceName": getattr(dev, "deviceName", None),
                    "vendorName": getattr(dev, "vendorName", None),
                    "classId": class_id,
                })

        return {
            "status": "success",
            "host_name": host_name,
            "num_gpus": len(gpus),
            "gpu_devices": gpus,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_vgpu_profiles(host_name: str) -> dict[str, Any]:
        """List vGPU profiles available on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("list_host_vgpu_profiles", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cfg = getattr(host_obj, "config", None)
        if cfg is None:
            return {"status": "error", "error": "config not available on this host"}

        profiles = []

        # Try sharedGpuCapabilities first (vSphere 7+)
        shared_gpu_caps = getattr(cfg, "sharedGpuCapabilities", None) or []
        for cap in shared_gpu_caps:
            profiles.append({
                "vgpu": getattr(cap, "vgpu", None),
                "diskSnapshotSupported": getattr(cap, "diskSnapshotSupported", None),
                "memSizeInKilobytes": getattr(cap, "memSizeInKilobytes", None),
                "maxFBSizeInKilobytes": getattr(cap, "maxFBSizeInKilobytes", None),
                "source": "sharedGpuCapabilities",
            })

        # Fallback: graphicsInfo
        if not profiles:
            graphics_info = getattr(cfg, "graphicsInfo", None) or []
            for info in graphics_info:
                vgpu_list = getattr(info, "vgpuMode", None) or []
                for vgpu in vgpu_list:
                    profiles.append({
                        "vgpu": getattr(vgpu, "vgpuMode", str(vgpu)),
                        "source": "graphicsInfo",
                    })

        return {
            "status": "success",
            "host_name": host_name,
            "num_profiles": len(profiles),
            "vgpu_profiles": profiles,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_vgpu_to_vm(
        vm_name: str,
        vgpu_profile: str,
    ) -> dict[str, Any]:
        """Add a vGPU profile to a VM.

        Args:
            vm_name: Name of the VM.
            vgpu_profile: vGPU profile name (e.g. "grid_v100-4q").
        """
        logger.info("add_vgpu_to_vm", vm_name=vm_name, vgpu_profile=vgpu_profile)

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        backing = vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo(vgpu=vgpu_profile)
        pci_device = vim.vm.device.VirtualPCIPassthrough(backing=backing)

        device_spec = vim.vm.device.VirtualDeviceSpec(
            operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
            device=pci_device,
        )
        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to add vGPU to VM")}

        return {
            "status": "success",
            "operation": "add_vgpu_to_vm",
            "vm_name": vm_name,
            "vgpu_profile": vgpu_profile,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vm_pci_devices(vm_name: str) -> dict[str, Any]:
        """List PCI passthrough and vGPU devices attached to a VM.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("get_vm_pci_devices", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        pci_devices = []
        for dev in found.get("config.hardware.device") or []:
            if not isinstance(dev, vim.vm.device.VirtualPCIPassthrough):
                continue

            device_info = getattr(dev, "deviceInfo", None)
            label = getattr(device_info, "label", None)
            backing = getattr(dev, "backing", None)
            backing_type = type(backing).__name__ if backing is not None else None

            entry: dict[str, Any] = {
                "label": label,
                "key": getattr(dev, "key", None),
                "backingType": backing_type,
            }

            if isinstance(backing, vim.vm.device.VirtualPCIPassthrough.DeviceBackingInfo):
                entry["deviceId"] = getattr(backing, "id", None)
                entry["systemId"] = getattr(backing, "systemId", None)
            elif isinstance(backing, vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo):
                entry["vgpuProfile"] = getattr(backing, "vgpu", None)

            pci_devices.append(entry)

        return {
            "status": "success",
            "vm_name": vm_name,
            "num_pci_devices": len(pci_devices),
            "pci_devices": pci_devices,
        }
