from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm

logger = get_logger(__name__)


def _get_storage_system(host_obj: Any) -> Any | None:
    """Return host storageSystem or None."""
    cm = getattr(host_obj, "configManager", None)
    if cm is None:
        return None
    return getattr(cm, "storageSystem", None)


def _find_iscsi_hba(storage_system: Any, adapter_name: str) -> Any | None:
    """Find an iSCSI HBA by device name from storage device info."""
    device_info = getattr(storage_system, "storageDeviceInfo", None)
    if device_info is None:
        return None
    for hba in getattr(device_info, "hostBusAdapter", None) or []:
        if isinstance(hba, vim.host.InternetScsiHba) and hba.device == adapter_name:
            return hba
    return None


def register_iscsi_config_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_iscsi_adapter_config(host_name: str) -> dict[str, Any]:
        """Get the full iSCSI adapter configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_iscsi_adapter_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        storage_system = _get_storage_system(host_obj)
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available on this host"}

        device_info = getattr(storage_system, "storageDeviceInfo", None)
        if device_info is None:
            return {"status": "error", "error": "storageDeviceInfo not available"}

        adapters = []
        for hba in getattr(device_info, "hostBusAdapter", None) or []:
            if not isinstance(hba, vim.host.InternetScsiHba):
                continue

            chap_auth = getattr(hba, "authenticationProperties", None)
            chap_info: dict[str, Any] | None = None
            if chap_auth is not None:
                chap_info = {
                    "chapAuthEnabled": getattr(chap_auth, "chapAuthEnabled", None),
                    "chapName": getattr(chap_auth, "chapName", None),
                    "mutualChapAuthEnabled": getattr(chap_auth, "mutualChapAuthEnabled", None),
                    "mutualChapName": getattr(chap_auth, "mutualChapName", None),
                }

            send_targets = []
            for t in getattr(hba, "configuredSendTarget", None) or []:
                send_targets.append({
                    "address": getattr(t, "address", None),
                    "port": getattr(t, "port", None),
                })

            static_targets = []
            for t in getattr(hba, "configuredStaticTarget", None) or []:
                static_targets.append({
                    "address": getattr(t, "address", None),
                    "port": getattr(t, "port", None),
                    "iScsiName": getattr(t, "iScsiName", None),
                })

            discovery_props = getattr(hba, "discoveryProperties", None)
            discovery_info: dict[str, Any] | None = None
            if discovery_props is not None:
                discovery_info = {
                    "sendTargetsDiscoveryEnabled": getattr(discovery_props, "sendTargetsDiscoveryEnabled", None),
                    "staticTargetDiscoveryEnabled": getattr(discovery_props, "staticTargetDiscoveryEnabled", None),
                }

            adapters.append({
                "device": hba.device,
                "model": getattr(hba, "model", None),
                "driver": getattr(hba, "driver", None),
                "iScsiName": getattr(hba, "iScsiName", None),
                "iScsiAlias": getattr(hba, "iScsiAlias", None),
                "status": getattr(hba, "status", None),
                "chapAuth": chap_info,
                "discoveryProperties": discovery_info,
                "sendTargets": send_targets,
                "staticTargets": static_targets,
            })

        return {
            "status": "success",
            "host_name": host_name,
            "num_adapters": len(adapters),
            "iscsi_adapters": adapters,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_iscsi_chap_auth(
        host_name: str,
        adapter_name: str,
        chap_name: str,
        chap_secret: str,
        mutual_chap_name: str | None = None,
        mutual_chap_secret: str | None = None,
    ) -> dict[str, Any]:
        """Set CHAP authentication properties on an iSCSI adapter.

        Args:
            host_name: Name of the ESXi host.
            adapter_name: iSCSI HBA device name (e.g. "vmhba65").
            chap_name: CHAP username.
            chap_secret: CHAP secret/password.
            mutual_chap_name: Mutual CHAP username (for bidirectional CHAP), or None to skip.
            mutual_chap_secret: Mutual CHAP secret (for bidirectional CHAP), or None to skip.
        """
        logger.info(
            "set_iscsi_chap_auth",
            host_name=host_name,
            adapter_name=adapter_name,
            chap_name=chap_name,
            mutual_chap_name=mutual_chap_name,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        storage_system = _get_storage_system(host_obj)
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available on this host"}

        hba = _find_iscsi_hba(storage_system, adapter_name)
        if hba is None:
            return {"status": "error", "error": f"iSCSI adapter '{adapter_name}' not found on host '{host_name}'"}

        auth_props = vim.host.InternetScsiHba.AuthenticationProperties(
            chapAuthEnabled=True,
            chapName=chap_name,
            chapSecret=chap_secret,
        )

        if mutual_chap_name is not None and mutual_chap_secret is not None:
            auth_props.mutualChapAuthEnabled = True
            auth_props.mutualChapName = mutual_chap_name
            auth_props.mutualChapSecret = mutual_chap_secret

        storage_system.UpdateInternetScsiAuthenticationProperties(
            iScsiHbaDevice=adapter_name,
            authenticationProperties=auth_props,
        )

        return {
            "status": "success",
            "operation": "set_iscsi_chap_auth",
            "host_name": host_name,
            "adapter_name": adapter_name,
            "chap_name": chap_name,
            "mutual_chap_enabled": mutual_chap_name is not None,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def add_iscsi_static_target(
        host_name: str,
        adapter_name: str,
        target_address: str,
        target_port: int = 3260,
        target_iqn: str = "",
    ) -> dict[str, Any]:
        """Add a static iSCSI target to an iSCSI adapter.

        Args:
            host_name: Name of the ESXi host.
            adapter_name: iSCSI HBA device name (e.g. "vmhba65").
            target_address: IP address or hostname of the iSCSI target.
            target_port: TCP port of the iSCSI target (default 3260).
            target_iqn: IQN of the target (e.g. "iqn.2021-01.com.example:storage"). Empty string if unknown.
        """
        logger.info(
            "add_iscsi_static_target",
            host_name=host_name,
            adapter_name=adapter_name,
            target_address=target_address,
            target_port=target_port,
            target_iqn=target_iqn,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        storage_system = _get_storage_system(host_obj)
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available on this host"}

        hba = _find_iscsi_hba(storage_system, adapter_name)
        if hba is None:
            return {"status": "error", "error": f"iSCSI adapter '{adapter_name}' not found on host '{host_name}'"}

        static_target = vim.host.InternetScsiHba.StaticTarget(
            address=target_address,
            port=target_port,
            iScsiName=target_iqn,
        )

        storage_system.AddInternetScsiStaticTargets(
            iScsiHbaDevice=adapter_name,
            targets=[static_target],
        )

        return {
            "status": "success",
            "operation": "add_iscsi_static_target",
            "host_name": host_name,
            "adapter_name": adapter_name,
            "target_address": target_address,
            "target_port": target_port,
            "target_iqn": target_iqn,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def remove_iscsi_target(
        host_name: str,
        adapter_name: str,
        target_address: str,
        target_port: int = 3260,
        static: bool = False,
    ) -> dict[str, Any]:
        """Remove an iSCSI target (send target or static target) from an iSCSI adapter.

        Args:
            host_name: Name of the ESXi host.
            adapter_name: iSCSI HBA device name (e.g. "vmhba65").
            target_address: IP address or hostname of the iSCSI target to remove.
            target_port: TCP port of the iSCSI target (default 3260).
            static: True to remove a static target, False to remove a send target (default False).
        """
        logger.info(
            "remove_iscsi_target",
            host_name=host_name,
            adapter_name=adapter_name,
            target_address=target_address,
            target_port=target_port,
            static=static,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        storage_system = _get_storage_system(host_obj)
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available on this host"}

        hba = _find_iscsi_hba(storage_system, adapter_name)
        if hba is None:
            return {"status": "error", "error": f"iSCSI adapter '{adapter_name}' not found on host '{host_name}'"}

        if static:
            target = vim.host.InternetScsiHba.StaticTarget(
                address=target_address,
                port=target_port,
            )
            storage_system.RemoveInternetScsiStaticTargets(
                iScsiHbaDevice=adapter_name,
                targets=[target],
            )
            target_type = "static"
        else:
            target = vim.host.InternetScsiHba.SendTarget(
                address=target_address,
                port=target_port,
            )
            storage_system.RemoveInternetScsiSendTargets(
                iScsiHbaDevice=adapter_name,
                targets=[target],
            )
            target_type = "send"

        return {
            "status": "success",
            "operation": "remove_iscsi_target",
            "host_name": host_name,
            "adapter_name": adapter_name,
            "target_address": target_address,
            "target_port": target_port,
            "target_type": target_type,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="low")
    def rescan_iscsi_hba(
        host_name: str,
        adapter_name: str,
    ) -> dict[str, Any]:
        """Rescan a specific iSCSI HBA on an ESXi host to discover new targets.

        Args:
            host_name: Name of the ESXi host.
            adapter_name: iSCSI HBA device name (e.g. "vmhba65").
        """
        logger.info("rescan_iscsi_hba", host_name=host_name, adapter_name=adapter_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        storage_system = _get_storage_system(host_obj)
        if storage_system is None:
            return {"status": "error", "error": "storageSystem not available on this host"}

        hba = _find_iscsi_hba(storage_system, adapter_name)
        if hba is None:
            return {"status": "error", "error": f"iSCSI adapter '{adapter_name}' not found on host '{host_name}'"}

        storage_system.RescanHba(hbaDevice=adapter_name)

        return {
            "status": "success",
            "operation": "rescan_iscsi_hba",
            "host_name": host_name,
            "adapter_name": adapter_name,
            "message": "iSCSI HBA rescan completed",
        }
