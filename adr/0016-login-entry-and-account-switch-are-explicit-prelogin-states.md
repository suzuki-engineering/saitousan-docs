# ADR-0016: 初回起動とアカウント切り替えはOTP本体とは別の事前状態として扱う

## Status
Proposed

## Context
Issue #15 は、初回起動時の同意画面、オンボーディング、既存アカウント継続、別アカウント選択、不具合情報送信ダイアログといった導線を、OTPログイン本体と分けて整理したいというものだ。

既存ADR-0008 では OTP 取得を `login start` / `login complete` の2段階に分け、人手ゲートとして扱う方針を採っている。しかし、アプリ起動後に必ずすぐメール入力へ入れるとは限らず、初回起動やアカウント切り替えの分岐が残る。この分岐を `login start` の内部へ無条件で埋め込むと、「なぜメール入力へ行けないか」が曖昧になる。

Issue本文が参照する既存Appium実装でも、`prepareLoginEntry`、`createSaitosanConsent`、`createSaitosanPrompts` のように、OTP本体とは別の操作群が既に分かれている。したがって、設計上も事前状態として独立させたほうが一貫する。

## Decision
初回起動とアカウント切り替えの導線は、OTPログイン本体とは別の pre-login state として扱う。

初期PoCの状態整理は次とする。

- `prepare-login-entry`: 初回起動同意、権限ダイアログ、オンボーディング、アカウント選択画面までを吸収する。
- `continue-default-account`: 既存アカウント継続導線を選ぶ。
- `choose-different-account`: 別アカウントでメールログインへ入る。
- `login start`: メールアドレス入力と確認コード送信だけを扱う。
- `login complete`: OTP入力とログイン完了確認だけを扱う。
- 不具合情報送信ダイアログは、明示設定がない限り保守的に `同意しない` を既定候補とする。

`app logout` は初期段階ではローカル状態リセット寄りの意味を維持し、アプリ内の完全なアカウント切り替え操作とは分けて記録する。

## Consequences
ログイン導線の責務が分かれ、失敗時に「OTP待ちなのか」「初回起動同意で止まったのか」「既存アカウント選択が必要なのか」を判別しやすくなる。既存のAppium helper構造とも整合するため、PoC実装と設計文書の差分が減る。

一方で、コマンド面や状態モデルは少し増える。利用者は `login` だけで全部終わる期待を持ちにくくなるが、その代わり曖昧な自動分岐を減らせる。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| pre-login state を明示分離する | 失敗原因が分かりやすい。helper構造と一致する | 操作面が少し増える | 採用 |
| `login start` に全部吸収する | 表面上は単純 | 状態曖昧。分岐失敗が追いにくい | 不採用 |
| 初回起動や切替を手動前提にする | 実装が軽い | 再現性が下がる。CI/AI運用に不向き | 初期段階では不採用 |

## Risk Notes
- 文言差分やダイアログ追加で pre-login state 判定が壊れやすい。
- `同意しない` を既定にした場合、機能差分が将来出る可能性がある。
- `app logout` の意味を曖昧にしたままだと、状態復旧時に誤解を生みやすい。

## Validation Plan

### Phase A: State Inventory

1. 初回起動、既存アカウント継続、別アカウント選択、ログイン済みの画面分岐を列挙する。
2. 各状態の入口条件と完了条件を定義する。
3. `login start` / `login complete` へ渡る前提状態を明記する。

Success criteria:

- OTP本体より前の分岐が図または表で整理される。
- 同一名称のコマンドが複数責務を持たない。

### Phase B: Flow Verification

1. 初回起動導線と別アカウント導線を少なくとも1回ずつ試す。
2. 不具合情報送信ダイアログの既定動作を記録する。
3. 既存アカウント継続導線がある状態とない状態を区別できるか確認する。

Success criteria:

- 主要な pre-login 導線で停止地点を説明できる。
- `prepare-login-entry` の完了後に、次の操作が機械的に選べる。

## Next Action
次は、pre-login state の状態遷移図を `research/` またはPoCメモに書き出し、`app logout` とアプリ内切替の差分を別途注記すること。

## Notes
関連ADR:

- `adr/0008-otp-login-is-a-human-gated-boundary.md`
- `adr/0012-cli-and-proto-first-control-surface.md`

Issue:

- https://github.com/ioComk/saitousan-docs/issues/15
