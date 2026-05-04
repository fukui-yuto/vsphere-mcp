# vSphere MCP Tools Reference (v0.5.0)

Total: **657 tools** across 71 modules.

---

## advanced_settings.py (4 tools)

| # | Tool | Description |
|---|------|-------------|
| 1 | `get_esxi_advanced_settings` | Get advanced settings for an ESXi host. Optionally filter by key prefix (e.g. 'Mem', 'Net'). |
| 2 | `get_vcenter_advanced_settings` | Get advanced settings for vCenter Server. Optionally filter by key prefix. |
| 3 | `set_esxi_advanced_setting` | Set an advanced setting on an ESXi host. Use get_esxi_advanced_settings to see current values first. |
| 4 | `set_vcenter_advanced_setting` | Set an advanced setting on vCenter Server. Use get_vcenter_advanced_settings to see current values first. |

## alarm.py (4 tools)

| # | Tool | Description |
|---|------|-------------|
| 5 | `create_alarm` | Create an alarm on a vSphere entity. |
| 6 | `delete_alarm` | Delete an alarm by name. |
| 7 | `reset_alarm_status` | Acknowledge an alarm to reset its status to green. |
| 8 | `enable_disable_alarm` | Enable or disable an alarm. |

## appliance_health.py (12 tools)

| # | Tool | Description |
|---|------|-------------|
| 9 | `get_appliance_health_overview` | Get health status for all vCenter appliance subsystems. |
| 10 | `get_appliance_health_memory` | Get memory health status of the vCenter appliance. |
| 11 | `get_appliance_health_cpu` | Get CPU load health status of the vCenter appliance. |
| 12 | `get_appliance_health_storage` | Get storage health status of the vCenter appliance. |
| 13 | `get_appliance_health_database` | Get database storage health status of the vCenter appliance. |
| 14 | `get_appliance_health_swap` | Get swap health status of the vCenter appliance. |
| 15 | `get_appliance_health_softwarepackages` | Get software packages health status of the vCenter appliance. |
| 16 | `get_appliance_monitoring_data` | Get appliance monitoring metrics. |
| 17 | `get_appliance_system_time` | Get the current system time of the vCenter appliance. |
| 18 | `get_appliance_timezone` | Get the configured timezone of the vCenter appliance. |
| 19 | `get_appliance_uptime` | Get the uptime of the vCenter appliance in seconds. |
| 20 | `shutdown_reboot_appliance` | Shutdown or reboot the vCenter appliance. |

## appliance_update.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 21 | `get_appliance_update_pending` | Get pending updates available for the vCenter appliance. |
| 22 | `get_appliance_update_staged` | Get information about the currently staged vCenter appliance update. |
| 23 | `stage_appliance_update` | Stage a pending vCenter appliance update for installation. |
| 24 | `get_appliance_dns_domains` | Get the DNS search domains configured on the vCenter appliance. |
| 25 | `get_appliance_dns_hostname` | Get the hostname configured on the vCenter appliance. |
| 26 | `get_appliance_firewall_rules` | Get inbound firewall rules configured on the vCenter appliance. |

## batch.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 27 | `batch_power_operation` | Perform power operation on multiple VMs. |
| 28 | `batch_create_snapshots` | Create snapshots on multiple VMs simultaneously. |
| 29 | `batch_get_vm_info` | Get info for multiple VMs in one call using a single PropertyCollector fetch. |
| 30 | `batch_reconfigure_vms` | Reconfigure CPU and/or memory for multiple VMs in one call. |
| 31 | `batch_migrate_vms` | Migrate (vMotion) multiple VMs to a target host and optionally a target datastore. |

## certificate.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 32 | `get_vcenter_tls_certificate` | Get vCenter TLS certificate information including subject, issuer, validity, thumbprint, and serial number. |
| 33 | `get_vcenter_tls_csr` | Generate a Certificate Signing Request (CSR) for the vCenter TLS certificate. |
| 34 | `renew_vcenter_tls_certificate` | Renew the vCenter TLS certificate using the VMware Certificate Authority (VMCA). |
| 35 | `replace_vcenter_tls_certificate` | Replace the vCenter TLS certificate with a custom certificate. |
| 36 | `list_trusted_root_certificates` | List all trusted root CA certificates configured in vCenter. |
| 37 | `add_trusted_root_certificate` | Add a trusted root CA certificate to vCenter. |
| 38 | `remove_trusted_root_certificate` | Remove a trusted root CA certificate from vCenter by its chain ID. |
| 39 | `get_certificate_expiry_status` | Check expiry status for all vCenter certificates including TLS and trusted root CAs. |

## cluster_config.py (25 tools)

| # | Tool | Description |
|---|------|-------------|
| 40 | `get_cluster_ha_config` | Get HA (High Availability) configuration for a cluster. |
| 41 | `get_cluster_drs_config` | Get DRS (Distributed Resource Scheduler) configuration for a cluster. |
| 42 | `list_drs_rules` | List DRS affinity/anti-affinity rules for a cluster. |
| 43 | `get_cluster_drs_recommendations` | Get current DRS recommendations for a cluster. |
| 44 | `create_resource_pool` | Create a resource pool on a cluster. |
| 45 | `update_resource_pool` | Update an existing resource pool configuration. |
| 46 | `delete_resource_pool` | Delete a resource pool. |
| 47 | `list_cluster_host_vm_groups` | List DRS host groups and VM groups for a cluster. |
| 48 | `configure_cluster_ha` | Configure High Availability (HA) settings on a cluster. |
| 49 | `configure_cluster_drs` | Configure Distributed Resource Scheduler (DRS) settings on a cluster. |
| 50 | `create_drs_rule` | Create a DRS affinity or anti-affinity rule for VMs in a cluster. |
| 51 | `delete_drs_rule` | Delete a DRS rule from a cluster. |
| 52 | `apply_drs_recommendation` | Apply a specific DRS recommendation on a cluster. |
| 53 | `create_cluster` | Create a new cluster in a datacenter. |
| 54 | `delete_cluster` | Delete a cluster from vCenter. This is a destructive operation. |
| 55 | `create_drs_vm_group` | Create a DRS VM group in a cluster. |
| 56 | `create_drs_host_group` | Create a DRS host group in a cluster. |
| 57 | `create_vm_host_affinity_rule` | Create a VM-Host affinity rule in a cluster. |
| 58 | `delete_drs_group` | Delete a DRS VM or Host group from a cluster. |
| 59 | `update_drs_group` | Update the members of a DRS VM or Host group in a cluster. |
| 60 | `set_evc_mode` | Set or disable the EVC (Enhanced vMotion Compatibility) mode on a cluster. |
| 61 | `get_evc_mode` | Get the current EVC (Enhanced vMotion Compatibility) mode of a cluster. |
| 62 | `move_vm_to_resource_pool` | Move one or more VMs into a resource pool. |
| 63 | `configure_dpm` | Configure DPM (Distributed Power Management) on a cluster. |
| 64 | `configure_ha_admission_control` | Configure HA admission control policy on a cluster. |

## cluster_ops_ext.py (12 tools)

| # | Tool | Description |
|---|------|-------------|
| 65 | `set_drs_vm_override` | Set a per-VM DRS automation level override within a cluster. |
| 66 | `list_drs_vm_overrides` | List all per-VM DRS automation level overrides configured in a cluster. |
| 67 | `set_ha_vm_override` | Set per-VM HA restart priority and host isolation response overrides. |
| 68 | `list_ha_vm_overrides` | List all per-VM HA restart priority and isolation response overrides in a cluster. |
| 69 | `configure_ha_heartbeat_datastores` | Configure the HA heartbeat datastore selection policy and preferred datastores. |
| 70 | `get_vcha_config` | Get the current vCenter High Availability (VCHA) cluster configuration. |
| 71 | `configure_vcha` | Deploy and configure a vCenter High Availability (VCHA) cluster. |
| 72 | `get_vcha_mode` | Get the current operational mode of the vCenter High Availability (VCHA) cluster. |
| 73 | `set_vcha_mode` | Set the operational mode of the vCenter High Availability (VCHA) cluster. |
| 74 | `get_cluster_resource_summary` | Get a resource usage summary (CPU and memory totals and usage) for a cluster. |
| 75 | `set_storage_drs_vm_override` | Set a per-VM Storage DRS (SDRS) override for a datastore cluster (storage pod). |
| 76 | `list_storage_drs_vm_overrides` | List all per-VM Storage DRS overrides configured in a datastore cluster (storage pod). |

## content_library.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 77 | `list_content_libraries` | List all content libraries in vCenter. |
| 78 | `create_local_content_library` | Create a local content library backed by a datastore. |
| 79 | `delete_content_library` | Delete a content library and all its items. |
| 80 | `list_library_items` | List all items in a content library. |
| 81 | `delete_library_item` | Delete an item from a content library. |
| 82 | `deploy_vm_from_library_item` | Deploy a VM from a content library item (OVF/OVA template). |
| 83 | `sync_subscribed_library` | Trigger a synchronization of a subscribed content library. |

## content_library_ext.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 84 | `create_subscribed_library` | Create a subscribed content library that syncs from a remote subscription URL. |
| 85 | `publish_library` | Publish a local content library so it can be subscribed to by other vCenters. |
| 86 | `get_library_subscription_info` | Get subscription details for a subscribed content library. |
| 87 | `update_library_subscription` | Update subscription settings for a subscribed content library. |
| 88 | `sync_library_item` | Sync a single item in a subscribed content library. |
| 89 | `create_library_item` | Create an empty item in a content library. |
| 90 | `update_library_item_metadata` | Update the metadata (name, description) of a content library item. |
| 91 | `get_library_item_files` | List all files contained in a content library item. |

## customization.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 92 | `list_customization_specs` | List all guest OS customization specs available in vCenter. |
| 93 | `get_customization_spec` | Get detailed information about a specific customization spec. |
| 94 | `create_linux_customization_spec` | Create a Linux guest OS customization spec. |
| 95 | `create_windows_customization_spec` | Create a Windows guest OS customization spec using Sysprep. |
| 96 | `delete_customization_spec` | Delete a customization spec from vCenter. |
| 97 | `apply_customization_to_vm` | Apply a customization spec to an existing virtual machine. |

## datacenter.py (3 tools)

| # | Tool | Description |
|---|------|-------------|
| 98 | `create_datacenter` | Create a new datacenter in the root folder of the vCenter inventory. |
| 99 | `delete_datacenter` | Delete a datacenter and all objects within it permanently. |
| 100 | `rename_datacenter` | Rename an existing datacenter. |

## datastore_browser.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 101 | `browse_datastore` | Browse files on a datastore. Returns file names, sizes, and modification times. |
| 102 | `delete_datastore_file` | Delete a file or directory from a datastore. This operation is irreversible. |
| 103 | `copy_datastore_file` | Copy a file between datastore paths. Paths use [datastore] format. |
| 104 | `move_datastore_file` | Move a file between datastore paths. Paths use [datastore] format. |
| 105 | `create_datastore_directory` | Create a directory on a datastore. Path must use [datastore] format, e.g. '[datastore1] new_folder'. |

## datastore_ext.py (2 tools)

| # | Tool | Description |
|---|------|-------------|
| 106 | `get_datastore_file_url` | Generate an authenticated HTTPS URL for a file on a vSphere datastore. |
| 107 | `upload_file_to_datastore` | Upload content to a file on a vSphere datastore using the HTTP file service. |

## diagnostics.py (11 tools)

| # | Tool | Description |
|---|------|-------------|
| 108 | `generate_support_bundle` | Generate a vCenter appliance support bundle. |
| 109 | `generate_host_support_bundle` | Generate an ESXi vm-support bundle for the specified host. |
| 110 | `get_ceip_status` | Get the Customer Experience Improvement Program (CEIP) participation status. |
| 111 | `set_ceip_status` | Set the Customer Experience Improvement Program (CEIP) participation status. |
| 112 | `validate_syslog_forwarding` | Test syslog forwarding configuration to verify remote log hosts are reachable. |
| 113 | `get_vcenter_deployment_type` | Get vCenter deployment type and installation information. |
| 114 | `list_extensions` | List all registered vCenter extensions and plugins. |
| 115 | `get_extension_info` | Get detailed information about a specific vCenter extension. |
| 116 | `register_extension` | Register a new vCenter extension/plugin. |
| 117 | `unregister_extension` | Unregister (remove) a vCenter extension/plugin. |
| 118 | `update_extension` | Update metadata for an existing vCenter extension. |

## dvs_advanced.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 119 | `configure_dvs_lacp` | Configure LACP (Link Aggregation Control Protocol) on a Distributed Virtual Switch. |
| 120 | `get_dvs_health` | Get health check status for a Distributed Virtual Switch. |
| 121 | `enable_dvs_health_check` | Enable health checking on a Distributed Virtual Switch. |
| 122 | `migrate_vm_networking_to_dvs` | Migrate a VM NIC from a standard portgroup to a DVS portgroup. |
| 123 | `export_dvs_config` | Export the configuration of a Distributed Virtual Switch. |
| 124 | `get_dvs_port_statistics` | Get port statistics for a Distributed Virtual Switch. |

## encryption.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 125 | `get_vm_encryption_state` | Get the encryption state of a virtual machine. |
| 126 | `encrypt_vm` | Encrypt a virtual machine using the default key provider. |
| 127 | `decrypt_vm` | Decrypt an encrypted virtual machine. |
| 128 | `rekey_vm` | Re-key the encryption on a virtual machine. |
| 129 | `list_key_providers` | List configured Key Management Server (KMS) providers in vCenter. |
| 130 | `get_encryption_status` | Get the overall vCenter encryption / key management status. |
| 131 | `list_encrypted_vms` | List all virtual machines that have encryption configured. |

## esxi_accounts.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 132 | `create_esxi_local_user` | Create a local user account on an ESXi host. |
| 133 | `remove_esxi_local_user` | Remove a local user account from an ESXi host. |
| 134 | `update_esxi_local_user` | Update an existing local user account on an ESXi host. |
| 135 | `join_esxi_to_domain` | Join an ESXi host to an Active Directory domain. |
| 136 | `leave_esxi_domain` | Remove an ESXi host from its current Active Directory domain. |

## event_ext.py (13 tools)

| # | Tool | Description |
|---|------|-------------|
| 137 | `post_custom_event` | Post a custom user event to vCenter for a specific entity. |
| 138 | `query_events_by_entity` | Query vCenter events for a specific entity. |
| 139 | `duplicate_customization_spec` | Duplicate an existing guest OS customization spec with a new name. |
| 140 | `rename_customization_spec` | Rename an existing guest OS customization spec. |
| 141 | `export_customization_spec_xml` | Export a guest OS customization spec as an XML string. |
| 142 | `update_performance_interval` | Update a performance collection interval setting in vCenter. |
| 143 | `get_composite_performance` | Get composite performance data for an entity, including child entity roll-ups. |
| 144 | `acquire_clone_ticket` | Acquire a clone ticket for the current vCenter session. |
| 145 | `get_current_session_info` | Get information about the current vCenter session. |
| 146 | `get_alarm_state` | Get triggered alarm states for a specific entity. |
| 147 | `set_alarm_status` | Set the acknowledged status of a triggered alarm on an entity. |
| 148 | `decode_license_key` | Decode a vSphere license key to retrieve its properties and features. |
| 149 | `get_license_usage` | Get current vCenter license usage statistics. |

## events.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 150 | `list_recent_events` | List recent vCenter events. |
| 151 | `list_alarms` | List triggered alarms. |
| 152 | `list_performance_counters` | List all performance counters. Optionally filter by group name. |
| 153 | `get_alarm_definitions` | List alarm definitions. Optionally filter by entity. |
| 154 | `get_host_system_log` | Browse host diagnostic log. |
| 155 | `list_diagnostic_log_keys` | List available diagnostic log keys on an ESXi host. |
| 156 | `get_vcenter_log` | Browse a vCenter diagnostic log by key. |
| 157 | `list_vcenter_log_keys` | List available vCenter diagnostic log keys. |

## fault_tolerance.py (3 tools)

| # | Tool | Description |
|---|------|-------------|
| 158 | `enable_fault_tolerance` | Enable Fault Tolerance for a VM by creating a secondary VM on the specified host. |
| 159 | `disable_fault_tolerance` | Disable Fault Tolerance for a VM. |
| 160 | `get_fault_tolerance_info` | Get Fault Tolerance configuration and status for a VM. |

## fcd.py (10 tools)

| # | Tool | Description |
|---|------|-------------|
| 161 | `create_fcd` | Create a First Class Disk (FCD / Improved Virtual Disk) on a datastore. |
| 162 | `delete_fcd` | Delete a First Class Disk (FCD) permanently from a datastore. |
| 163 | `list_fcds` | List all First Class Disks (FCDs) on a datastore. |
| 164 | `get_fcd_info` | Get detailed metadata for a specific First Class Disk (FCD). |
| 165 | `clone_fcd` | Clone a First Class Disk (FCD) to create a new independent copy. |
| 166 | `relocate_fcd` | Relocate a First Class Disk (FCD) to a different datastore (Storage vMotion for FCDs). |
| 167 | `create_fcd_snapshot` | Create a point-in-time snapshot of a First Class Disk (FCD). |
| 168 | `delete_fcd_snapshot` | Delete a snapshot of a First Class Disk (FCD). |
| 169 | `get_fcd_snapshots` | Get snapshot information for a First Class Disk (FCD). |
| 170 | `attach_detach_fcd` | Attach or detach a First Class Disk (FCD) to/from a VM. |

## folders.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 171 | `list_folders` | List all folders in the vSphere inventory with their types and paths. |
| 172 | `create_folder` | Create a new folder under the specified parent folder. |
| 173 | `move_vm_to_folder` | Move a VM into a specified folder. |
| 174 | `delete_folder` | Delete a folder from the vSphere inventory. This operation is irreversible. |
| 175 | `rename_folder` | Rename a folder in the vSphere inventory. |
| 176 | `move_entity_to_folder` | Move a vSphere entity (vm, host, datastore, network) into a target folder. |

## guest.py (14 tools)

| # | Tool | Description |
|---|------|-------------|
| 177 | `execute_guest_command` | Execute a command inside a VM's guest OS via VMware Tools. |
| 178 | `list_guest_processes` | List running processes inside a VM's guest OS via VMware Tools. |
| 179 | `list_guest_files` | List files in a directory inside a VM's guest OS via VMware Tools. |
| 180 | `create_guest_directory` | Create a directory inside a VM's guest OS via VMware Tools. |
| 181 | `delete_guest_file` | Delete a file inside a VM's guest OS via VMware Tools. |
| 182 | `terminate_guest_process` | Terminate a process by PID inside a VM's guest OS via VMware Tools. |
| 183 | `upgrade_vmware_tools` | Upgrade VMware Tools on a powered-on VM. |
| 184 | `read_guest_environment_variables` | Read environment variables from a VM's guest OS via VMware Tools. |
| 185 | `upload_file_to_guest` | Upload a file to a VM's guest OS via VMware Tools. |
| 186 | `download_file_from_guest` | Download a file from a VM's guest OS via VMware Tools. Returns content as text. |
| 187 | `move_guest_file` | Move or rename a file inside a VM's guest OS via VMware Tools. |
| 188 | `delete_guest_directory` | Delete a directory inside a VM's guest OS via VMware Tools. |
| 189 | `get_guest_network_info` | Get network interface information reported by VMware Tools for a guest VM. |
| 190 | `get_guest_os_info` | Get detailed guest OS information reported by VMware Tools for a VM. |

## guest_ext.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 191 | `create_guest_temp_file` | Create a temporary file inside a VM's guest OS via VMware Tools. |
| 192 | `create_guest_temp_directory` | Create a temporary directory inside a VM's guest OS via VMware Tools. |
| 193 | `set_guest_file_attributes` | Set POSIX file attributes on a file inside a VM's guest OS via VMware Tools. |
| 194 | `read_guest_file_content` | Read the content of a file from a VM's guest OS via VMware Tools. |
| 195 | `write_guest_file_content` | Write text content to a file inside a VM's guest OS via VMware Tools. |
| 196 | `get_guest_windows_registry` | Read Windows registry keys from a guest VM via VMware Tools. |
| 197 | `set_guest_windows_registry` | Set a Windows registry value in a guest VM via VMware Tools. |
| 198 | `list_guest_mapped_aliases` | List guest OS user aliases mapped for a VM via VMware Tools alias manager. |

## host.py (11 tools)

| # | Tool | Description |
|---|------|-------------|
| 199 | `enter_maintenance_mode` | Put an ESXi host into maintenance mode. Running VMs will be migrated or shut down. |
| 200 | `exit_maintenance_mode` | Take an ESXi host out of maintenance mode. |
| 201 | `shutdown_host` | Shut down an ESXi host. Host should be in maintenance mode first. |
| 202 | `reboot_host` | Reboot an ESXi host. Host should be in maintenance mode first. |
| 203 | `disconnect_host` | Disconnect an ESXi host from vCenter. |
| 204 | `reconnect_host` | Reconnect a disconnected ESXi host to vCenter. |
| 205 | `add_host_to_cluster` | Add an ESXi host to a cluster in vCenter. |
| 206 | `remove_host` | Remove a host from vCenter inventory. |
| 207 | `move_host_to_cluster` | Move a standalone ESXi host into a cluster. |
| 208 | `add_standalone_host` | Add a standalone ESXi host to a datacenter in vCenter. |
| 209 | `rename_host` | Rename an ESXi host in vCenter inventory. |

## host_config.py (33 tools)

| # | Tool | Description |
|---|------|-------------|
| 210 | `get_host_vswitches` | Get the list of standard vSwitches on an ESXi host. |
| 211 | `get_host_vmkernel_adapters` | Get the list of VMkernel adapters on an ESXi host. |
| 212 | `get_host_portgroups` | Get the list of standard switch port groups on an ESXi host. |
| 213 | `get_host_physical_nics` | Get the list of physical NICs on an ESXi host. |
| 214 | `list_host_services` | Get the list of services on an ESXi host. |
| 215 | `start_stop_host_service` | Start or stop a service on an ESXi host. |
| 216 | `list_host_firewall_rules` | Get the list of firewall rulesets on an ESXi host. |
| 217 | `get_host_dns_config` | Get the DNS configuration of an ESXi host. |
| 218 | `get_host_ntp_config` | Get the NTP configuration of an ESXi host. |
| 219 | `get_host_routing_config` | Get the routing configuration of an ESXi host. |
| 220 | `get_host_hardware_health` | Get hardware health information of an ESXi host. |
| 221 | `enable_esxi_ssh` | Enable SSH on an ESXi host by starting the TSM-SSH service. |
| 222 | `disable_esxi_ssh` | Disable SSH on an ESXi host by stopping the TSM-SSH service. |
| 223 | `get_host_syslog_config` | Get syslog configuration of an ESXi host. |
| 224 | `get_host_power_policy` | Get power management policy of an ESXi host. |
| 225 | `set_host_power_policy` | Set power management policy on an ESXi host. |
| 226 | `get_host_lockdown_mode` | Get lockdown mode of an ESXi host. |
| 227 | `get_host_certificate_info` | Get SSL certificate details of an ESXi host. |
| 228 | `get_host_time_config` | Get the current date and time of an ESXi host. |
| 229 | `create_vswitch` | Create a standard vSwitch on an ESXi host. |
| 230 | `remove_vswitch` | Remove a standard vSwitch from an ESXi host. |
| 231 | `update_vswitch` | Update settings of an existing standard vSwitch on an ESXi host. |
| 232 | `add_vmkernel_adapter` | Add a VMkernel adapter to an ESXi host. |
| 233 | `remove_vmkernel_adapter` | Remove a VMkernel adapter from an ESXi host (e.g. 'vmk1'). |
| 234 | `set_host_dns_config` | Set the DNS configuration on an ESXi host. |
| 235 | `set_host_ntp_servers` | Set NTP servers on an ESXi host. |
| 236 | `set_host_syslog_target` | Set the syslog remote target on an ESXi host. |
| 237 | `set_host_lockdown_mode` | Set the lockdown mode of an ESXi host. |
| 238 | `enable_host_firewall_ruleset` | Enable a firewall ruleset on an ESXi host. |
| 239 | `disable_host_firewall_ruleset` | Disable a firewall ruleset on an ESXi host. |
| 240 | `set_host_service_policy` | Set the startup policy for a service on an ESXi host. |
| 241 | `sync_host_time` | Synchronize the clock on an ESXi host to the current UTC time. |
| 242 | `refresh_host_ca_certificates` | Refresh CA certificates and CRLs on an ESXi host. |

## host_mgr_ext.py (10 tools)

| # | Tool | Description |
|---|------|-------------|
| 243 | `backup_host_firmware` | Backup the ESXi host firmware/configuration to a downloadable bundle. |
| 244 | `restore_host_firmware` | Restore the ESXi host firmware/configuration from a previously created backup. |
| 245 | `get_host_boot_devices` | Get the boot device list for an ESXi host. |
| 246 | `set_host_boot_device` | Set the primary boot device for an ESXi host. |
| 247 | `configure_host_cache` | Configure SSD-backed host cache for a swap file on an ESXi host. |
| 248 | `get_host_cache_config` | Get the current host cache configuration for an ESXi host. |
| 249 | `list_host_kernel_modules` | List ESXi kernel modules (VMkernel drivers) loaded on a host. |
| 250 | `get_host_vmkernel_nic_services` | Get VMkernel NIC service bindings for an ESXi host. |
| 251 | `set_host_vmkernel_nic_service` | Select or deselect a VMkernel NIC for a specific service type on an ESXi host. |
| 252 | `get_host_image_config` | Get the ESXi software image and VIB (VMware Installation Bundle) configuration. |

## host_ops_ext.py (18 tools)

| # | Tool | Description |
|---|------|-------------|
| 253 | `get_host_snmp_config` | Get the SNMP configuration for an ESXi host. |
| 254 | `set_host_snmp_config` | Set the SNMP configuration for an ESXi host. |
| 255 | `get_host_coredump_config` | Get the network coredump configuration for an ESXi host. |
| 256 | `set_host_coredump_config` | Set the network coredump configuration for an ESXi host. |
| 257 | `get_host_autostart_config` | Get the VM autostart configuration for an ESXi host. |
| 258 | `set_host_autostart_config` | Set the VM autostart configuration for an ESXi host. |
| 259 | `get_host_swap_config` | Get the swap configuration for an ESXi host. |
| 260 | `set_host_swap_datastore` | Set the swap datastore for an ESXi host via advanced configuration. |
| 261 | `get_host_tpm_attestation` | Get the TPM attestation state for an ESXi host. |
| 262 | `get_host_image_profile` | Get the installed image profile for an ESXi host. |
| 263 | `get_host_vibs` | Get the list of installed VIBs (software packages) for an ESXi host. |
| 264 | `get_host_fc_hba_info` | Get Fibre Channel HBA details for an ESXi host. |
| 265 | `get_host_cpu_features` | Get CPU feature flags for an ESXi host. |
| 266 | `get_host_graphics_config` | Get the graphics configuration for an ESXi host. |
| 267 | `set_host_graphics_config` | Set the default graphics type for an ESXi host. |
| 268 | `get_host_cim_provider_status` | Get the CIM provider health status for an ESXi host. |
| 269 | `get_host_agent_vm_settings` | Get the ESX Agent Manager (EAM) settings for an ESXi host. |
| 270 | `set_host_agent_vm_settings` | Set the ESX Agent Manager (EAM) agent VM datastore and network for an ESXi host. |

## host_profile.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 271 | `list_host_profiles` | List all host profiles defined in vCenter. |
| 272 | `check_host_profile_compliance` | Check whether a host is compliant with a given host profile. |
| 273 | `create_host_profile` | Create a host profile from a reference ESXi host. |
| 274 | `delete_host_profile` | Delete a host profile by name. |
| 275 | `apply_host_profile` | Apply a host profile to an ESXi host. |
| 276 | `associate_host_with_profile` | Associate an ESXi host with a host profile. |
| 277 | `export_host_profile` | Export a host profile as serialized profile data. |
| 278 | `remediate_host_profile` | Remediate an ESXi host to comply with a host profile. |

## instant_clone.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 279 | `instant_clone_vm` | Instant clone a running VM. The source VM must be powered on. |
| 280 | `cross_vcenter_migrate_vm` | Migrate a VM to a different vCenter (cross-vCenter vMotion). |
| 281 | `create_scheduled_task` | Create a scheduled task in vCenter for a VM or other entity. |
| 282 | `update_scheduled_task` | Update an existing scheduled task. |
| 283 | `get_scheduled_task_detail` | Get full details of a scheduled task including schedule, last run, and next run times. |

## inventory.py (18 tools)

| # | Tool | Description |
|---|------|-------------|
| 284 | `test_connection` | Test the vSphere connection and return server information. |
| 285 | `list_vms` | List all virtual machines. Filter by host/cluster. Supports pagination with limit/offset. |
| 286 | `get_vm_info` | Get detailed information for a specific virtual machine by name. |
| 287 | `list_hosts` | List all ESXi hosts. Optionally filter by cluster name. |
| 288 | `get_host_info` | Get detailed information for a specific ESXi host by name. |
| 289 | `list_datacenters` | List all datacenters in vCenter. |
| 290 | `list_clusters` | List all clusters. Optionally filter by datacenter name. |
| 291 | `list_datastores` | List all datastores. |
| 292 | `list_networks` | List all networks (port groups). |
| 293 | `list_snapshots` | List all snapshots for a virtual machine. |
| 294 | `get_cluster_health` | Get health summary for a cluster including CPU/memory utilization. |
| 295 | `search_vms` | Search virtual machines by name (case-insensitive substring match). |
| 296 | `list_resource_pools` | List all resource pools with CPU and memory allocation. |
| 297 | `list_distributed_switches` | List all distributed virtual switches. |
| 298 | `list_distributed_portgroups` | List all distributed virtual port groups. |
| 299 | `get_datacenter_info` | Get detailed datacenter info including folder names. |
| 300 | `get_vm_screenshot` | Take a screenshot of a running VM's console. |
| 301 | `wait_for_vm_guest_ip` | Wait until a VM reports a guest IP address from VMware Tools. |

## iscsi_config.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 302 | `get_iscsi_adapter_config` | Get the full iSCSI adapter configuration for an ESXi host. |
| 303 | `set_iscsi_chap_auth` | Set CHAP authentication on an iSCSI adapter. |
| 304 | `add_iscsi_static_target` | Add a static iSCSI target to an iSCSI adapter. |
| 305 | `remove_iscsi_target` | Remove an iSCSI target (send target or static target) from an iSCSI adapter. |
| 306 | `rescan_iscsi_hba` | Rescan a specific iSCSI HBA on an ESXi host to discover new targets. |

## license.py (4 tools)

| # | Tool | Description |
|---|------|-------------|
| 307 | `add_license` | Add a new license key to vCenter. |
| 308 | `remove_license` | Remove a license key from vCenter. |
| 309 | `assign_license` | Assign a license to a vCenter entity (e.g. a host or cluster) by its MoRef ID. |
| 310 | `list_license_assignments` | List all license assignments in vCenter. |

## lifecycle.py (13 tools)

| # | Tool | Description |
|---|------|-------------|
| 311 | `delete_vm` | Delete a virtual machine permanently. The VM must be powered off first. |
| 312 | `clone_vm` | Clone a virtual machine to create a new VM. |
| 313 | `deploy_from_template` | Deploy a new VM from a template. |
| 314 | `register_vm` | Register an existing VMX file as a virtual machine in vCenter. |
| 315 | `convert_vm_to_template` | Convert a powered-off VM to a template. |
| 316 | `convert_template_to_vm` | Convert a template back to a virtual machine on the specified host. |
| 317 | `create_vm` | Create a new virtual machine from scratch. |
| 318 | `linked_clone_vm` | Create a linked clone of a VM from a named snapshot. |
| 319 | `enable_vm_cbt` | Enable or disable Changed Block Tracking (CBT) on a virtual machine. |
| 320 | `query_vm_changed_disk_areas` | Query changed disk areas for incremental backup using Changed Block Tracking. |
| 321 | `answer_vm_question` | Answer a pending question blocking a virtual machine. |
| 322 | `get_vm_pending_question` | Get the pending question blocking a virtual machine, if any. |
| 323 | `list_guest_os_types` | List common supported guest OS type IDs for use when creating VMs. |

## migration.py (3 tools)

| # | Tool | Description |
|---|------|-------------|
| 324 | `migrate_vm` | Migrate a virtual machine to a different ESXi host. |
| 325 | `storage_vmotion` | Migrate VM disks to a different datastore (Storage vMotion). |
| 326 | `relocate_vm` | Relocate a VM (combined compute + storage migration). |

## namespace_compat.py (18 tools)

| # | Tool | Description |
|---|------|-------------|
| 327 | `create_datastore_namespace_directory` | Create a top-level directory on a datastore using the namespace manager. |
| 328 | `delete_datastore_namespace_directory` | Delete a top-level directory on a datastore using the namespace manager. |
| 329 | `check_vm_compatibility` | Check VM compatibility for migration to a target host or resource pool. |
| 330 | `check_power_on_compatibility` | Check power-on compatibility for a VM on a target host or resource pool. |
| 331 | `list_tenants` | List vSphere tenants (requires vSphere 7.0u2+ with multi-tenancy configured). |
| 332 | `query_host_connected_luns` | Query which hosts have a specific LUN (by UUID) attached. |
| 333 | `get_guest_customization_status` | Get the guest customization status for a VM (requires vSphere 7.0+). |
| 334 | `abort_guest_customization` | Abort an in-progress guest OS customization on a VM. |
| 335 | `get_vcenter_snmp_config` | Get the vCenter SNMP system configuration. |
| 336 | `refresh_vm_storage_info` | Refresh the storage information for a VM. |
| 337 | `set_vm_display_topology` | Set the display topology (resolution and position) for a VM's virtual displays. |
| 338 | `get_vcenter_service_list` | Get the list of services registered with the vCenter ServiceManager. |
| 339 | `get_cluster_profile_compliance` | Check profile compliance for a cluster using the ClusterProfileManager. |
| 340 | `list_cluster_profiles` | List all cluster profiles registered with the ClusterProfileManager. |
| 341 | `get_vcenter_resource_pools_rest` | List all resource pools visible in vCenter via the REST API. |
| 342 | `get_vcenter_authentication_token` | Acquire a new vCenter REST API session token using the configured credentials. |
| 343 | `get_guest_customization_specs_rest` | List guest OS customization specifications via the vCenter REST API. |
| 344 | `update_tenant` | Update tenant resource configuration (requires vSphere 7.0u2+ with multi-tenancy). |

## network_ext.py (13 tools)

| # | Tool | Description |
|---|------|-------------|
| 345 | `configure_dvs_netflow` | Configure NetFlow/IPFIX on a Distributed Virtual Switch. |
| 346 | `get_dvs_netflow_config` | Get NetFlow/IPFIX configuration for a Distributed Virtual Switch. |
| 347 | `configure_dvs_port_mirror` | Configure port mirroring (SPAN) session on a Distributed Virtual Switch. |
| 348 | `list_dvs_port_mirror_sessions` | List port mirroring (SPAN) sessions on a Distributed Virtual Switch. |
| 349 | `delete_dvs_port_mirror_session` | Delete a port mirroring (SPAN) session from a Distributed Virtual Switch. |
| 350 | `set_dvs_discovery_protocol` | Set the link discovery protocol (CDP or LLDP) on a Distributed Virtual Switch. |
| 351 | `list_ip_pools` | List IP pools defined in a datacenter. |
| 352 | `create_ip_pool` | Create an IP pool in a datacenter. |
| 353 | `delete_ip_pool` | Delete an IP pool from a datacenter. |
| 354 | `configure_network_protocol_profile` | Configure network protocol profile settings on an IP pool (DNS domain, DNS servers, NTP servers). |
| 355 | `get_vm_nic_advanced_settings` | Get advanced settings for all network adapters on a VM (Wake-on-LAN, UPT, adapter type). |
| 356 | `set_vm_nic_advanced_settings` | Set advanced settings (Wake-on-LAN, UPT compatibility) on a VM network adapter. |
| 357 | `configure_mac_address_pool` | Configure the MAC address range prefix used by vCenter for auto-generated MAC addresses. |

## networking.py (15 tools)

| # | Tool | Description |
|---|------|-------------|
| 358 | `get_dvswitch_config` | Get configuration details of a Distributed Virtual Switch. |
| 359 | `get_dvportgroup_config` | Get configuration of a Distributed Virtual Portgroup. |
| 360 | `create_dvswitch` | Create a new Distributed Virtual Switch in a datacenter. |
| 361 | `create_dvportgroup` | Create a Distributed Virtual Portgroup on a DVSwitch. |
| 362 | `add_host_portgroup` | Add a standard portgroup to an ESXi host's vSwitch. |
| 363 | `remove_host_portgroup` | Remove a standard portgroup from an ESXi host. |
| 364 | `delete_dvswitch` | Destroy a Distributed Virtual Switch. |
| 365 | `delete_dvportgroup` | Destroy a Distributed Virtual Portgroup. |
| 366 | `update_dvportgroup` | Update configuration of a Distributed Virtual Portgroup. |
| 367 | `update_dvswitch` | Update configuration of a Distributed Virtual Switch. |
| 368 | `add_host_to_dvswitch` | Add an ESXi host to a Distributed Virtual Switch. |
| 369 | `remove_host_from_dvswitch` | Remove an ESXi host from a Distributed Virtual Switch. |
| 370 | `list_dvswitch_ports` | List ports on a Distributed Virtual Switch. |
| 371 | `configure_dvs_pvlan` | Configure Private VLAN (PVLAN) on a Distributed Virtual Switch. |
| 372 | `configure_host_vswitch_nic_teaming` | Configure NIC teaming policy on a standard vSwitch on an ESXi host. |

## nioc.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 373 | `get_dvs_nioc_config` | Get Network I/O Control (NIOC) configuration on a Distributed Virtual Switch. |
| 374 | `enable_disable_dvs_nioc` | Enable or disable Network I/O Control (NIOC) on a Distributed Virtual Switch. |
| 375 | `list_dvs_nioc_resource_pools` | List Network I/O Control resource pools on a Distributed Virtual Switch. |
| 376 | `configure_dvs_nioc_resource_pool` | Configure a Network I/O Control resource pool on a Distributed Virtual Switch. |
| 377 | `set_vm_nioc_network_allocation` | Set per-VM NIC bandwidth allocation for Network I/O Control. |

## ovf.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 378 | `export_vm_as_ovf` | Initiate an OVF export lease for a virtual machine and return download URLs. |
| 379 | `import_ovf` | Import an OVF/OVA into vSphere from a URL using pyVmomi ImportVApp. |
| 380 | `capture_vm_to_library` | Capture a virtual machine to a content library as an OVF item. |
| 381 | `upload_file_to_library_item` | Upload a file from a URL into a content library item via an update session. |
| 382 | `list_ovf_deploy_options` | List deployment options (OVF properties, networks, storage) for a library item. |

## pci_passthrough.py (9 tools)

| # | Tool | Description |
|---|------|-------------|
| 383 | `list_host_pci_devices` | List PCI devices on an ESXi host. |
| 384 | `enable_pci_passthrough` | Enable or disable PCI passthrough for a device on an ESXi host. |
| 385 | `add_pci_passthrough_to_vm` | Add a PCI passthrough device to a VM. |
| 386 | `remove_pci_device_from_vm` | Remove a PCI passthrough device from a VM by its device label. |
| 387 | `list_host_sriov_nics` | List SR-IOV capable NICs on an ESXi host. |
| 388 | `list_host_gpu_devices` | List GPU (display controller) PCI devices on an ESXi host. |
| 389 | `list_host_vgpu_profiles` | List vGPU profiles available on an ESXi host. |
| 390 | `add_vgpu_to_vm` | Add a vGPU profile to a VM. |
| 391 | `get_vm_pci_devices` | List PCI passthrough and vGPU devices attached to a VM. |

## performance.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 392 | `get_vm_performance` | Get CPU and memory performance metrics for a VM. Uses real-time stats when available. |
| 393 | `get_host_performance` | Get CPU and memory performance metrics for an ESXi host. |
| 394 | `get_datastore_performance` | Get I/O performance metrics for a datastore. |
| 395 | `get_historical_performance` | Get historical performance data for any vSphere entity. |
| 396 | `get_custom_metrics` | Get custom performance metrics for a vSphere entity by specific counter keys. |
| 397 | `list_performance_intervals` | List all available historical performance collection intervals configured in vCenter. |
| 398 | `list_available_metrics` | List all available performance metrics for a vSphere entity. |

## power.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 399 | `power_on_vm` | Power on a virtual machine. |
| 400 | `power_off_vm` | Force power off a virtual machine. This is equivalent to pulling the power cord. |
| 401 | `shutdown_vm` | Gracefully shut down a virtual machine via VMware Tools guest OS shutdown. |
| 402 | `reboot_vm` | Reboot a virtual machine via VMware Tools guest OS reboot. |
| 403 | `suspend_vm` | Suspend (hibernate) a running virtual machine. |
| 404 | `reset_vm` | Hard reset a virtual machine (no graceful shutdown). |

## resources.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 405 | `set_vm_resources` | Change CPU and/or memory for a VM. VM may need to be powered off for changes to take effect. |
| 406 | `add_disk` | Add a new virtual disk to a VM. |
| 407 | `add_nic` | Add a new network adapter to a VM. |
| 408 | `add_vm_cd_drive` | Add a CD/DVD drive to a VM. |
| 409 | `set_vm_cpu_allocation` | Set CPU reservation, limit, and/or shares for a VM. |
| 410 | `set_vm_memory_allocation` | Set memory reservation, limit, and/or shares for a VM. |
| 411 | `set_vm_memory_hotadd` | Enable or disable memory hot-add for a VM. VM must be powered off. |
| 412 | `set_vm_latency_sensitivity` | Set the latency sensitivity level for a VM. |

## scheduled_tasks.py (3 tools)

| # | Tool | Description |
|---|------|-------------|
| 413 | `list_scheduled_tasks` | List all scheduled tasks defined in vCenter. |
| 414 | `delete_scheduled_task` | Delete a scheduled task by name. |
| 415 | `run_scheduled_task` | Run a scheduled task immediately by name. |

## sdrs.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 416 | `get_sdrs_placement_recommendations` | Get Storage DRS placement recommendations for a datastore cluster (pod). |
| 417 | `apply_sdrs_recommendation` | Apply a Storage DRS recommendation by its key. |
| 418 | `list_compute_policies` | List all compute policies defined in vCenter. |
| 419 | `create_compute_policy` | Create a new compute policy in vCenter. |
| 420 | `get_compute_policy` | Get details of a specific compute policy. |
| 421 | `delete_compute_policy` | Delete a compute policy from vCenter. |

## search_index.py (17 tools)

| # | Tool | Description |
|---|------|-------------|
| 422 | `find_vm_by_ip` | Find a virtual machine by its IP address using the vSphere SearchIndex. |
| 423 | `find_vm_by_uuid` | Find a virtual machine by its UUID using the vSphere SearchIndex. |
| 424 | `find_vm_by_dns_name` | Find a virtual machine by its DNS name using the vSphere SearchIndex. |
| 425 | `find_by_inventory_path` | Find any inventory entity by its full inventory path using the vSphere SearchIndex. |
| 426 | `create_alarm_with_action` | Create an alarm with email or SNMP action on a vSphere entity. |
| 427 | `list_event_history_collectors` | List available event history collectors and recent event counts from the event manager. |
| 428 | `get_vcenter_topology` | Get vCenter linked mode / multi-vCenter topology nodes via the REST API. |
| 429 | `list_solution_users` | List solution users (service accounts) registered in vCenter via the REST API. |
| 430 | `get_host_full_datetime_config` | Get the full date/time configuration including NTP and PTP settings for an ESXi host. |
| 431 | `set_host_time_method` | Set the time synchronization method (NTP) for an ESXi host. |
| 432 | `get_vcenter_appliance_access` | Get shell, SSH, and DCUI access settings for the vCenter appliance. |
| 433 | `set_vcenter_appliance_access` | Set shell, SSH, and/or DCUI access settings for the vCenter appliance. |
| 434 | `get_vcenter_ntp_config` | Get the NTP server configuration for the vCenter appliance. |
| 435 | `set_vcenter_ntp_config` | Set the NTP server configuration for the vCenter appliance. |
| 436 | `get_vcenter_proxy_config` | Get the HTTP/HTTPS proxy configuration for the vCenter appliance. |
| 437 | `get_vcenter_dns_config` | Get the DNS server configuration for the vCenter appliance. |
| 438 | `get_host_network_health` | Get network health information for an ESXi host, including NIC and DVS health. |

## security.py (10 tools)

| # | Tool | Description |
|---|------|-------------|
| 439 | `list_identity_sources` | List SSO (Single Sign-On) identity sources configured in vCenter. |
| 440 | `get_sso_domain_info` | Get SSO domain configuration including domain name and authentication settings. |
| 441 | `list_sso_users` | List users in the SSO domain (best-effort; may not be available on all versions). |
| 442 | `get_password_policy` | Get the global password policy for local vCenter appliance accounts. |
| 443 | `set_password_policy` | Set the global password policy for local vCenter appliance accounts. |
| 444 | `get_login_banner` | Get the vCenter login banner (Message of the Day) shown on the login screen. |
| 445 | `set_login_banner` | Set the vCenter login banner (Message of the Day) displayed on the login screen. |
| 446 | `get_trust_authority_clusters` | List vSphere Trust Authority (vTA) clusters configured in the environment. |
| 447 | `get_trust_authority_attestation_services` | List Trust Authority attestation services configured in the environment. |
| 448 | `configure_trust_authority_kms` | Configure a Trust Authority Key Management Server (KMS) provider. |

## snapshot.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 449 | `create_snapshot` | Create a snapshot of a virtual machine. |
| 450 | `revert_snapshot` | Revert a virtual machine to a named snapshot. |
| 451 | `remove_snapshot` | Remove a snapshot from a virtual machine. |
| 452 | `remove_all_snapshots` | Remove all snapshots from a virtual machine at once. |
| 453 | `rename_snapshot` | Rename a snapshot and/or update its description. |
| 454 | `revert_to_current_snapshot` | Revert a VM to its current (most recent) snapshot. |
| 455 | `consolidate_vm_disks` | Consolidate redundant redo log files for a VM's disks. |

## storage.py (21 tools)

| # | Tool | Description |
|---|------|-------------|
| 456 | `get_datastore_info` | Get detailed information for a specific datastore including host and VM counts. |
| 457 | `get_storage_summary` | Get overall storage summary across all datastores. |
| 458 | `list_host_storage_devices` | List SCSI LUNs and HBAs on an ESXi host. |
| 459 | `list_host_multipath_info` | List multipath policies for LUNs on an ESXi host. |
| 460 | `rescan_host_storage` | Rescan all HBAs and VMFS on an ESXi host to discover new storage. |
| 461 | `mount_nfs_datastore` | Mount an NFS datastore on an ESXi host. |
| 462 | `unmount_datastore` | Unmount a datastore from an ESXi host. |
| 463 | `rename_datastore` | Rename a datastore. |
| 464 | `refresh_datastore` | Refresh a datastore to update its storage information. |
| 465 | `enter_datastore_maintenance_mode` | Put a datastore into maintenance mode. |
| 466 | `exit_datastore_maintenance_mode` | Take a datastore out of maintenance mode. |
| 467 | `set_multipath_policy` | Set the multipath policy for a LUN on an ESXi host. |
| 468 | `list_datastore_hosts` | List all ESXi hosts that have a datastore mounted. |
| 469 | `create_vmfs_datastore` | Create a VMFS datastore on an ESXi host. |
| 470 | `expand_vmfs_datastore` | Expand a VMFS datastore to use all available space on its device. |
| 471 | `enable_iscsi_adapter` | Enable the software iSCSI adapter on an ESXi host. |
| 472 | `add_iscsi_target` | Add an iSCSI send target to an ESXi host's iSCSI HBA. |
| 473 | `create_datastore_cluster` | Create a datastore cluster (StoragePod) in a datacenter. |
| 474 | `configure_storage_drs` | Configure Storage DRS on a datastore cluster. |
| 475 | `list_datastore_clusters` | List all datastore clusters (StoragePods) in the vSphere environment. |
| 476 | `configure_sioc` | Configure Storage I/O Control (SIOC) on a datastore. |

## storage_ops_ext.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 477 | `get_vaai_status` | Get VAAI (vStorage APIs for Array Integration) hardware acceleration status per LUN on an ESXi host. |
| 478 | `unmap_vmfs_datastore` | Reclaim dead/deleted space on a VMFS datastore using the UNMAP primitive. |
| 479 | `list_vasa_providers` | List VASA (vSphere APIs for Storage Awareness) storage providers registered with vCenter. |
| 480 | `register_vasa_provider` | Register a VASA storage provider with vCenter. |
| 481 | `unregister_vasa_provider` | Unregister a VASA storage provider from vCenter. |
| 482 | `get_vvol_datastore_info` | Get detailed information about a VVol (Virtual Volumes) datastore. |
| 483 | `configure_sioc_per_vm` | Configure Storage I/O Control (SIOC) with per-VM granularity on a datastore. |
| 484 | `configure_nfs41_kerberos` | Configure Kerberos authentication for an NFS 4.1 datastore on an ESXi host. |

## storage_policy.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 485 | `list_storage_policies` | List all VM storage policies (SPBM) defined in vCenter. |
| 486 | `get_storage_policy` | Get detailed information about a specific VM storage policy. |
| 487 | `create_storage_policy` | Create a new VM storage policy (SPBM). |
| 488 | `delete_storage_policy` | Delete a VM storage policy by ID. |
| 489 | `assign_storage_policy_to_vm` | Assign a VM storage policy to a virtual machine. |
| 490 | `get_vm_storage_policy_compliance` | Check the storage policy compliance status of a virtual machine. |
| 491 | `get_compatible_datastores` | List datastores that are compatible with a given VM storage policy. |

## tags.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 492 | `get_vm_annotation` | Get the annotation (notes) for a virtual machine. |
| 493 | `set_vm_annotation` | Set the annotation (notes) for a virtual machine. |
| 494 | `get_custom_attributes` | List all custom attribute definitions in vCenter. |
| 495 | `create_custom_attribute` | Create a custom attribute definition. |
| 496 | `set_custom_attribute_value` | Set a custom attribute value on an entity. |
| 497 | `get_entity_custom_attribute_values` | Get all custom attribute values on an entity. |
| 498 | `delete_custom_attribute` | Delete a custom attribute definition from vCenter. |

## tanzu.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 499 | `list_namespaces` | List all vSphere Namespaces (Tanzu Kubernetes Grid namespaces). |
| 500 | `get_namespace` | Get detailed information about a vSphere Namespace. |
| 501 | `create_namespace` | Create a vSphere Namespace. |
| 502 | `delete_namespace` | Delete a vSphere Namespace. This operation is irreversible and removes all workloads. |
| 503 | `update_namespace` | Update resource quotas for a vSphere Namespace. |
| 504 | `list_wcp_clusters` | List all clusters with Workload Management (vSphere with Tanzu) enabled. |
| 505 | `get_wcp_cluster_status` | Get Workload Management status for a specific cluster. |

## trusted_infra.py (7 tools)

| # | Tool | Description |
|---|------|-------------|
| 506 | `list_trusted_kms_providers` | List Key Management Server (KMS) providers registered with the Trusted Infrastructure service. |
| 507 | `get_trusted_cluster_attestation_report` | Get the attestation report for a Trusted Cluster. |
| 508 | `configure_trust_authority_host` | Enable or disable Trust Authority on a host. |
| 509 | `list_trust_authority_hosts` | List all hosts enrolled in the Trusted Infrastructure service. |
| 510 | `query_compatible_hosts_for_dvs` | Query hosts compatible with creating a new Distributed Virtual Switch. |
| 511 | `query_dvs_feature_capability` | Query the feature capabilities of a Distributed Virtual Switch product. |
| 512 | `query_available_dvs_specs` | Query the available Distributed Virtual Switch product specifications. |

## vapp.py (4 tools)

| # | Tool | Description |
|---|------|-------------|
| 513 | `list_vapps` | List all vApps in the vCenter inventory. |
| 514 | `power_on_vapp` | Power on a vApp. |
| 515 | `power_off_vapp` | Power off a vApp. |
| 516 | `delete_vapp` | Permanently delete a vApp and all its contents. |

## vapp_ext.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 517 | `create_vapp` | Create a new vApp container in the specified resource pool. |
| 518 | `configure_vapp_start_order` | Configure the VM start order within a vApp. |
| 519 | `get_vapp_config` | Get configuration details for a vApp, including product info and entity start order. |
| 520 | `update_vapp_properties` | Update OVF properties for a vApp. |
| 521 | `suspend_vapp` | Suspend all VMs in a vApp. |
| 522 | `clone_vapp` | Clone a vApp to a new vApp with a different name. |

## vcenter_admin.py (14 tools)

| # | Tool | Description |
|---|------|-------------|
| 523 | `list_roles` | List all roles defined in vCenter with their privileges. |
| 524 | `get_entity_permissions` | Get permissions assigned to a vSphere entity. |
| 525 | `get_license_info` | Get vCenter license information with masked license keys. |
| 526 | `list_active_sessions` | List active sessions on vCenter. |
| 527 | `list_recent_tasks` | List recent tasks from vCenter task manager. |
| 528 | `terminate_session` | Terminate a specific vCenter session by session key. |
| 529 | `create_role` | Create a new authorization role in vCenter. |
| 530 | `update_role` | Update an existing authorization role's privileges in vCenter. |
| 531 | `delete_role` | Delete an authorization role from vCenter. |
| 532 | `set_entity_permissions` | Set permissions on a vSphere entity for a principal. |
| 533 | `remove_entity_permission` | Remove a permission assignment from a vSphere entity. |
| 534 | `cancel_task` | Cancel a running or queued vCenter task. |
| 535 | `list_privileges` | List all available privileges defined in vCenter. |
| 536 | `acknowledge_alarm` | Acknowledge all triggered alarms on a vSphere entity. |

## vcenter_rest_ext.py (11 tools)

| # | Tool | Description |
|---|------|-------------|
| 537 | `list_content_registries` | List Harbor container registries registered with vCenter. |
| 538 | `get_datastore_default_policy` | Get the default storage policy for a datastore. |
| 539 | `mount_iso_to_vm_rest` | Mount an ISO image from a content library item to a VM's CD-ROM via REST API. |
| 540 | `unmount_iso_from_vm_rest` | Unmount an ISO image from a VM's CD-ROM via REST API. |
| 541 | `get_hvc_links` | List Hybrid Linked Mode (HVC) links between vCenter instances. |
| 542 | `list_consumption_domains` | List consumption domain zones configured in vCenter. |
| 543 | `get_vcenter_system_config` | Get vCenter deployment and system configuration information. |
| 544 | `deploy_vm_from_library_template` | Deploy a new VM from a VM template stored in a content library. |
| 545 | `get_vm_guest_power_state_rest` | Get the guest OS power state for a VM via REST API. |
| 546 | `get_storage_policy_entity_compliance` | Get storage policy compliance status for VM entities. |
| 547 | `list_vcenter_networks_rest` | List networks visible in vCenter via REST API. |

## vcenter_services.py (10 tools)

| # | Tool | Description |
|---|------|-------------|
| 548 | `get_vcenter_health` | Get the overall health status of the vCenter appliance. |
| 549 | `list_vcenter_services` | List all vCenter appliance services with their current state and startup type. |
| 550 | `restart_vcenter_service` | Restart a vCenter appliance service. |
| 551 | `start_vcenter_service` | Start a stopped vCenter appliance service. |
| 552 | `stop_vcenter_service` | Stop a running vCenter appliance service. |
| 553 | `get_vcenter_backup_status` | List recent vCenter appliance backup jobs and their status. |
| 554 | `trigger_vcenter_backup` | Trigger a vCenter appliance backup job. |
| 555 | `get_vcenter_system_version` | Get vCenter appliance version, build number, and installation time. |
| 556 | `get_vcenter_disk_usage` | Get disk usage information for vCenter appliance partitions. |
| 557 | `get_vcenter_network_config` | Get network interface configuration for the vCenter appliance. |

## virtual_disk_mgr.py (10 tools)

| # | Tool | Description |
|---|------|-------------|
| 558 | `copy_virtual_disk` | Copy a virtual disk (VMDK) from one location to another. |
| 559 | `move_virtual_disk` | Move a virtual disk (VMDK) from one location to another. |
| 560 | `delete_virtual_disk` | Permanently delete a virtual disk (VMDK) file from a datastore. |
| 561 | `get_virtual_disk_uuid` | Get the UUID of a virtual disk (VMDK) file. |
| 562 | `set_virtual_disk_uuid` | Set the UUID of a virtual disk (VMDK) file. |
| 563 | `query_vm_config_option` | Query valid VM configuration options (hardware versions, guest OS descriptors) for a host or VM. |
| 564 | `query_vm_config_target` | Query available configuration targets (networks, datastores, devices) for a host or VM. |
| 565 | `extend_vmfs_datastore` | Add a new extent (partition) to an existing VMFS datastore. |
| 566 | `backup_dvs_config` | Export and back up the configuration of a Distributed Virtual Switch. |
| 567 | `restore_dvs_config` | Restore or import a Distributed Virtual Switch configuration from a backup blob. |

## vlcm.py (8 tools)

| # | Tool | Description |
|---|------|-------------|
| 568 | `list_vlcm_images` | List the desired software image configured for a vLCM-managed cluster. |
| 569 | `get_vlcm_cluster_compliance` | Get the software compliance status for all hosts in a vLCM-managed cluster. |
| 570 | `apply_vlcm_image` | Remediate a vLCM-managed cluster by applying the desired software image to all hosts. |
| 571 | `scan_host_for_patches` | Scan an ESXi host for patch compliance against the desired software image. |
| 572 | `get_host_patch_compliance` | Get the patch compliance status for an ESXi host. |
| 573 | `remediate_host` | Apply the desired software image to an ESXi host (will reboot the host). |
| 574 | `stage_patches_to_host` | Pre-download (stage) patches to an ESXi host without applying them. |
| 575 | `get_vlcm_base_images` | List all available ESXi base images in the vLCM software depot. |

## vm_boot_rest.py (4 tools)

| # | Tool | Description |
|---|------|-------------|
| 576 | `get_vm_boot_device_order` | Get the boot device order for a VM via the REST API. |
| 577 | `set_vm_boot_device_order` | Set the boot device order for a VM via the REST API. |
| 578 | `install_vm_tools` | Initiate VMware Tools installation on a VM via the REST API. |
| 579 | `upgrade_vm_tools_rest` | Upgrade VMware Tools on a VM via the REST API. |

## vm_devices.py (26 tools)

| # | Tool | Description |
|---|------|-------------|
| 580 | `remove_disk` | Remove a virtual disk from a VM. |
| 581 | `expand_disk` | Expand a virtual disk to a new size. The new size must be larger than the current size. |
| 582 | `remove_nic` | Remove a network adapter from a VM. Example: nic_label='Network adapter 1'. |
| 583 | `list_vm_controllers` | List all SCSI/IDE/SATA controllers on a VM with their connected devices. |
| 584 | `get_vm_extra_config` | Get VM extraConfig key/value pairs. Optionally filter by key prefix. |
| 585 | `set_vm_extra_config` | Set a VM extraConfig key/value pair. |
| 586 | `rename_vm` | Rename a virtual machine. |
| 587 | `unregister_vm` | Unregister a VM from the inventory without deleting its files. VM must be powered off. |
| 588 | `get_vm_console_url` | Acquire a WebMKS console ticket for a VM. May not work in all environments. |
| 589 | `set_vm_boot_options` | Set VM boot options (delay, BIOS setup, retry, EFI Secure Boot). |
| 590 | `list_vm_cddvd_drives` | List CD/DVD drives on a VM with ISO mount status and connected state. |
| 591 | `mount_vm_cdrom_iso` | Mount an ISO file to a VM CD/DVD drive. Example: cdrom_label='CD/DVD drive 1', iso_path='iso/ubuntu.iso'. |
| 592 | `disconnect_vm_cdrom` | Disconnect a CD/DVD drive (switch to client device). cdrom_label example: 'CD/DVD drive 1'. |
| 593 | `get_vm_video_card` | Get video card settings for a VM (video RAM, displays, 3D rendering). |
| 594 | `list_vm_disk_layout` | Get detailed disk layout for a VM: capacity, backing file, thin provisioning, disk mode. |
| 595 | `list_vm_snapshots_disk_usage` | Get snapshot disk usage for a VM using layoutEx to find snapshot files and their sizes. |
| 596 | `change_vm_nic_network` | Change an existing NIC to a different network/portgroup. Example: nic_label='Network adapter 1'. |
| 597 | `connect_disconnect_vm_nic` | Toggle a NIC connected state on a VM. |
| 598 | `add_vm_scsi_controller` | Add a SCSI/PVSCSI controller to a VM. controller_type: 'pvscsi', 'lsilogic', or 'lsilogicsas'. |
| 599 | `upgrade_vm_hardware` | Upgrade virtual hardware version for a VM. VM must be powered off. |
| 600 | `set_vm_cpu_hotadd` | Enable or disable CPU and/or memory hot-add for a VM. |
| 601 | `set_vm_cores_per_socket` | Set the number of cores per socket for a VM. |
| 602 | `change_vm_disk_mode` | Change disk mode for a virtual disk. |
| 603 | `add_vtpm` | Add a Virtual Trusted Platform Module (vTPM) device to a VM. |
| 604 | `set_vm_secure_boot` | Enable or disable EFI Secure Boot for a VM. |
| 605 | `configure_vm_vbs` | Enable or disable Virtualization Based Security (VBS) for a VM. |

## vm_devices_ext.py (12 tools)

| # | Tool | Description |
|---|------|-------------|
| 606 | `add_vm_serial_port` | Add a serial port to a VM. |
| 607 | `remove_vm_serial_port` | Remove a serial port from a VM by its device label. |
| 608 | `list_vm_serial_ports` | List all serial ports on a VM with backing type and connection info. |
| 609 | `add_vm_parallel_port` | Add a parallel port with file backing to a VM. |
| 610 | `remove_vm_parallel_port` | Remove a parallel port from a VM by its device label. |
| 611 | `add_vm_usb_controller` | Add a USB controller to a VM. |
| 612 | `add_vm_usb_device` | Add a USB passthrough device to a VM. |
| 613 | `remove_vm_usb_device` | Remove a USB device from a VM by its device label. |
| 614 | `add_vm_floppy_drive` | Add a floppy drive to a VM, optionally with an image file backing. |
| 615 | `remove_vm_floppy_drive` | Remove a floppy drive from a VM by its device label. |
| 616 | `configure_vm_shared_folders` | Configure an HGFS shared folder on a VM (requires VMware Tools). |
| 617 | `add_vm_nvme_controller` | Add an NVMe controller to a VM. |

## vm_methods_ext.py (6 tools)

| # | Tool | Description |
|---|------|-------------|
| 618 | `promote_vm_disks` | Promote linked clone disks to full independent disks. |
| 619 | `terminate_vm` | Force-terminate a VM process immediately without a graceful shutdown. |
| 620 | `mount_tools_installer` | Mount the VMware Tools installer ISO into the VM's CD/DVD drive. |
| 621 | `unmount_tools_installer` | Unmount the VMware Tools installer CD from the VM's CD/DVD drive. |
| 622 | `query_ft_compatibility` | Check Fault Tolerance (FT) compatibility for a VM. |
| 623 | `query_vm_unowned_files` | Find files in a VM's directory that are not registered as part of the VM. |

## vm_monitoring.py (5 tools)

| # | Tool | Description |
|---|------|-------------|
| 624 | `set_vm_monitoring` | Configure HA VM monitoring settings for a virtual machine. |
| 625 | `get_vm_monitoring_state` | Get the HA VM monitoring configuration for a virtual machine. |
| 626 | `get_vm_uptime` | Get uptime information for a virtual machine based on its boot time. |
| 627 | `export_vm_configuration` | Export the configuration of a virtual machine as a structured dictionary. |
| 628 | `find_orphaned_vmdks` | Find VMDK files on a datastore that are not attached to any registered VM. |

## vm_ops_ext.py (11 tools)

| # | Tool | Description |
|---|------|-------------|
| 629 | `query_vmotion_compatibility` | Check vMotion compatibility between a VM and a target ESXi host. |
| 630 | `check_migrate` | Check migration feasibility for a VM to a target host and/or datastore. |
| 631 | `standby_guest` | Put the guest OS of a virtual machine into standby (sleep) mode. |
| 632 | `acquire_vmrc_ticket` | Acquire a remote console ticket for a virtual machine. |
| 633 | `get_vm_disk_chain_info` | Get the disk backing chain (snapshot parent chain) for all virtual disks of a VM. |
| 634 | `shrink_vm_disk` | Shrink a thin-provisioned virtual disk to reclaim unused space. |
| 635 | `defragment_vm_disk` | Defragment a virtual disk to consolidate free space. |
| 636 | `inflate_vm_disk` | Inflate a thin-provisioned virtual disk to eagerly zeroed thick format. |
| 637 | `zero_fill_vm_disk` | Zero-fill a virtual disk, overwriting all blocks with zeros. |
| 638 | `query_compatible_hosts_for_vm` | Find all ESXi hosts that are compatible with a VM for placement or migration. |
| 639 | `create_scheduled_power_operation` | Schedule a power operation (power on/off, suspend, reset) for a virtual machine. |

## vsan.py (9 tools)

| # | Tool | Description |
|---|------|-------------|
| 640 | `get_vsan_cluster_config` | Get vSAN cluster configuration including enabled state, UUID, auto-claim, and fault domains. |
| 641 | `get_vsan_health_summary` | Get vSAN health summary for a cluster based on host-level vSAN status. |
| 642 | `list_vsan_disk_groups` | List vSAN disk groups per host in a cluster, showing cache and capacity disks. |
| 643 | `add_vsan_disk_group` | Add a vSAN disk group to a host. |
| 644 | `remove_vsan_disk_group` | Remove a vSAN disk group from a host by its cache tier SSD canonical name. |
| 645 | `get_vsan_resync_status` | Get vSAN resync status for a cluster, reporting resyncing object counts per host. |
| 646 | `set_vsan_cluster_config` | Configure vSAN settings on a cluster. |
| 647 | `get_vsan_disk_info` | Get detailed vSAN disk information for a host including disk state and capacity. |
| 648 | `evacuate_vsan_data_from_host` | Evacuate vSAN data from a host before maintenance by entering maintenance mode with a vSAN evacuation spec. |

## vsphere_tags.py (9 tools)

| # | Tool | Description |
|---|------|-------------|
| 649 | `create_tag_category` | Create a vSphere tag category. |
| 650 | `list_tag_categories` | List all vSphere tag categories with their details. |
| 651 | `delete_tag_category` | Delete a vSphere tag category by ID. This also deletes all tags in the category. |
| 652 | `create_tag` | Create a vSphere tag in a category. |
| 653 | `list_tags` | List all vSphere tags with their details. |
| 654 | `delete_tag` | Delete a vSphere tag by ID. |
| 655 | `attach_tag` | Attach a vSphere tag to an entity. |
| 656 | `detach_tag` | Detach a vSphere tag from an entity. |
| 657 | `list_attached_tags` | List all tags attached to a vSphere entity. |
