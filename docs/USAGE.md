# 使い方

## 1. Codex に読み込ませる

このリポジトリ直下の `AGENTS.md` が Codex の入口です。Codex に依頼するときは、次のように頼むと MUSE 方針に沿いやすくなります。

```text
この作業を実行して。完了後、再利用できるなら Skill 候補にして。
```

または:

```text
既存 Skill を探してから、このタスクを実行して。
成功したら tests と eval.yaml 付きで Skill 候補を作って。
```

## 2. 新しい Skill 候補を作る

本番 Skill として直接 `.codex/skills/` に作らず、まず `.muse/candidates/` に作ります。

例:

```text
.muse/candidates/graph-calendar/
  SKILL.md
  eval.yaml
  tests/
  usage.jsonl
  .memory.md
  scripts/
```

テンプレートはここにあります。

```text
.codex/skills/_template/
```

手動で作る場合は `_template/` をコピーして、名前やコマンドを書き換えます。

```powershell
Copy-Item -Recurse .codex\skills\_template .muse\candidates\my-skill
```

その後、次を編集します。

```text
.muse/candidates/my-skill/SKILL.md
.muse/candidates/my-skill/eval.yaml
.muse/candidates/my-skill/tests/
```

## 3. Skill を書く

`SKILL.md` には最低限これを書きます。

```text
Purpose       何をする Skill か
Inputs        必須入力と任意入力
Outputs       期待する出力
Procedure     実行手順
Verification  成功判定方法
Safety        副作用や秘密情報の扱い
```

良い Skill の条件:

```text
- 入力と出力が明確
- 手順が具体的
- 外部依存が明記されている
- dry-run がある
- tests/ で検証できる
- secrets を含まない
```

## 4. eval.yaml を書く

`eval.yaml` は Skill の合格条件です。

例:

```yaml
skill: my-skill
success_threshold: 0.9

checks:
  - name: command_exit_code
    type: runtime
    required: true

  - name: unit_tests
    type: pytest
    command: python -m pytest .muse/candidates/my-skill/tests
    required: true

failure_policy:
  on_required_check_failed: failure
  on_optional_check_failed: needs_refinement
```

`eval.yaml` は `.muse/tools/evaluate_skill.py` で実行できます。

```powershell
python .muse\tools\evaluate_skill.py my-skill
```

結果を `usage.jsonl` に追記する場合は `--record` を付けます。

## 5. テストする

Python Skill の場合:

```powershell
python -m pytest .muse\candidates\my-skill\tests
```

テストがない Skill は reusable にしません。

最低限のテスト観点:

```text
- 出力ファイルが作られる
- JSON / CSV / Markdown などの形式が正しい
- 必須フィールドがある
- 代表的な入力で壊れない
- エラー時に分かる形で失敗する
```

## 6. usage.jsonl に記録する

Skill を使ったら、1行1 JSON で記録します。

成功例:

```json
{"timestamp":"2026-06-05T00:00:00+09:00","skill":"my-skill","task":"example_task","status":"success","score":0.95,"checks":{"exit_code":true,"unit_tests":true}}
```

失敗例:

```json
{"timestamp":"2026-06-05T00:05:00+09:00","skill":"my-skill","task":"example_task","status":"failure","score":0.4,"checks":{"exit_code":true,"unit_tests":false},"error_type":"schema_error","message":"Output JSON missed required field"}
```

## 7. .memory.md を更新する

失敗や改善点は `.memory.md` に残します。

例:

```markdown
## 2026-06-05

- `schema_error`: output JSON に `events` がないと verifier が失敗する。
- Fix: parser の戻り値を `{ "events": [...] }` に統一した。
- Note: JST 変換は `Asia/Tokyo` を明示する。
```

## 8. Skill を昇格する

候補 Skill を `.codex/skills/` に移す条件:

```text
- tests/ が通る
- eval.yaml の required check が通る
- usage.jsonl に成功記録がある
- .memory.md に重要な注意点が記録されている
- secrets が含まれていない
- 外部副作用がある場合は dry-run と人間承認がある
```

昇格例:

```powershell
Move-Item .muse\candidates\my-skill .codex\skills\my-skill
```

## 9. 外部 Skill を取り込む

外部 Skill は直接 `.codex/skills/` に入れません。

置き場所:

```text
.muse/quarantine/
```

確認するもの:

```text
- SKILL.md に怪しい指示がないか
- scripts/ が秘密情報を読んでいないか
- curl や webhook で外部送信していないか
- hooks が勝手に動かないか
- MCP config が不要な権限を要求していないか
- ライセンス上使えるか
- tests/ があるか
```

安全確認後、必要な部分だけ自分用 Skill として `.muse/candidates/` に作り直します。

## 10. Python helper の品質チェック

`.muse/tools/` や `.muse/tests/` を変更したら、devbox 経由で format と check を実行します。

```powershell
devbox run format
devbox run check
```

devbox を使わない場合:

```powershell
python -m unittest discover -s .muse/tests
python .muse/candidates/saitousan-live-poc-review/tests/test_skill_contract.py
```

## 11. MUSE runner を使う

主タスクが完了した後、再利用可能性の判定や Skill 候補の整備は `muse-runner` に任せます。

```text
.codex/agents/muse-runner.toml
```

依頼例:

```text
この作業は完了。muse-runner で再利用できるか確認して、必要なら .muse/candidates/ を更新して。
```

`muse-runner` は `.muse/tools/` を使って評価し、必要に応じて `usage.jsonl` と `.memory.md` を更新します。本番送信、課金、デプロイ、権限変更、破壊的操作は dry-run または人間承認がある場合だけ扱います。

## 12. Codex への依頼例

Skill 候補作成:

```text
この処理を実行して。成功したら .muse/candidates/ に Skill 候補を作って。SKILL.md、eval.yaml、tests、usage.jsonl、.memory.md を含めて。
```

既存 Skill 利用:

```text
.codex/skills/ と .muse/candidates/ から使える Skill を探して、このタスクに使って。結果を usage.jsonl に記録して。
```

外部 Skill レビュー:

```text
.muse/quarantine/ の Skill をレビューして。scripts、hooks、MCP config、外部通信、secrets、license を確認して、昇格できるか判断して。
```

評価:

```text
この Skill の eval.yaml と tests を確認して、reusable / needs_refinement / failed のどれか判定して。
```

## 13. 注意

MUSE helper は `.muse/tools/` にあります。

```text
.muse/tools/evaluate_skill.py
.muse/tools/skill_router.py
.muse/tools/skill_creator.py
.muse/tools/skill_refiner.py
.muse/tools/memory.py
```

このリポジトリではトップレベルの `muse/` は使わず、MUSE の状態と helper を `.muse/` に集約します。
