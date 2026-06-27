#!/usr/bin/env python3
"""Evaluate a Skill and record refinement notes."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from typing import cast

from evaluate_skill import evaluate_skill
from memory import append_memory, append_usage
from skill_policy import SkillLocation, as_float, find_skill


def require_skill(identifier: str) -> SkillLocation:
    skill = find_skill(identifier)
    if skill is None:
        raise SystemExit(f"skill not found: {identifier}")
    return skill


def recommendations(result: Mapping[str, object]) -> list[str]:
    failed = string_list(result.get("failed"))
    manual = string_list(result.get("manual"))
    notes: list[str] = []
    if failed:
        notes.append("failed check を修正する: " + ", ".join(failed))
    if manual:
        notes.append(
            "自動検証できない check に command または file assertion を追加する: "
            + ", ".join(manual)
        )
    if not failed and not manual:
        notes.append("required check は自動検証済み。昇格条件を確認する。")
    return notes


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items = cast(list[object], value)
    return [str(item) for item in items]


def record_refinement(skill: SkillLocation, result: Mapping[str, object], source: str) -> None:
    append_usage(
        skill,
        task="skill_refinement_evaluation",
        status=str(result.get("status", "failed")),
        score=as_float(result.get("score"), 0.0),
        checks={
            "passed": string_list(result.get("passed")),
            "failed": string_list(result.get("failed")),
            "manual": string_list(result.get("manual")),
        },
        message=str(result.get("message", "")),
        source=source,
    )
    append_memory(
        skill,
        heading="refinement",
        notes=recommendations(result),
    )


def refine_skill(
    skill: SkillLocation,
    strict_manual: bool = False,
    record: bool = False,
) -> dict[str, object]:
    result = evaluate_skill(skill, strict_manual=strict_manual)
    result_data = cast(dict[str, object], dict(result))
    result_data["recommendations"] = recommendations(result_data)
    if record:
        record_refinement(skill, result_data, source="skill_refiner.py")
    return result_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate and record MUSE Skill refinement notes")
    parser.add_argument("skill")
    parser.add_argument("--strict-manual", action="store_true")
    parser.add_argument("--record", action="store_true", help="Append usage and memory records")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    skill = require_skill(args.skill)
    result = refine_skill(skill, strict_manual=args.strict_manual, record=args.record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
