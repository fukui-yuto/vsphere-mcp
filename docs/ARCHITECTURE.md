# アーキテクチャ設計書

## システム概要

```
┌─────────────┐    stdio/SSE    ┌──────────────────────┐    HTTPS     ┌───────────────────────┐
│             │ ◄────────────► │                      │ ◄──────────► │                       │
│ Claude Code │                │  vsphere-mcp server  │   pyVmomi   │  vCenter Server       │
│             │   MCP Protocol │       (Python)       │             │  または vcsim (開発用) │
└─────────────┘                └──────────────────────┘              └───────────────────────┘
```

## 主要コンポーネント

### server.py - MCP サーバーエントリポイント
- FastMCP を使用した MCP サーバー
- stdio トランスポート（デフォルト）または SSE トランスポート（`--transport sse --port 8080`）
- 全ツールモジュールの登録
- RBAC ポリシー・メトリクス・i18n の初期化

### config.py - 設定管理
- `pydantic-settings` による環境変数ベースの設定
- `VSPHERE_PASSWORD_FILE` 対応（Docker Secret / Kubernetes Secret 連携）
- `model_validator` によるパスワードファイルの自動読み込み

### client.py - vSphere 接続クライアント
- **遅延初期化**: 初回ツール呼び出し時に接続確立
- **自動再接続**: セッション切れ時に最大 3 回リトライ（2 秒間隔）
- **エラー分類**:
  - `VSphereAuthenticationError` - 認証失敗
  - `VSphereSSLError` - SSL 証明書検証エラー
  - `VSphereConnectionError` - ホスト到達不能・接続拒否

### logging.py - 構造化ログ
- structlog + JSONRenderer による JSON 形式ログ
- **パスワード自動マスク**: `password`, `pwd`, `secret`, `token`, `credential` を含むキーを `***MASKED***` に自動置換
- ISO 8601 タイムスタンプ

### tools/_base.py - 共通デコレータ

#### require_confirm デコレータ
```python
@require_confirm(danger_level="high")
def some_dangerous_operation(...):
```
- `confirm=True` が渡されない場合、実行せずに確認プロンプトを返す
- 危険度レベル: `low`, `medium`, `high`, `critical`
- 関数シグネチャに `confirm: bool = False` を自動追加

#### handle_tool_errors デコレータ
```python
@handle_tool_errors
def some_tool(...):
```
- 例外をキャッチしてユーザー可読なエラーメッセージに変換
- 実行時間（`duration_ms`）を自動記録
- `VSphereToolError` と一般例外を区別してログ出力

### metrics.py - Prometheus メトリクス
- オプション依存（`pip install vsphere-mcp[metrics]`）
- `--metrics-port` で指定したポートに Prometheus 形式のメトリクスエンドポイントを公開
- ツール呼び出し回数、レイテンシ、エラー率などを計測

### rbac.py - RBAC ポリシーエンジン
- `VSPHERE_RBAC_POLICY` 環境変数で JSON ポリシーファイルを指定
- ツール単位でのアクセス許可/拒否を制御
- ポリシー未設定時は全ツールアクセス可能（後方互換）

### i18n.py - 国際化メッセージフレームワーク
- `VSPHERE_LANG` 環境変数で言語を切り替え（`en` / `ja`）
- 確認プロンプト、エラーメッセージ等のローカライズ

### utils/property_collector.py - 効率的プロパティ取得
- `ContainerView` + `TraversalSpec` + `PropertySpec` による一括取得
- vcsim との互換性を確保（managed object reference への直接プロパティアクセスが動作しない問題を回避）
- 必要なプロパティのみを指定して取得（全件 fetch を回避）

## ツールモジュール構成

| モジュール | ツール数 | 概要 |
|---|---|---|
| `inventory.py` | 18 | 読み取り専用ツール（list/get/search + test_connection）、スクリーンショット、ゲストIP待機 |
| `power.py` | 6 | 電源操作（on/off/shutdown/reboot/suspend/reset） |
| `snapshot.py` | 7 | スナップショット（create/revert/remove/remove_all/rename/revert_current/consolidate） |
| `migration.py` | 3 | vMotion / Storage vMotion / Relocate |
| `lifecycle.py` | 13 | VM 作成/クローン/リンククローン/テンプレート展開・変換/削除/登録、CBT、VM質問応答 |
| `resources.py` | 8 | CPU/メモリ変更、ディスク/NIC/CD追加、リソース割り当て、ホットアド、レイテンシ感度 |
| `vm_devices.py` | 26 | ディスク削除/拡張、NIC管理、コントローラ、extraConfig、ブートオプション、vTPM、セキュアブート、VBS |
| `host.py` | 11 | メンテナンスモード、シャットダウン、リブート、切断/再接続、クラスタ追加/移動 |
| `host_config.py` | 33 | vSwitch/VMkernel/ポートグループ/物理NIC、サービス、ファイアウォール、DNS/NTP、SSH、syslog、電源ポリシー、ロックダウン、証明書、時刻 |
| `networking.py` | 15 | 分散スイッチ/ポートグループ管理、ホスト追加/削除、ポート一覧、PVLAN、NICチーミング |
| `performance.py` | 7 | VM/ホスト/データストアパフォーマンス、過去データ、カスタムメトリクス |
| `events.py` | 8 | イベント一覧、アラーム一覧/定義、パフォーマンスカウンタ一覧、診断ログ取得/キー一覧 |
| `storage.py` | 21 | データストア管理、VMFS作成/拡張、iSCSI、データストアクラスタ、Storage DRS、SIOC |
| `batch.py` | 5 | 一括電源操作、一括スナップショット、一括情報取得、一括設定変更、一括マイグレーション |
| `guest.py` | 14 | ゲストコマンド実行、プロセス/ファイル管理、アップロード/ダウンロード、ネットワーク/OS情報 |
| `tags.py` | 7 | アノテーション、カスタム属性CRUD |
| `advanced_settings.py` | 4 | ESXi/vCenter 詳細設定の取得・変更 |
| `vcenter_admin.py` | 14 | ロール/権限管理、ライセンス情報、セッション/タスク管理 |
| `cluster_config.py` | 25 | HA/DRS設定、DRSルール/グループ、リソースプール、EVC、DPM、アドミッションコントロール |
| `folders.py` | 6 | フォルダ一覧/作成/削除/リネーム、エンティティ移動 |
| `datastore_browser.py` | 5 | データストアファイル参照/削除/コピー/移動/ディレクトリ作成 |
| `datacenter.py` | 3 | データセンター作成/削除/リネーム |
| `customization.py` | 6 | Linux/Windowsカスタマイズ仕様の管理・VM適用 |
| `alarm.py` | 4 | アラーム定義の作成/削除/リセット/有効無効 |
| `vsphere_tags.py` | 9 | vSphereタグカテゴリ・タグのCRUD、オブジェクトへの付与/解除 |
| `content_library.py` | 7 | コンテンツライブラリ管理、VMデプロイ、同期 |
| `vapp.py` | 4 | vApp一覧/電源操作/削除 |
| `scheduled_tasks.py` | 3 | スケジュールタスク一覧/削除/即時実行 |
| `host_profile.py` | 2 | ホストプロファイル一覧/コンプライアンス確認 |
| `license.py` | 4 | ライセンスキー追加/削除/割り当て管理 |
| `fault_tolerance.py` | 3 | VMフォールトトレランス有効化/無効化/情報取得 |
| **合計** | **301** | |

## 設計判断

### なぜ pyvmomi か
- VMware 公式 Python SDK で最も成熟している
- vcsim（govmomi 同梱の vCenter Simulator）と互換性がある
- 代替（vmware-aria-automation-sdk）は対象が Aria 寄り

### なぜ confirm をデコレータにするか
- ツールごとに確認ロジックを書くと冗長で確認漏れのリスク
- 危険度を引数で分類することで将来的な UI 拡張が可能

### なぜ PropertyCollector を使うか
- vcsim では ContainerView から取得した managed object reference に対して直接プロパティアクセスすると `AttributeError` が発生する
- PropertyCollector を使えば vcsim・実機の両方で動作する
- 大量 VM 環境でのパフォーマンスにも有利

### なぜ stdio をデフォルトとするか
- ローカル運用が主用途で最もシンプル
- ポート公開なし = セキュリティリスクが低い
- SSE/HTTP は複数クライアント共有時のオプション

### なぜ uv を推奨するか
- 高速インストール・再現性のあるロックファイル
- `uvx vsphere-mcp` で即実行可能
- PyPI 公開後のユーザー体験が良い

## 既知のリスク・課題

| リスク | 内容 | 対応方針 |
|---|---|---|
| vcsim と実機の挙動差 | vcsim は API モックであり一部挙動が実機と異なる | README に既知の差分を明記 |
| pyvmomi のメンテナンス | Broadcom 買収後の OSS 方針が不透明 | 必要に応じて govmomi バインディングへの移行を検討 |
| 商標・ライセンス | VMware ロゴや製品名の利用 | プロジェクト名を `vsphere-mcp` とし VMware 公式と区別 |
| 認証情報の漏洩 | ログ・エラーメッセージへの混入 | structlog プロセッサーでの自動マスク |
