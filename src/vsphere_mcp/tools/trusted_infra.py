from __future__ import annotations

from typing import Any

import requests
import urllib3
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
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


def register_trusted_infra_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_trusted_kms_providers() -> dict[str, Any]:
        """List Key Management Server (KMS) providers registered with the Trusted Infrastructure service."""
        logger.info("list_trusted_kms_providers")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/trusted-infrastructure/kms/services")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"total": len(data), "kms_providers": data}

    @mcp.tool()
    @handle_tool_errors
    def get_trusted_cluster_attestation_report(cluster_id: str) -> dict[str, Any]:
        """Get the attestation report for a Trusted Cluster.

        Args:
            cluster_id: Managed object ID of the cluster (e.g. 'domain-c10').
        """
        logger.info("get_trusted_cluster_attestation_report", cluster_id=cluster_id)
        session, base_url = _get_rest_session(client)
        resp = session.get(
            f"{base_url}/api/vcenter/trusted-infrastructure/trusted-clusters/{cluster_id}/attestation"
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return {"cluster_id": cluster_id, "attestation_report": data}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def configure_trust_authority_host(host_id: str, action: str = "enable") -> dict[str, Any]:
        """Enable or disable Trust Authority on a host.

        Args:
            host_id: Managed object ID of the host (e.g. 'host-10').
            action: Action to perform: 'enable' or 'disable' (default 'enable').
        """
        logger.info("configure_trust_authority_host", host_id=host_id, action=action)
        valid_actions = ("enable", "disable")
        if action not in valid_actions:
            return {"status": "error", "error": f"action must be one of: {', '.join(valid_actions)}"}
        session, base_url = _get_rest_session(client)
        resp = session.post(
            f"{base_url}/api/vcenter/trusted-infrastructure/hosts/{host_id}?action={action}"
        )
        resp.raise_for_status()
        return {
            "status": "success",
            "operation": "configure_trust_authority_host",
            "host_id": host_id,
            "action": action,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_trust_authority_hosts() -> dict[str, Any]:
        """List all hosts enrolled in the Trusted Infrastructure service."""
        logger.info("list_trust_authority_hosts")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/trusted-infrastructure/hosts")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"total": len(data), "trust_authority_hosts": data}

    @mcp.tool()
    @handle_tool_errors
    def query_compatible_hosts_for_dvs(
        dvs_name: str = "",
        container_name: str = "",
    ) -> dict[str, Any]:
        """Query hosts compatible with creating a new Distributed Virtual Switch.

        Args:
            dvs_name: Optional name of an existing DVSwitch to use for product spec filtering.
            container_name: Optional name of a container (datacenter/cluster/folder) to search within.
        """
        logger.info("query_compatible_hosts_for_dvs", dvs_name=dvs_name, container_name=container_name)
        dvs_manager = client.content.dvSwitchManager
        if dvs_manager is None:
            return {"status": "error", "error": "DVSwitch manager not available"}

        container = client.content.rootFolder
        if container_name:
            for vim_type in (vim.Datacenter, vim.ClusterComputeResource, vim.Folder):
                items = collect_properties(client, vim_type, ["name"])
                for item in items:
                    if item.get("name") == container_name:
                        container = item["_obj"]
                        break

        switch_product_spec = None
        if dvs_name:
            dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "productInfo"])
            for item in dvs_items:
                if item.get("name") == dvs_name:
                    try:
                        product_info = item.get("productInfo")
                        if product_info:
                            switch_product_spec = vim.dvs.ProductSpec(version=product_info.version)
                    except Exception:
                        pass
                    break

        try:
            hosts = dvs_manager.QueryCompatibleHostForNewDvs(
                container=container,
                recursive=True,
                switchProductSpec=switch_product_spec,
            )
        except Exception as e:
            return {"status": "error", "error": f"Failed to query compatible hosts: {e}"}

        host_list = []
        for host in hosts or []:
            host_list.append(
                {
                    "name": host.name if hasattr(host, "name") else str(host),
                    "moref": host._moId if hasattr(host, "_moId") else None,
                }
            )
        return {"total": len(host_list), "compatible_hosts": host_list}

    @mcp.tool()
    @handle_tool_errors
    def query_dvs_feature_capability(dvs_name: str) -> dict[str, Any]:
        """Query the feature capabilities of a Distributed Virtual Switch product.

        Args:
            dvs_name: Name of the DVSwitch to query feature capabilities for.
        """
        logger.info("query_dvs_feature_capability", dvs_name=dvs_name)
        dvs_manager = client.content.dvSwitchManager
        if dvs_manager is None:
            return {"status": "error", "error": "DVSwitch manager not available"}

        dvs_items = collect_properties(client, vim.DistributedVirtualSwitch, ["name", "productInfo"])
        product_spec = None
        for item in dvs_items:
            if item.get("name") == dvs_name:
                try:
                    product_info = item.get("productInfo")
                    if product_info:
                        product_spec = vim.dvs.ProductSpec(version=product_info.version)
                except Exception:
                    pass
                break

        if product_spec is None:
            return {"status": "error", "error": f"DVSwitch '{dvs_name}' not found or product info unavailable"}

        try:
            capability = dvs_manager.QueryDvsFeatureCapability(switchProductSpec=product_spec)
        except Exception as e:
            return {"status": "error", "error": f"Failed to query DVS capabilities: {e}"}

        if capability is None:
            return {"dvs_name": dvs_name, "capability": None}

        result: dict[str, Any] = {
            "dvs_name": dvs_name,
            "nioc_supported": getattr(capability, "niocSupported", None),
            "vspan_supported": getattr(capability, "vspanSupported", None),
            "lacp_supported": getattr(capability, "lacpSupported", None),
            "ipfix_supported": getattr(capability, "ipfixSupported", None),
            "multicast_snooping_supported": getattr(capability, "multicastSnoopingSupported", None),
        }
        return result

    @mcp.tool()
    @handle_tool_errors
    def query_available_dvs_specs() -> dict[str, Any]:
        """Query the available Distributed Virtual Switch product specifications."""
        logger.info("query_available_dvs_specs")
        dvs_manager = client.content.dvSwitchManager
        if dvs_manager is None:
            return {"status": "error", "error": "DVSwitch manager not available"}

        try:
            specs = dvs_manager.QueryAvailableDvsSpec(recommended=False)
        except Exception as e:
            return {"status": "error", "error": f"Failed to query DVS specs: {e}"}

        spec_list: list[dict[str, Any]] = []
        for spec in specs or []:
            spec_list.append(
                {
                    "product_line_id": getattr(spec, "productLineId", None),
                    "vendor": getattr(spec, "vendor", None),
                    "version": getattr(spec, "version", None),
                    "name": getattr(spec, "name", None),
                    "description": getattr(spec, "description", None),
                }
            )
        return {"total": len(spec_list), "dvs_specs": spec_list}
