# 未実装機能ギャップ分析（v0.4.0 時点）

現在 413 ツール実装済み。以下は未実装の vSphere/vCenter API 機能一覧（全て pyVmomi または vSphere REST API で実装可能）。

---

## 1. VM デバイス管理 — 12個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 1 | `add_vm_serial_port` | シリアルポート追加（ネットワーク/ファイル/パイプ） | pyVmomi: `VirtualSerialPort` + `VirtualDeviceSpec` |
| 2 | `remove_vm_serial_port` | シリアルポート削除 | pyVmomi: `VirtualDeviceSpec(operation=remove)` |
| 3 | `list_vm_serial_ports` | シリアルポート一覧 | pyVmomi: `vm.config.hardware.device` |
| 4 | `add_vm_parallel_port` | パラレルポート追加 | pyVmomi: `VirtualParallelPort` |
| 5 | `remove_vm_parallel_port` | パラレルポート削除 | pyVmomi: `VirtualDeviceSpec` |
| 6 | `add_vm_usb_controller` | USB 2.0/3.0 コントローラ追加 | pyVmomi: `VirtualUSBController` / `VirtualUSBXHCIController` |
| 7 | `add_vm_usb_device` | USB パススルーデバイス追加 | pyVmomi: `VirtualUSB` |
| 8 | `remove_vm_usb_device` | USB デバイス削除 | pyVmomi: `VirtualDeviceSpec` |
| 9 | `add_vm_floppy_drive` | フロッピードライブ追加 | pyVmomi: `VirtualFloppy` |
| 10 | `remove_vm_floppy_drive` | フロッピードライブ削除 | pyVmomi: `VirtualDeviceSpec` |
| 11 | `configure_vm_shared_folders` | HGFS 共有フォルダ設定 | pyVmomi: `ConfigSpec.sharedFolder` |
| 12 | `add_vm_nvme_controller` | NVMe コントローラ追加 | pyVmomi: `VirtualNVMEController` |

## 2. VM 操作 — 11個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 13 | `query_vmotion_compatibility` | vMotion 互換性チェック | pyVmomi: `vm.QueryVMotionCompatibilityEx_Task()` |
| 14 | `check_migrate` | マイグレーション実行可能性検証 | pyVmomi: `vmProvisioningChecker.CheckMigrate_Task()` |
| 15 | `standby_guest` | ゲスト OS スタンバイ（S1/S3） | pyVmomi: `vm.StandbyGuest()` |
| 16 | `acquire_vmrc_ticket` | VMRC リモートコンソールチケット取得 | pyVmomi: `vm.AcquireTicket("vmrc")` |
| 17 | `get_vm_disk_chain_info` | ディスク親チェーン情報取得 | pyVmomi: `device[].backing.parent` 走査 |
| 18 | `shrink_vm_disk` | シンプロビジョニングディスク縮小 | pyVmomi: `VirtualDiskManager.ShrinkVirtualDisk_Task()` |
| 19 | `defragment_vm_disk` | 仮想ディスクデフラグ | pyVmomi: `VirtualDiskManager.DefragmentVirtualDisk_Task()` |
| 20 | `inflate_vm_disk` | シンディスクをシックに膨張 | pyVmomi: `VirtualDiskManager.InflateVirtualDisk_Task()` |
| 21 | `zero_fill_vm_disk` | 仮想ディスクゼロフィル | pyVmomi: `VirtualDiskManager.ZeroFillVirtualDisk_Task()` |
| 22 | `query_compatible_hosts_for_vm` | VM 互換ホスト検索 | pyVmomi: `vmProvisioningChecker.CheckMigrate_Task()` |
| 23 | `create_scheduled_power_operation` | VM 電源スケジュール登録 | pyVmomi: `ScheduledTaskManager` + PowerOn/Off |

## 3. ホスト操作 — 18個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 24 | `get_host_snmp_config` | ESXi SNMP エージェント設定取得 | pyVmomi: `snmpSystem.configuration` |
| 25 | `set_host_snmp_config` | SNMP 設定変更（コミュニティ/トラップ） | pyVmomi: `snmpSystem.ReconfigureSnmpAgent()` |
| 26 | `get_host_coredump_config` | ESXi コアダンプ設定取得 | pyVmomi: `diagnosticSystem` |
| 27 | `set_host_coredump_config` | ネットワークコアダンプターゲット設定 | pyVmomi: `diagnosticSystem.ConfigureNetworkCoreDump()` |
| 28 | `get_host_autostart_config` | VM 自動起動順序設定取得 | pyVmomi: `autoStartManager.config` |
| 29 | `set_host_autostart_config` | VM 自動起動/停止順序設定 | pyVmomi: `autoStartManager.ReconfigureAutostart()` |
| 30 | `get_host_swap_config` | ホストスワップ設定取得 | pyVmomi: `host.config.systemSwapConfiguration` |
| 31 | `set_host_swap_datastore` | スワップデータストア設定 | pyVmomi: advanced setting |
| 32 | `get_host_tpm_attestation` | ホスト TPM アテステーション状態 | pyVmomi: `host.runtime.tpmPcrValues` |
| 33 | `get_host_image_profile` | インストール済みイメージプロファイル | pyVmomi: `host.config.imageConfig` |
| 34 | `get_host_vibs` | インストール済み VIB 一覧 | REST: `/api/esx/software/installed-components` |
| 35 | `get_host_fc_hba_info` | FC HBA 詳細（WWN/ポート状態） | pyVmomi: `hostBusAdapter` filter `HostFibreChannelHba` |
| 36 | `get_host_cpu_features` | CPU 機能フラグ/ケーパビリティ | pyVmomi: `host.hardware.cpuFeature` |
| 37 | `get_host_graphics_config` | グラフィックス設定取得 | pyVmomi: `graphicsManager.graphicsConfig` |
| 38 | `set_host_graphics_config` | グラフィックス割り当てモード設定 | pyVmomi: `graphicsManager.UpdateGraphicsConfig()` |
| 39 | `get_host_cim_provider_status` | CIM/WBEM プロバイダ状態 | pyVmomi: `healthStatusSystem.runtime` |
| 40 | `get_host_agent_vm_settings` | ESX Agent Manager 設定取得 | pyVmomi: `esxAgentHostManager.configInfo` |
| 41 | `set_host_agent_vm_settings` | ESX Agent データストア/ネットワーク設定 | pyVmomi: `esxAgentHostManager.EsxAgentHostManagerUpdateConfig()` |

## 4. クラスタ操作 — 12個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 42 | `set_drs_vm_override` | VM 単位 DRS 自動化レベル設定 | pyVmomi: `ClusterConfigSpecEx(drsVmConfigSpec=[...])` |
| 43 | `list_drs_vm_overrides` | VM 単位 DRS オーバーライド一覧 | pyVmomi: `cluster.configuration.drsVmConfig[]` |
| 44 | `set_ha_vm_override` | VM 単位 HA 再起動優先度設定 | pyVmomi: `ClusterConfigSpecEx(dasVmConfigSpec=[...])` |
| 45 | `list_ha_vm_overrides` | VM 単位 HA オーバーライド一覧 | pyVmomi: `cluster.configuration.dasVmConfig[]` |
| 46 | `configure_ha_heartbeat_datastores` | HA ハートビートデータストア設定 | pyVmomi: `DasConfigInfo.heartbeatDatastore` |
| 47 | `get_vcha_config` | vCenter HA (VCHA) 構成取得 | REST: `/api/vcenter/vcha/cluster` |
| 48 | `configure_vcha` | vCenter HA デプロイ/構成 | REST: `/api/vcenter/vcha/cluster` POST |
| 49 | `get_vcha_mode` | VCHA モード取得 | REST: `/api/vcenter/vcha/cluster/mode` |
| 50 | `set_vcha_mode` | VCHA モード設定 | REST: `/api/vcenter/vcha/cluster/mode` PUT |
| 51 | `get_cluster_resource_summary` | クラスタリソース使用量サマリー | pyVmomi: `cluster.GetResourceUsage()` |
| 52 | `set_storage_drs_vm_override` | VM 単位 Storage DRS オーバーライド | pyVmomi: `storagePod.ReconfigureStoragePod_Task()` |
| 53 | `list_storage_drs_vm_overrides` | Storage DRS VM オーバーライド一覧 | pyVmomi: `storageDrsConfig.vmConfig[]` |

## 5. ネットワーク操作 — 13個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 54 | `configure_dvs_netflow` | DVS NetFlow/IPFIX 設定 | pyVmomi: `DVSConfigSpec(ipfixConfig=...)` |
| 55 | `get_dvs_netflow_config` | DVS NetFlow 設定取得 | pyVmomi: `dvs.config.ipfixConfig` |
| 56 | `configure_dvs_port_mirror` | DVS ポートミラーリングセッション設定 | pyVmomi: `VMwareVspanSession` |
| 57 | `list_dvs_port_mirror_sessions` | ポートミラーセッション一覧 | pyVmomi: `dvs.config.vspanSession[]` |
| 58 | `delete_dvs_port_mirror_session` | ポートミラーセッション削除 | pyVmomi: `ReconfigureDvs_Task` |
| 59 | `set_dvs_discovery_protocol` | CDP/LLDP ディスカバリプロトコル設定 | pyVmomi: `LinkDiscoveryProtocolConfig` |
| 60 | `list_ip_pools` | データセンター IP プール一覧 | pyVmomi: `IpPoolManager.QueryIpPools()` |
| 61 | `create_ip_pool` | IP プール作成 | pyVmomi: `IpPoolManager.CreateIpPool()` |
| 62 | `delete_ip_pool` | IP プール削除 | pyVmomi: `IpPoolManager.DestroyIpPool()` |
| 63 | `configure_network_protocol_profile` | ネットワークプロトコルプロファイル管理 | pyVmomi: `IpPoolManager` |
| 64 | `get_vm_nic_advanced_settings` | VM NIC 詳細設定取得（WoL/UPT） | pyVmomi: `VirtualEthernetCard` properties |
| 65 | `set_vm_nic_advanced_settings` | VM NIC Wake-on-LAN/UPT 設定 | pyVmomi: `VirtualDeviceSpec` |
| 66 | `configure_mac_address_pool` | MAC アドレスレンジ設定 | pyVmomi: advanced setting |

## 6. ストレージ操作 — 8個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 67 | `get_vaai_status` | VAAI ハードウェアアクセラレーション状態 | pyVmomi: `scsiLun[].capabilities` |
| 68 | `unmap_vmfs_datastore` | VMFS デッドスペース回収（UNMAP/TRIM） | pyVmomi: `UnmapVmfsVolumeEx_Task()` |
| 69 | `list_vasa_providers` | VASA ストレージプロバイダー一覧 | pyVmomi: `storageProviderManager.QueryStorageProviders()` |
| 70 | `register_vasa_provider` | VASA プロバイダー登録 | pyVmomi: `storageProviderManager.RegisterProvider()` |
| 71 | `unregister_vasa_provider` | VASA プロバイダー登録解除 | pyVmomi: `storageProviderManager.UnregisterProvider()` |
| 72 | `get_vvol_datastore_info` | VVol データストア詳細/コンテナ情報 | pyVmomi: datastore info (type=VVOL) |
| 73 | `configure_sioc_per_vm` | VM 単位 SIOC I/O シェア/リミット | pyVmomi: `ConfigureDatastoreIORM_Task()` |
| 74 | `configure_nfs41_kerberos` | NFS 4.1 Kerberos 認証設定 | pyVmomi: NAS spec `securityType="SEC_KRB5"` |

## 7. セキュリティ・ID 管理 — 10個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 75 | `list_identity_sources` | SSO ID ソース一覧 | REST: `/api/vcenter/identity/providers` |
| 76 | `get_sso_domain_info` | SSO ドメイン設定取得 | REST: `/api/vcenter/identity/info` |
| 77 | `list_sso_users` | SSO ドメインユーザー一覧 | REST |
| 78 | `get_password_policy` | パスワードポリシー取得 | REST: `/api/appliance/local-accounts/global-policy` |
| 79 | `set_password_policy` | パスワードポリシー設定 | REST: PUT |
| 80 | `get_login_banner` | vCenter ログインバナー取得 | advanced setting `vpxd.motd` |
| 81 | `set_login_banner` | vCenter ログインバナー設定 | advanced setting |
| 82 | `get_trust_authority_clusters` | Trust Authority クラスタ一覧 | REST: `/api/vcenter/trusted-infrastructure/trusted-clusters` |
| 83 | `get_trust_authority_attestation_services` | アテステーションサービス一覧 | REST |
| 84 | `configure_trust_authority_kms` | Trust Authority KMS 設定 | REST |

## 8. 監視・診断 — 6個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 85 | `generate_support_bundle` | vCenter サポートバンドル生成 | REST: `/api/appliance/support-bundle` |
| 86 | `generate_host_support_bundle` | ESXi vm-support バンドル生成 | pyVmomi: `DiagnosticManager.GenerateLogBundles_Task()` |
| 87 | `get_ceip_status` | CEIP 参加状態取得 | REST: `/api/appliance/telemetry` |
| 88 | `set_ceip_status` | CEIP 参加設定 | REST: PUT |
| 89 | `validate_syslog_forwarding` | syslog 転送テスト | REST: `/api/appliance/logging/forwarding?action=test` |
| 90 | `get_vcenter_deployment_type` | デプロイメントタイプ取得 | REST: `/api/vcenter/deployment` |

## 9. 拡張機能・プラグイン管理 — 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 91 | `list_extensions` | vCenter 拡張機能/プラグイン一覧 | pyVmomi: `extensionManager.extensionList` |
| 92 | `get_extension_info` | 拡張機能詳細取得 | pyVmomi: `extensionManager.FindExtension()` |
| 93 | `register_extension` | 拡張機能登録 | pyVmomi: `extensionManager.RegisterExtension()` |
| 94 | `unregister_extension` | 拡張機能登録解除 | pyVmomi: `extensionManager.UnregisterExtension()` |
| 95 | `update_extension` | 拡張機能メタデータ更新 | pyVmomi: `extensionManager.UpdateExtension()` |

## 10. vApp 操作 — 6個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 96 | `create_vapp` | vApp コンテナ作成 | pyVmomi: `resourcePool.CreateVApp()` |
| 97 | `configure_vapp_start_order` | vApp 内 VM 起動/停止順序設定 | pyVmomi: `vApp.UpdateVAppConfig()` |
| 98 | `get_vapp_config` | vApp 設定詳細取得 | pyVmomi: `vApp.vAppConfig` |
| 99 | `update_vapp_properties` | vApp OVF プロパティ更新 | pyVmomi: `vApp.UpdateVAppConfig()` |
| 100 | `suspend_vapp` | vApp サスペンド | pyVmomi: `vApp.SuspendVApp_Task()` |
| 101 | `clone_vapp` | vApp クローン | pyVmomi: `vApp.CloneVApp_Task()` |

## 11. ゲスト操作（拡張）— 8個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 102 | `create_guest_temp_file` | ゲスト OS 一時ファイル作成 | pyVmomi: `fileManager.CreateTemporaryFileInGuest()` |
| 103 | `create_guest_temp_directory` | ゲスト OS 一時ディレクトリ作成 | pyVmomi: `fileManager.CreateTemporaryDirectoryInGuest()` |
| 104 | `set_guest_file_attributes` | ゲストファイル権限/タイムスタンプ設定 | pyVmomi: `fileManager.ChangeFileAttributesInGuest()` |
| 105 | `read_guest_file_content` | ゲストファイル内容読み取り | pyVmomi: `InitiateFileTransferFromGuest()` + HTTP GET |
| 106 | `write_guest_file_content` | ゲストファイルに直接書き込み | pyVmomi: `InitiateFileTransferToGuest()` + HTTP PUT |
| 107 | `get_guest_windows_registry` | Windows レジストリキー読み取り | pyVmomi: `guestWindowsRegistryManager.ReadRegistryKeyValues()` |
| 108 | `set_guest_windows_registry` | Windows レジストリ値書き込み | pyVmomi: `guestWindowsRegistryManager.SetRegistryValue()` |
| 109 | `list_guest_mapped_aliases` | ゲストユーザーエイリアス一覧 | pyVmomi: `aliasManager.ListGuestAliases()` |

## 12. アラーム/自動化（拡張）— 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 110 | `create_alarm_with_action` | SNMP/メール/スクリプトアクション付きアラーム | pyVmomi: `AlarmSpec` + `AlarmTriggeringAction` |
| 111 | `list_event_history_collectors` | イベント履歴コレクタ一覧 | pyVmomi: `eventManager` |

## 13. その他 — 11個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 112 | `get_vcenter_topology` | リンクモード/マルチ vCenter トポロジ | REST: `/api/vcenter/topology/nodes` |
| 113 | `list_solution_users` | ソリューションユーザー一覧 | REST: SSO admin API |
| 114 | `get_host_full_datetime_config` | ホスト完全日時設定（PTP 含む） | pyVmomi: `dateTimeSystem.dateTimeInfo` |
| 115 | `set_host_time_method` | NTP/PTP 同期方式設定 | pyVmomi: `dateTimeSystem.UpdateDateTimeConfig()` |
| 116 | `get_vcenter_appliance_access` | vCenter シェル/SSH/DCUI アクセス設定 | REST: `/api/appliance/access/shell` |
| 117 | `set_vcenter_appliance_access` | vCenter アクセス設定変更 | REST: PUT |
| 118 | `get_vcenter_ntp_config` | vCenter アプライアンス NTP 設定 | REST: `/api/appliance/ntp` |
| 119 | `set_vcenter_ntp_config` | vCenter アプライアンス NTP 設定変更 | REST: PUT |
| 120 | `get_vcenter_proxy_config` | vCenter プロキシ設定取得 | REST: `/api/appliance/networking/proxy` |
| 121 | `get_vcenter_dns_config` | vCenter アプライアンス DNS 設定 | REST: `/api/appliance/networking/dns/servers` |
| 122 | `get_host_network_health` | ホストネットワークヘルスチェック | pyVmomi: `networkSystem` + DVS health |

---

## サマリー

| カテゴリ | ツール数 |
|----------|----------|
| VM デバイス管理 | 12 |
| VM 操作 | 11 |
| ホスト操作 | 18 |
| クラスタ操作 | 12 |
| ネットワーク操作 | 13 |
| ストレージ操作 | 8 |
| セキュリティ・ID 管理 | 10 |
| 監視・診断 | 6 |
| 拡張機能管理 | 5 |
| vApp 操作 | 6 |
| ゲスト操作（拡張） | 8 |
| アラーム/自動化 | 2 |
| その他 | 11 |
| **合計** | **122** |

実装完了後の総ツール数: **413 + 122 = 535**
