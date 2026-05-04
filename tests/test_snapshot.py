import pytest
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.tools.power import _find_vm_with_props, _wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties


@pytest.fixture(scope="module")
def client(vsphere_client: VSphereClient) -> VSphereClient:
    return vsphere_client


@pytest.fixture(scope="module")
def vm_name(client: VSphereClient) -> str:
    items = collect_properties(client, vim.VirtualMachine, ["name"])
    return items[0]["name"]


class TestSnapshotOperations:
    def test_create_snapshot(self, client: VSphereClient, vm_name: str) -> None:
        found = _find_vm_with_props(client, vm_name)
        assert found is not None
        task = found["_obj"].CreateSnapshot(name="test-snap", description="test", memory=False, quiesce=False)
        result = _wait_for_task(task)
        assert result["status"] == "success"

    def test_list_snapshots(self, client: VSphereClient, vm_name: str) -> None:
        found = _find_vm_with_props(client, vm_name, ["snapshot"])
        assert found is not None
        snap_info = found.get("snapshot")
        if snap_info and hasattr(snap_info, "rootSnapshotList"):
            assert len(snap_info.rootSnapshotList) > 0

    def test_remove_snapshot(self, client: VSphereClient, vm_name: str) -> None:
        found = _find_vm_with_props(client, vm_name, ["snapshot"])
        assert found is not None
        snap_info = found.get("snapshot")
        if snap_info and hasattr(snap_info, "rootSnapshotList") and snap_info.rootSnapshotList:
            snap = snap_info.rootSnapshotList[0].snapshot
            task = snap.RemoveSnapshot_Task(removeChildren=True)
            result = _wait_for_task(task)
            assert result["status"] == "success"
