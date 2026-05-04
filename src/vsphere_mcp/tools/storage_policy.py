from __future__ import annotations

from typing import Any

import requests
import urllib3

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task

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


def register_storage_policy_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_storage_policies() -> dict[str, Any]:
        """List all VM storage policies (SPBM) defined in vCenter."""
        logger.info("list_storage_policies")

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/storage/policies")
        resp.raise_for_status()
        raw: list[dict[str, Any]] = resp.json()

        policies = [
            {
                "id": p.get("policy"),
                "name": p.get("name"),
                "description": p.get("description", ""),
            }
            for p in raw
        ]

        return {
            "total": len(policies),
            "policies": policies,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_storage_policy(policy_id: str) -> dict[str, Any]:
        """Get detailed information about a specific VM storage policy.

        Args:
            policy_id: The ID of the storage policy (e.g. 'aa6d5a82-1c88-45da-85d3-3d74b91a5bad').
        """
        logger.info("get_storage_policy", policy_id=policy_id)

        session, base_url = _get_rest_session(client)
        resp = session.get(f"{base_url}/api/vcenter/storage/policies/{policy_id}")
        resp.raise_for_status()
        detail: dict[str, Any] = resp.json()

        return {
            "id": policy_id,
            "name": detail.get("name"),
            "description": detail.get("description", ""),
            "constraints": detail.get("constraints"),
            "sub_profiles": detail.get("sub_profiles", []),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_storage_policy(
        name: str,
        description: str = "",
        sub_profiles: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new VM storage policy (SPBM).

        Args:
            name: Name for the new storage policy.
            description: Optional description for the policy.
            sub_profiles: Optional list of sub-profile capability constraint dicts.
                          Each entry is passed verbatim as a sub-profile in the
                          policy spec. Omit to create a tag-based policy with no
                          capability rules, which can be refined later via the
                          vSphere UI or subsequent API calls.

        [HIGH RISK] Requires confirm=True to execute.
        """
        logger.info("create_storage_policy", name=name)

        session, base_url = _get_rest_session(client)
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "constraints": {
                "sub_profiles": sub_profiles if sub_profiles is not None else [],
            },
        }
        resp = session.post(f"{base_url}/api/vcenter/storage/policies", json=payload)
        resp.raise_for_status()
        policy_id: str = resp.json()

        return {
            "status": "success",
            "operation": "create_storage_policy",
            "policy_id": policy_id,
            "name": name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_storage_policy(policy_id: str) -> dict[str, Any]:
        """Delete a VM storage policy by ID.

        Args:
            policy_id: The ID of the storage policy to delete.

        [HIGH RISK] Requires confirm=True to execute.
        """
        logger.info("delete_storage_policy", policy_id=policy_id)

        session, base_url = _get_rest_session(client)
        resp = session.delete(f"{base_url}/api/vcenter/storage/policies/{policy_id}")
        resp.raise_for_status()

        return {
            "status": "success",
            "operation": "delete_storage_policy",
            "policy_id": policy_id,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def assign_storage_policy_to_vm(vm_name: str, policy_id: str) -> dict[str, Any]:
        """Assign a VM storage policy to a virtual machine.

        This reconfigures the VM's storage profile. The policy is applied to the
        VM home and all virtual disks.

        Args:
            vm_name: Name of the virtual machine.
            policy_id: ID of the storage policy to assign.

        [HIGH RISK] Requires confirm=True to execute.
        """
        from pyVmomi import vim

        logger.info("assign_storage_policy_to_vm", vm_name=vm_name, policy_id=policy_id)

        found = find_vm_with_props(client, vm_name, ["config.hardware.device"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        profile_spec = vim.vm.DefinedProfileSpec(profileId=policy_id)
        config_spec = vim.vm.ConfigSpec(vmProfile=[profile_spec])
        task = vm_obj.ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["policy_id"] = policy_id
        result["operation"] = "assign_storage_policy_to_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    def get_vm_storage_policy_compliance(vm_name: str) -> dict[str, Any]:
        """Check the storage policy compliance status of a virtual machine.

        Returns the assigned policy IDs and the runtime compliance status
        reported by vCenter.

        Args:
            vm_name: Name of the virtual machine to check.
        """
        logger.info("get_vm_storage_policy_compliance", vm_name=vm_name)

        found = find_vm_with_props(client, vm_name, ["config.vmProfile", "summary.runtime.connectionState"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        vm_profile = found.get("config.vmProfile") or []

        assigned_policies = []
        for profile in vm_profile:
            profile_id = getattr(profile, "profileId", None)
            if profile_id:
                assigned_policies.append(profile_id)

        # Retrieve the managed object ID for REST compliance check
        vm_moref = str(vm_obj._moId)  # type: ignore[attr-defined]

        session, base_url = _get_rest_session(client)
        compliance_results: list[dict[str, Any]] = []
        compliance_resp = session.get(
            f"{base_url}/api/vcenter/storage/policies/compliance/vm",
            params={"vm": [vm_moref]},
        )
        if compliance_resp.ok:
            raw = compliance_resp.json()
            # The response is a list of {vm, status, check_time, …} entries
            compliance_results = raw if isinstance(raw, list) else [raw]
        else:
            logger.warning(
                "compliance_check_rest_failed",
                status_code=compliance_resp.status_code,
                body=compliance_resp.text[:200],
            )

        return {
            "vm_name": vm_name,
            "vm_id": vm_moref,
            "assigned_policy_ids": assigned_policies,
            "compliance": compliance_results,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_compatible_datastores(policy_id: str) -> dict[str, Any]:
        """List datastores that are compatible with a given VM storage policy.

        Args:
            policy_id: The ID of the storage policy to check compatibility for.
        """
        logger.info("get_compatible_datastores", policy_id=policy_id)

        session, base_url = _get_rest_session(client)
        resp = session.get(
            f"{base_url}/api/vcenter/storage/policies/{policy_id}/compatible-datastores",
        )

        if resp.status_code == 404:
            # Older vCenter versions may not support this endpoint; fall back to
            # the filter endpoint available since vCenter 7.0 U1.
            filter_resp = session.get(
                f"{base_url}/api/vcenter/storage/policies/datastores/compliance",
                params={"policy": policy_id},
            )
            if filter_resp.ok:
                raw = filter_resp.json()
                compatible = [
                    {"datastore_id": entry.get("datastore"), "status": entry.get("status")}
                    for entry in (raw if isinstance(raw, list) else [])
                    if entry.get("status") == "COMPATIBLE"
                ]
                return {
                    "policy_id": policy_id,
                    "total": len(compatible),
                    "compatible_datastores": compatible,
                    "note": "Retrieved via compatibility filter endpoint",
                }
            filter_resp.raise_for_status()

        resp.raise_for_status()
        raw_ds: list[dict[str, Any]] = resp.json() if resp.content else []

        datastores = [
            {
                "datastore_id": ds.get("datastore") if isinstance(ds, dict) else ds,
                "name": ds.get("name") if isinstance(ds, dict) else None,
            }
            for ds in raw_ds
        ]

        return {
            "policy_id": policy_id,
            "total": len(datastores),
            "compatible_datastores": datastores,
        }
