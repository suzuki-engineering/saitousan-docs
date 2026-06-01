# ADR-0004: 斉藤さんLIVEの映像をYouTubeへミラーリングする案

## Status
Rejected

## Context
ADR-0002では、YouTube Liveを一次配信元にして、その映像を斉藤さんLIVEへ入力する案を検討した。

逆方向として、斉藤さんLIVEの画面を取得し、YouTubeへミラーリングまたは録画する案も考えられる。この方式なら、斉藤さん側のカメラ入力差し替えという難所を避けられる可能性がある。

ただし、斉藤さんLIVE上の映像・音声には、配信者本人だけでなく、相手ユーザー、コメント、プロフィール、通知などの第三者情報が含まれる可能性がある。YouTubeへ再配信・録画する場合は、同意、規約、プライバシー、著作権、肖像権のリスクが大きい。

## Decision
この方式は、技術検討のみで止める。実装ルートとしては採用しない。

理由は、今回の主目的が「斉藤さんLIVEの録画」ではなく、「YouTubeで配信した映像を斉藤さんLIVEにも流すこと」だからである。

加えて、斉藤さんLIVEをYouTubeへミラーリングする方式は、第三者映り込み、無断録画、再配信、個人情報露出のリスクが高い。

## Proposed Architecture

```text
Android device / Emulator
        |
        v
Saitousan app / Saitousan LIVE screen
        |
        v
screen capture + audio capture
        |
        v
OBS / FFmpeg / capture worker
        |
        v
YouTube Live or local archive
```

AWSを使う場合は次の構成になる。

```text
Android Runtime Host
        |
        +--> screen capture worker
        +--> audio capture worker
        +--> Appium controller
        |
        v
FFmpeg RTMP output
        |
        v
YouTube Live

Control UI / API
        |
        +--> start capture
        +--> stop capture
        +--> save logs and screenshots
```

## Goals
- 斉藤さんLIVE側に録画機能がなくても、映像を後から見返せる状態にする。
- Androidカメラ入力差し替えを避け、画面キャプチャ中心でPoC難度を下げる。
- YouTubeのアーカイブ、切り抜き、共有、分析機能を活用できるか検証する。

## Non-Goals
- 他ユーザーの映像・音声・個人情報を無断で公開配信すること。
- 斉藤さんの通信内容や非公式APIを解析すること。
- 最初から公開YouTube Liveへ自動ミラーリングすること。

## Comparison with ADR-0002

| Item | YouTube -> 斉藤さんLIVE | 斉藤さんLIVE -> YouTube |
| --- | --- | --- |
| 主な目的 | YouTube配信を斉藤さんにも流す | 斉藤さんLIVEを録画/アーカイブする |
| 技術難度 | Androidカメラ入力差し替えが難しい | 画面キャプチャ中心なので比較的簡単 |
| 録画問題 | YouTube側に自然に残る | YouTubeまたはローカルに残せる |
| 規約/同意リスク | 再配信入力の扱いが問題 | 第三者映り込み・無断録画リスクが大きい |
| 自動化対象 | 配信開始、カメラ入力、YouTube入力 | 画面録画、音声取得、YouTube RTMP出力 |
| 初期PoC | 難しい | 比較的始めやすい |

## Technical Options

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| Android実機 + OBS画面キャプチャ | 最も分かりやすく検証が速い | 常時運用や遠隔復旧が弱い | 最初のPoC候補 |
| Android Emulator + screenrecord/FFmpeg | 自動化しやすい | アプリ互換性、音声取得が課題 | 第二候補 |
| scrcpy + OBS/FFmpeg | Android画面をPCに出しやすい | 音声、安定性、運用設計が必要 | ローカルPoC向き |
| EC2上のAndroid Runtime + FFmpeg | 将来の自動運用に近い | GPU/仮想化/音声/コストが重い | 初手では避ける |
| YouTubeではなくローカル録画 | 規約・公開リスクを下げられる | 共有や自動切り抜きは弱い | 安全な初期検証向き |

## Compliance Gate

公開YouTube配信へ進む前に、最低限次を満たす必要がある。

- 配信者本人の映像・音声のみを扱う。
- 相手ユーザー、コメント、プロフィール、通知などが映る場合は、録画/公開対象から除外するか、明示的な同意を取る。
- 斉藤さんの利用規約で画面録画、再配信、自動操作が禁止されていないか確認する。
- YouTubeの規約で、外部アプリ画面の再配信が問題ないか確認する。
- 公開配信前に、ローカル録画または非公開テストで品質とリスクを確認する。

このゲートを通るまでは、公開YouTube Liveへの自動ミラーリングは行わない。

## Validation Plan

### Phase 0: Local Recording PoC

1. Android実機またはEmulatorで斉藤さんLIVE画面を表示する。
2. OBS、scrcpy、Android screenrecord、FFmpegのいずれかで画面を録画する。
3. 5分以上、映像と音声が保存できるか確認する。

Success criteria:

- 映像が5分以上止まらず録画できる。
- 音声が必要な品質で録れる、または音声取得が課題として明確になる。
- 個人情報や第三者情報を映さないテスト手順を作れる。

### Phase 1: Private YouTube Output PoC

1. OBSまたはFFmpegからYouTubeの非公開/限定公開LiveへRTMP出力する。
2. 遅延、解像度、音ズレ、フレーム落ちを確認する。
3. YouTube側にアーカイブが残るか確認する。

Success criteria:

- YouTubeに非公開/限定公開で10分以上配信できる。
- アーカイブが残り、後から切り抜き可能な品質で確認できる。
- 配信停止と復旧手順が分かる。

### Phase 2: Automation PoC

1. AppiumまたはADBでアプリ起動と画面状態確認を自動化する。
2. FFmpeg/OBSの開始停止をスクリプト化する。
3. 失敗時にログ、スクリーンショット、録画断片を保存する。

Success criteria:

- 手動介入なしで録画開始/停止を3回連続で実行できる。
- 失敗時に原因調査できるログが残る。

## Risks
- 第三者の映像・音声を無断でYouTubeへ配信してしまうリスクが高い。
- 通知、プロフィール、コメントなどの個人情報が画面に映る可能性がある。
- 音声取得はAndroidの制約やアプリ仕様により不安定になる可能性がある。
- YouTubeアーカイブが残るため、削除漏れや公開範囲設定ミスの影響が大きい。
- 画面キャプチャは実装しやすいが、公開運用のリスクはADR-0002より大きい可能性がある。

## Open Questions
- 斉藤さんLIVE画面に第三者情報がどの程度表示されるか。
- 配信者本人だけの画面に限定できるUI/運用があるか。
- Android実機で音声込みの安定キャプチャが可能か。
- YouTubeではなくローカル録画だけで課題を十分解決できるか。
- 斉藤さんLIVEの規約上、画面録画と再配信が許容されるか。

## Notes
この方式は、技術的にはADR-0002より早く検証できる可能性がある。一方で、公開YouTube Liveへ流す場合のコンプライアンスリスクは高い。

検討結果として、実装はADR-0002を優先する。
