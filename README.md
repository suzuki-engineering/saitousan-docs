# saitousan-docs

斉藤さん / 斉藤さんLIVE に関する技術調査、ADR、PoC計画をMarkdownで管理するドキュメント基盤。

## Contents
- `research/`: 技術調査メモ
- `adr/`: Architecture Decision Records
- `architecture/`: 構成図とアーキテクチャメモ

## ADR Flow
1. 課題や選択肢を整理する。
2. `adr/0000-template.md` を使ってADRを書く。
3. `Status` を `Proposed` で作成する。
4. 決定後に `Accepted` へ更新する。
5. 方針変更時は既存ADRを書き換えず、新しいADRで上書き判断を残す。

## Current ADRs
- `ADR-0001`: 調査結果サイトを静的HTMLで管理する
- `ADR-0002`: YouTube配信を斉藤さんLIVEへ中継するラッパー構成
- `ADR-0004`: 斉藤さんLIVEの映像をYouTubeへミラーリングする案 rejected
- `ADR-0005`: 斉藤さんコメントを名前付きでYouTubeへフィードバックする
- `ADR-0006`: クラウドコストは段階的PoCの成立後に拡大する proposed
- `ADR-0007`: SlackとCodexを接続した開発タスク依頼・PR作成ワークフロー proposed

## Local Usage
MarkdownファイルをエディタまたはGitHub上で読む。
