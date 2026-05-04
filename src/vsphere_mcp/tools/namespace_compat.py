from __future__ import annotations

from typing import Any

import requests
import urllib3
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
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


def register_namespace_compat_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_datastore_namespace_directory(datastore_name: str, path: str) -> dict[str, Any]:
        """Create a top-level directory on a datastore using the namespace manager.

        Args:
            datastore_name: Name of the datastore to create the directory on.
            path: Display name / path for the new directory.
        """
        logger.info("create_datastore_namespace_directory", datastore_name=datastore_name, path=path)
        ns_manager = getattr(client.content, "datastoreNamespaceManager", None)
        if ns_manager is None:
            return {"status": "error", "error": "datastoreNamespaceManager not available on this vCenter"}

        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        try:
            result_path = ns_manager.CreateDirectory(
                datastore=ds_obj,
                displayName=path,
                policy="",
            )
        except Exception as e:
            return {"status": "error", "error": f"Failed to create namespace directory: {e}"}

        return {
            "status": "success",
            "operation": "create_datastore_namespace_directory",
            "datastore_name": datastore_name,
            "path": path,
            "result_path": result_path,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_datastore_namespace_directory(
        datastore_name: str,
        datacenter_name: str,
        path: str,
    ) -> dict[str, Any]:
        """Delete a top-level directory on a datastore using the namespace manager.

        Args:
            datastore_name: Name of the datastore (used for context only).
            datacenter_name: Name of the datacenter containing the datastore.
            path: Datastore path of the directory to delete (e.g. '[ds] .sdd.sf-...').
        """
        logger.info(
            "delete_datastore_namespace_directory",
            datastore_name=datastore_name,
            datacenter_name=datacenter_name,
            path=path,
        )
        ns_manager = getattr(client.content, "datastoreNamespaceManager", None)
        if ns_manager is None:
            return {"status": "error", "error": "datastoreNamespaceManager not available on this vCenter"}

        dc_items = collect_properties(client, vim.Datacenter, ["name"])
        dc_obj = None
        for item in dc_items:
            if item.get("name") == datacenter_name:
                dc_obj = item["_obj"]
                break
        if dc_obj is None:
            return {"status": "error", "error": f"Datacenter '{datacenter_name}' not found"}

        try:
            ns_manager.DeleteDirectory(datacenter=dc_obj, datastorePath=path)
        except Exception as e:
            return {"status": "error", "error": f"Failed to delete namespace directory: {e}"}

        return {
            "status": "success",
            "operation": "delete_datastore_namespace_directory",
            "datacenter_name": datacenter_name,
            "path": path,
        }

    @mcp.tool()
    @handle_tool_errors
    def check_vm_compatibility(
        vm_name: str,
        host_name: str = "",
        pool_name: str = "",
    ) -> dict[str, Any]:
        """Check VM compatibility for migration to a target host or resource pool.

        Args:
            vm_name: Name of the VM to check.
            host_name: Optional name of the target host.
            pool_name: Optional name of the target resource pool.
        """
        logger.info("check_vm_compatibility", vm_name=vm_name, host_name=host_name, pool_name=pool_name)
        checker = getattr(client.content, "vmCompatibilityChecker", None)
        if checker is None:
            return {"status": "error", "error": "vmCompatibilityChecker not available on this vCenter"}

        vm_info = find_vm_with_props(client, vm_name)
        if vm_info is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = vm_info["_obj"]

        host_obj = None
        if host_name:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}

        pool_obj = None
        if pool_name:
            pool_items = collect_properties(client, vim.ResourcePool, ["name"])
            for item in pool_items:
                if item.get("name") == pool_name:
                    pool_obj = item["_obj"]
                    break
            if pool_obj is None:
                return {"status": "error", "error": f"Resource pool '{pool_name}' not found"}

        try:
            task = checker.CheckCompatibility_Task(
                vm=vm_obj,
                host=host_obj,
                pool=pool_obj,
                testType=None,
            )
            result = wait_for_task(task)
        except Exception as e:
            return {"status": "error", "error": f"Compatibility check failed: {e}"}

        return {
            "status": "success",
            "vm_name": vm_name,
            "host_name": host_name,
            "pool_name": pool_name,
            "compatibility_result": result,
        }

    @mcp.tool()
    @handle_tool_errors
    def check_power_on_compatibility(
        vm_name: str,
        host_name: str = "",
        pool_name: str = "",
    ) -> dict[str, Any]:
        """Check power-on compatibility for a VM on a target host or resource pool.

        Args:
            vm_name: Name of the VM to check.
            host_name: Optional name of the target host.
            pool_name: Optional name of the target resource pool.
        """
        logger.info(
            "check_power_on_compatibility",
            vm_name=vm_name,
            host_name=host_name,
            pool_name=pool_name,
        )
        checker = getattr(client.content, "vmCompatibilityChecker", None)
        if checker is None:
            return {"status": "error", "error": "vmCompatibilityChecker not available on this vCenter"}

        vm_info = find_vm_with_props(client, vm_name)
        if vm_info is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = vm_info["_obj"]

        host_obj = None
        if host_name:
            host_obj = find_host_by_name(client, host_name)
            if host_obj is None:
                return {"status": "error", "error": f"Host '{host_name}' not found"}

        pool_obj = None
        if pool_name:
            pool_items = collect_properties(client, vim.ResourcePool, ["name"])
            for item in pool_items:
                if item.get("name") == pool_name:
                    pool_obj = item["_obj"]
                    break
            if pool_obj is None:
                return {"status": "error", "error": f"Resource pool '{pool_name}' not found"}

        try:
            task = checker.CheckPowerOn_Task(
                vm=vm_obj,
                host=host_obj,
                pool=pool_obj,
                testType=None,
            )
            result = wait_for_task(task)
        except Exception as e:
            return {"status": "error", "error": f"Power-on compatibility check failed: {e}"}

        return {
            "status": "success",
            "vm_name": vm_name,
            "host_name": host_name,
            "pool_name": pool_name,
            "power_on_compatibility_result": result,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_tenants() -> dict[str, Any]:
        """List vSphere tenants (requires vSphere 7.0u2+ with multi-tenancy configured)."""
        logger.info("list_tenants")
        tenant_manager = getattr(client.content, "tenantManager", None)
        if tenant_manager is None:
            return {"status": "error", "error": "tenantManager not available on this vCenter"}
        try:
            tenants = tenant_manager.LookupTenantsByPolicy(policyId="") if hasattr(tenant_manager, "LookupTenantsByPolicy") else []
        except Exception as e:
            return {"status": "error", "error": f"Failed to list tenants: {e}"}
        tenant_list: list[dict[str, Any]] = []
        for t in tenants or []:
            tenant_list.append({"tenant": str(t)})
        return {"status": "success", "total": len(tenant_list), "tenants": tenant_list}

    @mcp.tool()
    @handle_tool_errors
    def query_host_connected_luns(lun_uuid: str) -> dict[str, Any]:
        """Query which hosts have a specific LUN (by UUID) attached.

        Args:
            lun_uuid: UUID of the LUN to query for attached hosts.
        """
        logger.info("query_host_connected_luns", lun_uuid=lun_uuid)
        storage_query_manager = getattr(client.content, "storageQueryManager", None)
        if storage_query_manager is None:
            return {"status": "error", "error": "storageQueryManager not available on this vCenter"}
        try:
            hosts = storage_query_manager.QueryHostsWithAttachedLun(lunUuid=lun_uuid)
        except Exception as e:
            return {"status": "error", "error": f"Failed to query hosts with attached LUN: {e}"}

        host_list: list[dict[str, Any]] = []
        for host in hosts or []:
            host_list.append(
                {
                    "name": host.name if hasattr(host, "name") else str(host),
                    "moref": host._moId if hasattr(host, "_moId") else None,
                }
            )
        return {"status": "success", "lun_uuid": lun_uuid, "total": len(host_list), "hosts": host_list}

    @mcp.tool()
    @handle_tool_errors
    def get_guest_customization_status(vm_name: str) -> dict[str, Any]:
        """Get the guest customization status for a VM (requires vSphere 7.0+).

        Args:
            vm_name: Name of the VM to query customization status for.
        """
        logger.info("get_guest_customization_status", vm_name=vm_name)
        cust_manager = getattr(client.content, "guestCustomizationManager", None)
        if cust_manager is None:
            return {"status": "error", "error": "guestCustomizationManager not available on this vCenter"}

        vm_info = find_vm_with_props(client, vm_name)
        if vm_info is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = vm_info["_obj"]

        try:
            status = cust_manager.QueryCustomizationStatus(vm=vm_obj)
        except AttributeError:
            return {"status": "error", "error": "QueryCustomizationStatus method not available"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to get guest customization status: {e}"}

        return {
            "status": "success",
            "vm_name": vm_name,
            "customization_status": str(status) if status else None,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def abort_guest_customization(vm_name: str) -> dict[str, Any]:
        """Abort an in-progress guest OS customization on a VM.

        Args:
            vm_name: Name of the VM to abort customization on.
        """
        logger.info("abort_guest_customization", vm_name=vm_name)
        cust_manager = getattr(client.content, "guestCustomizationManager", None)
        if cust_manager is None:
            return {"status": "error", "error": "guestCustomizationManager not available on this vCenter"}

        vm_info = find_vm_with_props(client, vm_name)
        if vm_info is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = vm_info["_obj"]

        try:
            cust_manager.AbortCustomization(vm=vm_obj, auth=None)
        except AttributeError:
            return {"status": "error", "error": "AbortCustomization method not available"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to abort guest customization: {e}"}

        return {
            "status": "success",
            "operation": "abort_guest_customization",
            "vm_name": vm_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_snmp_config() -> dict[str, Any]:
        """Get the vCenter SNMP system configuration."""
        logger.info("get_vcenter_snmp_config")
        snmp_system = getattr(client.content, "snmpSystem", None)
        if snmp_system is None:
            return {"status": "error", "error": "snmpSystem not available on this vCenter"}
        try:
            config = snmp_system.configuration
        except Exception as e:
            return {"status": "error", "error": f"Failed to get SNMP configuration: {e}"}
        if config is None:
            return {"status": "success", "snmp_config": None}

        return {
            "status": "success",
            "enabled": getattr(config, "enabled", None),
            "port": getattr(config, "port", None),
            "read_only_communities": list(getattr(config, "readOnlyCommunities", []) or []),
            "trap_targets": [
                {
                    "host_name": getattr(t, "hostName", None),
                    "port": getattr(t, "port", None),
                    "community": getattr(t, "community", None),
                }
                for t in (getattr(config, "trapTargets", []) or [])
            ],
        }

    @mcp.tool()
    @handle_tool_errors
    def refresh_vm_storage_info(vm_name: str) -> dict[str, Any]:
        """Refresh the storage information for a VM.

        Args:
            vm_name: Name of the VM to refresh storage info for.
        """
        logger.info("refresh_vm_storage_info", vm_name=vm_name)
        vm_info = find_vm_with_props(client, vm_name)
        if vm_info is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = vm_info["_obj"]
        try:
            vm_obj.RefreshStorageInfo()
        except Exception as e:
            return {"status": "error", "error": f"Failed to refresh VM storage info: {e}"}
        return {
            "status": "success",
            "operation": "refresh_vm_storage_info",
            "vm_name": vm_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_vm_display_topology(
        vm_name: str,
        displays: list[dict[str, int]],
    ) -> dict[str, Any]:
        """Set the display topology (resolution and position) for a VM's virtual displays.

        Args:
            vm_name: Name of the VM to configure displays for.
            displays: List of display config dicts, each with 'width', 'height', 'x', and 'y' keys.
        """
        logger.info("set_vm_display_topology", vm_name=vm_name, display_count=len(displays))
        if not displays:
            return {"status": "error", "error": "displays list must not be empty"}

        vm_info = find_vm_with_props(client, vm_name)
        if vm_info is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = vm_info["_obj"]

        display_specs: list[Any] = []
        for d in displays:
            spec = vim.vm.DisplayTopology()
            spec.width = d.get("width", 1024)
            spec.height = d.get("height", 768)
            spec.x = d.get("x", 0)
            spec.y = d.get("y", 0)
            display_specs.append(spec)

        try:
            vm_obj.SetDisplayTopology(displays=display_specs)
        except Exception as e:
            return {"status": "error", "error": f"Failed to set display topology: {e}"}

        return {
            "status": "success",
            "operation": "set_vm_display_topology",
            "vm_name": vm_name,
            "display_count": len(display_specs),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_service_list() -> dict[str, Any]:
        """Get the list of services registered with the vCenter ServiceManager."""
        logger.info("get_vcenter_service_list")
        service_manager = getattr(client.content, "serviceManager", None)
        if service_manager is None:
            return {"status": "error", "error": "serviceManager not available on this vCenter"}
        try:
            services = service_manager.QueryServiceList()
        except Exception as e:
            return {"status": "error", "error": f"Failed to query service list: {e}"}

        service_list: list[dict[str, Any]] = []
        for svc in services or []:
            service_list.append(
                {
                    "service_name": getattr(svc, "serviceName", None),
                    "description": getattr(svc, "description", None),
                    "service": str(svc.service) if hasattr(svc, "service") else None,
                }
            )
        return {"status": "success", "total": len(service_list), "services": service_list}

    @mcp.tool()
    @handle_tool_errors
    def get_cluster_profile_compliance(cluster_name: str) -> dict[str, Any]:
        """Check profile compliance for a cluster using the ClusterProfileManager.

        Args:
            cluster_name: Name of the cluster to check profile compliance for.
        """
        logger.info("get_cluster_profile_compliance", cluster_name=cluster_name)
        profile_manager = getattr(client.content, "clusterProfileManager", None)
        if profile_manager is None:
            return {"status": "error", "error": "clusterProfileManager not available on this vCenter"}

        cluster_items = collect_properties(client, vim.ClusterComputeResource, ["name"])
        cluster_obj = None
        for item in cluster_items:
            if item.get("name") == cluster_name:
                cluster_obj = item["_obj"]
                break
        if cluster_obj is None:
            return {"status": "error", "error": f"Cluster '{cluster_name}' not found"}

        try:
            task = profile_manager.CheckCompliance_Task(profile=[], entity=cluster_obj)
            result = wait_for_task(task)
        except AttributeError:
            return {"status": "error", "error": "CheckCompliance_Task not available on clusterProfileManager"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to check cluster profile compliance: {e}"}

        return {
            "status": "success",
            "cluster_name": cluster_name,
            "compliance_result": result,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_cluster_profiles() -> dict[str, Any]:
        """List all cluster profiles registered with the ClusterProfileManager."""
        logger.info("list_cluster_profiles")
        profile_manager = getattr(client.content, "clusterProfileManager", None)
        if profile_manager is None:
            return {"status": "error", "error": "clusterProfileManager not available on this vCenter"}
        try:
            profiles = profile_manager.profile or []
        except Exception as e:
            return {"status": "error", "error": f"Failed to list cluster profiles: {e}"}

        profile_list: list[dict[str, Any]] = []
        for p in profiles:
            try:
                info = p.config
                profile_list.append(
                    {
                        "name": getattr(info, "name", None),
                        "description": getattr(info, "annotation", None),
                        "moref": p._moId if hasattr(p, "_moId") else None,
                    }
                )
            except Exception:
                profile_list.append({"moref": p._moId if hasattr(p, "_moId") else str(p)})

        return {"status": "success", "total": len(profile_list), "cluster_profiles": profile_list}

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_resource_pools_rest() -> dict[str, Any]:
        """List all resource pools visible in vCenter via the REST API."""
        logger.info("get_vcenter_resource_pools_rest")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/resource-pool")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"status": "success", "total": len(data), "resource_pools": data}

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_authentication_token() -> dict[str, Any]:
        """Acquire a new vCenter REST API session token using the configured credentials."""
        logger.info("get_vcenter_authentication_token")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/session")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return {"status": "success", "session_info": data}

    @mcp.tool()
    @handle_tool_errors
    def get_guest_customization_specs_rest() -> dict[str, Any]:
        """List guest OS customization specifications via the vCenter REST API."""
        logger.info("get_guest_customization_specs_rest")
        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/guest/customization-specs")
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return {"status": "success", "total": len(data), "customization_specs": data}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_tenant(tenant_id: str, resources: dict[str, Any] | None = None) -> dict[str, Any]:
        """Update tenant resource configuration (requires vSphere 7.0u2+ with multi-tenancy).

        Args:
            tenant_id: Identifier of the tenant to update.
            resources: Resource configuration dict to apply to the tenant.
        """
        logger.info("update_tenant", tenant_id=tenant_id)
        tenant_manager = getattr(client.content, "tenantManager", None)
        if tenant_manager is None:
            return {"status": "error", "error": "tenantManager not available on this vCenter"}

        try:
            if hasattr(tenant_manager, "UpdateTenant"):
                tenant_manager.UpdateTenant(tenant=tenant_id, resources=resources or {})
            else:
                return {"status": "error", "error": "UpdateTenant method not available on tenantManager"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to update tenant '{tenant_id}': {e}"}

        return {
            "status": "success",
            "operation": "update_tenant",
            "tenant_id": tenant_id,
            "resources": resources,
        }
