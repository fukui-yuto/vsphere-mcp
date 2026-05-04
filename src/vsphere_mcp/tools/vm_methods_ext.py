from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_vm_methods_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def promote_vm_disks(
        vm_name: str,
        unlink: bool = True,
        disks: list[str] | None = None,
    ) -> dict[str, Any]:
        """Promote linked clone disks to full independent disks.

        Linked clones share disk blocks with a parent VM snapshot. Promoting
        them makes each disk a fully independent copy, removing the parent
        dependency. This operation can consume significant additional storage.

        Args:
            vm_name: Name of the VM whose disks to promote.
            unlink: If True, unlink the disks from their parent chain (default True).
            disks: Optional list of disk device keys (as strings) to promote.
                   If None or empty, all linked disks are promoted.
        """
        logger.info("promote_vm_disks", vm_name=vm_name, unlink=unlink)

        found = find_vm_with_props(client, vm_name, extra_props=["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]

        disk_objs: list[Any] | None = None
        if disks:
            devices = found.get("config.hardware.device") or []
            disk_objs = []
            requested_keys = set(str(k) for k in disks)
            for dev in devices:
                if isinstance(dev, vim.vm.device.VirtualDisk):
                    if str(dev.key) in requested_keys:
                        disk_objs.append(dev)
            if not disk_objs:
                return {"status": "error", "error": f"None of the specified disk keys found on VM '{vm_name}'"}

        try:
            task = vm_obj.PromoteDisks_Task(unlink=unlink, disks=disk_objs)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initiate disk promotion: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to promote VM disks")}

        return {
            "status": "success",
            "operation": "promote_vm_disks",
            "vm_name": vm_name,
            "unlink": unlink,
            "disks_specified": disks,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def terminate_vm(vm_name: str) -> dict[str, Any]:
        """Force-terminate a VM process immediately without a graceful shutdown.

        This is equivalent to pulling the power cord — no ACPI shutdown signal
        is sent and no VMware Tools interaction occurs. Use only when the VM is
        unresponsive to normal power-off operations.

        Args:
            vm_name: Name of the VM to terminate.
        """
        logger.info("terminate_vm", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        try:
            vm_obj.TerminateVM()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to terminate VM: {exc}"}

        return {
            "status": "success",
            "operation": "terminate_vm",
            "vm_name": vm_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def mount_tools_installer(vm_name: str) -> dict[str, Any]:
        """Mount the VMware Tools installer ISO into the VM's CD/DVD drive.

        After mounting, the guest OS can auto-run or manually install VMware Tools
        from the virtual CD-ROM. The VM must be powered on.

        Args:
            vm_name: Name of the VM to mount the VMware Tools installer on.
        """
        logger.info("mount_tools_installer", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        try:
            vm_obj.MountToolsInstaller()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to mount VMware Tools installer: {exc}"}

        return {
            "status": "success",
            "operation": "mount_tools_installer",
            "vm_name": vm_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def unmount_tools_installer(vm_name: str) -> dict[str, Any]:
        """Unmount the VMware Tools installer CD from the VM's CD/DVD drive.

        Args:
            vm_name: Name of the VM to unmount the VMware Tools installer from.
        """
        logger.info("unmount_tools_installer", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        try:
            vm_obj.UnmountToolsInstaller()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to unmount VMware Tools installer: {exc}"}

        return {
            "status": "success",
            "operation": "unmount_tools_installer",
            "vm_name": vm_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def query_ft_compatibility(vm_name: str) -> dict[str, Any]:
        """Check Fault Tolerance (FT) compatibility for a VM.

        Queries vCenter to determine whether the VM meets the requirements for
        enabling VMware Fault Tolerance. Returns a list of compatibility issues
        that would prevent FT enablement.

        Args:
            vm_name: Name of the VM to check for FT compatibility.
        """
        logger.info("query_ft_compatibility", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        issues: list[dict[str, Any]] = []

        try:
            # Try the extended version first (vSphere 6.0+)
            raw = vm_obj.QueryFaultToleranceCompatibilityEx()
        except AttributeError:
            try:
                raw = vm_obj.QueryFaultToleranceCompatibility()
            except AttributeError:
                return {
                    "status": "unavailable",
                    "message": "FT compatibility query API is not available on this vCenter version",
                    "vm_name": vm_name,
                    "issues": [],
                }
            except Exception as exc:
                return {"status": "error", "error": f"Failed to query FT compatibility: {exc}"}
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query FT compatibility: {exc}"}

        for item in raw or []:
            issues.append({
                "key": getattr(item, "key", None),
                "arg": [str(a) for a in (getattr(item, "arg", None) or [])],
                "message": str(getattr(item, "message", item)),
            })

        return {
            "status": "success",
            "vm_name": vm_name,
            "ft_compatible": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
        }

    @mcp.tool()
    @handle_tool_errors
    def query_vm_unowned_files(vm_name: str) -> dict[str, Any]:
        """Find files in a VM's directory that are not registered as part of the VM.

        Unowned files are leftover files in the VM storage directory that are not
        referenced by the VM configuration — for example, orphaned snapshots or
        temporary files. These can safely be deleted to reclaim storage.

        Args:
            vm_name: Name of the VM to inspect for unowned files.
        """
        logger.info("query_vm_unowned_files", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        try:
            file_list = vm_obj.QueryUnownedFiles()
        except AttributeError:
            return {
                "status": "unavailable",
                "message": "QueryUnownedFiles API is not available on this vCenter version",
                "vm_name": vm_name,
                "files": [],
            }
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query unowned files: {exc}"}

        return {
            "status": "success",
            "vm_name": vm_name,
            "file_count": len(file_list or []),
            "files": list(file_list or []),
        }
