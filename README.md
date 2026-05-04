# vsphere-mcp

[![CI](https://github.com/fukui-yuto/vsphere-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/fukui-yuto/vsphere-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

VMware vSphere / vCenter を AI コーディングツール（Claude Code、GitHub Copilot、Codex 等）から自然言語で操作するための MCP (Model Context Protocol) サーバーです。

> **注意**: 開発・テストはすべて [vcsim](https://github.com/vmware/govmomi/tree/main/vcsim)（vCenter Server Simulator）上で実施しています。商用 vSphere 環境への影響はありません。

## 機能一覧（全 204 ツール）

> 全ツールの詳細は [docs/TOOLS.md](docs/TOOLS.md) を参照してください。

### カテゴリ別サマリー

| カテゴリ | モジュール | 読み取り | 操作 | 合計 |
|---|---|---|---|---|
| インベントリ | `inventory.py` | 16 | - | 16 |
| 電源操作 | `power.py` | - | 6 | 6 |
| スナップショット | `snapshot.py` | - | 6 | 6 |
| マイグレーション | `migration.py` | - | 3 | 3 |
| ライフサイクル | `lifecycle.py` | 1 | 7 | 8 |
| リソース | `resources.py` | - | 4 | 4 |
| VM デバイス | `vm_devices.py` | 7 | 16 | 23 |
| ホスト管理 | `host.py` | - | 9 | 9 |
| ホスト設定 | `host_config.py` | 15 | 18 | 33 |
| ネットワ���ク | `networking.py` | 2 | 8 | 10 |
| パフォーマンス | `performance.py` | 2 | - | 2 |
| イベント・監視 | `events.py` | 8 | - | 8 |
| ストレージ | `storage.py` | 6 | 7 | 13 |
| バッチ操作 | `batch.py` | 1 | 2 | 3 |
| ゲスト操作 | `guest.py` | 3 | 5 | 8 |
| タグ・属性 | `tags.py` | 3 | 3 | 6 |
| 詳細設定 | `advanced_settings.py` | 2 | 2 | 4 |
| vCenter 管理 | `vcenter_admin.py` | 6 | 8 | 14 |
| クラスタ設定 | `cluster_config.py` | 5 | 12 | 17 |
| フォルダ | `folders.py` | 1 | 5 | 6 |
| DS ブラウザ | `datastore_browser.py` | 1 | 4 | 5 |
| **合計** | | **79** | **125** | **204** |

### 操作ツール（125 個・confirm 必須）

すべての操作ツールは `confirm=True` を指定しない限り実行されず、確認プロンプトを返します。

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
| **重大** | 永久的なデータ損失の可能性 | VM 削除、ホストシャットダウン/切断、データストアファイル削除 |

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
      inventory.py                # インベントリ情報取得（16 個）
      power.py                    # 電源操作（6 個）
      snapshot.py                 # スナップショット管理（6 個）
      migration.py                # vMotion / Storage vMotion（3 個）
      lifecycle.py                # VM ライフサイクル（8 個）
      resources.py                # リソース変更: CPU/メモリ/ディスク/NIC/CD（4 個）
      vm_devices.py               # VM デバイス管理（23 個）
      host.py                     # ホスト管理（9 個）
      host_config.py              # ホスト設定（33 個）
      networking.py               # ネットワーク設定��6 個）
      performance.py              # パフォーマンスメトリクス（2 個）
      events.py                   # イベント・監視（8 個）
      storage.py                  # ストレージ（13 個）
      batch.py                    # バッチ操作（3 個）
      guest.py                    # ゲスト OS 操作（8 個）
      tags.py                     # タグ・属性（6 個）
      advanced_settings.py        # 詳細設定（4 個）
      vcenter_admin.py            # vCenter 管理（14 個）
      cluster_config.py           # クラスタ設定（17 個）
      folders.py                  # フォルダ管理（6 個）
      datastore_browser.py        # データストアブラウザ（5 個）
    utils/
      property_collector.py       # PropertyCollector による効率的プロパティ取得
  tests/                          # vcsim 対象の統合テスト
  docs/
    ARCHITECTURE.md               # アーキテクチャ設計書
    DESIGN_DECISIONS.md           # 設計判断記録 (ADR)
    CONTRIBUTING.md               # コントリビュートガイド
    SECURITY.md                   # セキュリティポリシー
    CHANGELOG.md                  # 変更履歴
    TOOLS.md                      # 全 204 ツール詳細一覧
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
