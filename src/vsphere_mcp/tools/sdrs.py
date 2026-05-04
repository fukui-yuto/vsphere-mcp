from __future__ import annotations

from typing import Any

import requests
import urllib3
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = get_logger(__name__)


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


def register_sdrs_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_sdrs_placement_recommendations(
        pod_name: str,
        vm_name: str = "",
    ) -> dict[str, Any]:
        """Get Storage DRS placement recommendations for a datastore cluster (pod).

        Args:
            pod_name: Name of the datastore cluster (StoragePod) to query.
            vm_name: Optional name of a VM to include in the recommendation spec.
        """
        logger.info("get_sdrs_placement_recommendations", pod_name=pod_name, vm_name=vm_name)

        pod_items = collect_properties(client, vim.StoragePod, ["name"])
        pod_obj = None
        for item in pod_items:
            if item.get("name") == pod_name:
                pod_obj = item["_obj"]
                break
        if pod_obj is None:
            return {"status": "error", "error": f"StoragePod (datastore cluster) '{pod_name}' not found"}

        storage_spec = vim.StorageDrs.StoragePlacementSpec()
        storage_spec.type = vim.StorageDrs.StoragePlacementSpec.PlacementType.create
        storage_spec.podSelectionSpec = vim.StorageDrs.PodSelectionSpec()
        storage_spec.podSelectionSpec.storagePod = pod_obj

        if vm_name:
            vm_items = collect_properties(client, vim.VirtualMachine, ["name"])
            for item in vm_items:
                if item.get("name") == vm_name:
                    storage_spec.vm = item["_obj"]
                    break

        result = client.content.storageResourceManager.RecommendDatastores(storageSpec=storage_spec)

        recommendations: list[dict[str, Any]] = []
        for rec in result.recommendations or []:
            actions: list[dict[str, Any]] = []
            for action in rec.action or []:
                actions.append({
                    "type": type(action).__name__,
                    "destination": str(getattr(action, "destination", None)),
                })
            recommendations.append({
                "key": rec.key,
                "type": rec.type,
                "rating": rec.rating,
                "reason": rec.reason,
                "reason_text": rec.reasonText,
                "actions": actions,
            })

        return {
            "status": "success",
            "pod_name": pod_name,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def apply_sdrs_recommendation(recommendation_key: str) -> dict[str, Any]:
        """Apply a Storage DRS recommendation by its key.

        Args:
            recommendation_key: The recommendation key returned by get_sdrs_placement_recommendations.
        """
        logger.info("apply_sdrs_recommendation", recommendation_key=recommendation_key)

        task = client.content.storageResourceManager.ApplyStorageDrsRecommendation_Task(
            key=[recommendation_key]
        )
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to apply SDRS recommendation")}

        return {
            "status": "success",
            "operation": "apply_sdrs_recommendation",
            "recommendation_key": recommendation_key,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_compute_policies() -> dict[str, Any]:
        """List all compute policies defined in vCenter."""
        logger.info("list_compute_policies")
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/vcenter/compute-policies")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()

        return {
            "status": "success",
            "total": len(data),
            "policies": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_compute_policy(
        name: str,
        description: str = "",
        capability: str = "",
    ) -> dict[str, Any]:
        """Create a new compute policy in vCenter.

        Args:
            name: Display name for the compute policy.
            description: Optional description for the policy.
            capability: Optional capability identifier (e.g. a VM-Host affinity type).
        """
        logger.info("create_compute_policy", name=name, capability=capability)
        session, base_url = _get_rest_session(client)

        body: dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        if capability:
            body["capability"] = capability

        resp = session.post(f"{base_url}/api/vcenter/compute-policies", json=body)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json() if resp.content else {}

        return {
            "status": "success",
            "operation": "create_compute_policy",
            "name": name,
            "policy_id": result.get("policy") or result.get("id"),
            "result": result,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_compute_policy(policy_id: str) -> dict[str, Any]:
        """Get details of a specific compute policy.

        Args:
            policy_id: Identifier of the compute policy to retrieve.
        """
        logger.info("get_compute_policy", policy_id=policy_id)
        session, base_url = _get_rest_session(client)

        resp = session.get(f"{base_url}/api/vcenter/compute-policies/{policy_id}")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        return {
            "status": "success",
            "policy_id": policy_id,
            "policy": data,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_compute_policy(policy_id: str) -> dict[str, Any]:
        """Delete a compute policy from vCenter.

        Args:
            policy_id: Identifier of the compute policy to delete.
        """
        logger.info("delete_compute_policy", policy_id=policy_id)
        session, base_url = _get_rest_session(client)

        resp = session.delete(f"{base_url}/api/vcenter/compute-policies/{policy_id}")
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_compute_policy",
            "policy_id": policy_id,
        }
