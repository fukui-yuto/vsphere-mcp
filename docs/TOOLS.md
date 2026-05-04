# ツール一覧（全127個）

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

## 電源操作（power.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 17 | `power_on_vm` | VM 電源オン | 低 |
| 18 | `power_off_vm` | VM 強制電源オフ | 中 |
| 19 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 20 | `reboot_vm` | ゲスト OS リブート | 中 |

## スナップショット（snapshot.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 21 | `create_snapshot` | スナップショット作成 | 中 |
| 22 | `revert_snapshot` | スナップショット復元 | 高 |
| 23 | `remove_snapshot` | スナップショット削除 | 高 |

## マイグレーション（migration.py）- 1個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 24 | `migrate_vm` | vMotion 移行 | 高 |

## ライフサイクル（lifecycle.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 25 | `clone_vm` | VM クローン作成 | 高 |
| 26 | `deploy_from_template` | テンプレートデプロイ | 高 |
| 27 | `delete_vm` | VM 完全削除 | 重大 |
| 28 | `register_vm` | VMX ファイルから VM 登録 | 中 |
| 29 | `convert_vm_to_template` | VM をテンプレートに変換 | 高 |
| 30 | `convert_template_to_vm` | テンプレートを VM に変換 | 高 |
| 31 | `create_vm` | 空の VM を新規作成 | 高 |
| 32 | `list_guest_os_types` | サポートされるゲスト OS タイプ一覧 | - |

## リソース（resources.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 33 | `set_vm_resources` | VM CPU/メモリ変更 | 中 |
| 34 | `add_disk` | VM ディスク追加 | 中 |
| 35 | `add_nic` | VM NIC 追加 | 中 |

## VM デバイス（vm_devices.py）- 16個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 36 | `remove_disk` | VM ディスク削除 | 高 |
| 37 | `expand_disk` | VM ディスク拡張 | 中 |
| 38 | `remove_nic` | VM NIC 削除 | 高 |
| 39 | `list_vm_controllers` | VM コントローラ一覧 | - |
| 40 | `get_vm_extra_config` | VM extraConfig 取得 | - |
| 41 | `set_vm_extra_config` | VM extraConfig 設定 | 中 |
| 42 | `rename_vm` | VM リネーム | 中 |
| 43 | `unregister_vm` | VM 登録解除（ファイル保持） | 高 |
| 44 | `get_vm_console_url` | WebMKS コンソールチケット取得 | - |
| 45 | `set_vm_boot_options` | VM ブートオプション設定 | 中 |
| 46 | `list_vm_cddvd_drives` | CD/DVD ドライブ一覧（ISO マウント状態） | - |
| 47 | `mount_vm_cdrom_iso` | CD/DVD に ISO マウント | 中 |
| 48 | `disconnect_vm_cdrom` | CD/DVD ドライブ切断 | 低 |
| 49 | `get_vm_video_card` | ビデオカード設定取得 | - |
| 50 | `list_vm_disk_layout` | ディスクレイアウト詳細 | - |
| 51 | `list_vm_snapshots_disk_usage` | スナップショットディスク使用量 | - |

## ホスト管理（host.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 52 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 53 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |
| 54 | `shutdown_host` | ESXi ホストシャットダウン | 重大 |
| 55 | `reboot_host` | ESXi ホストリブート | 重大 |
| 56 | `disconnect_host` | ESXi ホスト切断 | 重大 |
| 57 | `reconnect_host` | ESXi ホスト再接続 | 高 |

## ホスト設定（host_config.py）- 19個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 58 | `get_host_vswitches` | ESXi 標準 vSwitch 一覧 | - |
| 59 | `get_host_vmkernel_adapters` | VMkernel アダプタ一覧 | - |
| 60 | `get_host_portgroups` | 標準スイッチポートグループ一覧 | - |
| 61 | `get_host_physical_nics` | 物理 NIC 一覧 | - |
| 62 | `list_host_services` | ESXi サービス一覧 | - |
| 63 | `start_stop_host_service` | ESXi サービス起動/停止 | 高 |
| 64 | `list_host_firewall_rules` | ESXi ファイアウォールルール一覧 | - |
| 65 | `get_host_dns_config` | ESXi DNS 設定取得 | - |
| 66 | `get_host_ntp_config` | ESXi NTP 設定取得 | - |
| 67 | `get_host_routing_config` | ESXi ルーティング設定取得 | - |
| 68 | `get_host_hardware_health` | ESXi ハードウェアヘルス情報 | - |
| 69 | `enable_esxi_ssh` | ESXi SSH 有効化 | 高 |
| 70 | `disable_esxi_ssh` | ESXi SSH 無効化 | 高 |
| 71 | `get_host_syslog_config` | ESXi syslog 設定取得 | - |
| 72 | `get_host_power_policy` | ESXi 電源管理ポリシー取得 | - |
| 73 | `set_host_power_policy` | ESXi 電源管理ポリシー設定 | 中 |
| 74 | `get_host_lockdown_mode` | ESXi ロックダウンモード取得 | - |
| 75 | `get_host_certificate_info` | ESXi SSL 証明書情報取得 | - |
| 76 | `get_host_time_config` | ESXi ホスト現在時刻取得 | - |

## ネットワーキング（networking.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 77 | `get_dvswitch_config` | 分散仮想スイッチ詳細設定取得 | - |
| 78 | `get_dvportgroup_config` | 分散ポートグループ詳細設定取得 | - |
| 79 | `add_host_portgroup` | 標準ポートグループ追加 | 高 |
| 80 | `remove_host_portgroup` | 標準ポートグループ削除 | 高 |

## パフォーマンス（performance.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 81 | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 82 | `get_host_performance` | ホストパフォーマンスメトリクス | - |

## イベント・監視（events.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 83 | `list_recent_events` | vCenter イベント一覧 | - |
| 84 | `list_alarms` | トリガー済みアラーム一覧 | - |
| 85 | `list_performance_counters` | パフォーマンスカウンタ一覧 | - |
| 86 | `get_alarm_definitions` | アラーム定義一覧 | - |
| 87 | `get_host_system_log` | ESXi ホスト診断ログ取得 | - |
| 88 | `list_diagnostic_log_keys` | 診断ログキー一覧 | - |

## ストレージ（storage.py）- 5個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 89 | `get_datastore_info` | データストア詳細情報 | - |
| 90 | `get_storage_summary` | ストレージ全体サマリー | - |
| 91 | `list_host_storage_devices` | ホスト SCSI LUN/HBA 一覧 | - |
| 92 | `list_host_multipath_info` | ホストマルチパス情報一覧 | - |
| 93 | `rescan_host_storage` | ホストストレージ再スキャン | 中 |

## バッチ操作（batch.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 94 | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 95 | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |
| 96 | `batch_get_vm_info` | 複数 VM 一括情報取得 | - |

## ゲスト操作（guest.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 97 | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 98 | `list_guest_processes` | ゲスト OS プロセス一覧 | - |

## タグ・カスタム属性（tags.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 99 | `get_vm_annotation` | VM アノテーション取得 | - |
| 100 | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 101 | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 102 | `create_custom_attribute` | カスタム属性定義作成 | 中 |
| 103 | `set_custom_attribute_value` | カスタム属性値設定 | 低 |
| 104 | `get_entity_custom_attribute_values` | エンティティのカスタム属性値取得 | - |

## 詳細設定（advanced_settings.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 105 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 106 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 107 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 108 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |

## vCenter 管理（vcenter_admin.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 109 | `list_roles` | vCenter ロール一覧 | - |
| 110 | `get_entity_permissions` | エンティティ権限取得 | - |
| 111 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 112 | `list_active_sessions` | アクティブセッション一覧 | - |
| 113 | `list_recent_tasks` | 最近のタスク一覧 | - |
| 114 | `terminate_session` | セッション強制終了 | 高 |

## クラスタ設定（cluster_config.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 115 | `get_cluster_ha_config` | HA 設定取得 | - |
| 116 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 117 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 118 | `get_cluster_drs_recommendations` | DRS レコメンデーション取得 | - |
| 119 | `create_resource_pool` | リソースプール作成 | 高 |
| 120 | `update_resource_pool` | リソースプール更新 | 高 |
| 121 | `delete_resource_pool` | リソースプール削除 | 高 |
| 122 | `list_cluster_host_vm_groups` | DRS ホスト/VM グループ一覧 | - |

## フォルダ（folders.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 123 | `list_folders` | フォルダ一覧（パス付き） | - |
| 124 | `create_folder` | フォルダ作成 | 中 |
| 125 | `move_vm_to_folder` | VM をフォルダに移動 | 中 |

## データストアブラウザ（datastore_browser.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 126 | `browse_datastore` | データストアファイル参照 | - |
| 127 | `delete_datastore_file` | データストアファイル削除 | 重大 |

---

## リスクレベル別サマリー

| リスクレベル | 件数 |
|-------------|------|
| - (読み取り専用) | 72 |
| 低 | 4 |
| 中 | 18 |
| 高 | 28 |
| 重大 | 5 |
| **合計** | **127** |
