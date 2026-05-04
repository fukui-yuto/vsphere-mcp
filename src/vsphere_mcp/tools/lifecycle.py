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

logger = get_logger(__name__)


def register_lifecycle_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_vm(vm_name: str) -> dict[str, Any]:
        """Delete a virtual machine permanently. The VM must be powered off first."""
        logger.info("delete_vm", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before deletion"}
        task = found["_obj"].Destroy()
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "delete_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def clone_vm(
        vm_name: str,
        clone_name: str,
        power_on: bool = False,
        datastore_name: str | None = None,
        host_name: str | None = None,
        resource_pool_name: str | None = None,
        folder_name: str | None = None,
        customization_spec_name: str | None = None,
        disk_format: str | None = None,
    ) -> dict[str, Any]:
        """Clone an existing virtual machine.

        Args:
            vm_name: Name of the source VM.
            clone_name: Name for the clone.
            power_on: Power on the clone after creation (default False).
            datastore_name: Target datastore (optional).
            host_name: Target host (optional).
            resource_pool_name: Target resource pool (optional).
            folder_name: Target folder (optional).
            customization_spec_name: Guest OS customization spec to apply (optional).
            disk_format: Disk format: 'thin', 'thick', or None to keep same as source.
        """
        logger.info("clone_vm", vm_name=vm_name, clone_name=clone_name)
        from vsphere_mcp.utils.property_collector import collect_properties

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = found["_obj"]

        relocate_spec = vim.vm.RelocateSpec()

        if datastore_name is not None:
            ds_items = collect_properties(client, vim.Datastore, ["name"])
            ds_obj = next((d["_obj"] for d in ds_items if d.get("name") == datastore_name), None)
            if ds_obj is None:
                return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}
            relocate_spec.datastore = ds_obj

        if host_name is not None:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}
            relocate_spec.host = host_obj

        if resource_pool_name is not None:
            rp_items = collect_properties(client, vim.ResourcePool, ["name"])
            rp_obj = next((r["_obj"] for r in rp_items if r.get("name") == resource_pool_name), None)
            if rp_obj is None:
                return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}
            relocate_spec.pool = rp_obj

        # Determine target folder
        if folder_name is not None:
            folder_items = collect_properties(client, vim.Folder, ["name"])
            folder_obj = next((f["_obj"] for f in folder_items if f.get("name") == folder_name), None)
            if folder_obj is None:
                return {"status": "error", "error": f"Folder '{folder_name}' not found"}
            folder = folder_obj
        else:
            folder = vm_obj.parent

        if disk_format is not None:
            fmt = disk_format.lower()
            if fmt == "thin":
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.sparse
            elif fmt == "thick":
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.flat
            else:
                return {"status": "error", "error": f"disk_format must be 'thin' or 'thick', got '{disk_format}'"}

        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
        )

        if customization_spec_name is not None:
            spec_manager = client.content.customizationSpecManager
            if spec_manager is None:
                return {"status": "error", "error": "Customization spec manager not available"}
            try:
                cust_spec_item = spec_manager.GetCustomizationSpec(name=customization_spec_name)
                clone_spec.customization = cust_spec_item.spec
            except Exception as e:
                return {"status": "error", "error": f"Customization spec '{customization_spec_name}' not found: {e}"}

        task = vm_obj.Clone(folder=folder, name=clone_name, spec=clone_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["clone_name"] = clone_name
        result["operation"] = "clone_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def deploy_from_template(
        template_name: str,
        vm_name: str,
        power_on: bool = False,
        datastore_name: str | None = None,
        host_name: str | None = None,
        resource_pool_name: str | None = None,
        folder_name: str | None = None,
        customization_spec_name: str | None = None,
        disk_format: str | None = None,
        num_cpus: int | None = None,
        memory_mb: int | None = None,
    ) -> dict[str, Any]:
        """Deploy a new VM from a template.

        Args:
            template_name: Name of the template to deploy from.
            vm_name: Name for the new VM.
            power_on: Power on after deploy (default False).
            datastore_name: Target datastore (optional).
            host_name: Target host (optional).
            resource_pool_name: Target resource pool (optional).
            folder_name: Target folder (optional).
            customization_spec_name: Guest OS customization spec to apply (optional).
            disk_format: Disk format: 'thin', 'thick', or None to keep same as template.
            num_cpus: Override CPU count (optional).
            memory_mb: Override memory in MB (optional).
        """
        logger.info("deploy_from_template", template_name=template_name, vm_name=vm_name)
        from vsphere_mcp.utils.property_collector import collect_properties

        found = find_vm_with_props(client, template_name)
        if found is None:
            return {"status": "error", "error": f"Template '{template_name}' not found"}
        template_obj = found["_obj"]

        # Verify the source is actually a template
        if not getattr(template_obj.config, "template", False):
            return {
                "status": "error",
                "error": f"'{template_name}' is not a template. Use clone_vm instead.",
            }

        relocate_spec = vim.vm.RelocateSpec()

        if datastore_name is not None:
            ds_items = collect_properties(client, vim.Datastore, ["name"])
            ds_obj = next((d["_obj"] for d in ds_items if d.get("name") == datastore_name), None)
            if ds_obj is None:
                return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}
            relocate_spec.datastore = ds_obj

        if host_name is not None:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}
            relocate_spec.host = host_obj

        if resource_pool_name is not None:
            rp_items = collect_properties(client, vim.ResourcePool, ["name"])
            rp_obj = next((r["_obj"] for r in rp_items if r.get("name") == resource_pool_name), None)
            if rp_obj is None:
                return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}
            relocate_spec.pool = rp_obj

        # Determine target folder
        if folder_name is not None:
            folder_items = collect_properties(client, vim.Folder, ["name"])
            folder_obj = next((f["_obj"] for f in folder_items if f.get("name") == folder_name), None)
            if folder_obj is None:
                return {"status": "error", "error": f"Folder '{folder_name}' not found"}
            folder = folder_obj
        else:
            folder = template_obj.parent

        if disk_format is not None:
            fmt = disk_format.lower()
            if fmt == "thin":
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.sparse
            elif fmt == "thick":
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.flat
            else:
                return {"status": "error", "error": f"disk_format must be 'thin' or 'thick', got '{disk_format}'"}

        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
        )

        if customization_spec_name is not None:
            spec_manager = client.content.customizationSpecManager
            if spec_manager is None:
                return {"status": "error", "error": "Customization spec manager not available"}
            try:
                cust_spec_item = spec_manager.GetCustomizationSpec(name=customization_spec_name)
                clone_spec.customization = cust_spec_item.spec
            except Exception as e:
                return {"status": "error", "error": f"Customization spec '{customization_spec_name}' not found: {e}"}

        if num_cpus is not None or memory_mb is not None:
            config_spec = vim.vm.ConfigSpec()
            if num_cpus is not None:
                config_spec.numCPUs = num_cpus
            if memory_mb is not None:
                config_spec.memoryMB = memory_mb
            clone_spec.config = config_spec

        task = template_obj.Clone(folder=folder, name=vm_name, spec=clone_spec)
        result = wait_for_task(task)
        result["template_name"] = template_name
        result["vm_name"] = vm_name
        result["operation"] = "deploy_from_template"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def register_vm(
        datacenter_name: str,
        folder_name: str,
        vmx_path: str,
        vm_name: str,
        resource_pool_name: str | None = None,
        host_name: str | None = None,
        as_template: bool = False,
    ) -> dict[str, Any]:
        """Register a VMX file as a VM. vmx_path example: '[ds1] vm/vm.vmx'."""
        logger.info(
            "register_vm",
            datacenter_name=datacenter_name,
            folder_name=folder_name,
            vmx_path=vmx_path,
            vm_name=vm_name,
        )
        from vsphere_mcp.utils.property_collector import collect_properties

        # Find datacenter
        datacenters = collect_properties(client, vim.Datacenter, ["name"])
        dc_obj = None
        for dc in datacenters:
            if dc.get("name") == datacenter_name:
                dc_obj = dc["_obj"]
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        # Find folder
        folders = collect_properties(client, vim.Folder, ["name"])
        folder_obj = None
        for f in folders:
            if f.get("name") == folder_name:
                folder_obj = f["_obj"]
                break
        if folder_obj is None:
            return {"status": "error", "error": f"Folder '{folder_name}' not found"}

        # Resolve optional resource pool
        pool_obj = None
        if resource_pool_name is not None:
            rp_items = collect_properties(client, vim.ResourcePool, ["name"])
            pool_obj = next((r["_obj"] for r in rp_items if r.get("name") == resource_pool_name), None)
            if pool_obj is None:
                return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}

        # Resolve optional host
        host_obj = None
        if host_name is not None:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}

        task = folder_obj.RegisterVM_Task(
            path=vmx_path,
            name=vm_name,
            asTemplate=as_template,
            pool=pool_obj,
            host=host_obj,
        )
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["vmx_path"] = vmx_path
        result["operation"] = "register_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def convert_vm_to_template(vm_name: str) -> dict[str, Any]:
        """Convert a powered-off VM to a template."""
        logger.info("convert_vm_to_template", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before converting to template"}

        found["_obj"].MarkAsTemplate()
        return {"status": "success", "vm_name": vm_name, "operation": "convert_vm_to_template"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def convert_template_to_vm(
        vm_name: str,
        host_name: str,
        resource_pool_name: str | None = None,
    ) -> dict[str, Any]:
        """Convert a template back to a virtual machine on the specified host."""
        logger.info("convert_template_to_vm", vm_name=vm_name, host_name=host_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM/template '{vm_name}' not found"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        # Resolve resource pool
        if resource_pool_name is not None:
            from vsphere_mcp.utils.property_collector import collect_properties

            rp_items = collect_properties(client, vim.ResourcePool, ["name"])
            pool_obj = next((r["_obj"] for r in rp_items if r.get("name") == resource_pool_name), None)
            if pool_obj is None:
                return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}
        else:
            # Fall back to the host's parent resource pool
            pool_obj = host_obj.parent.resourcePool

        found["_obj"].MarkAsVirtualMachine(host=host_obj, pool=pool_obj)
        return {"status": "success", "vm_name": vm_name, "host_name": host_name, "operation": "convert_template_to_vm"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_vm(
        datacenter_name: str,
        folder_name: str,
        vm_name: str,
        num_cpus: int,
        memory_mb: int,
        guest_id: str,
        datastore_name: str,
        resource_pool_name: str | None = None,
        firmware: str = "bios",
        num_cores_per_socket: int = 1,
        cpu_hot_add_enabled: bool = False,
        memory_hot_add_enabled: bool = False,
        nested_hypervisor_enabled: bool = False,
        secure_boot: bool = False,
        annotation: str | None = None,
    ) -> dict[str, Any]:
        """Create a new empty virtual machine with the specified configuration.

        Args:
            datacenter_name: Name of the datacenter.
            folder_name: Name of the VM folder.
            vm_name: Name for the new VM.
            num_cpus: Number of virtual CPUs.
            memory_mb: Memory size in MB.
            guest_id: Guest OS type ID (use list_guest_os_types for valid values).
            datastore_name: Name of the target datastore.
            resource_pool_name: Resource pool name (optional, uses first available if not specified).
            firmware: Firmware type: 'bios' or 'efi' (default 'bios').
            num_cores_per_socket: Number of cores per CPU socket (default 1).
            cpu_hot_add_enabled: Enable CPU hot-add (default False).
            memory_hot_add_enabled: Enable memory hot-add (default False).
            nested_hypervisor_enabled: Enable nested virtualization / VHV (default False).
            secure_boot: Enable EFI Secure Boot (requires firmware='efi', default False).
            annotation: VM notes/annotation (optional).
        """
        logger.info(
            "create_vm",
            datacenter_name=datacenter_name,
            folder_name=folder_name,
            vm_name=vm_name,
            num_cpus=num_cpus,
            memory_mb=memory_mb,
            guest_id=guest_id,
            datastore_name=datastore_name,
        )
        if num_cpus <= 0:
            return {"status": "error", "error": "num_cpus must be a positive integer"}
        if memory_mb < 4:
            return {"status": "error", "error": "memory_mb must be at least 4"}
        if firmware not in ("bios", "efi"):
            return {"status": "error", "error": "firmware must be 'bios' or 'efi'"}
        from vsphere_mcp.utils.property_collector import collect_properties

        # Find datacenter
        datacenters = collect_properties(client, vim.Datacenter, ["name", "hostFolder"])
        dc_obj = None
        for dc in datacenters:
            if dc.get("name") == datacenter_name:
                dc_obj = dc["_obj"]
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        # Find folder
        folders = collect_properties(client, vim.Folder, ["name"])
        folder_obj = None
        for f in folders:
            if f.get("name") == folder_name:
                folder_obj = f["_obj"]
                break
        if folder_obj is None:
            return {"status": "error", "error": f"Folder '{folder_name}' not found"}

        # Find resource pool
        resource_pools = collect_properties(client, vim.ResourcePool, ["name"])
        pool_obj = None
        if resource_pool_name is not None:
            pool_obj = next((r["_obj"] for r in resource_pools if r.get("name") == resource_pool_name), None)
            if pool_obj is None:
                return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}
        else:
            if resource_pools:
                pool_obj = resource_pools[0]["_obj"]
                logger.warning("create_vm: no resource_pool_name specified, using first available pool")
            if pool_obj is None:
                return {"status": "error", "error": "No resource pool found"}

        if secure_boot and firmware != "efi":
            return {"status": "error", "error": "secure_boot requires firmware='efi'"}
        if num_cores_per_socket < 1:
            return {"status": "error", "error": "num_cores_per_socket must be at least 1"}
        if num_cpus % num_cores_per_socket != 0:
            return {"status": "error", "error": "num_cpus must be divisible by num_cores_per_socket"}

        # Build VM config spec
        vm_file_info = vim.vm.FileInfo(vmPathName=f"[{datastore_name}]")
        config_spec = vim.vm.ConfigSpec(
            name=vm_name,
            numCPUs=num_cpus,
            numCoresPerSocket=num_cores_per_socket,
            memoryMB=memory_mb,
            guestId=guest_id,
            files=vm_file_info,
            firmware=firmware,
            cpuHotAddEnabled=cpu_hot_add_enabled,
            memoryHotAddEnabled=memory_hot_add_enabled,
            nestedHVEnabled=nested_hypervisor_enabled,
        )
        if annotation is not None:
            config_spec.annotation = annotation
        if secure_boot:
            config_spec.bootOptions = vim.vm.BootOptions(efiSecureBootEnabled=True)

        task = folder_obj.CreateVM_Task(config=config_spec, pool=pool_obj)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "create_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def linked_clone_vm(
        vm_name: str,
        clone_name: str,
        snapshot_name: str,
        power_on: bool = False,
    ) -> dict[str, Any]:
        """Create a linked clone of a VM from a named snapshot.

        The snapshot must already exist. Linked clones share the parent's disk
        and consume less space but depend on the source snapshot remaining intact.
        """
        logger.info("linked_clone_vm", vm_name=vm_name, clone_name=clone_name, snapshot_name=snapshot_name)
        from vsphere_mcp.tools.snapshot import _find_snapshot_by_name

        found = find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
            return {"status": "error", "error": f"No snapshots found for VM '{vm_name}'"}

        snap_ref = _find_snapshot_by_name(snap_info.rootSnapshotList, snapshot_name)
        if snap_ref is None:
            return {
                "status": "error",
                "error": f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'",
            }

        vm_obj = found["_obj"]
        relocate_spec = vim.vm.RelocateSpec(diskMoveType="createNewChildDiskBacking")
        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
            snapshot=snap_ref,
        )
        task = vm_obj.Clone(folder=vm_obj.parent, name=clone_name, spec=clone_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["clone_name"] = clone_name
        result["snapshot_name"] = snapshot_name
        result["operation"] = "linked_clone_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def enable_vm_cbt(
        vm_name: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Enable or disable Changed Block Tracking (CBT) on a virtual machine.

        CBT allows incremental backup tools to identify which disk blocks have
        changed since the last backup. The VM must be powered off or a
        snapshot cycle may be required for the change to take effect.
        """
        logger.info("enable_vm_cbt", vm_name=vm_name, enabled=enabled)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        config_spec = vim.vm.ConfigSpec(changeTrackingEnabled=enabled)
        task = vm_obj.ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["change_tracking_enabled"] = enabled
        result["operation"] = "enable_vm_cbt"
        return result

    @mcp.tool()
    @handle_tool_errors
    def query_vm_changed_disk_areas(
        vm_name: str,
        snapshot_name: str,
        disk_key: int,
        start_offset: int = 0,
        change_id: str = "*",
    ) -> dict[str, Any]:
        """Query changed disk areas for incremental backup using Changed Block Tracking.

        Returns disk extents (offset + length) that have changed since the
        change_id baseline. Use '*' as change_id for the first query.
        Requires CBT to be enabled on the VM.
        """
        logger.info(
            "query_vm_changed_disk_areas",
            vm_name=vm_name,
            snapshot_name=snapshot_name,
            disk_key=disk_key,
            change_id=change_id,
        )
        from vsphere_mcp.tools.snapshot import _find_snapshot_by_name

        found = find_vm_with_props(client, vm_name, ["snapshot"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        snap_info = found.get("snapshot")
        if not snap_info or not hasattr(snap_info, "rootSnapshotList"):
            return {"status": "error", "error": f"No snapshots found for VM '{vm_name}'"}

        snap_ref = _find_snapshot_by_name(snap_info.rootSnapshotList, snapshot_name)
        if snap_ref is None:
            return {
                "status": "error",
                "error": f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'",
            }

        vm_obj = found["_obj"]
        disk_change_info = vm_obj.QueryChangedDiskAreas(
            snapshot=snap_ref,
            deviceKey=disk_key,
            startOffset=start_offset,
            changeId=change_id,
        )

        extents = []
        for ext in disk_change_info.changedArea or []:
            extents.append({"start": ext.start, "length": ext.length})

        return {
            "vm_name": vm_name,
            "snapshot_name": snapshot_name,
            "disk_key": disk_key,
            "start_offset": start_offset,
            "change_id": change_id,
            "total_extents": len(extents),
            "changed_areas": extents,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def answer_vm_question(
        vm_name: str,
        choice_id: str,
    ) -> dict[str, Any]:
        """Answer a pending question blocking a virtual machine.

        Some VM operations (power on, snapshot revert, etc.) can stall waiting
        for user input. Use get_vm_pending_question to inspect the choices,
        then supply the choice_id (e.g. '0', '1') to unblock the VM.
        """
        logger.info("answer_vm_question", vm_name=vm_name, choice_id=choice_id)
        found = find_vm_with_props(client, vm_name, ["runtime.question"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        question = vm_obj.runtime.question
        if question is None:
            return {"status": "error", "error": f"VM '{vm_name}' has no pending question"}

        vm_obj.AnswerVM(questionId=question.id, answerChoice=choice_id)
        return {
            "status": "success",
            "vm_name": vm_name,
            "question_id": question.id,
            "choice_id": choice_id,
            "operation": "answer_vm_question",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vm_pending_question(vm_name: str) -> dict[str, Any]:
        """Get the pending question blocking a virtual machine, if any.

        Returns the question text and the available answer choices. If no
        question is pending, reports accordingly.
        """
        logger.info("get_vm_pending_question", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["runtime.question"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        question = vm_obj.runtime.question
        if question is None:
            return {"vm_name": vm_name, "pending_question": None, "message": "No pending question"}

        choices = []
        if hasattr(question, "choice") and question.choice:
            for opt in question.choice.choiceInfo or []:
                choices.append({"key": opt.key, "label": opt.label})

        return {
            "vm_name": vm_name,
            "pending_question": {
                "id": question.id,
                "text": question.text,
                "choices": choices,
                "default_choice": question.choice.defaultIndex if hasattr(question.choice, "defaultIndex") else None,
            },
        }

    @mcp.tool()
    @handle_tool_errors
    def list_guest_os_types() -> dict[str, Any]:
        """List common supported guest OS type IDs for use when creating VMs."""
        logger.info("list_guest_os_types")
        guest_os_types = [
            {"id": "dosGuest", "description": "MS-DOS"},
            {"id": "win31Guest", "description": "Windows 3.1"},
            {"id": "win95Guest", "description": "Windows 95"},
            {"id": "win98Guest", "description": "Windows 98"},
            {"id": "winNTGuest", "description": "Windows NT"},
            {"id": "win2000ProGuest", "description": "Windows 2000 Professional"},
            {"id": "win2000ServGuest", "description": "Windows 2000 Server"},
            {"id": "winXPProGuest", "description": "Windows XP Professional (32-bit)"},
            {"id": "winXPPro64Guest", "description": "Windows XP Professional (64-bit)"},
            {"id": "winNetEnterpriseGuest", "description": "Windows Server 2003 Enterprise (32-bit)"},
            {"id": "winNetEnterprise64Guest", "description": "Windows Server 2003 Enterprise (64-bit)"},
            {"id": "winVista64Guest", "description": "Windows Vista (64-bit)"},
            {"id": "windows7_64Guest", "description": "Windows 7 (64-bit)"},
            {"id": "windows8_64Guest", "description": "Windows 8 (64-bit)"},
            {"id": "windows9_64Guest", "description": "Windows 10/11 (64-bit)"},
            {"id": "windows9Server64Guest", "description": "Windows Server 2016/2019/2022 (64-bit)"},
            {"id": "ubuntu64Guest", "description": "Ubuntu Linux (64-bit)"},
            {"id": "centos64Guest", "description": "CentOS (64-bit)"},
            {"id": "rhel7_64Guest", "description": "Red Hat Enterprise Linux 7 (64-bit)"},
            {"id": "rhel8_64Guest", "description": "Red Hat Enterprise Linux 8 (64-bit)"},
            {"id": "rhel9_64Guest", "description": "Red Hat Enterprise Linux 9 (64-bit)"},
            {"id": "debian10_64Guest", "description": "Debian 10 (64-bit)"},
            {"id": "debian11_64Guest", "description": "Debian 11 (64-bit)"},
            {"id": "sles15_64Guest", "description": "SUSE Linux Enterprise Server 15 (64-bit)"},
            {"id": "fedora64Guest", "description": "Fedora Linux (64-bit)"},
            {"id": "other3xLinux64Guest", "description": "Other Linux 3.x (64-bit)"},
            {"id": "other4xLinux64Guest", "description": "Other Linux 4.x (64-bit)"},
            {"id": "other5xLinux64Guest", "description": "Other Linux 5.x (64-bit)"},
            {"id": "otherLinux64Guest", "description": "Other Linux (64-bit)"},
            {"id": "freebsd64Guest", "description": "FreeBSD (64-bit)"},
            {"id": "otherGuest64", "description": "Other (64-bit)"},
        ]
        return {"guest_os_types": guest_os_types}
