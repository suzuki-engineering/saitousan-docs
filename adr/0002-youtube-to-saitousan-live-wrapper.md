# ADR-0002: YouTube配信を斉藤さんLIVEへ中継するラッパー構成

## Status
Accepted

## Context
斉藤さんLIVEは、配信中の面白いシーンを保存・再利用する手段が弱く、現状は画面録画に頼る必要がある。

一方で、YouTube Liveで配信すれば録画、アーカイブ、切り抜き、共有、分析が使える。理想は「YouTubeで配信したら、その映像が自動的に斉藤さんLIVEにも流れる」状態を作ること。

想定している実現方法は次の通り。

- Android SDK / Emulator 上で斉藤さんアプリを動かす
- Appiumでアプリ操作を自動化する
- EC2上でAndroid実行環境をホストする
- Next.jsで操作用UI、状態確認、ジョブ管理を作る
- Android側のカメラ入力をYouTube配信映像に差し替える

## Decision
初期検討では、YouTube Liveを一次配信元とし、Android実行環境上の斉藤さんアプリへ映像入力する「ラッパー方式」を採用候補にする。

ただし、最初からEC2常時稼働やNext.js管理画面まで作らない。最初のPoCは、ローカルPC上で「Android実行環境に任意の映像をカメラ入力として渡し、斉藤さんLIVEの配信画面で認識されるか」を検証する。

ADR-0004の逆方向案は検討のみとし、実装ルートにはしない。目的は「斉藤さんLIVEを録画すること」ではなく、「YouTubeで配信した映像を斉藤さんLIVEにも流すこと」だからである。

構成は次を基本案とする。

- 配信元: YouTube Live
- 中継/制御: Next.js管理画面
- 自動操作: Appium
- 実行環境: EC2上のAndroid Emulatorまたは実機相当環境
- 入力変換: YouTube映像をAndroid仮想カメラ/カメラ入力へ流し込む
- 出力先: 斉藤さんLIVE

## Goals
- YouTube Live側に録画・アーカイブを残しながら、同じ映像を斉藤さんLIVEへ流す。
- 斉藤さんアプリ本体や通信プロトコルを改造・解析せず、外側から操作する。
- 配信開始、停止、状態確認、復旧を将来的に管理画面から扱えるようにする。
- 最初のPoCでは、技術的に最も不確実な「Androidカメラ入力差し替え」を検証する。

## Non-Goals
- 斉藤さんの非公式APIを解析して直接配信すること。
- 視聴者コメント、ギフト、ランキングなどの斉藤さん内部機能を再実装すること。
- 初期段階で完全自動の本番運用を作ること。
- 規約確認なしに公開運用すること。

## Proposed Architecture

```text
YouTube Live / test video
        |
        v
stream fetch / transcode
        |
        v
virtual camera / Android camera input
        |
        v
Android Emulator or Android device
        |
        v
Saitousan app
        |
        v
Saitousan LIVE
```

将来の管理系は次の構成を想定する。

```text
Next.js admin UI
        |
        v
job/controller API
        |
        +--> Appium: app launch, login check, start live, stop live
        +--> stream worker: YouTube input, transcode, health check
        +--> Android host: emulator/device lifecycle
        +--> logs/metrics: status, error, screenshots, recovery events
```

## Component Responsibilities

| Component | Responsibility | First PoC Requirement |
| --- | --- | --- |
| YouTube input | YouTube Live or test streamを取得する | 固定動画またはテストHLSで代替してよい |
| Transcode worker | 入力映像をAndroid側に渡せる形式へ変換する | 低遅延よりも認識可否を優先 |
| Android runtime | 斉藤さんアプリを動かす | Emulatorで起動できるかを確認 |
| Camera injection | Androidアプリのカメラ入力を差し替える | 最重要検証項目 |
| Appium | UI操作を自動化する | 起動、画面遷移、配信開始直前まで |
| Next.js | 管理UIを提供する | PoC後まで作らない |
| EC2 | 常時稼働環境を提供する | PoC後まで使わない |

## Consequences
YouTube側に録画とアーカイブを残せるため、斉藤さんLIVE側に録画機能がなくても、面白いシーンを後から切り出せる。

斉藤さんアプリ本体を改造せず、外側から自動操作するため、既存アプリの仕様変更に追従しやすい可能性がある。

一方で、Android Emulator上で商用アプリのカメラ入力を安定して差し替える難度は高い。映像遅延、音声同期、アプリ検知、ログイン維持、BAN/規約リスク、EC2 GPU/仮想化制約が主要なリスクになる。

また、斉藤さん側の利用規約、YouTube側の規約、配信者・視聴者の同意、録画・再配信に関する法的/倫理的確認が必要。

このため、PoCは段階的に進める。規約・アカウント停止・第三者映像の扱いに関わる検証は、公開配信ではなく自分のテストアカウントとテスト素材で行う。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| 画面録画を継続する | 実装不要、規約リスクが小さい | 録画漏れ、切り抜き作業、品質、運用負荷の問題が残る | 不採用。課題解決にならない |
| Android実機をローカルPCで自動操作する | Emulatorよりアプリ互換性が高い可能性がある | 常時稼働、遠隔操作、復旧が弱い | PoC代替案として保持 |
| EmulatorをローカルPCで動かす | 検証が速く、壊しても戻しやすい | カメラ入力とアプリ互換性が不確実 | 最初のPoC候補 |
| EC2上でEmulatorを動かす | 将来の常時稼働に近い | GPU/仮想化/コスト/デバッグ難度が高い | 初手では不採用 |
| OBSで斉藤さん画面を録画/配信する | 録画問題の一部は解ける | 「YouTube配信を斉藤さんへ流す」とは逆向き | 補助策としてのみ検討 |
| 専用Androidアプリを作る | 制御しやすい | 斉藤さんLIVEへ投稿する公式APIがない限り実現性が低い | 不採用 |
| 非公式API解析 | 自動化より直接的 | 規約・保守・アカウント停止リスクが高い | 不採用 |

## Open Questions
- 斉藤さんアプリはEmulator上で起動・ログイン・配信開始できるか。
- Android Emulatorで仮想カメラ入力を斉藤さんアプリが認識するか。
- YouTube Liveの映像をどの形式で取り出すか。RTMP、HLS、YouTube Data API、yt-dlp系のどれを使うか。
- 音声も同時に斉藤さん側へ入力できるか。
- EC2でAndroid Emulatorを安定稼働できるインスタンスタイプは何か。
- 配信開始、異常検知、再起動、ログイン切れ、BAN検知をどう運用するか。
- 規約上、外部配信映像の再配信や自動操作が許容されるか。
- Android側で音声入力をどう差し替えるか。マイク入力、仮想音声デバイス、メディア音声の扱いを確認する。
- YouTube Liveの遅延を許容できるか。超低遅延設定でも斉藤さん側の体験に問題がないか。
- 自動操作が失敗した時に、配信中の画面をどう検知して安全に停止するか。

## Risk Notes
- 規約リスク: アプリの自動操作、仮想環境、再配信が禁止されている可能性がある。
- 技術リスク: Androidカメラ入力差し替えは環境依存が大きい。
- 運用リスク: 配信中にAppium、Emulator、ネットワーク、YouTube入力のどこかが落ちると復旧が難しい。
- 品質リスク: 遅延、音ズレ、フレーム落ちがユーザー体験に直結する。
- セキュリティリスク: 斉藤さんアカウント、YouTubeアカウント、配信キー、Cookie、端末認証情報の管理が必要。
- コストリスク: EC2でGPU/Android環境を常時稼働させる場合、検証段階でも費用が膨らむ可能性がある。

## Compliance Gate

PoCから公開運用へ進む前に、次を確認する。

- 斉藤さん側の利用規約で、自動操作、仮想環境、再配信、外部入力が禁止されていないか。
- YouTube側の規約で、YouTube Live映像を別プラットフォームへ同時/二次配信することが問題ないか。
- 配信者本人の映像のみを扱い、第三者の映像・音声・コメントを無断録画/再配信しない運用になっているか。
- テストアカウントでの検証に限定し、本番アカウント停止時の影響を抑えられるか。

このゲートを通るまでは、公開配信や他者を巻き込む検証を行わない。

## Validation Plan

### Phase 0: Feasibility Spike

1. ローカルPCでAndroid Emulatorに斉藤さんをインストールし、起動できるか確認する。
2. ログイン、配信開始画面、カメラプレビュー画面まで手動で到達できるか確認する。
3. Appiumで起動、主要ボタン検出、画面遷移の最低限を自動化できるか確認する。

Success criteria:

- Emulator上で斉藤さんがクラッシュせず起動する。
- 配信開始直前のカメラプレビューまで到達できる。
- Appiumから最低限の画面要素を操作できる。

### Phase 1: Camera Injection PoC

1. YouTubeではなく固定動画を入力にする。
2. Android Emulatorのカメラ入力に固定動画または仮想カメラを接続する。
3. 斉藤さんのカメラプレビューでその映像が表示されるか確認する。
4. 可能なら短時間の非公開/テスト配信で映像が出るか確認する。

Success criteria:

- 斉藤さんアプリ内のカメラプレビューに任意映像が表示される。
- 5分以上、映像が止まらない。
- 音声なしでもよいので、映像経路の成立を確認できる。

Failure criteria:

- Emulatorが斉藤さんにブロックされる。
- カメラ入力差し替えがアプリから認識されない。
- 映像は出るが数十秒単位でクラッシュまたは停止する。

### Phase 2: YouTube Input PoC

1. YouTube LiveまたはテストHLSを入力にする。
2. 取得、変換、Android入力までの遅延を測る。
3. 音声入力の差し替え方式を検証する。
4. 10分以上の連続動作を確認する。

Success criteria:

- YouTube由来の映像を斉藤さん側の入力として表示できる。
- 10分以上、映像が止まらない。
- 遅延、音ズレ、フレーム落ちの程度を記録できる。

### Phase 3: Automation PoC

1. Appiumでアプリ起動、ログイン状態確認、配信開始、停止を自動化する。
2. 異常時にスクリーンショットとログを保存する。
3. 手動介入なしで3回連続して開始/停止できるか確認する。

Success criteria:

- 3回連続で開始/停止フローが通る。
- 失敗時にどの画面で止まったか分かるログが残る。

### Phase 4: Remote Host PoC

1. EC2または代替のリモートWindows/Linuxホストで同じ構成を動かす。
2. 費用、GPU/仮想化要件、再起動復旧、リモートデバッグを確認する。
3. Next.js管理画面はこの段階で最小実装する。

Success criteria:

- リモート環境で30分以上動作する。
- 管理画面から状態確認、開始、停止、ログ確認ができる。
- 月額運用コストの概算が出せる。

## Initial Implementation Boundary

最初に作るものは、Next.jsアプリではなくPoCスクリプトと検証メモにする。

- `poc/phase-0-emulator-check/`
- `poc/phase-1-camera-injection/`
- `research/validation-log.md`

Next.js管理画面は、Phase 1またはPhase 2で映像入力の成立が確認できてから作る。

## First Task

最初に手をつける作業は、`Phase 0: Android実行環境の成立確認` とする。

やること:

1. ローカルPCにAndroid Studio / Android SDK / Emulatorを用意する。
2. EmulatorでGoogle PlayまたはAPK経由により斉藤さんアプリを起動できるか確認する。
3. ログインまたは配信開始直前の画面まで到達できるか確認する。
4. Appiumでアプリ起動と最低限の画面要素取得ができるか確認する。
5. 結果を `research/validation-log.md` に記録する。

この段階では、YouTube入力、仮想カメラ、EC2、Next.jsは扱わない。

Phase 0の成功条件:

- Emulatorまたは代替Android実行環境で斉藤さんが起動する。
- 配信開始直前のカメラプレビュー画面まで到達できる。
- Appiumから画面要素またはスクリーンショットを取得できる。

Phase 0が失敗した場合:

- Android実機を使う代替ルートへ切り替える。
- その場合もADR-0002の目的は維持し、YouTube映像をAndroidカメラ入力へ渡す方向で検証を続ける。

## Decision Triggers

次の条件を満たしたら、このADRを `Accepted` に更新し、実装ADRへ進む。

- Emulatorまたは実機で、任意映像を斉藤さんのカメラ入力として認識できる。
- Appiumで最低限の開始/停止操作ができる。
- Compliance Gateの主要リスクに対して、公開運用可能またはテスト運用限定の判断ができる。

次の条件に該当したら、この方式を見直す。

- 斉藤さんがEmulator/自動操作/仮想カメラを明確にブロックする。
- カメラ入力差し替えが安定しない。
- 規約上、自動操作または再配信が許容できない。
- EC2/リモート運用コストが目的に対して高すぎる。

## Notes
このADRは実装開始前の技術検討から、最初の実装ルートへ昇格した。まずはPhase 0でAndroid実行環境の成立確認を行う。

AWS上で実現する場合の構成図は `architecture/aws-youtube-to-saitousan-live.md` に置く。
