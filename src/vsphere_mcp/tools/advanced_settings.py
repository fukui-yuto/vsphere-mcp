from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    find_host_by_name,
    handle_tool_errors,
    require_confirm,
)

logger = get_logger(__name__)


def register_advanced_settings_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_esxi_advanced_settings(
        host_name: str,
        prefix: str | None = None,
    ) -> dict[str, Any]:
        """Get advanced settings for an ESXi host. Optionally filter by key prefix (e.g. 'Mem', 'Net')."""
        logger.info("get_esxi_advanced_settings", host_name=host_name, prefix=prefix)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        option_manager = host_obj.configManager.advancedOption
        if not option_manager:
            return {"status": "error", "error": f"Advanced options not available for host '{host_name}'"}

        try:
            options = option_manager.QueryOptions()
        except Exception as e:
            return {"status": "error", "error": f"Failed to query options: {e}"}

        settings = []
        for opt in options or []:
            if prefix and not opt.key.startswith(prefix):
                continue
            settings.append(
                {
                    "key": opt.key,
                    "value": str(opt.value) if opt.value is not None else None,
                }
            )

        return {
            "host_name": host_name,
            "prefix": prefix,
            "total": len(settings),
            "settings": settings,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vcenter_advanced_settings(
        prefix: str | None = None,
    ) -> dict[str, Any]:
        """Get advanced settings for vCenter Server. Optionally filter by key prefix."""
        logger.info("get_vcenter_advanced_settings", prefix=prefix)
        content = client.content
        option_manager = content.setting
        if not option_manager:
            return {"status": "error", "error": "vCenter settings not available"}

        try:
            options = option_manager.QueryOptions()
        except Exception as e:
            return {"status": "error", "error": f"Failed to query options: {e}"}

        settings = []
        for opt in options or []:
            if prefix and not opt.key.startswith(prefix):
                continue
            settings.append(
                {
                    "key": opt.key,
                    "value": str(opt.value) if opt.value is not None else None,
                }
            )

        return {
            "prefix": prefix,
            "total": len(settings),
            "settings": settings,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_esxi_advanced_setting(
        host_name: str,
        key: str,
        value: str,
    ) -> dict[str, Any]:
        """Set an advanced setting on an ESXi host. Use get_esxi_advanced_settings to see current values first."""
        logger.info("set_esxi_advanced_setting", host_name=host_name, key=key)
        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        option_manager = host_obj.configManager.advancedOption
        if not option_manager:
            return {"status": "error", "error": f"Advanced options not available for host '{host_name}'"}

        # Get current value to determine type
        try:
            current_options = option_manager.QueryOptions(name=key)
        except Exception:
            current_options = []

        if not current_options:
            return {"status": "error", "error": f"Setting '{key}' not found on host '{host_name}'"}

        current = current_options[0]
        # Convert string value to the appropriate type
        typed_value: Any = value
        if isinstance(current.value, int):
            typed_value = int(value)
        elif isinstance(current.value, float):
            typed_value = float(value)
        elif isinstance(current.value, bool):
            typed_value = value.lower() in ("true", "1", "yes")

        try:
            option_manager.UpdateOptions(changedValue=[vim.option.OptionValue(key=key, value=typed_value)])
        except Exception as e:
            return {"status": "error", "error": f"Failed to set '{key}': {e}"}

        return {
            "status": "success",
            "host_name": host_name,
            "key": key,
            "value": str(typed_value),
            "previous_value": str(current.value) if current.value is not None else None,
            "operation": "set_esxi_advanced_setting",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_vcenter_advanced_setting(
        key: str,
        value: str,
    ) -> dict[str, Any]:
        """Set an advanced setting on vCenter Server. Use get_vcenter_advanced_settings to see current values first."""
        logger.info("set_vcenter_advanced_setting", key=key)
        content = client.content
        option_manager = content.setting
        if not option_manager:
            return {"status": "error", "error": "vCenter settings not available"}

        try:
            current_options = option_manager.QueryOptions(name=key)
        except Exception:
            current_options = []

        if not current_options:
            return {"status": "error", "error": f"Setting '{key}' not found"}

        current = current_options[0]
        typed_value: Any = value
        if isinstance(current.value, int):
            typed_value = int(value)
        elif isinstance(current.value, float):
            typed_value = float(value)
        elif isinstance(current.value, bool):
            typed_value = value.lower() in ("true", "1", "yes")

        try:
            option_manager.UpdateOptions(changedValue=[vim.option.OptionValue(key=key, value=typed_value)])
        except Exception as e:
            return {"status": "error", "error": f"Failed to set '{key}': {e}"}

        return {
            "status": "success",
            "key": key,
            "value": str(typed_value),
            "previous_value": str(current.value) if current.value is not None else None,
            "operation": "set_vcenter_advanced_setting",
        }
