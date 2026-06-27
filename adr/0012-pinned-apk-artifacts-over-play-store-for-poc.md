# ADR-0012: 初期PoCのアプリ導入はPlay Storeより検証済みAPK系artifactを優先する

## Status
Proposed

## Context
Issue #9 は、斉藤さんアプリをAndroid実行環境へ導入する際、Google Play依存を避けてAPK/XAPKを第一候補にすべきかを問うている。

Play Store経由は配布元として自然だが、Googleアカウント、Play Protect、2FA、端末認証、ストアUI変更といった外部依存が増える。PoCで確認したいのはストア操作ではなく、アプリ起動、ログイン、配信準備、Appium操作の成立可否である。

一方で、外部APK/XAPKは取得元の信頼性、改ざん、版ずれ、利用規約の確認が必要になる。このため、単に「外部サイトから落とす」ではなく、検証済みartifactとして再現性のある扱いにする必要がある。

## Decision
初期PoCでは、Google Play操作を必須要件にせず、検証済みAPK系artifactを優先する。

ただし、次の条件を満たす場合だけ許容する。

- リポジトリにはバイナリ本体を置かない
- 取得元URL、取得日、アプリ版、SHA256を記録する
- ローカルキャッシュまたは安全なartifact保管場所から再利用する
- 導入後にアプリ版を validation log に残す

Play Store経由は代替経路として保持するが、初期PoCの標準手順にはしない。

## Consequences
Android環境の成立確認に集中しやすくなり、Play StoreのUIやアカウント運用に引きずられにくくなる。PoC再現性も、artifact情報を固定すれば高めやすい。

一方で、artifact供給と検証の運用責任はこちらに残る。取得元の信頼性と利用条件を確認しない限り、安全な標準手順とは言えない。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| 検証済みAPK/XAPK artifactを使う | Googleアカウント依存を減らせる | 取得元と改ざん確認が必要 | 初期PoCで採用候補 |
| Play Storeから都度インストールする | 正規導線を使える | Googleアカウント、UI、保護機構に依存する | 代替ルートとして保持 |
| APKをリポジトリへ同梱する | 再現は簡単 | サイズ、配布権、更新管理が悪い | 不採用 |

## Risk Notes
- 非公式配布元からの取得は、改ざんや版不整合のリスクがある。
- バージョン更新でAppiumセレクタやログイン導線が壊れる可能性がある。
- Play Storeを避けても、利用規約やアプリ配布条件の確認は別途必要になる。

## Validation Plan

### Phase A: Artifact Policy Check

1. 取得元、取得日、版、SHA256を記録するための表またはメモ形式を決める。
2. 同じartifactを別端末で再利用できるか確認する。

Success criteria:

- アプリ導入元が追跡可能である。
- 同じ版を再現性高く導入できる。

### Phase B: Install Compatibility Check

1. Emulatorまたは実機へインストールする。
2. 起動可否、ログイン導線、配信画面到達可否を確認する。
3. 版更新時にどの手順を再検証するか整理する。

Success criteria:

- 導入版ごとの差分確認項目が定義される。
- Appium PoCへ進むための最小導入手順が固定される。

## Next Action
次の作業は、`research/validation-log.md` に「Saitousan app version」「artifact source」「SHA256」欄を追加し、最初に使う導入artifactの記録ルールを決めること。

## Notes
Issue: https://github.com/suzuki-engineering/saitousan-docs/issues/9

このADRはPoC導入方針の記録であり、配布元の適法性や安全性を自動的に保証するものではない。
