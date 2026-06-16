# ADR-0014: 配信開始設定は型付きCLI/API契約として先に固定する

## Status
Proposed

## Context
Issue #13 は、斉藤さんLIVEで配信開始時に設定する項目を、Appium操作だけの暗黙知にせず、CLI/API入力としてどう表現するかを問うている。

既存ADRでは、ADR-0012 が CLI + proto を初期主導線にし、ADR-0010 が配信時間を固定枠ではなく目標時間として扱う方針を採っている。一方、実際の配信開始画面では、配信種別、時間、画質、タイトル、タグ、通知先、Web公開、視聴者制限のように、配信種別ごとに有効条件が変わる項目が混在する。

この状態を画面操作へ直接押し込むと、CLI/APIでは不正な組み合わせを事前に弾けず、Appium側の失敗が契約不備なのかUI不具合なのか判別しにくい。初期PoCでは、まず入力契約を型付きで先に固定し、実機で未検証の項目は未対応として明示するほうが安全である。

## Decision
配信開始設定は、画面入力の写経ではなく型付きCLI/API契約として先に定義する。

初期契約の方針は次とする。

- `streamType` は `chat` / `camera_on` / `camera_off` / `premium` の enum にする。
- `targetDurationMinutes` は ADR-0010 に従い目標時間入力とし、通常配信3種では `30` 固定として validation する。
- `premiumQuality` は `premium` のときだけ `normal` / `high` を許可する。
- 通知先は `notifyFriends` / `notifyWatchers` / `notifyFollowers` の独立 boolean とする。
- `title` は任意文字列、`tags` は候補から選ぶ前提の配列として持つ。
- `webShareEnabled` は明示 boolean とし、初期既定値は `false` を採用候補とする。
- 視聴者制限は単一の公開範囲 enum へ潰さず、`minAccountAgeDays` と `relationshipGate` を分けて表現する。
- Appiumで未確認の項目は「契約には存在するが runtime では unsupported を返し得る」ことを許容する。

## Consequences
CLI/APIの利用者は、どの配信設定が指定可能で、どの組み合わせが不正かを事前に理解しやすくなる。Appium層は「この契約をどう画面へ反映するか」に責務を絞れるため、入力モデルとUI探索の問題を切り分けやすい。

一方で、実機確認前に契約を先行させるため、アプリUIの実態と差分が出る可能性はある。タグ候補取得や視聴者制限の同時指定可否などは、後続の検証で調整が必要になる。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| 型付きCLI/API契約を先に定義する | validationしやすい。proto化しやすい | 実機との差分調整が後で要る | 採用候補 |
| Appium画面項目をそのままCLIへ露出する | 実装が早い | UI都合が契約へ漏れる。不正組み合わせを弾きにくい | 不採用 |
| 最初はタイトルだけ扱う | PoCは軽い | 後で契約破壊的変更が増える | 初期段階では不採用 |

## Risk Notes
- `premium` 専用項目の条件分岐を曖昧にすると、無効入力が後段まで流れる。
- タグ候補が動的UI依存なら、事前validationと実行時選択の差分が出やすい。
- `webShareEnabled=false` を既定にすると、期待より公開範囲が狭くなる可能性がある。

## Validation Plan

### Phase A: Contract Draft

1. proto または仕様メモに `StartStreamRequest` 相当の構造を起こす。
2. 配信種別ごとの必須/禁止フィールドを表にする。
3. 不正組み合わせ時の validation error を定義する。

Success criteria:

- 入力スキーマだけで有効/無効の大半を説明できる。
- ADR-0010 の時間方針と矛盾しない。

### Phase B: Appium Capability Check

1. 実機またはエミュレータで各設定項目がUI上に存在するか確認する。
2. 項目ごとに `supported` / `unsupported` / `needs-discovery` を整理する。
3. unsupported 項目のエラー表現を決める。

Success criteria:

- 契約上の各フィールドに実装可否ラベルが付く。
- 未対応項目が黙って無視されない。

## Next Action
次は、配信開始設定の proto / JSON 例を別メモへ落とし、通常配信と `premium` の validation matrix を作ること。

## Notes
関連ADR:

- `adr/0010-target-duration-maps-to-fixed-live-slots.md`
- `adr/0012-cli-and-proto-first-control-surface.md`

Issue:

- https://github.com/ioComk/saitousan-docs/issues/13
