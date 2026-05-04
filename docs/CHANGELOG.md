# 変更履歴

このプロジェクトに対するすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/) に基づいており、
[セマンティックバージョニング](https://semver.org/lang/ja/) に準拠しています。

## [0.2.0] - 2026-05-04

大幅な機能拡充。127 ツールへの拡張、インフラ改善、ドキュメント整備。

### 全ツール一覧（127個）

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
| 79 | ネットワーク | `add_host_portgroup` | 標準ポートグループ追加 | 高 |
| 80 | ネットワーク | `remove_host_portgroup` | 標準ポートグループ削除 | 高 |
| 81 | パフォーマンス | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 82 | パフォーマンス | `get_host_performance` | ホストパフォーマンスメトリクス | - |
| 83 | イベント | `list_recent_events` | vCenter イベント一覧 | - |
| 84 | イベント | `list_alarms` | トリガー済みアラーム一覧 | - |
| 85 | イベント | `list_performance_counters` | パフォーマンスカウンタ一覧 | - |
| 86 | イベント | `get_alarm_definitions` | アラーム定義一覧 | - |
| 87 | イベント | `get_host_system_log` | ESXi ホスト診断ログ取得 | - |
| 88 | イベント | `list_diagnostic_log_keys` | 診断ログキー一覧 | - |
| 89 | ストレージ | `get_datastore_info` | データストア詳細情報 | - |
| 90 | ストレージ | `get_storage_summary` | ストレージ全体サマリー | - |
| 91 | ストレージ | `list_host_storage_devices` | ホスト SCSI LUN/HBA 一覧 | - |
| 92 | ストレージ | `list_host_multipath_info` | ホストマルチパス情報一覧 | - |
| 93 | ストレージ | `rescan_host_storage` | ホストストレージ再スキャン | 中 |
| 94 | バッチ | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 95 | バッチ | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |
| 96 | バッチ | `batch_get_vm_info` | 複数 VM 一括情報取得 | - |
| 97 | ゲスト | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 98 | ゲスト | `list_guest_processes` | ゲスト OS プロセス一覧 | - |
| 99 | タグ | `get_vm_annotation` | VM アノテーション取得 | - |
| 100 | タグ | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 101 | タグ | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 102 | タグ | `create_custom_attribute` | カスタム属性定義作成 | 中 |
| 103 | タグ | `set_custom_attribute_value` | カスタム属性値設定 | 低 |
| 104 | タグ | `get_entity_custom_attribute_values` | エンティティのカスタム属性値取得 | - |
| 105 | 詳細設定 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 106 | 詳細設定 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 107 | 詳細設定 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 108 | 詳細設定 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |
| 109 | vCenter 管理 | `list_roles` | vCenter ロール一覧 | - |
| 110 | vCenter 管理 | `get_entity_permissions` | エンティティ権限取得 | - |
| 111 | vCenter 管理 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 112 | vCenter 管理 | `list_active_sessions` | アクティブセッション一覧 | - |
| 113 | vCenter 管理 | `list_recent_tasks` | 最近のタスク一覧 | - |
| 114 | vCenter 管理 | `terminate_session` | セッション強制終了 | 高 |
| 115 | クラスタ設定 | `get_cluster_ha_config` | HA 設定取得 | - |
| 116 | クラスタ設定 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 117 | クラスタ設定 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 118 | クラスタ設定 | `get_cluster_drs_recommendations` | DRS レコメンデーション取得 | - |
| 119 | クラスタ設定 | `create_resource_pool` | リソースプール作成 | 高 |
| 120 | クラスタ設定 | `update_resource_pool` | リソースプール更新 | 高 |
| 121 | クラスタ設定 | `delete_resource_pool` | リソースプール削除 | 高 |
| 122 | クラスタ設定 | `list_cluster_host_vm_groups` | DRS ホスト/VM グループ一覧 | - |
| 123 | フォルダ | `list_folders` | フォルダ一覧（パス付き） | - |
| 124 | フォルダ | `create_folder` | フォルダ作成 | 中 |
| 125 | フォルダ | `move_vm_to_folder` | VM をフォルダに移動 | 中 |
| 126 | DS ブラウザ | `browse_datastore` | データストアファイル参照 | - |
| 127 | DS ブラウザ | `delete_datastore_file` | データストアファイル削除 | 重大 |

### リスクレベル別サマリー

| リスクレベル | 件数 | 説明 |
|-------------|------|------|
| - (読み取り専用) | 72 | 確認不要。情報取得のみ |
| 低 | 4 | 軽微な変更。確認必須 |
| 中 | 18 | 元に戻せる操作。確認必須 |
| 高 | 28 | 重大な影響の可能性。確認必須 |
| 重大 | 5 | 不可逆操作。確認必須 |

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
