from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_host_mgr_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def backup_host_firmware(host_name: str) -> dict[str, Any]:
        """Backup the ESXi host firmware/configuration to a downloadable bundle.

        Generates a configuration bundle containing the current ESXi host settings.
        The returned URL can be used to download the backup archive.

        Args:
            host_name: Name of the ESXi host to backup.
        """
        logger.info("backup_host_firmware", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        firmware_system = getattr(cm, "firmwareSystem", None)
        if firmware_system is None:
            return {"status": "error", "error": "firmwareSystem not available on this host"}

        try:
            download_url = firmware_system.BackupFirmwareConfiguration()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to backup firmware configuration: {exc}"}

        return {
            "status": "success",
            "operation": "backup_host_firmware",
            "host_name": host_name,
            "download_url": download_url,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def restore_host_firmware(host_name: str, force: bool = False) -> dict[str, Any]:
        """Restore the ESXi host firmware/configuration from a previously created backup.

        Restores the host configuration to the state captured during the last backup.
        The host may need to be rebooted after restoration for all settings to take effect.

        Args:
            host_name: Name of the ESXi host to restore.
            force: If True, force the restore even if version mismatches are detected (default False).
        """
        logger.info("restore_host_firmware", host_name=host_name, force=force)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        firmware_system = getattr(cm, "firmwareSystem", None)
        if firmware_system is None:
            return {"status": "error", "error": "firmwareSystem not available on this host"}

        try:
            firmware_system.RestoreFirmwareConfiguration(force=force)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to restore firmware configuration: {exc}"}

        return {
            "status": "success",
            "operation": "restore_host_firmware",
            "host_name": host_name,
            "force": force,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_boot_devices(host_name: str) -> dict[str, Any]:
        """Get the boot device list for an ESXi host.

        Returns the ordered list of boot devices configured on the host, including
        device keys, descriptions, and boot order.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_boot_devices", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        boot_device_system = getattr(cm, "bootDeviceSystem", None)
        if boot_device_system is None:
            return {"status": "error", "error": "bootDeviceSystem not available on this host"}

        try:
            boot_info = boot_device_system.QueryBootDevices()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query boot devices: {exc}"}

        if boot_info is None:
            return {"status": "success", "host_name": host_name, "boot_devices": [], "boot_order": []}

        devices = []
        for dev in getattr(boot_info, "bootDevices", None) or []:
            devices.append({
                "key": getattr(dev, "key", None),
                "description": getattr(dev, "description", None),
            })

        boot_order = []
        for entry in getattr(boot_info, "currentBootOrderPreference", None) or []:
            boot_order.append(str(entry))

        return {
            "status": "success",
            "host_name": host_name,
            "boot_devices": devices,
            "boot_order": boot_order,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_host_boot_device(host_name: str, device_key: str) -> dict[str, Any]:
        """Set the primary boot device for an ESXi host.

        Changes the boot device preference on the host. The new setting takes
        effect on the next host reboot.

        Args:
            host_name: Name of the ESXi host.
            device_key: Key of the boot device to set as primary (from get_host_boot_devices).
        """
        logger.info("set_host_boot_device", host_name=host_name, device_key=device_key)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        boot_device_system = getattr(cm, "bootDeviceSystem", None)
        if boot_device_system is None:
            return {"status": "error", "error": "bootDeviceSystem not available on this host"}

        try:
            boot_device_system.UpdateBootDevice(key=device_key)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to set boot device: {exc}"}

        return {
            "status": "success",
            "operation": "set_host_boot_device",
            "host_name": host_name,
            "device_key": device_key,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_host_cache(
        host_name: str,
        datastore_name: str,
        swap_size_mb: int = 0,
    ) -> dict[str, Any]:
        """Configure SSD-backed host cache for a swap file on an ESXi host.

        Host cache uses SSD storage to accelerate VM swapping. Specify a datastore
        backed by an SSD device and the amount of space to reserve for host swap.

        Args:
            host_name: Name of the ESXi host.
            datastore_name: Name of the SSD-backed datastore to use for host cache.
            swap_size_mb: Amount of swap space to allocate in megabytes (default 0 to disable).
        """
        logger.info("configure_host_cache", host_name=host_name, datastore_name=datastore_name, swap_size_mb=swap_size_mb)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        cache_mgr = getattr(cm, "cacheConfigurationManager", None)
        if cache_mgr is None:
            return {"status": "error", "error": "cacheConfigurationManager not available on this host"}

        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        spec = vim.host.CacheConfigurationManager.CacheConfigurationSpec(
            datastore=ds_obj,
            swapSize=swap_size_mb,
        )

        try:
            task = cache_mgr.ConfigureHostCache_Task(spec=spec)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initiate host cache configuration: {exc}"}

        result = wait_for_task(task)
        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure host cache")}

        return {
            "status": "success",
            "operation": "configure_host_cache",
            "host_name": host_name,
            "datastore_name": datastore_name,
            "swap_size_mb": swap_size_mb,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_cache_config(host_name: str) -> dict[str, Any]:
        """Get the current host cache configuration for an ESXi host.

        Returns information about the SSD datastore and swap size currently
        configured for host-level caching.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_cache_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        cache_mgr = getattr(cm, "cacheConfigurationManager", None)
        if cache_mgr is None:
            return {"status": "error", "error": "cacheConfigurationManager not available on this host"}

        cache_info_list = getattr(cache_mgr, "cacheConfigurationInfo", None) or []
        configs = []
        for entry in cache_info_list:
            ds_ref = getattr(entry, "key", None)
            ds_name = None
            if ds_ref is not None:
                try:
                    ds_name = getattr(ds_ref, "name", None)
                except Exception:
                    ds_name = str(ds_ref)
            configs.append({
                "datastore": ds_name,
                "swap_size_mb": getattr(entry, "swapSize", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "cache_configurations": configs,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_host_kernel_modules(host_name: str) -> dict[str, Any]:
        """List ESXi kernel modules (VMkernel drivers) loaded on a host.

        Returns all kernel modules with their name, version, description, and
        enabled/disabled status.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("list_host_kernel_modules", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        kernel_module_system = getattr(cm, "kernelModuleSystem", None)
        if kernel_module_system is None:
            return {"status": "error", "error": "kernelModuleSystem not available on this host"}

        try:
            modules_raw = kernel_module_system.QueryModules()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query kernel modules: {exc}"}

        modules = []
        for mod in modules_raw or []:
            modules.append({
                "name": getattr(mod, "name", None),
                "version": getattr(mod, "version", None),
                "filename": getattr(mod, "filename", None),
                "description": getattr(mod, "optionString", None),
                "enabled": getattr(mod, "enabled", None),
                "use_count": getattr(mod, "useCount", None),
                "loaded": getattr(mod, "loaded", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "module_count": len(modules),
            "modules": modules,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_vmkernel_nic_services(host_name: str) -> dict[str, Any]:
        """Get VMkernel NIC service bindings for an ESXi host.

        Queries all known VMkernel NIC service types (vMotion, management, vSAN,
        vSphere Replication, FT logging, etc.) and returns which VMkernel adapters
        are selected for each service.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_vmkernel_nic_services", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        virtual_nic_manager = getattr(cm, "virtualNicManager", None)
        if virtual_nic_manager is None:
            return {"status": "error", "error": "virtualNicManager not available on this host"}

        nic_types = [
            "vmotion",
            "management",
            "vsan",
            "vSphereReplication",
            "vSphereReplicationNFC",
            "faultToleranceLogging",
            "vSphereProvisioning",
        ]

        services: dict[str, Any] = {}
        for nic_type in nic_types:
            try:
                net_config = virtual_nic_manager.QueryNetConfig(nicType=nic_type)
                if net_config is None:
                    services[nic_type] = {"selected": [], "candidates": []}
                    continue

                selected = []
                for sel in getattr(net_config, "selectedVnic", None) or []:
                    selected.append(str(sel))

                candidates = []
                for cand in getattr(net_config, "candidateVnic", None) or []:
                    candidates.append({
                        "device": getattr(cand, "device", None),
                        "port": getattr(cand, "port", None),
                        "portgroup": getattr(cand, "portgroup", None),
                    })

                services[nic_type] = {"selected": selected, "candidates": candidates}
            except Exception as exc:
                services[nic_type] = {"error": str(exc)}

        return {
            "status": "success",
            "host_name": host_name,
            "vmkernel_nic_services": services,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_vmkernel_nic_service(
        host_name: str,
        vmk_name: str,
        service_type: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Select or deselect a VMkernel NIC for a specific service type on an ESXi host.

        Controls which VMkernel adapter handles a given service such as vMotion,
        management traffic, vSAN, or Fault Tolerance logging.

        Args:
            host_name: Name of the ESXi host.
            vmk_name: VMkernel adapter name (e.g., "vmk0", "vmk1").
            service_type: Service type to configure. Valid values include:
                "vmotion", "management", "vsan", "faultToleranceLogging",
                "vSphereReplication", "vSphereReplicationNFC", "vSphereProvisioning".
            enabled: If True, select this NIC for the service; if False, deselect it (default True).
        """
        logger.info(
            "set_host_vmkernel_nic_service",
            host_name=host_name,
            vmk_name=vmk_name,
            service_type=service_type,
            enabled=enabled,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        virtual_nic_manager = getattr(cm, "virtualNicManager", None)
        if virtual_nic_manager is None:
            return {"status": "error", "error": "virtualNicManager not available on this host"}

        try:
            if enabled:
                virtual_nic_manager.SelectVnic(nicType=service_type, device=vmk_name)
            else:
                virtual_nic_manager.DeselectVnic(nicType=service_type, device=vmk_name)
        except Exception as exc:
            action = "select" if enabled else "deselect"
            return {"status": "error", "error": f"Failed to {action} VMkernel NIC service: {exc}"}

        return {
            "status": "success",
            "operation": "set_host_vmkernel_nic_service",
            "host_name": host_name,
            "vmk_name": vmk_name,
            "service_type": service_type,
            "enabled": enabled,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_image_config(host_name: str) -> dict[str, Any]:
        """Get the ESXi software image and VIB (VMware Installation Bundle) configuration.

        Returns information about the currently installed ESXi image profile, software
        packages, and acceptance level. Availability depends on the ESXi version and
        whether the host is managed through VLCM or legacy Update Manager.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_image_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        image_config_manager = getattr(cm, "imageConfigManager", None)
        if image_config_manager is None:
            return {
                "status": "unavailable",
                "message": "imageConfigManager is not available on this host — may require ESXi 5.0+ with Image Builder support",
                "host_name": host_name,
            }

        result: dict[str, Any] = {
            "status": "success",
            "host_name": host_name,
        }

        try:
            fetch_url = image_config_manager.FetchSoftwarePackages()
            packages = []
            for pkg in fetch_url or []:
                packages.append({
                    "name": getattr(pkg, "name", None),
                    "version": getattr(pkg, "version", None),
                    "vendor": getattr(pkg, "vendor", None),
                    "description": getattr(pkg, "description", None),
                    "acceptance_level": getattr(pkg, "acceptanceLevel", None),
                })
            result["packages"] = packages
            result["package_count"] = len(packages)
        except AttributeError:
            result["packages"] = None
        except Exception as exc:
            result["packages_error"] = str(exc)

        try:
            profile = image_config_manager.GetSoftwarePackages()
            result["installed_packages"] = [str(p) for p in (profile or [])]
        except AttributeError:
            pass
        except Exception as exc:
            result["installed_packages_error"] = str(exc)

        try:
            acceptance = image_config_manager.QueryHostAcceptanceLevel()
            result["acceptance_level"] = str(acceptance)
        except AttributeError:
            pass
        except Exception as exc:
            result["acceptance_level_error"] = str(exc)

        return result
