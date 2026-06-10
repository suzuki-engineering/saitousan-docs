# ADR-0012: 開発初期の主導線はUIではなくCLIとprotoにする

## Status
Accepted

## Context
Issue #7 は、開発初期に管理UIを先行させるのではなく、CLIとgRPC互換API契約を主導線にすべきかを問うている。

このリポジトリの既存ADRでは、最初に解くべき問題は見た目ではなく、Android実行環境、配信開始、停止、状態確認、異常時ログ取得を再現性高く扱えることにある。特にAIやスクリプトから触る前提では、画面中心の操作面より、構造化I/Oと明示的な終了状態を持つCLIのほうが扱いやすい。

一方で、OTP入力や長時間ジョブ、失敗時の復旧など、即時レスポンス前提の単純CLIでは扱いにくい要素もある。そのため、CLIを採用する場合でも、契約、状態、出力形式を最初から整理しておく必要がある。

## Decision
開発初期の正式な操作面は、UI先行ではなくCLI先行にする。

API契約は proto を正本とし、CLIはその契約に追従する薄い制御面として設計する。管理UIは、Phase 0〜2で必要な制御パスが固まるまで補助または後続実装とする。

初期CLIの必須要件は次とする。

- 機械可読な `--output json`
- 明示的な exit code
- `status` / `start` / `stop` / `login` の分離
- 長時間ジョブの timeout と中断時の状態記録
- dry-run または validation-only モード
- スクリーンショット、ログ、実行IDの保存

## Consequences
AI、CI、手動オペレーションのいずれからも同じ制御面を使いやすくなる。契約をprotoに寄せることで、将来の別クライアントやUIを追加しても操作意味論を揃えやすい。

一方で、初期段階では操作性よりも厳密さが優先されるため、人間向けの使いやすさは限定的になる。OTP待機、配信状態監視、再実行などは、UIよりCLIのほうが利用者に制約を露出しやすい。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| CLI + proto先行 | 機械可読、再現性が高い、AI/CIと相性がよい | 対人UXは弱い | 採用 |
| Next.js UI先行 | 操作イメージを作りやすい | 実態のない画面先行になりやすい | 初期フェーズでは不採用 |
| RESTだけ先に作る | 学習コストが低い | 契約の揺れや長時間処理整理が弱い | 補助候補 |

## Risk Notes
- protoを早く固定しすぎると、PoCで必要な状態モデル変更に追従しにくい。
- CLI中心だと、OTPや対話的確認のUX設計を雑にしやすい。
- UIを後回しにすると、最終運用時の監視導線が別途必要になる。

## Validation Plan

### Phase A: Command Surface Definition

1. `install`, `login start`, `login complete`, `stream start`, `stream stop`, `status` の最小コマンド群を定義する。
2. 入力、JSON出力、主要エラーコードを文書化する。
3. 人手が必要なステップを明示する。

Success criteria:

- 主要操作がCLIサブコマンド単位で分解されている。
- コマンド結果を機械的に判定できる。

### Phase B: Long-running Flow Check

1. OTP待機や配信開始など、秒単位で終わらない処理を試験設計に落とす。
2. timeout、cancel、resume時のふるまいを定義する。

Success criteria:

- 途中失敗時に次の手順が判定できる。
- UIがなくても再実行方針が分かる。

## Next Action
次は、ADR-0002の Phase 0/1 に必要な操作だけを対象に、CLIの最小コマンド境界とJSON出力例を別メモまたはPoC仕様に落とす。

## Notes
Issue: https://github.com/ioComk/saitousan-docs/issues/7
