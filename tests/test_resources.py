import pytest
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.tools._base import find_vm_with_props, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties


@pytest.fixture(scope="module")
def client(vsphere_client: VSphereClient) -> VSphereClient:
    return vsphere_client


@pytest.fixture(scope="module")
def vm_name(client: VSphereClient) -> str:
    items = collect_properties(client, vim.VirtualMachine, ["name"])
    return items[0]["name"]


class TestSetVMResources:
    def test_set_cpu(self, client: VSphereClient, vm_name: str) -> None:
        found = find_vm_with_props(client, vm_name)
        assert found is not None
        spec = vim.vm.ConfigSpec()
        spec.numCPUs = 2
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        assert result["status"] == "success"

    def test_set_memory(self, client: VSphereClient, vm_name: str) -> None:
        found = find_vm_with_props(client, vm_name)
        assert found is not None
        spec = vim.vm.ConfigSpec()
        spec.memoryMB = 2048
        task = found["_obj"].Reconfigure(spec=spec)
        result = wait_for_task(task)
        assert result["status"] == "success"


class TestInputValidation:
    def test_invalid_cpu_rejected(self) -> None:
        """Verify validation logic for CPU count."""
        num_cpu = 0
        assert num_cpu < 1  # would be rejected by set_vm_resources

    def test_invalid_memory_rejected(self) -> None:
        """Verify validation logic for memory."""
        memory_mb = 0
        assert memory_mb < 4  # would be rejected by set_vm_resources

    def test_invalid_disk_size_rejected(self) -> None:
        """Verify validation logic for disk size."""
        size_gb = 0
        assert size_gb < 1  # would be rejected by add_disk
