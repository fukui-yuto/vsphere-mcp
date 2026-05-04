from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

logger = get_logger(__name__)


def register_license_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def add_license(
        license_key: str,
        labels: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Add a new license key to vCenter.

        Args:
            license_key: The license key string to add.
            labels: Optional key-value labels to associate with the license.
        """
        logger.info("add_license")
        license_manager = client.content.licenseManager
        if license_manager is None:
            return {"status": "error", "error": "License manager not available"}

        labels_list: list[vim.KeyValue] = []
        if labels:
            for k, v in labels.items():
                kv = vim.KeyValue()
                kv.key = k
                kv.value = v
                labels_list.append(kv)

        license_info = license_manager.AddLicense(licenseKey=license_key, labels=labels_list)
        return {
            "status": "success",
            "operation": "add_license",
            "license_name": license_info.name if hasattr(license_info, "name") else None,
            "edition_key": license_info.editionKey if hasattr(license_info, "editionKey") else None,
            "total": license_info.total if hasattr(license_info, "total") else None,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_license(license_key: str) -> dict[str, Any]:
        """Remove a license key from vCenter.

        Args:
            license_key: The license key string to remove.
        """
        logger.info("remove_license")
        license_manager = client.content.licenseManager
        if license_manager is None:
            return {"status": "error", "error": "License manager not available"}
        license_manager.RemoveLicense(licenseKey=license_key)
        return {
            "status": "success",
            "operation": "remove_license",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def assign_license(entity_id: str, license_key: str) -> dict[str, Any]:
        """Assign a license to a vCenter entity (e.g. a host or cluster) by its MoRef ID.

        Args:
            entity_id: Managed object reference ID of the entity (e.g. 'host-123').
            license_key: The license key string to assign.
        """
        logger.info("assign_license", entity_id=entity_id)
        license_manager = client.content.licenseManager
        if license_manager is None:
            return {"status": "error", "error": "License manager not available"}
        assignment_manager = license_manager.licenseAssignmentManager
        if assignment_manager is None:
            return {"status": "error", "error": "License assignment manager not available"}
        assignment_info = assignment_manager.UpdateAssignedLicense(
            entity=entity_id,
            licenseKey=license_key,
        )
        return {
            "status": "success",
            "operation": "assign_license",
            "entity_id": entity_id,
            "license_name": assignment_info.assignedLicense.name if hasattr(assignment_info, "assignedLicense") and assignment_info.assignedLicense else None,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_license_assignments() -> dict[str, Any]:
        """List all license assignments in vCenter."""
        logger.info("list_license_assignments")
        license_manager = client.content.licenseManager
        if license_manager is None:
            return {"status": "error", "error": "License manager not available"}
        assignment_manager = license_manager.licenseAssignmentManager
        if assignment_manager is None:
            return {"status": "error", "error": "License assignment manager not available"}
        raw_assignments = assignment_manager.QueryAssignedLicenses(entityId=None) or []
        assignments: list[dict[str, Any]] = []
        for assign in raw_assignments:
            lic = assign.assignedLicense if hasattr(assign, "assignedLicense") else None
            entry: dict[str, Any] = {
                "entity_id": assign.entityId if hasattr(assign, "entityId") else None,
                "entity_display_name": assign.entityDisplayName if hasattr(assign, "entityDisplayName") else None,
                "license_name": lic.name if lic and hasattr(lic, "name") else None,
                "license_key": lic.licenseKey if lic and hasattr(lic, "licenseKey") else None,
                "edition_key": lic.editionKey if lic and hasattr(lic, "editionKey") else None,
                "total": lic.total if lic and hasattr(lic, "total") else None,
                "used": lic.used if lic and hasattr(lic, "used") else None,
            }
            assignments.append(entry)
        return {"total": len(assignments), "assignments": assignments}
