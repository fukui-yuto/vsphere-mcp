from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_scheduled_task(client: VSphereClient, task_name: str) -> Any | None:
    """Find a scheduled task by name. Returns the task object or None."""
    manager = client.content.scheduledTaskManager
    if manager is None:
        return None
    for task in manager.scheduledTask or []:
        if getattr(task.info, "name", None) == task_name:
            return task
    return None


def register_instant_clone_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def instant_clone_vm(
        source_vm_name: str,
        new_name: str,
        relocate_spec: dict | None = None,
    ) -> dict[str, Any]:
        """Instant clone a running VM. The source VM must be powered on.

        Instant clone creates a sibling VM that shares memory pages with the source
        at the moment of cloning. The source VM is briefly quiesced during the operation.

        Args:
            source_vm_name: Name of the source VM (must be powered on).
            new_name: Name for the new instant-cloned VM.
            relocate_spec: Optional relocation spec as a dict with optional keys:
                "datastore" (datastore name) and "host" (host name).
        """
        logger.info("instant_clone_vm", source_vm_name=source_vm_name, new_name=new_name)

        found = find_vm_with_props(client, source_vm_name, ["runtime.powerState"])
        if found is None:
            return {"status": "error", "error": f"VM '{source_vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if power_state != vim.VirtualMachinePowerState.poweredOn:
            return {
                "status": "error",
                "error": f"VM '{source_vm_name}' must be powered on for instant clone (current state: {power_state})",
            }

        location = vim.vm.RelocateSpec()

        if relocate_spec:
            ds_name = relocate_spec.get("datastore")
            if ds_name:
                ds_items = collect_properties(client, vim.Datastore, ["name"])
                for ds in ds_items:
                    if ds.get("name") == ds_name:
                        location.datastore = ds["_obj"]
                        break
                else:
                    return {"status": "error", "error": f"Datastore '{ds_name}' not found"}

            host_name = relocate_spec.get("host")
            if host_name:
                host_items = collect_properties(client, vim.HostSystem, ["name"])
                for h in host_items:
                    if h.get("name") == host_name:
                        location.host = h["_obj"]
                        break
                else:
                    return {"status": "error", "error": f"Host '{host_name}' not found"}

        clone_spec = vim.vm.InstantCloneSpec(
            name=new_name,
            location=location,
        )

        task = found["_obj"].InstantClone_Task(spec=clone_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Instant clone failed")}

        return {
            "status": "success",
            "operation": "instant_clone_vm",
            "source_vm_name": source_vm_name,
            "new_name": new_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="critical")
    def cross_vcenter_migrate_vm(
        vm_name: str,
        target_vcenter_host: str,
        target_vcenter_user: str,
        target_vcenter_password: str,
        target_host: str,
        target_datastore: str | None = None,
    ) -> dict[str, Any]:
        """Migrate a VM to a different vCenter (Cross-vCenter vMotion).

        Builds a ServiceLocator pointing at the target vCenter and initiates
        a RelocateVM_Task with that service credential. The VM remains running
        during the migration (live vMotion).

        Args:
            vm_name: Name of the VM to migrate.
            target_vcenter_host: Hostname or IP of the target vCenter server.
            target_vcenter_user: Username for the target vCenter.
            target_vcenter_password: Password for the target vCenter.
            target_host: Name of the destination ESXi host on the target vCenter.
            target_datastore: Name of the destination datastore on the target vCenter,
                or None to keep the same datastore name.
        """
        logger.info(
            "cross_vcenter_migrate_vm",
            vm_name=vm_name,
            target_vcenter_host=target_vcenter_host,
            target_vcenter_user=target_vcenter_user,
            target_host=target_host,
            target_datastore=target_datastore,
        )

        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        credential = vim.ServiceLocator.NamePassword(
            username=target_vcenter_user,
            password=target_vcenter_password,
        )
        service_locator = vim.ServiceLocator(
            instanceUuid=target_vcenter_host,
            url=f"https://{target_vcenter_host}:443/sdk",
            credential=credential,
        )

        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.service = service_locator

        # Look up host on the target — resolved at the target vCenter side;
        # we pass the host MoRef via a raw reference string approach.
        # For cross-vCenter, the host reference must come from the local inventory
        # only if the host is already known. Otherwise we set host by name lookup
        # on the current connection (cross-vCenter relies on hostName in RelocateSpec).
        host_items = collect_properties(client, vim.HostSystem, ["name"])
        target_host_obj = None
        for h in host_items:
            if h.get("name") == target_host:
                target_host_obj = h["_obj"]
                break
        if target_host_obj is None:
            return {"status": "error", "error": f"Target host '{target_host}' not found in current inventory"}
        relocate_spec.host = target_host_obj

        if target_datastore:
            ds_items = collect_properties(client, vim.Datastore, ["name"])
            for ds in ds_items:
                if ds.get("name") == target_datastore:
                    relocate_spec.datastore = ds["_obj"]
                    break
            else:
                return {"status": "error", "error": f"Target datastore '{target_datastore}' not found"}

        task = found["_obj"].RelocateVM_Task(spec=relocate_spec)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Cross-vCenter migration failed")}

        return {
            "status": "success",
            "operation": "cross_vcenter_migrate_vm",
            "vm_name": vm_name,
            "target_vcenter_host": target_vcenter_host,
            "target_host": target_host,
            "target_datastore": target_datastore,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_scheduled_task(
        entity_name: str,
        entity_type: str,
        action_type: str,
        schedule_type: str,
        task_name: str,
        action_params: dict | None = None,
        schedule_params: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new scheduled task in vCenter.

        Args:
            entity_name: Name of the target entity (e.g. VM name, host name).
            entity_type: vSphere object type: "VirtualMachine", "HostSystem",
                "ResourcePool", "ClusterComputeResource", or "Datacenter".
            action_type: Action to perform: "PowerOn", "PowerOff", "Suspend",
                "Reset", "Snapshot", or "MethodAction".
            schedule_type: Recurrence schedule: "once", "daily", "weekly", or "monthly".
            task_name: Name to assign to the new scheduled task.
            action_params: Optional action parameters as a dict. For "Snapshot":
                {"name": "snap-name", "description": "desc", "memory": false, "quiesce": false}.
                For "MethodAction": {"method": "MethodName", "argument": []}.
            schedule_params: Optional schedule parameters as a dict.
                For "once": {"run_at": "2026-05-04T10:00:00"} (ISO 8601).
                For "daily": {"hour": 2, "minute": 0, "interval": 1}.
                For "weekly": {"hour": 2, "minute": 0, "day_of_week": ["monday"]}.
                For "monthly": {"hour": 2, "minute": 0, "day": 1}.
        """
        logger.info(
            "create_scheduled_task",
            entity_name=entity_name,
            entity_type=entity_type,
            action_type=action_type,
            schedule_type=schedule_type,
            task_name=task_name,
        )

        entity_type_map: dict[str, type] = {
            "VirtualMachine": vim.VirtualMachine,
            "HostSystem": vim.HostSystem,
            "ResourcePool": vim.ResourcePool,
            "ClusterComputeResource": vim.ClusterComputeResource,
            "Datacenter": vim.Datacenter,
        }
        vim_type = entity_type_map.get(entity_type)
        if vim_type is None:
            return {
                "status": "error",
                "error": f"entity_type must be one of: {', '.join(entity_type_map.keys())}",
            }

        items = collect_properties(client, vim_type, ["name"])
        entity_obj = None
        for item in items:
            if item.get("name") == entity_name:
                entity_obj = item["_obj"]
                break
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        params = action_params or {}
        valid_action_types = ("PowerOn", "PowerOff", "Suspend", "Reset", "Snapshot", "MethodAction")
        if action_type not in valid_action_types:
            return {
                "status": "error",
                "error": f"action_type must be one of: {', '.join(valid_action_types)}",
            }

        if action_type == "Snapshot":
            action = vim.action.CreateTaskAction(
                methodName="CreateSnapshot_Task",
            )
        elif action_type == "MethodAction":
            method_name = params.get("method", "")
            if not method_name:
                return {"status": "error", "error": "action_params.method is required for MethodAction"}
            action = vim.action.MethodAction(name=method_name)
            raw_args = params.get("argument", [])
            if raw_args:
                action.argument = [vim.action.MethodActionArgument(value=a) for a in raw_args]
        else:
            # PowerOn, PowerOff, Suspend, Reset → MethodAction on the entity
            method_map = {
                "PowerOn": "PowerOnVM_Task",
                "PowerOff": "PowerOffVM_Task",
                "Suspend": "SuspendVM_Task",
                "Reset": "ResetVM_Task",
            }
            action = vim.action.MethodAction(name=method_map[action_type])

        valid_schedule_types = ("once", "daily", "weekly", "monthly")
        if schedule_type not in valid_schedule_types:
            return {
                "status": "error",
                "error": f"schedule_type must be one of: {', '.join(valid_schedule_types)}",
            }

        sched_params = schedule_params or {}
        if schedule_type == "once":
            import datetime

            run_at_str = sched_params.get("run_at")
            if run_at_str:
                run_at = datetime.datetime.fromisoformat(run_at_str)
            else:
                run_at = datetime.datetime.now() + datetime.timedelta(hours=1)
            scheduler = vim.scheduler.OnceTaskScheduler(runAt=run_at)
        elif schedule_type == "daily":
            scheduler = vim.scheduler.DailyTaskScheduler(
                hour=sched_params.get("hour", 0),
                minute=sched_params.get("minute", 0),
                interval=sched_params.get("interval", 1),
            )
        elif schedule_type == "weekly":
            day_of_week = sched_params.get("day_of_week", ["monday"])
            scheduler = vim.scheduler.WeeklyTaskScheduler(
                hour=sched_params.get("hour", 0),
                minute=sched_params.get("minute", 0),
                sunday="sunday" in day_of_week,
                monday="monday" in day_of_week,
                tuesday="tuesday" in day_of_week,
                wednesday="wednesday" in day_of_week,
                thursday="thursday" in day_of_week,
                friday="friday" in day_of_week,
                saturday="saturday" in day_of_week,
            )
        else:  # monthly
            scheduler = vim.scheduler.MonthlyByDayTaskScheduler(
                hour=sched_params.get("hour", 0),
                minute=sched_params.get("minute", 0),
                day=sched_params.get("day", 1),
            )

        task_spec = vim.scheduler.ScheduledTaskSpec(
            name=task_name,
            description=params.get("description", ""),
            enabled=True,
            scheduler=scheduler,
            action=action,
            notification="",
        )

        manager = client.content.scheduledTaskManager
        if manager is None:
            return {"status": "error", "error": "Scheduled task manager not available"}

        manager.CreateScheduledTask(obj=entity_obj, spec=task_spec)

        return {
            "status": "success",
            "operation": "create_scheduled_task",
            "task_name": task_name,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "action_type": action_type,
            "schedule_type": schedule_type,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_scheduled_task(
        task_name: str,
        enabled: bool | None = None,
        new_name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing scheduled task.

        Args:
            task_name: Name of the scheduled task to update.
            enabled: Set to True to enable or False to disable the task,
                or None to leave unchanged.
            new_name: New name for the task, or None to leave unchanged.
            description: New description for the task, or None to leave unchanged.
        """
        logger.info(
            "update_scheduled_task",
            task_name=task_name,
            enabled=enabled,
            new_name=new_name,
            description=description,
        )

        manager = client.content.scheduledTaskManager
        if manager is None:
            return {"status": "error", "error": "Scheduled task manager not available"}

        task_obj = _find_scheduled_task(client, task_name)
        if task_obj is None:
            return {"status": "error", "error": f"Scheduled task '{task_name}' not found"}

        info = task_obj.info
        spec = vim.scheduler.ScheduledTaskSpec(
            name=new_name if new_name is not None else info.name,
            description=description if description is not None else getattr(info, "description", ""),
            enabled=enabled if enabled is not None else getattr(info, "enabled", True),
            scheduler=info.scheduler,
            action=info.action,
            notification=getattr(info, "notification", ""),
        )

        task_obj.ReconfigureScheduledTask(spec=spec)

        return {
            "status": "success",
            "operation": "update_scheduled_task",
            "task_name": task_name,
            "enabled": enabled,
            "new_name": new_name,
            "description": description,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_scheduled_task_detail(task_name: str) -> dict[str, Any]:
        """Get full details of a scheduled task including schedule, last run, and next run times.

        Args:
            task_name: Name of the scheduled task.
        """
        logger.info("get_scheduled_task_detail", task_name=task_name)

        task_obj = _find_scheduled_task(client, task_name)
        if task_obj is None:
            return {"status": "error", "error": f"Scheduled task '{task_name}' not found"}

        info = task_obj.info

        scheduler = getattr(info, "scheduler", None)
        scheduler_detail: dict[str, Any] = {}
        if scheduler is not None:
            scheduler_detail["type"] = type(scheduler).__name__
            for attr in ("hour", "minute", "interval", "day", "runAt",
                         "sunday", "monday", "tuesday", "wednesday",
                         "thursday", "friday", "saturday"):
                val = getattr(scheduler, attr, None)
                if val is not None:
                    scheduler_detail[attr] = str(val) if not isinstance(val, (int, bool)) else val

        action = getattr(info, "action", None)
        action_detail: dict[str, Any] = {}
        if action is not None:
            action_detail["type"] = type(action).__name__
            action_detail["name"] = getattr(action, "name", None)
            raw_args = getattr(action, "argument", None)
            if raw_args:
                action_detail["argument"] = [getattr(a, "value", str(a)) for a in raw_args]

        last_run_time = getattr(info, "lastModifiedTime", None)
        next_run_time = getattr(info, "nextRunTime", None)
        active_task = getattr(info, "activeTask", None)

        return {
            "status": "success",
            "task_name": task_name,
            "description": getattr(info, "description", None),
            "enabled": getattr(info, "enabled", None),
            "notification": getattr(info, "notification", None),
            "scheduler": scheduler_detail,
            "action": action_detail,
            "last_modified_time": str(last_run_time) if last_run_time else None,
            "next_run_time": str(next_run_time) if next_run_time else None,
            "active_task": str(active_task) if active_task else None,
        }
