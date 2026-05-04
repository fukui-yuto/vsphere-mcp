# vsphere-mcp

[![CI](https://github.com/fukui-yuto/vsphere-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/fukui-yuto/vsphere-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

VMware vSphere / vCenter を AI コーディングツール（Claude Code、GitHub Copilot、Codex 等）から自然言語で操作するための MCP (Model Context Protocol) サーバーです。

> **注意**: 開発・テストはすべて [vcsim](https://github.com/vmware/govmomi/tree/main/vcsim)（vCenter Server Simulator）上で実施しています。商用 vSphere 環境への影響はありません。

## 機能一覧（全 657 ツール）

> 全ツールの詳細は [docs/TOOLS.md](docs/TOOLS.md) を参照してください。

### カテゴリ別サマリー

| カテゴリ | モジュール | 読み取り | 操作 | 合計 |
|---|---|---|---|---|
| インベントリ | `inventory.py` | 18 | - | 18 |
| 電源操作 | `power.py` | - | 6 | 6 |
| スナップショット | `snapshot.py` | - | 7 | 7 |
| マイグレーション | `migration.py` | - | 3 | 3 |
| ライフサイクル | `lifecycle.py` | 2 | 11 | 13 |
| リソース | `resources.py` | - | 8 | 8 |
| VM デバイス | `vm_devices.py` | 7 | 19 | 26 |
| ホスト管理 | `host.py` | - | 11 | 11 |
| ホスト設定 | `host_config.py` | 15 | 18 | 33 |
| ネットワーク | `networking.py` | 3 | 12 | 15 |
| パフォーマンス | `performance.py` | 7 | - | 7 |
| イベント・監視 | `events.py` | 8 | - | 8 |
| ストレージ | `storage.py` | 8 | 13 | 21 |
| バッチ操作 | `batch.py` | 1 | 4 | 5 |
| ゲスト操作 | `guest.py` | 5 | 9 | 14 |
| タグ・属性 | `tags.py` | 3 | 4 | 7 |
| 詳細設定 | `advanced_settings.py` | 2 | 2 | 4 |
| vCenter 管理 | `vcenter_admin.py` | 6 | 8 | 14 |
| クラスタ設定 | `cluster_config.py` | 7 | 18 | 25 |
| フォルダ | `folders.py` | 1 | 5 | 6 |
| DS ブラウザ | `datastore_browser.py` | 1 | 4 | 5 |
| データセンター | `datacenter.py` | - | 3 | 3 |
| カスタマイズ | `customization.py` | 2 | 4 | 6 |
| アラーム | `alarm.py` | - | 4 | 4 |
| vSphere タグ | `vsphere_tags.py` | 3 | 6 | 9 |
| コンテンツライブラリ | `content_library.py` | 2 | 5 | 7 |
| vApp | `vapp.py` | 1 | 3 | 4 |
| スケジュールタスク | `scheduled_tasks.py` | 1 | 2 | 3 |
| ホストプロファイル | `host_profile.py` | 2 | - | 2 |
| ライセンス | `license.py` | 1 | 3 | 4 |
| フォールトトレランス | `fault_tolerance.py` | 1 | 2 | 3 |
| ストレージポリシー | `storage_policy.py` | 4 | 3 | 7 |
| OVF/OVA | `ovf.py` | 2 | 3 | 5 |
| vSAN | `vsan.py` | 5 | 4 | 9 |
| vLCM パッチ管理 | `vlcm.py` | 5 | 3 | 8 |
| VM 暗号化 | `encryption.py` | 4 | 3 | 7 |
| 証明書管理 | `certificate.py` | 4 | 4 | 8 |
| NIOC | `nioc.py` | 2 | 3 | 5 |
| インスタントクローン他 | `instant_clone.py` | 1 | 4 | 5 |
| コンテンツライブラリ拡張 | `content_library_ext.py` | 3 | 5 | 8 |
| vCenter サービス | `vcenter_services.py` | 6 | 4 | 10 |
| PCI/vGPU | `pci_passthrough.py` | 5 | 4 | 9 |
| DVS 高度機能 | `dvs_advanced.py` | 3 | 3 | 6 |
| iSCSI 拡張 | `iscsi_config.py` | 1 | 4 | 5 |
| Tanzu | `tanzu.py` | 4 | 3 | 7 |
| VM モニタリング | `vm_monitoring.py` | 4 | 1 | 5 |
| データストア拡張 | `datastore_ext.py` | 1 | 1 | 2 |
| VM デバイス拡張 | `vm_devices_ext.py` | - | 12 | 12 |
| VM 操作拡張 | `vm_ops_ext.py` | - | 11 | 11 |
| クラスタ操作拡張 | `cluster_ops_ext.py` | - | 12 | 12 |
| ホスト操作拡張 | `host_ops_ext.py` | - | 18 | 18 |
| ネットワーク拡張 | `network_ext.py` | - | 13 | 13 |
| ストレージ操作拡張 | `storage_ops_ext.py` | - | 8 | 8 |
| セキュリティ・ID管理 | `security.py` | - | 10 | 10 |
| 監視・診断・拡張管理 | `diagnostics.py` | 11 | - | 11 |
| vApp 拡張 | `vapp_ext.py` | - | 6 | 6 |
| ゲスト操作拡張 | `guest_ext.py` | - | 8 | 8 |
| SDRS・コンピュートポリシー | `sdrs.py` | - | 6 | 6 |
| アプライアンスヘルス | `appliance_health.py` | 12 | - | 12 |
| アプライアンス更新・ネットワーク | `appliance_update.py` | - | 6 | 6 |
| 検索インデックス・その他 | `search_index.py` | 17 | - | 17 |
| ESXi アカウント管理 | `esxi_accounts.py` | - | 5 | 5 |
| 仮想ディスク管理 | `virtual_disk_mgr.py` | - | 10 | 10 |
| First Class Disk | `fcd.py` | - | 10 | 10 |
| VM メソッド拡張 | `vm_methods_ext.py` | - | 6 | 6 |
| ホストマネージャー拡張 | `host_mgr_ext.py` | - | 10 | 10 |
| vCenter REST 拡張 | `vcenter_rest_ext.py` | - | 11 | 11 |
| Trusted Infrastructure | `trusted_infra.py` | - | 7 | 7 |
| イベント・カスタマイズ拡張 | `event_ext.py` | - | 13 | 13 |
| VM ブート・Tools REST | `vm_boot_rest.py` | - | 4 | 4 |
| Namespace・互換性チェック | `namespace_compat.py` | 18 | - | 18 |
| **合計** | | **219** | **438** | **657** |

### 操作ツール（438 個・confirm 必須）

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
      inventory.py                # インベントリ情報取得（18 個）
      power.py                    # 電源操作（6 個）
      snapshot.py                 # スナップショット管理（7 個）
      migration.py                # vMotion / Storage vMotion（3 個）
      lifecycle.py                # VM ライフサイクル（13 個）
      resources.py                # リソース変更: CPU/メモリ/ディスク/NIC/CD（8 個）
      vm_devices.py               # VM デバイス管理（26 個）
      host.py                     # ホスト管理（11 個）
      host_config.py              # ホスト設定（33 個）
      networking.py               # ネットワーク設定（15 個）
      performance.py              # パフォーマンスメトリクス（7 個）
      events.py                   # イベント・監視（8 個）
      storage.py                  # ストレージ（21 個）
      batch.py                    # バッチ操作（5 個）
      guest.py                    # ゲスト OS 操作（14 個）
      tags.py                     # タグ・属性（7 個）
      advanced_settings.py        # 詳細設定（4 個）
      vcenter_admin.py            # vCenter 管理（14 個）
      cluster_config.py           # クラスタ設定（25 個）
      folders.py                  # フォルダ管理（6 個）
      datastore_browser.py        # データストアブラウザ（5 個）
      datacenter.py               # データセンター管理（3 個）
      customization.py            # カスタマイズ仕様（6 個）
      alarm.py                    # アラーム管理（4 個）
      vsphere_tags.py             # vSphere タグ REST API（9 個）
      content_library.py          # コンテンツライブラリ（7 個）
      vapp.py                     # vApp ライフサイクル（4 個）
      scheduled_tasks.py          # スケジュールタスク（3 個）
      host_profile.py             # ホストプロファイル（2 個）
      license.py                  # ライセンス管理（4 個）
      fault_tolerance.py          # フォールトトレランス（3 個）
      storage_policy.py           # ストレージポリシー（7 個）
      ovf.py                      # OVF/OVA デプロイ（5 個）
      vsan.py                     # vSAN 管理（9 個）
      vlcm.py                     # vLCM パッチ管理（8 個）
      encryption.py               # VM 暗号化（7 個）
      certificate.py              # 証明書管理（8 個）
      nioc.py                     # NIOC（5 個）
      instant_clone.py            # インスタントクローン他（5 個）
      content_library_ext.py      # コンテンツライブラリ拡張（8 個）
      vcenter_services.py         # vCenter サービス（10 個）
      pci_passthrough.py          # PCI/vGPU パススルー（9 個）
      dvs_advanced.py             # DVS 高度機能（6 個）
      iscsi_config.py             # iSCSI 拡張（5 個）
      tanzu.py                    # Tanzu（7 個）
      vm_monitoring.py            # VM モニタリング（5 個）
      datastore_ext.py            # データストア拡張（2 個）
      vm_devices_ext.py           # VM デバイス拡張（12 個）
      vm_ops_ext.py               # VM 操作拡張（11 個）
      cluster_ops_ext.py          # クラスタ操作拡張（12 個）
      host_ops_ext.py             # ホスト操作拡張（18 個）
      network_ext.py              # ネットワーク拡張（13 個）
      storage_ops_ext.py          # ストレージ操作拡張（8 個）
      security.py                 # セキュリティ・ID管理（10 個）
      diagnostics.py              # 監視・診断・拡張管理（11 個）
      vapp_ext.py                 # vApp 拡張（6 個）
      guest_ext.py                # ゲスト操作拡張（8 個）
      sdrs.py                     # SDRS・コンピュートポリシー（6 個）
      appliance_health.py         # アプライアンスヘルス（12 個）
      appliance_update.py         # アプライアンス更新・ネットワーク（6 個）
      search_index.py             # 検索インデックス・その他（17 個）
      esxi_accounts.py            # ESXi アカウント管理（5 個）
      virtual_disk_mgr.py         # 仮想ディスク管理（10 個）
      fcd.py                      # First Class Disk（10 個）
      vm_methods_ext.py           # VM メソッド拡張（6 個）
      host_mgr_ext.py             # ホストマネージャー拡張（10 個）
      vcenter_rest_ext.py         # vCenter REST 拡張（11 個）
      trusted_infra.py            # Trusted Infrastructure（7 個）
      event_ext.py                # イベント・カスタマイズ拡張（13 個）
      vm_boot_rest.py             # VM ブート・Tools REST（4 個）
      namespace_compat.py         # Namespace・互換性チェック（18 個）
    utils/
      property_collector.py       # PropertyCollector による効率的プロパティ取得
  tests/                          # vcsim 対象の統合テスト
  docs/
    ARCHITECTURE.md               # アーキテクチャ設計書
    DESIGN_DECISIONS.md           # 設計判断記録 (ADR)
    CONTRIBUTING.md               # コントリビュートガイド
    SECURITY.md                   # セキュリティポリシー
    CHANGELOG.md                  # 変更履歴
    TOOLS.md                      # 全 657 ツール詳細一覧
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
