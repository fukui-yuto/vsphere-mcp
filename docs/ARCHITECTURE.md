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
- stdio トランスポート（デフォルト）
- 全ツールモジュールの登録

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

### utils/property_collector.py - 効率的プロパティ取得
- `ContainerView` + `TraversalSpec` + `PropertySpec` による一括取得
- vcsim との互換性を確保（managed object reference への直接プロパティアクセスが動作しない問題を回避）
- 必要なプロパティのみを指定して取得（全件 fetch を回避）

## ツールモジュール構成

| モジュール | ツール数 | 概要 |
|---|---|---|
| `inventory.py` | 12 | 読み取り専用ツール（list/get/search + test_connection）、ページネーション対応 |
| `power.py` | 4 | 電源操作（on/off/shutdown/reboot） |
| `snapshot.py` | 3 | スナップショット（create/revert/remove） |
| `migration.py` | 1 | vMotion |
| `lifecycle.py` | 3 | VM 削除/クローン/テンプレート展開 |
| `resources.py` | 3 | CPU/メモリ変更、ディスク追加、NIC 追加 |
| `host.py` | 2 | ESXi メンテナンスモード（enter/exit） |
| **合計** | **28** | |

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
