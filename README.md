# vsphere-mcp

[![CI](https://github.com/fukui-yuto/vsphere-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/fukui-yuto/vsphere-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

VMware vSphere / vCenter を AI コーディングツール（Claude Code、GitHub Copilot、Codex 等）から自然言語で操作するための MCP (Model Context Protocol) サーバーです。

> **注意**: 開発・テストはすべて [vcsim](https://github.com/vmware/govmomi/tree/main/vcsim)（vCenter Server Simulator）上で実施しています。商用 vSphere 環境への影響はありません。

## 機能一覧

### 情報取得ツール（28 個・読み取り専用・confirm 不要）

| ツール名 | 概要 |
|---|---|
| `test_connection` | vSphere 接続テスト・サーバー情報取得 |
| `list_vms` | VM 一覧取得（ホスト/クラスターフィルター、ページネーション対応） |
| `get_vm_info` | VM 詳細情報取得（CPU、メモリ、ディスク、NIC、ストレージ、VMware Tools） |
| `list_hosts` | ESXi ホスト一覧取得（クラスターフィルター） |
| `get_host_info` | ESXi ホスト詳細情報取得 |
| `list_datacenters` | データセンター一覧取得 |
| `list_clusters` | クラスター一覧取得（データセンターフィルター） |
| `list_datastores` | データストア一覧取得（容量/使用量付き） |
| `list_networks` | ネットワーク（ポートグループ）一覧取得 |
| `list_snapshots` | VM スナップショット一覧取得（ツリー構造） |
| `get_cluster_health` | クラスター健全性サマリー（ホスト詳細付き） |
| `search_vms` | VM 名で検索（大文字小文字区別なし） |
| `list_resource_pools` | リソースプール一覧取得（CPU/メモリ割り当て） |
| `list_distributed_switches` | 分散仮想スイッチ一覧取得 |
| `list_distributed_portgroups` | 分散ポートグループ一覧取得 |
| `get_vm_performance` | VM パフォーマンスメトリクス取得 |
| `get_host_performance` | ホストパフォーマンスメトリクス取得 |
| `list_recent_events` | vCenter イベント一覧取得 |
| `list_alarms` | トリガー済みアラーム一覧取得 |
| `get_datastore_info` | データストア詳細情報取得 |
| `get_storage_summary` | ストレージ全体サマリー取得 |
| `list_guest_processes` | ゲスト OS プロセス一覧取得 |
| `get_vm_annotation` | VM アノテーション取得 |
| `get_custom_attributes` | カスタム属性定義一覧取得 |
| `get_esxi_advanced_settings` | ESXi 詳細設定取得 |
| `get_vcenter_advanced_settings` | vCenter 詳細設定取得 |

### 操作ツール（22 個・confirm 必須）

すべての操作ツールは `confirm=True` を指定しない限り実行されず、確認プロンプトを返します。

| ツール名 | 概要 | 危険度 |
|---|---|---|
| `power_on_vm` | VM 起動 | 低 |
| `power_off_vm` | VM 強制電源 OFF | 中 |
| `shutdown_vm` | ゲスト OS シャットダウン | 中 |
| `reboot_vm` | ゲスト OS 再起動 | 中 |
| `create_snapshot` | スナップショット作成 | 中 |
| `set_vm_resources` | CPU/メモリ変更 | 中 |
| `add_disk` | ディスク追加 | 中 |
| `add_nic` | NIC 追加 | 中 |
| `set_vm_annotation` | VM アノテーション設定 | 低 |
| `revert_snapshot` | スナップショット復元 | 高 |
| `remove_snapshot` | スナップショット削除 | 高 |
| `migrate_vm` | vMotion（ホスト間移行） | 高 |
| `clone_vm` | VM クローン作成 | 高 |
| `deploy_from_template` | テンプレートから VM 展開 | 高 |
| `enter_maintenance_mode` | ESXi メンテナンスモード開始 | 高 |
| `exit_maintenance_mode` | ESXi メンテナンスモード終了 | 高 |
| `batch_power_operation` | 複数 VM の一括電源操作 | 高 |
| `batch_create_snapshots` | 複数 VM の一括スナップショット作成 | 高 |
| `execute_guest_command` | ゲスト OS コマンド実行 | 高 |
| `set_esxi_advanced_setting` | ESXi 詳細設定変更 | 高 |
| `set_vcenter_advanced_setting` | vCenter 詳細設定変更 | 高 |
| `delete_vm` | VM 完全削除 | **最高** |

## クイックスタート

### 前提条件

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/)（推奨）
- Docker（vcsim を使ったローカル開発用）

### 1. vcsim の起動（開発用）

```bash
docker compose up -d
```

ポート 8989 で vCenter Server Simulator が起動し、データセンター・クラスター・ホスト・VM・データストアが事前作成されます。

### 2. インストール

```bash
# ソースから
git clone https://github.com/fukui-yuto/vsphere-mcp.git
cd vsphere-mcp
uv venv
uv pip install -e .
```

### 3. AI ツールへの登録

#### Claude Code

`.claude/settings.json` または `.mcp.json` に以下を追加します。

**ローカル開発（vcsim）**

```json
{
  "mcpServers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "localhost",
        "VSPHERE_PORT": "8989",
        "VSPHERE_USER": "user",
        "VSPHERE_PASSWORD": "pass",
        "VSPHERE_IGNORE_SSL": "true"
      }
    }
  }
}
```

**本番 vCenter**

```json
{
  "mcpServers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "vcenter.example.com",
        "VSPHERE_PORT": "443",
        "VSPHERE_USER": "administrator@vsphere.local",
        "VSPHERE_PASSWORD": "your-password"
      }
    }
  }
}
```

**パスワードファイル（本番推奨）**

```json
{
  "mcpServers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "vcenter.example.com",
        "VSPHERE_PORT": "443",
        "VSPHERE_USER": "administrator@vsphere.local",
        "VSPHERE_PASSWORD_FILE": "/run/secrets/vsphere_password"
      }
    }
  }
}
```

#### GitHub Copilot（VS Code）

プロジェクトルートに `.vscode/mcp.json` を作成します。

**ローカル開発（vcsim）**

```json
{
  "servers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "localhost",
        "VSPHERE_PORT": "8989",
        "VSPHERE_USER": "user",
        "VSPHERE_PASSWORD": "pass",
        "VSPHERE_IGNORE_SSL": "true"
      }
    }
  }
}
```

**本番 vCenter**

```json
{
  "servers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "vcenter.example.com",
        "VSPHERE_PORT": "443",
        "VSPHERE_USER": "administrator@vsphere.local",
        "VSPHERE_PASSWORD": "your-password"
      }
    }
  }
}
```

> **ヒント**: VS Code のユーザー設定（`settings.json`）の `mcp.servers` に記述することも可能です。

#### OpenAI Codex CLI

プロジェクトルートに `codex.json` を作成します。

**ローカル開発（vcsim）**

```json
{
  "mcpServers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "localhost",
        "VSPHERE_PORT": "8989",
        "VSPHERE_USER": "user",
        "VSPHERE_PASSWORD": "pass",
        "VSPHERE_IGNORE_SSL": "true"
      }
    }
  }
}
```

**本番 vCenter**

```json
{
  "mcpServers": {
    "vsphere-mcp": {
      "command": "uv",
      "args": ["run", "vsphere-mcp"],
      "env": {
        "VSPHERE_HOST": "vcenter.example.com",
        "VSPHERE_PORT": "443",
        "VSPHERE_USER": "administrator@vsphere.local",
        "VSPHERE_PASSWORD": "your-password"
      }
    }
  }
}
```

### 4. 利用例

登録後、自然言語で操作できます:

```
> クラスター内の全 VM を表示して

> VM "web-server-01" のステータスを確認して

> VM "dev-test-01" を起動して（confirm=True）

> 全データストアの空き容量を一覧表示して

> "db-server" のスナップショットを "before-upgrade" という名前で作成して

> "web-01" を "web-01-staging" としてクローンして

> "app-server" に 50GB のディスクを追加して
```

## 環境変数

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `VSPHERE_HOST` | `localhost` | vCenter/ESXi のホスト名または IP |
| `VSPHERE_PORT` | `443` | vSphere API ポート |
| `VSPHERE_USER` | `administrator@vsphere.local` | ユーザー名 |
| `VSPHERE_PASSWORD` | (空) | パスワード |
| `VSPHERE_PASSWORD_FILE` | (空) | パスワードファイルのパス（`VSPHERE_PASSWORD` の代替） |
| `VSPHERE_IGNORE_SSL` | `false` | SSL 証明書検証をスキップ |
| `VSPHERE_RBAC_POLICY` | (空) | RBAC ポリシー JSON ファイルのパス |
| `VSPHERE_LANG` | `en` | メッセージ言語（`en` / `ja`） |

### SSL 設定

SSL 証明書の検証は**デフォルトで有効**です。自己署名証明書や開発環境の場合:

```bash
export VSPHERE_IGNORE_SSL=true
```

> **警告**: 本番環境では SSL 検証を無効化しないでください。

## 安全設計

### 確認システム

すべての破壊的操作は 2 段階の確認パターンを使用します:

1. **1 回目の呼び出し**（`confirm=True` なし）: 危険度付きのプレビューを返す
2. **2 回目の呼び出し**（`confirm=True` あり）: 実際に操作を実行

```
# 1 回目 - 確認プロンプトを返す
power_off_vm(vm_name="web-01")
# -> {"status": "confirmation_required", "danger_level": "medium", ...}

# 2 回目 - 実行
power_off_vm(vm_name="web-01", confirm=True)
# -> {"status": "success", "vm_name": "web-01", "operation": "power_off"}
```

### 危険度レベル

| レベル | 説明 | 例 |
|---|---|---|
| **低** | 容易に取り消し可能 | VM 起動、アノテーション設定 |
| **中** | 一時的な影響あり | 電源 OFF、シャットダウン、再起動、スナップショット作成、リソース変更 |
| **高** | 大きな影響・取り消し困難 | スナップショット復元/削除、vMotion、クローン、テンプレート展開、メンテナンスモード、一括操作、ゲストコマンド実行、詳細設定変更 |
| **最高** | 永久的なデータ損失の可能性 | VM 削除 |

### ログ

すべての操作は構造化 JSON 形式でログ記録されます:

```json
{"event": "power_off_vm", "vm_name": "web-01", "level": "info", "timestamp": "2025-05-04T12:00:00Z", "duration_ms": 1234.5}
```

認証情報はログに**一切含まれません**（自動マスク処理）。

## エラーハンドリング

接続エラーは診断しやすいように型で分類されます:

| エラー型 | 原因 | メッセージ例 |
|---|---|---|
| `VSphereAuthenticationError` | ユーザー名/パスワードが不正 | `Authentication failed for user 'admin' on vcenter:443` |
| `VSphereSSLError` | SSL 証明書検証失敗 | `SSL certificate verification failed ... Set VSPHERE_IGNORE_SSL=true` |
| `VSphereConnectionError` | ホスト到達不能・接続拒否 | `Cannot reach vSphere at vcenter:443` |

クライアントは一時的な接続障害時に自動リトライします（最大 3 回、2 秒間隔）。

## 開発

### テスト実行（vcsim が必要）

```bash
docker compose up -d
uv run pytest tests/ -v
```

### リント・フォーマット

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### プロジェクト構成

```
vsphere-mcp/
  pyproject.toml
  docker-compose.yml              # vcsim 起動用
  src/vsphere_mcp/
    server.py                     # MCP サーバーエントリポイント
    config.py                     # 環境変数による設定管理
    client.py                     # vSphere 接続（遅延初期化・自動再接続）
    logging.py                    # 構造化ログ（パスワードマスク付き）
    metrics.py                    # Prometheus メトリクス（オプション）
    rbac.py                       # RBAC ポリシーエンジン
    i18n.py                       # 国際化メッセージフレームワーク（en/ja）
    py.typed                      # 型情報マーカー
    tools/
      _base.py                    # require_confirm / handle_tool_errors デコレータ
      inventory.py                # 情報取得ツール（15 個）
      power.py                    # 電源操作（4 個）
      snapshot.py                 # スナップショット管理（3 個）
      migration.py                # vMotion（1 個）
      lifecycle.py                # VM クローン/展開/削除（3 個）
      resources.py                # リソース変更: CPU/メモリ/ディスク/NIC（3 個）
      host.py                     # ホストメンテナンスモード（2 個）
      performance.py              # パフォーマンスメトリクス（2 個）
      events.py                   # イベント・アラーム（2 個）
      storage.py                  # ストレージ詳細（2 個）
      batch.py                    # 一括操作（2 個）
      guest.py                    # ゲスト OS 操作（2 個）
      tags.py                     # アノテーション・カスタム属性（3 個）
      advanced_settings.py        # 詳細設定（4 個）
    utils/
      property_collector.py       # PropertyCollector による効率的プロパティ取得
  tests/                          # vcsim 対象の統合テスト
  docs/
    ARCHITECTURE.md               # アーキテクチャ設計書
    DESIGN_DECISIONS.md           # 設計判断記録 (ADR)
    CONTRIBUTING.md               # コントリビュートガイド
    SECURITY.md                   # セキュリティポリシー
    CHANGELOG.md                  # 変更履歴
  .github/
    workflows/ci.yml              # GitHub Actions CI
    dependabot.yml                # Dependabot 設定（pip / GitHub Actions）
```

## 高度な機能

### SSE トランスポート

複数クライアントから同一サーバーを共有する場合、SSE トランスポートを使用できます:

```bash
vsphere-mcp --transport sse --port 8080
```

### Prometheus メトリクス

オプションの依存パッケージをインストールすることで、Prometheus 形式のメトリクスエンドポイントを公開できます:

```bash
pip install vsphere-mcp[metrics]
vsphere-mcp --metrics-port 9090
```

### RBAC（ロールベースアクセス制御）

`VSPHERE_RBAC_POLICY` 環境変数にポリシー JSON ファイルのパスを指定することで、ツールごとのアクセス制御を設定できます:

```bash
export VSPHERE_RBAC_POLICY=/path/to/policy.json
```

### 国際化（i18n）

`VSPHERE_LANG` 環境変数でメッセージ言語を切り替えられます（デフォルト: `en`）:

```bash
export VSPHERE_LANG=ja
```

## アーキテクチャ

```
Claude Code
    |  stdio（デフォルト）または HTTP/SSE
    v
vsphere-mcp サーバー（Python, FastMCP）
    |  pyVmomi（HTTPS）
    v
vCenter Server（本番）または vcsim（開発）
```

- **トランスポート**: stdio（デフォルト、ローカル運用に最適）または SSE（複数クライアント共有用）
- **接続**: 初回ツール呼び出し時に遅延初期化、セッション切れ時に自動再接続
- **プロパティ取得**: PropertyCollector による効率的な一括クエリ
- **安全装置**: `require_confirm` デコレータによる危険度別の確認システム
- **エラーハンドリング**: 型付き例外（`VSphereAuthenticationError`, `VSphereSSLError`, `VSphereConnectionError`）

## 既知の制限事項

- **vcsim と実機の差異**: vcsim と本番 vCenter で一部 API の挙動が異なります。詳細は [vcsim ドキュメント](https://github.com/vmware/govmomi/tree/main/vcsim)を参照してください。
- **ゲスト操作**: `shutdown_vm`、`reboot_vm`、`execute_guest_command`、`list_guest_processes` はゲスト OS に VMware Tools がインストールされている必要があります。
- **vMotion**: 本番環境では互換性のあるホスト、共有ストレージ、適切なネットワーク構成が必要です。

## ライセンス

[Apache License 2.0](LICENSE)

## コントリビュート

開発環境のセットアップと貢献の手順は [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) を参照してください。

## セキュリティ

セキュリティポリシーと脆弱性の報告方法は [docs/SECURITY.md](docs/SECURITY.md) を参照してください。

## 変更履歴

リリース履歴は [docs/CHANGELOG.md](docs/CHANGELOG.md) を参照してください。

## 設計ドキュメント

- [アーキテクチャ設計書](docs/ARCHITECTURE.md)
- [設計判断記録 (ADR)](docs/DESIGN_DECISIONS.md)
