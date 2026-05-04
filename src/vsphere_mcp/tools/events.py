from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors

logger = get_logger(__name__)


def register_event_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_recent_events(
        max_count: int = 50,
        hours: int = 24,
        event_types: str | None = None,
        entity_type: str | None = None,
        entity_name: str | None = None,
    ) -> dict[str, Any]:
        """List recent vCenter events.

        Args:
            max_count: Maximum number of events to return (default 50, max 1000).
            hours: Time window in hours (default 24).
            event_types: Comma-separated keywords to filter by event type or message text.
            entity_type: Filter by entity type ('vm', 'host', 'datastore', 'cluster').
            entity_name: Name of the entity to filter events for (requires entity_type).
        """
        logger.info("list_recent_events", max_count=max_count, hours=hours)
        content = client.content
        event_manager = content.eventManager

        filter_spec = vim.event.EventFilterSpec()
        now = datetime.now(timezone.utc)
        filter_spec.time = vim.event.EventFilterSpec.ByTime(
            beginTime=now - timedelta(hours=hours),
            endTime=now,
        )

        # Entity-level filtering
        if entity_type and entity_name:
            from vsphere_mcp.utils.property_collector import collect_properties

            etype_map: dict[str, Any] = {
                "vm": vim.VirtualMachine,
                "host": vim.HostSystem,
                "datastore": vim.Datastore,
                "cluster": vim.ClusterComputeResource,
            }
            vim_type = etype_map.get(entity_type)
            if vim_type is None:
                return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}
            items = collect_properties(client, vim_type, ["name"])
            entity_obj = None
            for item in items:
                if item.get("name") == entity_name:
                    entity_obj = item["_obj"]
                    break
            if entity_obj is None:
                return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}
            filter_spec.entity = vim.event.EventFilterSpec.ByEntity(
                entity=entity_obj,
                recursion=vim.event.EventFilterSpec.RecursionOption.self,
            )

        try:
            collector = event_manager.CreateCollectorForEvents(filter=filter_spec)
        except Exception as e:
            return {"status": "error", "error": f"Failed to query events: {e}"}

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
            event_data: dict[str, Any] = {
                "key": ev.key,
                "event_type": type(ev).__name__,
                "created_time": str(ev.createdTime) if ev.createdTime else None,
                "message": (ev.fullFormattedMessage if hasattr(ev, "fullFormattedMessage") else str(ev)),
                "user": ev.userName if hasattr(ev, "userName") else None,
                "datacenter": (ev.datacenter.name if hasattr(ev, "datacenter") and ev.datacenter else None),
                "host": ev.host.name if hasattr(ev, "host") and ev.host else None,
                "vm": ev.vm.name if hasattr(ev, "vm") and ev.vm else None,
            }
            if event_types:
                keywords = [k.strip().lower() for k in event_types.split(",")]
                evt_type = event_data["event_type"].lower()
                msg = (event_data["message"] or "").lower()
                if not any(k in evt_type or k in msg for k in keywords):
                    continue
            events.append(event_data)

        return {"total": len(events), "hours": hours, "events": events}

    @mcp.tool()
    @handle_tool_errors
    def list_alarms(
        entity_type: str = "all",
        entity_name: str | None = None,
    ) -> dict[str, Any]:
        """List triggered alarms.

        Args:
            entity_type: 'all', 'host', 'vm', or 'datastore'.
            entity_name: Name of a specific entity to query alarms for.
        """
        logger.info("list_alarms", entity_type=entity_type)
        content = client.content
        alarm_manager = content.alarmManager

        if not alarm_manager:
            return {"status": "error", "error": "Alarm manager not available"}

        alarms: list[dict[str, Any]] = []
        type_map: dict[str, Any] = {
            "host": vim.HostSystem,
            "vm": vim.VirtualMachine,
            "datastore": vim.Datastore,
        }

        try:
            # Collect alarms from specific entities for broader coverage
            if entity_type != "all" and entity_type in type_map:
                from vsphere_mcp.utils.property_collector import collect_properties

                vim_type = type_map[entity_type]
                items = collect_properties(client, vim_type, ["name", "triggeredAlarmState"])
                if entity_name:
                    items = [i for i in items if i.get("name") == entity_name]
                    if not items:
                        return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}
                for item in items:
                    for state in item.get("triggeredAlarmState", []) or []:
                        alarm_data: dict[str, Any] = {
                            "alarm": (
                                state.alarm.info.name if hasattr(state.alarm, "info") else str(state.alarm)
                            ),
                            "entity": item.get("name", str(item["_obj"])),
                            "entity_type": type(item["_obj"]).__name__,
                            "status": str(state.overallStatus),
                            "time": str(state.time) if hasattr(state, "time") else None,
                            "acknowledged": state.acknowledged if hasattr(state, "acknowledged") else None,
                        }
                        alarms.append(alarm_data)
            else:
                # Fallback: query root folder for all alarm states
                alarm_states = alarm_manager.GetAlarmState(entity=content.rootFolder)
                for state in alarm_states or []:
                    alarm_data = {
                        "alarm": (
                            state.alarm.info.name if hasattr(state.alarm, "info") else str(state.alarm)
                        ),
                        "entity": (
                            state.entity.name if hasattr(state.entity, "name") else str(state.entity)
                        ),
                        "entity_type": type(state.entity).__name__,
                        "status": str(state.overallStatus),
                        "time": str(state.time) if hasattr(state, "time") else None,
                        "acknowledged": state.acknowledged if hasattr(state, "acknowledged") else None,
                    }
                    alarms.append(alarm_data)
        except Exception as e:
            return {"alarms": [], "message": f"Alarm query limited: {e}"}

        return {"total": len(alarms), "alarms": alarms}

    @mcp.tool()
    @handle_tool_errors
    def list_performance_counters(
        group_name: str | None = None,
    ) -> dict[str, Any]:
        """List all performance counters. Optionally filter by group name.

        Args:
            group_name: Filter counters by group (e.g. 'cpu', 'mem', 'disk', 'net').
        """
        logger.info("list_performance_counters", group_name=group_name)
        content = client.content
        perf_manager = content.perfManager
        if not perf_manager:
            return {"status": "error", "error": "Performance manager not available"}

        counters: list[dict[str, Any]] = []
        for counter in perf_manager.perfCounter or []:
            group_key = counter.groupInfo.key
            if group_name and group_key != group_name:
                continue
            counters.append(
                {
                    "group": group_key,
                    "name": counter.nameInfo.key,
                    "unit": counter.unitInfo.key,
                    "rollupType": str(counter.rollupType),
                    "level": counter.level,
                    "key": counter.key,
                }
            )

        return {"total": len(counters), "counters": counters}

    @mcp.tool()
    @handle_tool_errors
    def get_alarm_definitions(
        entity_type: str | None = None,
        entity_name: str | None = None,
    ) -> dict[str, Any]:
        """List alarm definitions. Optionally filter by entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster'). If omitted, uses root folder.
            entity_name: Name of the entity to get alarms for.
        """
        logger.info("get_alarm_definitions", entity_type=entity_type, entity_name=entity_name)
        content = client.content
        alarm_manager = content.alarmManager
        if not alarm_manager:
            return {"status": "error", "error": "Alarm manager not available"}

        entity = content.rootFolder
        if entity_type and entity_name:
            from vsphere_mcp.utils.property_collector import collect_properties

            type_map: dict[str, Any] = {
                "vm": vim.VirtualMachine,
                "host": vim.HostSystem,
                "datastore": vim.Datastore,
                "cluster": vim.ClusterComputeResource,
            }
            vim_type = type_map.get(entity_type)
            if vim_type is None:
                return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}
            items = collect_properties(client, vim_type, ["name"])
            found = None
            for item in items:
                if item.get("name") == entity_name:
                    found = item["_obj"]
                    break
            if found is None:
                return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}
            entity = found

        alarms_raw = alarm_manager.GetAlarm(entity=entity) or []

        alarms: list[dict[str, Any]] = []
        for alarm in alarms_raw:
            info = alarm.info
            expression_type = type(info.expression).__name__ if info.expression else None
            alarms.append(
                {
                    "name": info.name,
                    "description": info.description,
                    "enabled": info.enabled,
                    "expression_type": expression_type,
                }
            )

        return {"total": len(alarms), "alarms": alarms}

    @mcp.tool()
    @handle_tool_errors
    def get_host_system_log(
        host_name: str,
        log_key: str = "hostd",
        max_lines: int = 100,
    ) -> dict[str, Any]:
        """Browse host diagnostic log.

        Args:
            host_name: Name of the ESXi host.
            log_key: Log key to browse (default 'hostd').
            max_lines: Maximum number of lines to return (default 100).
        """
        logger.info("get_host_system_log", host_name=host_name, log_key=log_key, max_lines=max_lines)
        if max_lines <= 0 or max_lines > 1000:
            return {"status": "error", "error": "max_lines must be between 1 and 1000"}
        content = client.content
        diag_manager = content.diagnosticManager
        if not diag_manager:
            return {"status": "error", "error": "Diagnostic manager not available"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        # First call to get total line count, then fetch only the tail
        header = diag_manager.BrowseDiagnosticLog(host=host_obj, key=log_key, start=1, lines=1)
        line_end = header.lineEnd or 0
        start_line = max(1, line_end - max_lines + 1)
        log_data = diag_manager.BrowseDiagnosticLog(
            host=host_obj, key=log_key, start=start_line, lines=max_lines
        )
        lines = log_data.lineText or []

        return {
            "host_name": host_name,
            "log_key": log_key,
            "total_lines": len(lines),
            "lines": lines,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_diagnostic_log_keys(
        host_name: str,
    ) -> dict[str, Any]:
        """List available diagnostic log keys on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("list_diagnostic_log_keys", host_name=host_name)
        content = client.content
        diag_manager = content.diagnosticManager
        if not diag_manager:
            return {"status": "error", "error": "Diagnostic manager not available"}

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        descriptions = diag_manager.QueryDescriptions(host=host_obj) or []

        log_keys: list[dict[str, Any]] = []
        for desc in descriptions:
            log_keys.append(
                {
                    "key": desc.key,
                    "fileName": desc.fileName if hasattr(desc, "fileName") else None,
                    "description": desc.info.summary if hasattr(desc, "info") and desc.info else None,
                }
            )

        return {"host_name": host_name, "total": len(log_keys), "log_keys": log_keys}

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_log(key: str = "vpxd", num_lines: int = 100) -> dict[str, Any]:
        """Browse a vCenter diagnostic log by key.

        Args:
            key: Log key to browse (default 'vpxd').
            num_lines: Maximum number of lines to return from the end of the log (1-1000, default 100).
        """
        logger.info("get_vcenter_log", key=key, num_lines=num_lines)
        if num_lines <= 0 or num_lines > 1000:
            return {"status": "error", "error": "num_lines must be between 1 and 1000"}
        content = client.content
        dm = content.diagnosticManager
        if not dm:
            return {"status": "error", "error": "Diagnostic manager not available"}
        # First call to get total line count, then fetch only the tail
        header = dm.BrowseDiagnosticLog(host=None, key=key, start=1, lines=1)
        line_end = header.lineEnd or 0
        start_line = max(1, line_end - num_lines + 1)
        log = dm.BrowseDiagnosticLog(host=None, key=key, start=start_line, lines=num_lines)
        lines = log.lineText or []
        return {"key": key, "total_lines": len(lines), "lines": lines}

    @mcp.tool()
    @handle_tool_errors
    def list_vcenter_log_keys() -> dict[str, Any]:
        """List available vCenter diagnostic log keys."""
        logger.info("list_vcenter_log_keys")
        content = client.content
        dm = content.diagnosticManager
        if not dm:
            return {"status": "error", "error": "Diagnostic manager not available"}
        descriptions = dm.QueryDescriptions(host=None) or []
        log_keys: list[dict[str, Any]] = []
        for desc in descriptions:
            log_keys.append(
                {
                    "key": desc.key,
                    "fileName": desc.fileName if hasattr(desc, "fileName") else None,
                    "info": desc.info.summary if hasattr(desc, "info") and desc.info else None,
                }
            )
        return {"total": len(log_keys), "log_keys": log_keys}
