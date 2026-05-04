from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_storage_ops_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vaai_status(host_name: str) -> dict[str, Any]:
        """Get VAAI (vStorage APIs for Array Integration) hardware acceleration status per LUN on an ESXi host.

        Returns per-LUN VAAI capability flags including hardware-accelerated locking,
        copy, and zeroing support.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_vaai_status", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}

        device_info = storage_system.storageDeviceInfo
        if device_info is None:
            return {"status": "error", "error": "storageDeviceInfo not available"}

        lun_vaai_info = []
        for lun in device_info.scsiLun or []:
            caps = getattr(lun, "capabilities", None)
            vaai_caps: dict[str, Any] = {}
            if caps is not None:
                # VAAI capabilities are exposed as individual VScsiLunCapability entries
                if isinstance(caps, list):
                    for cap in caps:
                        cap_key = getattr(cap, "key", "")
                        cap_val = getattr(cap, "value", None)
                        if cap_key:
                            vaai_caps[cap_key] = cap_val
                else:
                    # Some API versions expose capabilities as a flat object
                    for attr_name in dir(caps):
                        if attr_name.startswith("_") or callable(getattr(caps, attr_name, None)):
                            continue
                        vaai_caps[attr_name] = getattr(caps, attr_name, None)

            lun_vaai_info.append({
                "device_name": lun.deviceName,
                "display_name": lun.displayName,
                "vendor": lun.vendor,
                "model": lun.model,
                "lun_type": lun.lunType,
                "vaai_capabilities": vaai_caps,
            })

        return {
            "status": "success",
            "host_name": host_name,
            "lun_count": len(lun_vaai_info),
            "luns": lun_vaai_info,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def unmap_vmfs_datastore(datastore_name: str) -> dict[str, Any]:
        """Reclaim dead/deleted space on a VMFS datastore using the UNMAP primitive.

        This sends SCSI UNMAP commands to the underlying array to reclaim thin-provisioned
        space that was freed by deleted VMs or files. The operation may take significant time
        on large datastores.

        Args:
            datastore_name: Name of the VMFS datastore to unmap.
        """
        logger.info("unmap_vmfs_datastore", datastore_name=datastore_name)

        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        ds_info = ds_obj.info
        if not isinstance(ds_info, vim.host.VmfsDatastoreInfo):
            return {"status": "error", "error": f"Datastore '{datastore_name}' is not a VMFS datastore"}

        vmfs = getattr(ds_info, "vmfs", None)
        if vmfs is None:
            return {"status": "error", "error": "Could not retrieve VMFS volume information"}

        vmfs_uuid = vmfs.uuid

        # Get a host that has this datastore mounted to run the unmap
        host_mounts = ds_obj.host or []
        if not host_mounts:
            return {"status": "error", "error": f"No hosts have '{datastore_name}' mounted"}

        host_ref = host_mounts[0].key
        cm = getattr(host_ref, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on the mounted host"}

        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available on the mounted host"}

        try:
            task = storage_system.UnmapVmfsVolumeEx_Task(vmfsUuid=[vmfs_uuid])
            result = wait_for_task(task)
        except AttributeError:
            # Fallback: older API uses UnmapVmfsVolume (synchronous, no task)
            try:
                storage_system.UnmapVmfsVolume(vmfsUuid=vmfs_uuid)
                result = {"status": "success"}
            except Exception as exc:
                return {"status": "error", "error": f"UNMAP operation failed: {exc}"}

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "UNMAP task failed")}

        return {
            "status": "success",
            "operation": "unmap_vmfs_datastore",
            "datastore_name": datastore_name,
            "vmfs_uuid": vmfs_uuid,
            "message": "UNMAP operation completed — dead space reclaimed from the array.",
        }

    @mcp.tool()
    @handle_tool_errors
    def list_vasa_providers() -> dict[str, Any]:
        """List VASA (vSphere APIs for Storage Awareness) storage providers registered with vCenter.

        Attempts to retrieve provider information via the vCenter storage query manager.
        Returns a best-effort list; availability depends on the vCenter version and configuration.
        """
        logger.info("list_vasa_providers")

        storage_manager = getattr(client.content, "storageQueryManager", None)
        if storage_manager is None:
            return {
                "status": "unavailable",
                "message": "storageQueryManager is not available on this vCenter — VASA provider enumeration requires vCenter 6.0+",
                "providers": [],
            }

        try:
            providers_raw = getattr(storage_manager, "storageProvider", None) or []
        except Exception as exc:
            return {
                "status": "unavailable",
                "message": f"Could not enumerate VASA providers: {exc}",
                "providers": [],
            }

        providers = []
        for p in providers_raw:
            providers.append({
                "name": getattr(p, "name", None),
                "url": getattr(p, "url", None),
                "type": getattr(p, "type", None),
                "operational_status": getattr(p, "operationalStatus", None),
                "description": getattr(p, "description", None),
            })

        return {
            "status": "success",
            "provider_count": len(providers),
            "providers": providers,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def register_vasa_provider(
        provider_url: str,
        name: str,
        username: str = "",
        password: str = "",
    ) -> dict[str, Any]:
        """Register a VASA storage provider with vCenter.

        After registration, vCenter can use the provider to expose storage
        capabilities and enable policy-based management for the backing array.

        Args:
            provider_url: HTTPS URL of the VASA provider endpoint.
            name: Display name for the provider.
            username: Optional username for provider authentication.
            password: Optional password for provider authentication.
        """
        logger.info("register_vasa_provider", provider_url=provider_url, name=name)

        storage_manager = getattr(client.content, "storageQueryManager", None)
        if storage_manager is None:
            return {
                "status": "error",
                "error": "storageQueryManager is not available — VASA provider registration requires vCenter 6.0+",
            }

        try:
            spec = vim.StorageQueryManager.StorageProviderSpec(
                name=name,
                url=provider_url,
                username=username,
                password=password,
            )
            storage_manager.RegisterStorageProvider(spec=spec)
        except AttributeError:
            return {
                "status": "error",
                "error": "VASA provider registration API is not available on this vCenter version",
            }
        except Exception as exc:
            return {"status": "error", "error": f"Failed to register VASA provider: {exc}"}

        return {
            "status": "success",
            "operation": "register_vasa_provider",
            "name": name,
            "provider_url": provider_url,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def unregister_vasa_provider(provider_name: str) -> dict[str, Any]:
        """Unregister a VASA storage provider from vCenter.

        After unregistering, vCenter will no longer receive storage capability
        information from this provider. Datastores using capabilities from this
        provider may lose their policy compliance status.

        Args:
            provider_name: Name of the VASA provider to unregister.
        """
        logger.info("unregister_vasa_provider", provider_name=provider_name)

        storage_manager = getattr(client.content, "storageQueryManager", None)
        if storage_manager is None:
            return {
                "status": "error",
                "error": "storageQueryManager is not available — VASA provider management requires vCenter 6.0+",
            }

        try:
            providers_raw = getattr(storage_manager, "storageProvider", None) or []
        except Exception as exc:
            return {"status": "error", "error": f"Could not enumerate VASA providers: {exc}"}

        target_provider = None
        for p in providers_raw:
            if getattr(p, "name", None) == provider_name:
                target_provider = p
                break

        if target_provider is None:
            return {"status": "error", "error": f"VASA provider '{provider_name}' not found"}

        try:
            storage_manager.UnregisterStorageProvider(provider=target_provider)
        except AttributeError:
            return {
                "status": "error",
                "error": "VASA provider unregistration API is not available on this vCenter version",
            }
        except Exception as exc:
            return {"status": "error", "error": f"Failed to unregister VASA provider: {exc}"}

        return {
            "status": "success",
            "operation": "unregister_vasa_provider",
            "provider_name": provider_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vvol_datastore_info(datastore_name: str) -> dict[str, Any]:
        """Get detailed information about a VVol (Virtual Volumes) datastore.

        Returns container UUID, backing storage type, protocol endpoint details,
        and provider information if available.

        Args:
            datastore_name: Name of the VVol datastore.
        """
        logger.info("get_vvol_datastore_info", datastore_name=datastore_name)

        ds_items = collect_properties(
            client,
            vim.Datastore,
            ["name", "summary.type", "summary.capacity", "summary.freeSpace", "summary.accessible", "info"],
        )
        ds_obj = None
        ds_data = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                ds_data = item
                break

        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        ds_type = ds_data.get("summary.type", "")
        if ds_type != "VVOL":
            return {
                "status": "error",
                "error": f"Datastore '{datastore_name}' is of type '{ds_type}', not VVOL",
            }

        capacity = ds_data.get("summary.capacity")
        free = ds_data.get("summary.freeSpace")

        vvol_info: dict[str, Any] = {
            "status": "success",
            "datastore_name": datastore_name,
            "type": ds_type,
            "capacity_gb": round(capacity / (1024**3), 2) if capacity else None,
            "free_gb": round(free / (1024**3), 2) if free else None,
            "accessible": ds_data.get("summary.accessible"),
        }

        ds_info = ds_data.get("info")
        if ds_info is None:
            try:
                ds_info = ds_obj.info
            except Exception:
                ds_info = None

        if ds_info is not None:
            vvol_vol = getattr(ds_info, "vvolDS", None)
            if vvol_vol is None:
                # Try alternate attribute name used in some API versions
                vvol_vol = getattr(ds_info, "vvolDatastore", None)
            if vvol_vol is not None:
                vvol_info["container_id"] = getattr(vvol_vol, "containerId", None)
                vvol_info["protocol_endpoint_type"] = getattr(vvol_vol, "protocolEndpointType", None)

                # Storage Container / VASA provider reference
                storage_array = getattr(vvol_vol, "storageArray", None)
                if storage_array is not None:
                    vvol_info["storage_array"] = {
                        "vendor": getattr(storage_array, "vendorId", None),
                        "model": getattr(storage_array, "modelId", None),
                        "name": getattr(storage_array, "name", None),
                    }

        return vvol_info

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_sioc_per_vm(
        datastore_name: str,
        enabled: bool = True,
        congestion_threshold_mode: str = "automatic",
        congestion_threshold: int = 30,
        percent_of_peak_throughput: int = 90,
    ) -> dict[str, Any]:
        """Configure Storage I/O Control (SIOC) with per-VM granularity on a datastore.

        This extends basic SIOC configuration with automatic threshold mode and
        peak-throughput percentage settings for more precise I/O prioritisation.

        Args:
            datastore_name: Name of the datastore to configure SIOC on.
            enabled: Enable or disable SIOC (default True).
            congestion_threshold_mode: Threshold mode — "automatic" uses latency-based
                detection; "manual" uses the fixed congestion_threshold value (default "automatic").
            congestion_threshold: Fixed I/O latency congestion threshold in milliseconds,
                used when congestion_threshold_mode is "manual" (default 30).
            percent_of_peak_throughput: When mode is "automatic", the percentage of peak
                throughput before SIOC kicks in (default 90, range 50–100).
        """
        logger.info(
            "configure_sioc_per_vm",
            datastore_name=datastore_name,
            enabled=enabled,
            congestion_threshold_mode=congestion_threshold_mode,
            congestion_threshold=congestion_threshold,
            percent_of_peak_throughput=percent_of_peak_throughput,
        )

        valid_modes = ("automatic", "manual")
        if congestion_threshold_mode not in valid_modes:
            return {
                "status": "error",
                "error": f"congestion_threshold_mode must be one of: {', '.join(valid_modes)}",
            }

        if congestion_threshold_mode == "manual" and not (5 <= congestion_threshold <= 100):
            return {"status": "error", "error": "congestion_threshold must be between 5 and 100 ms"}

        if not (50 <= percent_of_peak_throughput <= 100):
            return {"status": "error", "error": "percent_of_peak_throughput must be between 50 and 100"}

        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        iorm_spec = vim.StorageResourceManager.IORMConfigSpec(
            enabled=enabled,
            congestionThreshold=congestion_threshold,
        )

        # Set automatic threshold mode if requested (vSphere 6.0+ API)
        if congestion_threshold_mode == "automatic":
            try:
                iorm_spec.congestionThresholdMode = "automatic"
                iorm_spec.percentOfPeakThroughput = percent_of_peak_throughput
            except AttributeError:
                # Older API versions do not support these fields — fall back silently
                pass

        storage_rm = client.content.storageResourceManager
        task = storage_rm.ConfigureDatastoreIORM_Task(
            datastore=ds_obj,
            spec=iorm_spec,
        )
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to configure SIOC")}

        return {
            "status": "success",
            "operation": "configure_sioc_per_vm",
            "datastore_name": datastore_name,
            "enabled": enabled,
            "congestion_threshold_mode": congestion_threshold_mode,
            "congestion_threshold_ms": congestion_threshold,
            "percent_of_peak_throughput": percent_of_peak_throughput,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_nfs41_kerberos(
        host_name: str,
        datastore_name: str,
        security_type: str = "SEC_KRB5",
    ) -> dict[str, Any]:
        """Configure Kerberos authentication for an NFS 4.1 datastore on an ESXi host.

        NFS 4.1 supports Kerberos security types for stronger mutual authentication
        between the ESXi host and the NFS server. The host must already be joined
        to an Active Directory domain and have the NFS 4.1 datastore mounted.

        Args:
            host_name: Name of the ESXi host.
            datastore_name: Name of the NFS 4.1 datastore to configure.
            security_type: Kerberos security type. One of:
                "SEC_KRB5" — Kerberos authentication only (default),
                "SEC_KRB5I" — Kerberos with data integrity,
                "SEC_KRB5P" — Kerberos with privacy (encryption).
        """
        logger.info(
            "configure_nfs41_kerberos",
            host_name=host_name,
            datastore_name=datastore_name,
            security_type=security_type,
        )

        valid_security_types = ("SEC_KRB5", "SEC_KRB5I", "SEC_KRB5P")
        if security_type not in valid_security_types:
            return {
                "status": "error",
                "error": f"security_type must be one of: {', '.join(valid_security_types)}",
            }

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        storage_system = cm.storageSystem
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available"}

        # Locate the NFS volume by matching the datastore name
        file_system_vol_info = getattr(storage_system, "fileSystemVolumeInfo", None)
        if file_system_vol_info is None:
            return {"status": "error", "error": "fileSystemVolumeInfo not available on this host"}

        target_volume = None
        for mount_info in file_system_vol_info.mountInfo or []:
            vol = getattr(mount_info, "volume", None)
            if vol is None:
                continue
            if getattr(vol, "name", None) == datastore_name:
                target_volume = vol
                break

        if target_volume is None:
            return {
                "status": "error",
                "error": f"NFS volume '{datastore_name}' not found on host '{host_name}'",
            }

        if not isinstance(target_volume, vim.host.NasVolume):
            return {
                "status": "error",
                "error": f"Volume '{datastore_name}' is not an NFS volume (type: {type(target_volume).__name__})",
            }

        if getattr(target_volume, "type", "") not in ("NFS41", "NFS4.1"):
            return {
                "status": "error",
                "error": f"Volume '{datastore_name}' is NFS v3 — Kerberos is only supported on NFS 4.1",
            }

        try:
            spec = vim.host.NasVolume.Specification(
                remoteHost=target_volume.remoteHost,
                remotePath=target_volume.remotePath,
                localPath=target_volume.name,
                accessMode=getattr(target_volume, "accessMode", "readWrite"),
                type="NFS41",
                securityType=security_type,
            )
            storage_system.UpdateNasDatastore(spec=spec)
        except AttributeError:
            return {
                "status": "error",
                "error": "UpdateNasDatastore API is not available — this vCenter/ESXi version may not support NFS 4.1 Kerberos reconfiguration via this API",
            }
        except Exception as exc:
            return {"status": "error", "error": f"Failed to configure NFS 4.1 Kerberos: {exc}"}

        return {
            "status": "success",
            "operation": "configure_nfs41_kerberos",
            "host_name": host_name,
            "datastore_name": datastore_name,
            "security_type": security_type,
        }
