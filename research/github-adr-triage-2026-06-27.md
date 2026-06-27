# GitHub PR・Issue・ADR棚卸し（2026-06-27）

## Scope

GitHub repository `suzuki-engineering/saitousan-docs` の全Issue・全PR・既存ADRを確認した。

- Issue: 11件、すべてOpen、コメント0件
- PR: 6件
  - Open: 4件
  - Merged: 2件
- 既存ADR: ADR-0001〜0008（ADR-0003は削除済み）

Issue #2〜#5、#12、#18はIssue欠番ではなくPR番号である。

## PR整理

| PR | State | Role | Judgment / Next action |
| --- | --- | --- | --- |
| #2 | Merged | ADR-0007（Slack/Codex開発運用） | main反映済み。追加対応なし |
| #18 | Merged | Issue #17のADR-0008（EC2 Runtime Host） | main反映済み。2026-06-27のAWS公式情報に合わせ、nested virtualization前提を補正 |
| #12 | Open | Issue #6〜#11、#13〜#16のADR群 | 残るIssue ADRの唯一の統合先にする。mainへrebaseし、ADR-0008衝突を解消してADR-0009〜0018へ再採番 |
| #3 | Open | MUSE helper本体 | stack root。Windows pathとquarantine既定除外の修正済み |
| #4 | Open | Devbox/lint設定 | #3依存。Python 3.12固定済み |
| #5 | Open | MUSE review agent | #4依存。stack先端 |

### PR #3〜#5 stack

依存順は `#3 -> #4 -> #5`。個別にmainへ直接mergeするのではなく、この順序を維持する。

2026-06-27のローカル確認:

- `python -m unittest discover -s .muse/tests`: 13 tests passed
- `saitousan-live-poc-review` contract tests: 5 tests passed
- `evaluate_skill.py saitousan-live-poc-review`: score 1.0 / reusable
- `devbox run check`: Devbox未導入のため未実行

残るgateは、Devboxがある環境またはCIでstack先端の `devbox run check` を通すこと。通過後に #3、#4、#5 の順でmergeする。

`codex/monitor-saitousan-docs-issues-20260611` branchはPR #12の前身であり、内容はPR #12に包含される。PR #12 merge後に削除候補とする。

## IssueからADRへの対応

| Issue | ADR | Status | ADR judgment |
| --- | --- | --- | --- |
| #1 YouTube Comment | ADR-0005 | Proposed | 既存ADRで対応済み。映像bridge成立後のbeta、確認付き転送を維持 |
| #6 YouTube一次配信元の再評価 | ADR-0009 | Proposed | Phase 0〜2はYouTubeまたは固定映像を維持。自前配信起点は実測後に再評価 |
| #7 CLI/gRPC主導線 | ADR-0010 | Proposed | UI先行を避け、CLI + protoを初期制御面の第一候補にする |
| #8 OTPログイン | ADR-0011 | Proposed | OTP取得は初期PoCで人手gate。`login start` / `login complete` を分離 |
| #9 APK取得経路 | ADR-0012 | Proposed | 検証済みAPK/XAPK artifactを優先。ただし出所、版、SHA256、利用条件を記録 |
| #10 固定配信時間 | ADR-0013 | Proposed | 目標時間を固定枠へ内部変換。60分超と自動再開は初期PoC外 |
| #11 Android/Appium MCP | ADR-0014 | Proposed | Appium MCPを探索・PoC補助の第一候補にし、正式制御面はCLI + protoに保つ |
| #13 配信開始設定 | ADR-0015 | Proposed | 画面操作より先に型付きCLI/API契約とvalidationを定義 |
| #14 ホームから中継設定画面 | ADR-0016 | Proposed | 設定画面到達までを独立PoC境界にする。selector実測はvalidation logへ |
| #15 初回起動とアカウント切替 | ADR-0017 | Proposed | OTP本体とpre-login stateを分離 |
| #16 同一アカウント衝突 | ADR-0018 | Proposed | 配信系jobはaccount単位で直列化し、overrideは初期段階で禁止 |
| #17 EC2 Runtime Host | ADR-0008 | Proposed | 既存ADRで対応済み。nested virtualization対応familyとGPU/KVM責務を分離 |

全IssueにADR上の対応先がある。Issue #13〜#15は実装taskの要素も強いが、ADRでは契約・責務境界・PoC範囲だけを決め、画面selectorや実測値は `research/validation-log.md` へ残す。

## Dependency order

実行順はADR番号順と完全には一致しない。次のgate順で進める。

1. ADR-0009: 配信sourceの境界を固定
2. ADR-0010、ADR-0011、ADR-0012、ADR-0018: 制御面、認証、artifact、排他制御のfoundation
3. ADR-0017: pre-login stateを整理
4. ADR-0014、ADR-0016: direct Appium baseline、探索補助、設定画面到達
5. ADR-0013、ADR-0015: 時間変換と配信開始契約
6. ADR-0002 Phase 1/2: 映像入力とYouTube入力を実測
7. ADR-0005: コメントbridge beta
8. ADR-0008: local PoC成立後に短時間EC2検証

## Acceptance gate

すべての新規判断は `Proposed` のままにする。次を満たしたADRだけ、人間の明示承認後に `Accepted` へ変更する。

- 関連する前段ADRが矛盾していない
- Validation Planのruntime checkが通る
- 規約、第三者情報、認証情報のgateが確認される
- side effectを伴う配信、投稿、cloud起動は明示承認される
