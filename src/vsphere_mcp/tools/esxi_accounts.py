from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm, wait_for_task

logger = get_logger(__name__)


def register_esxi_accounts_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def create_esxi_local_user(
        host_name: str,
        username: str,
        password: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a local user account on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            username: Username for the new account.
            password: Password for the new account.
            description: Optional description for the account.
        """
        logger.info("create_esxi_local_user", host_name=host_name, username=username)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        account_manager = getattr(cm, "accountManager", None)
        if account_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        try:
            user_spec = vim.host.LocalAccountManager.PosixAccountSpecification(
                id=username,
                password=password,
                description=description,
                shellAccess=False,
            )
        except Exception:
            user_spec = vim.host.LocalAccountManager.AccountSpecification(
                id=username,
                password=password,
                description=description,
            )

        account_manager.CreateUser(user=user_spec)

        return {
            "status": "success",
            "operation": "create_esxi_local_user",
            "host_name": host_name,
            "username": username,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_esxi_local_user(host_name: str, username: str) -> dict[str, Any]:
        """Remove a local user account from an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            username: Username of the account to remove.
        """
        logger.info("remove_esxi_local_user", host_name=host_name, username=username)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        account_manager = getattr(cm, "accountManager", None)
        if account_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        account_manager.RemoveUser(userName=username)

        return {
            "status": "success",
            "operation": "remove_esxi_local_user",
            "host_name": host_name,
            "username": username,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def update_esxi_local_user(
        host_name: str,
        username: str,
        password: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """Update an existing local user account on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            username: Username of the account to update.
            password: New password (leave empty to keep existing password).
            description: New description (leave empty to keep existing description).
        """
        logger.info("update_esxi_local_user", host_name=host_name, username=username)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        account_manager = getattr(cm, "accountManager", None)
        if account_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        try:
            user_spec = vim.host.LocalAccountManager.PosixAccountSpecification(
                id=username,
                password=password if password else None,
                description=description,
            )
        except Exception:
            user_spec = vim.host.LocalAccountManager.AccountSpecification(
                id=username,
                password=password if password else None,
                description=description,
            )

        account_manager.UpdateUser(user=user_spec)

        return {
            "status": "success",
            "operation": "update_esxi_local_user",
            "host_name": host_name,
            "username": username,
            "password_changed": bool(password),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def join_esxi_to_domain(
        host_name: str,
        domain_name: str,
        username: str,
        password: str,
    ) -> dict[str, Any]:
        """Join an ESXi host to an Active Directory domain.

        Args:
            host_name: Name of the ESXi host.
            domain_name: Fully-qualified domain name (e.g. 'corp.example.com').
            username: Domain administrator username with permission to join computers.
            password: Password for the domain administrator account.
        """
        logger.info("join_esxi_to_domain", host_name=host_name, domain_name=domain_name, username=username)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        auth_manager = getattr(cm, "authenticationManager", None)
        if auth_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        ad_auth = None
        for info in getattr(auth_manager, "supportedStore", None) or []:
            if isinstance(info, vim.host.ActiveDirectoryAuthentication):
                ad_auth = info
                break

        if ad_auth is None:
            for store in getattr(auth_manager, "authStore", None) or []:
                if isinstance(store, vim.host.ActiveDirectoryAuthentication):
                    ad_auth = store
                    break

        if ad_auth is None:
            return {"status": "error", "error": "ActiveDirectoryAuthentication not available on this host"}

        join_method = getattr(ad_auth, "JoinDomain_Task", None)
        if join_method is None:
            return {"status": "error", "error": "JoinDomain_Task not available on this host"}

        task = join_method(domainName=domain_name, userName=username, password=password)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to join domain")}

        return {
            "status": "success",
            "operation": "join_esxi_to_domain",
            "host_name": host_name,
            "domain_name": domain_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def leave_esxi_domain(host_name: str, force: bool = False) -> dict[str, Any]:
        """Remove an ESXi host from its current Active Directory domain.

        Args:
            host_name: Name of the ESXi host.
            force: If True, force removal even if the host cannot contact the domain controller.
        """
        logger.info("leave_esxi_domain", host_name=host_name, force=force)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        auth_manager = getattr(cm, "authenticationManager", None)
        if auth_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        ad_auth = None
        for store in getattr(auth_manager, "authStore", None) or []:
            if isinstance(store, vim.host.ActiveDirectoryAuthentication):
                ad_auth = store
                break

        if ad_auth is None:
            return {"status": "error", "error": "ActiveDirectoryAuthentication not available on this host"}

        leave_method = getattr(ad_auth, "LeaveCurrentDomain_Task", None)
        if leave_method is None:
            return {"status": "error", "error": "LeaveCurrentDomain_Task not available on this host"}

        task = leave_method(force=force)
        result = wait_for_task(task)

        if result["status"] != "success":
            return {"status": "error", "error": result.get("message", "Failed to leave domain")}

        return {
            "status": "success",
            "operation": "leave_esxi_domain",
            "host_name": host_name,
            "force": force,
        }
