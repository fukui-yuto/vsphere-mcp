from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import (
    find_vm_with_props,
    handle_tool_errors,
    require_confirm,
    wait_for_task,
)

logger = get_logger(__name__)


def register_encryption_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_vm_encryption_state(vm_name: str) -> dict[str, Any]:
        """Get the encryption state of a virtual machine.

        Returns whether the VM is encrypted, the active key ID and provider ID,
        and the runtime crypto state string.

        Args:
            vm_name: Name of the VM.
        """
        logger.info("get_vm_encryption_state", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name, ["config.keyId", "runtime.cryptoState"])
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        key_id_obj = found.get("config.keyId")
        crypto_state = found.get("runtime.cryptoState")

        encrypted = key_id_obj is not None
        key_id = None
        provider_id = None
        if key_id_obj is not None:
            key_id = getattr(key_id_obj, "keyId", None)
            provider = getattr(key_id_obj, "providerId", None)
            if provider is not None:
                provider_id = getattr(provider, "id", None)

        return {
            "vm_name": vm_name,
            "encrypted": encrypted,
            "key_id": key_id,
            "provider_id": provider_id,
            "crypto_state": str(crypto_state) if crypto_state is not None else None,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def encrypt_vm(vm_name: str, policy_id: str | None = None) -> dict[str, Any]:
        """Encrypt a virtual machine using the default key provider.

        The VM must be powered off or meet encryption prerequisites. If a
        storage policy ID is specified it will be applied alongside the
        encryption spec.

        Args:
            vm_name: Name of the VM to encrypt.
            policy_id: Optional SPBM storage policy profile ID to apply.
        """
        logger.info("encrypt_vm", vm_name=vm_name, policy_id=policy_id)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        crypto_spec = vim.encryption.CryptoSpecEncrypt()
        config_spec = vim.vm.ConfigSpec(crypto=crypto_spec)

        if policy_id is not None:
            profile = vim.vm.DefinedProfileSpec(profileId=policy_id)
            config_spec.vmProfile = [profile]

        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "encrypt_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def decrypt_vm(vm_name: str) -> dict[str, Any]:
        """Decrypt an encrypted virtual machine.

        The VM must be powered off before decryption.

        Args:
            vm_name: Name of the VM to decrypt.
        """
        logger.info("decrypt_vm", vm_name=vm_name)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_state = found.get("runtime.powerState")
        if str(power_state) != "poweredOff":
            return {"status": "error", "error": f"VM '{vm_name}' must be powered off before decryption"}

        crypto_spec = vim.encryption.CryptoSpecDecrypt()
        config_spec = vim.vm.ConfigSpec(crypto=crypto_spec)

        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["operation"] = "decrypt_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def rekey_vm(vm_name: str, deep: bool = False) -> dict[str, Any]:
        """Re-key the encryption on a virtual machine.

        Shallow re-key (default) replaces the key-encryption key without
        re-encrypting disk data. Deep re-key fully re-encrypts all disk data
        with a new data-encryption key and is a significantly longer operation.

        Args:
            vm_name: Name of the VM.
            deep: If True, perform a deep (full disk) re-key. Default is shallow.
        """
        logger.info("rekey_vm", vm_name=vm_name, deep=deep)
        found = find_vm_with_props(client, vm_name)
        if found is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        if deep:
            crypto_spec = vim.encryption.CryptoSpecDeepRecrypt()
        else:
            crypto_spec = vim.encryption.CryptoSpecShallowRecrypt()

        config_spec = vim.vm.ConfigSpec(crypto=crypto_spec)
        task = found["_obj"].ReconfigVM_Task(spec=config_spec)
        result = wait_for_task(task)
        result["vm_name"] = vm_name
        result["rekey_type"] = "deep" if deep else "shallow"
        result["operation"] = "rekey_vm"
        return result

    @mcp.tool()
    @handle_tool_errors
    def list_key_providers() -> dict[str, Any]:
        """List configured Key Management Server (KMS) providers in vCenter.

        Returns each provider's name, server address(es), and connection status.
        Returns an empty list on systems without encryption configured.
        """
        logger.info("list_key_providers")
        si = client.si
        crypto_manager = si.content.cryptoManager

        if crypto_manager is None:
            return {
                "crypto_manager_available": False,
                "providers": [],
                "message": "CryptoManager is not available on this vCenter",
            }

        providers = []
        try:
            kmip_servers = getattr(crypto_manager, "kmipServers", None) or []
            for cluster in kmip_servers:
                cluster_info: dict[str, Any] = {
                    "provider_name": getattr(cluster, "clusterId", {}).id
                    if hasattr(cluster, "clusterId") and cluster.clusterId
                    else None,
                    "servers": [],
                }
                for server in getattr(cluster, "servers", []) or []:
                    server_info: dict[str, Any] = {
                        "address": getattr(server, "address", None),
                        "port": getattr(server, "port", None),
                        "name": getattr(server, "name", None),
                    }
                    cluster_info["servers"].append(server_info)

                status_obj = getattr(cluster, "useAsDefault", None)
                cluster_info["use_as_default"] = status_obj

                providers.append(cluster_info)
        except Exception as e:
            logger.warning("list_key_providers: failed to enumerate kmipServers", error=str(e))

        return {
            "crypto_manager_available": True,
            "provider_count": len(providers),
            "providers": providers,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_encryption_status() -> dict[str, Any]:
        """Get the overall vCenter encryption / key management status.

        Returns the CryptoManager type, default key provider, and the total
        number of configured providers.
        """
        logger.info("get_encryption_status")
        si = client.si
        crypto_manager = si.content.cryptoManager

        if crypto_manager is None:
            return {
                "crypto_manager_available": False,
                "crypto_manager_type": None,
                "default_provider": None,
                "provider_count": 0,
            }

        crypto_manager_type = type(crypto_manager).__name__

        kmip_servers = getattr(crypto_manager, "kmipServers", None) or []
        provider_count = len(kmip_servers)

        default_provider = None
        for cluster in kmip_servers:
            if getattr(cluster, "useAsDefault", False):
                if hasattr(cluster, "clusterId") and cluster.clusterId:
                    default_provider = cluster.clusterId.id
                break

        return {
            "crypto_manager_available": True,
            "crypto_manager_type": crypto_manager_type,
            "default_provider": default_provider,
            "provider_count": provider_count,
        }

    @mcp.tool()
    @handle_tool_errors
    def list_encrypted_vms() -> dict[str, Any]:
        """List all virtual machines that have encryption configured.

        Uses the property collector to find VMs where config.keyId is set.
        Returns each VM's name, key ID, and provider ID.
        """
        logger.info("list_encrypted_vms")
        from vsphere_mcp.utils.property_collector import collect_properties

        items = collect_properties(client, vim.VirtualMachine, ["name", "config.keyId"])

        encrypted_vms = []
        for item in items:
            key_id_obj = item.get("config.keyId")
            if key_id_obj is None:
                continue
            key_id = getattr(key_id_obj, "keyId", None)
            provider = getattr(key_id_obj, "providerId", None)
            provider_id = getattr(provider, "id", None) if provider is not None else None
            encrypted_vms.append(
                {
                    "vm_name": item.get("name"),
                    "key_id": key_id,
                    "provider_id": provider_id,
                }
            )

        return {
            "total": len(encrypted_vms),
            "encrypted_vms": encrypted_vms,
        }
