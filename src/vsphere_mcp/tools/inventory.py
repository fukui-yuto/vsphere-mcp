from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)

VM_LIST_PROPS = [
    "name",
    "runtime.powerState",
    "config.hardware.numCPU",
    "config.hardware.memoryMB",
    "config.guestFullName",
    "guest.ipAddress",
    "runtime.host",
    "config.template",
]

VM_DETAIL_PROPS = VM_LIST_PROPS + [
    "guest.hostName",
    "config.uuid",
    "config.instanceUuid",
    "config.files.vmPathName",
    "config.annotation",
    "summary.storage.committed",
    "summary.storage.uncommitted",
    "config.hardware.device",
    "guest.toolsStatus",
]

HOST_PROPS = [
    "name",
    "runtime.connectionState",
    "runtime.powerState",
    "summary.hardware.vendor",
    "summary.hardware.model",
    "summary.hardware.cpuModel",
    "summary.hardware.numCpuPkgs",
    "summary.hardware.numCpuCores",
    "summary.hardware.numCpuThreads",
    "summary.hardware.cpuMhz",
    "summary.hardware.memorySize",
    "vm",
]


def _format_vm_list(data: dict[str, Any]) -> dict[str, Any]:
    host_ref = data.get("runtime.host")
    return {
        "name": data.get("name"),
        "power_state": str(data.get("runtime.powerState", "")),
        "num_cpu": data.get("config.hardware.numCPU"),
        "memory_mb": data.get("config.hardware.memoryMB"),
        "guest_os": data.get("config.guestFullName"),
        "ip_address": data.get("guest.ipAddress"),
        "host": host_ref.name if host_ref else None,
        "template": data.get("config.template", False),
    }


def _format_vm_detail(data: dict[str, Any]) -> dict[str, Any]:
    host_ref = data.get("runtime.host")
    committed = data.get("summary.storage.committed")
    uncommitted = data.get("summary.storage.uncommitted")

    disks: list[dict[str, Any]] = []
    nics: list[dict[str, Any]] = []
    devices = data.get("config.hardware.device", [])
    if devices:
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                cap = 0.0
                if hasattr(dev, "capacityInBytes") and dev.capacityInBytes:
                    cap = round(dev.capacityInBytes / (1024**3), 2)
                elif dev.capacityInKB:
                    cap = round(dev.capacityInKB / (1024**2), 2)
                disks.append({"label": dev.deviceInfo.label, "capacity_gb": cap})
            elif isinstance(dev, vim.vm.device.VirtualEthernetCard):
                net = ""
                if hasattr(dev.backing, "deviceName"):
                    net = dev.backing.deviceName
                nics.append({"label": dev.deviceInfo.label, "mac_address": dev.macAddress, "network": net})

    return {
        "name": data.get("name"),
        "power_state": str(data.get("runtime.powerState", "")),
        "num_cpu": data.get("config.hardware.numCPU"),
        "memory_mb": data.get("config.hardware.memoryMB"),
        "guest_os": data.get("config.guestFullName"),
        "ip_address": data.get("guest.ipAddress"),
        "hostname": data.get("guest.hostName"),
        "host": host_ref.name if host_ref else None,
        "template": data.get("config.template", False),
        "uuid": data.get("config.uuid"),
        "instance_uuid": data.get("config.instanceUuid"),
        "path": data.get("config.files.vmPathName"),
        "annotation": data.get("config.annotation"),
        "storage": {
            "committed_gb": round(committed / (1024**3), 2) if committed else 0,
            "uncommitted_gb": round(uncommitted / (1024**3), 2) if uncommitted else 0,
        },
        "disks": disks,
        "nics": nics,
        "tools_status": str(data.get("guest.toolsStatus", "")),
    }


def _format_host(data: dict[str, Any]) -> dict[str, Any]:
    mem = data.get("summary.hardware.memorySize")
    vms = data.get("vm", [])
    return {
        "name": data.get("name"),
        "connection_state": str(data.get("runtime.connectionState", "")),
        "power_state": str(data.get("runtime.powerState", "")),
        "vendor": data.get("summary.hardware.vendor"),
        "model": data.get("summary.hardware.model"),
        "cpu_model": data.get("summary.hardware.cpuModel"),
        "num_cpu_packages": data.get("summary.hardware.numCpuPkgs"),
        "num_cpu_cores": data.get("summary.hardware.numCpuCores"),
        "num_cpu_threads": data.get("summary.hardware.numCpuThreads"),
        "cpu_mhz": data.get("summary.hardware.cpuMhz"),
        "memory_gb": round(mem / (1024**3), 2) if mem else 0,
        "num_vms": len(vms) if vms else 0,
    }


def register_inventory_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    def list_vms(
        host: str | None = None,
        cluster: str | None = None,
    ) -> list[dict[str, Any]]:
        """List all virtual machines. Optionally filter by host or cluster name."""
        logger.info("list_vms", host=host, cluster=cluster)
        items = collect_properties(client, vim.VirtualMachine, VM_LIST_PROPS)
        vms = []
        for item in items:
            host_ref = item.get("runtime.host")
            if host and host_ref and host_ref.name != host:
                continue
            if cluster and host_ref and hasattr(host_ref, "parent") and host_ref.parent and host_ref.parent.name != cluster:
                continue
            vms.append(_format_vm_list(item))
        return vms

    @mcp.tool()
    def get_vm_info(vm_name: str) -> dict[str, Any]:
        """Get detailed information for a specific virtual machine by name."""
        logger.info("get_vm_info", vm_name=vm_name)
        items = collect_properties(client, vim.VirtualMachine, VM_DETAIL_PROPS)
        for item in items:
            if item.get("name") == vm_name:
                return _format_vm_detail(item)
        return {"error": f"VM '{vm_name}' not found"}

    @mcp.tool()
    def list_hosts(cluster: str | None = None) -> list[dict[str, Any]]:
        """List all ESXi hosts. Optionally filter by cluster name."""
        logger.info("list_hosts", cluster=cluster)
        items = collect_properties(client, vim.HostSystem, HOST_PROPS)
        hosts = []
        for item in items:
            obj = item["_obj"]
            if cluster and hasattr(obj, "parent") and obj.parent and obj.parent.name != cluster:
                continue
            hosts.append(_format_host(item))
        return hosts
