# MUSE について

## MUSE とは

MUSE-Autoskill は、エージェントがタスクを解きながら Skill を作成・記憶・管理・評価・改善するためのフレームワークです。

通常の Skill 運用では、Skill は一度作ったら固定された説明文やスクリプトとして扱われがちです。MUSE では、Skill を長期的に育てる資産として扱います。

中心になるライフサイクルは次の5つです。

```text
creation    Skill を作成する
memory      Skill ごとの経験を蓄積する
management  Skill Bank を検索・統合・更新・削除する
evaluation  Unit test と runtime feedback で評価する
refinement  失敗した Skill を修正して再評価する
```

## MUSE の基本動作

MUSE 型のエージェントは、タスクを受けるとまず既存 Skill を探します。

```text
User Task
  -> 既存 Skill を検索
  -> 見つかれば使う
  -> 見つからなければ通常の方法で解く
  -> 成功したら Skill 化する価値を判定
  -> Skill 候補を作る
  -> tests/ と eval.yaml で評価
  -> 通ったら Skill Bank に登録
  -> 失敗したら memory に記録し、必要なら修正
```

重要なのは、最初から毎回 Skill を作るわけではないことです。まずタスクを解き、成功した再利用可能な手順だけを Skill 化します。

## Skill とは

このリポジトリでは、Skill は次のようなディレクトリとして扱います。

```text
.codex/skills/<skill-name>/
  SKILL.md
  eval.yaml
  tests/
  usage.jsonl
  .memory.md
  scripts/
```

各ファイルの役割:

```text
SKILL.md     Skill の目的、入力、出力、手順、安全ルール
eval.yaml    評価条件と成功閾値
tests/       自動テスト
usage.jsonl  使用履歴と成功/失敗ログ
.memory.md   失敗パターン、環境メモ、改善履歴
scripts/     必要な実行コード
```

## 成功判定

MUSE では、LLM に「成功したと思うか」を聞くのではなく、外部から検証できる signal を集めます。

優先順位:

1. Runtime check: exit code、例外、timeout、出力ファイル有無
2. Unit test: schema、変換処理、既知ケース
3. Integration test: API 応答、dry-run、外部サービス接続
4. Task-level acceptance criteria: ユーザー目的を満たしたか
5. LLM judge: 読みやすさ、自然さなど主観評価
6. Human approval: 本番送信、書き込み、デプロイなど

登録基準:

```text
score >= 0.9          reusable
0.6 <= score < 0.9    needs_refinement
score < 0.6           failed
```

## Memory

MUSE の特徴は Skill-level memory です。

Skill ごとに `.memory.md` を持ち、次のような情報を蓄積します。

```text
- よくある失敗
- API や外部サービスの癖
- 成功した入力形式
- timeout や rate limit の注意
- 修正済みの不具合
- 次回使うときの注意点
```

このリポジトリでは、まず Skill ごとの `.memory.md` を使います。将来的には short-term memory、long-term memory、skill-level memory を分けて管理できます。

## Skill Bank

Skill Bank は、テスト済み Skill の保存場所です。

このリポジトリでは次を Skill Bank とします。

```text
.codex/skills/
```

未検証の Skill はここに置きません。

```text
.muse/candidates/   作成中・テスト中の Skill
.muse/quarantine/   外部から持ってきた未信頼 Skill
```

## 外部 Skill の扱い

外部 Skill、GitHub リポジトリ、プラグインマーケット、Web snippets は直接 `.codex/skills/` に入れません。

安全な流れ:

```text
外部 Skill
  -> .muse/quarantine/
  -> SKILL.md / scripts / hooks / MCP config をレビュー
  -> secrets や外部送信を確認
  -> 必要部分だけ自分用に再構成
  -> tests/ と eval.yaml を追加
  -> dry-run
  -> 承認
  -> .codex/skills/ に昇格
```

## このリポジトリでの位置づけ

このリポジトリは、MUSE 論文の全機能を実行する完成システムではありません。

現時点では、Codex に読み込ませるための運用ポリシー、Skill 管理の土台、MUSE helper の最小実装です。

論文通りの完全実装に近づけるには、次の実行コードが必要です。

```text
.muse/tools/evaluate_skill.py   eval.yaml を読み、tests と runtime checks を実行する
.muse/tools/skill_router.py     既存 Skill を検索して選ぶ
.muse/tools/skill_creator.py    成功手順から Skill 候補を作る
.muse/tools/skill_refiner.py    失敗した Skill を修正する
.muse/tools/memory.py           usage.jsonl と .memory.md を読み書きする
```

## 参考

- MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation
- arXiv: https://arxiv.org/abs/2605.27366
