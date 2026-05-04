import os

import pytest

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.config import VSphereSettings


@pytest.fixture(scope="session")
def vsphere_settings() -> VSphereSettings:
    return VSphereSettings(
        host=os.environ.get("VSPHERE_HOST", "localhost"),
        port=int(os.environ.get("VSPHERE_PORT", "8989")),
        user=os.environ.get("VSPHERE_USER", "user"),
        password=os.environ.get("VSPHERE_PASSWORD", "pass"),
        ignore_ssl=True,
    )


@pytest.fixture(scope="session")
def vsphere_client(vsphere_settings: VSphereSettings) -> VSphereClient:
    client = VSphereClient(vsphere_settings)
    yield client  # type: ignore[misc]
    client.disconnect()
