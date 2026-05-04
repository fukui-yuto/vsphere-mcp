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


class TestCloneVM:
    def test_clone_vm(self, client: VSphereClient, vm_name: str) -> None:
        found = find_vm_with_props(client, vm_name)
        assert found is not None
        vm_obj = found["_obj"]
        folder = vm_obj.parent
        relocate_spec = vim.vm.RelocateSpec()
        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=False,
            template=False,
        )
        task = vm_obj.Clone(folder=folder, name="test-clone-vm", spec=clone_spec)
        result = wait_for_task(task)
        assert result["status"] == "success"

    def test_clone_exists(self, client: VSphereClient) -> None:
        found = find_vm_with_props(client, "test-clone-vm")
        assert found is not None

    def test_delete_clone(self, client: VSphereClient) -> None:
        found = find_vm_with_props(client, "test-clone-vm")
        assert found is not None
        # Ensure powered off first
        power_state = str(found.get("runtime.powerState", ""))
        if power_state != "poweredOff":
            task = found["_obj"].PowerOff()
            wait_for_task(task)
            found = find_vm_with_props(client, "test-clone-vm")
        task = found["_obj"].Destroy()
        result = wait_for_task(task)
        assert result["status"] == "success"
