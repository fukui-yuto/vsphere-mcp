import pytest
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.tools._base import find_vm_with_props, wait_for_task


@pytest.fixture(scope="module")
def client(vsphere_client: VSphereClient) -> VSphereClient:
    return vsphere_client


@pytest.fixture(scope="module")
def vm_name(client: VSphereClient) -> str:
    from vsphere_mcp.utils.property_collector import collect_properties

    items = collect_properties(client, vim.VirtualMachine, ["name"])
    return items[0]["name"]


class TestFindVM:
    def test_find_existing(self, client: VSphereClient, vm_name: str) -> None:
        found = find_vm_with_props(client, vm_name)
        assert found is not None
        assert found.get("name") == vm_name

    def test_find_nonexistent(self, client: VSphereClient) -> None:
        found = find_vm_with_props(client, "nonexistent-vm-99999")
        assert found is None


class TestPowerOperations:
    def test_power_off_vm(self, client: VSphereClient, vm_name: str) -> None:
        found = find_vm_with_props(client, vm_name)
        assert found is not None
        power_state = str(found.get("runtime.powerState", ""))
        if power_state == "poweredOn":
            task = found["_obj"].PowerOff()
            result = wait_for_task(task)
            assert result["status"] == "success"

    def test_power_on_vm(self, client: VSphereClient, vm_name: str) -> None:
        found = find_vm_with_props(client, vm_name)
        assert found is not None
        power_state = str(found.get("runtime.powerState", ""))
        if power_state == "poweredOff":
            task = found["_obj"].PowerOn()
            result = wait_for_task(task)
            assert result["status"] == "success"
