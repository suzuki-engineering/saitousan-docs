#!/usr/bin/env python3
"""MUSE Skill Router.

タスクに関連しそうな既存 Skill を探す軽量 helper。

通常運用では毎回自動実行せず、必要なときに明示コマンドから使う。
本流チャットに追加 context を注入したい場合だけ、JSON 出力を利用する。

Usage:
    echo "<prompt>" | python .muse/tools/skill_router.py
    python .muse/tools/skill_router.py --prompt "<prompt>"
    python .muse/tools/skill_router.py --prompt "<prompt>" --json
    python .muse/tools/skill_router.py --prompt "<prompt>" --include-quarantine
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TypedDict

from skill_policy import is_str_mapping, iter_skills, read_skill_text, score_prompt_against_text


class SkillRecord(TypedDict):
    name: str
    path: str
    root: str
    root_label: str
    trusted: bool
    text: str


class SkillMatch(TypedDict):
    name: str
    path: str
    root: str
    root_label: str
    trusted: bool
    score: float
    hits: list[str]


def load_skills(agent: str = "all", include_quarantine: bool = False) -> list[SkillRecord]:
    skills: list[SkillRecord] = []
    for skill in iter_skills(agent=agent, include_quarantine=include_quarantine):
        text = read_skill_text(skill)
        skills.append(
            {
                "name": skill.name,
                "path": skill.relative_path,
                "root": skill.root.key,
                "root_label": skill.root.label,
                "trusted": skill.root.trusted,
                "text": text,
            }
        )
    return skills


def route(
    prompt: str,
    threshold: float = 0.15,
    agent: str = "all",
    include_quarantine: bool = False,
) -> list[SkillMatch]:
    results: list[SkillMatch] = []
    for skill in load_skills(agent=agent, include_quarantine=include_quarantine):
        score, hits = score_prompt_against_text(prompt, skill["text"])
        if score >= threshold:
            results.append(
                {
                    "name": skill["name"],
                    "path": skill["path"],
                    "root": skill["root"],
                    "root_label": skill["root_label"],
                    "trusted": skill["trusted"],
                    "score": round(score, 3),
                    "hits": hits[:20],
                }
            )
    return sorted(results, key=lambda item: (-item["score"], item["root"], item["name"]))


def format_hint(matches: list[SkillMatch], limit: int = 3) -> str:
    if not matches:
        return ""

    lines = ["<!-- skill_router: 関連 Skill が見つかりました -->", ""]
    lines.append("以下の既存 Skill がこのタスクに関連する可能性があります。")
    lines.append("")
    for match in matches[:limit]:
        trust_note = "" if match["trusted"] else " / 未信頼のため実行前レビュー必須"
        lines.append(
            f"- **{match['name']}** ({match['root_label']}, score={match['score']}{trust_note})"
        )
        lines.append(f"  `{match['path']}/SKILL.md`")
        if match["hits"]:
            lines.append(f"  hits: {', '.join(match['hits'][:8])}")
    lines.append("")
    lines.append("タスクを解く前に、該当 Skill の手順・検証条件・安全ルールを確認してください。")
    return "\n".join(lines)


def read_prompt_from_stdin() -> str:
    raw = sys.stdin.read().strip()
    if not raw:
        return ""
    try:
        data: object = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if is_str_mapping(data):
        prompt_value = data.get("prompt")
        return str(prompt_value or raw)
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="MUSE Skill Router")
    parser.add_argument("--prompt", help="検索するプロンプト文字列")
    parser.add_argument("--threshold", type=float, default=0.15, help="マッチ閾値")
    parser.add_argument("--agent", choices=("all", "codex"), default="codex")
    parser.add_argument("--limit", type=int, default=3, help="ヒントに表示する最大件数")
    parser.add_argument(
        "--include-quarantine",
        action="store_true",
        help=".muse/quarantine も探索対象に含める",
    )
    parser.add_argument("--json", dest="output_json", action="store_true", help="JSON で出力")
    args = parser.parse_args()

    prompt = args.prompt if args.prompt is not None else read_prompt_from_stdin()
    if not prompt:
        parser.print_help()
        return 0

    matches = route(
        prompt,
        threshold=args.threshold,
        agent=args.agent,
        include_quarantine=args.include_quarantine,
    )

    if args.output_json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
        return 0

    hint = format_hint(matches, limit=args.limit)
    if hint:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": hint,
                    }
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
