# Codex での使い方

## 目的

このリポジトリを Codex で開いたときに、MUSE 方針で Skill を作成・評価・管理するための手順です。

Codex 用の入口は `AGENTS.md` です。

## 読み込み対象

Codex 向け:

```text
AGENTS.md
.codex/CODEX.md
.codex/skills/
.muse/tools/
```

共通ドキュメント:

```text
docs/MUSE.md
docs/USAGE.md
MUSE_ARCHITECTURE.md
```

## 基本の頼み方

Codex には次のように依頼します。

```text
既存 Skill を探してからこのタスクを実行して。
成功したら、再利用できるか判定して Skill 候補を作って。
```

または:

```text
この作業を実行して。完了後、MUSE 方針で usage.jsonl と .memory.md を更新して。
```

## Skill 候補の作成

新規 Skill はまず `.muse/candidates/` に作ります。

```powershell
Copy-Item -Recurse .codex\skills\_template .muse\candidates\my-skill
```

編集対象:

```text
.muse/candidates/my-skill/SKILL.md
.muse/candidates/my-skill/eval.yaml
.muse/candidates/my-skill/tests/
.muse/candidates/my-skill/.memory.md
.muse/candidates/my-skill/usage.jsonl
```

## Codex Skill への昇格

候補 Skill を `.codex/skills/` に昇格する条件:

```text
tests/ が通る
eval.yaml の required check が通る
usage.jsonl に成功記録がある
.memory.md に重要な注意点がある
secrets が含まれていない
副作用がある場合は dry-run または人間承認がある
```

昇格例:

```powershell
Move-Item .muse\candidates\my-skill .codex\skills\my-skill
```

## Codex 用の構成

```text
AGENTS.md
.codex/CODEX.md
.codex/skills/
.muse/tools/
```

MUSE 作業用:

```text
.muse/candidates/
.muse/quarantine/
.muse/evaluations/
.muse/logs/
docs/
```

## 注意

Codex 用の MUSE router / evaluator / creator / refiner / memory は `.muse/tools/` にあります。

代表的なコマンド:

```sh
python .muse/tools/skill_router.py --prompt "タスク内容" --json
python .muse/tools/evaluate_skill.py saitousan-live-poc-review
python .muse/tools/skill_refiner.py saitousan-live-poc-review --record
python .muse/tools/memory.py enqueue --task "完了した作業の要約" --source codex-main
```

Python helper を変更したら、devbox 経由で formatter と check を実行します。

```sh
devbox run format
devbox run check
```
