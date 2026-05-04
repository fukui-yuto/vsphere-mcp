from __future__ import annotations

from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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


def _find_cluster_moid(client: VSphereClient, cluster_name: str) -> str | None:
    """Find a cluster MOID by name using PropertyCollector."""
    from pyVmomi import vim

    items = collect_properties(client, vim.ClusterComputeResource, ["name"])
    for item in items:
        if item.get("name") == cluster_name:
            return item["_obj"]._moId
    return None


def register_tanzu_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_namespaces() -> dict[str, Any]:
        """List all vSphere Namespaces (Tanzu Kubernetes Grid namespaces)."""
        logger.info("list_namespaces")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/namespaces/instances")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()

        namespaces = [
            {
                "name": ns.get("namespace"),
                "cluster": ns.get("cluster"),
                "status": ns.get("config_status"),
            }
            for ns in data
        ]
        return {
            "total": len(namespaces),
            "namespaces": namespaces,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_namespace(namespace_name: str) -> dict[str, Any]:
        """Get detailed information about a vSphere Namespace.

        Args:
            namespace_name: Name of the namespace to retrieve.
        """
        logger.info("get_namespace", namespace_name=namespace_name)

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/namespaces/instances/{namespace_name}")
        if resp.status_code == 404:
            return {"status": "error", "error": f"Namespace '{namespace_name}' not found"}
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        result: dict[str, Any] = {
            "name": namespace_name,
            "cluster": data.get("cluster"),
            "status": data.get("config_status"),
            "description": data.get("description", ""),
        }

        resource_spec = data.get("resource_spec")
        if resource_spec:
            result["resource_quotas"] = resource_spec

        storage_specs = data.get("storage_specs")
        if storage_specs:
            result["storage_policies"] = [
                {
                    "policy": s.get("policy"),
                    "limit_mb": s.get("limit"),
                }
                for s in storage_specs
            ]

        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_namespace(
        namespace_name: str,
        cluster_name: str,
        storage_policy: str | None = None,
        cpu_limit: int | None = None,
        memory_limit_mb: int | None = None,
        storage_limit_mb: int | None = None,
    ) -> dict[str, Any]:
        """Create a vSphere Namespace on a Workload Management-enabled cluster.

        Args:
            namespace_name: Name for the new namespace.
            cluster_name: Name of the cluster to create the namespace on.
            storage_policy: Optional storage policy ID or name to associate with the namespace.
            cpu_limit: Optional CPU limit in MHz for the namespace.
            memory_limit_mb: Optional memory limit in MB for the namespace.
            storage_limit_mb: Optional storage limit in MB per storage policy.
        """
        logger.info("create_namespace", namespace_name=namespace_name, cluster_name=cluster_name)

        cluster_moid = _find_cluster_moid(client, cluster_name)
        if cluster_moid is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        session, base_url = _get_rest_session(client)

        payload: dict[str, Any] = {
            "namespace": namespace_name,
            "cluster": cluster_moid,
        }

        resource_spec: dict[str, Any] = {}
        if cpu_limit is not None:
            resource_spec["cpu_limit"] = cpu_limit
        if memory_limit_mb is not None:
            resource_spec["memory_limit"] = memory_limit_mb
        if resource_spec:
            payload["resource_spec"] = resource_spec

        if storage_policy is not None:
            storage_entry: dict[str, Any] = {"policy": storage_policy}
            if storage_limit_mb is not None:
                storage_entry["limit"] = storage_limit_mb
            payload["storage_specs"] = [storage_entry]

        resp = session.post(f"{base_url}/api/vcenter/namespaces/instances", json=payload)
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "create_namespace",
            "namespace": namespace_name,
            "cluster": cluster_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def delete_namespace(namespace_name: str) -> dict[str, Any]:
        """Delete a vSphere Namespace. This operation is irreversible and removes all workloads.

        Args:
            namespace_name: Name of the namespace to delete.
        """
        logger.info("delete_namespace", namespace_name=namespace_name)

        session, base_url = _get_rest_session(client)
        resp = session.delete(f"{base_url}/api/vcenter/namespaces/instances/{namespace_name}")
        if resp.status_code == 404:
            return {"status": "error", "error": f"Namespace '{namespace_name}' not found"}
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_namespace",
            "namespace": namespace_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_namespace(
        namespace_name: str,
        cpu_limit: int | None = None,
        memory_limit_mb: int | None = None,
        storage_limit_mb: int | None = None,
    ) -> dict[str, Any]:
        """Update resource quotas for a vSphere Namespace.

        Args:
            namespace_name: Name of the namespace to update.
            cpu_limit: New CPU limit in MHz. None to leave unchanged.
            memory_limit_mb: New memory limit in MB. None to leave unchanged.
            storage_limit_mb: New storage limit in MB. None to leave unchanged.
        """
        logger.info("update_namespace", namespace_name=namespace_name)

        session, base_url = _get_rest_session(client)

        resource_spec: dict[str, Any] = {}
        if cpu_limit is not None:
            resource_spec["cpu_limit"] = cpu_limit
        if memory_limit_mb is not None:
            resource_spec["memory_limit"] = memory_limit_mb

        payload: dict[str, Any] = {}
        if resource_spec:
            payload["resource_spec"] = resource_spec
        if storage_limit_mb is not None:
            payload["storage_specs"] = [{"limit": storage_limit_mb}]

        if not payload:
            return {"status": "error", "error": "No update parameters provided"}

        resp = session.patch(
            f"{base_url}/api/vcenter/namespaces/instances/{namespace_name}",
            json=payload,
        )
        if resp.status_code == 404:
            return {"status": "error", "error": f"Namespace '{namespace_name}' not found"}
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "update_namespace",
            "namespace": namespace_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_wcp_clusters() -> dict[str, Any]:
        """List all clusters with Workload Management (vSphere with Tanzu) enabled."""
        logger.info("list_wcp_clusters")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/namespace-management/clusters")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()

        clusters = [
            {
                "cluster": entry.get("cluster"),
                "cluster_name": entry.get("cluster_name"),
                "status": entry.get("config_status"),
                "kubernetes_status": entry.get("kubernetes_status"),
            }
            for entry in data
        ]
        return {
            "total": len(clusters),
            "clusters": clusters,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_wcp_cluster_status(cluster_name: str) -> dict[str, Any]:
        """Get Workload Management status for a specific cluster.

        Args:
            cluster_name: Name of the cluster to query.
        """
        logger.info("get_wcp_cluster_status", cluster_name=cluster_name)

        cluster_moid = _find_cluster_moid(client, cluster_name)
        if cluster_moid is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/namespace-management/clusters/{cluster_moid}")
        if resp.status_code == 404:
            return {
                "status": "error",
                "error": f"Workload Management not enabled or not found for cluster '{cluster_name}'",
            }
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

        return {
            "cluster_name": cluster_name,
            "cluster_moid": cluster_moid,
            "status": data.get("config_status"),
            "kubernetes_status": data.get("kubernetes_status"),
            "api_server_management_endpoint": data.get("api_server_management_endpoint"),
            "tls_management_endpoint_certificate": data.get("tls_management_endpoint_certificate"),
            "default_kubernetes_service_content_library": data.get(
                "default_kubernetes_service_content_library"
            ),
            "ncp_cluster_network_spec": data.get("ncp_cluster_network_spec"),
        }
