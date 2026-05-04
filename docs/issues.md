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

## 14. SearchIndex（検索）— 4個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 123 | `find_vm_by_ip` | IP アドレスで VM 検索 | pyVmomi: `searchIndex.FindByIp(ip, vmSearch=True)` |
| 124 | `find_vm_by_uuid` | UUID で VM 検索 | pyVmomi: `searchIndex.FindByUuid(uuid, vmSearch=True)` |
| 125 | `find_vm_by_dns_name` | DNS 名で VM 検索 | pyVmomi: `searchIndex.FindByDnsName(dnsName, vmSearch=True)` |
| 126 | `find_by_inventory_path` | インベントリパスでエンティティ検索 | pyVmomi: `searchIndex.FindByInventoryPath(path)` |

## 15. ESXi ローカルアカウント管理 — 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 127 | `create_esxi_local_user` | ESXi ローカルユーザー作成 | pyVmomi: `hostLocalAccountManager.CreateUser()` |
| 128 | `remove_esxi_local_user` | ESXi ローカルユーザー削除 | pyVmomi: `hostLocalAccountManager.RemoveUser()` |
| 129 | `update_esxi_local_user` | ESXi ローカルユーザー更新（パスワード等） | pyVmomi: `hostLocalAccountManager.UpdateUser()` |

## 16. ESXi AD ドメイン参加 — 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 130 | `join_esxi_to_domain` | ESXi を AD ドメインに参加 | pyVmomi: `hostAuthenticationManager.JoinDomain_Task()` |
| 131 | `leave_esxi_domain` | ESXi を AD ドメインから離脱 | pyVmomi: `hostAuthenticationManager.LeaveCurrentDomain_Task()` |

## 17. VirtualDiskManager（仮想ディスクファイル操作）— 5個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 132 | `copy_virtual_disk` | 仮想ディスクファイルコピー（データストア間） | pyVmomi: `VirtualDiskManager.CopyVirtualDisk_Task()` |
| 133 | `move_virtual_disk` | 仮想ディスクファイル移動 | pyVmomi: `VirtualDiskManager.MoveVirtualDisk_Task()` |
| 134 | `delete_virtual_disk` | 仮想ディスクファイル削除 | pyVmomi: `VirtualDiskManager.DeleteVirtualDisk_Task()` |
| 135 | `get_virtual_disk_uuid` | 仮想ディスク UUID 取得 | pyVmomi: `VirtualDiskManager.QueryVirtualDiskUuid()` |
| 136 | `set_virtual_disk_uuid` | 仮想ディスク UUID 設定 | pyVmomi: `VirtualDiskManager.SetVirtualDiskUuid()` |

## 18. VM 構成オプション — 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 137 | `query_vm_config_option` | HW バージョン別有効構成オプション取得 | pyVmomi: `environmentBrowser.QueryConfigOption()` |
| 138 | `query_vm_config_target` | VM 作成時のターゲットリソース情報取得 | pyVmomi: `environmentBrowser.QueryConfigTarget()` |

## 19. VMFS エクステント / DVS エクスポート — 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 139 | `extend_vmfs_datastore` | VMFS にエクステント追加（expand とは別） | pyVmomi: `datastoreSystem.ExtendVmfsDatastore()` |
| 140 | `backup_dvs_config` | DVS 構成バックアップ（エクスポート） | pyVmomi: `DVSManagerExportEntity_Task()` |
| 141 | `restore_dvs_config` | DVS 構成リストア（インポート） | pyVmomi: `DVSManagerImportEntity_Task()` |

## 20. First Class Disks（FCD / IVD）— 10個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 142 | `create_fcd` | First Class Disk 作成 | pyVmomi: `vStorageObjectManager.CreateDisk_Task()` |
| 143 | `delete_fcd` | First Class Disk 削除 | pyVmomi: `vStorageObjectManager.DeleteVStorageObject_Task()` |
| 144 | `list_fcds` | データストア上 FCD 一覧 | pyVmomi: `vStorageObjectManager.ListVStorageObject()` |
| 145 | `get_fcd_info` | FCD メタデータ取得 | pyVmomi: `vStorageObjectManager.RetrieveVStorageObject()` |
| 146 | `clone_fcd` | FCD クローン | pyVmomi: `vStorageObjectManager.CloneVStorageObject_Task()` |
| 147 | `relocate_fcd` | FCD 別データストアへ移動 | pyVmomi: `vStorageObjectManager.RelocateVStorageObject_Task()` |
| 148 | `create_fcd_snapshot` | FCD スナップショット作成 | pyVmomi: `vStorageObjectManager.CreateSnapshot_Task()` |
| 149 | `delete_fcd_snapshot` | FCD スナップショット削除 | pyVmomi: `vStorageObjectManager.DeleteSnapshot_Task()` |
| 150 | `get_fcd_snapshots` | FCD スナップショット情報取得 | pyVmomi: `vStorageObjectManager.RetrieveSnapshotInfo()` |
| 151 | `attach_detach_fcd` | FCD を VM に接続/切断 | pyVmomi: `AttachDisk_Task()` / `DetachDisk_Task()` |

## 21. VM メソッド（追加）— 6個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 152 | `promote_vm_disks` | リンククローンディスクをフルコピーに昇格 | pyVmomi: `vm.PromoteDisks_Task()` |
| 153 | `terminate_vm` | VM 強制終了（電源 OFF とは異なる） | pyVmomi: `vm.TerminateVM()` |
| 154 | `mount_tools_installer` | VMware Tools インストーラ CD マウント | pyVmomi: `vm.MountToolsInstaller()` |
| 155 | `unmount_tools_installer` | VMware Tools インストーラ CD アンマウント | pyVmomi: `vm.UnmountToolsInstaller()` |
| 156 | `query_ft_compatibility` | VM FT 互換性チェック | pyVmomi: `vm.QueryFaultToleranceCompatibility()` |
| 157 | `query_vm_unowned_files` | VM 未所有ファイル検出 | pyVmomi: `vm.QueryUnownedFiles()` |

## 22. ホストマネージャー（追加）— 10個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 158 | `backup_host_firmware` | ESXi ファームウェア/設定バックアップ | pyVmomi: `firmwareSystem.BackupFirmwareConfiguration()` |
| 159 | `restore_host_firmware` | ESXi ファームウェア設定リストア | pyVmomi: `firmwareSystem.RestoreFirmwareConfiguration()` |
| 160 | `get_host_boot_devices` | ESXi ブートデバイス一覧 | pyVmomi: `bootDeviceSystem.QueryBootDevices()` |
| 161 | `set_host_boot_device` | ESXi ブートデバイス設定 | pyVmomi: `bootDeviceSystem.UpdateBootDevice()` |
| 162 | `configure_host_cache` | SSD ホストキャッシュ設定 | pyVmomi: `cacheConfigurationManager.ConfigureHostCache_Task()` |
| 163 | `get_host_cache_config` | ホストキャッシュ構成取得 | pyVmomi: `cacheConfigurationManager` |
| 164 | `list_host_kernel_modules` | ESXi カーネルモジュール一覧 | pyVmomi: `kernelModuleSystem.QueryModules()` |
| 165 | `get_host_vmkernel_nic_services` | VMkernel NIC サービスバインド取得 | pyVmomi: `virtualNicManager.QueryNetConfig()` |
| 166 | `set_host_vmkernel_nic_service` | VMkernel NIC サービス選択/解除 | pyVmomi: `virtualNicManager.SelectVnic()` / `DeselectVnic()` |
| 167 | `get_host_image_config` | ESXi イメージ設定取得 | pyVmomi: `imageConfigManager.FetchSoftwarePackages()` |

## 23. StorageResourceManager（SDRS 追加）— 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 168 | `get_sdrs_placement_recommendations` | SDRS 配置レコメンデーション取得 | pyVmomi: `StorageResourceManager.RecommendDatastores()` |
| 169 | `apply_sdrs_recommendation` | SDRS レコメンデーション適用 | pyVmomi: `ApplyStorageDrsRecommendation_Task()` |

## 24. コンピュートポリシー（vSphere 7+）— 4個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 170 | `list_compute_policies` | コンピュートポリシー一覧 | REST: `GET /api/vcenter/compute-policies` |
| 171 | `create_compute_policy` | コンピュートポリシー作成 | REST: `POST /api/vcenter/compute-policies` |
| 172 | `get_compute_policy` | コンピュートポリシー詳細取得 | REST: `GET /api/vcenter/compute-policies/{id}` |
| 173 | `delete_compute_policy` | コンピュートポリシー削除 | REST: `DELETE /api/vcenter/compute-policies/{id}` |

## 25. アプライアンスヘルス/監視 REST — 12個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 174 | `get_appliance_health_overview` | アプライアンス全サブシステムヘルス | REST: `GET /api/appliance/health` |
| 175 | `get_appliance_health_memory` | アプライアンスメモリヘルス | REST: `GET /api/appliance/health/mem` |
| 176 | `get_appliance_health_cpu` | アプライアンス CPU 負荷ヘルス | REST: `GET /api/appliance/health/load` |
| 177 | `get_appliance_health_storage` | アプライアンスストレージヘルス | REST: `GET /api/appliance/health/storage` |
| 178 | `get_appliance_health_database` | アプライアンス DB ヘルス | REST: `GET /api/appliance/health/database-storage` |
| 179 | `get_appliance_health_swap` | アプライアンススワップヘルス | REST: `GET /api/appliance/health/swap` |
| 180 | `get_appliance_health_softwarepackages` | ソフトウェアパッケージヘルス | REST: `GET /api/appliance/health/software-packages` |
| 181 | `get_appliance_monitoring_data` | アプライアンス監視メトリクス | REST: `GET /api/appliance/monitoring` |
| 182 | `get_appliance_system_time` | アプライアンスシステム時刻 | REST: `GET /api/appliance/system/time` |
| 183 | `get_appliance_timezone` | アプライアンスタイムゾーン取得/設定 | REST: `GET/PUT /api/appliance/system/time/timezone` |
| 184 | `get_appliance_uptime` | アプライアンスアップタイム | REST: `GET /api/appliance/system/uptime` |
| 185 | `shutdown_reboot_appliance` | アプライアンスシャットダウン/リブート | REST: `POST /api/appliance/shutdown` |

## 26. アプライアンスアップデート管理 — 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 186 | `get_appliance_update_pending` | 保留中アップデート一覧 | REST: `GET /api/appliance/update/pending` |
| 187 | `get_appliance_update_staged` | ステージ済みアップデート情報 | REST: `GET /api/appliance/update/staged` |
| 188 | `stage_appliance_update` | アップデートステージング | REST: `POST /api/appliance/update/pending/{ver}?action=stage` |

## 27. アプライアンスネットワーク（追加）— 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 189 | `get_appliance_dns_domains` | DNS 検索ドメイン取得 | REST: `GET /api/appliance/networking/dns/domains` |
| 190 | `get_appliance_dns_hostname` | ホスト名取得 | REST: `GET /api/appliance/networking/dns/hostname` |
| 191 | `get_appliance_firewall_rules` | アプライアンスファイアウォールルール | REST: `GET /api/appliance/networking/firewall/inbound` |

## 28. vCenter REST API（追加エンドポイント）— 11個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 192 | `list_content_registries` | Harbor コンテナレジストリ一覧 | REST: `GET /api/vcenter/content/registries` |
| 193 | `get_datastore_default_policy` | データストアデフォルトポリシー取得 | REST: `GET /api/vcenter/datastore/default-policy` |
| 194 | `mount_iso_to_vm_rest` | ISO マウント（REST） | REST: `POST /api/vcenter/iso/vm/{vm}` |
| 195 | `unmount_iso_from_vm_rest` | ISO アンマウント（REST） | REST: `POST /api/vcenter/iso/vm/{vm}?action=unmount` |
| 196 | `get_hvc_links` | Hybrid Linked Mode リンク一覧 | REST: `GET /api/vcenter/hvc/links` |
| 197 | `list_consumption_domains` | コンサンプションドメイン一覧 | REST: `GET /api/vcenter/consumption-domains` |
| 198 | `get_vcenter_system_config` | vCenter システム設定取得 | REST: `GET /api/vcenter/system-config` |
| 199 | `deploy_vm_from_library_template` | ライブラリテンプレートから VM デプロイ（REST） | REST: `POST /api/vcenter/vm-template/library-items/{id}?action=deploy` |
| 200 | `get_vm_guest_power_state_rest` | VM ゲスト電源状態取得（REST） | REST: `GET /api/vcenter/vm/{vm}/guest/power` |
| 201 | `get_storage_policy_entity_compliance` | エンティティ別ポリシー準拠状態 | REST: `GET /api/vcenter/storage/policies/entities/compliance` |
| 202 | `list_vcenter_networks_rest` | ネットワーク一覧（REST/NSX 含む） | REST: `GET /api/vcenter/network` |

## 29. Trusted Infrastructure（拡張）— 4個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 203 | `list_trusted_kms_providers` | 信頼済み KMS プロバイダー一覧 | REST: `GET /api/vcenter/trusted-infrastructure/kms/services` |
| 204 | `get_trusted_cluster_attestation_report` | クラスタアテステーションレポート | REST |
| 205 | `configure_trust_authority_host` | Trust Authority ホスト設定 | REST |
| 206 | `list_trust_authority_hosts` | Trust Authority ホスト一覧 | REST |

## 30. DVSManager メソッド — 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 207 | `query_compatible_hosts_for_dvs` | DVS 互換ホスト照会 | pyVmomi: `dvsManager.QueryCompatibleHostForNewDvs()` |
| 208 | `query_dvs_feature_capability` | DVS 機能ケーパビリティ照会 | pyVmomi: `dvsManager.QueryDvsFeatureCapability()` |
| 209 | `query_available_dvs_specs` | 利用可能 DVS 仕様照会 | pyVmomi: `dvsManager.QueryAvailableDvsSpec()` |

## 31. EventManager（追加）— 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 210 | `post_custom_event` | カスタムイベント投稿 | pyVmomi: `eventManager.PostEvent()` |
| 211 | `query_events_by_entity` | エンティティ別イベント照会 | pyVmomi: `eventManager.QueryEvents()` |

## 32. CustomizationSpecManager（追加）— 3個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 212 | `duplicate_customization_spec` | カスタマイズ仕様複製 | pyVmomi: `DuplicateCustomizationSpec()` |
| 213 | `rename_customization_spec` | カスタマイズ仕様リネーム | pyVmomi: `RenameCustomizationSpec()` |
| 214 | `export_customization_spec_xml` | カスタマイズ仕様 XML エクスポート/インポート | pyVmomi: `CustomizationSpecItemToXml()` |

## 33. PerfManager（追加）— 2個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 215 | `update_performance_interval` | パフォーマンス収集インターバル更新 | pyVmomi: `perfManager.UpdatePerfInterval()` |
| 216 | `get_composite_performance` | 複合パフォーマンスデータ取得 | pyVmomi: `perfManager.QueryPerfComposite()` |

## 34. SessionManager / AlarmManager / LicenseManager（追加）— 6個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 217 | `acquire_clone_ticket` | セッションクローンチケット取得 | pyVmomi: `sessionManager.AcquireCloneTicket()` |
| 218 | `get_current_session_info` | 現在のセッション詳細取得 | pyVmomi: `sessionManager.CurrentSession` |
| 219 | `get_alarm_state` | エンティティのアラーム状態取得 | pyVmomi: `alarmManager.GetAlarmState()` |
| 220 | `set_alarm_status` | アラームステータス設定（green/yellow/red） | pyVmomi: `alarmManager.SetAlarmStatus()` |
| 221 | `decode_license_key` | ライセンスキーデコード（エディション/機能表示） | pyVmomi: `licenseManager.DecodeLicenseKeyResult()` |
| 222 | `get_license_usage` | ライセンス使用状況/消費データ | pyVmomi: `licenseManager.QueryLicenseUsage()` |

## 35. VM ブートデバイス / Tools（REST）— 4個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 223 | `get_vm_boot_device_order` | VM ブートデバイス順序取得（REST） | REST: `GET /api/vcenter/vm/{vm}/hardware/boot/device` |
| 224 | `set_vm_boot_device_order` | VM ブートデバイス順序設定（REST） | REST: `PUT /api/vcenter/vm/{vm}/hardware/boot/device` |
| 225 | `install_vm_tools` | VMware Tools インストール（REST） | REST: `POST /api/vcenter/vm/{vm}/tools?action=install` |
| 226 | `upgrade_vm_tools_rest` | VMware Tools アップグレード（REST） | REST: `POST /api/vcenter/vm/{vm}/tools?action=upgrade` |

## 36. DatastoreNamespaceManager / VMCompatibilityChecker / その他 — 11個

| # | ツール名 | 説明 | API |
|---|----------|------|-----|
| 227 | `create_datastore_namespace_directory` | VVOL/vSAN トップレベルディレクトリ作成 | pyVmomi: `datastoreNamespaceManager.CreateDirectory()` |
| 228 | `delete_datastore_namespace_directory` | Namespace ディレクトリ削除 | pyVmomi: `datastoreNamespaceManager.DeleteDirectory()` |
| 229 | `check_vm_compatibility` | VM 配置互換性チェック | pyVmomi: `vmCompatibilityChecker.CheckCompatibility_Task()` |
| 230 | `check_power_on_compatibility` | VM 電源 ON 互換性チェック | pyVmomi: `vmCompatibilityChecker.CheckPowerOn_Task()` |
| 231 | `list_tenants` | テナント一覧（vSphere 7.0u2+） | pyVmomi: `tenantManager` |
| 232 | `query_host_connected_luns` | ホスト接続 LUN 照会 | pyVmomi: `storageQueryManager.QueryHostsWithAttachedLun()` |
| 233 | `get_guest_customization_status` | ゲストカスタマイゼーション状態取得 | pyVmomi: `guestCustomizationManager.GetCustomizationStatus()` |
| 234 | `abort_guest_customization` | ゲストカスタマイゼーション中断 | pyVmomi: `guestCustomizationManager.AbortCustomization()` |
| 235 | `get_vcenter_snmp_config` | vCenter SNMP 設定取得 | pyVmomi: `content.snmpSystem.configuration` |
| 236 | `refresh_vm_storage_info` | VM ストレージ情報リフレッシュ | pyVmomi: `vm.RefreshStorageInfo()` |
| 237 | `set_vm_display_topology` | VM ディスプレイ解像度/トポロジ設定 | pyVmomi: `vm.SetDisplayTopology()` |
| 238 | `get_vcenter_service_list` | vCenter サービス一覧（ServiceManager） | pyVmomi: `serviceManager.QueryServiceList()` |
| 239 | `get_cluster_profile_compliance` | クラスタプロファイル準拠チェック | pyVmomi: `clusterProfileManager.CheckCompliance_Task()` |
| 240 | `list_cluster_profiles` | クラスタコンピュートプロファイル一覧 | pyVmomi: `clusterProfileManager.profiles` |
| 241 | `get_vcenter_resource_pools_rest` | リソースプール一覧（REST） | REST: `GET /api/vcenter/resource-pool` |
| 242 | `get_vcenter_authentication_token` | vCenter 認証トークン取得 | REST: `GET /api/vcenter/authentication/token` |
| 243 | `get_guest_customization_specs_rest` | カスタマイズ仕様一覧（REST） | REST: `GET /api/vcenter/guest/customization-specs` |
| 244 | `update_tenant` | テナントリソース割り当て更新 | pyVmomi: `tenantManager.UpdateTenantConfiguration()` |

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
| SearchIndex | 4 |
| ESXi ローカルアカウント | 3 |
| ESXi AD ドメイン | 2 |
| VirtualDiskManager | 5 |
| VM 構成オプション | 2 |
| VMFS / DVS | 3 |
| First Class Disks (FCD) | 10 |
| VM メソッド（追加） | 6 |
| ホストマネージャー（追加） | 10 |
| SDRS（追加） | 2 |
| コンピュートポリシー | 4 |
| アプライアンスヘルス/監視 | 12 |
| アプライアンスアップデート | 3 |
| アプライアンスネットワーク（追加） | 3 |
| vCenter REST（追加） | 11 |
| Trusted Infrastructure（拡張） | 4 |
| DVSManager | 3 |
| EventManager（追加） | 2 |
| CustomizationSpecManager（追加） | 3 |
| PerfManager（追加） | 2 |
| Session/Alarm/License（追加） | 6 |
| VM Boot/Tools REST | 4 |
| Namespace/Compat/その他 | 18 |
| **合計** | **244** |

実装完了後の総ツール数: **413 + 244 = 657**
