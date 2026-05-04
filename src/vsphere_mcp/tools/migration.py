from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    find_host_by_name,
    find_vm_with_props,
    handle_tool_errors,
    require_confirm,
    wait_for_task,
)
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_migration_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def migrate_vm(vm_name: str, target_host: str) -> dict[str, Any]:
        """Migrate a virtual machine to a different ESXi host.

        Supports both hot (vMotion) and cold migration. The VM can be powered
        on or off. For cross-cluster migration, consider using ``relocate_vm``
        with the ``target_resource_pool`` parameter.
        """
        logger.info("migrate_vm", vm_name=vm_name, target_host=target_host)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        host = find_host_by_name(client, target_host)
        if host is None:
            return {"status": "error", "error": f"Host '{target_host}' not found"}
        relocate_spec = vim.vm.RelocateSpec(host=host)
        task = found["_obj"].Relocate(spec=relocate_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["target_host"] = target_host
        result["operation"] = "migrate_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def storage_vmotion(
        vm_name: str, target_datastore: str, disk_format: str | None = None
    ) -> dict[str, Any]:
        """Migrate VM disks to a different datastore (Storage vMotion).

        Args:
            vm_name: Name of the VM.
            target_datastore: Name of the target datastore.
            disk_format: Optional disk format conversion — "thin" or "thick".
        """
        logger.info("storage_vmotion", vm_name=vm_name, target_datastore=target_datastore)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == target_datastore:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{target_datastore}' not found"}
        relocate_spec = vim.vm.RelocateSpec(datastore=ds_obj)
        if disk_format is not None:
            fmt = disk_format.lower()
            if fmt == "thin":
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.sparse
            elif fmt == "thick":
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.flat
            else:
                return {
                    "status": "error",
                    "error": f"Invalid disk_format '{disk_format}'. Must be 'thin' or 'thick'.",
                }
        task = found["_obj"].Relocate(spec=relocate_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["target_datastore"] = target_datastore
        result["operation"] = "storage_vmotion"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def relocate_vm(
        vm_name: str,
        target_host: str | None = None,
        target_datastore: str | None = None,
        target_resource_pool: str | None = None,
        disk_format: str | None = None,
    ) -> dict[str, Any]:
        """Relocate a VM (combined compute + storage migration).

        Args:
            vm_name: Name of the VM.
            target_host: Target ESXi host name (optional).
            target_datastore: Target datastore name (optional).
            target_resource_pool: Target resource pool name (optional).
            disk_format: Optional disk format conversion — "thin" or "thick".
        """
        logger.info(
            "relocate_vm",
            vm_name=vm_name,
            target_host=target_host,
            target_datastore=target_datastore,
            target_resource_pool=target_resource_pool,
        )
        if not any([target_host, target_datastore, target_resource_pool]):
            return {
                "status": "error",
                "error": "At least one target (host, datastore, or resource_pool) must be specified",
            }
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        spec = vim.vm.RelocateSpec()
        if target_host:
            host_obj = find_host_by_name(client, target_host)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{target_host}' not found"}
            spec.host = host_obj
        if target_datastore:
            ds_items = collect_properties(client, vim.Datastore, ["name"])
            ds_obj = None
            for item in ds_items:
                if item.get("name") == target_datastore:
                    ds_obj = item["_obj"]
                    break
            if ds_obj is None:
                return {"status": "error", "error": f"Datastore '{target_datastore}' not found"}
            spec.datastore = ds_obj
        if target_resource_pool:
            rp_items = collect_properties(client, vim.ResourcePool, ["name"])
            rp_obj = None
            for item in rp_items:
                if item.get("name") == target_resource_pool:
                    rp_obj = item["_obj"]
                    break
            if rp_obj is None:
                return {"status": "error", "error": f"Resource pool '{target_resource_pool}' not found"}
            spec.pool = rp_obj
        if disk_format is not None:
            fmt = disk_format.lower()
            if fmt == "thin":
                spec.transform = vim.vm.RelocateSpec.Transformation.sparse
            elif fmt == "thick":
                spec.transform = vim.vm.RelocateSpec.Transformation.flat
            else:
                return {
                    "status": "error",
                    "error": f"Invalid disk_format '{disk_format}'. Must be 'thin' or 'thick'.",
                }

        task = found["_obj"].Relocate(spec=spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "relocate_vm"
        return result
