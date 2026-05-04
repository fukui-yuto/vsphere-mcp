# 変更履歴

このプロジェクトに対するすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/) に基づいており、
[セマンティックバージョニング](https://semver.org/lang/ja/) に準拠しています。

## [0.5.0] - 2026-05-04

657 ツールへの拡張。issues.md の全 244 項目（残存 vSphere API ギャップ）を実装。

### 追加

#### 新規モジュール（24 モジュール、244 ツール）

| モジュール | ツール数 | 概要 |
|-----------|---------|------|
| `vm_devices_ext.py` | 12 | シリアル/パラレル/USB/フロッピー/NVMe コントローラ管理 |
| `vm_ops_ext.py` | 11 | vMotion 互換性/ディスク操作/スケジュール電源操作 |
| `host_ops_ext.py` | 18 | SNMP/コアダンプ/自動起動/TPM/FC HBA/グラフィックス |
| `cluster_ops_ext.py` | 12 | DRS/HA VM オーバーライド/VCHA/SDRS/リソースサマリ |
| `network_ext.py` | 13 | NetFlow/ポートミラー/IP Pool/NIC 詳細設定 |
| `storage_ops_ext.py` | 8 | VAAI/UNMAP/VASA プロバイダー/SIOC/NFS Kerberos |
| `security.py` | 10 | SSO/パスワードポリシー/ログインバナー/Trust Authority |
| `diagnostics.py` | 11 | サポートバンドル/CEIP/syslog/拡張機能管理 |
| `vapp_ext.py` | 6 | vApp 作成/クローン/起動順序/OVF プロパティ |
| `guest_ext.py` | 8 | ゲストファイル読み書き/レジストリ/エイリアス |
| `sdrs.py` | 6 | SDRS レコメンデーション/コンピュートポリシー |
| `appliance_health.py` | 12 | アプライアンス CPU/メモリ/DB/スワップヘルス |
| `appliance_update.py` | 6 | アップデート管理/DNS/ファイアウォール |
| `search_index.py` | 17 | SearchIndex/アラーム/NTP/アプライアンスアクセス |
| `esxi_accounts.py` | 5 | ESXi ローカルアカウント/AD ドメイン参加 |
| `virtual_disk_mgr.py` | 10 | VirtualDiskManager/VM 構成オプション/DVS バックアップ |
| `fcd.py` | 10 | First Class Disk CRUD/スナップショット/アタッチ |
| `vm_methods_ext.py` | 6 | ディスク昇格/強制終了/Tools マウント/FT 互換 |
| `host_mgr_ext.py` | 10 | ファームウェア/ブートデバイス/キャッシュ/カーネルモジュール |
| `vcenter_rest_ext.py` | 11 | ISO マウント/テンプレートデプロイ/HVC リンク |
| `trusted_infra.py` | 7 | Trusted Infrastructure/DVSManager |
| `event_ext.py` | 13 | カスタムイベント/カスタマイズ仕様/パフォーマンス/セッション |
| `vm_boot_rest.py` | 4 | VM ブートデバイス順序/VMware Tools REST |
| `namespace_compat.py` | 18 | Namespace ディレクトリ/互換性チェック/テナント |

### 変更

- ツール総数: 413 → 657（+244）
- ツールモジュール数: 47 → 71（+24）

---

## [0.3.0] - 2026-05-04

301 ツールへの拡張。issues.md の全 Gap Analysis 項目を実装。

### 追加

#### 新規モジュール

| モジュール | ツール数 | 概要 |
|-----------|---------|------|
| `datacenter.py` | 3 | データセンター作成・削除・リネーム |
| `customization.py` | 6 | Linux/Windows カスタマイズ仕様の管理・VM 適用 |
| `alarm.py` | 4 | アラーム定義の作成・削除・制御 |
| `vsphere_tags.py` | 9 | vSphere タグカテゴリ・タグの管理とオブジェクトへの付与 |
| `content_library.py` | 7 | コンテンツライブラリの管理・VM デプロイ |
| `vapp.py` | 4 | vApp の一覧・電源操作・削除 |
| `scheduled_tasks.py` | 3 | スケジュールタスクの一覧・削除・即時実行 |
| `host_profile.py` | 2 | ホストプロファイル一覧・コンプライアンス確認 |
| `license.py` | 4 | ライセンスキーの追加・削除・割り当て管理 |
| `fault_tolerance.py` | 3 | VM フォールトトレランスの有効化・無効化・情報取得 |

#### 既存モジュール拡張

| モジュール | 追加数 | 追加ツール |
|-----------|--------|-----------|
| `guest.py` | +6 | `upload_file_to_guest`, `download_file_from_guest`, `move_guest_file`, `delete_guest_directory`, `get_guest_network_info`, `get_guest_os_info` |
| `lifecycle.py` | +5 | `linked_clone_vm`, `enable_vm_cbt`, `query_vm_changed_disk_areas`, `answer_vm_question`, `get_vm_pending_question` |
| `cluster_config.py` | +8 | `create_vm_host_affinity_rule`, `delete_drs_group`, `update_drs_group`, `set_evc_mode`, `get_evc_mode`, `move_vm_to_resource_pool`, `configure_dpm`, `configure_ha_admission_control` |
| `performance.py` | +5 | `get_datastore_performance`, `get_historical_performance`, `get_custom_metrics`, `list_performance_intervals`, `list_available_metrics` |
| `networking.py` | +5 | `add_host_to_dvswitch`, `remove_host_from_dvswitch`, `list_dvswitch_ports`, `configure_dvs_pvlan`, `configure_host_vswitch_nic_teaming` |
| `storage.py` | +8 | `create_vmfs_datastore`, `expand_vmfs_datastore`, `enable_iscsi_adapter`, `add_iscsi_target`, `create_datastore_cluster`, `configure_storage_drs`, `list_datastore_clusters`, `configure_sioc` |
| `vm_devices.py` | +3 | `add_vtpm`, `set_vm_secure_boot`, `configure_vm_vbs` |
| `resources.py` | +4 | `set_vm_cpu_allocation`, `set_vm_memory_allocation`, `set_vm_memory_hotadd`, `set_vm_latency_sensitivity` |
| `batch.py` | +2 | `batch_reconfigure_vms`, `batch_migrate_vms` |
| `tags.py` | +1 | `delete_custom_attribute` |
| `snapshot.py` | +1 | `consolidate_vm_disks` |
| `host.py` | +2 | `add_standalone_host`, `rename_host` |
| `inventory.py` | +2 | `get_vm_screenshot`, `wait_for_vm_guest_ip` |

### 変更

- ツール総数: 204 → 301（+97）

---

## [0.2.0] - 2026-05-04

大幅な機能拡充。204 ツールへの拡張、インフラ改善、ドキュメント整備。

### 全ツール一覧（204個）

| # | カテゴリ | ツール名 | 説明 | リスク |
|---|---------|----------|------|--------|
| 1 | 接続 | `test_connection` | vCenter 接続テストと基本情報取得 | - |
| 2 | VM 一覧 | `list_vms` | 全 VM 一覧（ホスト/クラスタフィルタ） | - |
| 3 | VM 情報 | `get_vm_info` | VM 詳細情報（CPU/メモリ/ディスク/NIC） | - |
| 4 | VM 検索 | `search_vms` | VM 名検索（大文字小文字区別なし） | - |
| 5 | ホスト一覧 | `list_hosts` | 全 ESXi ホスト一覧 | - |
| 6 | ホスト情報 | `get_host_info` | ESXi ホスト詳細情報 | - |
| 7 | DC 一覧 | `list_datacenters` | 全データセンター一覧 | - |
| 8 | クラスタ一覧 | `list_clusters` | 全クラスタ一覧 | - |
| 9 | DS 一覧 | `list_datastores` | 全データストア一覧（容量付き） | - |
| 10 | ネットワーク | `list_networks` | 全ネットワーク一覧 | - |
| 11 | スナップショット | `list_snapshots` | VM スナップショットツリー表示 | - |
| 12 | クラスタ健全性 | `get_cluster_health` | クラスタヘルスサマリ | - |
| 13 | リソースプール | `list_resource_pools` | リソースプール一覧 | - |
| 14 | 分散スイッチ | `list_distributed_switches` | 分散仮想スイッチ一覧 | - |
| 15 | 分散PG | `list_distributed_portgroups` | 分散ポートグループ一覧 | - |
| 16 | DC 情報 | `get_datacenter_info` | データセンター詳細情報（フォルダ名含む） | - |
| 17 | 電源 | `power_on_vm` | VM 電源オン | 低 |
| 18 | 電源 | `power_off_vm` | VM 強制電源オフ | 中 |
| 19 | 電源 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 20 | 電源 | `reboot_vm` | ゲスト OS リブート | 中 |
| 21 | スナップショット | `create_snapshot` | スナップショット作成 | 中 |
| 22 | スナップショット | `revert_snapshot` | スナップショット復元 | 高 |
| 23 | スナップショット | `remove_snapshot` | スナップショット削除 | 高 |
| 24 | マイグレーション | `migrate_vm` | vMotion 移行 | 高 |
| 25 | ライフサイクル | `clone_vm` | VM クローン作成 | 高 |
| 26 | ライフサイクル | `deploy_from_template` | テンプレートデプロイ | 高 |
| 27 | ライフサイクル | `delete_vm` | VM 完全削除 | 重大 |
| 28 | ライフサイクル | `register_vm` | VMX ファイルから VM 登録 | 中 |
| 29 | ライフサイクル | `convert_vm_to_template` | VM をテンプレートに変換 | 高 |
| 30 | ライフサイクル | `convert_template_to_vm` | テンプレートを VM に変換 | 高 |
| 31 | ライフサイクル | `create_vm` | 空の VM を新規作成 | 高 |
| 32 | ライフサイクル | `list_guest_os_types` | サポートされるゲスト OS タイプ一覧 | - |
| 33 | リソース | `set_vm_resources` | VM CPU/メモリ変更 | 中 |
| 34 | リソース | `add_disk` | VM ディスク追加 | 中 |
| 35 | リソース | `add_nic` | VM NIC 追加 | 中 |
| 36 | VM デバイス | `remove_disk` | VM ディスク削除 | 高 |
| 37 | VM デバイス | `expand_disk` | VM ディスク拡張 | 中 |
| 38 | VM デバイス | `remove_nic` | VM NIC 削除 | 高 |
| 39 | VM デバイス | `list_vm_controllers` | VM コントローラ一覧 | - |
| 40 | VM デバイス | `get_vm_extra_config` | VM extraConfig 取得 | - |
| 41 | VM デバイス | `set_vm_extra_config` | VM extraConfig 設定 | 中 |
| 42 | VM デバイス | `rename_vm` | VM リネーム | 中 |
| 43 | VM デバイス | `unregister_vm` | VM 登録解除（ファイル保持） | 高 |
| 44 | VM デバイス | `get_vm_console_url` | WebMKS コンソールチケット取得 | - |
| 45 | VM デバイス | `set_vm_boot_options` | VM ブートオプション設定 | 中 |
| 46 | VM デバイス | `list_vm_cddvd_drives` | CD/DVD ドライブ一覧（ISO マウント状態） | - |
| 47 | VM デバイス | `mount_vm_cdrom_iso` | CD/DVD に ISO マウント | 中 |
| 48 | VM デバイス | `disconnect_vm_cdrom` | CD/DVD ドライブ切断 | 低 |
| 49 | VM デバイス | `get_vm_video_card` | ビデオカード設定取得 | - |
| 50 | VM デバイス | `list_vm_disk_layout` | ディスクレイアウト詳細 | - |
| 51 | VM デバイス | `list_vm_snapshots_disk_usage` | スナップショットディスク使用量 | - |
| 52 | ホスト管理 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 53 | ホスト管理 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |
| 54 | ホスト管理 | `shutdown_host` | ESXi ホストシャットダウン | 重大 |
| 55 | ホスト管理 | `reboot_host` | ESXi ホストリブート | 重大 |
| 56 | ホスト管理 | `disconnect_host` | ESXi ホスト切断 | 重大 |
| 57 | ホスト管理 | `reconnect_host` | ESXi ホスト再接続 | 高 |
| 58 | ホスト設定 | `get_host_vswitches` | ESXi 標準 vSwitch 一覧 | - |
| 59 | ホスト設定 | `get_host_vmkernel_adapters` | VMkernel アダプタ一覧 | - |
| 60 | ホスト設定 | `get_host_portgroups` | 標準スイッチポートグループ一覧 | - |
| 61 | ホスト設定 | `get_host_physical_nics` | 物理 NIC 一覧 | - |
| 62 | ホスト設定 | `list_host_services` | ESXi サービス一覧 | - |
| 63 | ホスト設定 | `start_stop_host_service` | ESXi サービス起動/停止 | 高 |
| 64 | ホスト設定 | `list_host_firewall_rules` | ESXi ファイアウォールルール一覧 | - |
| 65 | ホスト設定 | `get_host_dns_config` | ESXi DNS 設定取得 | - |
| 66 | ホスト設定 | `get_host_ntp_config` | ESXi NTP 設定取得 | - |
| 67 | ホスト設定 | `get_host_routing_config` | ESXi ルーティング設定取得 | - |
| 68 | ホスト設定 | `get_host_hardware_health` | ESXi ハードウェアヘルス情報 | - |
| 69 | ホスト設定 | `enable_esxi_ssh` | ESXi SSH 有効化 | 高 |
| 70 | ホスト設定 | `disable_esxi_ssh` | ESXi SSH 無効化 | 高 |
| 71 | ホスト設定 | `get_host_syslog_config` | ESXi syslog 設定取得 | - |
| 72 | ホスト設定 | `get_host_power_policy` | ESXi 電源管理ポリシー取得 | - |
| 73 | ホスト設定 | `set_host_power_policy` | ESXi 電源管理ポリシー設定 | 中 |
| 74 | ホスト設定 | `get_host_lockdown_mode` | ESXi ロックダウンモード取得 | - |
| 75 | ホスト設定 | `get_host_certificate_info` | ESXi SSL 証明書情報取得 | - |
| 76 | ホスト設定 | `get_host_time_config` | ESXi ホスト現在時刻取得 | - |
| 77 | ネットワーク | `get_dvswitch_config` | 分散仮想スイッチ詳細設定取得 | - |
| 78 | ネットワーク | `get_dvportgroup_config` | 分散ポートグループ詳細設定取得 | - |
| 79 | ネットワーク | `create_dvswitch` | 分散仮想スイッチ作成 | 高 |
| 80 | ネットワーク | `create_dvportgroup` | 分散ポートグループ作成 | 高 |
| 81 | ネットワーク | `add_host_portgroup` | 標準ポートグループ追加 | 高 |
| 82 | ネットワーク | `remove_host_portgroup` | 標準ポートグループ削除 | 高 |
| 83 | パフォーマンス | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 84 | パフォーマンス | `get_host_performance` | ホストパフォーマンスメトリクス | - |
| 85 | イベント | `list_recent_events` | vCenter イベント一覧 | - |
| 86 | イベント | `list_alarms` | トリガー済みアラーム一覧 | - |
| 87 | イベント | `list_performance_counters` | パフォーマンスカウンタ一覧 | - |
| 88 | イベント | `get_alarm_definitions` | アラーム定義一覧 | - |
| 89 | イベント | `get_host_system_log` | ESXi ホスト診断ログ取得 | - |
| 90 | イベント | `list_diagnostic_log_keys` | 診断ログキー一覧 | - |
| 91 | ストレージ | `get_datastore_info` | データストア詳細情報 | - |
| 92 | ストレージ | `get_storage_summary` | ストレージ全体サマリー | - |
| 93 | ストレージ | `list_host_storage_devices` | ホスト SCSI LUN/HBA 一覧 | - |
| 94 | ストレージ | `list_host_multipath_info` | ホストマルチパス情報一覧 | - |
| 95 | ストレージ | `rescan_host_storage` | ホストストレージ再スキャン | 中 |
| 96 | バッチ | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 97 | バッチ | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |
| 98 | バッチ | `batch_get_vm_info` | 複数 VM 一括情報取得 | - |
| 99 | ゲスト | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 100 | ゲスト | `list_guest_processes` | ゲスト OS プロセス一覧 | - |
| 101 | タグ | `get_vm_annotation` | VM アノテーション取得 | - |
| 102 | タグ | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 103 | タグ | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 104 | タグ | `create_custom_attribute` | カスタム属性定義作成 | 中 |
| 105 | タグ | `set_custom_attribute_value` | カスタム属性値設定 | 低 |
| 106 | タグ | `get_entity_custom_attribute_values` | エンティティのカスタム属性値取得 | - |
| 107 | 詳細設定 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 108 | 詳細設定 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 109 | 詳細設定 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 110 | 詳細設定 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |
| 111 | vCenter 管理 | `list_roles` | vCenter ロール一覧 | - |
| 112 | vCenter 管理 | `get_entity_permissions` | エンティティ権限取得 | - |
| 113 | vCenter 管理 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 114 | vCenter 管理 | `list_active_sessions` | アクティブセッション一覧 | - |
| 115 | vCenter 管理 | `list_recent_tasks` | 最近のタスク一覧 | - |
| 116 | vCenter 管理 | `terminate_session` | セッション強制終了 | 高 |
| 117 | クラスタ設定 | `get_cluster_ha_config` | HA 設定取得 | - |
| 118 | クラスタ設定 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 119 | クラスタ設定 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 120 | クラスタ設定 | `get_cluster_drs_recommendations` | DRS レコメンデーション取得 | - |
| 121 | クラスタ設定 | `create_resource_pool` | リソースプール作成 | 高 |
| 122 | クラスタ設定 | `update_resource_pool` | リソースプール更新 | 高 |
| 123 | クラスタ設定 | `delete_resource_pool` | リソースプール削除 | 高 |
| 124 | クラスタ設定 | `list_cluster_host_vm_groups` | DRS ホスト/VM グループ一覧 | - |
| 125 | ���ォルダ | `list_folders` | フォルダ一覧（パス付き） | - |
| 126 | フォルダ | `create_folder` | フォルダ作成 | 中 |
| 127 | フォルダ | `move_vm_to_folder` | VM をフォルダに移動 | 中 |
| 128 | DS ブラウザ | `browse_datastore` | データストアファイル参照 | - |
| 129 | DS ブラウザ | `delete_datastore_file` | データストアファイル削除 | 重大 |
| 130 | 電源 | `suspend_vm` | VM サスペンド | 中 |
| 131 | 電源 | `reset_vm` | VM ハードリセット | 高 |
| 132 | スナップショット | `remove_all_snapshots` | 全スナップショット削除 | 高 |
| 133 | スナップショット | `rename_snapshot` | スナップショットリネーム | 中 |
| 134 | スナップショット | `revert_to_current_snapshot` | 現在のスナップショットに復元 | 高 |
| 135 | マイグレーション | `storage_vmotion` | Storage vMotion（ディスク移行） | 高 |
| 136 | マイグレーション | `relocate_vm` | VM 再配置（コンピュート+ストレージ） | 高 |
| 137 | リソース | `add_vm_cd_drive` | VM CD/DVD ドライブ追加 | 中 |
| 138 | VM デバイス | `change_vm_nic_network` | VM NIC ネットワーク変更 | 中 |
| 139 | VM デバイス | `connect_disconnect_vm_nic` | VM NIC 接続/切断 | 中 |
| 140 | VM デバイス | `add_vm_scsi_controller` | SCSI コントローラ追加 | 中 |
| 141 | VM デバイス | `upgrade_vm_hardware` | VM ハードウェアアップグレード | 高 |
| 142 | VM デバイス | `set_vm_cpu_hotadd` | CPU ホットアド有効/無効 | 中 |
| 143 | VM デバイス | `set_vm_cores_per_socket` | ソケットあたりコア数設定 | 中 |
| 144 | VM デバイス | `change_vm_disk_mode` | VM ディスクモード変更 | 高 |
| 145 | ホスト管理 | `add_host_to_cluster` | クラスタにホスト追加 | 高 |
| 146 | ホスト管理 | `remove_host` | ホスト削除 | 重大 |
| 147 | ホスト管理 | `move_host_to_cluster` | ホストを別クラスタに移動 | 高 |
| 148 | ホスト設定 | `create_vswitch` | 標準 vSwitch 作成 | 高 |
| 149 | ホスト設定 | `remove_vswitch` | 標準 vSwitch 削除 | 高 |
| 150 | ホスト設定 | `update_vswitch` | 標準 vSwitch 更新 | 高 |
| 151 | ホスト設定 | `add_vmkernel_adapter` | VMkernel アダプタ追加 | 高 |
| 152 | ホスト設定 | `remove_vmkernel_adapter` | VMkernel アダプタ削除 | 高 |
| 153 | ホスト設定 | `set_host_dns_config` | ESXi DNS 設定変更 | 高 |
| 154 | ホスト設定 | `set_host_ntp_servers` | ESXi NTP サーバー設定 | 高 |
| 155 | ホスト設定 | `set_host_syslog_target` | ESXi syslog 送信先設定 | 高 |
| 156 | ホスト設定 | `set_host_lockdown_mode` | ESXi ロックダウンモード設定 | 重大 |
| 157 | ホスト設定 | `enable_host_firewall_ruleset` | ファイアウォールルールセット有効化 | 高 |
| 158 | ホスト設定 | `disable_host_firewall_ruleset` | ファイアウォールルールセット無効化 | 高 |
| 159 | ホスト設定 | `set_host_service_policy` | ESXi サービスポリシー設定 | 高 |
| 160 | ホスト設定 | `sync_host_time` | ESXi ホスト時刻同期 | 中 |
| 161 | ホスト設定 | `refresh_host_ca_certificates` | ESXi SSL 証明書更新 | 高 |
| 162 | ネットワーク | `delete_dvswitch` | 分散仮想スイッチ削除 | 重大 |
| 163 | ネットワーク | `delete_dvportgroup` | 分散ポートグループ削除 | 重大 |
| 164 | ネットワーク | `update_dvportgroup` | 分散ポートグループ設定更新 | 高 |
| 165 | ネットワーク | `update_dvswitch` | 分散仮想スイッチ設定更新 | 高 |
| 166 | イベント | `get_vcenter_log` | vCenter ログ取得 | - |
| 167 | イベント | `list_vcenter_log_keys` | vCenter ログキー一覧 | - |
| 168 | ストレージ | `mount_nfs_datastore` | NFS データストアマウント | 高 |
| 169 | ストレージ | `unmount_datastore` | データストアアンマウント | 重大 |
| 170 | ストレージ | `rename_datastore` | データストアリネーム | 中 |
| 171 | ストレージ | `refresh_datastore` | データストアリフレッシュ | - |
| 172 | ストレージ | `enter_datastore_maintenance_mode` | データストアメンテナンスモード開始 | 高 |
| 173 | ストレージ | `exit_datastore_maintenance_mode` | データストアメンテナンスモード解除 | 高 |
| 174 | ストレージ | `set_multipath_policy` | マルチパスポリシー設定 | 高 |
| 175 | ストレージ | `list_datastore_hosts` | データストア接続ホスト一覧 | - |
| 176 | ゲスト | `list_guest_files` | ゲスト OS ファイル一覧 | - |
| 177 | ゲスト | `create_guest_directory` | ゲスト OS ディレクトリ作成 | 中 |
| 178 | ゲスト | `delete_guest_file` | ゲスト OS ファイル削除 | 高 |
| 179 | ゲスト | `terminate_guest_process` | ゲスト OS プロセス終了 | 高 |
| 180 | ゲスト | `upgrade_vmware_tools` | VMware Tools アップグレード | 中 |
| 181 | ゲスト | `read_guest_environment_variables` | ゲスト OS 環境変数取得 | - |
| 182 | vCenter 管理 | `create_role` | ロール作成 | 高 |
| 183 | vCenter 管理 | `update_role` | ロール更新 | 高 |
| 184 | vCenter 管理 | `delete_role` | ロール削除 | 高 |
| 185 | vCenter 管理 | `set_entity_permissions` | エンティティ権限設定 | 高 |
| 186 | vCenter 管理 | `remove_entity_permission` | エンティティ権限削除 | 高 |
| 187 | vCenter 管理 | `cancel_task` | タスクキャンセル | 中 |
| 188 | vCenter 管理 | `list_privileges` | 権限一覧 | - |
| 189 | vCenter 管理 | `acknowledge_alarm` | アラーム確認応答 | 低 |
| 190 | クラスタ設定 | `configure_cluster_ha` | クラスタ HA 設定変更 | 高 |
| 191 | クラスタ設定 | `configure_cluster_drs` | クラスタ DRS 設定変更 | 高 |
| 192 | クラスタ設定 | `create_drs_rule` | DRS アフィニティルール作成 | 高 |
| 193 | クラスタ設定 | `delete_drs_rule` | DRS アフィニティルール削除 | 高 |
| 194 | クラスタ設定 | `apply_drs_recommendation` | DRS レコメンデーション適用 | 高 |
| 195 | クラスタ設定 | `create_cluster` | クラスタ作成 | 高 |
| 196 | クラスタ設定 | `delete_cluster` | クラスタ削除 | 重大 |
| 197 | クラスタ設定 | `create_drs_vm_group` | DRS VM グループ作成 | 高 |
| 198 | クラスタ設定 | `create_drs_host_group` | DRS ホストグループ作成 | 高 |
| 199 | フォルダ | `delete_folder` | フォルダ削除 | 高 |
| 200 | フォルダ | `rename_folder` | フォルダリネーム | 中 |
| 201 | フォルダ | `move_entity_to_folder` | エンティティをフォルダに移動 | 高 |
| 202 | DS ブラウザ | `copy_datastore_file` | データストアファイルコピー | 高 |
| 203 | DS ブラウザ | `move_datastore_file` | データストアファイル移動 | 高 |
| 204 | DS ブラウザ | `create_datastore_directory` | データストアディレクトリ作成 | 中 |

### リスクレベル別サマリー

| リスクレベル | 件数 | 説明 |
|-------------|------|------|
| - (読み取り専用) | 79 | 確認不要。情報取得のみ |
| 低 | 5 | 軽微な変更。確認必須 |
| 中 | 33 | 元に戻せる操作。確認必須 |
| 高 | 76 | 重大な影響の可能性。確認必須 |
| 重大 | 11 | 不可逆操作。確認必須 |

## [0.1.0] - 2025-05-04

初回リリース。vSphere 管理用 MCP サーバーの基盤と 28 個のツールを実装。

### 追加

#### 情報取得ツール（読み取り専用・確認不要）- 12個

| # | ツール名 | 説明 |
|---|----------|------|
| 1 | `test_connection` | vCenter 接続テストと基本情報取得 |
| 2 | `list_vms` | 全 VM 一覧（ホスト/クラスタフィルタ対応） |
| 3 | `get_vm_info` | VM 詳細情報取得 |
| 4 | `list_hosts` | 全 ESXi ホスト一覧 |
| 5 | `get_host_info` | ESXi ホスト詳細情報取得 |
| 6 | `list_datacenters` | 全データセンター一覧 |
| 7 | `list_clusters` | 全クラスタ一覧 |
| 8 | `list_datastores` | 全データストア一覧（容量付き） |
| 9 | `list_networks` | 全ネットワーク一覧 |
| 10 | `list_snapshots` | VM スナップショットツリー表示 |
| 11 | `get_cluster_health` | クラスタヘルスサマリ |
| 12 | `search_vms` | VM 名検索 |

#### 操作ツール（確認必須）- 16個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 1 | `power_on_vm` | VM 電源オン | 低 |
| 2 | `power_off_vm` | VM 強制電源オフ | 中 |
| 3 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 4 | `reboot_vm` | ゲスト OS リブート | 中 |
| 5 | `create_snapshot` | スナップショット作成 | 中 |
| 6 | `revert_snapshot` | スナップショット復元 | 高 |
| 7 | `remove_snapshot` | スナップショット削除 | 高 |
| 8 | `migrate_vm` | vMotion 移行 | 高 |
| 9 | `clone_vm` | VM クローン | 高 |
| 10 | `deploy_from_template` | テンプレートデプロイ | 高 |
| 11 | `set_vm_resources` | VM リソース変更 | 中 |
| 12 | `add_disk` | VM ディスク追加 | 中 |
| 13 | `add_nic` | VM NIC 追加 | 中 |
| 14 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 15 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |
| 16 | `delete_vm` | VM 完全削除 | 重大 |

#### インフラストラクチャ

- FastMCP による MCP サーバー（stdio トランスポート）
- 遅延初期化・自動再接続対応の vSphere 接続クライアント
- PropertyCollector による効率的なプロパティ取得
- `require_confirm` デコレータによる破壊的操作の安全装置
- `handle_tool_errors` デコレータによる統一的なエラーハンドリング
- `VSPHERE_PASSWORD_FILE` によるファイルベースのシークレット管理
- ログマスク機能（認証情報のログ出力を自動抑制）
- 環境変数による設定管理（pydantic-settings）
- 構造化 JSON ログ（structlog）
- vcsim Docker Compose によるローカル開発環境
- GitHub Actions CI（vcsim 使用）
- 50 件の自動テスト
