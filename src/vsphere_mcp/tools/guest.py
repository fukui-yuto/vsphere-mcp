from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm

logger = get_logger(__name__)


def register_guest_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def execute_guest_command(
        vm_name: str,
        username: str,
        password: str,
        command: str,
        arguments: str = "",
        working_directory: str = "",
    ) -> dict[str, Any]:
        """Execute a command inside a VM's guest OS via VMware Tools.

        Requires VMware Tools running in the guest.
        """
        logger.info("execute_guest_command", vm_name=vm_name, command=command)
        found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        tools_status = str(found.get("guest.toolsStatus", ""))
        if tools_status not in ("toolsOk", "toolsOld"):
            return {
                "status": "error",
                "error": (f"VMware Tools not running on '{vm_name}' (status: {tools_status})"),
            }

        content = client.content
        guest_ops = content.guestOperationsManager
        if not guest_ops or not guest_ops.processManager:
            return {"status": "error", "error": "Guest operations not available"}

        creds = vim.vm.guest.NamePasswordAuthentication(username=username, password=password, interactiveSession=False)

        prog_spec = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=command,
            arguments=arguments,
            workingDirectory=working_directory if working_directory else None,
        )

        try:
            pid = guest_ops.processManager.StartProgramInGuest(vm=found["_obj"], auth=creds, spec=prog_spec)
            return {
                "status": "success",
                "vm_name": vm_name,
                "pid": pid,
                "command": command,
                "arguments": arguments,
                "operation": "execute_guest_command",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {
                "status": "error",
                "error": "Guest operations unavailable (VMware Tools not ready)",
            }

    @mcp.tool()
    @handle_tool_errors
    def list_guest_processes(
        vm_name: str,
        username: str,
        password: str,
    ) -> dict[str, Any]:
        """List running processes inside a VM's guest OS via VMware Tools."""
        logger.info("list_guest_processes", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        tools_status = str(found.get("guest.toolsStatus", ""))
        if tools_status not in ("toolsOk", "toolsOld"):
            return {
                "status": "error",
                "error": (f"VMware Tools not running on '{vm_name}' (status: {tools_status})"),
            }

        content = client.content
        guest_ops = content.guestOperationsManager
        if not guest_ops or not guest_ops.processManager:
            return {"status": "error", "error": "Guest operations not available"}

        creds = vim.vm.guest.NamePasswordAuthentication(username=username, password=password, interactiveSession=False)

        try:
            processes = guest_ops.processManager.ListProcessesInGuest(vm=found["_obj"], auth=creds)
            proc_list = []
            for p in processes or []:
                proc_list.append(
                    {
                        "pid": p.pid,
                        "name": p.name,
                        "owner": p.owner if hasattr(p, "owner") else None,
                        "cmd_line": p.cmdLine if hasattr(p, "cmdLine") else None,
                        "start_time": (str(p.startTime) if hasattr(p, "startTime") and p.startTime else None),
                        "exit_code": p.exitCode if hasattr(p, "exitCode") else None,
                    }
                )
            return {"vm_name": vm_name, "total": len(proc_list), "processes": proc_list}
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable"}
