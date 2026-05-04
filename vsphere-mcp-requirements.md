# vsphere-mcp 要件定義書

## 1. プロジェクト概要

### 1.1 目的

VMware vSphere / vCenter を Claude Code から自然言語で操作するための MCP (Model Context Protocol) サーバーを開発する。既存の `proxmox-lab-mcp` の設計思想を踏襲し、安全性・拡張性・運用性を担保する。

### 1.2 想定ユースケース

- Claude Code から自然言語で vCenter の状態確認・操作を実施
- 仮想化基盤運用者の日常作業(VM 一覧、ホスト健全性確認、スナップショット管理など)を効率化
- 危険操作(電源 OFF、削除、vMotion など)は confirm 必須で誤操作を防止

### 1.3 OSS として公開

- ライセンス: Apache License 2.0
- リポジトリ名: `vsphere-mcp`(VMware 商標を避けるため `vmware-mcp` は使用しない)
- README に「テストは vcsim 上で実施」と明記し、商用環境への影響がないことを示す

---

## 2. 技術スタック

| カテゴリ | 採用技術 | 備考 |
|---|---|---|
| 言語 | Python 3.11+ | メイン言語 |
| MCP SDK | `mcp` (公式 Python SDK) | stdio / SSE 両対応 |
| vSphere SDK | `pyvmomi` | VMware 公式 Python SDK |
| 接続補助 | `pyvim` | SmartConnect ヘルパー |
| 設定管理 | `pydantic-settings` | 環境変数ベースの設定 |
| ロギング | `structlog` | 構造化ログ |
| テスト | `pytest`, `pytest-asyncio` | |
| CI | GitHub Actions + vcsim Docker | |
| Lint/Format | `ruff`, `mypy` | |
| パッケージ管理 | `uv` または `poetry` | uv を推奨 |

---

## 3. 開発環境

### 3.1 vcsim を利用したローカル開発

実機の vCenter を持たないため、開発・テストは **vcsim** (govmomi 同梱の vCenter Server Simulator) で行う。

```bash
# vcsim 起動
docker run --rm -p 8989:8989 vmware/vcsim -l 0.0.0.0:8989

# 接続情報
host: localhost
port: 8989
user: user
pass: pass
ignore_ssl: true
```

vcsim はデフォルトでデータセンター・クラスター・ホスト・VM・データストアが事前定義されており、pyVmomi から実 vCenter と同じ API で接続可能。

### 3.2 実機検証(必要時のみ)

- VMware Hands-on Labs (HOL) を参照用に利用(セッション数時間制限あり、ローカルからの API 直接接続は不可)
- 必要に応じて Workstation Pro + ネステッド ESXi 環境を構築

---

## 4. 機能要件

### 4.1 提供する MCP Tool 一覧

#### 4.1.1 情報取得系(読み取り専用・confirm 不要)

| Tool 名 | 概要 | 主な引数 |
|---|---|---|
| `list_datacenters` | データセンター一覧取得 | なし |
| `list_clusters` | クラスター一覧取得 | datacenter (任意) |
| `list_hosts` | ESXi ホスト一覧取得 | cluster (任意) |
| `list_vms` | VM 一覧取得 | host / cluster / folder (任意), filter |
| `get_vm_info` | 特定 VM の詳細取得 | vm_name または vm_id |
| `get_host_info` | 特定 ESXi ホストの詳細取得 | host_name |
| `list_datastores` | データストア一覧取得 | host / cluster (任意) |
| `list_networks` | ネットワーク(ポートグループ)一覧取得 | host / cluster (任意) |
| `list_snapshots` | VM のスナップショット一覧取得 | vm_name |
| `get_cluster_health` | クラスター健全性サマリー取得 | cluster_name |
| `search_vms` | VM をキーワード検索 | query, fields |

#### 4.1.2 操作系(confirm 必須)

| Tool 名 | 概要 | 主な引数 | 危険度 |
|---|---|---|---|
| `power_on_vm` | VM 起動 | vm_name | 低 |
| `power_off_vm` | VM 強制電源 OFF | vm_name | 中 |
| `shutdown_vm` | VM ゲスト OS シャットダウン | vm_name | 中 |
| `reboot_vm` | VM 再起動 | vm_name | 中 |
| `create_snapshot` | スナップショット作成 | vm_name, name, description, memory, quiesce | 中 |
| `revert_snapshot` | スナップショット復元 | vm_name, snapshot_name | 高 |
| `remove_snapshot` | スナップショット削除 | vm_name, snapshot_name | 高 |
| `migrate_vm` | vMotion 実施 | vm_name, target_host | 高 |
| `delete_vm` | VM 削除 | vm_name | **最高** |

> **confirm 必須**:操作系 Tool はすべて、引数に `confirm: bool = False` を持ち、`True` でない限り実行しない。Claude Code 側で「本当に実行しますか?」と人間に確認させる設計。

#### 4.1.3 (将来拡張)

- `clone_vm` / `deploy_from_template`
- `add_disk` / `resize_disk`
- `add_nic` / `change_network`
- `set_vm_resources` (CPU / メモリ変更)
- `enter_maintenance_mode` / `exit_maintenance_mode`(ESXi ホスト)

---

## 5. 非機能要件

### 5.1 安全性

- **破壊的操作はすべて confirm 必須**(引数 `confirm=True` 明示が必要)
- 接続情報・認証情報は環境変数または設定ファイルから読み込み、コード/ログに出力しない
- SSL 証明書検証はデフォルト有効、自己署名対応のための明示的フラグを用意

### 5.2 認証・接続

- 接続情報は環境変数で管理:
  - `VSPHERE_HOST`
  - `VSPHERE_USER`
  - `VSPHERE_PASSWORD`(または `VSPHERE_PASSWORD_FILE`)
  - `VSPHERE_PORT`(デフォルト 443)
  - `VSPHERE_IGNORE_SSL`(デフォルト false)
- 接続は遅延初期化(初回 Tool 呼び出し時に確立)
- セッションの自動再接続・タイムアウトハンドリング

### 5.3 ロギング・監査

- すべての Tool 呼び出しを構造化ログに記録(JSON 形式)
- ログ項目: timestamp, tool_name, arguments(機微情報除外), user, result_status, duration_ms
- 操作系 Tool の実行は別レベル(INFO 以上)で必ず記録

### 5.4 エラーハンドリング

- vSphere API のエラーをユーザー可読なメッセージに変換
- 接続失敗時は明確なエラー(認証失敗 / ホスト到達不能 / 証明書エラー等を区別)
- 引数バリデーションは pydantic で型レベルから担保

### 5.5 パフォーマンス

- 一覧取得系は PropertyCollector で必要プロパティのみ取得(全件 fetch を避ける)
- 大量 VM 環境(1000 台以上)を想定し、ページング・件数制限引数を用意

---

## 6. アーキテクチャ

### 6.1 ディレクトリ構成

```
vsphere-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── docker-compose.yml          # vcsim 起動用
├── .github/
│   └── workflows/
│       └── ci.yml              # vcsim 起動 → pytest
├── src/
│   └── vsphere_mcp/
│       ├── __init__.py
│       ├── server.py           # MCP サーバーエントリポイント
│       ├── config.py           # 設定(pydantic-settings)
│       ├── client.py           # vSphere 接続クライアント
│       ├── logging.py          # 構造化ログ設定
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── _base.py        # Tool 基底クラス、confirm デコレータ
│       │   ├── inventory.py    # list_*, get_*
│       │   ├── power.py        # power_on/off, shutdown, reboot
│       │   ├── snapshot.py     # create/revert/remove_snapshot
│       │   ├── migration.py    # migrate_vm
│       │   └── lifecycle.py    # delete_vm, clone_vm
│       └── utils/
│           ├── __init__.py
│           └── property_collector.py
└── tests/
    ├── conftest.py             # vcsim フィクスチャ
    ├── test_inventory.py
    ├── test_power.py
    └── test_snapshot.py
```

### 6.2 接続フロー

```
Claude Code
    │  stdio または HTTP/SSE
    ▼
vsphere-mcp server (Python)
    │  pyvmomi (HTTPS)
    ▼
vCenter Server (本番) または vcsim (開発)
```

### 6.3 confirm デコレータ設計案

```python
def require_confirm(danger_level: str = "medium"):
    """操作系 Tool に付与するデコレータ。confirm=True でなければ実行を拒否。"""
    def decorator(func):
        async def wrapper(*args, confirm: bool = False, **kwargs):
            if not confirm:
                return {
                    "status": "confirmation_required",
                    "danger_level": danger_level,
                    "tool": func.__name__,
                    "message": f"This is a {danger_level}-risk operation. Re-call with confirm=True to execute.",
                    "preview": _build_preview(func, args, kwargs),
                }
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 7. テスト戦略

### 7.1 ユニットテスト

- 各 Tool 関数を pytest で個別テスト
- vcsim を `conftest.py` で fixture 化(セッションスコープ)
- カバレッジ目標: 80% 以上

### 7.2 統合テスト

- GitHub Actions 上で vcsim Docker を起動 → MCP サーバー起動 → 全 Tool を順次実行
- Tool の組み合わせシナリオ(VM 起動 → スナップショット → 復元 → 削除)を E2E でテスト

### 7.3 手動検証

- HOL で本物の vCenter UI と挙動を比較(年数回)
- 可能であれば業務環境で読み取り系のみ実行(許可取得後)

---

## 8. ドキュメント

### 8.1 README に含める内容

- プロジェクト概要・スクリーンショット(Claude Code との連携例)
- インストール手順(`uv pip install vsphere-mcp` または `pipx`)
- Claude Code への登録コマンド:
  ```
  claude mcp add --transport stdio vsphere-mcp \
    --command "uvx" --args "vsphere-mcp"
  ```
- 環境変数一覧
- vcsim を使った動作確認手順
- 提供 Tool 一覧と使用例
- セキュリティ上の注意事項(本番環境利用時)
- コントリビュートガイド

### 8.2 別ファイル

- `CONTRIBUTING.md`
- `SECURITY.md`(脆弱性報告手順)
- `CHANGELOG.md`(Keep a Changelog 形式)

---

## 9. 開発ロードマップ

### Phase 1: MVP(最低限動くもの)

- [ ] プロジェクト雛形作成(`pyproject.toml`, ディレクトリ構成)
- [ ] vcsim を docker-compose で起動できる状態
- [ ] 接続クライアント(`client.py`)実装
- [ ] `list_vms` / `get_vm_info` / `list_hosts` の 3 Tool だけ実装
- [ ] Claude Code から接続して動作確認
- [ ] README 初版

### Phase 2: 情報取得系の拡充

- [ ] 残りの `list_*` / `get_*` Tool を実装
- [ ] PropertyCollector による高速化
- [ ] 構造化ログ実装
- [ ] ユニットテスト整備

### Phase 3: 操作系 Tool

- [ ] confirm デコレータ実装
- [ ] 電源操作・スナップショット操作・vMotion 実装
- [ ] 操作系の統合テスト
- [ ] CI(GitHub Actions + vcsim)整備

### Phase 4: 公開準備

- [ ] PyPI 公開
- [ ] ドキュメントサイト(MkDocs Material 等)作成
- [ ] サンプル動画・ブログ記事執筆
- [ ] X / Qiita / Zenn でのアナウンス

### Phase 5: 拡張

- [ ] クローン・テンプレート展開・リソース変更等
- [ ] DRS/HA 関連の問い合わせ Tool
- [ ] vSAN / NSX への対応検討

---

## 10. 設計判断メモ

### 10.1 なぜ pyvmomi か

- VMware 公式 Python SDK で最も枯れている
- 代替として `vmware-aria-automation-sdk` があるが、対象が Aria 寄り
- govmomi (Go) に比べると遅いが、MCP サーバー用途では十分

### 10.2 なぜ confirm をデコレータにするか

- Tool ごとに分岐ロジックを書くと冗長で、確認漏れのリスク
- 危険度を引数で分類することで、将来 UI 側で「中以上は二段階確認」等の拡張が可能

### 10.3 なぜ stdio をデフォルトとするか

- ローカル運用が主用途で、stdio が最もシンプル
- SSE / HTTP は複数クライアント共有や監査要件が出た場合のオプション

### 10.4 なぜ uv を推奨するか

- 高速、再現性のあるロックファイル、`uvx` での実行が容易
- ユーザーが `uvx vsphere-mcp` だけで起動できるのが理想

---

## 11. 既知のリスク・課題

| リスク | 内容 | 対応方針 |
|---|---|---|
| vcsim と実機の挙動差 | vcsim は API モックなので、一部挙動が実機と異なる | HOL で定期的に挙動確認、README に既知の差分を明記 |
| pyvmomi のメンテナンス | Broadcom 買収後の OSS 方針が不透明 | 必要に応じて govmomi バインディングへの移行を検討 |
| 商標・ライセンス | VMware ロゴや製品名の利用 | プロジェクト名・ロゴを VMware 公式と区別、README で明示 |
| 認証情報の漏洩 | ログ・エラーメッセージへの混入 | ログフィルタ実装、テストで検証 |

---

## 12. 参考リンク

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [pyvmomi GitHub](https://github.com/vmware/pyvmomi)
- [vcsim (govmomi 内)](https://github.com/vmware/govmomi/tree/main/vcsim)
- [VMware Hands-on Labs](https://www.vmware.com/resources/hands-on-labs)
- [proxmox-lab-mcp](https://fukui-yuto.github.io/homelab.html)(自身の既存作)

---

## 13. Claude Code への引き継ぎ事項

このドキュメントを Claude Code で開いた後、以下の順で進めることを推奨:

1. **Phase 1 から着手**:まず雛形 + `list_vms` だけが動く状態を最速で作る
2. **vcsim を docker-compose.yml で起動可能にする**:`docker compose up` 一発で開発開始できる状態を最初に整える
3. **テスト駆動で進める**:vcsim 前提のため、ユニットテストが書きやすい。Tool 追加時は必ずテストとセット
4. **confirm デコレータは Phase 3 冒頭で先に実装**:後付けすると全 Tool の改修が発生する
5. **README は Phase 1 完了時点で初版を書く**:後回しにすると書けなくなる

開発中に悩んだら、以下の優先順位で判断:

1. 安全性(誤操作防止)
2. 実機 vSphere との API 互換性
3. コードの読みやすさ
4. パフォーマンス
