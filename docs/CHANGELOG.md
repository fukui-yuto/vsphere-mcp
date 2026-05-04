# 変更履歴

このプロジェクトに対するすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/) に基づいており、
[セマンティックバージョニング](https://semver.org/lang/ja/) に準拠しています。

## [0.2.0] - 2026-05-04

大幅な機能拡充。83 ツールへの拡張、インフラ改善、ドキュメント整備。

### 全ツール一覧（83個）

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
| 16 | 電源 | `power_on_vm` | VM 電源オン | 低 |
| 17 | 電源 | `power_off_vm` | VM 強制電源オフ | 中 |
| 18 | 電源 | `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| 19 | 電源 | `reboot_vm` | ゲスト OS リブート | 中 |
| 20 | スナップショット | `create_snapshot` | スナップショット作成 | 中 |
| 21 | スナップショット | `revert_snapshot` | スナップショット復元 | 高 |
| 22 | スナップショット | `remove_snapshot` | スナップショット削除 | 高 |
| 23 | マイグレーション | `migrate_vm` | vMotion 移行 | 高 |
| 24 | ライフサイクル | `clone_vm` | VM クローン作成 | 高 |
| 25 | ライフサイクル | `deploy_from_template` | テンプレートデプロイ | 高 |
| 26 | ライフサイクル | `delete_vm` | VM 完全削除 | 重大 |
| 27 | リソース | `set_vm_resources` | VM CPU/メモリ変更 | 中 |
| 28 | リソース | `add_disk` | VM ディスク追加 | 中 |
| 29 | リソース | `add_nic` | VM NIC 追加 | 中 |
| 30 | ホスト管理 | `enter_maintenance_mode` | メンテナンスモード開始 | 高 |
| 31 | ホスト管理 | `exit_maintenance_mode` | メンテナンスモード解除 | 高 |
| 32 | パフォーマンス | `get_vm_performance` | VM パフォーマンスメトリクス | - |
| 33 | パフォーマンス | `get_host_performance` | ホストパフォーマンスメトリクス | - |
| 34 | イベント | `list_recent_events` | vCenter イベント一覧 | - |
| 35 | イベント | `list_alarms` | トリガー済みアラーム一覧 | - |
| 36 | ストレージ | `get_datastore_info` | データストア詳細情報 | - |
| 37 | ストレージ | `get_storage_summary` | ストレージ全体サマリー | - |
| 38 | バッチ | `batch_power_operation` | 複数 VM 一括電源操作 | 高 |
| 39 | バッチ | `batch_create_snapshots` | 複数 VM 一括スナップショット | 高 |
| 40 | ゲスト | `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| 41 | ゲスト | `list_guest_processes` | ゲスト OS プロセス一覧 | - |
| 42 | タグ | `get_vm_annotation` | VM アノテーション取得 | - |
| 43 | タグ | `set_vm_annotation` | VM アノテーション設定 | 低 |
| 44 | タグ | `get_custom_attributes` | カスタム属性定義一覧 | - |
| 45 | 詳細設定 | `get_esxi_advanced_settings` | ESXi 詳細設定取得 | - |
| 46 | 詳細設定 | `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| 47 | 詳細設定 | `get_vcenter_advanced_settings` | vCenter 詳細設定取得 | - |
| 48 | 詳細設定 | `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |
| 49 | ホスト設定 | `get_host_vswitches` | ESXi 標準 vSwitch 一覧 | - |
| 50 | ホスト設定 | `get_host_vmkernel_adapters` | VMkernel アダプタ一覧 | - |
| 51 | ホスト設定 | `get_host_portgroups` | 標準スイッチポートグループ一覧 | - |
| 52 | ホスト設定 | `get_host_physical_nics` | 物理 NIC 一覧 | - |
| 53 | ホスト設定 | `list_host_services` | ESXi サービス一覧 | - |
| 54 | ホスト設定 | `start_stop_host_service` | ESXi サービス起動/停止 | 高 |
| 55 | ホスト設定 | `list_host_firewall_rules` | ESXi ファイアウォールルール一覧 | - |
| 56 | ホスト設定 | `get_host_dns_config` | ESXi DNS 設定取得 | - |
| 57 | ホスト設定 | `get_host_ntp_config` | ESXi NTP 設定取得 | - |
| 58 | ホスト設定 | `get_host_routing_config` | ESXi ルーティング設定取得 | - |
| 59 | ホスト設定 | `get_host_hardware_health` | ESXi ハードウェアヘルス情報 | - |
| 60 | vCenter 管理 | `list_roles` | vCenter ロール一覧 | - |
| 61 | vCenter 管理 | `get_entity_permissions` | エンティティ権限取得 | - |
| 62 | vCenter 管理 | `get_license_info` | ライセンス情報（キーマスク済み） | - |
| 63 | vCenter 管理 | `list_active_sessions` | アクティブセッション一覧 | - |
| 64 | vCenter 管理 | `list_recent_tasks` | 最近のタスク一覧 | - |
| 65 | クラスタ設定 | `get_cluster_ha_config` | HA 設定取得 | - |
| 66 | クラスタ設定 | `get_cluster_drs_config` | DRS 設定取得 | - |
| 67 | クラスタ設定 | `list_drs_rules` | DRS アフィニティルール一覧 | - |
| 68 | クラスタ設定 | `get_cluster_drs_recommendations` | DRS レコメンデーション取得 | - |
| 69 | VM デバイス | `remove_disk` | VM ディスク削除 | 高 |
| 70 | VM デバイス | `expand_disk` | VM ディスク拡張 | 中 |
| 71 | VM デバイス | `remove_nic` | VM NIC 削除 | 高 |
| 72 | VM デバイス | `list_vm_controllers` | VM コントローラ一覧 | - |
| 73 | VM デバイス | `get_vm_extra_config` | VM extraConfig 取得 | - |
| 74 | VM デバイス | `set_vm_extra_config` | VM extraConfig 設定 | 中 |
| 75 | VM デバイス | `rename_vm` | VM リネーム | 中 |
| 76 | VM デバイス | `unregister_vm` | VM 登録解除（ファイル保持） | 高 |
| 77 | VM デバイス | `get_vm_console_url` | WebMKS コンソールチケット取得 | - |
| 78 | VM デバイス | `set_vm_boot_options` | VM ブートオプション設定 | 中 |
| 79 | フォルダ | `list_folders` | フォルダ一覧（パス付き） | - |
| 80 | フォルダ | `create_folder` | フォルダ作成 | 中 |
| 81 | フォルダ | `move_vm_to_folder` | VM をフォルダに移動 | 中 |
| 82 | DS ブラウザ | `browse_datastore` | データストアファイル参照 | - |
| 83 | DS ブラウザ | `delete_datastore_file` | データストアファイル削除 | 重大 |

### リスクレベル別サマリー

| リスクレベル | 件数 | 説明 |
|-------------|------|------|
| - (読み取り専用) | 47 | 確認不要。情報取得のみ |
| 低 | 2 | 軽微な変更。確認必須 |
| 中 | 13 | 元に戻せる操作。確認必須 |
| 高 | 19 | 重大な影響の可能性。確認必須 |
| 重大 | 2 | 不可逆操作。確認必須 |

### 追加（v0.2.0 新規）

#### インフラ

- SSE トランスポート対応（`--transport sse --port 8080`）
- Prometheus メトリクス（`--metrics-port 9090`、オプション依存）
- RBAC ポリシー（`VSPHERE_RBAC_POLICY` 環境変数）
- i18n メッセージフレームワーク（`VSPHERE_LANG` 環境変数、en/ja）
- `py.typed` マーカー（型情報提供）
- Dependabot 設定（pip / GitHub Actions 週次更新）

### 改善

- 共通ユーティリティの統合（`find_vm_with_props`, `wait_for_task`, `find_host_by_name` を `_base.py` に移動）
- デコレータ適用順序の修正（`handle_tool_errors` を外側に統一）
- タスクタイムアウト時のキャンセル処理追加
- バッチ操作での VM 一括取得による効率化
- 入力バリデーション強化（CPU/メモリ/ディスクサイズ）
- SSL 無効化時の警告ログ追加
- PropertyCollector の propSet null ガード
- CI にカバレッジレポート（pytest-cov）と型チェック（mypy）を追加
- confirm レスポンスでのパスワード自動マスク
- configManager / fileManager 等の null ガード追加
- ライセンスキーの安全なマスク処理改善
- クロスレビューによる品質向上（2エージェント体制）
- 50 件の自動テスト

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
