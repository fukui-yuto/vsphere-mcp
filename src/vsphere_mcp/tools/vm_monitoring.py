from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_cluster_for_vm(client: VSphereClient, vm_obj: Any) -> Any | None:
    """Walk the parent chain of a VM's host to find the owning ClusterComputeResource."""
    current = getattr(vm_obj, "parent", None)
    max_depth = 20
    depth = 0
    while current and depth < max_depth:
        if isinstance(current, vim.ClusterComputeResource):
            return current
        current = getattr(current, "parent", None)
        depth += 1
    return None


def _format_uptime(seconds: int) -> str:
    """Convert seconds to a human-readable duration string."""
    days = seconds // 86400
    remaining = seconds % 86400
    hours = remaining // 3600
    remaining = remaining % 3600
    minutes = remaining // 60
    secs = remaining % 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def register_vm_monitoring_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_monitoring(
        vm_name: str,
        monitoring_mode: str = "vmMonitoringOnly",
        failure_interval: int = 30,
        min_uptime: int = 120,
        max_failures: int = 3,
        max_failure_window: int = -1,
    ) -> dict[str, Any]:
        """Configure VM monitoring (HA VM heartbeat monitoring) for a virtual machine.

        Args:
            vm_name: Name of the VM to configure monitoring for.
            monitoring_mode: Monitoring mode — 'vmMonitoringOnly' (VM heartbeats) or
                             'vmAndAppMonitoring' (VM and application heartbeats).
            failure_interval: Seconds after which the VM is declared failed with no heartbeat.
            min_uptime: Minimum uptime in seconds before monitoring activates after a VM reset.
            max_failures: Maximum number of resets allowed within the failure window.
            max_failure_window: Seconds defining the failure window. -1 means no window limit.
        """
        logger.info("set_vm_monitoring", vm_name=vm_name, monitoring_mode=monitoring_mode)

        valid_modes = {"vmMonitoringOnly", "vmAndAppMonitoring"}
        if monitoring_mode not in valid_modes:
            return {
                "status": "error",
                "error": f"Invalid monitoring_mode '{monitoring_mode}'. Valid: {sorted(valid_modes)}",
            }

        found = find_vm_with_props(client, vm_name, [])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        cluster = _find_cluster_for_vm(client, vm_obj)
        if cluster is None:
            return {
                "status": "error",
                "error": f"VM '{vm_name}' is not in a cluster — HA monitoring requires a cluster",
            }

        das_settings = vim.cluster.DasVmSettings(
            vmToolsMonitoringSettings=vim.cluster.VmToolsMonitoringSettings(
                vmMonitoring=monitoring_mode,
                clusterSettings=False,
                failureInterval=failure_interval,
                minUpTime=min_uptime,
                maxFailures=max_failures,
                maxFailureWindow=max_failure_window,
            )
        )
        das_vm_config_spec = vim.cluster.DasVmConfigSpec(
            operation=vim.option.ArrayUpdateSpec.Operation.edit,
            info=vim.cluster.DasVmConfigInfo(
                key=vm_obj,
                dasSettings=das_settings,
            ),
        )
        cluster_spec = vim.cluster.ConfigSpecEx(
            dasVmConfigSpec=[das_vm_config_spec],
        )
        task = cluster.ReconfigureComputeResource_Task(spec=cluster_spec, modify=True)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["monitoring_mode"] = monitoring_mode
        result["operation"] = "set_vm_monitoring"
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vm_monitoring_state(vm_name: str) -> dict[str, Any]:
        """Get the HA VM monitoring configuration for a virtual machine.

        Args:
            vm_name: Name of the VM to query.
        """
        logger.info("get_vm_monitoring_state", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, ["runtime.dasVmProtection"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        das_protection = found.get("runtime.dasVmProtection")

        result: dict[str, Any] = {
            "vm_name": vm_name,
            "das_protected": getattr(das_protection, "dasProtected", None) if das_protection else None,
        }

        cluster = _find_cluster_for_vm(client, vm_obj)
        if cluster is None:
            result["cluster"] = None
            result["vm_override"] = None
            return result

        result["cluster"] = getattr(cluster, "name", None)

        config = getattr(cluster, "configuration", None)
        das_vm_config = getattr(config, "dasVmConfig", []) if config else []
        override = None
        for entry in das_vm_config:
            if getattr(entry, "key", None) == vm_obj:
                override = entry
                break

        if override and override.dasSettings and override.dasSettings.vmToolsMonitoringSettings:
            mon = override.dasSettings.vmToolsMonitoringSettings
            result["vm_override"] = {
                "vmMonitoring": mon.vmMonitoring,
                "clusterSettings": mon.clusterSettings,
                "failureInterval": mon.failureInterval,
                "minUpTime": mon.minUpTime,
                "maxFailures": mon.maxFailures,
                "maxFailureWindow": mon.maxFailureWindow,
            }
        else:
            result["vm_override"] = None
            das_config = getattr(config, "dasConfig", None) if config else None
            if das_config:
                result["cluster_default_monitoring"] = getattr(das_config, "vmMonitoring", None)

        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vm_uptime(vm_name: str) -> dict[str, Any]:
        """Get uptime information for a virtual machine based on its boot time.

        Args:
            vm_name: Name of the VM to query.
        """
        logger.info("get_vm_uptime", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, ["runtime.bootTime"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        boot_time = found.get("runtime.bootTime")

        if power_state != vim.VirtualMachine.PowerState.poweredOn:
            return {
                "vm_name": vm_name,
                "power_state": str(power_state),
                "uptime_seconds": None,
                "uptime_human_readable": None,
                "boot_time": None,
            }

        if boot_time is None:
            return {
                "vm_name": vm_name,
                "power_state": str(power_state),
                "uptime_seconds": None,
                "uptime_human_readable": "Boot time not available",
                "boot_time": None,
            }

        now = datetime.now(tz=timezone.utc)
        if boot_time.tzinfo is None:
            boot_time = boot_time.replace(tzinfo=timezone.utc)
        uptime_seconds = int((now - boot_time).total_seconds())

        return {
            "vm_name": vm_name,
            "power_state": str(power_state),
            "boot_time": boot_time.isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_human_readable": _format_uptime(uptime_seconds),
        }

    @mcp.tool()
    @handle_tool_errors
    def export_vm_configuration(vm_name: str) -> dict[str, Any]:
        """Export the configuration of a virtual machine as a structured dictionary.

        Args:
            vm_name: Name of the VM to export configuration for.
        """
        logger.info("export_vm_configuration", vm_name=vm_name)

        extra_props = [
            "config.hardware.numCPU",
            "config.hardware.memoryMB",
            "config.hardware.device",
            "config.hardware.numCoresPerSocket",
            "config.guestId",
            "config.guestFullName",
            "config.uuid",
            "config.instanceUuid",
            "config.version",
            "config.firmware",
            "config.annotation",
            "config.files.vmPathName",
            "config.extraConfig",
            "config.cpuHotAddEnabled",
            "config.memoryHotAddEnabled",
            "config.nestedHVEnabled",
        ]

        found = find_vm_with_props(client, vm_name, extra_props)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        devices = found.get("config.hardware.device", [])
        disks = []
        nics = []
        for dev in devices:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                backing_file = None
                if hasattr(dev, "backing") and hasattr(dev.backing, "fileName"):
                    backing_file = dev.backing.fileName
                disks.append({
                    "label": dev.deviceInfo.label if dev.deviceInfo else None,
                    "capacity_kb": dev.capacityInKB,
                    "backing_file": backing_file,
                    "thin_provisioned": getattr(dev.backing, "thinProvisioned", None),
                })
            elif isinstance(dev, vim.vm.device.VirtualEthernetCard):
                nics.append({
                    "label": dev.deviceInfo.label if dev.deviceInfo else None,
                    "mac_address": dev.macAddress,
                    "network": getattr(getattr(dev, "backing", None), "deviceName", None),
                    "connected": getattr(getattr(dev, "connectable", None), "connected", None),
                })

        extra_config = {}
        for item in (found.get("config.extraConfig") or []):
            extra_config[item.key] = item.value

        return {
            "vm_name": vm_name,
            "hardware": {
                "numCPU": found.get("config.hardware.numCPU"),
                "numCoresPerSocket": found.get("config.hardware.numCoresPerSocket"),
                "memoryMB": found.get("config.hardware.memoryMB"),
                "version": found.get("config.version"),
                "firmware": found.get("config.firmware"),
            },
            "guest": {
                "guestId": found.get("config.guestId"),
                "guestFullName": found.get("config.guestFullName"),
            },
            "identity": {
                "uuid": found.get("config.uuid"),
                "instanceUuid": found.get("config.instanceUuid"),
            },
            "files": {
                "vmPathName": found.get("config.files.vmPathName"),
            },
            "annotation": found.get("config.annotation", ""),
            "capabilities": {
                "cpuHotAddEnabled": found.get("config.cpuHotAddEnabled"),
                "memoryHotAddEnabled": found.get("config.memoryHotAddEnabled"),
                "nestedHVEnabled": found.get("config.nestedHVEnabled"),
            },
            "disks": disks,
            "nics": nics,
            "extraConfig": extra_config,
        }

    @mcp.tool()
    @handle_tool_errors
    def find_orphaned_vmdks(datastore_name: str) -> dict[str, Any]:
        """Find VMDK files on a datastore that are not attached to any registered VM.

        Args:
            datastore_name: Name of the datastore to scan.
        """
        logger.info("find_orphaned_vmdks", datastore_name=datastore_name)

        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        browser = getattr(ds_obj, "browser", None)
        if browser is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' browser not available"}

        search_spec = vim.host.DatastoreBrowser.SearchSpec(
            matchPattern=["*.vmdk"],
            details=vim.host.DatastoreBrowser.FileInfo.Details(
                fileType=True,
                fileSize=True,
                modification=True,
            ),
            query=[vim.host.DatastoreBrowser.VmDiskQuery()],
        )
        task = browser.SearchDatastoreSubFolders_Task(
            datastorePath=f"[{datastore_name}]",
            searchSpec=search_spec,
        )
        task_result = wait_for_task(task)
        if task_result.get("status") != "success":
            return task_result

        all_vmdk_paths: set[str] = set()
        if hasattr(task.info, "result") and task.info.result:
            for folder_result in task.info.result:
                folder_path = folder_result.folderPath
                for file_info in folder_result.file or []:
                    full_path = folder_path + file_info.path
                    all_vmdk_paths.add(full_path)

        vm_items = collect_properties(client, vim.VirtualMachine, ["config.hardware.device"])
        registered_vmdks: set[str] = set()
        for vm_item in vm_items:
            devices = vm_item.get("config.hardware.device") or []
            for dev in devices:
                if isinstance(dev, vim.vm.device.VirtualDisk):
                    backing = getattr(dev, "backing", None)
                    if backing and hasattr(backing, "fileName"):
                        registered_vmdks.add(backing.fileName)

        flat_suffix = "-flat.vmdk"
        orphaned = []
        for path in sorted(all_vmdk_paths):
            if path.endswith(flat_suffix):
                continue
            if path not in registered_vmdks:
                orphaned.append(path)

        return {
            "datastore": datastore_name,
            "total_vmdks_found": len(all_vmdk_paths),
            "total_registered": len(registered_vmdks),
            "orphaned_count": len(orphaned),
            "orphaned_vmdks": orphaned,
        }
