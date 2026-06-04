# ADR-0006: クラウドコストは段階的PoCの成立後に拡大する

## Status

Proposed

## Context

ADR-0002では、YouTube Liveまたはテスト映像をAndroid実行環境へ入力し、斉藤さんLIVEへ流すラッパー構成を採用候補としている。

ただし、現時点で最も不確実なのはクラウド構成ではなく、次のローカルPoC項目である。

- Android EmulatorまたはAndroid実機で斉藤さんアプリが起動するか。
- 配信開始直前またはカメラプレビューまで到達できるか。
- Appiumで最低限の画面操作・状態取得ができるか。
- Android側のカメラ入力を固定動画または仮想カメラで差し替えられるか。
- 映像・音声・遅延・安定性が許容できるか。

一方で、AWS上でAndroid Emulator、Appium、FFmpeg、仮想カメラ、Next.js管理画面を早期に構築すると、EC2 GPU、Windowsインスタンス、EBS、CloudWatch Logs、S3、Secrets Manager、NAT Gatewayなどのコストが先行して発生する。

特にAndroid Emulatorや映像変換をクラウドで安定稼働させる場合、GPU/高性能インスタンスやWindows GUI環境が必要になる可能性があり、常時稼働すると月額コストが大きくなる。

## Decision

クラウドコストは、PoCフェーズの不確実性が解消されるまで最小化する。

現時点では、Phase 0〜1をローカル中心で進め、AWS常時稼働、Next.js管理画面、API Gateway、SQS、Secrets Manager、NAT Gateway、ECS常時ワーカーは導入しない。

推奨する段階的方針は次の通り。

| Phase | 対象 | クラウド方針 | 月額目安 |
| --- | --- | --- | ---: |
| Phase 0 | Android起動、ログイン/画面到達、Appium疎通 | ローカルのみ | 0円 |
| Phase 1 | 固定動画/仮想カメラ入力 | ローカルのみ | 0円〜数百円 |
| Phase 2 | YouTube Liveまたはtest HLS入力、遅延・音声検証 | 原則ローカル。必要なら少量ログ保存 | 0円〜5,000円 |
| Phase 3 | Appium/FFmpeg開始停止、ログ・スクリーンショット保存 | 短時間VMまたは軽量ストレージのみ検討 | 5,000円〜30,000円 |
| Phase 4 | リモートホスト、AWS実行環境、管理UI | 必要時だけ起動する最小EC2から開始 | 30,000円〜100,000円+ |

AWSを使う場合の最初の構成は、必要時だけ起動するEC2 1台に限定する。

```text
EC2 1台
  - Android Runtime
  - Appium
  - FFmpeg / media bridge
  - ログは最小限
  - 検証終了後に停止
```

初期段階では次を避ける。

- EC2の24時間常時稼働
- NAT Gateway
- フルNext.js管理画面
- API Gateway / SQS / ECSの早期導入
- 大量スクリーンショットや録画artifactの長期保存
- 本番アカウント・公開配信前提の自動化

## Consequences

良くなること:

- 技術的に成立するか分からない段階でクラウド費用を先払いしなくて済む。
- Android Emulator、Appium、カメラ入力差し替えという最大リスクに集中できる。
- AWS構成を作る前に、必要なインスタンスタイプ、ログ量、稼働時間、復旧要件を実測できる。
- 規約・公開配信・第三者情報・アカウント停止リスクをローカル/非公開検証で先に確認できる。

難しくなること:

- Phase 0〜2ではリモート運用や管理画面の検証は進まない。
- ローカルPC環境に依存する検証結果が増える。
- クラウド上でのGPU/仮想化/音声入力/復旧性の問題はPhase 4まで確定しない。

リスク:

- ローカルPoCが通っても、AWS上のAndroid Runtimeで同じように動くとは限らない。
- Phase 4に入ると、EC2 GPU/Windows/高性能インスタンスの費用が急に増える可能性がある。
- スクリーンショットやログに個人情報が含まれる場合、保存コストだけでなくプライバシーリスクも発生する。

## Alternatives Considered

- 最初からAWSフル構成を作る:
  - Pros: 将来の本番構成に近い形で検証できる。
  - Cons: Android入力差し替えが失敗した場合、クラウド構成の投資が無駄になる。EC2 GPU/Windows/NAT/監視/管理画面のコストが先行する。
  - Judgment: 不採用。

- EC2 1台で早期にリモートPoCする:
  - Pros: クラウド実行環境の制約を早く確認できる。
  - Cons: ローカルでアプリ起動・Appium・カメラ入力が未確認のままだと、問題の切り分けが難しい。
  - Judgment: Phase 2以降の候補として保持。

- ローカルPoCのみで進める:
  - Pros: 最小コストで最大不確実性を検証できる。
  - Cons: リモート運用性、復旧、自動停止、クラウドコストの実測は後回しになる。
  - Judgment: Phase 0〜1の採用方針。

- 管理画面を先に作る:
  - Pros: 操作イメージを早く確認できる。
  - Cons: 映像入力・Android実行・Appiumが成立しない場合、UI実装が不要になる。
  - Judgment: 不採用。Phase 1またはPhase 2の成功後に再検討する。

## Cost Controls

Phase 3以降でクラウドを使う場合は、最低限次を入れる。

- EC2には `owner`、`purpose`、`phase`、`expire_at` タグを付ける。
- 検証用EC2は2〜4時間の自動停止を設定する。
- AWS Budgetsまたは請求アラートを設定する。
- NAT Gatewayを初期構成に入れない。
- CloudWatch Logs、S3 artifact、スクリーンショットは7〜30日で削除する。
- 録画artifactは必要なものだけ保存する。
- secrets、Cookie、配信キー、アカウント情報をコードやログに残さない。
- 公開配信、本番アカウント、自動投稿、第三者情報を含む検証は人間承認と規約確認後に限定する。

## Notes

関連ADR:

- `adr/0002-youtube-to-saitousan-live-wrapper.md`
- `adr/0004-saitousan-live-to-youtube-mirror.md`

関連アーキテクチャメモ:

- `architecture/aws-youtube-to-saitousan-live.md`

次の作業:

1. Phase 0をローカルで実行する。
2. 結果を `research/validation-log.md` に記録する。
3. Phase 1が成功したら、短時間EC2検証の具体的なインスタンス候補と起動停止手順をADRまたはarchitecture noteに追加する。
