# 変更履歴

このプロジェクトに対するすべての重要な変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/) に基づいており、
[セマンティックバージョニング](https://semver.org/lang/ja/) に準拠しています。

## [0.2.0] - 2026-05-04

大幅な機能拡充。48 ツールへの拡張、インフラ改善、ドキュメント整備。

### 追加

#### 新ツール（20個追加）

**情報取得ツール（16個追加）**
- `list_resource_pools` - リソースプール一覧（CPU/メモリ割り当て）
- `list_distributed_switches` - 分散仮想スイッチ一覧
- `list_distributed_portgroups` - 分散ポートグループ一覧
- `get_vm_performance` - VM パフォーマンスメトリクス取得
- `get_host_performance` - ホストパフォーマンスメトリクス取得
- `list_recent_events` - vCenter イベント一覧取得
- `list_alarms` - トリガー済みアラーム一覧
- `get_datastore_info` - データストア詳細情報取得
- `get_storage_summary` - ストレージ全体サマリー
- `list_guest_processes` - ゲスト OS プロセス一覧
- `get_vm_annotation` - VM アノテーション取得
- `get_custom_attributes` - カスタム属性定義一覧
- `get_esxi_advanced_settings` - ESXi 詳細設定取得
- `get_vcenter_advanced_settings` - vCenter 詳細設定取得

**操作ツール（6個追加）**
- `batch_power_operation` - 複数 VM の一括電源操作（高リスク）
- `batch_create_snapshots` - 複数 VM の一括スナップショット作成（高リスク）
- `execute_guest_command` - ゲスト OS コマンド実行（高リスク）
- `set_vm_annotation` - VM アノテーション設定（低リスク）
- `set_esxi_advanced_setting` - ESXi 詳細設定変更（高リスク）
- `set_vcenter_advanced_setting` - vCenter 詳細設定変更（高リスク）

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
- 50 件の自動テスト

## [0.1.0] - 2025-05-04

初回リリース。vSphere 管理用 MCP サーバーの基盤と 28 個のツールを実装。

### 追加

#### 情報取得ツール（読み取り専用・確認不要）- 12個

- `test_connection` - vCenter への接続テストと基本情報の取得
- `list_vms` - 全仮想マシンの一覧表示（ホスト/クラスタによるフィルタ対応）
- `get_vm_info` - VM の詳細情報取得（CPU、メモリ、ディスク、NIC、ストレージ）
- `list_hosts` - 全 ESXi ホストの一覧表示（クラスタによるフィルタ対応）
- `get_host_info` - ESXi ホストの詳細情報取得
- `list_datacenters` - 全データセンターの一覧表示
- `list_clusters` - 全クラスタの一覧表示（データセンターによるフィルタ対応）
- `list_datastores` - 全データストアの一覧表示（容量情報付き）
- `list_networks` - 全ネットワーク（ポートグループ）の一覧表示
- `list_snapshots` - VM のスナップショット一覧（ツリー構造表示）
- `get_cluster_health` - クラスタのヘルスサマリとホスト詳細の取得
- `search_vms` - VM 名による検索（大文字小文字を区別しない）

#### 操作ツール（確認必須）- 16個

- `power_on_vm` - VM の電源オン（低リスク）
- `power_off_vm` - VM の強制電源オフ（中リスク）
- `shutdown_vm` - ゲスト OS のグレースフルシャットダウン（中リスク）
- `reboot_vm` - ゲスト OS のリブート（中リスク）
- `create_snapshot` - VM スナップショットの作成（中リスク）
- `revert_snapshot` - 指定スナップショットへの復元（高リスク）
- `remove_snapshot` - スナップショットの削除（高リスク）
- `migrate_vm` - 別ホストへの vMotion 移行（高リスク）
- `clone_vm` - VM のクローン作成（高リスク）
- `deploy_from_template` - テンプレートからの VM デプロイ（高リスク）
- `set_vm_resources` - VM リソース設定の変更（CPU/メモリ）（中リスク）
- `add_disk` - VM へのディスク追加（中リスク）
- `add_nic` - VM へのネットワークアダプタ追加（中リスク）
- `enter_maintenance_mode` - ESXi ホストのメンテナンスモード開始（高リスク）
- `exit_maintenance_mode` - ESXi ホストのメンテナンスモード解除（高リスク）
- `delete_vm` - VM の完全削除（重大リスク）

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
