# コントリビュートガイド

vsphere-mcp への貢献に興味を持っていただきありがとうございます。

## 開発環境のセットアップ

### 前提条件

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/)（推奨）または pip
- Docker（vcsim 用）

### セットアップ手順

1. リポジトリをクローン:

```bash
git clone https://github.com/fukui-yuto/vsphere-mcp.git
cd vsphere-mcp
```

2. vcsim（vCenter Server シミュレータ）を起動:

```bash
docker compose up -d
```

3. 仮想環境の作成と依存パッケージのインストール:

```bash
uv venv
uv pip install -e .
uv pip install pytest pytest-asyncio ruff mypy
```

4. テストを実行:

```bash
uv run pytest tests/ -v
```

## プロジェクト構成

```
src/vsphere_mcp/
  server.py           # MCP サーバーのエントリーポイント
  config.py           # 環境変数による設定管理
  client.py           # vSphere 接続クライアント（遅延初期化・自動再接続）
  logging.py          # 構造化ログ（structlog）
  tools/
    _base.py          # require_confirm デコレータ、handle_tool_errors
    inventory.py      # 情報取得ツール（list_*, get_*, search_*）
    power.py          # 電源操作（on/off/shutdown/reboot）
    snapshot.py       # スナップショット管理（create/revert/remove）
    migration.py      # vMotion（migrate_vm）
    provisioning.py   # VM プロビジョニング（clone, deploy_from_template）
    config_mgmt.py    # VM 構成変更（set_vm_resources, add_disk, add_nic）
    maintenance.py    # ホストメンテナンスモード（enter/exit）
    lifecycle.py      # VM 削除（delete_vm）
  utils/
    property_collector.py  # PropertyCollector による効率的なプロパティ取得
tests/
  conftest.py         # vcsim 接続フィクスチャ
  test_*.py           # テストモジュール
```

## 新しいツールの追加方法

1. カテゴリを決定: 情報取得（読み取り専用）か操作（破壊的）か。

2. **情報取得ツール**の場合は `tools/inventory.py` に追加:
   - プロパティ定数を定義（例: `MY_NEW_PROPS = [...]`）
   - フォーマッタ関数を作成（例: `_format_my_object(data)`）
   - `register_inventory_tools()` 内でツールを登録

3. **操作ツール**の場合は適切なモジュールに追加（または新規モジュールを作成）:
   - `@require_confirm(danger_level="...")` デコレータを使用
   - danger_level: `low`、`medium`、`high`、`critical` の4段階
   - VM 検索には `_find_vm_with_props()` を利用

4. 新規モジュールを作成した場合は `server.py` に登録。

5. `tests/test_*.py` にテストを作成。

## コードスタイル

- **フォーマッタ / リンター**: [ruff](https://docs.astral.sh/ruff/)
- **型チェック**: mypy（strict モード）
- 1行の最大文字数: 120文字

```bash
# リント
uv run ruff check src/ tests/

# フォーマット
uv run ruff format src/ tests/

# 型チェック
uv run mypy src/
```

## テストの方針

- すべてのテストは vcsim（vCenter シミュレータ）に対して実行（実際の vCenter は不要）
- vSphere オブジェクトの取得には PropertyCollector（`collect_properties`）を使用すること
- vcsim では ManagedObject の直接プロパティアクセスが動作しないため、必ず PropertyCollector を経由する
- テストクラスはモジュール単位でまとめ、共有フィクスチャを活用する

## コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に従ってください:

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメントのみの変更
- `test:` テストの追加・更新
- `refactor:` バグ修正でも機能追加でもないコード変更
- `chore:` ビルドプロセスや補助ツールの変更

## PR（プルリクエスト）手順

1. `main` ブランチからフィーチャーブランチを作成
2. テストを含む変更を実装
3. すべてのテストが通り、リントがクリーンであることを確認
4. わかりやすい説明を添えて PR を作成

## 問題報告方法

[GitHub Issues](https://github.com/fukui-yuto/vsphere-mcp/issues) で報告してください。以下の情報を含めてください:

- 再現手順
- 期待される動作と実際の動作
- Python バージョンと OS
- vcsim か実 vCenter か（実環境の場合はバージョンも記載）
