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
            elif isinstance(rule, vim.cluster.VmHostRuleInfo):
                rule_type = "VmHostRuleInfo"

            rule_entry: dict[str, Any] = {
                "name": rule.name,
                "enabled": rule.enabled if hasattr(rule, "enabled") else None,
                "type": rule_type,
                "mandatory": rule.mandatory if hasattr(rule, "mandatory") else None,
            }

            if rule_type == "VmHostRuleInfo":
                rule_entry["vmGroupName"] = getattr(rule, "vmGroupName", None)
                rule_entry["affineHostGroupName"] = getattr(rule, "affineHostGroupName", None)
                rule_entry["antiAffineHostGroupName"] = getattr(rule, "antiAffineHostGroupName", None)
            else:
                vm_names: list[str] = []
                if hasattr(rule, "vm") and rule.vm:
                    for vm_ref in rule.vm:
                        try:
                            vm_names.append(vm_ref.name)
                        except Exception:
                            vm_names.append(str(vm_ref))
                rule_entry["vm"] = vm_names

            rules.append(rule_entry)

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
                    "key": rec.key,
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
        shares_level: str = "normal",
        shares_value: int | None = None,
    ) -> dict[str, Any]:
        """Create a resource pool on a cluster.

        Args:
            cluster_name: Name of the cluster.
            pool_name: Name for the new resource pool.
            cpu_reservation: CPU reservation in MHz (default 0).
            cpu_limit: CPU limit in MHz (-1 for unlimited).
            memory_reservation_mb: Memory reservation in MB (default 0).
            memory_limit_mb: Memory limit in MB (-1 for unlimited).
            shares_level: Shares level for cpu and memory: 'low', 'normal', 'high', or 'custom' (default 'normal').
            shares_value: Custom shares value (required when shares_level is 'custom').
        """
        logger.info("create_resource_pool", cluster_name=cluster_name, pool_name=pool_name)

        valid_shares_levels = {"low", "normal", "high", "custom"}
        if shares_level not in valid_shares_levels:
            return {
                "status": "error",
                "error": f"Invalid shares_level '{shares_level}'. "
                f"Valid values: {', '.join(sorted(valid_shares_levels))}",
            }
        if shares_level == "custom" and shares_value is None:
            return {
                "status": "error",
                "error": "shares_value is required when shares_level is 'custom'",
            }

        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        resource_pool = cluster.resourcePool
        if resource_pool is None:
            return {"status": "error", "error": f"Resource pool not available on cluster '{cluster_name}'"}

        shares_level_enum = getattr(vim.SharesInfo.Level, shares_level)
        shares_info = vim.SharesInfo(level=shares_level_enum)
        if shares_level == "custom" and shares_value is not None:
            shares_info.shares = shares_value

        cpu_alloc = vim.ResourceAllocationInfo(
            reservation=cpu_reservation,
            limit=cpu_limit,
            expandableReservation=True,
            shares=shares_info,
        )
        mem_alloc = vim.ResourceAllocationInfo(
            reservation=memory_reservation_mb,
            limit=memory_limit_mb,
            expandableReservation=True,
            shares=vim.SharesInfo(level=shares_level_enum, shares=shares_value if shares_level == "custom" else 0),
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
        cpu_reservation: int | None = None,
        cpu_limit: int | None = None,
        memory_reservation_mb: int | None = None,
        memory_limit_mb: int | None = None,
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

        current_config = pool_obj.config
        cpu_alloc = vim.ResourceAllocationInfo(
            reservation=cpu_reservation if cpu_reservation is not None else current_config.cpuAllocation.reservation,
            limit=cpu_limit if cpu_limit is not None else current_config.cpuAllocation.limit,
            expandableReservation=current_config.cpuAllocation.expandableReservation,
            shares=current_config.cpuAllocation.shares,
        )
        mem_alloc = vim.ResourceAllocationInfo(
            reservation=(
                memory_reservation_mb
                if memory_reservation_mb is not None
                else current_config.memoryAllocation.reservation
            ),
            limit=memory_limit_mb if memory_limit_mb is not None else current_config.memoryAllocation.limit,
            expandableReservation=current_config.memoryAllocation.expandableReservation,
            shares=current_config.memoryAllocation.shares,
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

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_cluster_ha(
        cluster_name: str,
        enabled: bool,
        admission_control_enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Configure High Availability (HA) settings on a cluster.

        Args:
            cluster_name: Name of the cluster to configure.
            enabled: Whether to enable HA.
            admission_control_enabled: Whether to enable admission control (optional).
        """
        logger.info("configure_cluster_ha", cluster_name=cluster_name, enabled=enabled)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        das_config = vim.cluster.DasConfigInfo(enabled=enabled)
        if admission_control_enabled is not None:
            das_config.admissionControlEnabled = admission_control_enabled

        spec = vim.cluster.ConfigSpecEx(dasConfig=das_config)
        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)
        result["operation"] = "configure_cluster_ha"
        result["cluster_name"] = cluster_name
        result["enabled"] = enabled
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_cluster_drs(
        cluster_name: str,
        enabled: bool,
        automation_level: str | None = None,
        vmotion_rate: int | None = None,
    ) -> dict[str, Any]:
        """Configure Distributed Resource Scheduler (DRS) settings on a cluster.

        Args:
            cluster_name: Name of the cluster to configure.
            enabled: Whether to enable DRS.
            automation_level: Automation level: 'manual', 'partiallyAutomated', or 'fullyAutomated' (optional).
            vmotion_rate: DRS aggressiveness from 1 (conservative) to 5 (aggressive) (optional).
        """
        logger.info("configure_cluster_drs", cluster_name=cluster_name, enabled=enabled)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        if vmotion_rate is not None and (vmotion_rate < 1 or vmotion_rate > 5):
            return {
                "status": "error",
                "error": f"vmotion_rate must be between 1 and 5, got {vmotion_rate}",
            }

        automation_level_map = {
            "manual": vim.cluster.DrsConfigInfo.DrsBehavior.manual,
            "partiallyAutomated": vim.cluster.DrsConfigInfo.DrsBehavior.partiallyAutomated,
            "fullyAutomated": vim.cluster.DrsConfigInfo.DrsBehavior.fullyAutomated,
        }

        drs_config = vim.cluster.DrsConfigInfo(enabled=enabled)
        if automation_level is not None:
            mapped = automation_level_map.get(automation_level)
            if mapped is None:
                return {
                    "status": "error",
                    "error": f"Unknown automation_level '{automation_level}'. "
                    f"Valid values: {', '.join(automation_level_map.keys())}",
                }
            drs_config.defaultVmBehavior = mapped

        if vmotion_rate is not None:
            drs_config.vmotionRate = vmotion_rate

        spec = vim.cluster.ConfigSpecEx(drsConfig=drs_config)
        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)
        result["operation"] = "configure_cluster_drs"
        result["cluster_name"] = cluster_name
        result["enabled"] = enabled
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_drs_rule(
        cluster_name: str,
        rule_name: str,
        vm_names: list[str],
        affinity: bool = True,
        mandatory: bool = False,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a DRS affinity or anti-affinity rule for VMs in a cluster.

        Args:
            cluster_name: Name of the cluster.
            rule_name: Name for the new DRS rule.
            vm_names: List of VM names to include in the rule.
            affinity: If True, create an affinity rule; if False, create an anti-affinity rule (default True).
            mandatory: Whether the rule is mandatory (default False).
            enabled: Whether the rule is enabled (default True).
        """
        logger.info("create_drs_rule", cluster_name=cluster_name, rule_name=rule_name, affinity=affinity)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        all_vms = collect_properties(client, vim.VirtualMachine, ["name"])
        vm_refs = []
        for vm_name in vm_names:
            found = None
            for item in all_vms:
                if item.get("name") == vm_name:
                    found = item["_obj"]
                    break
            if found is None:
                return {"status": "error", "error": f"VM '{vm_name}' not found"}
            vm_refs.append(found)

        if affinity:
            rule = vim.cluster.AffinityRuleSpec(
                name=rule_name, enabled=enabled, mandatory=mandatory, vm=vm_refs,
            )
        else:
            rule = vim.cluster.AntiAffinityRuleSpec(
                name=rule_name, enabled=enabled, mandatory=mandatory, vm=vm_refs,
            )

        rule_spec = vim.cluster.RuleSpec(info=rule, operation="add")
        spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])
        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)
        result["operation"] = "create_drs_rule"
        result["cluster_name"] = cluster_name
        result["rule_name"] = rule_name
        result["affinity"] = affinity
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_drs_rule(
        cluster_name: str,
        rule_name: str,
    ) -> dict[str, Any]:
        """Delete a DRS rule from a cluster.

        Args:
            cluster_name: Name of the cluster.
            rule_name: Name of the DRS rule to delete.
        """
        logger.info("delete_drs_rule", cluster_name=cluster_name, rule_name=rule_name)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        config = getattr(cluster, "configuration", None)
        rules_raw = (config.rule if config else None) or []
        rule_to_delete = None
        for rule in rules_raw:
            if rule.name == rule_name:
                rule_to_delete = rule
                break
        if rule_to_delete is None:
            return {"status": "error", "error": f"DRS rule '{rule_name}' not found in cluster '{cluster_name}'"}

        rule_spec = vim.cluster.RuleSpec(removeKey=rule_to_delete.key, operation="remove")
        spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])
        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)
        result["operation"] = "delete_drs_rule"
        result["cluster_name"] = cluster_name
        result["rule_name"] = rule_name
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def apply_drs_recommendation(
        cluster_name: str,
        recommendation_key: str,
    ) -> dict[str, Any]:
        """Apply a specific DRS recommendation on a cluster.

        Args:
            cluster_name: Name of the cluster.
            recommendation_key: The key of the DRS recommendation to apply (from get_cluster_drs_recommendations).
        """
        logger.info("apply_drs_recommendation", cluster_name=cluster_name, recommendation_key=recommendation_key)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        cluster.ApplyRecommendation(key=recommendation_key)
        return {
            "status": "success",
            "operation": "apply_drs_recommendation",
            "cluster_name": cluster_name,
            "recommendation_key": recommendation_key,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_cluster(
        datacenter_name: str,
        cluster_name: str,
    ) -> dict[str, Any]:
        """Create a new cluster in a datacenter.

        Args:
            datacenter_name: Name of the datacenter in which to create the cluster.
            cluster_name: Name for the new cluster.
        """
        logger.info("create_cluster", datacenter_name=datacenter_name, cluster_name=cluster_name)
        dcs = collect_properties(client, vim.Datacenter, ["name"])
        dc_obj = None
        for item in dcs:
            if item.get("name") == datacenter_name:
                dc_obj = item["_obj"]
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        host_folder = dc_obj.hostFolder
        host_folder.CreateClusterEx(name=cluster_name, spec=vim.cluster.ConfigSpecEx())
        return {
            "status": "success",
            "operation": "create_cluster",
            "datacenter_name": datacenter_name,
            "cluster_name": cluster_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_cluster(
        cluster_name: str,
    ) -> dict[str, Any]:
        """Delete a cluster from vCenter. This is a destructive operation.

        Args:
            cluster_name: Name of the cluster to delete.
        """
        logger.info("delete_cluster", cluster_name=cluster_name)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        task = cluster.Destroy_Task()
        result = wait_for_task(task)
        result["operation"] = "delete_cluster"
        result["cluster_name"] = cluster_name
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_drs_vm_group(
        cluster_name: str,
        group_name: str,
        vm_names: list[str],
    ) -> dict[str, Any]:
        """Create a DRS VM group in a cluster.

        Args:
            cluster_name: Name of the cluster.
            group_name: Name for the new VM group.
            vm_names: List of VM names to include in the group.
        """
        logger.info("create_drs_vm_group", cluster_name=cluster_name, group_name=group_name)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        all_vms = collect_properties(client, vim.VirtualMachine, ["name"])
        vm_refs = []
        for vm_name in vm_names:
            found = None
            for item in all_vms:
                if item.get("name") == vm_name:
                    found = item["_obj"]
                    break
            if found is None:
                return {"status": "error", "error": f"VM '{vm_name}' not found"}
            vm_refs.append(found)

        group = vim.cluster.VmGroup(name=group_name, vm=vm_refs)
        group_spec = vim.cluster.GroupSpec(info=group, operation="add")
        spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])
        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)
        result["operation"] = "create_drs_vm_group"
        result["cluster_name"] = cluster_name
        result["group_name"] = group_name
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_drs_host_group(
        cluster_name: str,
        group_name: str,
        host_names: list[str],
    ) -> dict[str, Any]:
        """Create a DRS host group in a cluster.

        Args:
            cluster_name: Name of the cluster.
            group_name: Name for the new host group.
            host_names: List of host names to include in the group.
        """
        logger.info("create_drs_host_group", cluster_name=cluster_name, group_name=group_name)
        cluster = _find_cluster_by_name(client, cluster_name)
        if cluster is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        all_hosts = collect_properties(client, vim.HostSystem, ["name"])
        host_refs = []
        for host_name in host_names:
            found = None
            for item in all_hosts:
                if item.get("name") == host_name:
                    found = item["_obj"]
                    break
            if found is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}
            host_refs.append(found)

        group = vim.cluster.HostGroup(name=group_name, host=host_refs)
        group_spec = vim.cluster.GroupSpec(info=group, operation="add")
        spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])
        task = cluster.ReconfigureComputeResource_Task(spec=spec, modify=True)
        result = wait_for_task(task)
        result["operation"] = "create_drs_host_group"
        result["cluster_name"] = cluster_name
        result["group_name"] = group_name
        return result
