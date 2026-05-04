# 詳細要件定義

ai-coding-setup プロジェクトの設計思想、要件、仕様を定義するドキュメント。

---

## 1. プロジェクト概要

### 目的

AI コーディングエージェントが一貫した品質で動作するための「ハーネス」（プロジェクト用設定一式）を提供する。
「同じプロジェクトで何度も同じ手順を踏む」状態を解消し、エージェントの出力品質を安定させる。

### スコープ

- エージェントロール定義（サブエージェント）
- プロジェクト指示書（AGENTS.md）
- MCP サーバ設定
- 上記のマルチツール対応

### 対象ツール

| ツール | 対応レベル |
|---|---|
| Claude Code | フル対応（指示書 + ロール定義 + MCP + Skill） |
| GitHub Copilot | フル対応（指示書 + ロール定義 + MCP） |
| Cline | フル対応（指示書 + ロール定義 + MCP） |
| Codex CLI | 基本対応（指示書のみ） |
| Gemini CLI | 基本対応（指示書 + 専用指示書） |
| OpenClaw | 基本対応（指示書のみ） |

---

## 2. 設計原則

### P1: 汎用ロールで大半をカバー

5 つの標準ロール（Explorer / Planner / Generator / Critic / Evaluator）+ オプションの Executor で実務の大半をカバーする。専門エージェントは必要時のみ外部カタログから補完する（0〜2 個に抑える）。

### P2: AGENTS.md を主軸にしたマルチツール対応

`AGENTS.md` をプロジェクトの主指示書とする。ほぼ全ての主要エージェントツールが読み取るため、1 ファイルで情報の二重管理を避けられる。ツール固有の設定だけを個別ファイルに分ける。

### P3: 最小権限の原則

各ロールには責務に必要な最小限のツール権限のみを付与する。Read/Edit/Write/Bash すべてを持つロールは作らない。

### P4: 副作用の隔離

副作用ある操作（デプロイ、マイグレーション、本番変更等）は Executor ロールに隔離し、dry-run と明示的な承認を必須とする。

### P5: 具体性の徹底

指示書・ロール定義には抽象的なマニフェスト（「品質を重視する」等）を書かない。具体的なコマンド、規約、制約を記述する。

---

## 3. エージェントロール要件

### 3.1 ロール一覧

| ロール | 責務 | 副作用 | 推奨モデル |
|---|---|---|---|
| Explorer | 既存コード/ドキュメント/外部仕様の調査 | なし（read-only） | 軽量（haiku） |
| Planner | タスクの分解、実装計画の作成 | なし（read-only） | 中〜上位（sonnet） |
| Generator | 計画に従ってコード/設定/ドキュメントを生成 | ファイル編集 | 中〜上位（sonnet） |
| Critic | Generator の出力を品質観点でレビュー | なし（read-only） | 中〜上位（sonnet） |
| Evaluator | テスト/ビルド/ベンチマークを実行し合否判定 | コマンド実行 | 軽量（haiku） |
| Executor | デプロイ/マイグレーション等の副作用ある実行 | 強い副作用 | 中〜上位（sonnet） |

### 3.2 ツール権限マトリクス

| ロール | Read | Edit | Write | Bash | Grep | Glob | Agent |
|---|---|---|---|---|---|---|---|
| Explorer | o | x | x | x | o | o | x |
| Planner | o | x | x | x | o | o | x |
| Generator | o | o | o | x | o | o | x |
| Critic | o | x | x | x | o | o | o |
| Evaluator | o | x | x | o | o | x | x |
| Executor | o | x | x | o | x | x | x |

- `o`: 許可
- `x`: 禁止
- `△`: 最小限の使用に限定

### 3.3 構成パターン

| パターン | ロール | 推奨ケース |
|---|---|---|
| 最小構成（3 ロール） | Planner / Generator / Evaluator | 小規模・個人開発 |
| 推奨構成（5 ロール） | Explorer / Planner / Generator / Critic / Evaluator | 中規模以上 |
| フル構成（6 ロール） | 上記 + Executor | デプロイ・インフラ操作あり |

### 3.4 ロール定義ファイル仕様

#### ファイル形式

Markdown + YAML frontmatter

#### 必須フィールド

```yaml
---
name: <ロール名>            # kebab-case、英小文字
description: <トリガー文>    # 「いつ呼ばれるか」を明示する文
tools: <ツールリスト>        # カンマ区切り
model: <モデル名>            # haiku / sonnet / opus
---
```

#### description の要件

- 「ラベル」ではなく「トリガー文」として記述する
- 「いつ呼ばれるべきか」を具体的に書く
- `MUST BE USED`、`proactively` 等の表現で自動発動を促す

```yaml
# NG: ラベル
description: コードレビュアー

# OK: トリガー文
description: コミット前にコード変更を必ずレビューする。Generator の出力直後にも proactively 使用する。
```

#### 本文の構成

1. ロールの宣言（1 行）
2. `## 役割` セクション（箇条書き）
3. `## ワークフロー` セクション（番号付きリスト）
4. `## 制約` セクション（箇条書き）

#### 配置先

| ツール | パス |
|---|---|
| Claude Code | `.claude/agents/<role-name>.md` |
| GitHub Copilot | `.github/agents/<role-name>.md` |
| Cline | `.cline/agents/<role-name>.md` |

### 3.5 各ロールの詳細要件

#### Explorer

- 目的: 既存コードベースの調査、影響範囲の特定
- 入力: 調査対象の指示
- 出力: 構造化された調査報告（事実と推測を区別）
- ワークフロー: 対象明確化 → Glob で構造把握 → Grep で検索 → Read で精読 → 報告
- 禁止事項: ファイル編集、コマンド実行

#### Planner

- 目的: タスクを実装可能な単位に分解し、計画を作成
- 入力: 要求・要件の記述
- 出力: 3〜10 ステップの実装計画（各ステップに完了条件付き）
- ワークフロー: 要求確認 → 影響範囲見積 → ステップ分解 → 完了条件明示 → リスク記述
- 禁止事項: ファイル編集、コマンド実行、曖昧な表現（「適切に修正する」等）
- 制約: 1 ステップ = 1 コミット相当が目安

#### Generator

- 目的: 計画に従ったコード・設定・ドキュメントの生成・編集
- 入力: Planner の計画、または直接の修正指示
- 出力: 変更されたファイル + 変更内容の報告
- ワークフロー: 計画確認 → 対象ファイル Read → Edit/Write で変更 → 報告
- 禁止事項: 計画にない変更、過剰なリファクタリング
- 制約: Bash は最小限（ファイル操作は Edit/Write 優先）

#### Critic

- 目的: コード変更の品質レビュー
- 入力: Generator の出力（変更されたファイル）
- 出力: 問題点と改善提案（優先度付き: Critical / Major / Minor / Nitpick）
- ワークフロー: 変更ファイル確認 → 計画照合 → 多角的レビュー → 報告
- レビュー観点:
  - 正確性: ロジックにバグがないか
  - セキュリティ: 脆弱性がないか
  - 可読性: 命名、構造が明瞭か
  - 規約準拠: プロジェクトの規約に沿っているか
- 禁止事項: ファイル編集、コマンド実行、改善案のない批判

#### Evaluator

- 目的: テスト・ビルド・リント・型チェックの実行と合否判定
- 入力: 検証対象の変更
- 出力: PASS / FAIL の判定 + 原因分析
- ワークフロー: 対象確認 → コマンド実行 → 結果報告
- 禁止事項: ファイル編集、テスト結果の改ざん、失敗の隠蔽

#### Executor

- 目的: デプロイ・マイグレーション等の副作用ある操作の安全な実行
- 入力: 実行対象の操作指示
- 出力: 実行結果 + 検証報告
- ワークフロー（必須、省略不可）:
  1. 意図確認
  2. Dry-run / Plan / Preview を提示
  3. 影響範囲とロールバック手順を明示
  4. ユーザーの明示的な承認を取得
  5. 適用
  6. 検証と報告
- 禁止事項: 承認なしの実行、ファイル編集、ロールバック手順なしの実行

---

## 4. 指示書要件

### 4.1 AGENTS.md（全ツール共通）

#### 目的

毎セッションでエージェントが読むプロジェクトのコンテキストを提供する。

#### 必須セクション

1. プロジェクト名と説明（1〜3 行）
2. 技術スタック（言語、ランタイム、パッケージマネージャ、フレームワーク、テストフレームワーク）
3. ディレクトリ構成
4. コーディング規約
5. 制約（絶対にしてはいけないこと）
6. エージェントロール一覧
7. 推奨ワークフロー

#### 制約

- 100 行以内を目標
- 抽象的なマニフェストを書かない
- コマンドは実際に動くものを具体的に記述
- 否定形（「〜しない」）を積極的に使う（守られやすい）

### 4.2 CLAUDE.md（Claude Code 固有）

#### 目的

Claude Code 固有の設定と参照先を記述する。

#### 必須内容

- AGENTS.md への参照
- サブエージェント定義の配置先（`.claude/agents/`）
- MCP 設定の配置先（`.mcp.json`、リポジトリルート）
- Skill 配置先（`.claude/skills/`）

### 4.3 GEMINI.md（Gemini CLI 固有）

#### 目的

Gemini CLI 固有の設定を記述する。AGENTS.md と重複する場合は AGENTS.md への参照で代替可。

#### 必須内容

- AGENTS.md への参照
- ロール一覧（Gemini CLI はロール定義ファイルを読まないため本文に記載）
- 推奨ワークフロー
- 制約

---

## 5. MCP サーバ要件

### 5.1 設定ファイルの配置

| ツール | ファイルパス | キー名 |
|---|---|---|
| Claude Code | `.mcp.json`（リポジトリルート） | `mcpServers` |
| GitHub Copilot | `.vscode/mcp.json` | `servers` |
| Cline | `.cline/mcp_settings.json` | `mcpServers` |

### 5.2 同梱する MCP サーバ

| サーバ | パッケージ | 用途 |
|---|---|---|
| context7 | `@upstash/context7-mcp@latest` | ライブラリ最新ドキュメント参照 |
| playwright | `@anthropic-ai/mcp-server-playwright` | ブラウザ操作（テスト、スクレイピング） |
| filesystem | `@anthropic-ai/mcp-server-filesystem` | スコープ付きファイルアクセス |

### 5.3 制約

- MCP サーバは 3 個以下に抑える（各サーバが毎ターンのコンテキストを消費するため）
- トークン・シークレットは必ず環境変数経由（`${ENV_VAR}`）。ハードコード厳禁
- `.mcp.json` はリポジトリルートに配置（`.claude/` の中ではない）
- 追加する場合の選定基準:
  - プロジェクトで頻繁に使う外部サービスか
  - 手動操作の削減効果が大きいか
  - コンテキスト消費に見合う価値があるか

### 5.4 MCP サーバ追加時の手順

新しい MCP サーバを追加する場合、以下の全ファイルを同時に更新する:

1. `.mcp.json`（Claude Code 用、キー: `mcpServers`）
2. `.vscode/mcp.json`（Copilot 用、キー: `servers`）
3. `.cline/mcp_settings.json`（Cline 用、キー: `mcpServers`）

---

## 6. ディレクトリ構成要件

### 6.1 完全なファイルツリー

```
ai-coding-setup/
├── AGENTS.md                          # 全ツール共通指示書
├── CLAUDE.md                          # Claude Code 固有設定
├── GEMINI.md                          # Gemini CLI 固有設定
├── .mcp.json                          # Claude Code 用 MCP 設定
├── README.md                          # リポジトリ説明
│
├── .claude/
│   └── agents/                        # Claude Code 用ロール定義
│       ├── explorer.md
│       ├── planner.md
│       ├── generator.md
│       ├── critic.md
│       └── evaluator.md
│
├── .github/
│   └── agents/                        # GitHub Copilot 用ロール定義
│       ├── explorer.md
│       ├── planner.md
│       ├── generator.md
│       ├── critic.md
│       └── evaluator.md
│
├── .cline/
│   ├── agents/                        # Cline 用ロール定義
│   │   ├── explorer.md
│   │   ├── planner.md
│   │   ├── generator.md
│   │   ├── critic.md
│   │   └── evaluator.md
│   └── mcp_settings.json             # Cline 用 MCP 設定
│
├── .vscode/
│   └── mcp.json                       # Copilot 用 MCP 設定
│
└── docs/
    ├── requirements.md                # 本ドキュメント（詳細要件定義）
    └── usage.md                       # 使い方ガイド
```

### 6.2 ファイル命名規約

- kebab-case を使用
- ロール定義: `<role-name>.md`（英小文字）
- 設定ファイル: ツールの規約に従う

---

## 7. ワークフロー要件

### 7.1 複雑なタスク（5 ステップ）

```
Explorer → Planner → Generator → Critic → Evaluator
```

1. **Explorer**: 既存コードを調査、関連箇所を特定
2. **Planner**: 実装計画を作成、ステップ分解
3. **Generator**: 計画に従って実装
4. **Critic**: 品質レビュー（バグ、セキュリティ、可読性）
5. **Evaluator**: テスト/ビルド/型チェック

### 7.2 簡単な変更（2 ステップ）

```
Generator → Evaluator
```

1. **Generator**: タイポ修正、ログ追加など
2. **Evaluator**: 検証

### 7.3 副作用ある操作（6 ステップ、Executor 使用）

```
Explorer → Planner → Generator → Critic → Evaluator → Executor
```

Executor のワークフローは省略不可:
1. 意図確認
2. Dry-run を実行
3. 影響範囲とロールバック手順を提示
4. ユーザー承認を取得
5. 適用
6. 検証と報告

---

## 8. マルチツール対応要件

### 8.1 対応マトリクス

| 機能 | Claude Code | GitHub Copilot | Cline | Codex CLI | Gemini CLI | OpenClaw |
|---|---|---|---|---|---|---|
| AGENTS.md 読み取り | o | o | o | o | o | o |
| 専用指示書 | CLAUDE.md | - | - | - | GEMINI.md | - |
| サブエージェント定義 | `.claude/agents/` | `.github/agents/` | 参考用のみ | x | x | 限定的 |
| ロール呼び出し方式 | 自動発動 | `@ロール名` | プロンプト指示 | プロンプト指示 | プロンプト指示 | プロンプト指示 |
| MCP 設定 | `.mcp.json` | `.vscode/mcp.json` | `.cline/mcp_settings.json` | x | x | 独自 |
| Skill 配置 | `.claude/skills/` | `.github/skills/` | `.cline/skills/` | x | x | 独自 |

### 8.2 ロール定義の同期

- 全ツールのロール定義は同一内容を維持する
- 変更時は `.claude/agents/` を原本とし、`.github/agents/` と `.cline/agents/` にコピーする
- `tools:` と `model:` は Claude Code 固有のフィールドだが、他ツールでは無視されるため残して問題ない

### 8.3 MCP 設定の同期

- 全ツールの MCP 設定は同一サーバ構成を維持する
- キー名がツールによって異なる点に注意:
  - Claude Code / Cline: `mcpServers`
  - Copilot: `servers`
- サーバ追加・変更時は 3 ファイルすべてを同時に更新する

---

## 9. 品質要件

### 9.1 指示書の品質基準

- AGENTS.md は 100 行以内
- 抽象的な記述がない
- すべてのコマンドが実際に動作する
- 否定形の制約が明確に記述されている

### 9.2 ロール定義の品質基準

- description がトリガー文になっている（ラベルではない）
- ツール権限が最小限に設定されている
- ワークフローが番号付きリストで具体的に記述されている
- 制約セクションで禁止事項が明示されている

### 9.3 MCP 設定の品質基準

- トークンがハードコードされていない
- サーバ数が 3 個以下
- 全ツールの設定ファイルが同期されている

---

## 10. アンチパターン

このプロジェクトで避けるべきパターン:

| アンチパターン | 問題 | 対策 |
|---|---|---|
| 過剰なロール定義 | 使われないロールが増える | 2〜3 個で開始、必要時に追加 |
| 全権限ロール | 安全機構が無効化 | ロールごとに最小権限 |
| AGENTS.md のマニフェスト化 | 抽象論は無価値 | 具体的なコマンド・規約・制約のみ |
| ロール間の責務重複 | 品質低下 | Critic と Evaluator 等は観点で分離 |
| ハードコードされた秘密情報 | セキュリティ事故 | 常に `${ENV_VAR}` 経由 |
| 複数ツールで指示書分裂 | 情報不整合 | AGENTS.md を主軸に統合 |
| ロール定義の未更新 | 古い情報が害を及ぼす | 規約変更時に同期更新 |
| dry-run なしの Executor | 事故の元 | 段階的実行を必須化 |
| MCP サーバ過多 | コンテキスト圧迫 | 3 個以下に抑制 |
| `.mcp.json` の誤配置 | 認識されない | リポジトリルートに配置 |
| description がラベル | 自動発動しない | 「いつ呼ばれるか」を記述 |
| ツール間の MCP 設定不整合 | 動作差異 | 3 ファイル同時更新 |

---

## 11. プロジェクト種別ごとの推奨セット

導入先プロジェクトの種別に応じた推奨構成:

| プロジェクト種別 | ロール構成 | 追加推奨 MCP |
|---|---|---|
| ライブラリ / CLI | Planner / Generator / Critic / Evaluator | context7 |
| Web アプリケーション | Explorer / Planner / Generator / Critic / Evaluator | context7, playwright |
| データ処理 / ETL | Planner / Generator / Evaluator | DB MCP（開発環境のみ） |
| LLM / RAG / ML | フル 5 ロール | context7 |
| インフラ自動化（k8s/IaC） | フル 6 ロール（Executor 必須） | GitHub MCP |

---

## 12. 今後の拡張方針

### Skill パッケージ化

ハーネス一式を Claude Code の Skill としてパッケージ化し、`/agent-harness-setup` で自動セットアップできるようにする。

- 配置先: `.claude/skills/agent-harness-setup/`
- 構成: `SKILL.md` + `references/` + `templates/`

### マーケットプレイス公開

GitHub プラグインマーケットプレイスへの公開を検討:

- `plugin.json` / `marketplace.json` の整備
- semver によるバージョン管理
- `claude plugin marketplace` コマンドでのインストール対応

### シンボリックリンクによる一元管理

複数ツール間でスキルを共有する場合:

```bash
ln -sf ~/skills-master/agent-harness-setup ~/.claude/skills/agent-harness-setup
ln -sf ~/skills-master/agent-harness-setup ~/.copilot/skills/agent-harness-setup
ln -sf ~/skills-master/agent-harness-setup ~/.cline/skills/agent-harness-setup
```
