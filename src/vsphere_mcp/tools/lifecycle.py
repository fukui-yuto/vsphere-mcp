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
    ) -> dict[str, Any]:
        """Clone an existing virtual machine."""
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

        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
        )
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
    ) -> dict[str, Any]:
        """Deploy a new VM from a template."""
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

        clone_spec = vim.vm.CloneSpec(
            location=relocate_spec,
            powerOn=power_on,
            template=False,
        )
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
    ) -> dict[str, Any]:
        """Create a new empty virtual machine with the specified configuration."""
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

        # Build VM config spec
        vm_file_info = vim.vm.FileInfo(vmPathName=f"[{datastore_name}]")
        config_spec = vim.vm.ConfigSpec(
            name=vm_name,
            numCPUs=num_cpus,
            memoryMB=memory_mb,
            guestId=guest_id,
            files=vm_file_info,
            firmware=firmware,
        )

        task = folder_obj.CreateVM_Task(config=config_spec, pool=pool_obj)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "create_vm"
        return result

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
