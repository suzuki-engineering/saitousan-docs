# ADR-0003: HTMLを使わずMarkdownで管理する

## Status
Accepted

## Context
ADRでは、決定内容をGitで管理し、差分レビューしやすい形式にすることが重要。

以前は調査ページやADR補助UIとしてHTMLを使う案を試したが、ADR運用としてはMarkdownの方が一般的で、GitHub上でもそのまま読める。

## Decision
このドキュメント基盤では、正式な調査メモとADRをMarkdownで管理する。

`index.html` と `adr-template.html` は撤廃する。

## Consequences
Git差分が読みやすくなり、GitHub上でのレビューや編集が簡単になる。

一方で、採点UIやインタラクティブな比較画面は使わない。選択肢比較はADR本文の `Alternatives Considered` と表で表現する。

## Alternatives Considered
- HTMLで調査ページを管理する: 見た目は整えやすいが、ADRとしては差分レビューしづらい。
- HTMLでADR作成UIを作る: 入力補助にはなるが、正式な記録媒体としては過剰。
- Markdownのみで管理する: 見た目は簡素だが、GitHub/Git運用に最も合う。

## Notes
ADR-0001の「静的HTMLで管理する」判断は、このADRで上書きする。
