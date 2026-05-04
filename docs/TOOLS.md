# ツール一覧（全204個）

vsphere-mcp が提供する全ツールの一覧です。

## リスクレベル

| レベル | 説明 |
|--------|------|
| - | 読み取り専用。確認不要 |
| 低 | 軽微な変更。確認必須 |
| 中 | 元に戻せる操作。確認必須 |
| 高 | 重大な影響の可能性。確認必須 |
| 重大 | 不可逆操作。確認必須 |

---

## インベントリ（inventory.py）- 16個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 1 | `test_connection` | vCenter 接続テストと基本情報取得 | - |
| 2 | `list_vms` | 全 VM 一覧（ホスト/クラスタフィルタ） | - |
| 3 | `get_vm_info` | VM 詳細情報（CPU/メモリ/ディスク/NIC） | - |
| 4 | `search_vms` | VM 名検索（大文字小文字区別なし） | - |
| 5 | `list_hosts` | 全 ESXi ホスト一覧 | - |
| 6 | `get_host_info` | ESXi ホスト詳細情報 | - |
| 7 | `list_datacenters` | 全データセンター一覧 | - |
| 8 | `list_clusters` | 全クラスタ一覧 | - |
| 9 | `list_datastores` | 全データストア一覧（容量付き） | - |
| 10 | `list_networks` | 全ネットワーク一覧 | - |
| 11 | `list_snapshots` | VM スナップショットツリー表示 | - |
| 12 | `get_cluster_health` | クラスタヘルスサマリ | - |
| 13 | `list_resource_pools` | リソースプール一覧 | - |
| 14 | `list_distributed_switches` | 分散仮想スイッチ一覧 | - |
| 15 | `list_distributed_portgroups` | 分散ポートグループ一覧 | - |
| 16 | `get_datacenter_info` | データセンター詳細情報（フォルダ名含む） | - |

## 電源操作（power.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 17 | `power_on_vm` | VM 電源オン | 低 |
| 18 | `power_off_vm` | VM 強制電源オフ | 中 |
| 19 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 20 | `reboot_vm` | ゲスト OS リブート | 中 |
| 21 | `suspend_vm` | VM サスペンド | 中 |
| 22 | `reset_vm` | VM ハードリセット | 高 |

## スナップショット（snapshot.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 23 | `create_snapshot` | スナップショット作成 | 中 |
| 24 | `revert_snapshot` | スナップショット復元 | 高 |
| 25 | `remove_snapshot` | スナップショット削除 | 高 |
| 26 | `remove_all_snapshots` | 全スナップショット削除 | 高 |
| 27 | `rename_snapshot` | スナップショットリネーム | 中 |
| 28 | `revert_to_current_snapshot` | 現在のスナップショットに復元 | 高 |

## マイグレーション（migration.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 29 | `migrate_vm` | vMotion 移行 | 高 |
| 30 | `storage_vmotion` | Storage vMotion（ディスク移行） | 高 |
| 31 | `relocate_vm` | VM 再配置（コンピュート+ストレージ） | 高 |

## ライフサイクル（lifecycle.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 32 | `clone_vm` | VM クローン作成 | 高 |
| 33 | `deploy_from_template` | テンプレートデプロイ | 高 |
| 34 | `delete_vm` | VM 完全削除 | 重大 |
| 35 | `register_vm` | VMX ファイルから VM 登録 | 中 |
| 36 | `convert_vm_to_template` | VM をテンプレートに変換 | 高 |
| 37 | `convert_template_to_vm` | テンプレートを VM に変換 | 高 |
| 38 | `create_vm` | 空の VM を新規作成 | 高 |
| 39 | `list_guest_os_types` | サポートされるゲスト OS タイプ一覧 | - |

## リソース（resources.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 40 | `set_vm_resources` | VM CPU/メモリ変更 | 中 |
| 41 | `add_disk` | VM ディスク追加 | 中 |
| 42 | `add_nic` | VM NIC 追加 | 中 |
| 43 | `add_vm_cd_drive` | VM CD/DVD ドライブ追加 | 中 |

## VM デバイス（vm_devices.py）- 23個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 44 | `remove_disk` | VM ディスク削除 | 高 |
| 45 | `expand_disk` | VM ディスク拡張 | 中 |
| 46 | `remove_nic` | VM NIC 削除 | 高 |
| 47 | `list_vm_controllers` | VM コントローラ一覧 | - |
| 48 | `get_vm_extra_config` | VM extraConfig 取得 | - |
| 49 | `set_vm_extra_config` | VM extraConfig 設定 | 中 |
| 50 | `rename_vm` | VM リネーム | 中 |
| 51 | `unregister_vm` | VM 登録解除（ファイル保持） | 高 |
| 52 | `get_vm_console_url` | WebMKS コンソールチケット取得 | - |
| 53 | `set_vm_boot_options` | VM ブートオプション設定 | 中 |
| 54 | `list_vm_cddvd_drives` | CD/DVD ドライブ一覧（ISO マウント状態） | - |
| 55 | `mount_vm_cdrom_iso` | CD/DVD に ISO マウント | 中 |
| 56 | `disconnect_vm_cdrom` | CD/DVD ドライブ切断 | 低 |
| 57 | `get_vm_video_card` | ビデオカード設定取得 | - |
| 58 | `list_vm_disk_layout` | ディスクレイアウト詳細 | - |
| 59 | `list_vm_snapshots_disk_usage` | スナップショットディスク使用量 | - |
| 60 | `change_vm_nic_network` | VM NIC ネットワーク変更 | 中 |
| 61 | `connect_disconnect_vm_nic` | VM NIC 接続/切断 | 中 |
| 62 | `add_vm_scsi_controller` | SCSI コントローラ追加 | 中 |
| 63 | `upgrade_vm_hardware` | VM ハードウェアバージョンアップグレード | 高 |
| 64 | `set_vm_cpu_hotadd` | CPU ホットアド有効/無効 | 中 |
| 65 | `set_vm_cores_per_socket` | ソケットあたりコア数設定 | 中 |
| 66 | `change_vm_disk_mode` | VM ディスクモード変更 | 高 |

## ホスト管理（host.py）- 9個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 67 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 68 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |
| 69 | `shutdown_host` | ESXi ホストシャットダウン | 重大 |
| 70 | `reboot_host` | ESXi ホストリブート | 重大 |
| 71 | `disconnect_host` | ESXi ホスト切断 | 重大 |
| 72 | `reconnect_host` | ESXi ホスト再接続 | 高 |
| 73 | `add_host_to_cluster` | クラスタにホスト追加 | 高 |
| 74 | `remove_host` | ホスト削除（インベントリから） | 重大 |
| 75 | `move_host_to_cluster` | ホストを別クラスタに移動 | 高 |

## ホスト設定（host_config.py）- 33個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 76 | `get_host_vswitches` | ESXi 標準 vSwitch 一覧 | - |
| 77 | `get_host_vmkernel_adapters` | VMkernel アダプタ一覧 | - |
| 78 | `get_host_portgroups` | 標準スイッチポートグループ一覧 | - |
| 79 | `get_host_physical_nics` | 物理 NIC 一覧 | - |
| 80 | `list_host_services` | ESXi サービス一覧 | - |
| 81 | `start_stop_host_service` | ESXi サービス起動/停止 | 高 |
| 82 | `list_host_firewall_rules` | ESXi ファイアウォールルール一覧 | - |
| 83 | `get_host_dns_config` | ESXi DNS 設定取得 | - |
| 84 | `get_host_ntp_config` | ESXi NTP 設定取得 | - |
| 85 | `get_host_routing_config` | ESXi ルーティング設定取得 | - |
| 86 | `get_host_hardware_health` | ESXi ハードウェアヘルス情報 | - |
| 87 | `enable_esxi_ssh` | ESXi SSH 有効化 | 高 |
| 88 | `disable_esxi_ssh` | ESXi SSH 無効化 | 高 |
| 89 | `get_host_syslog_config` | ESXi syslog 設定取得 | - |
| 90 | `get_host_power_policy` | ESXi 電源管理ポリシー取得 | - |
| 91 | `set_host_power_policy` | ESXi 電源管理ポリシー設定 | 中 |
| 92 | `get_host_lockdown_mode` | ESXi ロックダウンモード取得 | - |
| 93 | `get_host_certificate_info` | ESXi SSL 証明書情報取得 | - |
| 94 | `get_host_time_config` | ESXi ホスト現在時刻取得 | - |
| 95 | `create_vswitch` | 標準 vSwitch 作成 | 高 |
| 96 | `remove_vswitch` | 標準 vSwitch 削除 | 高 |
| 97 | `update_vswitch` | 標準 vSwitch 更新 | 高 |
| 98 | `add_vmkernel_adapter` | VMkernel アダプタ追加 | 高 |
| 99 | `remove_vmkernel_adapter` | VMkernel アダプタ削除 | 高 |
| 100 | `set_host_dns_config` | ESXi DNS 設定変更 | 高 |
| 101 | `set_host_ntp_servers` | ESXi NTP サーバー設定 | 高 |
| 102 | `set_host_syslog_target` | ESXi syslog 送信先設定 | 高 |
| 103 | `set_host_lockdown_mode` | ESXi ロックダウンモード設定 | 重大 |
| 104 | `enable_host_firewall_ruleset` | ファイアウォールルールセット有効化 | 高 |
| 105 | `disable_host_firewall_ruleset` | ファイアウォールルールセット無効化 | 高 |
| 106 | `set_host_service_policy` | ESXi サービスポリシー設定 | 高 |
| 107 | `sync_host_time` | ESXi ホスト時刻同期 | 中 |
| 108 | `refresh_host_ca_certificates` | ESXi CA 証明書/CRL リフレッシュ | 高 |

## ネットワーキング（networking.py）- 10個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 109 | `get_dvswitch_config` | 分散仮想スイッチ詳細設定取得 | - |
| 110 | `get_dvportgroup_config` | 分散ポートグループ詳細設定取得 | - |
| 111 | `create_dvswitch` | 分散仮想スイッチ作成 | 高 |
| 112 | `create_dvportgroup` | 分散ポートグループ作成 | 高 |
| 113 | `add_host_portgroup` | 標準ポートグループ追加 | 高 |
| 114 | `remove_host_portgroup` | 標準ポートグループ削除 | 高 |
| 115 | `delete_dvswitch` | 分散仮想スイッチ削除 | 重大 |
| 116 | `delete_dvportgroup` | 分散ポートグループ削除 | 重大 |
| 117 | `update_dvportgroup` | 分散ポートグループ設定更新 | 高 |
| 118 | `update_dvswitch` | 分散仮想スイッチ設定更新 | 高 |

## パフォーマンス（performance.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 119 | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 120 | `get_host_performance` | ホストパフォーマンスメトリクス | - |

## イベント・監視（events.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 121 | `list_recent_events` | vCenter イベント一覧 | - |
| 122 | `list_alarms` | トリガー済みアラーム一覧 | - |
| 123 | `list_performance_counters` | パフォーマンスカウンタ一覧 | - |
| 124 | `get_alarm_definitions` | アラーム定義一覧 | - |
| 125 | `get_host_system_log` | ESXi ホスト診断ログ取得 | - |
| 126 | `list_diagnostic_log_keys` | 診断ログキー一覧 | - |
| 127 | `get_vcenter_log` | vCenter ログ取得 | - |
| 128 | `list_vcenter_log_keys` | vCenter ログキー一覧 | - |

## ストレージ（storage.py）- 13個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 129 | `get_datastore_info` | データストア詳細情報 | - |
| 130 | `get_storage_summary` | ストレージ全体サマリー | - |
| 131 | `list_host_storage_devices` | ホスト SCSI LUN/HBA 一覧 | - |
| 132 | `list_host_multipath_info` | ホストマルチパス情報一覧 | - |
| 133 | `rescan_host_storage` | ホストストレージ再スキャン | 中 |
| 134 | `mount_nfs_datastore` | NFS データストアマウント | 高 |
| 135 | `unmount_datastore` | データストアアンマウント | 重大 |
| 136 | `rename_datastore` | データストアリネーム | 中 |
| 137 | `refresh_datastore` | データストアリフレッシュ | - |
| 138 | `enter_datastore_maintenance_mode` | データストアメンテナンスモード開始 | 高 |
| 139 | `exit_datastore_maintenance_mode` | データストアメンテナンスモード解除 | 高 |
| 140 | `set_multipath_policy` | マルチパスポリシー設定 | 高 |
| 141 | `list_datastore_hosts` | データストア接続ホスト一覧 | - |

## バッチ操作（batch.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 142 | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 143 | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |
| 144 | `batch_get_vm_info` | 複数 VM 一括情報取得 | - |

## ゲスト操作（guest.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 145 | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 146 | `list_guest_processes` | ゲスト OS プロセス一覧 | - |
| 147 | `list_guest_files` | ゲスト OS ファイル一覧 | - |
| 148 | `create_guest_directory` | ゲスト OS ディレクトリ作成 | 中 |
| 149 | `delete_guest_file` | ゲスト OS ファイル削除 | 高 |
| 150 | `terminate_guest_process` | ゲスト OS プロセス終了 | 高 |
| 151 | `upgrade_vmware_tools` | VMware Tools アップグレード | 中 |
| 152 | `read_guest_environment_variables` | ゲスト OS 環境変数取得 | - |

## タグ・カスタム属性（tags.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 153 | `get_vm_annotation` | VM アノテーション取得 | - |
| 154 | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 155 | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 156 | `create_custom_attribute` | カスタム属性定義作成 | 中 |
| 157 | `set_custom_attribute_value` | カスタム属性値設定 | 低 |
| 158 | `get_entity_custom_attribute_values` | エンティティのカスタム属性値取得 | - |

## 詳細設定（advanced_settings.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 159 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 160 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 161 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 162 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |

## vCenter 管理（vcenter_admin.py）- 14個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 163 | `list_roles` | vCenter ロール一覧 | - |
| 164 | `get_entity_permissions` | エンティティ権限取得 | - |
| 165 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 166 | `list_active_sessions` | アクティブセッション一覧 | - |
| 167 | `list_recent_tasks` | 最近のタスク一覧 | - |
| 168 | `terminate_session` | セッション強制終了 | 高 |
| 169 | `create_role` | ロール作成 | 高 |
| 170 | `update_role` | ロール更新 | 高 |
| 171 | `delete_role` | ロール削除 | 高 |
| 172 | `set_entity_permissions` | エンティティ権限設定 | 高 |
| 173 | `remove_entity_permission` | エンティティ権限削除 | 高 |
| 174 | `cancel_task` | タスクキャンセル | 中 |
| 175 | `list_privileges` | 権限一覧 | - |
| 176 | `acknowledge_alarm` | アラーム確認応答 | 低 |

## クラスタ設定（cluster_config.py）- 17個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 177 | `get_cluster_ha_config` | HA 設定取得 | - |
| 178 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 179 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 180 | `get_cluster_drs_recommendations` | DRS レコメンデーション取得 | - |
| 181 | `create_resource_pool` | リソースプール作成 | 高 |
| 182 | `update_resource_pool` | リソースプール更新 | 高 |
| 183 | `delete_resource_pool` | リソースプール削除 | 高 |
| 184 | `list_cluster_host_vm_groups` | DRS ホスト/VM グループ一覧 | - |
| 185 | `configure_cluster_ha` | クラスタ HA 設定変更 | 高 |
| 186 | `configure_cluster_drs` | クラスタ DRS 設定変更 | 高 |
| 187 | `create_drs_rule` | DRS アフィニティルール作成 | 高 |
| 188 | `delete_drs_rule` | DRS アフィニティルール削除 | 高 |
| 189 | `apply_drs_recommendation` | DRS レコメンデーション適用 | 高 |
| 190 | `create_cluster` | クラスタ作成 | 高 |
| 191 | `delete_cluster` | クラスタ削除 | 重大 |
| 192 | `create_drs_vm_group` | DRS VM グループ作成 | 高 |
| 193 | `create_drs_host_group` | DRS ホストグループ作成 | 高 |

## フォルダ（folders.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 194 | `list_folders` | フォルダ一覧（パス付き） | - |
| 195 | `create_folder` | フォルダ作成 | 中 |
| 196 | `move_vm_to_folder` | VM をフォルダに移動 | 中 |
| 197 | `delete_folder` | フォルダ削除 | 高 |
| 198 | `rename_folder` | フォルダリネーム | 中 |
| 199 | `move_entity_to_folder` | エンティティをフォルダに移動 | 高 |

## データストアブラウザ（datastore_browser.py）- 5個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 200 | `browse_datastore` | データストアファイル参照 | - |
| 201 | `delete_datastore_file` | データストアファイル削除 | 重大 |
| 202 | `copy_datastore_file` | データストアファイルコピー | 高 |
| 203 | `move_datastore_file` | データストアファイル移動 | 高 |
| 204 | `create_datastore_directory` | データストアディレクトリ作成 | 中 |

---

## リスクレベル別サマリー

| リスクレベル | 件数 |
|-------------|------|
| - (読み取り専用) | 79 |
| 低 | 5 |
| 中 | 33 |
| 高 | 76 |
| 重大 | 11 |
| **合計** | **204** |
