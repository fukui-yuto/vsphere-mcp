from __future__ import annotations

import base64
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_datacenter(client: VSphereClient, dc_name: str) -> Any | None:
    """Find a datacenter by name, or return the first one if dc_name is empty."""
    items = collect_properties(client, vim.Datacenter, ["name"])
    if not dc_name:
        return items[0]["_obj"] if items else None
    for item in items:
        if item.get("name") == dc_name:
            return item["_obj"]
    return None


def register_virtual_disk_mgr_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def copy_virtual_disk(
        source_path: str,
        dest_path: str,
        datacenter_name: str = "",
        dest_datacenter_name: str = "",
        disk_type: str = "",
    ) -> dict[str, Any]:
        """Copy a virtual disk (VMDK) from one location to another.

        Args:
            source_path: Source VMDK path in datastore notation (e.g. '[datastore1] vm/vm.vmdk').
            dest_path: Destination VMDK path in datastore notation.
            datacenter_name: Datacenter containing the source disk. Uses first available if empty.
            dest_datacenter_name: Datacenter for the destination. Uses source datacenter if empty.
            disk_type: Destination disk type (e.g. 'thin', 'thick', 'eagerZeroedThick'). Uses source type if empty.
        """
        logger.info(
            "copy_virtual_disk",
            source_path=source_path,
            dest_path=dest_path,
            datacenter_name=datacenter_name,
            dest_datacenter_name=dest_datacenter_name,
        )

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        src_dc = _find_datacenter(client, datacenter_name)
        dst_dc = _find_datacenter(client, dest_datacenter_name) if dest_datacenter_name else src_dc

        dest_spec: Any = None
        if disk_type:
            type_map: dict[str, str] = {
                "thin": "thin",
                "thick": "thick",
                "eagerZeroedThick": "eagerZeroedThick",
                "preallocated": "preallocated",
            }
            if disk_type not in type_map:
                return {"status": "error", "error": f"Invalid disk_type '{disk_type}'. Valid: {list(type_map.keys())}"}
            dest_spec = vim.VirtualDiskManager.VirtualDiskSpec(
                diskType=disk_type,
                adapterType="lsiLogic",
            )

        task = vdm.CopyVirtualDisk_Task(
            sourceName=source_path,
            sourceDatacenter=src_dc,
            destName=dest_path,
            destDatacenter=dst_dc,
            destSpec=dest_spec,
            force=False,
        )
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to copy virtual disk")}

        return {
            "status": "success",
            "operation": "copy_virtual_disk",
            "source_path": source_path,
            "dest_path": dest_path,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def move_virtual_disk(
        source_path: str,
        dest_path: str,
        datacenter_name: str = "",
        dest_datacenter_name: str = "",
        force: bool = False,
    ) -> dict[str, Any]:
        """Move a virtual disk (VMDK) from one location to another.

        Args:
            source_path: Source VMDK path in datastore notation (e.g. '[datastore1] vm/vm.vmdk').
            dest_path: Destination VMDK path in datastore notation.
            datacenter_name: Datacenter containing the source disk. Uses first available if empty.
            dest_datacenter_name: Datacenter for the destination. Uses source datacenter if empty.
            force: If True, overwrite an existing disk at the destination (default False).
        """
        logger.info(
            "move_virtual_disk",
            source_path=source_path,
            dest_path=dest_path,
            datacenter_name=datacenter_name,
            force=force,
        )

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        src_dc = _find_datacenter(client, datacenter_name)
        dst_dc = _find_datacenter(client, dest_datacenter_name) if dest_datacenter_name else src_dc

        task = vdm.MoveVirtualDisk_Task(
            sourceName=source_path,
            sourceDatacenter=src_dc,
            destName=dest_path,
            destDatacenter=dst_dc,
            force=force,
        )
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to move virtual disk")}

        return {
            "status": "success",
            "operation": "move_virtual_disk",
            "source_path": source_path,
            "dest_path": dest_path,
            "force": force,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_virtual_disk(disk_path: str, datacenter_name: str = "") -> dict[str, Any]:
        """Permanently delete a virtual disk (VMDK) file from a datastore.

        Args:
            disk_path: VMDK path in datastore notation (e.g. '[datastore1] vm/vm.vmdk').
            datacenter_name: Datacenter containing the disk. Uses first available if empty.
        """
        logger.info("delete_virtual_disk", disk_path=disk_path, datacenter_name=datacenter_name)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        dc = _find_datacenter(client, datacenter_name)

        task = vdm.DeleteVirtualDisk_Task(name=disk_path, datacenter=dc)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to delete virtual disk")}

        return {
            "status": "success",
            "operation": "delete_virtual_disk",
            "disk_path": disk_path,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_virtual_disk_uuid(disk_path: str, datacenter_name: str = "") -> dict[str, Any]:
        """Get the UUID of a virtual disk (VMDK) file.

        Args:
            disk_path: VMDK path in datastore notation (e.g. '[datastore1] vm/vm.vmdk').
            datacenter_name: Datacenter containing the disk. Uses first available if empty.
        """
        logger.info("get_virtual_disk_uuid", disk_path=disk_path, datacenter_name=datacenter_name)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        dc = _find_datacenter(client, datacenter_name)
        uuid: str = vdm.QueryVirtualDiskUuid(name=disk_path, datacenter=dc)

        return {
            "status": "success",
            "disk_path": disk_path,
            "uuid": uuid,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_virtual_disk_uuid(
        disk_path: str,
        uuid: str,
        datacenter_name: str = "",
    ) -> dict[str, Any]:
        """Set the UUID of a virtual disk (VMDK) file.

        Args:
            disk_path: VMDK path in datastore notation (e.g. '[datastore1] vm/vm.vmdk').
            uuid: New UUID string to assign to the virtual disk.
            datacenter_name: Datacenter containing the disk. Uses first available if empty.
        """
        logger.info("set_virtual_disk_uuid", disk_path=disk_path, uuid=uuid)

        vdm = getattr(client.content, "virtualDiskManager", None)
        if vdm is None:
            return {"status": "error", "error": "virtualDiskManager not available on this vCenter"}

        dc = _find_datacenter(client, datacenter_name)
        vdm.SetVirtualDiskUuid(name=disk_path, datacenter=dc, uuid=uuid)

        return {
            "status": "success",
            "operation": "set_virtual_disk_uuid",
            "disk_path": disk_path,
            "uuid": uuid,
        }

    @mcp.tool()
    @handle_tool_errors
    def query_vm_config_option(
        host_name: str = "",
        vm_name: str = "",
    ) -> dict[str, Any]:
        """Query valid VM configuration options (hardware versions, guest OS descriptors) for a host or VM.

        Args:
            host_name: Name of the ESXi host to query config options against. Uses any host if empty.
            vm_name: Name of the VM whose environment browser to use. Takes precedence over host_name.
        """
        logger.info("query_vm_config_option", host_name=host_name, vm_name=vm_name)

        env_browser: Any = None

        if vm_name:
            vm_items = collect_properties(client, vim.VirtualMachine, ["name"])
            for item in vm_items:
                if item.get("name") == vm_name:
                    vm_obj = item["_obj"]
                    env_browser = getattr(vm_obj, "environmentBrowser", None)
                    break
            if env_browser is None:
                return {"status": "error", "error": f"VM '{vm_name}' not found or environmentBrowser unavailable"}
        elif host_name:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}
            parent = getattr(host_obj, "parent", None)
            if parent is not None:
                env_browser = getattr(parent, "environmentBrowser", None)
            if env_browser is None:
                return {"status": "error", "error": "environmentBrowser not available for this host's compute resource"}
        else:
            cr_items = collect_properties(client, vim.ComputeResource, ["name"])
            if cr_items:
                env_browser = getattr(cr_items[0]["_obj"], "environmentBrowser", None)
            if env_browser is None:
                return {"status": "error", "error": "No compute resource found to query config options"}

        config_option = env_browser.QueryConfigOption()
        if config_option is None:
            return {"status": "error", "error": "No config options returned"}

        guest_descriptors: list[dict[str, Any]] = []
        for gd in getattr(config_option, "guestOSDescriptor", None) or []:
            guest_descriptors.append({
                "id": getattr(gd, "id", None),
                "family": getattr(gd, "family", None),
                "fullName": getattr(gd, "fullName", None),
                "recommended": getattr(gd, "recommended", None),
            })

        return {
            "status": "success",
            "version": getattr(config_option, "version", None),
            "description": getattr(config_option, "description", None),
            "num_guest_os_descriptors": len(guest_descriptors),
            "guest_os_descriptors": guest_descriptors,
            "max_cpu_per_vm": getattr(config_option, "numCPUMax", None),
            "max_memory_mb_per_vm": getattr(config_option, "memoryMax", None),
        }

    @mcp.tool()
    @handle_tool_errors
    def query_vm_config_target(
        host_name: str = "",
        vm_name: str = "",
    ) -> dict[str, Any]:
        """Query available configuration targets (networks, datastores, devices) for a host or VM.

        Args:
            host_name: Name of the ESXi host to query config target for. Uses any host if empty.
            vm_name: Name of the VM whose environment browser to use. Takes precedence over host_name.
        """
        logger.info("query_vm_config_target", host_name=host_name, vm_name=vm_name)

        env_browser: Any = None
        host_obj: Any = None

        if vm_name:
            vm_items = collect_properties(client, vim.VirtualMachine, ["name"])
            for item in vm_items:
                if item.get("name") == vm_name:
                    vm_obj = item["_obj"]
                    env_browser = getattr(vm_obj, "environmentBrowser", None)
                    break
            if env_browser is None:
                return {"status": "error", "error": f"VM '{vm_name}' not found or environmentBrowser unavailable"}
        elif host_name:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}
            parent = getattr(host_obj, "parent", None)
            if parent is not None:
                env_browser = getattr(parent, "environmentBrowser", None)
            if env_browser is None:
                return {"status": "error", "error": "environmentBrowser not available for this host's compute resource"}
        else:
            cr_items = collect_properties(client, vim.ComputeResource, ["name"])
            if cr_items:
                env_browser = getattr(cr_items[0]["_obj"], "environmentBrowser", None)
            if env_browser is None:
                return {"status": "error", "error": "No compute resource found to query config target"}

        config_target = env_browser.QueryConfigTarget(host=host_obj)
        if config_target is None:
            return {"status": "error", "error": "No config target returned"}

        networks: list[dict[str, Any]] = []
        for net in getattr(config_target, "network", None) or []:
            net_summary = getattr(net, "network", None)
            networks.append({
                "name": getattr(net_summary, "name", None) if net_summary else None,
                "accessible": getattr(net_summary, "accessible", None) if net_summary else None,
            })

        datastores: list[dict[str, Any]] = []
        for ds in getattr(config_target, "datastore", None) or []:
            ds_summary = getattr(ds, "datastore", None)
            datastores.append({
                "name": getattr(ds_summary, "name", None) if ds_summary else None,
                "accessible": getattr(ds_summary, "accessible", None) if ds_summary else None,
                "type": getattr(ds_summary, "type", None) if ds_summary else None,
                "freeSpace": getattr(ds_summary, "freeSpace", None) if ds_summary else None,
            })

        return {
            "status": "success",
            "num_networks": len(networks),
            "networks": networks,
            "num_datastores": len(datastores),
            "datastores": datastores,
            "num_cpu": getattr(config_target, "numCpus", None),
            "num_cpu_cores": getattr(config_target, "numCpuCores", None),
            "num_numa_nodes": getattr(config_target, "numNumaNodes", None),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def extend_vmfs_datastore(
        datastore_name: str,
        host_name: str,
        device_path: str,
    ) -> dict[str, Any]:
        """Add a new extent (partition) to an existing VMFS datastore.

        Args:
            datastore_name: Name of the existing VMFS datastore to extend.
            host_name: Name of the ESXi host that has access to both the datastore and the device.
            device_path: Canonical device path for the new extent (e.g. '/vmfs/devices/disks/naa.xxx').
        """
        logger.info(
            "extend_vmfs_datastore",
            datastore_name=datastore_name,
            host_name=host_name,
            device_path=device_path,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        datastore_system = getattr(cm, "datastoreSystem", None)
        if datastore_system is None:
            return {"status": "error", "error": "datastoreSystem not available on this host"}

        # Resolve the datastore managed object
        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        # Try to use the datastore system's own extent spec generation
        try:
            extend_options = datastore_system.QueryVmfsDatastoreExtendOptions(
                datastore=ds_obj,
                devicePath=device_path,
            )
            if extend_options and len(extend_options) > 0:
                spec = extend_options[0].spec
            else:
                return {"status": "error", "error": f"No valid extend options for device '{device_path}'"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to query VMFS extend options: {e}"}

        try:
            datastore_system.ExtendVmfsDatastore(datastore=ds_obj, spec=spec)
        except Exception as e:
            return {"status": "error", "error": f"Failed to extend VMFS datastore: {e}"}

        return {
            "status": "success",
            "operation": "extend_vmfs_datastore",
            "datastore_name": datastore_name,
            "host_name": host_name,
            "device_path": device_path,
        }

    @mcp.tool()
    @handle_tool_errors
    def backup_dvs_config(dvs_name: str) -> dict[str, Any]:
        """Export and back up the configuration of a Distributed Virtual Switch.

        Args:
            dvs_name: Name of the DVSwitch to export.
        """
        logger.info("backup_dvs_config", dvs_name=dvs_name)

        dvsm = getattr(client.content, "dvSwitchManager", None)
        if dvsm is None:
            return {"status": "error", "error": "dvSwitchManager not available on this vCenter"}

        # Find the DVS managed object
        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "uuid"])
        dvs_obj = None
        dvs_uuid = None
        for item in dvs_items:
            if item.get("name") == dvs_name:
                dvs_obj = item["_obj"]
                dvs_uuid = item.get("uuid")
                break
        if dvs_obj is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found"}

        selection = vim.dvs.EntityBackup.EntitySelectionSet()
        selection.entityType = "distributedVirtualSwitch"

        export_method = getattr(dvsm, "DVSManagerExportEntity_Task", None)
        if export_method is None:
            return {"status": "error", "error": "DVSManagerExportEntity_Task not available"}

        task = export_method(selectionSet=[selection])
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to export DVS configuration")}

        # Try to read the task result
        config_blob: str | None = None
        try:
            task_result = task.info.result
            if task_result and len(task_result) > 0:
                entity_backup = task_result[0]
                config_data = getattr(entity_backup, "configBlob", None)
                if config_data is not None:
                    config_blob = base64.b64encode(config_data).decode("utf-8")
        except Exception:
            config_blob = None

        return {
            "status": "success",
            "operation": "backup_dvs_config",
            "dvs_name": dvs_name,
            "dvs_uuid": dvs_uuid,
            "config_blob_base64": config_blob,
            "message": "Export completed. config_blob_base64 contains the backup data if available.",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def restore_dvs_config(
        dvs_name: str,
        config_blob: str,
        create_new: bool = False,
    ) -> dict[str, Any]:
        """Restore or import a Distributed Virtual Switch configuration from a backup blob.

        Args:
            dvs_name: Name of the DVSwitch to restore (used to locate the existing switch).
            config_blob: Base64-encoded configuration blob previously obtained from backup_dvs_config.
            create_new: If True, import as a new DVS; if False, merge into existing DVS (default False).
        """
        logger.info("restore_dvs_config", dvs_name=dvs_name, create_new=create_new)

        dvsm = getattr(client.content, "dvSwitchManager", None)
        if dvsm is None:
            return {"status": "error", "error": "dvSwitchManager not available on this vCenter"}

        try:
            config_data = base64.b64decode(config_blob)
        except Exception as e:
            return {"status": "error", "error": f"Invalid base64 config_blob: {e}"}

        entity_backup = vim.dvs.EntityBackup.Config(
            configBlob=config_data,
            entityType="distributedVirtualSwitch",
            name=dvs_name,
        )

        import_type = "createEntityWithNewIdentifier" if create_new else "applyToEntitySpecified"

        import_method = getattr(dvsm, "DVSManagerImportEntity_Task", None)
        if import_method is None:
            return {"status": "error", "error": "DVSManagerImportEntity_Task not available"}

        task = import_method(entityBackup=[entity_backup], importType=import_type)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to restore DVS configuration")}

        return {
            "status": "success",
            "operation": "restore_dvs_config",
            "dvs_name": dvs_name,
            "create_new": create_new,
            "import_type": import_type,
        }
