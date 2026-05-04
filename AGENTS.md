# ai-coding-setup

<!-- テンプレート: このファイルを自分のプロジェクトにコピーした後、各セクションの内容を書き換えてください -->

AI コーディングエージェントのハーネス（プロジェクト設定一式）を構築するための実践ガイドとテンプレート集。
Claude Code / GitHub Copilot / Cline 等のマルチツール対応。

## 技術スタック
- 言語: Markdown, JSON, YAML
- 対象ツール: Claude Code, GitHub Copilot, Cline, OpenClaw, Codex CLI, Gemini CLI

## ディレクトリ構成
<!-- 自分のプロジェクトの実際のディレクトリ構造に書き換えてください -->
```
my-project/
├── src/                               # ソースコード
├── tests/                             # テスト
├── docs/                              # ドキュメント
└── package.json                       # 依存管理
```

## コーディング規約
- ファイル命名: kebab-case
- ロール定義: Markdown + YAML frontmatter 形式
- AGENTS.md: 100 行以内を目標
- ロール description: 「いつ呼ばれるか」を明示するトリガー文で書く

## 制約（絶対にしてはいけないこと）
- `.env` や `secrets/` 配下を絶対にコミットしない
- `.mcp.json` にトークンをハードコードしない（常に `${ENV_VAR}` 経由）
- ロールに全権限（Read/Edit/Write/Bash すべて）を与えない
- AGENTS.md に抽象的なマニフェスト（「品質を重視」等）を書かない

## エージェントロール
- explorer / planner / generator / critic / evaluator

## 開発コマンド
<!-- 重要: 以下は Node.js プロジェクト向けの例です。自分のプロジェクトの実際のコマンドに書き換えてください -->
```bash
# テスト
npm test              # 全テスト実行
npm run test:watch    # ウォッチモード

# リント・フォーマット
npm run lint          # リント
npm run format        # フォーマット

# ビルド
npm run build         # プロダクションビルド

# 型チェック
npm run typecheck     # TypeScript 型チェック
```

## 推奨ワークフロー
- 複雑なタスク: Explorer → Planner → Generator → Critic → Evaluator
- 簡単な変更: Generator → Evaluator
