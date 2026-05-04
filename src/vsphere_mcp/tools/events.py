from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors

logger = get_logger(__name__)


def register_event_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_recent_events(
        max_count: int = 50,
        hours: int = 24,
        event_types: str | None = None,
    ) -> dict[str, Any]:
        """List recent vCenter events. Optionally filter by hours and event type keywords."""
        logger.info("list_recent_events", max_count=max_count, hours=hours)
        content = client.content
        event_manager = content.eventManager

        filter_spec = vim.event.EventFilterSpec()
        now = datetime.now(timezone.utc)
        filter_spec.time = vim.event.EventFilterSpec.ByTime(
            beginTime=now - timedelta(hours=hours),
            endTime=now,
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
    ) -> dict[str, Any]:
        """List triggered alarms. entity_type: 'all', 'host', 'vm', 'datastore'."""
        logger.info("list_alarms", entity_type=entity_type)
        content = client.content
        alarm_manager = content.alarmManager

        if not alarm_manager:
            return {"status": "error", "error": "Alarm manager not available"}

        alarms: list[dict[str, Any]] = []
        type_map = {"host": "HostSystem", "vm": "VirtualMachine", "datastore": "Datastore"}

        try:
            alarm_states = alarm_manager.GetAlarmState(entity=content.rootFolder)
            for state in alarm_states or []:
                alarm_data: dict[str, Any] = {
                    "alarm": (state.alarm.info.name if hasattr(state.alarm, "info") else str(state.alarm)),
                    "entity": (state.entity.name if hasattr(state.entity, "name") else str(state.entity)),
                    "entity_type": type(state.entity).__name__,
                    "status": str(state.overallStatus),
                    "time": str(state.time) if hasattr(state, "time") else None,
                    "acknowledged": (state.acknowledged if hasattr(state, "acknowledged") else None),
                }
                if entity_type != "all":
                    expected_type = type_map.get(entity_type, "")
                    if alarm_data["entity_type"] != expected_type:
                        continue
                alarms.append(alarm_data)
        except Exception as e:
            return {"alarms": [], "message": f"Alarm query limited: {e}"}

        return {"total": len(alarms), "alarms": alarms}
