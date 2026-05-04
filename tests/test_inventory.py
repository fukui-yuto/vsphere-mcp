import pytest
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.tools.inventory import (
    CLUSTER_PROPS,
    DATACENTER_PROPS,
    DATASTORE_PROPS,
    HOST_PROPS,
    NETWORK_PROPS,
    VM_DETAIL_PROPS,
    VM_LIST_PROPS,
    _format_cluster,
    _format_datacenter,
    _format_datastore,
    _format_host,
    _format_network,
    _format_vm_detail,
    _format_vm_list,
)
from vsphere_mcp.utils.property_collector import collect_properties


@pytest.fixture(scope="module")
def client(vsphere_client: VSphereClient) -> VSphereClient:
    return vsphere_client


class TestListVMs:
    def test_returns_list(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.VirtualMachine, VM_LIST_PROPS)
        vms = [_format_vm_list(item) for item in items]
        assert isinstance(vms, list)
        assert len(vms) > 0

    def test_vm_has_required_fields(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.VirtualMachine, VM_LIST_PROPS)
        vm_dict = _format_vm_list(items[0])
        required = {"name", "power_state", "num_cpu", "memory_mb"}
        assert required.issubset(vm_dict.keys())


class TestGetVMInfo:
    def test_existing_vm(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.VirtualMachine, VM_DETAIL_PROPS)
        detail = _format_vm_detail(items[0])
        assert detail["name"] is not None
        assert "disks" in detail
        assert "nics" in detail
        assert "storage" in detail

    def test_nonexistent_vm(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.VirtualMachine, VM_DETAIL_PROPS)
        names = [item.get("name") for item in items]
        assert "nonexistent-vm-12345" not in names


class TestListHosts:
    def test_returns_list(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.HostSystem, HOST_PROPS)
        hosts = [_format_host(item) for item in items]
        assert isinstance(hosts, list)
        assert len(hosts) > 0

    def test_host_has_required_fields(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.HostSystem, HOST_PROPS)
        host_dict = _format_host(items[0])
        required = {"name", "connection_state", "power_state", "num_cpu_cores", "memory_gb"}
        assert required.issubset(host_dict.keys())


class TestListDatacenters:
    def test_returns_list(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.Datacenter, DATACENTER_PROPS)
        dcs = [_format_datacenter(item) for item in items]
        assert isinstance(dcs, list)
        assert len(dcs) > 0
        assert dcs[0]["name"] is not None


class TestListClusters:
    def test_returns_list(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.ClusterComputeResource, CLUSTER_PROPS)
        clusters = [_format_cluster(item) for item in items]
        assert isinstance(clusters, list)
        assert len(clusters) > 0

    def test_cluster_has_required_fields(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.ClusterComputeResource, CLUSTER_PROPS)
        cluster_dict = _format_cluster(items[0])
        required = {"name", "total_cpu_mhz", "total_memory_gb", "num_cpu_cores"}
        assert required.issubset(cluster_dict.keys())


class TestListDatastores:
    def test_returns_list(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.Datastore, DATASTORE_PROPS)
        datastores = [_format_datastore(item) for item in items]
        assert isinstance(datastores, list)
        assert len(datastores) > 0

    def test_datastore_has_required_fields(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.Datastore, DATASTORE_PROPS)
        ds_dict = _format_datastore(items[0])
        required = {"name", "capacity_gb", "free_gb"}
        assert required.issubset(ds_dict.keys())


class TestListNetworks:
    def test_returns_list(self, client: VSphereClient) -> None:
        items = collect_properties(client, vim.Network, NETWORK_PROPS)
        networks = [_format_network(item) for item in items]
        assert isinstance(networks, list)
        assert len(networks) > 0
