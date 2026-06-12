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
- `ADR-0008`: OTPログインは初期段階では人手ゲートとして扱う
- `ADR-0009`: 初期PoCのアプリ導入はPlay Storeより検証済みAPK系artifactを優先する
- `ADR-0010`: 配信時間入力は目標時間にし、固定枠選択は内部で吸収する
- `ADR-0011`: ADR-0002の一次配信元は当面YouTubeを維持する
- `ADR-0012`: 開発初期の主導線はUIではなくCLIとprotoにする
- `ADR-0013`: Android向けエージェント操作の初期検証はAppium MCPを第一候補にする

## Local Usage
MarkdownファイルをエディタまたはGitHub上で読む。
