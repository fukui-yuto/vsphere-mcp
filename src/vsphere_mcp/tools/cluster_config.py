from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
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


def register_cluster_config_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_cluster_ha_config(
        cluster_name: str,
    ) -> dict[str, Any]:
        """Get HA (High Availability) configuration for a cluster."""
        logger.info("get_cluster_ha_config", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config = getattr(cluster, "configuration", None)
        if config is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' configuration not available"}
        das_config = config.dasConfig
        if das_config is None:
            return {"status": "error", "error": "HA configuration not available on this cluster"}

        ha_config: dict[str, Any] = {
            "cluster_name": cluster_name,
            "enabled": das_config.enabled,
            "vmMonitoring": das_config.vmMonitoring,
            "hostMonitoring": das_config.hostMonitoring,
        }

        if hasattr(das_config, "admissionControlEnabled"):
            ha_config["admissionControlEnabled"] = das_config.admissionControlEnabled

        if hasattr(das_config, "admissionControlPolicy") and das_config.admissionControlPolicy:
            policy = das_config.admissionControlPolicy
            ha_config["admissionControlPolicy"] = type(policy).__name__
            if hasattr(policy, "failoverLevel"):
                ha_config["failoverLevel"] = policy.failoverLevel

        if hasattr(das_config, "defaultVmSettings") and das_config.defaultVmSettings:
            vm_settings = das_config.defaultVmSettings
            ha_config["defaultVmSettings"] = {
                "restartPriority": (vm_settings.restartPriority if hasattr(vm_settings, "restartPriority") else None),
                "isolationResponse": (
                    vm_settings.isolationResponse if hasattr(vm_settings, "isolationResponse") else None
                ),
            }

        return ha_config

    @mcp.tool()
    @handle_tool_errors
    def get_cluster_drs_config(
        cluster_name: str,
    ) -> dict[str, Any]:
        """Get DRS (Distributed Resource Scheduler) configuration for a cluster."""
        logger.info("get_cluster_drs_config", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config = getattr(cluster, "configuration", None)
        if config is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' configuration not available"}
        drs_config = config.drsConfig
        if drs_config is None:
            return {"status": "error", "error": "DRS configuration not available on this cluster"}

        return {
            "cluster_name": cluster_name,
            "enabled": drs_config.enabled,
            "defaultVmBehavior": str(drs_config.defaultVmBehavior),
            "vmotionRate": drs_config.vmotionRate,
            "enableVmBehaviorOverrides": drs_config.enableVmBehaviorOverrides,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_drs_rules(
        cluster_name: str,
    ) -> dict[str, Any]:
        """List DRS affinity/anti-affinity rules for a cluster."""
        logger.info("list_drs_rules", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config = getattr(cluster, "configuration", None)
        rules_raw = (config.rule if config else None) or []

        rules: list[dict[str, Any]] = []
        for rule in rules_raw:
            rule_type = "Unknown"
            if isinstance(rule, vim.cluster.AffinityRuleSpec):
                rule_type = "AffinityRuleSpec"
            elif isinstance(rule, vim.cluster.AntiAffinityRuleSpec):
                rule_type = "AntiAffinityRuleSpec"

            vm_names: list[str] = []
            if hasattr(rule, "vm") and rule.vm:
                for vm_ref in rule.vm:
                    try:
                        vm_names.append(vm_ref.name)
                    except Exception:
                        vm_names.append(str(vm_ref))

            rules.append(
                {
                    "name": rule.name,
                    "enabled": rule.enabled if hasattr(rule, "enabled") else None,
                    "type": rule_type,
                    "mandatory": rule.mandatory if hasattr(rule, "mandatory") else None,
                    "vm": vm_names,
                }
            )

        return {
            "cluster_name": cluster_name,
            "total": len(rules),
            "rules": rules,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_cluster_drs_recommendations(
        cluster_name: str,
    ) -> dict[str, Any]:
        """Get current DRS recommendations for a cluster."""
        logger.info("get_cluster_drs_recommendations", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        recommendations_raw = cluster.recommendation or []

        recommendations: list[dict[str, Any]] = []
        for rec in recommendations_raw:
            actions: list[dict[str, Any]] = []
            for action in rec.action or []:
                action_data: dict[str, Any] = {"type": type(action).__name__}
                if hasattr(action, "target") and action.target:
                    try:
                        action_data["target"] = action.target.name
                    except Exception:
                        action_data["target"] = str(action.target)
                actions.append(action_data)

            recommendations.append(
                {
                    "reason": rec.reason,
                    "reasonText": rec.reasonText if hasattr(rec, "reasonText") else None,
                    "target": rec.target.name if hasattr(rec, "target") and rec.target else None,
                    "actions": actions,
                }
            )

        return {
            "cluster_name": cluster_name,
            "total": len(recommendations),
            "recommendations": recommendations,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_resource_pool(
        cluster_name: str,
        pool_name: str,
        cpu_reservation: int = 0,
        cpu_limit: int = -1,
        memory_reservation_mb: int = 0,
        memory_limit_mb: int = -1,
    ) -> dict[str, Any]:
        """Create a resource pool on a cluster.

        Args:
            cluster_name: Name of the cluster.
            pool_name: Name for the new resource pool.
            cpu_reservation: CPU reservation in MHz (default 0).
            cpu_limit: CPU limit in MHz (-1 for unlimited).
            memory_reservation_mb: Memory reservation in MB (default 0).
            memory_limit_mb: Memory limit in MB (-1 for unlimited).
        """
        logger.info("create_resource_pool", cluster_name=cluster_name, pool_name=pool_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        resource_pool = cluster.resourcePool
        if resource_pool is None:
            return {"status": "error", "error": f"Resource pool not available on cluster '{cluster_name}'"}

        cpu_alloc = vim.ResourceAllocationInfo(
            reservation=cpu_reservation,
            limit=cpu_limit,
            expandableReservation=True,
            shares=vim.SharesInfo(level=vim.SharesInfo.Level.normal),
        )
        mem_alloc = vim.ResourceAllocationInfo(
            reservation=memory_reservation_mb,
            limit=memory_limit_mb,
            expandableReservation=True,
            shares=vim.SharesInfo(level=vim.SharesInfo.Level.normal),
        )
        spec = vim.ResourceConfigSpec(
            cpuAllocation=cpu_alloc,
            memoryAllocation=mem_alloc,
        )

        resource_pool.CreateResourcePool(name=pool_name, spec=spec)

        return {
            "status": "success",
            "operation": "create_resource_pool",
            "cluster_name": cluster_name,
            "pool_name": pool_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def update_resource_pool(
        pool_name: str,
        cpu_reservation: int = 0,
        cpu_limit: int = -1,
        memory_reservation_mb: int = 0,
        memory_limit_mb: int = -1,
    ) -> dict[str, Any]:
        """Update an existing resource pool configuration.

        Args:
            pool_name: Name of the resource pool to update.
            cpu_reservation: CPU reservation in MHz (default 0).
            cpu_limit: CPU limit in MHz (-1 for unlimited).
            memory_reservation_mb: Memory reservation in MB (default 0).
            memory_limit_mb: Memory limit in MB (-1 for unlimited).
        """
        logger.info("update_resource_pool", pool_name=pool_name)

        items = collect_properties(client, vim.ResourcePool, ["name"])
        pool_obj = None
        for item in items:
            if item.get("name") == pool_name:
                pool_obj = item["_obj"]
                break
        if pool_obj is None:
            return {"status": "error", "error": f"Resource pool '{pool_name}' not found"}

        cpu_alloc = vim.ResourceAllocationInfo(
            reservation=cpu_reservation,
            limit=cpu_limit,
            expandableReservation=True,
            shares=vim.SharesInfo(level=vim.SharesInfo.Level.normal),
        )
        mem_alloc = vim.ResourceAllocationInfo(
            reservation=memory_reservation_mb,
            limit=memory_limit_mb,
            expandableReservation=True,
            shares=vim.SharesInfo(level=vim.SharesInfo.Level.normal),
        )
        config = vim.ResourceConfigSpec(
            cpuAllocation=cpu_alloc,
            memoryAllocation=mem_alloc,
        )

        pool_obj.UpdateConfig(name=pool_name, config=config)

        return {
            "status": "success",
            "operation": "update_resource_pool",
            "pool_name": pool_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_resource_pool(
        pool_name: str,
    ) -> dict[str, Any]:
        """Delete a resource pool.

        Args:
            pool_name: Name of the resource pool to delete.
        """
        logger.info("delete_resource_pool", pool_name=pool_name)

        items = collect_properties(client, vim.ResourcePool, ["name"])
        pool_obj = None
        for item in items:
            if item.get("name") == pool_name:
                pool_obj = item["_obj"]
                break
        if pool_obj is None:
            return {"status": "error", "error": f"Resource pool '{pool_name}' not found"}

        task = pool_obj.Destroy_Task()
        result = wait_for_task(task)
        result["operation"] = "delete_resource_pool"
        result["pool_name"] = pool_name
        return result

    @mcp.tool()
    @handle_tool_errors
    def list_cluster_host_vm_groups(
        cluster_name: str,
    ) -> dict[str, Any]:
        """List DRS host groups and VM groups for a cluster."""
        logger.info("list_cluster_host_vm_groups", cluster_name=cluster_name)

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config_ex = getattr(cluster, "configurationEx", None)
        config = config_ex if config_ex is not None else getattr(cluster, "configuration", None)
        groups_raw = (getattr(config, "group", None) if config else None) or []

        host_groups: list[dict[str, Any]] = []
        vm_groups: list[dict[str, Any]] = []

        for group in groups_raw:
            if isinstance(group, vim.cluster.HostGroup):
                host_names: list[str] = []
                for host_ref in group.host or []:
                    try:
                        host_names.append(host_ref.name)
                    except Exception:
                        host_names.append(str(host_ref))
                host_groups.append(
                    {
                        "name": group.name,
                        "hosts": host_names,
                    }
                )
            elif isinstance(group, vim.cluster.VmGroup):
                vm_names: list[str] = []
                for vm_ref in group.vm or []:
                    try:
                        vm_names.append(vm_ref.name)
                    except Exception:
                        vm_names.append(str(vm_ref))
                vm_groups.append(
                    {
                        "name": group.name,
                        "vms": vm_names,
                    }
                )

        return {
            "cluster_name": cluster_name,
            "host_groups": host_groups,
            "vm_groups": vm_groups,
            "total_host_groups": len(host_groups),
            "total_vm_groups": len(vm_groups),
        }
