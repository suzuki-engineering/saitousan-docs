# ADR-0007: SlackとCodexを接続した開発タスク依頼・PR作成ワークフロー

## Status
Proposed

## Context

現在は2人で開発しているが、今後メンバーが増える可能性がある。

開発タスクの入口をSlackに寄せ、SlackのチャットやスレッドからGPT/Codexへタスクを投げ、コード修正、テスト、Pull Request作成まで進められる状態にしたい。

ただし、少人数チームでは運用が重すぎる仕組みを先に作ると、ツール管理、権限管理、レビュー漏れ、意図しない情報共有、コスト増が先行する。特にSlackの会話履歴、GitHubリポジトリ、Codex実行環境、APIキーやOAuthトークンが接続されるため、導入初期から安全な権限境界と人間レビューを前提にする必要がある。

2026-06-06時点の確認では、OpenAIのCodex Slack連携は、Slackのチャンネルまたはスレッドで `@Codex` にメンションしてCodex cloud taskを開始し、完了後に結果リンクを返す公式機能として提供されている。利用にはCodex cloud tasksのセットアップ、対応プラン、GitHub接続、環境設定が必要で、Slackワークスペースのポリシーによっては管理者承認が必要になる。

## Decision

初期導入では、独自Slack botを作らず、公式のCodex Slack連携とGitHub連携を使う。

Slackは「依頼・議論・結果通知」の入口とし、コード変更の最終確定はGitHub Pull Requestで行う。Codexが作成した差分は、必ず人間がレビューし、CIや最低限の確認を通してからマージする。

初期運用は次の方針にする。

1. Slackに開発依頼用チャンネルを作る。
   - 例: `#dev-codex` またはプロジェクト別チャンネル。
   - タスク依頼は原則スレッド単位で完結させる。
   - 最新メッセージには、目的、対象リポジトリ、期待する成果物、テスト観点、制約を書く。

2. Codex公式Slack連携を導入する。
   - ChatGPT/Codex側でGitHub接続とCodex cloud environmentを設定する。
   - SlackワークスペースにCodex appをインストールし、必要ならSlack管理者承認を受ける。
   - チャンネルに `@Codex` を追加し、メンションでタスクを開始する。

3. GitHub側にPR前提のガードレールを置く。
   - `main` または既定ブランチへの直接pushは禁止する。
   - Pull Requestレビューを必須にする。
   - 最低限のCI、lint、test、docs checkを必須ステータスにする。
   - CodexがPRを作っても、マージ権限は人間に残す。

4. タスク種別ごとにCodexへ任せる範囲を分ける。

| Task Type | Codexに任せる範囲 | 人間が確認すること |
| --- | --- | --- |
| ドキュメント追加・ADR作成 | 下書き、整形、リンク整理、PR作成 | 方針の妥当性、機密情報混入、表現 |
| 小さなバグ修正 | 原因調査、修正、テスト追加、PR作成 | 再現条件、影響範囲、テスト結果 |
| UI/文言修正 | 実装、スクリーンショット添付、PR作成 | 見た目、文言、アクセシビリティ |
| 依存関係更新 | 更新案、互換性確認、CI実行 | breaking change、セキュリティ、リリース判断 |
| 本番・課金・権限変更 | 原則Codex単独では実行しない | 人間承認、手順レビュー、ロールバック |

5. Slackに書いてよい情報を制限する。
   - APIキー、OAuthトークン、Cookie、パスワード、配信キー、個人情報を貼らない。
   - 本番ログや顧客情報を含む内容は、マスキングまたは別管理にする。
   - Codexへ渡すSlackスレッド履歴に、不要な秘密情報が含まれないようにする。

6. チームが増えたらIssue/Project管理を追加する。
   - 2人の間はSlackスレッド起点でよい。
   - 3〜5人以上になり、優先順位、担当者、期限、リリース単位の管理が必要になったら、GitHub Issues/ProjectsまたはLinear等を正式なタスク台帳にする。
   - Slackはタスク台帳ではなく、依頼・相談・通知の場に寄せる。

## Consequences

良くなること:

- Slackの会話からすぐに開発タスクを開始できる。
- 2人チームではIssue作成や細かいチケット管理の手間を減らせる。
- Codexの作業結果がPRに集約されるため、レビュー、CI、履歴管理がしやすい。
- 独自botや独自OAuth実装を持たないため、初期の実装・保守コストを抑えられる。
- 将来メンバーが増えたときも、GitHub PRベースの合流点を維持できる。

難しくなること:

- Slackスレッドだけに依存すると、タスクの一覧性、優先順位、期限管理が弱い。
- Codexがスレッド文脈を誤解する可能性があるため、依頼文の品質が成果に直結する。
- Codex cloud environment、GitHub repo map、Slack権限の設定がずれると、意図しないリポジトリや環境で実行される可能性がある。
- 公式連携の仕様、料金、利用可能プラン、管理者設定は変わり得るため、導入時に最新ドキュメント確認が必要になる。

リスク:

- Slackスレッド履歴に秘密情報が含まれると、Codexタスクに不要な情報が渡る可能性がある。
- Codexの差分を十分にレビューしないと、仕様誤解、セキュリティ問題、不要な大規模変更が混入する可能性がある。
- PR作成まで自動化すると「PRがある = 正しい」と錯覚しやすい。
- 将来人数が増えたとき、Slackだけでは意思決定やタスク状態が散らばる。

## Alternatives Considered

- 独自Slack bot + OpenAI API/Codex SDKで作る:
  - Pros: ワークフロー、承認、ログ、タスク台帳との接続を自由に設計できる。
  - Cons: Slack OAuth、トークン保管、GitHub権限、キュー、監査ログ、失敗時リトライ、プロンプトインジェクション対策を自前で持つ必要がある。
  - Judgment: 初期2人チームには重い。公式連携で不足が明確になってから再検討する。

- GitHub Issues/Projectsを必須入口にする:
  - Pros: タスク管理、担当、優先順位、履歴、検索性が強い。
  - Cons: 2人チームの初期速度が落ちる可能性がある。雑な相談や小修正までIssue化すると運用負荷が上がる。
  - Judgment: 初期は任意。人数増加またはタスク滞留が見えた時点で正式導入する。

- Codex CLIを各自ローカルで使い、Slack連携しない:
  - Pros: Slack権限やスレッド履歴共有のリスクが小さい。各自のローカル環境で完結する。
  - Cons: タスク依頼、進捗共有、PR作成までの流れが個人作業に閉じやすい。
  - Judgment: 個人作業には併用可。ただしチームの依頼入口としてはSlack連携を採用候補にする。

- Slackから直接マージまたはデプロイまで自動化する:
  - Pros: 速度は最も速い。
  - Cons: 誤操作、権限濫用、レビュー漏れ、本番事故のリスクが高い。
  - Judgment: 不採用。少なくともPRレビューとCIを通す。

## Operating Rules

### Slack依頼テンプレート

```text
@Codex
目的:
対象リポジトリ/ディレクトリ:
やってほしいこと:
やってほしくないこと:
完了条件:
確認してほしいコマンド:
PRに書いてほしい観点:
```

### PRレビュー基準

- 依頼内容と差分が一致している。
- 変更範囲が不要に広がっていない。
- テスト、lint、ビルド、またはドキュメント整合チェックが実行されている。
- 秘密情報、個人情報、不要なログ、スクリーンショットが含まれていない。
- 破壊的操作、権限変更、課金リソース作成、本番設定変更が含まれる場合は、別途人間承認がある。

### 導入ステップ

1. GitHubの既定ブランチ保護、必須レビュー、必須チェックを設定する。
2. Codex cloud tasks用のGitHub接続とenvironment/repo mapを設定する。
3. SlackワークスペースにCodex appをインストールする。
4. `#dev-codex` などの限定チャンネルで試験運用する。
5. ドキュメント修正や小さなバグ修正から開始する。
6. PR品質、レビュー時間、失敗パターン、料金を1〜2週間観察する。
7. 成果が安定したら、チャンネル、対象リポジトリ、依頼テンプレートを拡張する。

## Notes

確認した公式情報:

- OpenAI Developers: `Use Codex in Slack` では、Slackのチャンネル/スレッドで `@Codex` にメンションしてCodex cloud taskを開始し、結果をSlackへ返す流れが説明されている。利用には対応プラン、GitHub接続、Codex environmentが必要。
  - https://developers.openai.com/codex/integrations/slack
- OpenAI: `Codex is now generally available` では、Slackで `@Codex` をタグ付けすると会話文脈からCodex cloud taskを開始し、完了タスクへのリンクを返すと説明されている。
  - https://openai.com/index/codex-now-generally-available/
- Slack Developer Docs: Slack appはOAuth v2でスコープを要求し、トークンを取得する。トークンは安全に保管する必要がある。
  - https://docs.slack.dev/authentication/installing-with-oauth/
- GitHub Docs: protected branchesにより、PRへの必須レビューや必須ステータスチェックなどのルールを設定できる。
  - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

Open Questions:

- 利用するChatGPT/Codexプランと料金上限をどうするか。
- SlackでCodexを使えるメンバーを全員にするか、初期は2人に限定するか。
- Codex cloud environmentに接続するリポジトリをこのdocsリポジトリだけにするか、アプリ本体リポジトリも含めるか。
- PRレビュー必須人数を1人にするか、重要変更のみ2人にするか。
- Slack連携で完了時の回答本文を投稿するか、タスクリンクのみ投稿するか。
