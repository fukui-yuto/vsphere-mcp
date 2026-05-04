import pytest
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.tools._base import find_host_by_name, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties


@pytest.fixture(scope="module")
def client(vsphere_client: VSphereClient) -> VSphereClient:
    return vsphere_client


@pytest.fixture(scope="module")
def host_name(client: VSphereClient) -> str:
    items = collect_properties(client, vim.HostSystem, ["name"])
    return items[0]["name"]


class TestHostOperations:
    def test_find_host(self, client: VSphereClient, host_name: str) -> None:
        host = find_host_by_name(client, host_name)
        assert host is not None

    def test_find_nonexistent_host(self, client: VSphereClient) -> None:
        host = find_host_by_name(client, "nonexistent-host-99999")
        assert host is None

    def test_enter_maintenance_mode(self, client: VSphereClient, host_name: str) -> None:
        host = find_host_by_name(client, host_name)
        assert host is not None
        task = host.EnterMaintenanceMode(timeout=60, evacuatePoweredOffVms=True)
        result = wait_for_task(task)
        assert result["status"] == "success"

    def test_exit_maintenance_mode(self, client: VSphereClient, host_name: str) -> None:
        host = find_host_by_name(client, host_name)
        assert host is not None
        task = host.ExitMaintenanceMode(timeout=60)
        result = wait_for_task(task)
        assert result["status"] == "success"
