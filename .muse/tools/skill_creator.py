#!/usr/bin/env python3
"""Create MUSE Skill candidates."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from memory import append_memory, append_usage
from skill_policy import REPO_ROOT, SkillLocation, SkillRoot

CANDIDATE_ROOT = REPO_ROOT / ".muse" / "candidates"


@dataclass(frozen=True)
class SkillDraft:
    name: str
    purpose: str
    inputs: list[str]
    outputs: list[str]
    procedure: list[str]
    safety: list[str]


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9_-]+", "-", lowered)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        raise ValueError("skill name must contain at least one ASCII letter or digit")
    return slug


def bullet_lines(items: list[str]) -> str:
    if not items:
        return "- 未定義"
    return "\n".join(f"- {item}" for item in items)


def numbered_lines(items: list[str]) -> str:
    if not items:
        return "1. 未定義"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def skill_markdown(draft: SkillDraft) -> str:
    return f"""# Skill: {draft.name}

## 目的

{draft.purpose}

## 入力

{bullet_lines(draft.inputs)}

## 出力

{bullet_lines(draft.outputs)}

## 手順

{numbered_lines(draft.procedure)}

## 検証

`eval.yaml` の required check を実行する。

```sh
python .muse/tools/evaluate_skill.py {draft.name}
```

## 安全ルール

{bullet_lines(draft.safety)}
"""


def eval_yaml(name: str) -> str:
    return f"""skill: {name}
version: "0.1"
score_threshold:
  reusable: 0.9
  needs_refinement: 0.6

checks:
  required:
    - id: unit_tests
      description: "Skill metadata/static tests pass"
      type: unittest
      command: "python -m unittest discover -s .muse/candidates/{name}/tests"
"""


def static_test(name: str) -> str:
    return f"""from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "SKILL.md"
EVAL_YAML = ROOT / "eval.yaml"
USAGE_JSONL = ROOT / "usage.jsonl"
MEMORY_MD = ROOT / ".memory.md"


class {test_class_name(name)}Test(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        for path in (SKILL_MD, EVAL_YAML, USAGE_JSONL, MEMORY_MD):
            self.assertTrue(path.is_file(), f"{{path}} is missing")

    def test_skill_has_required_sections(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        for heading in ("## 目的", "## 入力", "## 出力", "## 手順", "## 検証", "## 安全ルール"):
            self.assertIn(heading, text)

    def test_eval_yaml_has_unit_tests(self) -> None:
        text = EVAL_YAML.read_text(encoding="utf-8")
        self.assertIn("id: unit_tests", text)
        self.assertIn("python -m unittest discover", text)


if __name__ == "__main__":
    unittest.main()
"""


def test_class_name(name: str) -> str:
    parts = re.findall(r"[a-zA-Z0-9]+", name)
    class_name = "".join(part.capitalize() for part in parts) or "GeneratedSkill"
    if not class_name[0].isalpha():
        return f"Generated{class_name}"
    return class_name


def create_skill_candidate(
    draft: SkillDraft,
    candidate_root: Path = CANDIDATE_ROOT,
    force: bool = False,
) -> SkillLocation:
    name = slugify(draft.name)
    path = candidate_root / name
    if path.exists() and not force:
        raise FileExistsError(f"skill candidate already exists: {path}")

    (path / "tests").mkdir(parents=True, exist_ok=True)
    normalized_draft = SkillDraft(
        name=name,
        purpose=draft.purpose,
        inputs=draft.inputs,
        outputs=draft.outputs,
        procedure=draft.procedure,
        safety=draft.safety,
    )
    (path / "SKILL.md").write_text(skill_markdown(normalized_draft), encoding="utf-8")
    (path / "eval.yaml").write_text(eval_yaml(name), encoding="utf-8")
    (path / "tests" / "test_skill_static.py").write_text(static_test(name), encoding="utf-8")
    (path / "usage.jsonl").touch()
    (path / ".memory.md").write_text(f"# Memory: {name}\n", encoding="utf-8")

    skill = SkillLocation(
        name=name,
        path=path,
        root=SkillRoot("candidate", "MUSE Candidate", candidate_root, 30),
    )
    append_usage(
        skill,
        task="skill_candidate_created",
        status="needs_refinement",
        score=0.6,
        checks={"required_files": True, "unit_tests_defined": True},
        source="skill_creator.py",
    )
    append_memory(
        skill,
        heading="初回作成",
        notes=[
            "skill_creator.py で候補を作成した。",
            "実利用後に検証結果と運用上の注意点を追記する。",
        ],
    )
    return skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a MUSE Skill candidate")
    parser.add_argument("name")
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--step", action="append", default=[])
    parser.add_argument("--safety", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    skill = create_skill_candidate(
        SkillDraft(
            name=args.name,
            purpose=args.purpose,
            inputs=args.input,
            outputs=args.output,
            procedure=args.step,
            safety=args.safety
            or ["secrets, credentials, tokens, private user data を保存しない。"],
        ),
        force=args.force,
    )
    print(
        json.dumps(
            {"status": "created", "skill": skill.name, "path": skill.relative_path},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
