from __future__ import annotations

from typing import Any

from pyVmomi import vim

from vsphere_mcp.client import VSphereClient
from vsphere_mcp.logging import get_logger
from vsphere_mcp.tools._base import find_host_by_name, handle_tool_errors, require_confirm
from vsphere_mcp.utils.property_collector import collect_properties

logger = get_logger(__name__)


def register_host_ops_ext_tools(mcp: Any, client: VSphereClient) -> None:
    @mcp.tool()
    @handle_tool_errors
    def get_host_snmp_config(host_name: str) -> dict[str, Any]:
        """Get the SNMP configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_snmp_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        snmp_system = getattr(cm, "snmpSystem", None)
        if snmp_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        config = getattr(snmp_system, "configuration", None)
        if config is None:
            return {"status": "error", "error": "SNMP configuration not available"}

        communities = list(getattr(config, "readCommunities", None) or [])

        trap_targets = []
        for t in getattr(config, "trapTargets", None) or []:
            trap_targets.append({
                "hostName": getattr(t, "hostName", None),
                "port": getattr(t, "port", None),
                "community": getattr(t, "community", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "enabled": getattr(config, "enabled", None),
            "port": getattr(config, "port", None),
            "communities": communities,
            "trap_targets": trap_targets,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_snmp_config(
        host_name: str,
        enabled: bool = True,
        community: str = "",
        port: int = 161,
        trap_targets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Set the SNMP configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            enabled: Whether SNMP should be enabled (default True).
            community: Community string for SNMP (default empty).
            port: SNMP port (default 161).
            trap_targets: List of trap target IP addresses (default empty).
        """
        logger.info("set_host_snmp_config", host_name=host_name, enabled=enabled, port=port)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        snmp_system = getattr(cm, "snmpSystem", None)
        if snmp_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        targets = []
        for addr in (trap_targets or []):
            targets.append(vim.host.SnmpSystem.SnmpConfigSpec.TrapTarget(
                hostName=addr,
                port=162,
                community=community,
            ))

        spec = vim.host.SnmpSystem.SnmpConfigSpec(
            enabled=enabled,
            port=port,
            readCommunities=[community] if community else [],
            trapTargets=targets,
        )

        snmp_system.ReconfigureSnmpAgent(spec=spec)

        return {
            "status": "success",
            "operation": "set_host_snmp_config",
            "host_name": host_name,
            "enabled": enabled,
            "port": port,
            "community": community,
            "num_trap_targets": len(targets),
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_coredump_config(host_name: str) -> dict[str, Any]:
        """Get the network coredump configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_coredump_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        diag_system = getattr(cm, "diagnosticSystem", None)
        if diag_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        query_method = getattr(diag_system, "QueryNetworkCoreDump", None)
        if query_method is None:
            return {"status": "error", "error": "QueryNetworkCoreDump not available on this host"}

        net_coredump = query_method()

        if net_coredump is None:
            return {
                "status": "success",
                "host_name": host_name,
                "configured": False,
            }

        return {
            "status": "success",
            "host_name": host_name,
            "configured": True,
            "enabled": getattr(net_coredump, "enabled", None),
            "interface_name": getattr(net_coredump, "interfaceName", None),
            "server_ip": getattr(net_coredump, "serverIp", None),
            "server_port": getattr(net_coredump, "serverPort", None),
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="high")
    def set_host_coredump_config(
        host_name: str,
        interface_name: str,
        server_ip: str,
        server_port: int = 6500,
    ) -> dict[str, Any]:
        """Set the network coredump configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            interface_name: VMkernel interface to use for coredump (e.g. "vmk0").
            server_ip: IP address of the coredump server.
            server_port: UDP port of the coredump server (default 6500).
        """
        logger.info(
            "set_host_coredump_config",
            host_name=host_name,
            interface_name=interface_name,
            server_ip=server_ip,
            server_port=server_port,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        diag_system = getattr(cm, "diagnosticSystem", None)
        if diag_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        configure_method = getattr(diag_system, "ConfigureNetworkCoreDump", None)
        if configure_method is None:
            return {"status": "error", "error": "ConfigureNetworkCoreDump not available on this host"}

        spec = vim.host.DiagnosticSystem.NetworkCoreDumpConfig(
            enabled=True,
            interfaceName=interface_name,
            serverIp=server_ip,
            serverPort=server_port,
        )

        configure_method(networkCoreDumpConfig=spec)

        return {
            "status": "success",
            "operation": "set_host_coredump_config",
            "host_name": host_name,
            "interface_name": interface_name,
            "server_ip": server_ip,
            "server_port": server_port,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_autostart_config(host_name: str) -> dict[str, Any]:
        """Get the VM autostart configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_autostart_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        autostart_manager = getattr(cm, "autoStartManager", None)
        if autostart_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        config = getattr(autostart_manager, "config", None)
        if config is None:
            return {"status": "error", "error": "Autostart configuration not available"}

        defaults = getattr(config, "defaults", None)
        defaults_info: dict[str, Any] | None = None
        if defaults is not None:
            defaults_info = {
                "enabled": getattr(defaults, "enabled", None),
                "startDelay": getattr(defaults, "startDelay", None),
                "stopAction": getattr(defaults, "stopAction", None),
                "stopDelay": getattr(defaults, "stopDelay", None),
                "waitForHeartbeat": getattr(defaults, "waitForHeartbeat", None),
            }

        power_info_list = []
        for pi in getattr(config, "powerInfo", None) or []:
            vm_ref = getattr(pi, "key", None)
            vm_name = None
            if vm_ref is not None:
                try:
                    vm_name = getattr(vm_ref, "name", None)
                except Exception:
                    vm_name = None
            power_info_list.append({
                "vm_name": vm_name,
                "startOrder": getattr(pi, "startOrder", None),
                "startDelay": getattr(pi, "startDelay", None),
                "startAction": getattr(pi, "startAction", None),
                "stopAction": getattr(pi, "stopAction", None),
                "stopDelay": getattr(pi, "stopDelay", None),
                "waitForHeartbeat": getattr(pi, "waitForHeartbeat", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "defaults": defaults_info,
            "power_info": power_info_list,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_autostart_config(
        host_name: str,
        vm_name: str,
        start_order: int = 1,
        start_delay: int = -1,
        stop_action: str = "systemDefault",
        stop_delay: int = -1,
    ) -> dict[str, Any]:
        """Set the autostart configuration for a specific VM on an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            vm_name: Name of the VM to configure autostart for.
            start_order: Boot order priority (lower numbers boot first, default 1).
            start_delay: Delay in seconds before starting (default -1 uses system default).
            stop_action: Action on shutdown - "systemDefault", "powerOff", "suspend", "guestShutdown" (default "systemDefault").
            stop_delay: Delay in seconds before stopping (default -1 uses system default).
        """
        logger.info(
            "set_host_autostart_config",
            host_name=host_name,
            vm_name=vm_name,
            start_order=start_order,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        autostart_manager = getattr(cm, "autoStartManager", None)
        if autostart_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        # Find the VM managed object
        vm_items = collect_properties(client, vim.VirtualMachine, ["name"])
        vm_obj = None
        for item in vm_items:
            if item.get("name") == vm_name:
                vm_obj = item["_obj"]
                break
        if vm_obj is None:
            return {"status": "error", "error": f"VM '{vm_name}' not found"}

        power_info = vim.host.AutoStartManager.AutoPowerInfo(
            key=vm_obj,
            startOrder=start_order,
            startDelay=start_delay,
            startAction="powerOn",
            stopAction=stop_action,
            stopDelay=stop_delay,
            waitForHeartbeat=vim.host.AutoStartManager.AutoPowerInfo.WaitHeartbeatSetting.systemDefault,
        )

        spec = vim.host.AutoStartManager.Config(powerInfo=[power_info])
        autostart_manager.ReconfigureAutostart(spec=spec)

        return {
            "status": "success",
            "operation": "set_host_autostart_config",
            "host_name": host_name,
            "vm_name": vm_name,
            "start_order": start_order,
            "start_delay": start_delay,
            "stop_action": stop_action,
            "stop_delay": stop_delay,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_swap_config(host_name: str) -> dict[str, Any]:
        """Get the swap configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_swap_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cfg = getattr(host_obj, "config", None)
        if cfg is None:
            return {"status": "error", "error": "config not available on this host"}

        swap_cfg = getattr(cfg, "systemSwapConfiguration", None)
        if swap_cfg is None:
            return {"status": "error", "error": "Feature not available on this host"}

        options = []
        for opt in getattr(swap_cfg, "option", None) or []:
            options.append({
                "key": getattr(opt, "key", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "swap_options": options,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_swap_datastore(host_name: str, datastore_name: str) -> dict[str, Any]:
        """Set the swap datastore for an ESXi host via advanced configuration.

        Args:
            host_name: Name of the ESXi host.
            datastore_name: Name of the datastore to use for host-level swap files.
        """
        logger.info("set_host_swap_datastore", host_name=host_name, datastore_name=datastore_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        # Resolve the datastore managed object
        ds_items = collect_properties(client, vim.Datastore, ["name", "info"])
        ds_obj = None
        ds_url = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                info = item.get("info")
                ds_url = getattr(info, "url", None) if info is not None else None
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        adv_config = getattr(cm, "advancedOption", None)
        if adv_config is None:
            return {"status": "error", "error": "advancedOption manager not available on this host"}

        scratch_path = ds_url if ds_url else f"[{datastore_name}]"
        option = vim.option.OptionValue(key="ScratchConfig.CurrentScratchLocation", value=scratch_path)
        adv_config.UpdateValues(value=[option])

        return {
            "status": "success",
            "operation": "set_host_swap_datastore",
            "host_name": host_name,
            "datastore_name": datastore_name,
            "scratch_path": scratch_path,
            "message": "Host reboot may be required for the change to take full effect",
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_tpm_attestation(host_name: str) -> dict[str, Any]:
        """Get the TPM attestation state for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_tpm_attestation", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        runtime = getattr(host_obj, "runtime", None)
        if runtime is None:
            return {"status": "error", "error": "runtime not available on this host"}

        tpm_pcr_values = getattr(runtime, "tpmPcrValues", None)
        if tpm_pcr_values is None:
            return {"status": "error", "error": "Feature not available on this host"}

        pcr_digests = []
        for pcr in tpm_pcr_values:
            digests = []
            for digest in getattr(pcr, "digestValue", None) or []:
                digests.append({
                    "algorithmId": getattr(digest, "algorithmId", None),
                    "digestValue": list(getattr(digest, "digestValue", None) or []),
                })
            pcr_digests.append({
                "index": getattr(pcr, "index", None),
                "pcr_digests": digests,
            })

        return {
            "status": "success",
            "host_name": host_name,
            "num_pcr_values": len(pcr_digests),
            "tpm_pcr_values": pcr_digests,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_image_profile(host_name: str) -> dict[str, Any]:
        """Get the installed image profile for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_image_profile", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cfg = getattr(host_obj, "config", None)
        if cfg is None:
            return {"status": "error", "error": "config not available on this host"}

        image_config = getattr(cfg, "imageConfigManager", None)
        if image_config is None:
            # Fall back to reading from config directly
            image_config = getattr(cfg, "imageConfig", None)

        if image_config is None:
            return {"status": "error", "error": "Feature not available on this host"}

        fetch_method = getattr(image_config, "fetchSoftwarePackages", None)
        if fetch_method is not None:
            # imageConfigManager object — read properties directly
            acceptance_level = getattr(image_config, "hostAcceptanceLevel", None)
            profile_name = None
        else:
            acceptance_level = getattr(image_config, "acceptanceLevel", None)
            profile_name = getattr(image_config, "name", None)

        return {
            "status": "success",
            "host_name": host_name,
            "acceptance_level": str(acceptance_level) if acceptance_level is not None else None,
            "profile_name": profile_name,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_vibs(host_name: str) -> dict[str, Any]:
        """Get the list of installed VIBs (software packages) for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_vibs", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cfg = getattr(host_obj, "config", None)
        if cfg is None:
            return {"status": "error", "error": "config not available on this host"}

        software = getattr(cfg, "software", None)
        if software is None:
            return {"status": "error", "error": "Feature not available on this host"}

        vibs = []
        for pkg in getattr(software, "packages", None) or []:
            vibs.append({
                "name": getattr(pkg, "name", None),
                "version": getattr(pkg, "version", None),
                "vendor": getattr(pkg, "vendor", None),
                "description": getattr(pkg, "description", None),
                "installDate": str(getattr(pkg, "installDate", None)),
                "acceptanceLevel": getattr(pkg, "acceptanceLevel", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "num_vibs": len(vibs),
            "vibs": vibs,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_fc_hba_info(host_name: str) -> dict[str, Any]:
        """Get Fibre Channel HBA details for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_fc_hba_info", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cfg = getattr(host_obj, "config", None)
        if cfg is None:
            return {"status": "error", "error": "config not available on this host"}

        storage_device = getattr(cfg, "storageDevice", None)
        if storage_device is None:
            return {"status": "error", "error": "storageDevice not available on this host"}

        fc_hbas = []
        for hba in getattr(storage_device, "hostBusAdapter", None) or []:
            if not isinstance(hba, vim.host.FibreChannelHba):
                continue
            fc_hbas.append({
                "device": getattr(hba, "device", None),
                "model": getattr(hba, "model", None),
                "driver": getattr(hba, "driver", None),
                "status": getattr(hba, "status", None),
                "nodeWorldWideName": getattr(hba, "nodeWorldWideName", None),
                "portWorldWideName": getattr(hba, "portWorldWideName", None),
                "portType": str(getattr(hba, "portType", None)),
                "speed": getattr(hba, "speed", None),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "num_fc_hbas": len(fc_hbas),
            "fc_hbas": fc_hbas,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_cpu_features(host_name: str) -> dict[str, Any]:
        """Get CPU feature flags for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_cpu_features", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        hw = getattr(host_obj, "hardware", None)
        if hw is None:
            return {"status": "error", "error": "hardware not available on this host"}

        cpu_features = getattr(hw, "cpuFeature", None)
        if cpu_features is None:
            return {"status": "error", "error": "Feature not available on this host"}

        feature_list = []
        for feat in cpu_features:
            feature_list.append({
                "level": getattr(feat, "level", None),
                "vendor": getattr(feat, "vendor", None),
                "eax": getattr(feat, "eax", None),
                "ebx": getattr(feat, "ebx", None),
                "ecx": getattr(feat, "ecx", None),
                "edx": getattr(feat, "edx", None),
            })

        cpu_pkg = getattr(hw, "cpuPkg", None) or []
        cpu_info = []
        for pkg in cpu_pkg:
            cpu_info.append({
                "index": getattr(pkg, "index", None),
                "vendor": getattr(pkg, "vendor", None),
                "hz": getattr(pkg, "hz", None),
                "busHz": getattr(pkg, "busHz", None),
                "description": getattr(pkg, "description", None),
                "threadId": list(getattr(pkg, "threadId", None) or []),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "num_cpu_feature_levels": len(feature_list),
            "cpu_features": feature_list,
            "cpu_packages": cpu_info,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_graphics_config(host_name: str) -> dict[str, Any]:
        """Get the graphics configuration for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_graphics_config", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        graphics_manager = getattr(cm, "graphicsManager", None)
        if graphics_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        graphics_config = getattr(graphics_manager, "graphicsConfig", None)
        if graphics_config is None:
            return {"status": "error", "error": "graphicsConfig not available"}

        device_configs = []
        for dc in getattr(graphics_config, "deviceType", None) or []:
            device_configs.append({
                "deviceId": getattr(dc, "deviceId", None),
                "graphicsType": str(getattr(dc, "graphicsType", None)),
            })

        return {
            "status": "success",
            "host_name": host_name,
            "host_default_graphics_type": str(getattr(graphics_config, "hostDefaultGraphicsType", None)),
            "shared_passthrough_gpu_types": str(getattr(graphics_config, "sharedPassthruGpuTypes", None)),
            "device_type_configs": device_configs,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_graphics_config(
        host_name: str,
        host_default_type: str = "shared",
    ) -> dict[str, Any]:
        """Set the default graphics type for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            host_default_type: Default graphics type - "shared" or "sharedDirect" (default "shared").
        """
        logger.info("set_host_graphics_config", host_name=host_name, host_default_type=host_default_type)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        graphics_manager = getattr(cm, "graphicsManager", None)
        if graphics_manager is None:
            return {"status": "error", "error": "Feature not available on this host"}

        update_method = getattr(graphics_manager, "UpdateGraphicsConfig", None)
        if update_method is None:
            return {"status": "error", "error": "UpdateGraphicsConfig not available on this host"}

        valid_types = ("shared", "sharedDirect")
        if host_default_type not in valid_types:
            return {
                "status": "error",
                "error": f"Invalid host_default_type '{host_default_type}'. Must be one of: {valid_types}",
            }

        config = vim.host.GraphicsManager.GraphicsConfig(
            hostDefaultGraphicsType=host_default_type,
        )
        update_method(config=config)

        return {
            "status": "success",
            "operation": "set_host_graphics_config",
            "host_name": host_name,
            "host_default_type": host_default_type,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_cim_provider_status(host_name: str) -> dict[str, Any]:
        """Get the CIM provider health status for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_cim_provider_status", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        health_system = getattr(cm, "healthStatusSystem", None)
        if health_system is None:
            return {"status": "error", "error": "Feature not available on this host"}

        runtime = getattr(health_system, "runtime", None)
        if runtime is None:
            return {"status": "error", "error": "health runtime not available"}

        hardware_status_info = getattr(runtime, "hardwareStatusInfo", None)
        cpu_status = []
        memory_status = []
        storage_status = []

        if hardware_status_info is not None:
            for entry in getattr(hardware_status_info, "cpuStatusInfo", None) or []:
                status = getattr(entry, "status", None)
                cpu_status.append({
                    "name": getattr(entry, "name", None),
                    "status": getattr(status, "key", None) if status else None,
                    "summary": getattr(status, "summary", None) if status else None,
                })
            for entry in getattr(hardware_status_info, "memoryStatusInfo", None) or []:
                status = getattr(entry, "status", None)
                memory_status.append({
                    "name": getattr(entry, "name", None),
                    "status": getattr(status, "key", None) if status else None,
                    "summary": getattr(status, "summary", None) if status else None,
                })
            for entry in getattr(hardware_status_info, "storageStatusInfo", None) or []:
                status = getattr(entry, "status", None)
                storage_status.append({
                    "name": getattr(entry, "name", None),
                    "status": getattr(status, "key", None) if status else None,
                    "summary": getattr(status, "summary", None) if status else None,
                })

        system_health = getattr(runtime, "systemHealthInfo", None)
        numeric_sensors = []
        if system_health is not None:
            for sensor in getattr(system_health, "numericSensorInfo", None) or []:
                health_state = getattr(sensor, "healthState", None)
                numeric_sensors.append({
                    "name": getattr(sensor, "name", None),
                    "sensorType": getattr(sensor, "sensorType", None),
                    "currentReading": getattr(sensor, "currentReading", None),
                    "unitModifier": getattr(sensor, "unitModifier", None),
                    "baseUnits": getattr(sensor, "baseUnits", None),
                    "healthState": getattr(health_state, "key", None) if health_state else None,
                })

        return {
            "status": "success",
            "host_name": host_name,
            "cpu_status": cpu_status,
            "memory_status": memory_status,
            "storage_status": storage_status,
            "numeric_sensors": numeric_sensors,
        }

    @mcp.tool()
    @handle_tool_errors
    def get_host_agent_vm_settings(host_name: str) -> dict[str, Any]:
        """Get the ESX Agent Manager (EAM) settings for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
        """
        logger.info("get_host_agent_vm_settings", host_name=host_name)

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        eam = getattr(cm, "esxAgentHostManager", None)
        if eam is None:
            return {"status": "error", "error": "Feature not available on this host"}

        config_info = getattr(eam, "configInfo", None)
        if config_info is None:
            return {"status": "error", "error": "EAM configInfo not available"}

        agent_datastore = getattr(config_info, "agentVmDatastore", None)
        agent_network = getattr(config_info, "agentVmNetwork", None)

        datastore_name = None
        if agent_datastore is not None:
            try:
                datastore_name = getattr(agent_datastore, "name", None)
            except Exception:
                datastore_name = None

        network_name = None
        if agent_network is not None:
            try:
                network_name = getattr(agent_network, "name", None)
            except Exception:
                network_name = None

        return {
            "status": "success",
            "host_name": host_name,
            "agent_vm_datastore": datastore_name,
            "agent_vm_network": network_name,
        }

    @mcp.tool()
    @handle_tool_errors
    @require_confirm(danger_level="medium")
    def set_host_agent_vm_settings(
        host_name: str,
        datastore_name: str,
        network_name: str,
    ) -> dict[str, Any]:
        """Set the ESX Agent Manager (EAM) agent VM datastore and network for an ESXi host.

        Args:
            host_name: Name of the ESXi host.
            datastore_name: Name of the datastore to use for agent VMs.
            network_name: Name of the network to use for agent VMs.
        """
        logger.info(
            "set_host_agent_vm_settings",
            host_name=host_name,
            datastore_name=datastore_name,
            network_name=network_name,
        )

        host_obj = find_host_by_name(client, host_name)
        if host_obj is None:
            return {"status": "error", "error": f"Host '{host_name}' not found"}

        cm = getattr(host_obj, "configManager", None)
        if cm is None:
            return {"status": "error", "error": "configManager not available on this host"}

        eam = getattr(cm, "esxAgentHostManager", None)
        if eam is None:
            return {"status": "error", "error": "Feature not available on this host"}

        # Resolve datastore managed object
        ds_items = collect_properties(client, vim.Datastore, ["name"])
        ds_obj = None
        for item in ds_items:
            if item.get("name") == datastore_name:
                ds_obj = item["_obj"]
                break
        if ds_obj is None:
            return {"status": "error", "error": f"Datastore '{datastore_name}' not found"}

        # Resolve network managed object
        net_items = collect_properties(client, vim.Network, ["name"])
        net_obj = None
        for item in net_items:
            if item.get("name") == network_name:
                net_obj = item["_obj"]
                break
        if net_obj is None:
            return {"status": "error", "error": f"Network '{network_name}' not found"}

        config_info = vim.host.EsxAgentHostManager.ConfigInfo(
            agentVmDatastore=ds_obj,
            agentVmNetwork=net_obj,
        )

        eam.EsxAgentHostManagerUpdateConfig(configInfo=config_info)

        return {
            "status": "success",
            "operation": "set_host_agent_vm_settings",
            "host_name": host_name,
            "datastore_name": datastore_name,
            "network_name": network_name,
        }
