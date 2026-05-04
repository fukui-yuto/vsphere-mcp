from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)

ENTITY_TYPE_MAP: dict[str, type] = {
    "vm": vim.VirtualMachine,
    "host": vim.HostSystem,
    "datacenter": vim.Datacenter,
    "cluster": vim.ClusterComputeResource,
    "folder": vim.Folder,
}


def register_vcenter_admin_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_roles() -> dict[str, Any]:
        """List all roles defined in vCenter with their privileges."""
        logger.info("list_roles")
        content = client.content
        auth_mgr = content.authorizationManager
        if auth_mgr is None:
            return {"status": "error", "error": "authorizationManager not available"}
        role_list = auth_mgr.roleList

        roles: list[dict[str, Any]] = []
        for role in role_list or []:
            roles.append(
                {
                    "roleId": role.roleId,
                    "name": role.name,
                    "label": role.info.label if hasattr(role.info, "label") else None,
                    "summary": role.info.summary if hasattr(role.info, "summary") else None,
                    "privilege": list(role.privilege) if role.privilege else [],
                }
            )

        return {"total": len(roles), "roles": roles}

    @mcp.tool()
    @handle_tool_errors
    def get_entity_permissions(
        entity_type: str,
        entity_name: str,
    ) -> dict[str, Any]:
        """Get permissions assigned to a vSphere entity.

        entity_type: 'vm', 'host', 'datacenter', 'cluster', or 'folder'.
        entity_name: Name of the entity to look up.
        """
        logger.info(
            "get_entity_permissions",
            entity_type=entity_type,
            entity_name=entity_name,
        )

        vim_type = ENTITY_TYPE_MAP.get(entity_type.lower())
        if vim_type is None:
            return {
                "status": "error",
                "error": (f"Unknown entity_type '{entity_type}'. Valid types: {', '.join(ENTITY_TYPE_MAP.keys())}"),
            }

        items = collect_properties(client, vim_type, ["name"])
        entity = None
        for item in items:
            if item.get("name") == entity_name:
                entity = item["_obj"]
                break

        if entity is None:
            return {
                "status": "error",
                "error": f"{entity_type} '{entity_name}' not found",
            }

        content = client.content
        permissions_raw = content.authorizationManager.RetrieveEntityPermissions(
            entity=entity,
            inherited=True,
        )

        permissions: list[dict[str, Any]] = []
        for perm in permissions_raw or []:
            permissions.append(
                {
                    "principal": perm.principal,
                    "roleId": perm.roleId,
                    "group": perm.group,
                    "propagate": perm.propagate,
                }
            )

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "total": len(permissions),
            "permissions": permissions,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_license_info() -> dict[str, Any]:
        """Get vCenter license information with masked license keys."""
        logger.info("get_license_info")
        content = client.content
        license_list = content.licenseManager.licenses

        licenses: list[dict[str, Any]] = []
        for lic in license_list or []:
            masked_key = ("****-" + lic.licenseKey[-5:]) if lic.licenseKey else None

            expiration_date = None
            properties: dict[str, Any] = {}
            for prop in lic.properties or []:
                if prop.key == "expirationDate":
                    expiration_date = str(prop.value) if prop.value else None
                else:
                    properties[prop.key] = str(prop.value) if prop.value is not None else None

            licenses.append(
                {
                    "name": lic.name,
                    "licenseKey": masked_key,
                    "total": lic.total,
                    "used": lic.used,
                    "expirationDate": expiration_date,
                    "properties": properties,
                }
            )

        return {"total": len(licenses), "licenses": licenses}

    @mcp.tool()
    @handle_tool_errors
    def list_active_sessions() -> dict[str, Any]:
        """List active sessions on vCenter."""
        logger.info("list_active_sessions")
        content = client.content
        session_mgr = content.sessionManager
        if session_mgr is None:
            return {"status": "error", "error": "sessionManager not available"}
        session_list = session_mgr.sessionList

        sessions: list[dict[str, Any]] = []
        for session in session_list or []:
            sessions.append(
                {
                    "key": session.key,
                    "userName": session.userName,
                    "fullName": session.fullName,
                    "loginTime": str(session.loginTime) if session.loginTime else None,
                    "lastActiveTime": (str(session.lastActiveTime) if session.lastActiveTime else None),
                    "ipAddress": session.ipAddress,
                    "userAgent": session.userAgent,
                }
            )

        return {"total": len(sessions), "sessions": sessions}

    @mcp.tool()
    @handle_tool_errors
    def list_recent_tasks(
        max_count: int = 50,
        hours: int = 24,
    ) -> dict[str, Any]:
        """List recent tasks from vCenter task manager.

        max_count: Maximum number of tasks to return (default 50).
        hours: Look back this many hours (default 24).
        """
        logger.info("list_recent_tasks", max_count=max_count, hours=hours)
        if hours <= 0:
            return {"status": "error", "error": "hours must be a positive integer"}
        if max_count <= 0:
            return {"status": "error", "error": "max_count must be a positive integer"}
        content = client.content
        task_manager = content.taskManager

        filter_spec = vim.TaskFilterSpec()
        now = datetime.now(timezone.utc)
        filter_spec.time = vim.TaskFilterSpec.ByTime(
            beginTime=now - timedelta(hours=hours),
            endTime=now,
            timeType=vim.TaskFilterSpec.TimeOption.startedTime,
        )

        collector = task_manager.CreateCollectorForTasks(filter=filter_spec)
        try:
            collector.ResetCollector()
            raw_tasks = collector.ReadNextTasks(maxCount=max_count)

            tasks: list[dict[str, Any]] = []
            for task_info in raw_tasks or []:
                entity_name = None
                if hasattr(task_info, "entityName") and task_info.entityName:
                    entity_name = task_info.entityName
                elif hasattr(task_info, "entity") and task_info.entity:
                    try:
                        entity_name = task_info.entity.name
                    except Exception:
                        entity_name = str(task_info.entity)

                error_msg = None
                if task_info.error:
                    error_msg = str(task_info.error)

                result_val = None
                if task_info.result is not None:
                    result_val = str(task_info.result)

                tasks.append(
                    {
                        "taskId": task_info.key if hasattr(task_info, "key") else None,
                        "descriptionId": task_info.descriptionId,
                        "entityName": entity_name,
                        "state": str(task_info.state),
                        "startTime": (str(task_info.startTime) if task_info.startTime else None),
                        "completeTime": (str(task_info.completeTime) if task_info.completeTime else None),
                        "result": result_val,
                        "error": error_msg,
                    }
                )
        finally:
            try:
                collector.DestroyCollector()
            except Exception:
                pass

        return {"total": len(tasks), "hours": hours, "tasks": tasks}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def terminate_session(session_key: str) -> dict[str, Any]:
        """Terminate a specific vCenter session by session key.

        Args:
            session_key: The session key to terminate (from list_active_sessions).
        """
        logger.info("terminate_session", session_key=session_key)
        content = client.content
        session_mgr = content.sessionManager
        if session_mgr is None:
            return {"status": "error", "error": "sessionManager not available"}
        session_mgr.TerminateSession(sessionList=[session_key])
        return {
            "status": "success",
            "session_key": session_key,
            "operation": "terminate_session",
        }
