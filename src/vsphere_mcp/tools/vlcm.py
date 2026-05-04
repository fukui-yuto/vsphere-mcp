from __future__ import annotations

from typing import Any

import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

logger = get_logger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _get_rest_session(client: VSphereClient):
    import requests

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
    """Return the managed object ID for a cluster by name."""
    from pyVmomi import vim

    from vsphere_mcp.utils.property_collector import collect_properties

    items = collect_properties(client, vim.ClusterComputeResource, ["name"])
    for item in items:
        if item.get("name") == cluster_name:
            return item["_obj"]._moId
    return None


def _find_host_moid(client: VSphereClient, host_name: str) -> str | None:
    """Return the managed object ID for a host by name."""
    from pyVmomi import vim

    from vsphere_mcp.utils.property_collector import collect_properties

    items = collect_properties(client, vim.HostSystem, ["name"])
    for item in items:
        if item.get("name") == host_name:
            return item["_obj"]._moId
    return None


def register_vlcm_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_vlcm_images(cluster_name: str) -> dict[str, Any]:
        """List the desired software image configured for a vLCM-managed cluster.

        Args:
            cluster_name: Name of the cluster to inspect.
        """
        logger.info("list_vlcm_images", cluster_name=cluster_name)

        moid = _find_cluster_moid(client, cluster_name)
        if moid is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/esx/settings/clusters/{moid}/software")
        resp.raise_for_status()
        data = resp.json()

        base_image = data.get("base_image", {})
        components = data.get("components", {})
        add_ons = data.get("add_ons", {})

        return {
            "cluster_name": cluster_name,
            "cluster_moid": moid,
            "base_image": {
                "version": base_image.get("version"),
                "display_name": base_image.get("display_name"),
                "display_version": base_image.get("display_version"),
            },
            "components": [
                {
                    "name": name,
                    "version": info.get("version") if isinstance(info, dict) else info,
                }
                for name, info in components.items()
            ],
            "add_ons": [
                {
                    "name": name,
                    "version": info.get("version") if isinstance(info, dict) else info,
                }
                for name, info in add_ons.items()
            ],
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vlcm_cluster_compliance(cluster_name: str) -> dict[str, Any]:
        """Get the software compliance status for all hosts in a vLCM-managed cluster.

        Args:
            cluster_name: Name of the cluster to check.
        """
        logger.info("get_vlcm_cluster_compliance", cluster_name=cluster_name)

        moid = _find_cluster_moid(client, cluster_name)
        if moid is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/esx/settings/clusters/{moid}/software/compliance")
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        host_info = data.get("hosts", {})

        hosts = []
        for host_moid, host_data in host_info.items():
            hosts.append({
                "host_moid": host_moid,
                "status": host_data.get("status"),
                "notifications": host_data.get("notifications", {}),
            })

        return {
            "cluster_name": cluster_name,
            "cluster_moid": moid,
            "overall_status": status,
            "host_count": len(hosts),
            "hosts": hosts,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def apply_vlcm_image(cluster_name: str) -> dict[str, Any]:
        """Remediate a vLCM-managed cluster by applying the desired software image to all hosts.

        This will reboot hosts in the cluster as needed to apply the image.

        Args:
            cluster_name: Name of the cluster to remediate.
        """
        logger.info("apply_vlcm_image", cluster_name=cluster_name)

        moid = _find_cluster_moid(client, cluster_name)
        if moid is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.post(
            f"{base_url}/api/esx/settings/clusters/{moid}/software?action=apply",
            json={},
        )
        resp.raise_for_status()

        task_id = resp.json() if resp.content else None

        return {
            "status": "success",
            "operation": "apply_vlcm_image",
            "cluster_name": cluster_name,
            "cluster_moid": moid,
            "task_id": task_id,
            "message": "Cluster remediation task submitted. Hosts will be rebooted as required.",
        }

    @mcp.tool()
    @handle_tool_errors
    def scan_host_for_patches(host_name: str) -> dict[str, Any]:
        """Scan an ESXi host for patch compliance against the desired software image.

        Args:
            host_name: Name (FQDN or short name) of the ESXi host to scan.
        """
        logger.info("scan_host_for_patches", host_name=host_name)

        moid = _find_host_moid(client, host_name)
        if moid is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        session, base_url = _get_rest_session(client)

        # Try scan action first; fall back to reading current compliance if not supported
        scan_resp = session.post(
            f"{base_url}/api/esx/settings/hosts/{moid}/software?action=scan",
            json={},
        )
        if scan_resp.ok:
            task_id = scan_resp.json() if scan_resp.content else None
            return {
                "status": "success",
                "operation": "scan_host_for_patches",
                "host_name": host_name,
                "host_moid": moid,
                "task_id": task_id,
                "message": "Patch scan task submitted for host.",
            }

        # Fallback: retrieve compliance directly
        comp_resp = session.get(f"{base_url}/api/esx/settings/hosts/{moid}/software/compliance")
        comp_resp.raise_for_status()
        data = comp_resp.json()

        return {
            "status": "success",
            "operation": "scan_host_for_patches",
            "host_name": host_name,
            "host_moid": moid,
            "compliance_status": data.get("status"),
            "data": data,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_patch_compliance(host_name: str) -> dict[str, Any]:
        """Get the patch compliance status for an ESXi host.

        Args:
            host_name: Name (FQDN or short name) of the ESXi host.
        """
        logger.info("get_host_patch_compliance", host_name=host_name)

        moid = _find_host_moid(client, host_name)
        if moid is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/esx/settings/hosts/{moid}/software/compliance")
        resp.raise_for_status()
        data = resp.json()

        notifications = data.get("notifications", {})
        missing = notifications.get("warnings", []) + notifications.get("errors", [])

        return {
            "host_name": host_name,
            "host_moid": moid,
            "compliance_status": data.get("status"),
            "scan_time": data.get("scan_time"),
            "missing_patches": missing,
            "notifications": notifications,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def remediate_host(host_name: str) -> dict[str, Any]:
        """Apply the desired software image to an ESXi host (will reboot the host).

        Args:
            host_name: Name (FQDN or short name) of the ESXi host to remediate.
        """
        logger.info("remediate_host", host_name=host_name)

        moid = _find_host_moid(client, host_name)
        if moid is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.post(
            f"{base_url}/api/esx/settings/hosts/{moid}/software?action=apply",
            json={},
        )
        resp.raise_for_status()

        task_id = resp.json() if resp.content else None

        return {
            "status": "success",
            "operation": "remediate_host",
            "host_name": host_name,
            "host_moid": moid,
            "task_id": task_id,
            "message": "Host remediation task submitted. The host will be rebooted.",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def stage_patches_to_host(host_name: str) -> dict[str, Any]:
        """Pre-download (stage) patches to an ESXi host without applying them.

        Staging downloads patch payloads to the host so that the actual
        remediation reboot window is minimised.

        Args:
            host_name: Name (FQDN or short name) of the ESXi host.
        """
        logger.info("stage_patches_to_host", host_name=host_name)

        moid = _find_host_moid(client, host_name)
        if moid is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        session, base_url = _get_rest_session(client)
        resp = session.post(
            f"{base_url}/api/esx/settings/hosts/{moid}/software?action=stage",
            json={},
        )
        resp.raise_for_status()

        task_id = resp.json() if resp.content else None

        return {
            "status": "success",
            "operation": "stage_patches_to_host",
            "host_name": host_name,
            "host_moid": moid,
            "task_id": task_id,
            "message": "Patch staging task submitted. Patches will be downloaded to the host.",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vlcm_base_images() -> dict[str, Any]:
        """List all available ESXi base images in the vLCM software depot.

        Returns the available ESXi versions that can be used as the base image
        for vLCM-managed clusters.
        """
        logger.info("get_vlcm_base_images")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/esx/settings/depot-content/base-images")
        resp.raise_for_status()
        data = resp.json()

        # Response may be a list of base image objects or a dict with a versions key
        if isinstance(data, list):
            images = data
        else:
            images = data.get("versions", data.get("base_images", []))

        formatted = []
        for image in images:
            if isinstance(image, dict):
                formatted.append({
                    "version": image.get("version"),
                    "display_name": image.get("display_name"),
                    "display_version": image.get("display_version"),
                    "summary": image.get("summary"),
                    "release_date": image.get("release_date"),
                })
            else:
                formatted.append({"version": image})

        return {
            "total": len(formatted),
            "base_images": formatted,
        }
