# ADR運用

このフォルダーでは、開発や調査サイト作成に関する意思決定をADRとして残す。

## 書き方
1. `0000-template.md` をコピーする。
2. 連番で `0002-title.md` のように作る。
3. `Status` は `Proposed`、`Accepted`、`Deprecated`、`Superseded` のどれかにする。
4. 決定理由だけでなく、捨てた選択肢とデメリットも書く。

## 基本フロー
1. 調査または要件を整理する。
2. 選択肢を2-3個出す。
3. ADRに決定を書く。
4. その決定に沿って実装やHTML更新を行う。
5. 方針が変わったら古いADRを書き換えず、新しいADRで上書き判断を残す。


## ADR一覧

- [ADR-0001: Static HTML Research Site](0001-static-html-research-site.md)
- [ADR-0002: YouTube配信を斉藤さんLIVEへ中継するラッパー構成](0002-youtube-to-saitousan-live-wrapper.md)
- [ADR-0004: Saitousan LIVE to YouTube Mirror](0004-saitousan-live-to-youtube-mirror.md)
- [ADR-0005: Saitousan Comment to YouTube](0005-saitousan-comment-to-youtube.md)
- [ADR-0006: クラウドコストは段階的PoCの成立後に拡大する](0006-cloud-cost-phased-poc.md)
- [ADR-0007: SlackとCodexを使った開発ワークフロー](0007-slack-codex-development-workflow.md)
- [ADR-0008: Android SDK/Emulator用EC2 Runtime Host候補とOS方針](0008-android-runtime-ec2-host-candidates.md)

## 運用ルール

- このプロジェクトで「検討して」と依頼された場合は、基本的にADRとして残す。
- まだ決定していない検討は `Status: Proposed` にする。
- ユーザーが明示的に採用を指示した、または既に合意済みの方針は `Status: Accepted` にする。
- 一時的な実験ログや実測結果はADRではなく `research/validation-log.md` に記録する。
