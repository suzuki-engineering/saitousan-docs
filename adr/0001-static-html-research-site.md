# ADR-0001: 調査結果サイトを静的HTMLで管理する

## Status
Accepted

## Context
斉藤さん / 斉藤さんLIVE について、バックエンド、サーバー、インフラ観点の調査結果をローカルで見られる形にしたい。

現時点では、頻繁なデータ更新、ログイン、検索、DB保存、管理画面などは不要。まずは調査内容を読みやすく整理し、出典と推定を分けて確認できることが重要。

## Decision
調査結果は `index.html` の静的HTMLとして `Desktop/saitousan/` に配置する。

ADRは `Desktop/saitousan/adr/` にMarkdownで保存し、今後の設計判断を時系列で残す。

## Consequences
静的HTMLなので、ブラウザで直接開ける。サーバーやビルド環境が不要で、ファイル単体でも扱いやすい。

一方で、ページ数が増えたり検索・タグ・更新履歴・共同編集が必要になった場合は、静的サイトジェネレーターや小さなWebアプリへの移行を検討する必要がある。

## Alternatives Considered
- Markdownのみで管理: 書くのは速いが、閲覧体験や表組みの見やすさが弱い。
- React/ViteなどでWebアプリ化: 拡張性はあるが、現段階では実装と運用が重い。
- Google Docs等で管理: 共有はしやすいが、ローカル成果物としての扱いやすさは下がる。

## Notes
- 対象HTML: `Desktop/saitousan/index.html`
- 次にADR化するとよい候補: 出典管理方法、ページ分割方針、調査対象の追加方針。
