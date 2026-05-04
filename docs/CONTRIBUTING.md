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
  metrics.py          # Prometheus メトリクス（オプション）
  rbac.py             # RBAC ポリシーエンジン
  i18n.py             # 国際化メッセージフレームワーク（en/ja）
  py.typed            # 型情報マーカー
  tools/
    _base.py              # require_confirm デコレータ、handle_tool_errors、共通ユーティリティ
    inventory.py          # インベントリ情報取得（list_*, get_*, search_*）- 16 個
    power.py              # 電源操作（on/off/shutdown/reboot/suspend/reset）- 6 個
    snapshot.py           # スナップショット管理（create/revert/remove/remove_all/rename/revert_current）- 6 個
    migration.py          # vMotion / Storage vMotion / Relocate - 3 個
    lifecycle.py          # VM ライフサイクル（作成/クローン/テンプレート/削除/登録）- 8 個
    resources.py          # VM 構成変更（set_vm_resources, add_disk, add_nic, add_vm_cd_drive）- 4 個
    vm_devices.py         # VM デバイス管理（ディスク/NIC/CD-DVD/ブート/extraConfig/ハードウェア等）- 23 個
    host.py               # ホスト管理（メンテナンスモード/シャットダウン/リブート/切断/追加/移動）- 9 個
    host_config.py        # ホスト設定（vSwitch/VMkernel/サービス/DNS/NTP/SSH/ファイアウォール等）- 33 個
    networking.py         # ネットワーク（分散スイッチ/ポートグループ設定・作成・更新・削除）- 10 個
    performance.py        # パフォーマンスメトリクス（VM/ホスト）- 2 個
    events.py             # イベント・監視（イベント/アラーム/診断ログ/vCenterログ）- 8 個
    storage.py            # ストレージ（データストア詳細/デバイス/マルチパス/再スキャン/NFS/メンテナンス）- 13 個
    batch.py              # バッチ操作（一括電源/スナップショット/VM 情報）- 3 個
    guest.py              # ゲスト OS 操作（プロセス/コマンド/ファイル/ディレクトリ/VMware Tools）- 8 個
    tags.py               # タグ・属性（アノテーション/カスタム属性）- 6 個
    advanced_settings.py  # ESXi/vCenter 詳細設定の取得・変更 - 4 個
    vcenter_admin.py      # vCenter 管理（ロール/権限/ライセンス/セッション/タスク/アラーム）- 14 個
    cluster_config.py     # クラスタ設定（HA/DRS/リソースプール/グループ/クラスタ作成・削除）- 17 個
    folders.py            # フォルダ管理（一覧/作成/削除/リネーム/VM 移動/エンティティ移動）- 6 個
    datastore_browser.py  # データストアブラウザ（ファイル参照/削除/コピー/移動/ディレクトリ作成）- 5 個
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
