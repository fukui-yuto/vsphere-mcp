# ツール一覧（全301個）

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

## インベントリ（inventory.py）- 18個

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
| 17 | `get_vm_screenshot` | VM スクリーンショット取得 | - |
| 18 | `wait_for_vm_guest_ip` | VM ゲスト IP アドレス待機取得 | - |

## 電源操作（power.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 19 | `power_on_vm` | VM 電源オン | 低 |
| 20 | `power_off_vm` | VM 強制電源オフ | 中 |
| 21 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 22 | `reboot_vm` | ゲスト OS リブート | 中 |
| 23 | `suspend_vm` | VM サスペンド | 中 |
| 24 | `reset_vm` | VM ハードリセット | 高 |

## スナップショット（snapshot.py）- 7個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 25 | `create_snapshot` | スナップショット作成 | 中 |
| 26 | `revert_snapshot` | スナップショット復元 | 高 |
| 27 | `remove_snapshot` | スナップショット削除 | 高 |
| 28 | `remove_all_snapshots` | 全スナップショット削除 | 高 |
| 29 | `rename_snapshot` | スナップショットリネーム | 中 |
| 30 | `revert_to_current_snapshot` | 現在のスナップショットに復元 | 高 |
| 31 | `consolidate_vm_disks` | VM ディスク統合（スナップショットコミット） | 高 |

## マイグレーション（migration.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 32 | `migrate_vm` | vMotion 移行 | 高 |
| 33 | `storage_vmotion` | Storage vMotion（ディスク移行） | 高 |
| 34 | `relocate_vm` | VM 再配置（コンピュート+ストレージ） | 高 |

## ライフサイクル（lifecycle.py）- 13個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 35 | `clone_vm` | VM クローン作成 | 高 |
| 36 | `deploy_from_template` | テンプレートデプロイ | 高 |
| 37 | `delete_vm` | VM 完全削除 | 重大 |
| 38 | `register_vm` | VMX ファイルから VM 登録 | 中 |
| 39 | `convert_vm_to_template` | VM をテンプレートに変換 | 高 |
| 40 | `convert_template_to_vm` | テンプレートを VM に変換 | 高 |
| 41 | `create_vm` | 空の VM を新規作成 | 高 |
| 42 | `list_guest_os_types` | サポートされるゲスト OS タイプ一覧 | - |
| 43 | `linked_clone_vm` | リンククローン VM 作成 | 高 |
| 44 | `enable_vm_cbt` | VM Change Block Tracking 有効化 | 中 |
| 45 | `query_vm_changed_disk_areas` | CBT による変更ディスク領域クエリ | - |
| 46 | `answer_vm_question` | VM 質問ダイアログへの応答 | 中 |
| 47 | `get_vm_pending_question` | VM 保留中の質問取得 | - |

## リソース（resources.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 48 | `set_vm_resources` | VM CPU/メモリ変更 | 中 |
| 49 | `add_disk` | VM ディスク追加 | 中 |
| 50 | `add_nic` | VM NIC 追加 | 中 |
| 51 | `add_vm_cd_drive` | VM CD/DVD ドライブ追加 | 中 |
| 52 | `set_vm_cpu_allocation` | VM CPU リソース割り当て設定（予約/制限/シェア） | 中 |
| 53 | `set_vm_memory_allocation` | VM メモリリソース割り当て設定 | 中 |
| 54 | `set_vm_memory_hotadd` | VM メモリホットアド有効/無効 | 中 |
| 55 | `set_vm_latency_sensitivity` | VM レイテンシ感度設定 | 中 |

## VM デバイス（vm_devices.py）- 26個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 56 | `remove_disk` | VM ディスク削除 | 高 |
| 57 | `expand_disk` | VM ディスク拡張 | 中 |
| 58 | `remove_nic` | VM NIC 削除 | 高 |
| 59 | `list_vm_controllers` | VM コントローラ一覧 | - |
| 60 | `get_vm_extra_config` | VM extraConfig 取得 | - |
| 61 | `set_vm_extra_config` | VM extraConfig 設定 | 中 |
| 62 | `rename_vm` | VM リネーム | 中 |
| 63 | `unregister_vm` | VM 登録解除（ファイル保持） | 高 |
| 64 | `get_vm_console_url` | WebMKS コンソールチケット取得 | - |
| 65 | `set_vm_boot_options` | VM ブートオプション設定 | 中 |
| 66 | `list_vm_cddvd_drives` | CD/DVD ドライブ一覧（ISO マウント状態） | - |
| 67 | `mount_vm_cdrom_iso` | CD/DVD に ISO マウント | 中 |
| 68 | `disconnect_vm_cdrom` | CD/DVD ドライブ切断 | 低 |
| 69 | `get_vm_video_card` | ビデオカード設定取得 | - |
| 70 | `list_vm_disk_layout` | ディスクレイアウト詳細 | - |
| 71 | `list_vm_snapshots_disk_usage` | スナップショットディスク使用量 | - |
| 72 | `change_vm_nic_network` | VM NIC ネットワーク変更 | 中 |
| 73 | `connect_disconnect_vm_nic` | VM NIC 接続/切断 | 中 |
| 74 | `add_vm_scsi_controller` | SCSI コントローラ追加 | 中 |
| 75 | `upgrade_vm_hardware` | VM ハードウェアバージョンアップグレード | 高 |
| 76 | `set_vm_cpu_hotadd` | CPU ホットアド有効/無効 | 中 |
| 77 | `set_vm_cores_per_socket` | ソケットあたりコア数設定 | 中 |
| 78 | `change_vm_disk_mode` | VM ディスクモード変更 | 高 |
| 79 | `add_vtpm` | 仮想 TPM デバイス追加 | 高 |
| 80 | `set_vm_secure_boot` | VM セキュアブート有効/無効 | 中 |
| 81 | `configure_vm_vbs` | VM 仮想化ベースセキュリティ設定 | 高 |

## ホスト管理（host.py）- 11個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 82 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 83 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |
| 84 | `shutdown_host` | ESXi ホストシャットダウン | 重大 |
| 85 | `reboot_host` | ESXi ホストリブート | 重大 |
| 86 | `disconnect_host` | ESXi ホスト切断 | 重大 |
| 87 | `reconnect_host` | ESXi ホスト再接続 | 高 |
| 88 | `add_host_to_cluster` | クラスタにホスト追加 | 高 |
| 89 | `remove_host` | ホスト削除（インベントリから） | 重大 |
| 90 | `move_host_to_cluster` | ホストを別クラスタに移動 | 高 |
| 91 | `add_standalone_host` | スタンドアロンホスト追加 | 高 |
| 92 | `rename_host` | ESXi ホストリネーム | 中 |

## ホスト設定（host_config.py）- 33個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 93 | `get_host_vswitches` | ESXi 標準 vSwitch 一覧 | - |
| 94 | `get_host_vmkernel_adapters` | VMkernel アダプタ一覧 | - |
| 95 | `get_host_portgroups` | 標準スイッチポートグループ一覧 | - |
| 96 | `get_host_physical_nics` | 物理 NIC 一覧 | - |
| 97 | `list_host_services` | ESXi サービス一覧 | - |
| 98 | `start_stop_host_service` | ESXi サービス起動/停止 | 高 |
| 99 | `list_host_firewall_rules` | ESXi ファイアウォールルール一覧 | - |
| 100 | `get_host_dns_config` | ESXi DNS 設定取得 | - |
| 101 | `get_host_ntp_config` | ESXi NTP 設定取得 | - |
| 102 | `get_host_routing_config` | ESXi ルーティング設定取得 | - |
| 103 | `get_host_hardware_health` | ESXi ハードウェアヘルス情報 | - |
| 104 | `enable_esxi_ssh` | ESXi SSH 有効化 | 高 |
| 105 | `disable_esxi_ssh` | ESXi SSH 無効化 | 高 |
| 106 | `get_host_syslog_config` | ESXi syslog 設定取得 | - |
| 107 | `get_host_power_policy` | ESXi 電源管理ポリシー取得 | - |
| 108 | `set_host_power_policy` | ESXi 電源管理ポリシー設定 | 中 |
| 109 | `get_host_lockdown_mode` | ESXi ロックダウンモード取得 | - |
| 110 | `get_host_certificate_info` | ESXi SSL 証明書情報取得 | - |
| 111 | `get_host_time_config` | ESXi ホスト現在時刻取得 | - |
| 112 | `create_vswitch` | 標準 vSwitch 作成 | 高 |
| 113 | `remove_vswitch` | 標準 vSwitch 削除 | 高 |
| 114 | `update_vswitch` | 標準 vSwitch 更新 | 高 |
| 115 | `add_vmkernel_adapter` | VMkernel アダプタ追加 | 高 |
| 116 | `remove_vmkernel_adapter` | VMkernel アダプタ削除 | 高 |
| 117 | `set_host_dns_config` | ESXi DNS 設定変更 | 高 |
| 118 | `set_host_ntp_servers` | ESXi NTP サーバー設定 | 高 |
| 119 | `set_host_syslog_target` | ESXi syslog 送信先設定 | 高 |
| 120 | `set_host_lockdown_mode` | ESXi ロックダウンモード設定 | 重大 |
| 121 | `enable_host_firewall_ruleset` | ファイアウォールルールセット有効化 | 高 |
| 122 | `disable_host_firewall_ruleset` | ファイアウォールルールセット無効化 | 高 |
| 123 | `set_host_service_policy` | ESXi サービスポリシー設定 | 高 |
| 124 | `sync_host_time` | ESXi ホスト時刻同期 | 中 |
| 125 | `refresh_host_ca_certificates` | ESXi CA 証明書/CRL リフレッシュ | 高 |

## ネットワーキング（networking.py）- 15個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 126 | `get_dvswitch_config` | 分散仮想スイッチ詳細設定取得 | - |
| 127 | `get_dvportgroup_config` | 分散ポートグループ詳細設定取得 | - |
| 128 | `create_dvswitch` | 分散仮想スイッチ作成 | 高 |
| 129 | `create_dvportgroup` | 分散ポートグループ作成 | 高 |
| 130 | `add_host_portgroup` | 標準ポートグループ追加 | 高 |
| 131 | `remove_host_portgroup` | 標準ポートグループ削除 | 高 |
| 132 | `delete_dvswitch` | 分散仮想スイッチ削除 | 重大 |
| 133 | `delete_dvportgroup` | 分散ポートグループ削除 | 重大 |
| 134 | `update_dvportgroup` | 分散ポートグループ設定更新 | 高 |
| 135 | `update_dvswitch` | 分散仮想スイッチ設定更新 | 高 |
| 136 | `add_host_to_dvswitch` | ホストを分散仮想スイッチに追加 | 高 |
| 137 | `remove_host_from_dvswitch` | ホストを分散仮想スイッチから削除 | 高 |
| 138 | `list_dvswitch_ports` | 分散仮想スイッチポート一覧 | - |
| 139 | `configure_dvs_pvlan` | DVS プライベート VLAN 設定 | 高 |
| 140 | `configure_host_vswitch_nic_teaming` | ホスト vSwitch NIC チーミング設定 | 高 |

## パフォーマンス（performance.py）- 7個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 141 | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 142 | `get_host_performance` | ホストパフォーマンスメトリクス | - |
| 143 | `get_datastore_performance` | データストアパフォーマンスメトリクス | - |
| 144 | `get_historical_performance` | 過去のパフォーマンスデータ取得 | - |
| 145 | `get_custom_metrics` | カスタムメトリクス取得 | - |
| 146 | `list_performance_intervals` | パフォーマンス収集インターバル一覧 | - |
| 147 | `list_available_metrics` | 利用可能なパフォーマンスメトリクス一覧 | - |

## イベント・監視（events.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 148 | `list_recent_events` | vCenter イベント一覧 | - |
| 149 | `list_alarms` | トリガー済みアラーム一覧 | - |
| 150 | `list_performance_counters` | パフォーマンスカウンタ一覧 | - |
| 151 | `get_alarm_definitions` | アラーム定義一覧 | - |
| 152 | `get_host_system_log` | ESXi ホスト診断ログ取得 | - |
| 153 | `list_diagnostic_log_keys` | 診断ログキー一覧 | - |
| 154 | `get_vcenter_log` | vCenter ログ取得 | - |
| 155 | `list_vcenter_log_keys` | vCenter ログキー一覧 | - |

## ストレージ（storage.py）- 21個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 156 | `get_datastore_info` | データストア詳細情報 | - |
| 157 | `get_storage_summary` | ストレージ全体サマリー | - |
| 158 | `list_host_storage_devices` | ホスト SCSI LUN/HBA 一覧 | - |
| 159 | `list_host_multipath_info` | ホストマルチパス情報一覧 | - |
| 160 | `rescan_host_storage` | ホストストレージ再スキャン | 中 |
| 161 | `mount_nfs_datastore` | NFS データストアマウント | 高 |
| 162 | `unmount_datastore` | データストアアンマウント | 重大 |
| 163 | `rename_datastore` | データストアリネーム | 中 |
| 164 | `refresh_datastore` | データストアリフレッシュ | - |
| 165 | `enter_datastore_maintenance_mode` | データストアメンテナンスモード開始 | 高 |
| 166 | `exit_datastore_maintenance_mode` | データストアメンテナンスモード解除 | 高 |
| 167 | `set_multipath_policy` | マルチパスポリシー設定 | 高 |
| 168 | `list_datastore_hosts` | データストア接続ホスト一覧 | - |
| 169 | `create_vmfs_datastore` | VMFS データストア作成 | 高 |
| 170 | `expand_vmfs_datastore` | VMFS データストア拡張 | 高 |
| 171 | `enable_iscsi_adapter` | ソフトウェア iSCSI アダプタ有効化 | 高 |
| 172 | `add_iscsi_target` | iSCSI ターゲット追加 | 高 |
| 173 | `create_datastore_cluster` | データストアクラスタ作成 | 高 |
| 174 | `configure_storage_drs` | Storage DRS 設定 | 高 |
| 175 | `list_datastore_clusters` | データストアクラスタ一覧 | - |
| 176 | `configure_sioc` | Storage I/O Control 設定 | 高 |

## バッチ操作（batch.py）- 5個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 177 | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 178 | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |
| 179 | `batch_get_vm_info` | 複数 VM 一括情報取得 | - |
| 180 | `batch_reconfigure_vms` | 複数 VM 一括設定変更 | 高 |
| 181 | `batch_migrate_vms` | 複数 VM 一括マイグレーション | 高 |

## ゲスト操作（guest.py）- 14個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 182 | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 183 | `list_guest_processes` | ゲスト OS プロセス一覧 | - |
| 184 | `list_guest_files` | ゲスト OS ファイル一覧 | - |
| 185 | `create_guest_directory` | ゲスト OS ディレクトリ作成 | 中 |
| 186 | `delete_guest_file` | ゲスト OS ファイル削除 | 高 |
| 187 | `terminate_guest_process` | ゲスト OS プロセス終了 | 高 |
| 188 | `upgrade_vmware_tools` | VMware Tools アップグレード | 中 |
| 189 | `read_guest_environment_variables` | ゲスト OS 環境変数取得 | - |
| 190 | `upload_file_to_guest` | ゲスト OS へファイルアップロード | 高 |
| 191 | `download_file_from_guest` | ゲスト OS からファイルダウンロード | - |
| 192 | `move_guest_file` | ゲスト OS ファイル移動/リネーム | 中 |
| 193 | `delete_guest_directory` | ゲスト OS ディレクトリ削除 | 高 |
| 194 | `get_guest_network_info` | ゲスト OS ネットワーク情報取得 | - |
| 195 | `get_guest_os_info` | ゲスト OS 詳細情報取得 | - |

## タグ・カスタム属性（tags.py）- 7個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 196 | `get_vm_annotation` | VM アノテーション取得 | - |
| 197 | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 198 | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 199 | `create_custom_attribute` | カスタム属性定義作成 | 中 |
| 200 | `set_custom_attribute_value` | カスタム属性値設定 | 低 |
| 201 | `get_entity_custom_attribute_values` | エンティティのカスタム属性値取得 | - |
| 202 | `delete_custom_attribute` | カスタム属性定義削除 | 高 |

## 詳細設定（advanced_settings.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 203 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 204 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 205 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 206 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |

## vCenter 管理（vcenter_admin.py）- 14個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 207 | `list_roles` | vCenter ロール一覧 | - |
| 208 | `get_entity_permissions` | エンティティ権限取得 | - |
| 209 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 210 | `list_active_sessions` | アクティブセッション一覧 | - |
| 211 | `list_recent_tasks` | 最近のタスク一覧 | - |
| 212 | `terminate_session` | セッション強制終了 | 高 |
| 213 | `create_role` | ロール作成 | 高 |
| 214 | `update_role` | ロール更新 | 高 |
| 215 | `delete_role` | ロール削除 | 高 |
| 216 | `set_entity_permissions` | エンティティ権限設定 | 高 |
| 217 | `remove_entity_permission` | エンティティ権限削除 | 高 |
| 218 | `cancel_task` | タスクキャンセル | 中 |
| 219 | `list_privileges` | 権限一覧 | - |
| 220 | `acknowledge_alarm` | アラーム確認応答 | 低 |

## クラスタ設定（cluster_config.py）- 25個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 221 | `get_cluster_ha_config` | HA 設定取得 | - |
| 222 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 223 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 224 | `get_cluster_drs_recommendations` | DRS レコメンデーション取得 | - |
| 225 | `create_resource_pool` | リソースプール作成 | 高 |
| 226 | `update_resource_pool` | リソースプール更新 | 高 |
| 227 | `delete_resource_pool` | リソースプール削除 | 高 |
| 228 | `list_cluster_host_vm_groups` | DRS ホスト/VM グループ一覧 | - |
| 229 | `configure_cluster_ha` | クラスタ HA 設定変更 | 高 |
| 230 | `configure_cluster_drs` | クラスタ DRS 設定変更 | 高 |
| 231 | `create_drs_rule` | DRS アフィニティルール作成 | 高 |
| 232 | `delete_drs_rule` | DRS アフィニティルール削除 | 高 |
| 233 | `apply_drs_recommendation` | DRS レコメンデーション適用 | 高 |
| 234 | `create_cluster` | クラスタ作成 | 高 |
| 235 | `delete_cluster` | クラスタ削除 | 重大 |
| 236 | `create_drs_vm_group` | DRS VM グループ作成 | 高 |
| 237 | `create_drs_host_group` | DRS ホストグループ作成 | 高 |
| 238 | `create_vm_host_affinity_rule` | VM-ホストアフィニティルール作成 | 高 |
| 239 | `delete_drs_group` | DRS グループ削除 | 高 |
| 240 | `update_drs_group` | DRS グループ更新 | 高 |
| 241 | `set_evc_mode` | クラスタ EVC モード設定 | 高 |
| 242 | `get_evc_mode` | クラスタ EVC モード取得 | - |
| 243 | `move_vm_to_resource_pool` | VM をリソースプールに移動 | 中 |
| 244 | `configure_dpm` | Distributed Power Management 設定 | 高 |
| 245 | `configure_ha_admission_control` | HA アドミッションコントロール設定 | 高 |

## フォルダ（folders.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 246 | `list_folders` | フォルダ一覧（パス付き） | - |
| 247 | `create_folder` | フォルダ作成 | 中 |
| 248 | `move_vm_to_folder` | VM をフォルダに移動 | 中 |
| 249 | `delete_folder` | フォルダ削除 | 高 |
| 250 | `rename_folder` | フォルダリネーム | 中 |
| 251 | `move_entity_to_folder` | エンティティをフォルダに移動 | 高 |

## データストアブラウザ（datastore_browser.py）- 5個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 252 | `browse_datastore` | データストアファイル参照 | - |
| 253 | `delete_datastore_file` | データストアファイル削除 | 重大 |
| 254 | `copy_datastore_file` | データストアファイルコピー | 高 |
| 255 | `move_datastore_file` | データストアファイル移動 | 高 |
| 256 | `create_datastore_directory` | データストアディレクトリ作成 | 中 |

## データセンター（datacenter.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 257 | `create_datacenter` | データセンター作成 | 高 |
| 258 | `delete_datacenter` | データセンター削除 | 重大 |
| 259 | `rename_datacenter` | データセンターリネーム | 中 |

## カスタマイズ仕様（customization.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 260 | `list_customization_specs` | カスタマイズ仕様一覧 | - |
| 261 | `get_customization_spec` | カスタマイズ仕様詳細取得 | - |
| 262 | `create_linux_customization_spec` | Linux カスタマイズ仕様作成 | 中 |
| 263 | `create_windows_customization_spec` | Windows カスタマイズ仕様作成 | 中 |
| 264 | `delete_customization_spec` | カスタマイズ仕様削除 | 高 |
| 265 | `apply_customization_to_vm` | カスタマイズ仕様を VM に適用 | 高 |

## アラーム管理（alarm.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 266 | `create_alarm` | アラーム定義作成 | 高 |
| 267 | `delete_alarm` | アラーム定義削除 | 高 |
| 268 | `reset_alarm_status` | アラームステータスリセット | 中 |
| 269 | `enable_disable_alarm` | アラーム有効/無効 | 中 |

## vSphere タグ（vsphere_tags.py）- 9個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 270 | `create_tag_category` | タグカテゴリ作成 | 中 |
| 271 | `list_tag_categories` | タグカテゴリ一覧 | - |
| 272 | `delete_tag_category` | タグカテゴリ削除 | 高 |
| 273 | `create_tag` | タグ作成 | 中 |
| 274 | `list_tags` | タグ一覧 | - |
| 275 | `delete_tag` | タグ削除 | 高 |
| 276 | `attach_tag` | オブジェクトにタグ付与 | 低 |
| 277 | `detach_tag` | オブジェクトからタグ削除 | 低 |
| 278 | `list_attached_tags` | オブジェクトのタグ一覧 | - |

## コンテンツライブラリ（content_library.py）- 7個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 279 | `list_content_libraries` | コンテンツライブラリ一覧 | - |
| 280 | `create_local_content_library` | ローカルコンテンツライブラリ作成 | 高 |
| 281 | `delete_content_library` | コンテンツライブラリ削除 | 重大 |
| 282 | `list_library_items` | ライブラリアイテム一覧 | - |
| 283 | `delete_library_item` | ライブラリアイテム削除 | 高 |
| 284 | `deploy_vm_from_library_item` | ライブラリアイテムから VM デプロイ | 高 |
| 285 | `sync_subscribed_library` | サブスクライブライブラリ同期 | 中 |

## vApp（vapp.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 286 | `list_vapps` | vApp 一覧 | - |
| 287 | `power_on_vapp` | vApp 電源オン | 中 |
| 288 | `power_off_vapp` | vApp 電源オフ | 高 |
| 289 | `delete_vapp` | vApp 削除 | 重大 |

## スケジュールタスク（scheduled_tasks.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 290 | `list_scheduled_tasks` | スケジュールタスク一覧 | - |
| 291 | `delete_scheduled_task` | スケジュールタスク削除 | 高 |
| 292 | `run_scheduled_task` | スケジュールタスク即時実行 | 高 |

## ホストプロファイル（host_profile.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 293 | `list_host_profiles` | ホストプロファイル一覧 | - |
| 294 | `check_host_profile_compliance` | ホストプロファイルコンプライアンス確認 | - |

## ライセンス管理（license.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 295 | `add_license` | ライセンスキー追加 | 高 |
| 296 | `remove_license` | ライセンスキー削除 | 高 |
| 297 | `assign_license` | エンティティにライセンス割り当て | 高 |
| 298 | `list_license_assignments` | ライセンス割り当て一覧 | - |

## フォールトトレランス（fault_tolerance.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 299 | `enable_fault_tolerance` | VM フォールトトレランス有効化 | 高 |
| 300 | `disable_fault_tolerance` | VM フォールトトレランス無効化 | 高 |
| 301 | `get_fault_tolerance_info` | フォールトトレランス情報取得 | - |

---

## リスクレベル別サマリー

| リスクレベル | 件数 |
|-------------|------|
| - (読み取り専用) | 104 |
| 低 | 7 |
| 中 | 51 |
| 高 | 124 |
| 重大 | 15 |
| **合計** | **301** |
