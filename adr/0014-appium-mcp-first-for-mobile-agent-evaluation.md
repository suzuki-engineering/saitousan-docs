# ADR-0014: Android向けエージェント操作の初期検証はAppium MCPを第一候補にする

## Status
Proposed

## Context

Issue #11 は、Playwright MCP のように AI エージェントから扱いやすい操作面を Android / Appium でも持てるかを問うている。

このリポジトリの既存方針では、まず ADR-0002 の Phase 0/1 で Android 実行環境、アプリ起動、ログイン導線、最低限の操作、映像入力差し替えの成立可否を確かめる必要がある。また ADR-0010 では、製品側の正式な制御面は CLI と proto を主導線にする案を提示している。

一方で、調査や PoC の現場では、AI エージェントや人手オペレーターが Android 画面を探索し、スクリーンショット、要素探索、tap/type、画面遷移を素早く検証できる補助操作面があると、Appium スクリプトを毎回手書きするより反復が速い可能性がある。

2026-06-27 時点の Appium 公式ドキュメントでは、`appium-mcp` はAppium teamが保守するOfficial Toolとして掲載され、`npx appium-mcp@latest` と `ANDROID_HOME` を用いる MCP client 設定例が案内されている。Android 自動化では、Appium 本体に加えて Android SDK、`adb`、JDK、UiAutomator2 driver などの前提も必要であり、ブラウザ向けの Playwright MCP より環境依存が大きい。

したがって今必要なのは、「モバイル操作MCPを正式採用するか」ではなく、「最小検証で最も妥当な第一候補は何か」と「どの時点で不採用または代替候補へ切り替えるか」を先に記録することである。

## Decision

初期検証では、Android 向けエージェント操作面の第一候補を `appium/appium-mcp` にする。

ただし、これは製品の正式制御面を MCP にする決定ではない。位置づけは次の通りとする。

- 正式な制御面: ADR-0010 の通り CLI + proto を第一候補にする。
- Appium MCP: 調査、探索、PoC、画面要素確認、最小操作検証の補助ツールとして使う。
- 代替候補比較: 第一候補が安定しない場合のみ `@gavrix/appium-mcp` などを同条件で比較する。
- 直接 Appium baseline: MCP の可否とは別に、`appium` + `uiautomator2` + `adb` でセッション作成できることを最低基準にする。

初期評価の判断基準は次とする。

| Check | 合格条件 | 不合格時の扱い |
| --- | --- | --- |
| 環境前提 | `adb devices`、Appium本体、UiAutomator2 driver が揃う | MCP以前に Android/Appium 基盤課題として切り分ける |
| セッション作成 | Android emulator または実機に接続し Appium session を張れる | まず direct Appium を修復する |
| 最低限操作 | screenshot、要素探索、tap、type、画面遷移確認ができる | MCP候補の継続可否を再評価する |
| コンテキスト量 | UIツリー取得が実用範囲の速度と token 量に収まる | 必要に応じて screenshot/OCR 主体へ寄せる |
| 再現性 | 同じ画面で手順を繰り返しても大きくぶれない | 代替 MCP または直書き Appiumへ切り替える |

## Consequences

良くなること:

- Appium スクリプトを毎回書かずに、画面探索と最小操作の当たりを早く付けられる。
- ADR-0002 の Phase 0 で必要な「起動できるか」「押せるか」「状態が読めるか」を AI 補助で反復しやすくなる。
- 公式ドキュメントに載っている候補から先に検証するため、選定理由を説明しやすい。

難しくなること:

- Appium MCP が使えても、製品の正式 API や CLI 設計が固まるわけではない。
- モバイル UI ツリーはブラウザより大きくなりやすく、 token 消費や応答速度の揺れが出やすい。
- Appium、Android SDK、JDK、driver、emulator 実機差分といった前提が多く、セットアップ不具合の切り分けが必要になる。

リスク:

- `appium/appium-mcp` が探索用途には便利でも、長いシナリオや安定運用には不十分な可能性がある。
- MCP 操作に依存しすぎると、後で CLI + proto の正式制御面と責務が混ざる。
- UI ツリー取得やスクリーンショットが第三者情報を含む場合、ログや artifact の保存方針に注意が必要になる。

## Alternatives Considered

| Option | Pros | Cons | Current Judgment |
| --- | --- | --- | --- |
| `appium/appium-mcp` を第一候補にする | Appium 公式 docs で案内されている。MCP client から使いやすい | 実運用安定性は環境依存。 token 消費も未知数 | 初期検証で採用候補 |
| `@gavrix/appium-mcp` を第一候補にする | 軽量比較候補として使える | 現時点では本リポジトリ上の第一根拠が弱い | 代替比較候補 |
| MCPを使わず direct Appium だけで進める | 依存が少ない。最終的な自動化基盤に近い | 探索速度が落ちやすい。AI補助との相性が弱い | baselineとして併用 |
| 先に管理UIを作る | 人間向けの見た目は整う | Phase 0 の不確実性解消に直結しない | 不採用 |

## Validation Plan

### Phase A: Direct Appium Baseline

1. `appium` を起動できることを確認する。
2. `appium driver install uiautomator2` が通ることを確認する。
3. `adb devices` で emulator または実機が見えることを確認する。
4. direct Appium session を 1 回張り、スクリーンショット取得まで到達する。

Success criteria:

- MCPを使わなくても Appium session が成立する。
- Android 側の前提不足と MCP 固有問題を分離できる。

### Phase B: Appium MCP Minimum Flow

1. MCP client に `npx appium-mcp@latest` を追加する。
2. `ANDROID_HOME` を明示し、必要なら `JAVA_HOME` も固定する。
3. デバイス選択、セッション作成、スクリーンショット取得、tap/type、簡単な画面遷移を確認する。
4. UI ツリー取得時の応答速度と token 量を記録する。

Success criteria:

- 画面探索と最小操作が direct Appium より速く、十分安定している。
- 失敗時に direct Appium へ切り戻して原因を切り分けられる。

### Phase C: Comparative Fallback

1. `appium/appium-mcp` が不安定なら、同じ端末・同じ画面で `@gavrix/appium-mcp` を比較する。
2. それでも不十分なら、MCP常用を見送り、PoC は direct Appium + 補助スクリプトへ戻す。

Success criteria:

- 第一候補の継続、代替採用、MCP見送りのどれかを明確に判断できる。

## Next Action

次は、ローカル環境で direct Appium baseline と `appium/appium-mcp` 最小導入手順を実測し、結果を `research/validation-log.md` または別メモに記録すること。

## Notes

関連ADR:

- `adr/0002-youtube-to-saitousan-live-wrapper.md`
- `adr/0010-cli-and-proto-first-control-surface.md`

Issue:

- https://github.com/suzuki-engineering/saitousan-docs/issues/11

2026-06-27 時点で確認した公式情報:

- Appium Docs, Related Tools, `Appium MCP`
  - https://appium.io/docs/en/latest/ecosystem/tools/#appium-mcp
- Appium Docs, Install Appium
  - https://appium.io/docs/en/latest/quickstart/install/
- GitHub repository, `appium/appium-mcp`
  - https://github.com/appium/appium-mcp
