from __future__ import annotations

import time
from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LEASE_READY_TIMEOUT = 60
_LEASE_POLL_INTERVAL = 0.5


def _get_rest_session(client: VSphereClient) -> tuple[requests.Session, str]:
    """Create a REST session using vSphere credentials."""
    settings = client._settings
    base_url = f"https://{settings.host}"
    session = requests.Session()
    session.verify = not settings.ignore_ssl
    resp = session.post(f"{base_url}/api/session", auth=(settings.user, settings.password))
    resp.raise_for_status()
    token = resp.json()
    session.headers.update({"vmware-api-session-id": token})
    return session, base_url


def _wait_for_lease(lease: Any, timeout: int = _LEASE_READY_TIMEOUT) -> None:
    """Block until an HttpNfcLease reaches the ready state or raises on error/timeout."""
    from pyVmomi import vim

    start = time.time()
    while lease.state == vim.HttpNfcLease.State.initializing:
        if time.time() - start > timeout:
            try:
                lease.HttpNfcLeaseAbort()
            except Exception:
                pass
            raise TimeoutError(f"HttpNfcLease did not become ready within {timeout}s")
        time.sleep(_LEASE_POLL_INTERVAL)

    if lease.state == vim.HttpNfcLease.State.error:
        error_msg = str(lease.error) if lease.error else "Unknown lease error"
        raise RuntimeError(f"HttpNfcLease entered error state: {error_msg}")


def register_ovf_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def export_vm_as_ovf(vm_name: str) -> dict[str, Any]:
        """Initiate an OVF export lease for a virtual machine and return download URLs.

        Calls ExportVm() on the target VM to obtain an HttpNfcLease. Returns the
        lease reference details and per-device download URLs. The caller is
        responsible for downloading the files from the returned URLs before the
        lease expires. The lease must be aborted or completed by the caller.

        Args:
            vm_name: Name of the VM to export.
        """
        logger.info("export_vm_as_ovf", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        lease = vm_obj.ExportVm()
        _wait_for_lease(lease)

        info = lease.info
        device_urls = []
        for url_item in info.deviceUrl or []:
            device_urls.append(
                {
                    "key": url_item.key,
                    "import_key": url_item.importKey,
                    "url": url_item.url,
                    "ssl_thumbprint": url_item.sslThumbprint,
                    "disk": getattr(url_item, "disk", None),
                }
            )

        return {
            "vm_name": vm_name,
            "operation": "export_vm_as_ovf",
            "total_disk_capacity_kb": info.totalDiskCapacityInKB,
            "lease_timeout_sec": info.leaseTimeout,
            "device_urls": device_urls,
            "note": (
                "Download files from device_urls, then complete or abort the lease. "
                "The lease is live and will expire per lease_timeout_sec."
            ),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def import_ovf(
        resource_pool_name: str,
        datastore_name: str,
        name: str,
        ovf_url: str | None = None,
        host_name: str | None = None,
    ) -> dict[str, Any]:
        """Import an OVF/OVA into vSphere from a URL using pyVmomi ImportVApp.

        Downloads and parses the OVF descriptor from ovf_url, creates an import
        spec, and initiates an ImportVApp lease against the specified resource
        pool and datastore. Returns the upload URLs so the caller can stream disk
        images. The caller must upload disk files and complete the lease.

        Args:
            resource_pool_name: Name of the target resource pool.
            datastore_name: Name of the target datastore.
            name: Name to assign to the imported VM.
            ovf_url: HTTP/HTTPS URL of the .ovf or .ova descriptor file.
            host_name: Optional target ESXi host name.
        """
        logger.info("import_ovf", name=name, resource_pool_name=resource_pool_name, datastore_name=datastore_name)
        from pyVmomi import vim

        from vsphere_mcp.tools._base import find_host_by_name
        from vsphere_mcp.utils.property_collector import collect_properties

        if ovf_url is None:
            return {"status": "error", "error": "ovf_url is required"}

        # Resolve resource pool
        rp_items = collect_properties(client, vim.ResourcePool, ["name"])
        rp_obj = next((r["_obj"] for r in rp_items if r.get("name") == resource_pool_name), None)
        if rp_obj is None:
            return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}

        # Resolve datastore
        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = next((d["_obj"] for d in ds_items if d.get("name") == datastore_name), None)
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        # Resolve optional host
        host_obj = None
        if host_name is not None:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}

        # Fetch OVF descriptor
        verify_ssl = not client._settings.ignore_ssl
        ovf_resp = requests.get(ovf_url, verify=verify_ssl, timeout=30)
        ovf_resp.raise_for_status()
        ovf_descriptor = ovf_resp.text

        # Create import spec
        ovf_manager = client.content.ovfManager
        import_spec_params = vim.OvfManager.CreateImportSpecParams(entityName=name)
        import_spec_result = ovf_manager.CreateImportSpec(
            ovfDescriptor=ovf_descriptor,
            resourcePool=rp_obj,
            datastore=ds_obj,
            cisp=import_spec_params,
        )

        if import_spec_result.error:
            error_msgs = [str(e.localizedMessage) for e in import_spec_result.error]
            return {"status": "error", "error": f"OVF import spec errors: {'; '.join(error_msgs)}"}

        if import_spec_result.warning:
            for w in import_spec_result.warning:
                logger.warning("import_ovf_warning", warning=str(w.localizedMessage))

        # Initiate import
        folder = rp_obj.owner.vmFolder if hasattr(rp_obj.owner, "vmFolder") else client.content.rootFolder
        lease = rp_obj.ImportVApp(
            spec=import_spec_result.importSpec,
            folder=folder,
            host=host_obj,
        )
        _wait_for_lease(lease)

        info = lease.info
        device_urls = []
        for url_item in info.deviceUrl or []:
            device_urls.append(
                {
                    "key": url_item.key,
                    "import_key": url_item.importKey,
                    "url": url_item.url,
                    "ssl_thumbprint": url_item.sslThumbprint,
                }
            )

        return {
            "status": "success",
            "operation": "import_ovf",
            "name": name,
            "resource_pool_name": resource_pool_name,
            "datastore_name": datastore_name,
            "lease_timeout_sec": info.leaseTimeout,
            "device_urls": device_urls,
            "note": (
                "Upload disk files to device_urls matching importKey values, "
                "then call HttpNfcLeaseComplete to finalize the import."
            ),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def capture_vm_to_library(
        vm_name: str,
        library_id: str,
        item_name: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Capture a virtual machine to a content library as an OVF item.

        Uses the vSphere REST API to create a new OVF library item by capturing
        the running or stopped VM. The operation is asynchronous on the server;
        the returned result ID can be used to track progress.

        Args:
            vm_name: Name of the VM to capture.
            library_id: ID of the target content library.
            item_name: Name for the new library item.
            description: Optional description for the library item.
        """
        logger.info("capture_vm_to_library", vm_name=vm_name, library_id=library_id, item_name=item_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        vm_moref = str(vm_obj._moId)

        session, base_url = _get_rest_session(client)

        body = {
            "create_spec": {
                "description": description,
                "name": item_name,
                "library_id": library_id,
            },
            "source": {
                "id": vm_moref,
                "type": "VirtualMachine",
            },
        }

        resp = session.post(
            f"{base_url}/api/vcenter/ovf/library-item?action=create",
            json=body,
        )
        resp.raise_for_status()
        result_data: dict[str, Any] = resp.json()

        return {
            "status": "success",
            "operation": "capture_vm_to_library",
            "vm_name": vm_name,
            "vm_moref": vm_moref,
            "library_id": library_id,
            "item_name": item_name,
            "result": result_data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def upload_file_to_library_item(
        library_id: str,
        item_name: str,
        file_name: str,
        source_url: str,
    ) -> dict[str, Any]:
        """Upload a file from a URL into a content library item via an update session.

        Creates a library item (if it does not exist), opens an update session,
        adds the file from source_url, and completes the session. Suitable for
        uploading OVF descriptors or disk images to an existing or new library item.

        Args:
            library_id: ID of the target content library.
            item_name: Name of the library item to create or update.
            file_name: Destination file name within the library item.
            source_url: HTTP/HTTPS URL from which the server should pull the file.
        """
        logger.info(
            "upload_file_to_library_item",
            library_id=library_id,
            item_name=item_name,
            file_name=file_name,
            source_url=source_url,
        )

        session, base_url = _get_rest_session(client)

        # Create library item
        create_body = {
            "create_spec": {
                "library_id": library_id,
                "name": item_name,
                "type": "ovf",
            }
        }
        item_resp = session.post(f"{base_url}/api/content/library/item", json=create_body)
        item_resp.raise_for_status()
        item_id: str = item_resp.json()

        # Create update session
        session_body = {
            "create_spec": {
                "library_item_id": item_id,
            }
        }
        update_session_resp = session.post(
            f"{base_url}/api/content/library/item/update-session",
            json=session_body,
        )
        update_session_resp.raise_for_status()
        update_session_id: str = update_session_resp.json()

        # Add file from URL
        file_body = {
            "file_spec": {
                "name": file_name,
                "source_type": "PULL",
                "source_endpoint": {
                    "uri": source_url,
                },
            }
        }
        file_resp = session.post(
            f"{base_url}/api/content/library/item/updatesession/file?update_session_id={update_session_id}&action=add",
            json=file_body,
        )
        file_resp.raise_for_status()

        # Complete the session
        complete_resp = session.post(
            f"{base_url}/api/content/library/item/update-session/{update_session_id}?action=complete"
        )
        complete_resp.raise_for_status()

        return {
            "status": "success",
            "operation": "upload_file_to_library_item",
            "library_id": library_id,
            "item_id": item_id,
            "item_name": item_name,
            "file_name": file_name,
            "source_url": source_url,
            "update_session_id": update_session_id,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_ovf_deploy_options(
        library_item_id: str,
        resource_pool_id: str | None = None,
        datacenter_id: str | None = None,
        folder_id: str | None = None,
        host_id: str | None = None,
    ) -> dict[str, Any]:
        """List deployment options (OVF properties, networks, storage) for a library item.

        Calls the OVF filter action against the specified library item to enumerate
        available deployment configurations, network mappings, storage policies,
        and OVF properties. Provide at least one target hint (resource_pool_id,
        datacenter_id, etc.) for accurate results.

        Args:
            library_item_id: ID of the OVF content library item.
            resource_pool_id: Optional managed object ID of the target resource pool.
            datacenter_id: Optional managed object ID of the target datacenter.
            folder_id: Optional managed object ID of the target VM folder.
            host_id: Optional managed object ID of the target host.
        """
        logger.info("list_ovf_deploy_options", library_item_id=library_item_id)

        session, base_url = _get_rest_session(client)

        target: dict[str, Any] = {}
        if resource_pool_id is not None:
            target["resource_pool_id"] = resource_pool_id
        if datacenter_id is not None:
            target["datacenter_id"] = datacenter_id
        if folder_id is not None:
            target["folder_id"] = folder_id
        if host_id is not None:
            target["host_id"] = host_id

        body: dict[str, Any] = {"target": target}

        resp = session.post(
            f"{base_url}/api/vcenter/ovf/library-item/{library_item_id}?action=filter",
            json=body,
        )
        resp.raise_for_status()
        result_data: dict[str, Any] = resp.json()

        return {
            "library_item_id": library_item_id,
            "operation": "list_ovf_deploy_options",
            "deploy_options": result_data,
        }
