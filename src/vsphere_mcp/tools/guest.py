from __future__ import annotations

from typing import Any

import requests
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
        guest_username: str,
        guest_password: str,
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

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

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
        guest_username: str,
        guest_password: str,
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

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

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

    @mcp.tool()
    @handle_tool_errors
    def list_guest_files(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        directory_path: str,
    ) -> dict[str, Any]:
        """List files in a directory inside a VM's guest OS via VMware Tools."""
        logger.info("list_guest_files", vm_name=vm_name, directory_path=directory_path)
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
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager
        result = fm.ListFilesInGuest(vm=vm_obj, auth=auth, filePath=directory_path)
        files = []
        for f in result.files or []:
            files.append(
                {
                    "path": f.path,
                    "type": f.type if hasattr(f, "type") else None,
                    "size": f.size if hasattr(f, "size") else None,
                }
            )
        return {"vm_name": vm_name, "directory_path": directory_path, "total": len(files), "files": files}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_guest_directory(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        directory_path: str,
        create_parents: bool = True,
    ) -> dict[str, Any]:
        """Create a directory inside a VM's guest OS via VMware Tools."""
        logger.info("create_guest_directory", vm_name=vm_name, directory_path=directory_path)
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
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager
        fm.MakeDirectoryInGuest(
            vm=vm_obj, auth=auth, directoryPath=directory_path, createParentDirectories=create_parents
        )
        return {
            "status": "success",
            "vm_name": vm_name,
            "directory_path": directory_path,
            "create_parents": create_parents,
            "operation": "create_guest_directory",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_guest_file(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        file_path: str,
    ) -> dict[str, Any]:
        """Delete a file inside a VM's guest OS via VMware Tools."""
        logger.info("delete_guest_file", vm_name=vm_name, file_path=file_path)
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
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager
        fm.DeleteFileInGuest(vm=vm_obj, auth=auth, filePath=file_path)
        return {
            "status": "success",
            "vm_name": vm_name,
            "file_path": file_path,
            "operation": "delete_guest_file",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def terminate_guest_process(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        pid: int,
    ) -> dict[str, Any]:
        """Terminate a process by PID inside a VM's guest OS via VMware Tools."""
        logger.info("terminate_guest_process", vm_name=vm_name, pid=pid)
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

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        pm = guest_ops.processManager
        pm.TerminateProcessInGuest(vm=vm_obj, auth=auth, pid=pid)
        return {
            "status": "success",
            "vm_name": vm_name,
            "pid": pid,
            "operation": "terminate_guest_process",
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def upgrade_vmware_tools(vm_name: str) -> dict[str, Any]:
        """Upgrade VMware Tools on a powered-on VM."""
        from vsphere_mcp.tools._base import wait_for_task

        logger.info("upgrade_vmware_tools", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["runtime.powerState"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}
        power_state = str(found.get("runtime.powerState", ""))
        if power_state != "poweredOn":
            return {"status": "error", "error": f"VM '{vm_name}' is not powered on (state: {power_state})"}
        vm_obj = found["_obj"]
        task = vm_obj.UpgradeTools_Task()
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "upgrade_vmware_tools"
        return result

    @mcp.tool()
    @handle_tool_errors
    def read_guest_environment_variables(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        names: list[str] | None = None,
    ) -> dict[str, Any]:
        """Read environment variables from a VM's guest OS via VMware Tools."""
        logger.info("read_guest_environment_variables", vm_name=vm_name, names=names)
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

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        pm = guest_ops.processManager
        env_vars = pm.ReadEnvironmentVariableInGuest(vm=vm_obj, auth=auth, names=names or [])
        parsed = {}
        for entry in env_vars or []:
            if "=" in entry:
                k, _, v = entry.partition("=")
                parsed[k] = v
            else:
                parsed[entry] = None
        return {"vm_name": vm_name, "total": len(parsed), "environment_variables": parsed}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def upload_file_to_guest(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        guest_file_path: str,
        file_content: str,
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """Upload text file content to a path inside a VM's guest OS via VMware Tools."""
        logger.info("upload_file_to_guest", vm_name=vm_name, guest_file_path=guest_file_path)
        found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        tools_status = str(found.get("guest.toolsStatus", ""))
        if tools_status not in ("toolsOk", "toolsOld"):
            return {
                "status": "error",
                "error": f"VMware Tools not running on '{vm_name}' (status: {tools_status})",
            }

        content = client.content
        guest_ops = content.guestOperationsManager
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager

        encoded = file_content.encode("utf-8")
        file_size = len(encoded)
        file_attributes = vim.vm.guest.FileManager.FileAttributes()

        try:
            upload_url = fm.InitiateFileTransferToGuest(
                vm=vm_obj,
                auth=auth,
                guestFilePath=guest_file_path,
                fileAttributes=file_attributes,
                fileSize=file_size,
                overwrite=overwrite,
            )
            resp = requests.put(upload_url, data=encoded, verify=False)  # noqa: S501
            resp.raise_for_status()
            return {
                "status": "success",
                "vm_name": vm_name,
                "guest_file_path": guest_file_path,
                "bytes_uploaded": file_size,
                "operation": "upload_file_to_guest",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    def download_file_from_guest(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        guest_file_path: str,
    ) -> dict[str, Any]:
        """Download a file from a VM's guest OS via VMware Tools. Returns content as text."""
        logger.info("download_file_from_guest", vm_name=vm_name, guest_file_path=guest_file_path)
        found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        tools_status = str(found.get("guest.toolsStatus", ""))
        if tools_status not in ("toolsOk", "toolsOld"):
            return {
                "status": "error",
                "error": f"VMware Tools not running on '{vm_name}' (status: {tools_status})",
            }

        content = client.content
        guest_ops = content.guestOperationsManager
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager

        try:
            file_transfer_info = fm.InitiateFileTransferFromGuest(
                vm=vm_obj, auth=auth, guestFilePath=guest_file_path
            )
            resp = requests.get(file_transfer_info.url, verify=False)  # noqa: S501
            resp.raise_for_status()
            return {
                "status": "success",
                "vm_name": vm_name,
                "guest_file_path": guest_file_path,
                "size": file_transfer_info.size,
                "file_content": resp.text,
                "operation": "download_file_from_guest",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def move_guest_file(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        src_path: str,
        dst_path: str,
    ) -> dict[str, Any]:
        """Move or rename a file inside a VM's guest OS via VMware Tools."""
        logger.info("move_guest_file", vm_name=vm_name, src_path=src_path, dst_path=dst_path)
        found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        tools_status = str(found.get("guest.toolsStatus", ""))
        if tools_status not in ("toolsOk", "toolsOld"):
            return {
                "status": "error",
                "error": f"VMware Tools not running on '{vm_name}' (status: {tools_status})",
            }

        content = client.content
        guest_ops = content.guestOperationsManager
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager

        try:
            fm.MoveFileInGuest(vm=vm_obj, auth=auth, srcFilePath=src_path, dstFilePath=dst_path, overwrite=True)
            return {
                "status": "success",
                "vm_name": vm_name,
                "src_path": src_path,
                "dst_path": dst_path,
                "operation": "move_guest_file",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def delete_guest_directory(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        directory_path: str,
        recursive: bool = True,
    ) -> dict[str, Any]:
        """Delete a directory inside a VM's guest OS via VMware Tools."""
        logger.info("delete_guest_directory", vm_name=vm_name, directory_path=directory_path)
        found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        tools_status = str(found.get("guest.toolsStatus", ""))
        if tools_status not in ("toolsOk", "toolsOld"):
            return {
                "status": "error",
                "error": f"VMware Tools not running on '{vm_name}' (status: {tools_status})",
            }

        content = client.content
        guest_ops = content.guestOperationsManager
        if not guest_ops or not guest_ops.fileManager:
            return {"status": "error", "error": "Guest operations not available"}

        vm_obj = found["_obj"]
        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )
        fm = guest_ops.fileManager

        try:
            fm.DeleteDirectoryInGuest(vm=vm_obj, auth=auth, directoryPath=directory_path, recursive=recursive)
            return {
                "status": "success",
                "vm_name": vm_name,
                "directory_path": directory_path,
                "recursive": recursive,
                "operation": "delete_guest_directory",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    def get_guest_network_info(vm_name: str) -> dict[str, Any]:
        """Get network interface information reported by VMware Tools for a guest VM."""
        logger.info("get_guest_network_info", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["guest.net", "guest.ipAddress", "guest.hostName"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        vm_obj = found["_obj"]
        guest = vm_obj.guest

        nics = []
        for nic in guest.net or []:
            ip_addresses = list(nic.ipAddress) if hasattr(nic, "ipAddress") and nic.ipAddress else []
            nics.append(
                {
                    "network": nic.network if hasattr(nic, "network") else None,
                    "mac_address": nic.macAddress if hasattr(nic, "macAddress") else None,
                    "connected": nic.connected if hasattr(nic, "connected") else None,
                    "ip_addresses": ip_addresses,
                    "ip_config": (
                        {
                            "dhcp": (
                                nic.ipConfig.dhcp.ipv4.enable
                                if hasattr(nic, "ipConfig")
                                and nic.ipConfig
                                and hasattr(nic.ipConfig, "dhcp")
                                and nic.ipConfig.dhcp
                                and hasattr(nic.ipConfig.dhcp, "ipv4")
                                else None
                            )
                        }
                        if hasattr(nic, "ipConfig") and nic.ipConfig
                        else None
                    ),
                    "dns_config": (
                        {
                            "host_name": nic.dnsConfig.hostName if hasattr(nic.dnsConfig, "hostName") else None,
                            "domain_name": nic.dnsConfig.domainName if hasattr(nic.dnsConfig, "domainName") else None,
                            "ip_addresses": (
                                list(nic.dnsConfig.ipAddress) if hasattr(nic.dnsConfig, "ipAddress") else []
                            ),
                        }
                        if hasattr(nic, "dnsConfig") and nic.dnsConfig
                        else None
                    ),
                }
            )

        return {
            "vm_name": vm_name,
            "hostname": guest.hostName if hasattr(guest, "hostName") else None,
            "primary_ip": guest.ipAddress if hasattr(guest, "ipAddress") else None,
            "total_nics": len(nics),
            "nics": nics,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_guest_os_info(vm_name: str) -> dict[str, Any]:
        """Get detailed guest OS information reported by VMware Tools for a VM."""
        logger.info("get_guest_os_info", vm_name=vm_name)
        found = find_vm_with_props(
            client,
            vm_name,
            [
                "guest.guestFullName",
                "guest.hostName",
                "guest.ipAddress",
                "guest.toolsStatus",
                "guest.toolsVersion",
                "guest.guestId",
                "guest.guestState",
            ],
        )
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        return {
            "vm_name": vm_name,
            "guest_full_name": found.get("guest.guestFullName"),
            "guest_id": found.get("guest.guestId"),
            "hostname": found.get("guest.hostName"),
            "ip_address": found.get("guest.ipAddress"),
            "guest_state": str(found.get("guest.guestState", "")),
            "tools_status": str(found.get("guest.toolsStatus", "")),
            "tools_version": found.get("guest.toolsVersion"),
        }
