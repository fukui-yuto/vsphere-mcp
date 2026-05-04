from __future__ import annotations

from typing import Any

import requests
from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_vm_with_props, handle_tool_errors, require_confirm

logger = get_logger(__name__)

_TOOLS_OK = ("toolsOk", "toolsOld")


def _check_guest_ops(client: VSphereClient, vm_name: str) -> tuple[Any | None, Any | None, str]:
    """Find VM and validate guest operations are available.

    Returns (vm_obj, guest_ops, error_message). If error_message is non-empty the
    caller should return an error dict immediately.
    """
    found = find_vm_with_props(client, vm_name, ["guest.toolsStatus"])
    if found is None:
        return None, None, f"VM '{vm_name}' not found"

    tools_status = str(found.get("guest.toolsStatus", ""))
    if tools_status not in _TOOLS_OK:
        return None, None, f"VMware Tools not running on '{vm_name}' (status: {tools_status})"

    guest_ops = client.content.guestOperationsManager
    if not guest_ops:
        return None, None, "Guest operations manager not available"

    return found["_obj"], guest_ops, ""


def register_guest_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def create_guest_temp_file(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        prefix: str = "tmp",
        suffix: str = "",
        directory_path: str = "",
    ) -> dict[str, Any]:
        """Create a temporary file inside a VM's guest OS via VMware Tools.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            prefix: Prefix for the temp file name.
            suffix: Suffix for the temp file name.
            directory_path: Directory in which to create the temp file. Uses OS default if empty.
        """
        logger.info("create_guest_temp_file", vm_name=vm_name, prefix=prefix)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        if not guest_ops.fileManager:
            return {"status": "error", "error": "Guest file manager not available"}

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            temp_path = guest_ops.fileManager.CreateTemporaryFileInGuest(
                vm=vm_obj,
                auth=auth,
                prefix=prefix,
                suffix=suffix,
                directoryPath=directory_path if directory_path else None,
            )
            return {
                "status": "success",
                "vm_name": vm_name,
                "temp_file_path": temp_path,
                "operation": "create_guest_temp_file",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    def create_guest_temp_directory(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        prefix: str = "tmp",
        suffix: str = "",
        directory_path: str = "",
    ) -> dict[str, Any]:
        """Create a temporary directory inside a VM's guest OS via VMware Tools.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            prefix: Prefix for the temp directory name.
            suffix: Suffix for the temp directory name.
            directory_path: Parent directory for the temp directory. Uses OS default if empty.
        """
        logger.info("create_guest_temp_directory", vm_name=vm_name, prefix=prefix)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        if not guest_ops.fileManager:
            return {"status": "error", "error": "Guest file manager not available"}

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            temp_path = guest_ops.fileManager.CreateTemporaryDirectoryInGuest(
                vm=vm_obj,
                auth=auth,
                prefix=prefix,
                suffix=suffix,
                directoryPath=directory_path if directory_path else None,
            )
            return {
                "status": "success",
                "vm_name": vm_name,
                "temp_directory_path": temp_path,
                "operation": "create_guest_temp_directory",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    def set_guest_file_attributes(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        file_path: str,
        owner_id: int = -1,
        group_id: int = -1,
        permissions: str = "",
    ) -> dict[str, Any]:
        """Set POSIX file attributes on a file inside a VM's guest OS via VMware Tools.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            file_path: Absolute path to the file in the guest OS.
            owner_id: POSIX owner UID. Use -1 to leave unchanged.
            group_id: POSIX group GID. Use -1 to leave unchanged.
            permissions: Octal permission string (e.g. '0644'). Leave empty to leave unchanged.
        """
        logger.info("set_guest_file_attributes", vm_name=vm_name, file_path=file_path)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        if not guest_ops.fileManager:
            return {"status": "error", "error": "Guest file manager not available"}

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            # Try POSIX attributes first; fall back to base FileAttributes for Windows guests
            file_attributes: Any
            try:
                file_attributes = vim.vm.guest.FileManager.PosixFileAttributes()
                if owner_id >= 0:
                    file_attributes.ownerId = owner_id
                if group_id >= 0:
                    file_attributes.groupId = group_id
                if permissions:
                    file_attributes.permissions = int(permissions, 8)
            except AttributeError:
                file_attributes = vim.vm.guest.FileManager.FileAttributes()

            guest_ops.fileManager.ChangeFileAttributesInGuest(
                vm=vm_obj,
                auth=auth,
                guestFilePath=file_path,
                fileAttributes=file_attributes,
            )
            return {
                "status": "success",
                "vm_name": vm_name,
                "file_path": file_path,
                "operation": "set_guest_file_attributes",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def read_guest_file_content(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        file_path: str,
    ) -> dict[str, Any]:
        """Read the content of a file from a VM's guest OS via VMware Tools.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            file_path: Absolute path to the file in the guest OS.
        """
        logger.info("read_guest_file_content", vm_name=vm_name, file_path=file_path)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        if not guest_ops.fileManager:
            return {"status": "error", "error": "Guest file manager not available"}

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            transfer_info = guest_ops.fileManager.InitiateFileTransferFromGuest(
                vm=vm_obj, auth=auth, guestFilePath=file_path
            )
            resp = requests.get(transfer_info.url, verify=False)  # noqa: S501
            resp.raise_for_status()
            return {
                "status": "success",
                "vm_name": vm_name,
                "file_path": file_path,
                "size": transfer_info.size,
                "file_content": resp.text,
                "operation": "read_guest_file_content",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def write_guest_file_content(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        file_path: str,
        content: str,
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """Write text content to a file inside a VM's guest OS via VMware Tools.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            file_path: Absolute destination path in the guest OS.
            content: Text content to write to the file.
            overwrite: If True, overwrite the file if it already exists.
        """
        logger.info("write_guest_file_content", vm_name=vm_name, file_path=file_path)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        if not guest_ops.fileManager:
            return {"status": "error", "error": "Guest file manager not available"}

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        encoded = content.encode("utf-8")
        file_size = len(encoded)
        file_attributes = vim.vm.guest.FileManager.FileAttributes()

        try:
            upload_url = guest_ops.fileManager.InitiateFileTransferToGuest(
                vm=vm_obj,
                auth=auth,
                guestFilePath=file_path,
                fileAttributes=file_attributes,
                fileSize=file_size,
                overwrite=overwrite,
            )
            resp = requests.put(upload_url, data=encoded, verify=False)  # noqa: S501
            resp.raise_for_status()
            return {
                "status": "success",
                "vm_name": vm_name,
                "file_path": file_path,
                "bytes_written": file_size,
                "overwrite": overwrite,
                "operation": "write_guest_file_content",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}

    @mcp.tool()
    @handle_tool_errors
    def get_guest_windows_registry(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        registry_path: str,
        recursive: bool = False,
    ) -> dict[str, Any]:
        """Read Windows registry keys from a guest VM via VMware Tools.

        Only available for Windows guests with VMware Tools installed.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            registry_path: Registry key path (e.g. 'HKLM\\\\SOFTWARE\\\\MyApp').
            recursive: If True, enumerate keys recursively.
        """
        logger.info("get_guest_windows_registry", vm_name=vm_name, registry_path=registry_path)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        registry_manager = getattr(guest_ops, "guestWindowsRegistryManager", None)
        if registry_manager is None:
            return {
                "status": "error",
                "error": "guestWindowsRegistryManager not available (Windows guests only)",
            }

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            keys = registry_manager.ListRegistryKeysInGuest(
                vm=vm_obj, auth=auth, keyName=registry_path, recursive=recursive
            )
            key_list: list[dict[str, Any]] = []
            for k in keys or []:
                key_list.append(
                    {
                        "key": k.key.keyName if hasattr(k, "key") and hasattr(k.key, "keyName") else str(k),
                        "class_type": k.classType if hasattr(k, "classType") else None,
                        "last_written": str(k.lastWritten) if hasattr(k, "lastWritten") and k.lastWritten else None,
                    }
                )

            values = registry_manager.ListRegistryValuesInGuest(
                vm=vm_obj, auth=auth, keyName=registry_path, expandStrings=True
            )
            value_list: list[dict[str, Any]] = []
            for v in values or []:
                value_list.append(
                    {
                        "name": v.name.valueName if hasattr(v, "name") and hasattr(v.name, "valueName") else str(v),
                        "type": v.data.__class__.__name__ if hasattr(v, "data") else None,
                        "data": str(v.data) if hasattr(v, "data") else None,
                    }
                )

            return {
                "status": "success",
                "vm_name": vm_name,
                "registry_path": registry_path,
                "keys": key_list,
                "values": value_list,
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}
        except Exception as e:
            return {"status": "error", "error": f"Registry read failed: {e}"}

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_guest_windows_registry(
        vm_name: str,
        guest_username: str,
        guest_password: str,
        key_path: str,
        value_name: str,
        value_data: str,
        value_type: str = "REG_SZ",
    ) -> dict[str, Any]:
        """Set a Windows registry value inside a guest VM via VMware Tools.

        Only available for Windows guests with VMware Tools installed.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
            key_path: Registry key path (e.g. 'HKLM\\\\SOFTWARE\\\\MyApp').
            value_name: Name of the registry value to set.
            value_data: Data to write to the registry value.
            value_type: Registry value type ('REG_SZ', 'REG_DWORD', 'REG_EXPAND_SZ', 'REG_BINARY').
        """
        logger.info(
            "set_guest_windows_registry",
            vm_name=vm_name,
            key_path=key_path,
            value_name=value_name,
            value_type=value_type,
        )
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        registry_manager = getattr(guest_ops, "guestWindowsRegistryManager", None)
        if registry_manager is None:
            return {
                "status": "error",
                "error": "guestWindowsRegistryManager not available (Windows guests only)",
            }

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            # Build the registry value based on type
            reg_value_name = vim.vm.guest.WindowsRegistryManager.RegistryValueName()
            reg_value_name.keyPath = key_path
            reg_value_name.valueName = value_name

            if value_type in ("REG_SZ", "REG_EXPAND_SZ"):
                reg_data = vim.vm.guest.WindowsRegistryManager.RegistryValueString()
                reg_data.value = value_data
                reg_data.expand = value_type == "REG_EXPAND_SZ"
            elif value_type == "REG_DWORD":
                reg_data = vim.vm.guest.WindowsRegistryManager.RegistryValueDword()
                reg_data.value = int(value_data)
            elif value_type == "REG_BINARY":
                reg_data = vim.vm.guest.WindowsRegistryManager.RegistryValueBinary()
                reg_data.value = list(bytes.fromhex(value_data))
            else:
                reg_data = vim.vm.guest.WindowsRegistryManager.RegistryValueString()
                reg_data.value = value_data
                reg_data.expand = False

            reg_value = vim.vm.guest.WindowsRegistryManager.RegistryValue()
            reg_value.name = reg_value_name
            reg_value.data = reg_data

            registry_manager.SetRegistryValueInGuest(vm=vm_obj, auth=auth, value=reg_value)

            return {
                "status": "success",
                "vm_name": vm_name,
                "key_path": key_path,
                "value_name": value_name,
                "value_type": value_type,
                "operation": "set_guest_windows_registry",
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}
        except Exception as e:
            return {"status": "error", "error": f"Registry write failed: {e}"}

    @mcp.tool()
    @handle_tool_errors
    def list_guest_mapped_aliases(
        vm_name: str,
        guest_username: str,
        guest_password: str,
    ) -> dict[str, Any]:
        """List guest OS user aliases mapped for a VM via VMware Tools alias manager.

        Args:
            vm_name: Name of the target VM.
            guest_username: Guest OS username for authentication.
            guest_password: Guest OS password for authentication.
        """
        logger.info("list_guest_mapped_aliases", vm_name=vm_name)
        vm_obj, guest_ops, err = _check_guest_ops(client, vm_name)
        if err:
            return {"status": "error", "error": err}

        alias_manager = getattr(guest_ops, "aliasManager", None)
        if alias_manager is None:
            return {"status": "error", "error": "aliasManager not available on this vCenter"}

        auth = vim.vm.guest.NamePasswordAuthentication(
            username=guest_username, password=guest_password, interactiveSession=False
        )

        try:
            aliases = alias_manager.ListGuestAliases(vm=vm_obj, auth=auth, username=guest_username)
            alias_list: list[dict[str, Any]] = []
            for a in aliases or []:
                alias_list.append(
                    {
                        "base64_cert": a.base64Cert if hasattr(a, "base64Cert") else None,
                        "aliases": [
                            {
                                "subject": str(sa.subject) if hasattr(sa, "subject") else None,
                                "comment": sa.comment if hasattr(sa, "comment") else None,
                            }
                            for sa in (a.aliases or [])
                        ]
                        if hasattr(a, "aliases")
                        else [],
                    }
                )

            return {
                "status": "success",
                "vm_name": vm_name,
                "guest_username": guest_username,
                "total": len(alias_list),
                "aliases": alias_list,
            }
        except vim.fault.InvalidGuestLogin:
            return {"status": "error", "error": "Invalid guest credentials"}
        except vim.fault.GuestOperationsUnavailable:
            return {"status": "error", "error": "Guest operations unavailable (VMware Tools not ready)"}
        except Exception as e:
            return {"status": "error", "error": f"Alias listing failed: {e}"}
