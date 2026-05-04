from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors
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

        das_config = cluster.configuration.dasConfig

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

        drs_config = cluster.configuration.drsConfig

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

        rules_raw = cluster.configuration.rule or []

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
