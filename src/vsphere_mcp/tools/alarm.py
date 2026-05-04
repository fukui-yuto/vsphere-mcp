from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_entity(client: VSphereClient, entity_type: str, entity_name: str | None) -> Any | None:
    """Return a managed object for the given entity type and name."""
    content = client.content
    if entity_name is None:
        return content.rootFolder

    type_map: dict[str, Any] = {
        "vm": vim.VirtualMachine,
        "host": vim.HostSystem,
        "datastore": vim.Datastore,
        "cluster": vim.ClusterComputeResource,
    }
    vim_type = type_map.get(entity_type)
    if vim_type is None:
        return None

    items = collect_properties(client, vim_type, ["name"])
    for item in items:
        if item.get("name") == entity_name:
            return item["_obj"]
    return None


def _find_alarm_by_name(client: VSphereClient, alarm_name: str) -> Any | None:
    """Find an alarm managed object by name, searching from the root folder."""
    content = client.content
    alarm_manager = content.alarmManager
    alarms = alarm_manager.GetAlarm(entity=content.rootFolder)
    for alarm in alarms or []:
        try:
            if alarm.info.name == alarm_name:
                return alarm
        except Exception:
            continue
    return None


def register_alarm_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_alarm(
        entity_type: str,
        alarm_name: str,
        expression_type: str,
        entity_name: str | None = None,
        description: str = "",
        metric_key: str | None = None,
        operator: str = "isAbove",
        yellow_threshold: int | None = None,
        red_threshold: int | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create an alarm on a vSphere entity.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster').
            alarm_name: Name for the new alarm.
            expression_type: Type of alarm expression ('metric' or 'state').
            entity_name: Name of the entity. If None, the alarm is created on the root folder.
            description: Human-readable description of the alarm.
            metric_key: Metric key for metric-type alarms (e.g. 'cpu.usage.average').
            operator: Comparison operator for metric alarms ('isAbove' or 'isBelow').
            yellow_threshold: Warning threshold value for metric alarms.
            red_threshold: Critical threshold value for metric alarms.
            enabled: Whether the alarm is enabled after creation.
        """
        logger.info(
            "create_alarm",
            entity_type=entity_type,
            entity_name=entity_name,
            alarm_name=alarm_name,
            expression_type=expression_type,
        )

        valid_entity_types = {"vm", "host", "datastore", "cluster"}
        if entity_type not in valid_entity_types:
            return {"status": "error", "error": f"Invalid entity_type '{entity_type}'. Valid: {sorted(valid_entity_types)}"}

        valid_expression_types = {"metric", "state"}
        if expression_type not in valid_expression_types:
            return {"status": "error", "error": f"Invalid expression_type '{expression_type}'. Valid: {sorted(valid_expression_types)}"}

        entity = _find_entity(client, entity_type, entity_name)
        if entity is None:
            if entity_name is None:
                return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        if expression_type == "metric":
            if metric_key is None:
                return {"status": "error", "error": "metric_key is required for expression_type='metric'"}

            operator_map: dict[str, Any] = {
                "isAbove": vim.alarm.MetricAlarmExpression.MetricOperator.isAbove,
                "isBelow": vim.alarm.MetricAlarmExpression.MetricOperator.isBelow,
            }
            vim_operator = operator_map.get(operator)
            if vim_operator is None:
                return {"status": "error", "error": f"Invalid operator '{operator}'. Valid: {list(operator_map.keys())}"}

            metric_id = vim.PerformanceManager.MetricId(counterId=0, instance="")
            expression = vim.alarm.MetricAlarmExpression(
                metric=metric_id,
                operator=vim_operator,
                yellow=yellow_threshold if yellow_threshold is not None else 0,
                red=red_threshold if red_threshold is not None else 0,
            )
            # Override metric key string representation via comparisons
            expression.metric.counterId = 0
        else:
            # State expression: use a simple AndAlarmExpression with no sub-expressions
            expression = vim.alarm.AndAlarmExpression(expression=[])

        action = vim.alarm.AlarmTriggeringAction(
            action=vim.action.SendEmailAction(toList="", ccList="", subject="", body=""),
            transitionSpecs=[],
        )

        spec = vim.alarm.AlarmSpec(
            name=alarm_name,
            description=description,
            enabled=enabled,
            expression=expression,
            action=action,
            actionFrequency=0,
            setting=vim.alarm.AlarmSetting(
                toleranceRange=0,
                reportingFrequency=300,
            ),
        )

        content = client.content
        alarm = content.alarmManager.CreateAlarm(entity=entity, spec=spec)

        return {
            "status": "success",
            "operation": "create_alarm",
            "alarm_name": alarm_name,
            "alarm_moref": str(alarm),
            "entity_type": entity_type,
            "entity_name": entity_name,
            "enabled": enabled,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_alarm(alarm_name: str) -> dict[str, Any]:
        """Delete an alarm by name.

        Args:
            alarm_name: Name of the alarm to delete.
        """
        logger.info("delete_alarm", alarm_name=alarm_name)
        alarm = _find_alarm_by_name(client, alarm_name)
        if alarm is None:
            return {"status": "error", "error": f"Alarm '{alarm_name}' not found"}

        alarm.RemoveAlarm()
        return {
            "status": "success",
            "operation": "delete_alarm",
            "alarm_name": alarm_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def reset_alarm_status(
        entity_type: str,
        alarm_name: str,
        entity_name: str | None = None,
    ) -> dict[str, Any]:
        """Acknowledge an alarm to reset its status to green.

        Args:
            entity_type: Type of entity ('vm', 'host', 'datastore', 'cluster').
            alarm_name: Name of the alarm to acknowledge.
            entity_name: Name of the entity. If None, uses the root folder.
        """
        logger.info("reset_alarm_status", entity_type=entity_type, alarm_name=alarm_name, entity_name=entity_name)

        entity = _find_entity(client, entity_type, entity_name)
        if entity is None:
            if entity_name is None:
                return {"status": "error", "error": f"Unknown entity_type '{entity_type}'"}
            return {"status": "error", "error": f"{entity_type} '{entity_name}' not found"}

        alarm = _find_alarm_by_name(client, alarm_name)
        if alarm is None:
            return {"status": "error", "error": f"Alarm '{alarm_name}' not found"}

        content = client.content
        content.alarmManager.AcknowledgeAlarm(alarm=alarm, entity=entity)

        return {
            "status": "success",
            "operation": "reset_alarm_status",
            "alarm_name": alarm_name,
            "entity_type": entity_type,
            "entity_name": entity_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def enable_disable_alarm(alarm_name: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable an alarm.

        Args:
            alarm_name: Name of the alarm to enable or disable.
            enabled: True to enable, False to disable.
        """
        logger.info("enable_disable_alarm", alarm_name=alarm_name, enabled=enabled)

        alarm = _find_alarm_by_name(client, alarm_name)
        if alarm is None:
            return {"status": "error", "error": f"Alarm '{alarm_name}' not found"}

        # Copy existing spec and toggle enabled flag
        current_info = alarm.info
        spec = vim.alarm.AlarmSpec(
            name=current_info.name,
            description=current_info.description or "",
            enabled=enabled,
            expression=current_info.expression,
            action=current_info.action,
            actionFrequency=current_info.actionFrequency if hasattr(current_info, "actionFrequency") else 0,
            setting=current_info.setting if hasattr(current_info, "setting") else vim.alarm.AlarmSetting(
                toleranceRange=0,
                reportingFrequency=300,
            ),
        )
        alarm.ReconfigureAlarm(spec=spec)

        return {
            "status": "success",
            "operation": "enable_disable_alarm",
            "alarm_name": alarm_name,
            "enabled": enabled,
        }
