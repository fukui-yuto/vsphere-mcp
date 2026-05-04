import pytest
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.tools.inventory import (
    VM_DETAIL_PROPS,
    VM_LIST_PROPS,
    HOST_PROPS,
    _format_host,
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
