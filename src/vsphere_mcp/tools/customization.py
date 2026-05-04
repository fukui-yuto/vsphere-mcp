from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm, wait_for_task
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_customization_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def list_customization_specs() -> dict[str, Any]:
        """List all guest OS customization specs available in vCenter."""
        logger.info("list_customization_specs")
        spec_manager = client.content.customizationSpecManager
        info_list = spec_manager.info or []
        specs = [
            {
                "name": item.name,
                "type": item.type,
                "description": item.description,
                "last_update_time": str(item.lastUpdateTime) if item.lastUpdateTime else None,
            }
            for item in info_list
        ]
        return {
            "status": "success",
            "total": len(specs),
            "specs": specs,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_customization_spec(spec_name: str) -> dict[str, Any]:
        """Get detailed information about a specific customization spec.

        Args:
            spec_name: Name of the customization spec to retrieve.
        """
        logger.info("get_customization_spec", spec_name=spec_name)
        spec_manager = client.content.customizationSpecManager
        try:
            cust_spec = spec_manager.GetCustomizationSpec(name=spec_name)
        except Exception as e:
            return {"status": "error", "error": f"Failed to get customization spec '{spec_name}': {e}"}
        spec = cust_spec.spec
        identity = spec.identity
        identity_type = type(identity).__name__

        global_ip = spec.globalIPSettings
        dns_servers = list(global_ip.dnsServerList) if global_ip.dnsServerList else []
        dns_suffix = list(global_ip.dnsSuffixList) if global_ip.dnsSuffixList else []

        result: dict[str, Any] = {
            "status": "success",
            "name": cust_spec.info.name,
            "type": cust_spec.info.type,
            "description": cust_spec.info.description,
            "identity_type": identity_type,
            "dns_servers": dns_servers,
            "dns_suffix_list": dns_suffix,
        }

        if isinstance(identity, vim.vm.customization.LinuxPrep):
            result["hostname_type"] = type(identity.hostName).__name__
            if isinstance(identity.hostName, vim.vm.customization.FixedName):
                result["hostname"] = identity.hostName.name
            result["domain"] = identity.domain
            result["timezone"] = identity.timeZone

        elif isinstance(identity, vim.vm.customization.Sysprep):
            user_data = identity.userData
            result["computer_name_type"] = type(user_data.computerName).__name__
            if isinstance(user_data.computerName, vim.vm.customization.FixedName):
                result["computer_name"] = user_data.computerName.name
            result["organization"] = user_data.orgName
            result["full_name"] = user_data.fullName
            gui_unattended = identity.guiUnattended
            result["timezone"] = gui_unattended.timeZone
            result["auto_logon"] = gui_unattended.autoLogon
            result["auto_logon_count"] = gui_unattended.autoLogonCount

        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_linux_customization_spec(
        spec_name: str,
        hostname: str,
        domain: str,
        dns_servers: list[str],
        dns_suffix_list: list[str] | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        """Create a Linux guest OS customization spec.

        Args:
            spec_name: Name for the new customization spec.
            hostname: Fixed hostname for the guest OS.
            domain: DNS domain name for the guest.
            dns_servers: List of DNS server IP addresses.
            dns_suffix_list: Optional list of DNS search suffixes.
            timezone: Optional timezone string (e.g. "America/New_York"). Defaults to "UTC".
        """
        logger.info(
            "create_linux_customization_spec",
            spec_name=spec_name,
            hostname=hostname,
            domain=domain,
        )
        spec_manager = client.content.customizationSpecManager

        global_ip = vim.vm.customization.GlobalIPSettings(
            dnsServerList=dns_servers,
            dnsSuffixList=dns_suffix_list or [],
        )

        linux_prep = vim.vm.customization.LinuxPrep(
            hostName=vim.vm.customization.FixedName(name=hostname),
            domain=domain,
            timeZone=timezone or "UTC",
        )

        # Use DHCP for network adapter by default
        adapter_mapping = vim.vm.customization.AdapterMapping(
            adapter=vim.vm.customization.IPSettings(
                ip=vim.vm.customization.DhcpIpGenerator(),
            )
        )

        cust_spec = vim.vm.customization.Specification(
            identity=linux_prep,
            globalIPSettings=global_ip,
            nicSettingMap=[adapter_mapping],
        )

        spec_item = vim.CustomizationSpecItem(
            info=vim.CustomizationSpecInfo(
                name=spec_name,
                type="Linux",
                description="",
            ),
            spec=cust_spec,
        )

        spec_manager.CreateCustomizationSpec(item=spec_item)
        return {
            "status": "success",
            "operation": "create_linux_customization_spec",
            "spec_name": spec_name,
            "hostname": hostname,
            "domain": domain,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def create_windows_customization_spec(
        spec_name: str,
        computer_name: str,
        organization: str,
        full_name: str,
        timezone: int = 85,
        auto_logon: bool = False,
        auto_logon_count: int = 1,
    ) -> dict[str, Any]:
        """Create a Windows guest OS customization spec using Sysprep.

        Args:
            spec_name: Name for the new customization spec.
            computer_name: Fixed computer name for the Windows guest.
            organization: Organization name for Windows Sysprep.
            full_name: Full name (owner) for Windows Sysprep.
            timezone: Windows timezone integer code (default 85 = Pacific Standard Time).
            auto_logon: Whether to enable automatic logon after customization (default False).
            auto_logon_count: Number of times to auto-logon (default 1).
        """
        logger.info(
            "create_windows_customization_spec",
            spec_name=spec_name,
            computer_name=computer_name,
            organization=organization,
        )
        spec_manager = client.content.customizationSpecManager

        global_ip = vim.vm.customization.GlobalIPSettings()

        sysprep = vim.vm.customization.Sysprep(
            userData=vim.vm.customization.UserData(
                computerName=vim.vm.customization.FixedName(name=computer_name),
                orgName=organization,
                fullName=full_name,
                productId="",
            ),
            guiUnattended=vim.vm.customization.GuiUnattended(
                timeZone=timezone,
                autoLogon=auto_logon,
                autoLogonCount=auto_logon_count,
                password=None,
            ),
            identification=vim.vm.customization.Identification(),
        )

        # Use DHCP for network adapter by default
        adapter_mapping = vim.vm.customization.AdapterMapping(
            adapter=vim.vm.customization.IPSettings(
                ip=vim.vm.customization.DhcpIpGenerator(),
            )
        )

        cust_spec = vim.vm.customization.Specification(
            identity=sysprep,
            globalIPSettings=global_ip,
            nicSettingMap=[adapter_mapping],
        )

        spec_item = vim.CustomizationSpecItem(
            info=vim.CustomizationSpecInfo(
                name=spec_name,
                type="Windows",
                description="",
            ),
            spec=cust_spec,
        )

        spec_manager.CreateCustomizationSpec(item=spec_item)
        return {
            "status": "success",
            "operation": "create_windows_customization_spec",
            "spec_name": spec_name,
            "computer_name": computer_name,
            "organization": organization,
            "full_name": full_name,
            "timezone": timezone,
            "auto_logon": auto_logon,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_customization_spec(spec_name: str) -> dict[str, Any]:
        """Delete a customization spec from vCenter.

        Args:
            spec_name: Name of the customization spec to delete.
        """
        logger.info("delete_customization_spec", spec_name=spec_name)
        spec_manager = client.content.customizationSpecManager
        try:
            spec_manager.DeleteCustomizationSpec(name=spec_name)
        except Exception as e:
            return {"status": "error", "error": f"Failed to delete customization spec '{spec_name}': {e}"}
        return {
            "status": "success",
            "operation": "delete_customization_spec",
            "spec_name": spec_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def apply_customization_to_vm(vm_name: str, spec_name: str) -> dict[str, Any]:
        """Apply a customization spec to an existing virtual machine.

        The VM must be powered off or in a state that allows customization.
        The customization takes effect on the next boot.

        Args:
            vm_name: Name of the virtual machine to customize.
            spec_name: Name of the customization spec to apply.
        """
        logger.info("apply_customization_to_vm", vm_name=vm_name, spec_name=spec_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        vm_obj = found["_obj"]

        spec_manager = client.content.customizationSpecManager
        try:
            cust_spec = spec_manager.GetCustomizationSpec(name=spec_name)
        except Exception as e:
            return {"status": "error", "error": f"Failed to get customization spec '{spec_name}': {e}"}

        task = vm_obj.CustomizeVM_Task(spec=cust_spec.spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["spec_name"] = spec_name
        result["operation"] = "apply_customization_to_vm"
        return result
