from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import requests
import urllib3

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _find_datastore_and_datacenter(
    client: VSphereClient, datastore_name: str
) -> tuple[Any, Any] | None:
    """Find a datastore object and its parent datacenter by datastore name."""
    ds_items = collect_properties(client, vim.Datastore, ["name"])
    ds_obj = None
    for item in ds_items:
        if item.get("name") == datastore_name:
            ds_obj = item["_obj"]
            break
    if ds_obj is None:
        return None

    current = getattr(ds_obj, "parent", None)
    max_depth = 50
    depth = 0
    while current and depth < max_depth:
        if isinstance(current, vim.Datacenter):
            return ds_obj, current
        current = getattr(current, "parent", None)
        depth += 1

    dc_items = collect_properties(client, vim.Datacenter, ["name"])
    if dc_items:
        return ds_obj, dc_items[0]["_obj"]
    return ds_obj, None


def register_datastore_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_datastore_file_url(datastore_name: str, file_path: str) -> dict[str, Any]:
        """Generate an authenticated HTTPS URL for a file on a vSphere datastore.

        The returned URL can be used with a valid vSphere session cookie or basic
        credentials to download the file directly from the vCenter HTTP file service.

        Args:
            datastore_name: Name of the datastore containing the file.
            file_path: Path to the file within the datastore (e.g. 'my-vm/my-vm.vmdk').
        """
        logger.info("get_datastore_file_url", datastore_name=datastore_name, file_path=file_path)

        found = _find_datastore_and_datacenter(client, datastore_name)
        if found is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        ds_obj, dc_obj = found
        host = client._settings.host
        dc_name = getattr(dc_obj, "name", "") if dc_obj else ""

        encoded_path = quote(file_path.lstrip("/"), safe="/")
        encoded_dc = quote(dc_name)
        encoded_ds = quote(datastore_name)

        url = (
            f"https://{host}/folder/{encoded_path}"
            f"?dcPath={encoded_dc}&dsName={encoded_ds}"
        )

        return {
            "datastore": datastore_name,
            "file_path": file_path,
            "datacenter": dc_name,
            "url": url,
            "note": (
                "Use this URL with a vmware-api-session-id header or HTTP basic auth "
                "to download the file."
            ),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def upload_file_to_datastore(
        datastore_name: str,
        remote_path: str,
        content_base64: str,
    ) -> dict[str, Any]:
        """Upload content to a file on a vSphere datastore using the HTTP file service.

        Args:
            datastore_name: Name of the datastore to upload to.
            remote_path: Destination path within the datastore (e.g. 'my-folder/file.txt').
            content_base64: Base64-encoded content to write to the file.
        """
        logger.info("upload_file_to_datastore", datastore_name=datastore_name, remote_path=remote_path)

        try:
            content_bytes = base64.b64decode(content_base64)
        except Exception as exc:
            return {"status": "error", "error": f"Invalid base64 content: {exc}"}

        found = _find_datastore_and_datacenter(client, datastore_name)
        if found is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        ds_obj, dc_obj = found
        settings = client._settings
        host = settings.host
        dc_name = getattr(dc_obj, "name", "") if dc_obj else ""

        encoded_path = quote(remote_path.lstrip("/"), safe="/")
        encoded_dc = quote(dc_name)
        encoded_ds = quote(datastore_name)
        url = (
            f"https://{host}/folder/{encoded_path}"
            f"?dcPath={encoded_dc}&dsName={encoded_ds}"
        )

        session = requests.Session()
        session.verify = not settings.ignore_ssl
        resp = session.put(
            url,
            data=content_bytes,
            auth=(settings.user, settings.password),
            headers={"Content-Type": "application/octet-stream"},
        )
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "upload_file_to_datastore",
            "datastore": datastore_name,
            "remote_path": remote_path,
            "bytes_uploaded": len(content_bytes),
            "http_status": resp.status_code,
        }
