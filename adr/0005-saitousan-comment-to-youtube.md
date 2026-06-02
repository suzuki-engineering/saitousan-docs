# ADR-0005: 斉藤さんコメントを名前付きでYouTubeへフィードバックする

## Status
Proposed

## Context
Issue #1 では「斉藤さんのコメントを名前付きでYouTubeにフィードバックしたい」とされている。

ADR-0002では、YouTube Liveを一次配信元にして、その映像を斉藤さんLIVEへ入力する構成を採用候補にしている。この構成では映像の流れは YouTube -> 斉藤さんLIVE だが、コメントや反応は斉藤さんLIVE側に閉じるため、YouTube側の視聴者やアーカイブには残らない。

やりたいことは、斉藤さんLIVE側で発生したコメントを、投稿者名または表示名付きでYouTube Live Chatへ投稿し、YouTube側にも会話の流れを残すことである。

ただし、コメントと名前は第三者情報になり得る。YouTubeへ転送すると、斉藤さんアプリ内だけの発言が外部プラットフォームに複製・保存・公開される可能性がある。そのため、技術方式より先に、同意、公開範囲、保存期間、規約、モデレーションの扱いを決める必要がある。

## Decision
初期方針として、斉藤さんコメントのYouTube転送は「自動転送」ではなく「オペレーター確認付き転送」として検討する。

PoCでは次の範囲に限定する。

- コメント取得は画面OCRまたは手動入力で代替し、非公式API解析はしない。
- YouTubeへの投稿はYouTube Data APIの `liveChatMessages.insert` を使う候補とする。
- 投稿前に管理画面またはローカルツールで内容を確認できるようにする。
- 投稿フォーマットは `表示名: コメント本文` を基本にする。
- 実ユーザーのコメントを公開YouTubeへ転送する検証は、同意と規約確認が済むまで行わない。

このIssueは、ADR-0002の本体機能ではなく、成立後に追加する「コメントブリッジ」機能として扱う。ADR-0002のPhase 0/1で映像入力の成立を確認するまでは、本格実装に進めない。

## Proposed Architecture

```text
Saitousan app screen
        |
        v
comment capture
  - manual input for first PoC
  - OCR/screen parsing candidate
        |
        v
operator review queue
        |
        v
YouTube Data API
        |
        v
YouTube Live Chat
```

将来の管理画面を含める場合は次の構成にする。

```text
Android runtime / Saitousan app
        |
        +--> screenshot / UI capture
        |
        v
comment extractor
        |
        v
moderation and consent filter
        |
        v
admin UI review
        |
        v
YouTube liveChatMessages.insert
```

## Goals

- 斉藤さんLIVE側のコメントや反応を、YouTube側の配信文脈にも残す。
- YouTubeアーカイブを見返した時に、斉藤さん側で何が起きていたか分かるようにする。
- 投稿者名または表示名を付けて、コメントの発言者が分かる形にする。
- 初期PoCでは、規約・同意・プライバシーリスクを抑えるため、手動確認を必須にする。

## Non-Goals

- 斉藤さんの非公式APIや通信プロトコルを解析してコメントを直接取得すること。
- 第三者のコメント、名前、プロフィール情報を同意なくYouTubeへ公開すること。
- スパム、誹謗中傷、個人情報を自動的にYouTubeへ投稿すること。
- ADR-0002の映像ブリッジ成立前に、本番品質のコメント連携を作ること。

## Consequences

YouTube側にコメント文脈を残せるため、アーカイブや切り抜きで状況を理解しやすくなる。

YouTube Live Chatの通常コメントとして投稿できれば、アーカイブやチャットリプレイにも残る可能性がある。ただし、YouTube APIの権限、レート制限、ライブチャットIDの取得、配信状態による投稿可否を確認する必要がある。

一方で、第三者情報の外部転送リスクが大きい。コメント本文だけでなく、表示名も個人情報または識別情報になり得る。自動転送にすると、不適切発言、個人情報、相手が外部公開を想定していない発言まで保存される可能性がある。

そのため、初期段階ではオペレーター確認、匿名化、転送対象の限定、テスト素材での検証を必須にする。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| 手動でYouTubeチャットへ投稿する | 実装不要、リスクを人間が判断できる | 運用負荷が高い、遅延する | 初期運用の基準として採用 |
| 手動入力フォームから投稿する | YouTube APIのPoCがしやすい、確認導線を作れる | コメント取得は自動化されない | 最初のPoC候補 |
| OCRで画面上のコメントを取得する | アプリ改造なしで取得できる可能性がある | 誤認識、名前と本文の分離、重複排除が難しい | 映像ブリッジ成立後に検証 |
| Appium/UIツリーからコメントを読む | OCRより構造化される可能性がある | アプリのUI実装次第、取得できない可能性がある | Phase 0の結果次第 |
| 非公式API解析で取得する | 精度が高い可能性がある | 規約・保守・アカウント停止リスクが高い | 不採用 |
| 自動で全コメントをYouTubeへ転送する | 低遅延、運用が軽い | プライバシー、モデレーション、同意リスクが大きい | 初期段階では不採用 |

## Open Questions

- 斉藤さんLIVEのコメント欄に、表示名と本文がどのような形式で表示されるか。
- Appiumからコメント要素を取得できるか。取得できない場合、OCRで十分な精度が出るか。
- YouTube Live Chatへ投稿するアカウントは、配信者本人アカウントか、専用Botアカウントか。
- YouTube APIの投稿レート制限は、想定コメント量に耐えられるか。
- コメント投稿者から、YouTubeへの転送・保存について明示的な同意を取れるか。
- 表示名をそのまま出すか、匿名化して `Saitousan user` のようにするか。
- 不適切発言、個人情報、URL、電話番号などを投稿前にどう検出・停止するか。
- YouTubeのチャットリプレイやアーカイブに、Bot投稿がどのように残るか。

## Validation Plan

### Phase A: Manual YouTube Chat Posting PoC

1. テスト用のYouTube Liveを限定公開または非公開で作成する。
2. YouTube Data APIでLive Chat IDを取得する。
3. 手動入力した `表示名: コメント本文` をLive Chatへ投稿する。
4. OAuthスコープ、quota、レート制限、表示遅延、アーカイブへの残り方を確認する。

Success criteria:

- API経由でYouTube Live Chatへ投稿できる。
- 投稿が配信画面とアーカイブで確認できる。
- 投稿失敗時のエラー内容をログに残せる。

### Phase B: Operator Review PoC

1. ローカルフォームにコメント候補を入力する。
2. 投稿前に内容を確認し、送信または破棄を選べるようにする。
3. 個人情報らしき文字列やURLを警告する。

Success criteria:

- オペレーターが確認してから投稿できる。
- 誤投稿を防ぐ破棄導線がある。
- 投稿ログに、元コメント、投稿本文、投稿時刻、結果が残る。

### Phase C: Comment Capture Spike

1. 斉藤さんアプリのコメント表示をスクリーンショットで取得する。
2. Appium UIツリーまたはOCRで、表示名と本文を抽出できるか確認する。
3. 同じコメントを二重投稿しないための識別方法を検討する。

Success criteria:

- テストコメントから表示名と本文を分離できる。
- 5分間のテストで重複投稿を抑制できる。
- 誤認識時に投稿前レビューで止められる。

## Risk Notes

- プライバシーリスク: 表示名、コメント本文、プロフィール情報が外部公開される可能性がある。
- 同意リスク: コメント投稿者がYouTubeへの転送を想定していない可能性がある。
- モデレーションリスク: 不適切発言や個人情報をYouTubeへ投稿してしまう可能性がある。
- 規約リスク: 斉藤さん側の画面取得、自動操作、コメント転送が禁止されている可能性がある。
- 技術リスク: OCRやUI取得はアプリ更新で壊れやすい。
- 運用リスク: Botアカウントの権限、API quota、投稿失敗時の復旧が必要になる。

## Compliance Gate

PoCから実ユーザーコメントの転送へ進む前に、次を確認する。

- 斉藤さん側の利用規約で、コメントの外部転送、画面取得、自動操作が禁止されていないか。
- YouTube側の規約で、Bot投稿、代理投稿、チャット自動化が問題ないか。
- コメント投稿者に、YouTubeへ転送されることを事前に明示できるか。
- 表示名を出す場合、本人が外部公開に同意しているか。
- 個人情報、不適切発言、URLなどを投稿前に止める運用があるか。
- 投稿ログに個人情報を保存する場合、保存期間と削除手順を決めているか。

このゲートを通るまでは、実ユーザーの名前付きコメントを公開YouTubeへ自動転送しない。

## First Task

最初に手をつける作業は、斉藤さんアプリからコメントを取ることではなく、YouTube Live Chatへ安全に投稿できる最小PoCにする。

やること:

1. テスト用YouTube Liveを用意する。
2. YouTube Data APIの認証方式と必要スコープを確認する。
3. `表示名: コメント本文` の固定テキストをLive Chatへ投稿する。
4. 投稿結果、レート制限、アーカイブへの残り方を記録する。
5. 実ユーザーコメントを扱う前に、同意と匿名化方針を決める。

## Notes

Issue: https://github.com/ioComk/saitousan-docs/issues/1

References:

- YouTube Live Streaming API `liveChatMessages.insert`: https://developers.google.com/youtube/v3/live/docs/liveChatMessages/insert
- YouTube Live Streaming API `liveChatMessages.list`: https://developers.google.com/youtube/v3/live/docs/liveChatMessages/list

このADRは、コメント連携の検討を開始するためのもの。採用判断は、ADR-0002の映像ブリッジPoCと、YouTube Live Chat投稿PoCの結果を見てから行う。
