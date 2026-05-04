from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def _find_vapp(client: VSphereClient, vapp_name: str) -> Any | None:
    """Find a vApp by name and return its managed object."""
    items = collect_properties(client, vim.VirtualApp, ["name"])
    for item in items:
        if item.get("name") == vapp_name:
            return item["_obj"]
    return None


def register_vapp_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_vapp(
        name: str,
        resource_pool_name: str,
        folder_name: str = "",
    ) -> dict[str, Any]:
        """Create a new vApp container in the specified resource pool.

        Args:
            name: Name for the new vApp.
            resource_pool_name: Name of the resource pool where the vApp will be created.
            folder_name: Optional name of the VM folder to place the vApp in.
        """
        logger.info("create_vapp", name=name, resource_pool_name=resource_pool_name)

        rp_items = collect_properties(client, vim.ResourcePool, ["name"])
        rp_obj = None
        for item in rp_items:
            if item.get("name") == resource_pool_name:
                rp_obj = item["_obj"]
                break
        if rp_obj is None:
            return {"status": "error", "error": f"Resource pool '{resource_pool_name}' not found"}

        vm_folder = None
        if folder_name:
            folder_items = collect_properties(client, vim.Folder, ["name"])
            for item in folder_items:
                if item.get("name") == folder_name:
                    vm_folder = item["_obj"]
                    break
            if vm_folder is None:
                return {"status": "error", "error": f"Folder '{folder_name}' not found"}
        else:
            # Use the default VM folder from the first datacenter
            dc_items = collect_properties(client, vim.Datacenter, ["name", "vmFolder"])
            if dc_items:
                vm_folder = dc_items[0].get("vmFolder") or dc_items[0]["_obj"].vmFolder

        res_spec = vim.ResourceConfigSpec()
        res_spec.cpuAllocation = vim.ResourceAllocationInfo()
        res_spec.cpuAllocation.reservation = 0
        res_spec.cpuAllocation.limit = -1
        res_spec.cpuAllocation.shares = vim.SharesInfo(level=vim.SharesInfo.Level.normal, shares=0)
        res_spec.memoryAllocation = vim.ResourceAllocationInfo()
        res_spec.memoryAllocation.reservation = 0
        res_spec.memoryAllocation.limit = -1
        res_spec.memoryAllocation.shares = vim.SharesInfo(level=vim.SharesInfo.Level.normal, shares=0)

        vapp_config = vim.vApp.VAppConfigSpec()

        vapp_obj = rp_obj.CreateVApp(name=name, resSpec=res_spec, configSpec=vapp_config, vmFolder=vm_folder)

        return {
            "status": "success",
            "operation": "create_vapp",
            "name": name,
            "resource_pool": resource_pool_name,
            "moref": str(vapp_obj),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def configure_vapp_start_order(
        vapp_name: str,
        vm_name: str,
        start_order: int = 1,
        start_delay: int = 0,
        start_action: str = "powerOn",
        stop_action: str = "powerOff",
        stop_delay: int = 0,
    ) -> dict[str, Any]:
        """Configure the start/stop order for a VM within a vApp.

        Args:
            vapp_name: Name of the vApp.
            vm_name: Name of the VM whose start order to configure.
            start_order: Start order index (lower numbers start first).
            start_delay: Seconds to wait after starting this VM before starting the next.
            start_action: Action taken on start ('powerOn' or 'none').
            stop_action: Action taken on stop ('powerOff', 'guestShutdown', or 'none').
            stop_delay: Seconds to wait after stopping this VM before stopping the next.
        """
        logger.info(
            "configure_vapp_start_order",
            vapp_name=vapp_name,
            vm_name=vm_name,
            start_order=start_order,
        )

        vapp_obj = _find_vapp(client, vapp_name)
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}

        vm_items = collect_properties(client, vim.VirtualMachine, ["name"])
        vm_obj = None
        for item in vm_items:
            if item.get("name") == vm_name:
                vm_obj = item["_obj"]
                break
        if vm_obj is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        entity_config = vim.vApp.EntityConfigInfo()
        entity_config.key = vm_obj
        entity_config.startOrder = start_order
        entity_config.startDelay = start_delay
        entity_config.startAction = start_action
        entity_config.stopAction = stop_action
        entity_config.stopDelay = stop_delay
        entity_config.waitingForGuest = False

        spec = vim.vApp.VAppConfigSpec()
        spec.entityConfig = [entity_config]

        vapp_obj.UpdateVAppConfig(spec=spec)

        return {
            "status": "success",
            "operation": "configure_vapp_start_order",
            "vapp_name": vapp_name,
            "vm_name": vm_name,
            "start_order": start_order,
            "start_delay": start_delay,
            "start_action": start_action,
            "stop_action": stop_action,
            "stop_delay": stop_delay,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_vapp_config(vapp_name: str) -> dict[str, Any]:
        """Get configuration details for a vApp, including product info and entity start order.

        Args:
            vapp_name: Name of the vApp.
        """
        logger.info("get_vapp_config", vapp_name=vapp_name)

        vapp_obj = _find_vapp(client, vapp_name)
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}

        cfg = vapp_obj.vAppConfig

        product_info: list[dict[str, Any]] = []
        if cfg and hasattr(cfg, "product") and cfg.product:
            for p in cfg.product:
                product_info.append(
                    {
                        "name": p.name if hasattr(p, "name") else None,
                        "vendor": p.vendor if hasattr(p, "vendor") else None,
                        "version": p.version if hasattr(p, "version") else None,
                        "full_version": p.fullVersion if hasattr(p, "fullVersion") else None,
                        "product_url": p.productUrl if hasattr(p, "productUrl") else None,
                    }
                )

        properties: list[dict[str, Any]] = []
        if cfg and hasattr(cfg, "property") and cfg.property:
            for prop in cfg.property:
                properties.append(
                    {
                        "id": prop.id if hasattr(prop, "id") else None,
                        "key": prop.key if hasattr(prop, "key") else None,
                        "label": prop.label if hasattr(prop, "label") else None,
                        "type": prop.type if hasattr(prop, "type") else None,
                        "value": prop.value if hasattr(prop, "value") else None,
                        "description": prop.description if hasattr(prop, "description") else None,
                    }
                )

        entity_configs: list[dict[str, Any]] = []
        if cfg and hasattr(cfg, "entityConfig") and cfg.entityConfig:
            for ec in cfg.entityConfig:
                entity_configs.append(
                    {
                        "start_order": ec.startOrder if hasattr(ec, "startOrder") else None,
                        "start_delay": ec.startDelay if hasattr(ec, "startDelay") else None,
                        "start_action": ec.startAction if hasattr(ec, "startAction") else None,
                        "stop_action": ec.stopAction if hasattr(ec, "stopAction") else None,
                        "stop_delay": ec.stopDelay if hasattr(ec, "stopDelay") else None,
                    }
                )

        return {
            "vapp_name": vapp_name,
            "annotation": cfg.annotation if cfg and hasattr(cfg, "annotation") else None,
            "product": product_info,
            "properties": properties,
            "entity_configs": entity_configs,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_vapp_properties(
        vapp_name: str,
        properties: dict[str, str],
    ) -> dict[str, Any]:
        """Update OVF properties for a vApp.

        Args:
            vapp_name: Name of the vApp to update.
            properties: Dictionary mapping property id to new value string.
        """
        logger.info("update_vapp_properties", vapp_name=vapp_name, properties=properties)

        vapp_obj = _find_vapp(client, vapp_name)
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}

        cfg = vapp_obj.vAppConfig
        if cfg is None or not hasattr(cfg, "property") or not cfg.property:
            return {"status": "error", "error": f"vApp '{vapp_name}' has no OVF properties defined"}

        prop_specs: list[vim.vApp.PropertySpec] = []
        existing_keys = {str(p.id): p for p in cfg.property if hasattr(p, "id")}

        for prop_id, new_value in properties.items():
            if prop_id not in existing_keys:
                return {"status": "error", "error": f"Property '{prop_id}' not found in vApp '{vapp_name}'"}
            existing_prop = existing_keys[prop_id]
            prop_info = vim.vApp.PropertyInfo()
            prop_info.key = existing_prop.key
            prop_info.id = existing_prop.id
            prop_info.value = new_value
            prop_spec = vim.vApp.PropertySpec()
            prop_spec.operation = "edit"
            prop_spec.info = prop_info
            prop_specs.append(prop_spec)

        spec = vim.vApp.VAppConfigSpec()
        spec.property = prop_specs

        vapp_obj.UpdateVAppConfig(spec=spec)

        return {
            "status": "success",
            "operation": "update_vapp_properties",
            "vapp_name": vapp_name,
            "updated_properties": list(properties.keys()),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def suspend_vapp(vapp_name: str) -> dict[str, Any]:
        """Suspend all VMs in a vApp.

        Args:
            vapp_name: Name of the vApp to suspend.
        """
        logger.info("suspend_vapp", vapp_name=vapp_name)

        vapp_obj = _find_vapp(client, vapp_name)
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}

        task = vapp_obj.SuspendVApp_Task()
        result = wait_for_task(task)
        result["vapp_name"] = vapp_name
        result["operation"] = "suspend_vapp"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def clone_vapp(
        vapp_name: str,
        new_name: str,
        target_resource_pool: str = "",
    ) -> dict[str, Any]:
        """Clone a vApp to a new vApp with a different name.

        Args:
            vapp_name: Name of the source vApp to clone.
            new_name: Name for the cloned vApp.
            target_resource_pool: Name of the resource pool for the clone. Uses the same pool if not specified.
        """
        logger.info("clone_vapp", vapp_name=vapp_name, new_name=new_name)

        vapp_obj = _find_vapp(client, vapp_name)
        if vapp_obj is None:
            return {"status": "error", "error": f"vApp '{vapp_name}' not found"}

        target_rp = None
        if target_resource_pool:
            rp_items = collect_properties(client, vim.ResourcePool, ["name"])
            for item in rp_items:
                if item.get("name") == target_resource_pool:
                    target_rp = item["_obj"]
                    break
            if target_rp is None:
                return {"status": "error", "error": f"Resource pool '{target_resource_pool}' not found"}
        else:
            # Clone to same resource pool as parent
            target_rp = vapp_obj.parent

        clone_spec = vim.vApp.CloneSpec()
        clone_spec.powerOn = False
        clone_spec.snapshot = None

        task = vapp_obj.CloneVApp_Task(name=new_name, target=target_rp, spec=clone_spec)
        result = wait_for_task(task)
        result["source_vapp"] = vapp_name
        result["new_name"] = new_name
        result["target_resource_pool"] = target_resource_pool or "(same as source)"
        result["operation"] = "clone_vapp"
        return result
