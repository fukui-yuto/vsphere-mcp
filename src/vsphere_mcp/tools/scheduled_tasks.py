from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm

logger = get_logger(__name__)


def register_scheduled_task_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_scheduled_tasks() -> dict[str, Any]:
        """List all scheduled tasks defined in vCenter."""
        logger.info("list_scheduled_tasks")
        manager = client.content.scheduledTaskManager
        if manager is None:
            return {"status": "error", "error": "Scheduled task manager not available"}
        raw_tasks = manager.scheduledTask or []
        tasks: list[dict[str, Any]] = []
        for task in raw_tasks:
            info = task.info
            entry: dict[str, Any] = {
                "name": info.name if hasattr(info, "name") else None,
                "description": info.description if hasattr(info, "description") else None,
                "enabled": info.enabled if hasattr(info, "enabled") else None,
                "next_run_time": str(info.nextRunTime) if hasattr(info, "nextRunTime") and info.nextRunTime else None,
                "last_modified_time": str(info.lastModifiedTime) if hasattr(info, "lastModifiedTime") and info.lastModifiedTime else None,
                "scheduler": type(info.scheduler).__name__ if hasattr(info, "scheduler") and info.scheduler else None,
            }
            tasks.append(entry)
        return {"total": len(tasks), "scheduled_tasks": tasks}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_scheduled_task(task_name: str) -> dict[str, Any]:
        """Delete a scheduled task by name.

        Args:
            task_name: Name of the scheduled task to delete.
        """
        logger.info("delete_scheduled_task", task_name=task_name)
        manager = client.content.scheduledTaskManager
        if manager is None:
            return {"status": "error", "error": "Scheduled task manager not available"}
        raw_tasks = manager.scheduledTask or []
        task_obj = None
        for task in raw_tasks:
            if getattr(task.info, "name", None) == task_name:
                task_obj = task
                break
        if task_obj is None:
            return {"status": "error", "error": f"Scheduled task '{task_name}' not found"}
        task_obj.RemoveScheduledTask()
        return {
            "status": "success",
            "operation": "delete_scheduled_task",
            "task_name": task_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def run_scheduled_task(task_name: str) -> dict[str, Any]:
        """Run a scheduled task immediately by name.

        Args:
            task_name: Name of the scheduled task to run.
        """
        logger.info("run_scheduled_task", task_name=task_name)
        manager = client.content.scheduledTaskManager
        if manager is None:
            return {"status": "error", "error": "Scheduled task manager not available"}
        raw_tasks = manager.scheduledTask or []
        task_obj = None
        for task in raw_tasks:
            if getattr(task.info, "name", None) == task_name:
                task_obj = task
                break
        if task_obj is None:
            return {"status": "error", "error": f"Scheduled task '{task_name}' not found"}
        task_obj.RunScheduledTask()
        return {
            "status": "success",
            "operation": "run_scheduled_task",
            "task_name": task_name,
        }
