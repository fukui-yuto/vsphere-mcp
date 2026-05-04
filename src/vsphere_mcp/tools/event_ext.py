from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_entity_obj(client: VSphereClient, entity_type: str, entity_name: str) -> Any | None:
    """Find a managed object by entity type and name."""
    type_map: dict[str, Any] = {
        "vm": vim.VirtualMachine,
        "host": vim.HostSystem,
        "datastore": vim.Datastore,
        "cluster": vim.ClusterComputeResource,
        "datacenter": vim.Datacenter,
    }
    vim_type = type_map.get(entity_type)
    if vim_type is None:
        return None
    items = collect_properties(client, vim_type, ["name"])
    for item in items:
        if item.get("name") == entity_name:
            return item["_obj"]
    return None


def register_event_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def post_custom_event(entity_type: str, entity_name: str, message: str) -> dict[str, Any]:
        """Post a custom user event to vCenter for a specific entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster', 'datacenter').
            entity_name: Name of the entity to associate the event with.
            message: Custom message to include in the event.
        """
        logger.info("post_custom_event", entity_type=entity_type, entity_name=entity_name)
        entity_obj = _find_entity_obj(client, entity_type, entity_name)
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        event_manager = client.content.eventManager
        event = vim.event.GeneralUserEvent()
        event.message = message
        event.userName = ""

        if isinstance(entity_obj, vim.VirtualMachine):
            vm_ref = vim.event.VmEventArgument()
            vm_ref.vm = entity_obj
            event.vm = vm_ref
        elif isinstance(entity_obj, vim.HostSystem):
            host_ref = vim.event.HostEventArgument()
            host_ref.host = entity_obj
            event.host = host_ref

        try:
            event_manager.PostEvent(eventToPost=event)
        except Exception as e:
            return {"status": "error", "error": f"Failed to post event: {e}"}

        return {
            "status": "success",
            "operation": "post_custom_event",
            "entity_type": entity_type,
            "entity_name": entity_name,
            "message": message,
        }

    @mcp.tool()
    @handle_tool_errors
    def query_events_by_entity(
        entity_type: str,
        entity_name: str,
        max_count: int = 50,
        event_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Query vCenter events for a specific entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster', 'datacenter').
            entity_name: Name of the entity to query events for.
            max_count: Maximum number of events to return (default 50).
            event_types: Optional list of event type class names to filter by.
        """
        logger.info("query_events_by_entity", entity_type=entity_type, entity_name=entity_name)
        entity_obj = _find_entity_obj(client, entity_type, entity_name)
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        event_manager = client.content.eventManager
        filter_spec = vim.event.EventFilterSpec()
        filter_spec.entity = vim.event.EventFilterSpec.ByEntity(
            entity=entity_obj,
            recursion=vim.event.EventFilterSpec.RecursionOption.self,
        )
        if event_types is not None and len(event_types) > 0:
            filter_spec.type = event_types

        try:
            collector = event_manager.CreateCollectorForEvents(filter=filter_spec)
        except Exception as e:
            return {"status": "error", "error": f"Failed to create event collector: {e}"}

        try:
            collector.SetCollectorPageSize(max_count)
            events_raw = collector.latestPage
        except Exception as e:
            return {"status": "error", "error": f"Failed to query events: {e}"}
        finally:
            try:
                collector.DestroyCollector()
            except Exception:
                pass

        events: list[dict[str, Any]] = []
        for ev in events_raw or []:
            events.append(
                {
                    "key": ev.key,
                    "event_type": type(ev).__name__,
                    "created_time": str(ev.createdTime) if ev.createdTime else None,
                    "message": (
                        ev.fullFormattedMessage if hasattr(ev, "fullFormattedMessage") else str(ev)
                    ),
                    "user": ev.userName if hasattr(ev, "userName") else None,
                }
            )

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "total": len(events),
            "events": events,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def duplicate_customization_spec(source_name: str, new_name: str) -> dict[str, Any]:
        """Duplicate an existing guest OS customization spec with a new name.

        Args:
            source_name: Name of the customization spec to duplicate.
            new_name: Name for the duplicated customization spec.
        """
        logger.info("duplicate_customization_spec", source_name=source_name, new_name=new_name)
        spec_manager = client.content.customizationSpecManager
        try:
            spec_manager.DuplicateCustomizationSpec(name=source_name, newName=new_name)
        except Exception as e:
            return {"status": "error", "error": f"Failed to duplicate spec '{source_name}': {e}"}
        return {
            "status": "success",
            "operation": "duplicate_customization_spec",
            "source_name": source_name,
            "new_name": new_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def rename_customization_spec(old_name: str, new_name: str) -> dict[str, Any]:
        """Rename an existing guest OS customization spec.

        Args:
            old_name: Current name of the customization spec.
            new_name: New name for the customization spec.
        """
        logger.info("rename_customization_spec", old_name=old_name, new_name=new_name)
        spec_manager = client.content.customizationSpecManager
        try:
            spec_manager.RenameCustomizationSpec(name=old_name, newName=new_name)
        except Exception as e:
            return {"status": "error", "error": f"Failed to rename spec '{old_name}': {e}"}
        return {
            "status": "success",
            "operation": "rename_customization_spec",
            "old_name": old_name,
            "new_name": new_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def export_customization_spec_xml(spec_name: str) -> dict[str, Any]:
        """Export a guest OS customization spec as an XML string.

        Args:
            spec_name: Name of the customization spec to export.
        """
        logger.info("export_customization_spec_xml", spec_name=spec_name)
        spec_manager = client.content.customizationSpecManager
        try:
            item = spec_manager.GetCustomizationSpec(name=spec_name)
            xml_content = spec_manager.CustomizationSpecItemToXml(item=item)
        except Exception as e:
            return {"status": "error", "error": f"Failed to export spec '{spec_name}': {e}"}
        return {
            "spec_name": spec_name,
            "xml": xml_content,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_performance_interval(
        interval_id: int,
        length: int = 0,
        level: int = 0,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Update a performance collection interval setting in vCenter.

        Args:
            interval_id: ID of the performance interval to update (e.g. 1=realtime, 2=5min, 3=30min, 4=2hr, 5=1day).
            length: Retention period in seconds (0 = use current value).
            level: Collection level 1-4 (0 = use current value).
            enabled: Whether the interval is enabled (default True).
        """
        logger.info(
            "update_performance_interval",
            interval_id=interval_id,
            length=length,
            level=level,
            enabled=enabled,
        )
        perf_manager = client.content.perfManager
        if perf_manager is None:
            return {"status": "error", "error": "Performance manager not available"}

        existing_intervals = perf_manager.historicalInterval or []
        target_interval = None
        for interval in existing_intervals:
            if interval.key == interval_id:
                target_interval = interval
                break

        if target_interval is None:
            return {"status": "error", "error": f"Performance interval with id {interval_id} not found"}

        updated_interval = vim.PerformanceManager.IntervalDefinition()
        updated_interval.key = interval_id
        updated_interval.samplingPeriod = target_interval.samplingPeriod
        updated_interval.name = target_interval.name
        updated_interval.length = length if length > 0 else target_interval.length
        updated_interval.level = level if level > 0 else target_interval.level
        updated_interval.enabled = enabled

        try:
            perf_manager.UpdatePerfInterval(interval=updated_interval)
        except Exception as e:
            return {"status": "error", "error": f"Failed to update performance interval: {e}"}

        return {
            "status": "success",
            "operation": "update_performance_interval",
            "interval_id": interval_id,
            "length": updated_interval.length,
            "level": updated_interval.level,
            "enabled": enabled,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_composite_performance(
        entity_type: str,
        entity_name: str,
        metric_id: str,
        interval_id: int = 300,
    ) -> dict[str, Any]:
        """Get composite performance data for an entity, including child entity roll-ups.

        Args:
            entity_type: Type of entity ('vm', 'host', 'cluster').
            entity_name: Name of the entity to query.
            metric_id: Performance counter key string (e.g. 'cpu.usage.average').
            interval_id: Sampling interval in seconds (default 300).
        """
        logger.info(
            "get_composite_performance",
            entity_type=entity_type,
            entity_name=entity_name,
            metric_id=metric_id,
        )
        perf_manager = client.content.perfManager
        if perf_manager is None:
            return {"status": "error", "error": "Performance manager not available"}

        entity_obj = _find_entity_obj(client, entity_type, entity_name)
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        counter_map: dict[str, int] = {}
        for counter in perf_manager.perfCounter or []:
            key = f"{counter.groupInfo.key}.{counter.nameInfo.key}.{counter.rollupType}"
            counter_map[key] = counter.key

        counter_id = counter_map.get(metric_id)
        if counter_id is None:
            return {"status": "error", "error": f"Performance counter '{metric_id}' not found"}

        metric = vim.PerformanceManager.MetricId(counterId=counter_id, instance="")
        query_spec = vim.PerformanceManager.QuerySpec(
            entity=entity_obj,
            metricId=[metric],
            intervalId=interval_id,
            maxSample=1,
        )

        try:
            result = perf_manager.QueryPerfComposite(querySpec=query_spec)
        except Exception as e:
            return {"status": "error", "error": f"Failed to query composite performance: {e}"}

        entity_value = None
        child_values: list[dict[str, Any]] = []

        if result:
            if result.entity and result.entity.value:
                for val in result.entity.value:
                    samples = list(val.value) if val.value else []
                    entity_value = {
                        "counter_id": val.id.counterId,
                        "instance": val.id.instance,
                        "latest": samples[-1] if samples else None,
                    }
            for child in result.childEntity or []:
                child_entry: dict[str, Any] = {"entity": str(child.entity)}
                for val in child.value or []:
                    samples = list(val.value) if val.value else []
                    child_entry["latest"] = samples[-1] if samples else None
                child_values.append(child_entry)

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "metric_id": metric_id,
            "entity_value": entity_value,
            "child_count": len(child_values),
            "child_values": child_values,
        }

    @mcp.tool()
    @handle_tool_errors
    def acquire_clone_ticket() -> dict[str, Any]:
        """Acquire a clone ticket for the current vCenter session.

        Clone tickets can be used to clone the current session without re-authenticating.
        """
        logger.info("acquire_clone_ticket")
        session_manager = client.content.sessionManager
        try:
            ticket = session_manager.AcquireCloneTicket()
        except Exception as e:
            return {"status": "error", "error": f"Failed to acquire clone ticket: {e}"}
        return {"status": "success", "clone_ticket": ticket}

    @mcp.tool()
    @handle_tool_errors
    def get_current_session_info() -> dict[str, Any]:
        """Get information about the current vCenter session."""
        logger.info("get_current_session_info")
        session_manager = client.content.sessionManager
        current = session_manager.currentSession
        if current is None:
            return {"status": "error", "error": "No current session available"}
        return {
            "session_key": current.key if hasattr(current, "key") else None,
            "user_name": current.userName if hasattr(current, "userName") else None,
            "full_name": current.fullName if hasattr(current, "fullName") else None,
            "login_time": str(current.loginTime) if hasattr(current, "loginTime") else None,
            "last_active_time": str(current.lastActiveTime) if hasattr(current, "lastActiveTime") else None,
            "locale": current.locale if hasattr(current, "locale") else None,
            "message_locale": current.messageLocale if hasattr(current, "messageLocale") else None,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_alarm_state(entity_type: str, entity_name: str) -> dict[str, Any]:
        """Get triggered alarm states for a specific entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster', 'datacenter').
            entity_name: Name of the entity to get alarm states for.
        """
        logger.info("get_alarm_state", entity_type=entity_type, entity_name=entity_name)
        alarm_manager = client.content.alarmManager
        if alarm_manager is None:
            return {"status": "error", "error": "Alarm manager not available"}

        entity_obj = _find_entity_obj(client, entity_type, entity_name)
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        try:
            alarm_states = alarm_manager.GetAlarmState(entity=entity_obj)
        except Exception as e:
            return {"status": "error", "error": f"Failed to get alarm states: {e}"}

        states: list[dict[str, Any]] = []
        for state in alarm_states or []:
            states.append(
                {
                    "alarm": (
                        state.alarm.info.name
                        if hasattr(state, "alarm") and hasattr(state.alarm, "info")
                        else str(state.alarm)
                    ),
                    "entity": (
                        state.entity.name
                        if hasattr(state, "entity") and hasattr(state.entity, "name")
                        else str(state.entity)
                    ),
                    "status": str(state.overallStatus),
                    "time": str(state.time) if hasattr(state, "time") else None,
                    "acknowledged": state.acknowledged if hasattr(state, "acknowledged") else None,
                }
            )

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "total": len(states),
            "alarm_states": states,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_alarm_status(
        entity_type: str,
        entity_name: str,
        alarm_moref: str,
        status: str = "green",
    ) -> dict[str, Any]:
        """Set the acknowledged status of a triggered alarm on an entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster', 'datacenter').
            entity_name: Name of the entity the alarm is triggered on.
            alarm_moref: Managed object reference ID of the alarm (e.g. 'alarm-10').
            status: Alarm status to set: 'green', 'yellow', or 'red' (default 'green').
        """
        logger.info(
            "set_alarm_status",
            entity_type=entity_type,
            entity_name=entity_name,
            alarm_moref=alarm_moref,
            status=status,
        )
        valid_statuses = ("green", "yellow", "red")
        if status not in valid_statuses:
            return {"status": "error", "error": f"status must be one of: {', '.join(valid_statuses)}"}

        alarm_manager = client.content.alarmManager
        if alarm_manager is None:
            return {"status": "error", "error": "Alarm manager not available"}

        entity_obj = _find_entity_obj(client, entity_type, entity_name)
        if entity_obj is None:
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        alarm_obj = None
        try:
            all_alarms = alarm_manager.GetAlarm(entity=client.content.rootFolder)
            for alarm in all_alarms or []:
                if alarm._moId == alarm_moref:
                    alarm_obj = alarm
                    break
        except Exception as e:
            return {"status": "error", "error": f"Failed to look up alarm '{alarm_moref}': {e}"}

        if alarm_obj is None:
            return {"status": "error", "error": f"Alarm '{alarm_moref}' not found"}

        try:
            alarm_manager.SetAlarmStatus(alarm=alarm_obj, entity=entity_obj, status=status)
        except Exception as e:
            return {"status": "error", "error": f"Failed to set alarm status: {e}"}

        return {
            "status": "success",
            "operation": "set_alarm_status",
            "entity_type": entity_type,
            "entity_name": entity_name,
            "alarm_moref": alarm_moref,
            "new_status": status,
        }

    @mcp.tool()
    @handle_tool_errors
    def decode_license_key(license_key: str) -> dict[str, Any]:
        """Decode a vSphere license key to retrieve its properties and features.

        Args:
            license_key: The license key string to decode.
        """
        logger.info("decode_license_key")
        license_manager = client.content.licenseManager
        if license_manager is None:
            return {"status": "error", "error": "License manager not available"}
        try:
            info = license_manager.DecodeLicense(licenseKey=license_key)
        except Exception as e:
            return {"status": "error", "error": f"Failed to decode license key: {e}"}
        if info is None:
            return {"status": "error", "error": "License decode returned no result"}

        properties: list[dict[str, Any]] = []
        for prop in getattr(info, "properties", []) or []:
            properties.append({"key": prop.key, "value": str(prop.value)})

        return {
            "name": getattr(info, "name", None),
            "product_name": getattr(info, "productName", None),
            "product_version": getattr(info, "productVersion", None),
            "total": getattr(info, "total", None),
            "edition_key": getattr(info, "editionKey", None),
            "license_key": license_key,
            "properties": properties,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_license_usage() -> dict[str, Any]:
        """Get current vCenter license usage statistics."""
        logger.info("get_license_usage")
        license_manager = client.content.licenseManager
        if license_manager is None:
            return {"status": "error", "error": "License manager not available"}
        try:
            usage = license_manager.QueryLicenseUsage(host=None)
        except Exception as e:
            return {"status": "error", "error": f"Failed to query license usage: {e}"}
        if usage is None:
            return {"status": "error", "error": "License usage query returned no result"}

        source_available: list[dict[str, Any]] = []
        for avail in getattr(usage, "sourceAvailable", []) or []:
            source_available.append(
                {
                    "key": getattr(avail, "key", None),
                    "total": getattr(avail, "total", None),
                    "used": getattr(avail, "used", None),
                    "unit": getattr(avail, "unit", None),
                }
            )

        reserved: list[dict[str, Any]] = []
        for res in getattr(usage, "reserved", []) or []:
            reserved.append(
                {
                    "key": getattr(res, "key", None),
                    "total": getattr(res, "total", None),
                    "used": getattr(res, "used", None),
                    "unit": getattr(res, "unit", None),
                }
            )

        return {
            "source_available": source_available,
            "reserved": reserved,
        }
