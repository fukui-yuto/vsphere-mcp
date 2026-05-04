# ツール一覧（全118個）

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

## インベントリ（inventory.py）- 15個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 1 | `test_connection` | vCenter 接続テストと基本情報取得 | - |
| 2 | `list_vms` | 全 VM 一覧（ホスト/クラスタフィルタ） | - |
| 3 | `get_vm_info` | VM 詳細情報（CPU/メモリ/���ィスク/NIC） | - |
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

## 電源操作（power.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 16 | `power_on_vm` | VM 電源オン | 低 |
| 17 | `power_off_vm` | VM 強制電源オフ | 中 |
| 18 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 19 | `reboot_vm` | ゲスト OS リブート | 中 |

## スナップショット（snapshot.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 20 | `create_snapshot` | スナップショット作成 | 中 |
| 21 | `revert_snapshot` | スナップショット復元 | 高 |
| 22 | `remove_snapshot` | スナップショット削除 | 高 |

## マイグレーション（migration.py）- 1個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 23 | `migrate_vm` | vMotion 移行 | 高 |

## ライフサイクル（lifecycle.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 24 | `clone_vm` | VM クローン作成 | 高 |
| 25 | `deploy_from_template` | テンプレートデプロイ | 高 |
| 26 | `delete_vm` | VM 完全削��� | 重大 |
| 27 | `register_vm` | VMX ファイルから VM 登録 | 中 |
| 28 | `convert_vm_to_template` | VM をテンプレートに変換 | 高 |
| 29 | `convert_template_to_vm` | テンプレートを VM に変換 | 高 |
| 30 | `create_vm` | 空の VM を新規作成 | 高 |
| 31 | `list_guest_os_types` | サポートされるゲスト OS タイプ一覧 | - |

## リソース（resources.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 32 | `set_vm_resources` | VM CPU/メモリ変更 | 中 |
| 33 | `add_disk` | VM ディスク追加 | 中 |
| 34 | `add_nic` | VM NIC 追加 | 中 |

## VM デバイス（vm_devices.py）- 15個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 35 | `remove_disk` | VM ディスク削除 | 高 |
| 36 | `expand_disk` | VM ディスク拡張 | 中 |
| 37 | `remove_nic` | VM NIC 削除 | 高 |
| 38 | `list_vm_controllers` | VM コントローラ一覧 | - |
| 39 | `get_vm_extra_config` | VM extraConfig 取得 | - |
| 40 | `set_vm_extra_config` | VM extraConfig 設定 | 中 |
| 41 | `rename_vm` | VM リネーム | 中 |
| 42 | `unregister_vm` | VM 登録解除（ファイル保持） | 高 |
| 43 | `get_vm_console_url` | WebMKS コンソールチケット取得 | - |
| 44 | `set_vm_boot_options` | VM ブートオプション設定 | 中 |
| 45 | `list_vm_cddvd_drives` | CD/DVD ドライブ一覧（ISO マウント状態） | - |
| 46 | `mount_vm_cdrom_iso` | CD/DVD に ISO マウント | 中 |
| 47 | `disconnect_vm_cdrom` | CD/DVD ドライブ切断 | 低 |
| 48 | `get_vm_video_card` | ビデオカード設定取得 | - |
| 49 | `list_vm_disk_layout` | ディスクレイアウト詳細 | - |

## ホスト管理（host.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 50 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 51 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |

## ホスト設定（host_config.py）- 18個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 52 | `get_host_vswitches` | ESXi 標準 vSwitch 一覧 | - |
| 53 | `get_host_vmkernel_adapters` | VMkernel アダプタ一覧 | - |
| 54 | `get_host_portgroups` | 標準スイッチポートグループ一覧 | - |
| 55 | `get_host_physical_nics` | ���理 NIC 一覧 | - |
| 56 | `list_host_services` | ESXi サービス一覧 | - |
| 57 | `start_stop_host_service` | ESXi サービス起動/停止 | 高 |
| 58 | `list_host_firewall_rules` | ESXi ファイアウォールルール一覧 | - |
| 59 | `get_host_dns_config` | ESXi DNS 設定���得 | - |
| 60 | `get_host_ntp_config` | ESXi NTP 設定取得 | - |
| 61 | `get_host_routing_config` | ESXi ルーティング設定取得 | - |
| 62 | `get_host_hardware_health` | ESXi ハードウェアヘルス情報 | - |
| 63 | `enable_esxi_ssh` | ESXi SSH 有効化 | 高 |
| 64 | `disable_esxi_ssh` | ESXi SSH 無効化 | 高 |
| 65 | `get_host_syslog_config` | ESXi syslog 設定取得 | - |
| 66 | `get_host_power_policy` | ESXi 電源管理ポリシー取得 | - |
| 67 | `set_host_power_policy` | ESXi 電源管理ポリシー設定 | 中 |
| 68 | `get_host_lockdown_mode` | ESXi ロックダウンモード取得 | - |
| 69 | `get_host_certificate_info` | ESXi SSL 証明書情報取得 | - |

## ネットワーキング（networking.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 70 | `get_dvswitch_config` | 分散仮想スイッチ詳細設定取得 | - |
| 71 | `get_dvportgroup_config` | 分散ポートグループ詳細設定取得 | - |
| 72 | `add_host_portgroup` | 標準ポートグループ追加 | 高 |
| 73 | `remove_host_portgroup` | 標準ポートグループ削除 | 高 |

## パフォーマンス（performance.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 74 | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 75 | `get_host_performance` | ホストパフォーマンスメトリクス | - |

## イベント・監視（events.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 76 | `list_recent_events` | vCenter イベント一覧 | - |
| 77 | `list_alarms` | トリガー済みアラーム一覧 | - |
| 78 | `list_performance_counters` | パフォーマンスカウンタ一覧 | - |
| 79 | `get_alarm_definitions` | アラーム定義一覧 | - |
| 80 | `get_host_system_log` | ESXi ホスト診断ログ取得 | - |
| 81 | `list_diagnostic_log_keys` | 診断ログキー一覧 | - |

## ストレージ（storage.py）- 5個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 82 | `get_datastore_info` | データストア詳細情報 | - |
| 83 | `get_storage_summary` | ストレージ全体サマリー | - |
| 84 | `list_host_storage_devices` | ホスト SCSI LUN/HBA 一覧 | - |
| 85 | `list_host_multipath_info` | ホストマルチパス情報一覧 | - |
| 86 | `rescan_host_storage` | ホストストレージ再スキャン | 中 |

## バッチ操作（batch.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 87 | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 88 | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |

## ゲスト操作（guest.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 89 | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 90 | `list_guest_processes` | ゲスト OS プロセス一覧 | - |

## タグ・カスタム属性（tags.py）- 6個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 91 | `get_vm_annotation` | VM アノテーション取得 | - |
| 92 | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 93 | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 94 | `create_custom_attribute` | カスタム属性定義作成 | 中 |
| 95 | `set_custom_attribute_value` | カスタム属性値設定 | 低 |
| 96 | `get_entity_custom_attribute_values` | エンティティのカスタム属性値取得 | - |

## 詳細設定（advanced_settings.py）- 4個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 97 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 98 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 99 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 100 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |

## vCenter 管理（vcenter_admin.py）- 5個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 101 | `list_roles` | vCenter ロール一覧 | - |
| 102 | `get_entity_permissions` | エンティティ権限取得 | - |
| 103 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 104 | `list_active_sessions` | アクティブセッション一覧 | - |
| 105 | `list_recent_tasks` | 最近のタスク一覧 | - |

## クラスタ設定（cluster_config.py）- 8個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 106 | `get_cluster_ha_config` | HA 設定取得 | - |
| 107 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 108 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 109 | `get_cluster_drs_recommendations` | DRS レコメ��デーション取得 | - |
| 110 | `create_resource_pool` | リソースプール作成 | 高 |
| 111 | `update_resource_pool` | リソースプール更新 | 高 |
| 112 | `delete_resource_pool` | リソースプール削除 | 高 |
| 113 | `list_cluster_host_vm_groups` | DRS ホスト/VM グループ一覧 | - |

## フォルダ（folders.py）- 3個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 114 | `list_folders` | フォルダ一覧（パス付き） | - |
| 115 | `create_folder` | フォルダ作成 | 中 |
| 116 | `move_vm_to_folder` | VM をフォルダに移動 | 中 |

## データストアブラウザ（datastore_browser.py）- 2個

| # | ツール名 | 説明 | リスク |
|---|----------|------|--------|
| 117 | `browse_datastore` | データストアファイル参照 | - |
| 118 | `delete_datastore_file` | データストアファイル削除 | 重大 |

---

## リスクレベル別サマリー

| リスクレベル | 件数 |
|-------------|------|
| - (読み取り専用) | 64 |
| 低 | 4 |
| 中 | 18 |
| 高 | 29 |
| 重大 | 3 |
| **合計** | **118** |
