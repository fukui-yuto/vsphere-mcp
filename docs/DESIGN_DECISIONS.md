# 設計判断記録 (ADR)

Architecture Decision Records (ADR) 形式で主要な設計判断を記録します。

---

## ADR-001: pyvmomi の採用

**ステータス**: 採用

**背景**: vSphere API にアクセスするための Python SDK を選定する必要がある。

**選択肢**:
1. pyvmomi - VMware 公式 Python SDK
2. vmware-aria-automation-sdk - Aria 向け SDK
3. govmomi（Go）の Python バインディング

**決定**: pyvmomi を採用

**理由**:
- VMware 公式で最も成熟しており、ドキュメント・コミュニティが豊富
- vcsim（govmomi 同梱）と同じ API で互換性がある
- MCP サーバー用途では Go の速度優位性は不要

**リスク**: Broadcom 買収後の OSS 方針変更

---

## ADR-002: confirm デコレータパターン

**ステータス**: 採用

**背景**: 破壊的操作（電源 OFF、VM 削除等）の誤操作を防止する仕組みが必要。

**選択肢**:
1. 各ツール関数内で個別に confirm チェック
2. デコレータで一元化
3. MCP プロトコルレベルでの確認機構

**決定**: `@require_confirm(danger_level="...")` デコレータで一元化

**理由**:
- ツールごとに分岐ロジックを書くと冗長で確認漏れのリスクがある
- 危険度レベル（low/medium/high/critical）を引数で指定できる
- `inspect.signature` を操作して `confirm: bool` パラメータを自動追加
- 将来 UI 側で「高以上は二段階確認」等の拡張が可能

---

## ADR-003: PropertyCollector の使用

**ステータス**: 採用

**背景**: vcsim 環境で `ContainerView.view` から取得した managed object reference に対して直接プロパティアクセス（`vm.summary` 等）すると `AttributeError` が発生する問題が判明。

**選択肢**:
1. 直接プロパティアクセス（`vm.summary.config.numCpu`）
2. PropertyCollector（`RetrieveContents` + `FilterSpec`）

**決定**: 全プロパティ取得を PropertyCollector 経由に統一

**理由**:
- vcsim と実機 vCenter の両方で動作する
- 必要なプロパティのみを指定して取得するため、大量 VM 環境でもパフォーマンスが良い
- VMware 公式ドキュメントでも推奨されている方式

**トレードオフ**: コードの可読性がやや低下（ドット区切りのプロパティパス文字列）

---

## ADR-004: stdio をデフォルトトランスポートに

**ステータス**: 採用

**背景**: MCP サーバーの通信トランスポートを決定する必要がある。

**選択肢**:
1. stdio（標準入出力）
2. SSE (Server-Sent Events)
3. Streamable HTTP

**決定**: stdio をデフォルトとする

**理由**:
- ローカル運用が主用途で最もシンプル
- ポート公開不要 = セキュリティリスクが低い
- Claude Code の `claude mcp add` で即登録可能
- SSE/HTTP は将来のオプションとして残す

---

## ADR-005: handle_tool_errors による例外一元化

**ステータス**: 採用

**背景**: vSphere API の例外が多岐にわたり、各ツールで個別にハンドリングすると冗長になる。

**選択肢**:
1. 各ツール関数内で try/except
2. デコレータで一元化
3. ミドルウェアパターン

**決定**: `@handle_tool_errors` デコレータで一元化

**理由**:
- `VSphereToolError` と一般例外を区別してログ出力
- 実行時間（`duration_ms`）を自動記録
- エラー時も統一フォーマット（`{"status": "error", "error": "..."}`)で返却
- ツール関数はビジネスロジックに集中できる

---

## ADR-006: PASSWORD_FILE によるシークレット管理

**ステータス**: 採用

**背景**: Docker Secret / Kubernetes Secret 環境では、パスワードを環境変数ではなくファイルとして提供するパターンが標準的。

**選択肢**:
1. 環境変数 `VSPHERE_PASSWORD` のみ
2. `VSPHERE_PASSWORD_FILE` の追加対応

**決定**: 両方に対応（`PASSWORD_FILE` が設定されている場合はファイルから読み込み）

**理由**:
- Docker Compose の `secrets` / Kubernetes の `Secret` マウントに対応
- `pydantic` の `model_validator` で読み込みロジックを実装
- `PASSWORD` が直接設定されている場合はそちらを優先
