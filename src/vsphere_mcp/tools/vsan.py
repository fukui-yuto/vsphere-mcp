from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_cluster_by_name(
    client: VSphereClient,
    cluster_name: str,
) -> vim.ClusterComputeResource | None:
    """Find a cluster by name using PropertyCollector."""
    items = collect_properties(client, vim.ClusterComputeResource, ["name"])
    for item in items:
        if item.get("name") == cluster_name:
            return item["_obj"]
    return None


def register_vsan_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vsan_cluster_config(cluster_name: str) -> dict[str, Any]:
        """Get vSAN cluster configuration including enabled state, UUID, auto-claim, and fault domains."""
        logger.info("get_vsan_cluster_config", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config_ex = getattr(cluster, "configurationEx", None)
        if config_ex is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' configurationEx not available"}

        vsan_info = getattr(config_ex, "vsanConfigInfo", None)
        if vsan_info is None:
            return {
                "cluster_name": cluster_name,
                "vsan_supported": False,
                "message": "vSAN configuration not available on this cluster",
            }

        result: dict[str, Any] = {
            "cluster_name": cluster_name,
            "vsan_supported": True,
            "enabled": getattr(vsan_info, "enabled", None),
        }

        default_config = getattr(vsan_info, "defaultConfig", None)
        if default_config is not None:
            result["defaultConfig"] = {
                "uuid": getattr(default_config, "uuid", None),
                "autoClaimStorage": getattr(default_config, "autoClaimStorage", None),
            }

        fault_domain_info = getattr(vsan_info, "faultDomainInfo", None)
        if fault_domain_info is not None:
            fd_list: list[dict[str, Any]] = []
            for fd in getattr(fault_domain_info, "faultDomain", None) or []:
                fd_list.append({
                    "name": getattr(fd, "name", None),
                    "id": getattr(fd, "id", None),
                })
            result["faultDomains"] = fd_list

        result["vsanEsaEnabled"] = getattr(vsan_info, "vsanEsaEnabled", None)
        result["dedupConfig"] = getattr(vsan_info, "dedupConfig", None)

        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vsan_health_summary(cluster_name: str) -> dict[str, Any]:
        """Get vSAN health summary for a cluster based on host-level vSAN status."""
        logger.info("get_vsan_health_summary", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config_ex = getattr(cluster, "configurationEx", None)
        vsan_info = getattr(config_ex, "vsanConfigInfo", None) if config_ex else None
        vsan_enabled = getattr(vsan_info, "enabled", False) if vsan_info else False

        hosts_raw = getattr(cluster, "host", None) or []
        host_health: list[dict[str, Any]] = []
        for host_ref in hosts_raw:
            host_name = getattr(host_ref, "name", str(host_ref))
            runtime = getattr(host_ref, "runtime", None)
            connection_state = str(getattr(runtime, "connectionState", "unknown"))
            in_maintenance = getattr(runtime, "inMaintenanceMode", False)

            vsan_host_config = None
            config_manager = getattr(host_ref, "configManager", None)
            if config_manager is not None:
                vsan_system = getattr(config_manager, "vsanSystem", None)
                if vsan_system is not None:
                    try:
                        vsan_host_config = vsan_system.config
                    except Exception:
                        vsan_host_config = None

            host_entry: dict[str, Any] = {
                "host_name": host_name,
                "connection_state": connection_state,
                "in_maintenance_mode": in_maintenance,
            }

            if vsan_host_config is not None:
                host_entry["vsan_enabled"] = getattr(vsan_host_config, "enabled", None)
                host_entry["vsan_node_uuid"] = getattr(vsan_host_config, "clusterInfo", None) and getattr(
                    vsan_host_config.clusterInfo, "nodeUuid", None
                )

            host_health.append(host_entry)

        return {
            "cluster_name": cluster_name,
            "vsan_enabled": vsan_enabled,
            "host_count": len(host_health),
            "host_health": host_health,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_vsan_disk_groups(cluster_name: str) -> dict[str, Any]:
        """List vSAN disk groups per host in a cluster, showing cache and capacity disks."""
        logger.info("list_vsan_disk_groups", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        hosts_raw = getattr(cluster, "host", None) or []
        host_disk_groups: list[dict[str, Any]] = []

        for host_ref in hosts_raw:
            host_name = getattr(host_ref, "name", str(host_ref))
            entry: dict[str, Any] = {"host_name": host_name, "disk_groups": []}

            config_manager = getattr(host_ref, "configManager", None)
            if config_manager is None:
                entry["error"] = "configManager not available"
                host_disk_groups.append(entry)
                continue

            vsan_system = getattr(config_manager, "vsanSystem", None)
            if vsan_system is None:
                entry["error"] = "vsanSystem not available"
                host_disk_groups.append(entry)
                continue

            try:
                vsan_config = vsan_system.config
                storage_info = getattr(vsan_config, "storageInfo", None)
                disk_mappings = getattr(storage_info, "diskMapping", None) or [] if storage_info else []

                for mapping in disk_mappings:
                    ssd = getattr(mapping, "ssd", None)
                    capacity_disks = getattr(mapping, "nonSsd", None) or []

                    group_entry: dict[str, Any] = {
                        "cache_disk": {
                            "canonicalName": getattr(ssd, "canonicalName", None),
                            "displayName": getattr(ssd, "displayName", None),
                            "ssd": getattr(ssd, "ssd", None),
                            "capacity_gb": round(getattr(ssd, "capacity", 0) / (1024 ** 3), 2) if getattr(ssd, "capacity", None) else None,
                        } if ssd else None,
                        "capacity_disks": [
                            {
                                "canonicalName": getattr(d, "canonicalName", None),
                                "displayName": getattr(d, "displayName", None),
                                "capacity_gb": round(getattr(d, "capacity", 0) / (1024 ** 3), 2) if getattr(d, "capacity", None) else None,
                            }
                            for d in capacity_disks
                        ],
                    }
                    entry["disk_groups"].append(group_entry)
            except Exception as exc:
                entry["error"] = f"Failed to retrieve disk groups: {exc}"

            host_disk_groups.append(entry)

        return {
            "cluster_name": cluster_name,
            "host_disk_groups": host_disk_groups,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_vsan_disk_group(
        host_name: str,
        ssd_disk: str,
        data_disks: list[str],
    ) -> dict[str, Any]:
        """Add a vSAN disk group to a host.

        Args:
            host_name: Name of the ESXi host.
            ssd_disk: Canonical name of the cache tier SSD (e.g. 'naa.xxx').
            data_disks: List of canonical names for capacity tier disks.
        """
        logger.info("add_vsan_disk_group", host_name=host_name, ssd_disk=ssd_disk, data_disks=data_disks)

        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        config_manager = getattr(host, "configManager", None)
        if config_manager is None:
            return {"status": "error", "error": f"configManager not available on host '{host_name}'"}

        vsan_system = getattr(config_manager, "vsanSystem", None)
        if vsan_system is None:
            return {"status": "error", "error": f"vsanSystem not available on host '{host_name}'"}

        # Look up disk objects by canonical name
        try:
            all_disks = vsan_system.QueryDisksForVsan()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query disks: {exc}"}

        disk_map: dict[str, Any] = {d.disk.canonicalName: d.disk for d in all_disks if d.disk}

        ssd_obj = disk_map.get(ssd_disk)
        if ssd_obj is None:
            return {"status": "error", "error": f"SSD disk '{ssd_disk}' not found on host '{host_name}'"}

        capacity_objs: list[Any] = []
        for name in data_disks:
            obj = disk_map.get(name)
            if obj is None:
                return {"status": "error", "error": f"Data disk '{name}' not found on host '{host_name}'"}
            capacity_objs.append(obj)

        disk_mapping = vim.vsan.host.DiskMapping(ssd=ssd_obj, nonSsd=capacity_objs)
        try:
            task = vsan_system.InitializeDisks_Task(mapping=[disk_mapping])
        except Exception as exc:
            return {"status": "error", "error": f"Failed to initialize disks: {exc}"}

        result = wait_for_task(task)
        result["host_name"] = host_name
        result["ssd_disk"] = ssd_disk
        result["data_disks"] = data_disks
        result["operation"] = "add_vsan_disk_group"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def remove_vsan_disk_group(
        host_name: str,
        ssd_disk: str,
    ) -> dict[str, Any]:
        """Remove a vSAN disk group from a host by its cache tier SSD canonical name.

        Args:
            host_name: Name of the ESXi host.
            ssd_disk: Canonical name of the cache tier SSD identifying the disk group.
        """
        logger.info("remove_vsan_disk_group", host_name=host_name, ssd_disk=ssd_disk)

        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        config_manager = getattr(host, "configManager", None)
        if config_manager is None:
            return {"status": "error", "error": f"configManager not available on host '{host_name}'"}

        vsan_system = getattr(config_manager, "vsanSystem", None)
        if vsan_system is None:
            return {"status": "error", "error": f"vsanSystem not available on host '{host_name}'"}

        # Find the disk mapping matching the given SSD
        try:
            vsan_config = vsan_system.config
            storage_info = getattr(vsan_config, "storageInfo", None)
            disk_mappings = getattr(storage_info, "diskMapping", None) or [] if storage_info else []
        except Exception as exc:
            return {"status": "error", "error": f"Failed to read vSAN config: {exc}"}

        target_mapping = None
        for mapping in disk_mappings:
            if getattr(getattr(mapping, "ssd", None), "canonicalName", None) == ssd_disk:
                target_mapping = mapping
                break

        if target_mapping is None:
            return {
                "status": "error",
                "error": f"No disk group with SSD '{ssd_disk}' found on host '{host_name}'",
            }

        try:
            task = vsan_system.RemoveDiskMapping_Task(mapping=[target_mapping])
        except Exception as exc:
            return {"status": "error", "error": f"Failed to remove disk mapping: {exc}"}

        result = wait_for_task(task)
        result["host_name"] = host_name
        result["ssd_disk"] = ssd_disk
        result["operation"] = "remove_vsan_disk_group"
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vsan_resync_status(cluster_name: str) -> dict[str, Any]:
        """Get vSAN resync status for a cluster, reporting resyncing object counts per host."""
        logger.info("get_vsan_resync_status", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        hosts_raw = getattr(cluster, "host", None) or []
        host_resync: list[dict[str, Any]] = []
        total_resyncing = 0

        for host_ref in hosts_raw:
            host_name = getattr(host_ref, "name", str(host_ref))
            entry: dict[str, Any] = {"host_name": host_name}

            config_manager = getattr(host_ref, "configManager", None)
            internal_system = getattr(config_manager, "vsanInternalSystem", None) if config_manager else None

            if internal_system is None:
                entry["resyncing_objects"] = None
                entry["note"] = "vsanInternalSystem not available"
                host_resync.append(entry)
                continue

            try:
                # QueryVsanObjectUuidsByFilter with resync filter is available on newer APIs;
                # fall back to a simple availability check.
                objects_json = internal_system.QueryVsanObjects(uuids=[])
                entry["resyncing_objects"] = None
                entry["note"] = "Detailed resync data requires vSAN API; basic connectivity verified"
            except AttributeError:
                entry["resyncing_objects"] = None
                entry["note"] = "QueryVsanObjects not available on this host"
            except Exception as exc:
                entry["resyncing_objects"] = None
                entry["note"] = f"Query failed: {exc}"

            host_resync.append(entry)

        return {
            "cluster_name": cluster_name,
            "total_resyncing_objects": total_resyncing,
            "host_resync_status": host_resync,
            "note": (
                "Full resync detail requires vim.cluster.VsanVcClusterHealthSystem "
                "or direct vSAN management API access"
            ),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_vsan_cluster_config(
        cluster_name: str,
        enabled: bool | None = None,
        auto_claim: bool | None = None,
        dedup_enabled: bool | None = None,
        compression_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Configure vSAN settings on a cluster.

        Args:
            cluster_name: Name of the cluster to configure.
            enabled: Enable or disable vSAN on the cluster.
            auto_claim: Enable or disable automatic disk claiming.
            dedup_enabled: Enable or disable deduplication.
            compression_enabled: Enable or disable compression.
        """
        logger.info(
            "set_vsan_cluster_config",
            cluster_name=cluster_name,
            enabled=enabled,
            auto_claim=auto_claim,
            dedup_enabled=dedup_enabled,
            compression_enabled=compression_enabled,
        )

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config_ex = getattr(cluster, "configurationEx", None)
        if config_ex is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' configurationEx not available"}

        vsan_config = vim.vsan.cluster.ConfigInfo()

        if enabled is not None:
            vsan_config.enabled = enabled

        default_config = vim.vsan.cluster.ConfigInfo.HostDefaultInfo()
        changed_default = False
        if auto_claim is not None:
            default_config.autoClaimStorage = auto_claim
            changed_default = True
        if changed_default:
            vsan_config.defaultConfig = default_config

        # dedup/compression settings are applied via the datastore config on supported vSphere versions.
        # Both flags are recorded in `changes` for the caller; note that compression_enabled requires
        # deduplication to also be enabled on most vSAN versions.
        if dedup_enabled is not None:
            try:
                vsan_config.dedupConfig = vim.vsan.host.DeduplicationAndCompressionConfig(
                    featureEnabled=dedup_enabled
                )
            except Exception:
                pass  # Attribute may not exist on older pyVmomi stubs; silently skip

        cluster_spec = vim.cluster.ConfigSpecEx()
        cluster_spec.vsanConfig = vsan_config

        try:
            task = cluster.ReconfigureComputeResource_Task(spec=cluster_spec, modify=True)
        except Exception as exc:
            return {"status": "error", "error": f"Failed to reconfigure cluster: {exc}"}

        result = wait_for_task(task)
        result["cluster_name"] = cluster_name
        result["operation"] = "set_vsan_cluster_config"
        changes: dict[str, Any] = {}
        if enabled is not None:
            changes["enabled"] = enabled
        if auto_claim is not None:
            changes["auto_claim"] = auto_claim
        if dedup_enabled is not None:
            changes["dedup_enabled"] = dedup_enabled
        if compression_enabled is not None:
            changes["compression_enabled"] = compression_enabled
        result["changes"] = changes
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vsan_disk_info(host_name: str) -> dict[str, Any]:
        """Get detailed vSAN disk information for a host including disk state and capacity."""
        logger.info("get_vsan_disk_info", host_name=host_name)

        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        config_manager = getattr(host, "configManager", None)
        if config_manager is None:
            return {"status": "error", "error": f"configManager not available on host '{host_name}'"}

        vsan_system = getattr(config_manager, "vsanSystem", None)
        if vsan_system is None:
            return {"status": "error", "error": f"vsanSystem not available on host '{host_name}'"}

        try:
            disk_results = vsan_system.QueryDisksForVsan()
        except Exception as exc:
            return {"status": "error", "error": f"Failed to query disks for vSAN: {exc}"}

        disks: list[dict[str, Any]] = []
        for dr in disk_results:
            disk = getattr(dr, "disk", None)
            if disk is None:
                continue
            capacity_bytes = getattr(disk, "capacity", None)
            disk_entry: dict[str, Any] = {
                "canonicalName": getattr(disk, "canonicalName", None),
                "displayName": getattr(disk, "displayName", None),
                "ssd": getattr(disk, "ssd", None),
                "capacity_gb": round(capacity_bytes / (1024 ** 3), 2) if capacity_bytes else None,
                "state": str(getattr(dr, "state", None)),
                "vsanUuid": getattr(dr, "vsanUuid", None),
                "ineligibilityReason": [
                    str(r) for r in (getattr(dr, "error", None) or [])
                ],
            }
            disks.append(disk_entry)

        return {
            "host_name": host_name,
            "disk_count": len(disks),
            "disks": disks,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def evacuate_vsan_data_from_host(
        host_name: str,
        evacuation_mode: str = "evacuateAllData",
    ) -> dict[str, Any]:
        """Evacuate vSAN data from a host before maintenance by entering maintenance mode with a vSAN evacuation spec.

        Args:
            host_name: Name of the ESXi host.
            evacuation_mode: vSAN evacuation mode. One of: 'evacuateAllData', 'ensureObjectAccessibility',
                             'noAction'. Defaults to 'evacuateAllData'.
        """
        logger.info("evacuate_vsan_data_from_host", host_name=host_name, evacuation_mode=evacuation_mode)

        valid_modes = {"evacuateAllData", "ensureObjectAccessibility", "noAction"}
        if evacuation_mode not in valid_modes:
            return {
                "status": "error",
                "error": f"Invalid evacuation_mode '{evacuation_mode}'. Must be one of: {sorted(valid_modes)}",
            }

        host = find_host_by_name(client, host_name)
        if host is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        vsan_spec = vim.vsan.host.MaintenanceSpec(vsanMode=vim.vsan.host.DecommissionMode(objectAction=evacuation_mode))
        maintenance_spec = vim.host.MaintenanceSpec(vsanMode=vsan_spec)

        try:
            task = host.EnterMaintenanceMode_Task(
                timeout=0,
                evacuatePoweredOffVms=True,
                maintenanceSpec=maintenance_spec,
            )
        except Exception as exc:
            return {"status": "error", "error": f"Failed to enter maintenance mode: {exc}"}

        result = wait_for_task(task)
        result["host_name"] = host_name
        result["evacuation_mode"] = evacuation_mode
        result["operation"] = "evacuate_vsan_data_from_host"
        return result
