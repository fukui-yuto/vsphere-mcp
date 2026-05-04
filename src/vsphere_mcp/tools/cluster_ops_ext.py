from __future__ import annotations

from typing import Any

import requests
import urllib3

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _find_cluster(client: VSphereClient, cluster_name: str) -> vim.ClusterComputeResource | None:
    """Find a cluster by name using PropertyCollector."""
    items = collect_properties(client, vim.ClusterComputeResource, ["name"])
    for item in items:
        if item.get("name") == cluster_name:
            return item["_obj"]
    return None


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


def register_cluster_ops_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_drs_vm_override(
        cluster_name: str,
        vm_name: str,
        behavior: str = "fullyAutomated",
    ) -> dict[str, Any]:
        """Set a per-VM DRS automation level override within a cluster.

        Args:
            cluster_name: Name of the target cluster.
            vm_name: Name of the VM to configure.
            behavior: DRS behavior — 'fullyAutomated', 'partiallyAutomated', or 'manual'.
        """
        logger.info("set_drs_vm_override", cluster_name=cluster_name, vm_name=vm_name, behavior=behavior)

        valid_behaviors = {"fullyAutomated", "partiallyAutomated", "manual"}
        if behavior not in valid_behaviors:
            return {"status": "error", "error": f"Invalid behavior '{behavior}'. Must be one of {sorted(valid_behaviors)}"}

        cluster = _find_cluster(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        vm_data = find_vm_with_props(client, vm_name)
        if vm_data is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_ref = vm_data["_obj"]

        behavior_map = {
            "fullyAutomated": vim.cluster.DrsConfigInfo.DrsBehavior.fullyAutomated,
            "partiallyAutomated": vim.cluster.DrsConfigInfo.DrsBehavior.partiallyAutomated,
            "manual": vim.cluster.DrsConfigInfo.DrsBehavior.manual,
        }

        drs_vm_config = vim.cluster.DrsVmConfigInfo()
        drs_vm_config.key = vm_ref
        drs_vm_config.enabled = True
        drs_vm_config.behavior = behavior_map[behavior]

        drs_vm_config_spec = vim.cluster.DrsVmConfigSpec()
        drs_vm_config_spec.operation = vim.option.ArrayUpdateSpec.Operation.edit
        drs_vm_config_spec.info = drs_vm_config

        spec = vim.cluster.ConfigSpecEx()
        spec.drsVmConfigSpec = [drs_vm_config_spec]

        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)

        if result["status"] != "success":
            return result

        return {
            "status": "success",
            "operation": "set_drs_vm_override",
            "cluster_name": cluster_name,
            "vm_name": vm_name,
            "behavior": behavior,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_drs_vm_overrides(cluster_name: str) -> dict[str, Any]:
        """List all per-VM DRS automation level overrides configured in a cluster.

        Args:
            cluster_name: Name of the cluster to inspect.
        """
        logger.info("list_drs_vm_overrides", cluster_name=cluster_name)

        cluster = _find_cluster(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config = getattr(cluster, "configuration", None)
        if config is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' configuration not available"}

        drs_vm_configs = getattr(config, "drsVmConfig", None) or []
        overrides: list[dict[str, Any]] = []
        for entry in drs_vm_configs:
            vm_ref = getattr(entry, "key", None)
            vm_name = getattr(vm_ref, "name", None) if vm_ref else None
            overrides.append({
                "vm_name": vm_name,
                "enabled": getattr(entry, "enabled", None),
                "behavior": str(val) if (val := getattr(entry, "behavior", None)) is not None else None,
            })

        return {
            "status": "success",
            "cluster_name": cluster_name,
            "total": len(overrides),
            "overrides": overrides,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_ha_vm_override(
        cluster_name: str,
        vm_name: str,
        restart_priority: str = "medium",
        isolation_response: str = "clusterDefault",
    ) -> dict[str, Any]:
        """Set per-VM HA restart priority and host isolation response overrides.

        Args:
            cluster_name: Name of the target cluster.
            vm_name: Name of the VM to configure.
            restart_priority: HA restart priority — 'disabled', 'lowest', 'low', 'medium', 'high', 'highest', or 'clusterRestartPriority'.
            isolation_response: HA isolation response — 'none', 'powerOff', 'shutdown', or 'clusterDefault'.
        """
        logger.info(
            "set_ha_vm_override",
            cluster_name=cluster_name,
            vm_name=vm_name,
            restart_priority=restart_priority,
            isolation_response=isolation_response,
        )

        cluster = _find_cluster(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        vm_data = find_vm_with_props(client, vm_name)
        if vm_data is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_ref = vm_data["_obj"]

        das_vm_settings = vim.cluster.DasVmSettings()
        das_vm_settings.restartPriority = restart_priority
        das_vm_settings.isolationResponse = isolation_response

        das_vm_config = vim.cluster.DasVmConfigInfo()
        das_vm_config.key = vm_ref
        das_vm_config.dasSettings = das_vm_settings

        das_vm_config_spec = vim.cluster.DasVmConfigSpec()
        das_vm_config_spec.operation = vim.option.ArrayUpdateSpec.Operation.edit
        das_vm_config_spec.info = das_vm_config

        spec = vim.cluster.ConfigSpecEx()
        spec.dasVmConfigSpec = [das_vm_config_spec]

        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)

        if result["status"] != "success":
            return result

        return {
            "status": "success",
            "operation": "set_ha_vm_override",
            "cluster_name": cluster_name,
            "vm_name": vm_name,
            "restart_priority": restart_priority,
            "isolation_response": isolation_response,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_ha_vm_overrides(cluster_name: str) -> dict[str, Any]:
        """List all per-VM HA restart priority and isolation response overrides in a cluster.

        Args:
            cluster_name: Name of the cluster to inspect.
        """
        logger.info("list_ha_vm_overrides", cluster_name=cluster_name)

        cluster = _find_cluster(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config = getattr(cluster, "configuration", None)
        if config is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' configuration not available"}

        das_vm_configs = getattr(config, "dasVmConfig", None) or []
        overrides: list[dict[str, Any]] = []
        for entry in das_vm_configs:
            vm_ref = getattr(entry, "key", None)
            vm_name = getattr(vm_ref, "name", None) if vm_ref else None
            das_settings = getattr(entry, "dasSettings", None)
            overrides.append({
                "vm_name": vm_name,
                "restart_priority": (str(val) if (val := getattr(das_settings, "restartPriority", None)) is not None else None) if das_settings else None,
                "isolation_response": (str(val) if (val := getattr(das_settings, "isolationResponse", None)) is not None else None) if das_settings else None,
                "vm_monitoring": (str(val) if (val := getattr(das_settings, "vmMonitoring", None)) is not None else None) if das_settings else None,
            })

        return {
            "status": "success",
            "cluster_name": cluster_name,
            "total": len(overrides),
            "overrides": overrides,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_ha_heartbeat_datastores(
        cluster_name: str,
        datastore_names: list[str],
        policy: str = "allFeasibleDsWithUserPreference",
    ) -> dict[str, Any]:
        """Configure the HA heartbeat datastore selection policy and preferred datastores.

        Args:
            cluster_name: Name of the target cluster.
            datastore_names: List of datastore names to use as heartbeat datastores.
            policy: Heartbeat datastore selection policy — 'allFeasibleDs', 'userSelectedDs', or 'allFeasibleDsWithUserPreference'.
        """
        logger.info(
            "configure_ha_heartbeat_datastores",
            cluster_name=cluster_name,
            datastore_names=datastore_names,
            policy=policy,
        )

        valid_policies = {"allFeasibleDs", "userSelectedDs", "allFeasibleDsWithUserPreference"}
        if policy not in valid_policies:
            return {"status": "error", "error": f"Invalid policy '{policy}'. Must be one of {sorted(valid_policies)}"}

        cluster = _find_cluster(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        ds_items = collect_properties(client, vim.Datastore, ["name"])
        name_to_ds: dict[str, Any] = {item["name"]: item["_obj"] for item in ds_items if "name" in item}

        ds_refs: list[Any] = []
        not_found: list[str] = []
        for ds_name in datastore_names:
            if ds_name in name_to_ds:
                ds_refs.append(name_to_ds[ds_name])
            else:
                not_found.append(ds_name)

        if not_found:
            return {"status": "error", "error": f"Datastores not found: {not_found}"}

        das_config = vim.cluster.DasConfigInfo()
        das_config.hBDatastoreCandidatePolicy = policy
        das_config.heartbeatDatastore = ds_refs

        spec = vim.cluster.ConfigSpecEx()
        spec.dasConfig = das_config

        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)

        if result["status"] != "success":
            return result

        return {
            "status": "success",
            "operation": "configure_ha_heartbeat_datastores",
            "cluster_name": cluster_name,
            "policy": policy,
            "datastores_configured": datastore_names,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcha_config() -> dict[str, Any]:
        """Get the current vCenter High Availability (VCHA) cluster configuration."""
        logger.info("get_vcha_config")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/vcenter/vcha/cluster")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        return {"status": "success", "vcha_config": data}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_vcha(
        witness_placement: dict[str, Any],
        passive_placement: dict[str, Any],
    ) -> dict[str, Any]:
        """Deploy and configure a vCenter High Availability (VCHA) cluster.

        Args:
            witness_placement: Placement spec for the witness node (host, datastore, folder, network, etc.).
            passive_placement: Placement spec for the passive node (host, datastore, folder, network, etc.).
        """
        logger.info("configure_vcha")
        session, base_url = _get_rest_session(client)

        body = {
            "witness_spec": {"placement": witness_placement},
            "passive_spec": {"placement": passive_placement},
        }

        resp = session.post(f"{base_url}/api/vcenter/vcha/cluster", json=body)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "configure_vcha",
            "message": "VCHA cluster configuration initiated",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcha_mode() -> dict[str, Any]:
        """Get the current operational mode of the vCenter High Availability (VCHA) cluster."""
        logger.info("get_vcha_mode")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/vcenter/vcha/cluster/mode")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        return {"status": "success", "mode": data}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_vcha_mode(mode: str = "ENABLED") -> dict[str, Any]:
        """Set the operational mode of the vCenter High Availability (VCHA) cluster.

        Args:
            mode: Target VCHA mode — 'ENABLED', 'DISABLED', or 'MAINTENANCE'.
        """
        logger.info("set_vcha_mode", mode=mode)

        valid_modes = {"ENABLED", "DISABLED", "MAINTENANCE"}
        if mode not in valid_modes:
            return {"status": "error", "error": f"Invalid mode '{mode}'. Must be one of {sorted(valid_modes)}"}

        session, base_url = _get_rest_session(client)

        body = {"mode": mode}
        resp = session.put(f"{base_url}/api/vcenter/vcha/cluster/mode", json=body)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "set_vcha_mode",
            "mode": mode,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_cluster_resource_summary(cluster_name: str) -> dict[str, Any]:
        """Get a resource usage summary (CPU and memory totals and usage) for a cluster.

        Args:
            cluster_name: Name of the cluster to query.
        """
        logger.info("get_cluster_resource_summary", cluster_name=cluster_name)

        cluster = _find_cluster(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        usage = cluster.GetResourceUsage()
        if usage is None:
            return {"status": "error", "error": f"Could not retrieve resource usage for cluster '{cluster_name}'"}

        cpu_capacity_mhz = getattr(usage, "cpuCapacityMHz", None)
        cpu_used_mhz = getattr(usage, "cpuUsedMHz", None)
        mem_capacity_mb = getattr(usage, "memCapacityMB", None)
        mem_used_mb = getattr(usage, "memUsedMB", None)
        storage_capacity_mb = getattr(usage, "storageCapacityMB", None)
        storage_used_mb = getattr(usage, "storageUsedMB", None)

        result: dict[str, Any] = {
            "status": "success",
            "cluster_name": cluster_name,
            "cpu": {
                "capacity_mhz": cpu_capacity_mhz,
                "used_mhz": cpu_used_mhz,
                "free_mhz": (cpu_capacity_mhz - cpu_used_mhz) if cpu_capacity_mhz is not None and cpu_used_mhz is not None else None,
                "usage_percent": round(cpu_used_mhz / cpu_capacity_mhz * 100, 1) if cpu_capacity_mhz and cpu_used_mhz else None,
            },
            "memory": {
                "capacity_mb": mem_capacity_mb,
                "used_mb": mem_used_mb,
                "free_mb": (mem_capacity_mb - mem_used_mb) if mem_capacity_mb is not None and mem_used_mb is not None else None,
                "usage_percent": round(mem_used_mb / mem_capacity_mb * 100, 1) if mem_capacity_mb and mem_used_mb else None,
            },
        }

        if storage_capacity_mb is not None:
            result["storage"] = {
                "capacity_mb": storage_capacity_mb,
                "used_mb": storage_used_mb,
                "free_mb": (storage_capacity_mb - storage_used_mb) if storage_used_mb is not None else None,
                "usage_percent": round(storage_used_mb / storage_capacity_mb * 100, 1) if storage_capacity_mb and storage_used_mb else None,
            }

        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_storage_drs_vm_override(
        pod_name: str,
        vm_name: str,
        enabled: bool = True,
        behavior: str = "automated",
    ) -> dict[str, Any]:
        """Set a per-VM Storage DRS (SDRS) override for a datastore cluster (storage pod).

        Args:
            pod_name: Name of the storage pod (datastore cluster).
            vm_name: Name of the VM to configure.
            enabled: Whether SDRS is enabled for this VM.
            behavior: SDRS behavior — 'automated' or 'manual'.
        """
        logger.info(
            "set_storage_drs_vm_override",
            pod_name=pod_name,
            vm_name=vm_name,
            enabled=enabled,
            behavior=behavior,
        )

        valid_behaviors = {"automated", "manual"}
        if behavior not in valid_behaviors:
            return {"status": "error", "error": f"Invalid behavior '{behavior}'. Must be one of {sorted(valid_behaviors)}"}

        pod_items = collect_properties(client, vim.StoragePod, ["name"])
        storage_pod = None
        for item in pod_items:
            if item.get("name") == pod_name:
                storage_pod = item["_obj"]
                break

        if storage_pod is None:
            return {"status": "error", "error": f"Storage pod '{pod_name}' not found"}

        vm_data = find_vm_with_props(client, vm_name)
        if vm_data is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_ref = vm_data["_obj"]

        vm_override = vim.StorageDrsVmConfigInfo()
        vm_override.vm = vm_ref
        vm_override.enabled = enabled
        vm_override.behavior = behavior

        vm_override_spec = vim.StorageDrsVmConfigSpec()
        vm_override_spec.operation = vim.option.ArrayUpdateSpec.Operation.edit
        vm_override_spec.info = vm_override

        pod_config_spec = vim.StorageDrsPodConfigSpec()
        pod_config_spec.vmConfigSpec = [vm_override_spec]

        spec = vim.StorageDrsConfigSpec()
        spec.podConfigSpec = pod_config_spec

        task = storage_pod.ReconfigureStoragePod_Task(spec=spec, modify=True)
        result = wait_for_task(task)

        if result["status"] != "success":
            return result

        return {
            "status": "success",
            "operation": "set_storage_drs_vm_override",
            "pod_name": pod_name,
            "vm_name": vm_name,
            "enabled": enabled,
            "behavior": behavior,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_storage_drs_vm_overrides(pod_name: str) -> dict[str, Any]:
        """List all per-VM Storage DRS overrides configured in a datastore cluster (storage pod).

        Args:
            pod_name: Name of the storage pod (datastore cluster) to inspect.
        """
        logger.info("list_storage_drs_vm_overrides", pod_name=pod_name)

        pod_items = collect_properties(client, vim.StoragePod, ["name"])
        storage_pod = None
        for item in pod_items:
            if item.get("name") == pod_name:
                storage_pod = item["_obj"]
                break

        if storage_pod is None:
            return {"status": "error", "error": f"Storage pod '{pod_name}' not found"}

        pod_config = getattr(storage_pod, "podStorageDrsEntry", None)
        if pod_config is None:
            return {
                "status": "success",
                "pod_name": pod_name,
                "total": 0,
                "overrides": [],
                "message": "No SDRS configuration available for this storage pod",
            }

        sdrs_config = getattr(pod_config, "storageDrsConfig", None)
        vm_configs = getattr(sdrs_config, "vmConfig", None) or [] if sdrs_config else []

        overrides: list[dict[str, Any]] = []
        for entry in vm_configs:
            vm_ref = getattr(entry, "vm", None)
            vm_name = getattr(vm_ref, "name", None) if vm_ref else None
            overrides.append({
                "vm_name": vm_name,
                "enabled": getattr(entry, "enabled", None),
                "behavior": str(val) if (val := getattr(entry, "behavior", None)) is not None else None,
            })

        return {
            "status": "success",
            "pod_name": pod_name,
            "total": len(overrides),
            "overrides": overrides,
        }
