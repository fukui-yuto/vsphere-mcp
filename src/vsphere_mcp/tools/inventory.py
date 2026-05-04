from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors
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

DATACENTER_PROPS = [
    "name",
]

DATACENTER_DETAIL_PROPS = [
    "name",
    "vmFolder",
    "hostFolder",
    "datastoreFolder",
    "networkFolder",
]

CLUSTER_PROPS = [
    "name",
    "summary.totalCpu",
    "summary.totalMemory",
    "summary.numCpuCores",
    "summary.numCpuThreads",
    "summary.numHosts",
    "summary.numEffectiveHosts",
    "host",
]

DATASTORE_PROPS = [
    "name",
    "summary.type",
    "summary.capacity",
    "summary.freeSpace",
    "summary.accessible",
    "summary.url",
]

NETWORK_PROPS = [
    "name",
]

RESOURCE_POOL_PROPS = [
    "name",
    "summary.config.cpuAllocation.reservation",
    "summary.config.cpuAllocation.limit",
    "summary.config.memoryAllocation.reservation",
    "summary.config.memoryAllocation.limit",
    "summary.runtime.cpu.overallUsage",
    "summary.runtime.memory.overallUsage",
    "vm",
]

DVSWITCH_PROPS = [
    "name",
    "summary.numPorts",
    "summary.numHosts",
    "config.uplinkPortgroup",
    "uuid",
]

DVPORTGROUP_PROPS = [
    "name",
    "config.defaultPortConfig",
    "summary.ipPoolName",
]

SNAPSHOT_PROPS = [
    "name",
    "snapshot",
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
                nics.append(
                    {
                        "label": dev.deviceInfo.label,
                        "mac_address": dev.macAddress,
                        "network": net,
                    }
                )

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


def _format_datacenter(data: dict[str, Any]) -> dict[str, Any]:
    return {"name": data.get("name")}


def _format_cluster(data: dict[str, Any]) -> dict[str, Any]:
    total_mem = data.get("summary.totalMemory")
    hosts = data.get("host", [])
    return {
        "name": data.get("name"),
        "total_cpu_mhz": data.get("summary.totalCpu"),
        "total_memory_gb": round(total_mem / (1024**3), 2) if total_mem else 0,
        "num_cpu_cores": data.get("summary.numCpuCores"),
        "num_cpu_threads": data.get("summary.numCpuThreads"),
        "num_hosts": data.get("summary.numHosts"),
        "num_effective_hosts": data.get("summary.numEffectiveHosts"),
        "num_hosts_actual": len(hosts) if hosts else 0,
    }


def _format_datastore(data: dict[str, Any]) -> dict[str, Any]:
    capacity = data.get("summary.capacity")
    free = data.get("summary.freeSpace")
    return {
        "name": data.get("name"),
        "type": data.get("summary.type"),
        "capacity_gb": round(capacity / (1024**3), 2) if capacity else 0,
        "free_gb": round(free / (1024**3), 2) if free else 0,
        "used_gb": round((capacity - free) / (1024**3), 2) if capacity and free else 0,
        "accessible": data.get("summary.accessible"),
        "url": data.get("summary.url"),
    }


def _format_network(data: dict[str, Any]) -> dict[str, Any]:
    return {"name": data.get("name")}


def _format_resource_pool(data: dict[str, Any]) -> dict[str, Any]:
    vms = data.get("vm", [])
    return {
        "name": data.get("name"),
        "cpu_reservation_mhz": data.get("summary.config.cpuAllocation.reservation"),
        "cpu_limit_mhz": data.get("summary.config.cpuAllocation.limit"),
        "memory_reservation_mb": data.get("summary.config.memoryAllocation.reservation"),
        "memory_limit_mb": data.get("summary.config.memoryAllocation.limit"),
        "cpu_usage_mhz": data.get("summary.runtime.cpu.overallUsage"),
        "memory_usage_mb": data.get("summary.runtime.memory.overallUsage"),
        "num_vms": len(vms) if vms else 0,
    }


def _format_dvswitch(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": data.get("name"),
        "uuid": data.get("uuid"),
        "num_ports": data.get("summary.numPorts"),
        "num_hosts": data.get("summary.numHosts"),
    }


def _format_dvportgroup(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": data.get("name"),
    }


def _walk_snapshots(snapshot_tree: list[Any], result: list[dict[str, Any]], depth: int = 0) -> None:
    for snap in snapshot_tree:
        result.append(
            {
                "name": snap.name,
                "description": snap.description,
                "create_time": str(snap.createTime),
                "state": str(snap.state),
                "quiesced": snap.quiesced,
                "depth": depth,
            }
        )
        if snap.childSnapshotList:
            _walk_snapshots(snap.childSnapshotList, result, depth + 1)


def register_inventory_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def test_connection() -> dict[str, Any]:
        """Test the vSphere connection and return server information."""
        logger.info("test_connection")
        content = client.content
        about = content.about
        return {
            "status": "connected",
            "server": about.fullName,
            "api_version": about.apiVersion,
            "build": about.build,
            "instance_uuid": about.instanceUuid,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_vms(
        host: str | None = None,
        cluster: str | None = None,
        limit: int = 0,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all virtual machines. Filter by host/cluster. Supports pagination with limit/offset."""
        logger.info("list_vms", host=host, cluster=cluster, limit=limit, offset=offset)
        items = collect_properties(client, vim.VirtualMachine, VM_LIST_PROPS)
        vms = []
        for item in items:
            host_ref = item.get("runtime.host")
            if host and host_ref and host_ref.name != host:
                continue
            if cluster and host_ref and hasattr(host_ref, "parent"):
                if host_ref.parent and host_ref.parent.name != cluster:
                    continue
            vms.append(_format_vm_list(item))
        total = len(vms)
        if offset > 0:
            vms = vms[offset:]
        if limit > 0:
            vms = vms[:limit]
        return {"total": total, "offset": offset, "limit": limit, "vms": vms}

    @mcp.tool()
    @handle_tool_errors
    def get_vm_info(vm_name: str) -> dict[str, Any]:
        """Get detailed information for a specific virtual machine by name."""
        logger.info("get_vm_info", vm_name=vm_name)
        items = collect_properties(client, vim.VirtualMachine, VM_DETAIL_PROPS)
        for item in items:
            if item.get("name") == vm_name:
                return _format_vm_detail(item)
        return {"status": "error", "error": f"VM '{vm_name}' not found"}

    @mcp.tool()
    @handle_tool_errors
    def list_hosts(cluster: str | None = None) -> list[dict[str, Any]]:
        """List all ESXi hosts. Optionally filter by cluster name."""
        logger.info("list_hosts", cluster=cluster)
        items = collect_properties(client, vim.HostSystem, HOST_PROPS)
        hosts = []
        for item in items:
            obj = item["_obj"]
            if cluster and hasattr(obj, "parent") and obj.parent:
                if obj.parent.name != cluster:
                    continue
            hosts.append(_format_host(item))
        return hosts

    @mcp.tool()
    @handle_tool_errors
    def get_host_info(host_name: str) -> dict[str, Any]:
        """Get detailed information for a specific ESXi host by name."""
        logger.info("get_host_info", host_name=host_name)
        items = collect_properties(client, vim.HostSystem, HOST_PROPS)
        for item in items:
            if item.get("name") == host_name:
                return _format_host(item)
        return {"status": "error", "error": f"Host '{host_name}' not found"}

    @mcp.tool()
    @handle_tool_errors
    def list_datacenters() -> list[dict[str, Any]]:
        """List all datacenters in vCenter."""
        logger.info("list_datacenters")
        items = collect_properties(client, vim.Datacenter, DATACENTER_PROPS)
        return [_format_datacenter(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def list_clusters(datacenter: str | None = None) -> list[dict[str, Any]]:
        """List all clusters. Optionally filter by datacenter name."""
        logger.info("list_clusters", datacenter=datacenter)
        items = collect_properties(client, vim.ClusterComputeResource, CLUSTER_PROPS)
        if datacenter:
            filtered = []
            for item in items:
                obj = item["_obj"]
                parent = obj.parent
                while parent:
                    if isinstance(parent, vim.Datacenter) and parent.name == datacenter:
                        filtered.append(item)
                        break
                    parent = parent.parent
            items = filtered
        return [_format_cluster(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def list_datastores() -> list[dict[str, Any]]:
        """List all datastores."""
        logger.info("list_datastores")
        items = collect_properties(client, vim.Datastore, DATASTORE_PROPS)
        return [_format_datastore(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def list_networks() -> list[dict[str, Any]]:
        """List all networks (port groups)."""
        logger.info("list_networks")
        items = collect_properties(client, vim.Network, NETWORK_PROPS)
        return [_format_network(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def list_snapshots(vm_name: str) -> dict[str, Any]:
        """List all snapshots for a virtual machine."""
        logger.info("list_snapshots", vm_name=vm_name)
        items = collect_properties(client, vim.VirtualMachine, SNAPSHOT_PROPS)
        for item in items:
            if item.get("name") == vm_name:
                snap_info = item.get("snapshot")
                if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
                    return {"vm_name": vm_name, "snapshots": []}
                result: list[dict[str, Any]] = []
                _walk_snapshots(snap_info.rootSnapshotList, result)
                return {"vm_name": vm_name, "snapshots": result}
        return {"status": "error", "error": f"VM '{vm_name}' not found"}

    @mcp.tool()
    @handle_tool_errors
    def get_cluster_health(cluster_name: str) -> dict[str, Any]:
        """Get health summary for a cluster including CPU/memory utilization."""
        logger.info("get_cluster_health", cluster_name=cluster_name)
        items = collect_properties(client, vim.ClusterComputeResource, CLUSTER_PROPS)
        for item in items:
            if item.get("name") == cluster_name:
                cluster_data = _format_cluster(item)
                host_items = collect_properties(client, vim.HostSystem, HOST_PROPS)
                cluster_hosts = []
                for h in host_items:
                    obj = h["_obj"]
                    if hasattr(obj, "parent") and obj.parent:
                        if obj.parent.name == cluster_name:
                            cluster_hosts.append(_format_host(h))
                cluster_data["hosts"] = cluster_hosts
                return cluster_data
        return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

    @mcp.tool()
    @handle_tool_errors
    def search_vms(query: str) -> list[dict[str, Any]]:
        """Search virtual machines by name (case-insensitive substring match)."""
        logger.info("search_vms", query=query)
        items = collect_properties(client, vim.VirtualMachine, VM_LIST_PROPS)
        query_lower = query.lower()
        return [_format_vm_list(item) for item in items if item.get("name") and query_lower in item["name"].lower()]

    @mcp.tool()
    @handle_tool_errors
    def list_resource_pools() -> list[dict[str, Any]]:
        """List all resource pools with CPU and memory allocation."""
        logger.info("list_resource_pools")
        items = collect_properties(client, vim.ResourcePool, RESOURCE_POOL_PROPS)
        return [_format_resource_pool(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def list_distributed_switches() -> list[dict[str, Any]]:
        """List all distributed virtual switches."""
        logger.info("list_distributed_switches")
        items = collect_properties(client, vim.DistributedVirtualSwitch, DVSWITCH_PROPS)
        return [_format_dvswitch(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def list_distributed_portgroups() -> list[dict[str, Any]]:
        """List all distributed virtual port groups."""
        logger.info("list_distributed_portgroups")
        items = collect_properties(client, vim.dvs.DistributedVirtualPortgroup, DVPORTGROUP_PROPS)
        return [_format_dvportgroup(item) for item in items]

    @mcp.tool()
    @handle_tool_errors
    def get_datacenter_info(datacenter_name: str) -> dict[str, Any]:
        """Get detailed datacenter info including folder names."""
        logger.info("get_datacenter_info", datacenter_name=datacenter_name)
        items = collect_properties(client, vim.Datacenter, DATACENTER_DETAIL_PROPS)
        for item in items:
            if item.get("name") == datacenter_name:
                vm_folder = item.get("vmFolder")
                host_folder = item.get("hostFolder")
                ds_folder = item.get("datastoreFolder")
                net_folder = item.get("networkFolder")
                return {
                    "name": datacenter_name,
                    "vmFolder": vm_folder.name if vm_folder else None,
                    "hostFolder": host_folder.name if host_folder else None,
                    "datastoreFolder": ds_folder.name if ds_folder else None,
                    "networkFolder": net_folder.name if net_folder else None,
                }
        return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}
