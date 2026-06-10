#!/usr/bin/env python3
"""Shared MUSE Skill policy helpers.

This module intentionally uses only the Python standard library.  The repository
is meant to work as a lightweight agent workspace, so the core router/evaluator
should not require installing dependencies before it can inspect Skills.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeGuard, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
MUSE_ROOT = REPO_ROOT / ".muse"

REQUIRED_SKILL_ENTRIES = ("SKILL.md", "eval.yaml", "tests", "usage.jsonl", ".memory.md")
SKIP_SKILL_DIRS = {"_template", "__pycache__"}

type YamlDict = dict[str, object]
type CheckList = list[YamlDict]
type CheckGroups = dict[str, CheckList]
type ChecksNode = CheckList | CheckGroups

EN_TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-\.]{3,}")
JP_SEQ_RE = re.compile(r"[ぁ-んァ-ヶー一-龠々]{2,}")
JP_MEANINGFUL_TOKEN_RE = re.compile(r"^[ァ-ヶー一-龠々]+$")
JP_STOPWORDS = {
    "これ",
    "この",
    "その",
    "ため",
    "よう",
    "こと",
    "もの",
    "して",
    "した",
    "する",
    "です",
    "ます",
    "タスク",
    "実行",
}


def dict_mapping() -> Mapping[str, object]:
    return {}


@dataclass(frozen=True)
class SkillRoot:
    key: str
    label: str
    path: Path
    priority: int
    trusted: bool = True


@dataclass(frozen=True)
class SkillLocation:
    name: str
    path: Path
    root: SkillRoot

    @property
    def skill_md(self) -> Path:
        return self.path / "SKILL.md"

    @property
    def eval_yaml(self) -> Path:
        return self.path / "eval.yaml"

    @property
    def tests_dir(self) -> Path:
        return self.path / "tests"

    @property
    def usage_jsonl(self) -> Path:
        return self.path / "usage.jsonl"

    @property
    def memory_md(self) -> Path:
        return self.path / ".memory.md"

    @property
    def relative_path(self) -> str:
        return str(self.path.relative_to(REPO_ROOT))


@dataclass(frozen=True)
class EvalCheck:
    id: str
    type: str = "manual"
    required: bool = True
    description: str = ""
    command: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict_mapping)


@dataclass(frozen=True)
class EvalConfig:
    skill: str
    checks: list[EvalCheck]
    reusable_threshold: float = 0.9
    needs_refinement_threshold: float = 0.6
    raw: Mapping[str, object] = field(default_factory=dict_mapping)


def skill_roots(agent: str = "all", include_quarantine: bool = True) -> list[SkillRoot]:
    """Return ordered Skill roots for the requested agent."""
    roots = {
        "codex": SkillRoot("codex", "Codex Skill Bank", REPO_ROOT / ".codex" / "skills", 10),
        "candidate": SkillRoot("candidate", "MUSE Candidate", MUSE_ROOT / "candidates", 30),
        "quarantine": SkillRoot(
            "quarantine",
            "MUSE Quarantine",
            MUSE_ROOT / "quarantine",
            40,
            trusted=False,
        ),
    }

    if agent == "codex" or agent == "all":
        ordered = [roots["codex"], roots["candidate"]]
    else:
        raise ValueError(f"unknown agent: {agent}")

    if include_quarantine:
        ordered.append(roots["quarantine"])
    return ordered


def iter_skills(agent: str = "all", include_quarantine: bool = True) -> list[SkillLocation]:
    """Discover Skills from configured roots."""
    found: list[SkillLocation] = []
    for root in skill_roots(agent=agent, include_quarantine=include_quarantine):
        if not root.path.exists():
            continue
        for skill_dir in sorted(root.path.iterdir()):
            if skill_dir.name in SKIP_SKILL_DIRS or not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").is_file():
                continue
            found.append(SkillLocation(name=skill_dir.name, path=skill_dir, root=root))
    return sorted(found, key=lambda item: (item.root.priority, item.name))


def find_skill(
    identifier: str, agent: str = "all", include_quarantine: bool = True
) -> SkillLocation | None:
    """Find a Skill by name or path."""
    raw_path = Path(identifier)
    candidates: list[Path] = []
    if raw_path.exists():
        candidates.append(raw_path)
    candidates.append(REPO_ROOT / identifier)

    for path in candidates:
        if path.is_file() and path.name == "SKILL.md":
            path = path.parent
        if path.is_dir() and (path / "SKILL.md").is_file():
            root = _root_for_path(path, agent=agent, include_quarantine=include_quarantine)
            return SkillLocation(name=path.name, path=path.resolve(), root=root)

    for skill in iter_skills(agent=agent, include_quarantine=include_quarantine):
        if skill.name == identifier:
            return skill
    return None


def _root_for_path(path: Path, agent: str, include_quarantine: bool) -> SkillRoot:
    resolved = path.resolve()
    for root in skill_roots(agent=agent, include_quarantine=include_quarantine):
        try:
            resolved.relative_to(root.path.resolve())
            return root
        except ValueError:
            continue
    return SkillRoot("path", "Explicit Path", path.parent, 99)


def read_skill_text(skill: SkillLocation) -> str:
    return skill.skill_md.read_text(encoding="utf-8")


def extract_keywords(text: str) -> set[str]:
    """Extract simple search keywords from Skill text."""
    keywords: set[str] = set()
    lower_text = text.lower()

    for token in EN_TOKEN_RE.findall(lower_text):
        keywords.add(token)

    for seq in JP_SEQ_RE.findall(text):
        if is_meaningful_japanese_token(seq) and len(seq) <= 16:
            keywords.add(seq)
        for size in (2, 3, 4):
            if len(seq) >= size:
                for index in range(0, len(seq) - size + 1):
                    token = seq[index : index + size]
                    if is_meaningful_japanese_token(token):
                        keywords.add(token)

    return keywords


def prompt_tokens(prompt: str) -> set[str]:
    tokens = set(EN_TOKEN_RE.findall(prompt.lower()))
    for seq in JP_SEQ_RE.findall(prompt):
        if is_meaningful_japanese_token(seq) and len(seq) <= 16:
            tokens.add(seq)
        for size in (2, 3, 4):
            if len(seq) >= size:
                for index in range(0, len(seq) - size + 1):
                    token = seq[index : index + size]
                    if is_meaningful_japanese_token(token):
                        tokens.add(token)
    return tokens


def is_meaningful_japanese_token(token: str) -> bool:
    if token in JP_STOPWORDS:
        return False
    if not JP_MEANINGFUL_TOKEN_RE.match(token):
        return False
    has_kanji = bool(re.search(r"[一-龠々]", token))
    has_katakana = bool(re.search(r"[ァ-ヶー]", token))
    if has_kanji:
        return True
    return bool(has_katakana and len(token) >= 4)


def score_prompt_against_text(prompt: str, text: str) -> tuple[float, list[str]]:
    tokens = prompt_tokens(prompt)
    if not tokens:
        return 0.0, []

    keywords = extract_keywords(text)
    hits = sorted(tokens & keywords)
    if not hits:
        return 0.0, []

    direct_bonus = 0.0
    lower_text = text.lower()
    for hit in hits:
        if hit.lower() in lower_text:
            direct_bonus += 0.03

    score = min((len(hits) / max(len(tokens), 1)) + direct_bonus, 1.0)
    return score, hits


def load_eval_config(path: Path) -> EvalConfig:
    data = load_yaml_like(path)
    if not is_str_mapping(data):
        raise ValueError(f"{path} does not contain a YAML mapping")
    return normalize_eval_config(data)


def load_yaml_like(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    return parse_eval_yaml_subset(text)


def normalize_eval_config(data: Mapping[str, object]) -> EvalConfig:
    skill_name = str(data.get("skill") or "unknown")
    reusable_threshold = 0.9
    needs_refinement_threshold = 0.6

    score_threshold = data.get("score_threshold")
    if is_str_mapping(score_threshold):
        thresholds = score_threshold
        reusable_threshold = as_float(thresholds.get("reusable"), reusable_threshold)
        needs_refinement_threshold = as_float(
            thresholds.get("needs_refinement"), needs_refinement_threshold
        )
    else:
        success_threshold = data.get("success_threshold")
        if success_threshold is not None:
            reusable_threshold = as_float(success_threshold, reusable_threshold)

    checks: list[EvalCheck] = []
    raw_checks = data.get("checks", [])

    if is_check_groups(raw_checks):
        for required_value, group_name in ((True, "required"), (False, "optional")):
            group = raw_checks.get(group_name, [])
            for index, raw_check in enumerate(group):
                checks.append(normalize_check(raw_check, index=index, required=required_value))
    elif is_check_list(raw_checks):
        for index, raw_check in enumerate(raw_checks):
            required = parse_bool(raw_check.get("required", True))
            checks.append(normalize_check(raw_check, index=index, required=required))

    return EvalConfig(
        skill=skill_name,
        checks=checks,
        reusable_threshold=reusable_threshold,
        needs_refinement_threshold=needs_refinement_threshold,
        raw=data,
    )


def normalize_check(raw_check: Mapping[str, object], index: int, required: bool) -> EvalCheck:
    check_id = raw_check.get("id") or raw_check.get("name") or f"check_{index}"
    command_value = raw_check.get("command")
    return EvalCheck(
        id=str(check_id),
        type=str(raw_check.get("type") or "manual"),
        required=required,
        description=str(raw_check.get("description") or ""),
        command=str(command_value) if command_value is not None else None,
        raw=raw_check,
    )


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def as_float(value: object, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, int | float | str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def status_for_score(
    score: float,
    reusable_threshold: float = 0.9,
    needs_refinement_threshold: float = 0.6,
) -> str:
    if score >= reusable_threshold:
        return "reusable"
    if score >= needs_refinement_threshold:
        return "needs_refinement"
    return "failed"


def parse_eval_yaml_subset(text: str) -> YamlDict:
    """Parse the small eval.yaml subset used by this repository.

    This fallback supports top-level scalar mappings, `score_threshold`, a list
    based `checks:` value, and the `checks.required` / `checks.optional` form.
    It is not intended to be a general YAML parser.
    """
    lines = _normalized_yaml_lines(text)
    result: YamlDict = {}
    index = 0

    while index < len(lines):
        indent, content = lines[index]
        if indent != 0:
            index += 1
            continue

        key, value = _split_yaml_pair(content)
        if key == "score_threshold" or key == "failure_policy":
            mapping, index = _parse_scalar_mapping(lines, index + 1, min_indent=2)
            result[key] = mapping
        elif key == "checks":
            checks, index = _parse_checks(lines, index + 1)
            result[key] = checks
        else:
            result[key] = _parse_scalar(value)
            index += 1

    return result


def _normalized_yaml_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    return lines


def _split_yaml_pair(content: str) -> tuple[str, str]:
    if ":" not in content:
        return content, ""
    key, value = content.split(":", 1)
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> object:
    if value == "":
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_scalar_mapping(
    lines: list[tuple[int, str]], index: int, min_indent: int
) -> tuple[YamlDict, int]:
    mapping: YamlDict = {}
    while index < len(lines):
        indent, content = lines[index]
        if indent < min_indent:
            break
        key, value = _split_yaml_pair(content)
        mapping[key] = _parse_scalar(value)
        index += 1
    return mapping, index


def _parse_checks(lines: list[tuple[int, str]], index: int) -> tuple[ChecksNode, int]:
    if index >= len(lines):
        return [], index

    indent, content = lines[index]
    if indent == 2 and content.startswith("- "):
        checks, index = _parse_check_list(lines, index, item_indent=2)
        return checks, index

    groups: CheckGroups = {}
    while index < len(lines):
        indent, content = lines[index]
        if indent < 2:
            break
        if indent != 2:
            index += 1
            continue
        group_name, _ = _split_yaml_pair(content)
        if group_name not in {"required", "optional"}:
            break
        group_checks, index = _parse_check_list(lines, index + 1, item_indent=4)
        groups[group_name] = group_checks
    return groups, index


def _parse_check_list(
    lines: list[tuple[int, str]], index: int, item_indent: int
) -> tuple[CheckList, int]:
    items: CheckList = []
    while index < len(lines):
        indent, content = lines[index]
        if indent < item_indent:
            break
        if indent != item_indent or not content.startswith("- "):
            break

        item: YamlDict = {}
        rest = content[2:].strip()
        if rest:
            key, value = _split_yaml_pair(rest)
            item[key] = _parse_scalar(value)
        index += 1

        while index < len(lines):
            next_indent, next_content = lines[index]
            if next_indent <= item_indent:
                break
            key, value = _split_yaml_pair(next_content)
            if value == "" and index + 1 < len(lines):
                list_value, next_index = _parse_scalar_list(
                    lines,
                    index + 1,
                    min_indent=next_indent + 2,
                )
                if list_value:
                    item[key] = list_value
                    index = next_index
                    continue
            item[key] = _parse_scalar(value)
            index += 1

        items.append(item)
    return items, index


def _parse_scalar_list(
    lines: list[tuple[int, str]], index: int, min_indent: int
) -> tuple[list[object], int]:
    values: list[object] = []
    while index < len(lines):
        indent, content = lines[index]
        if indent < min_indent or not content.startswith("- "):
            break
        values.append(_parse_scalar(content[2:].strip()))
        index += 1
    return values, index


def is_str_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return False
    mapping = cast(Mapping[object, object], value)
    return all(isinstance(key, str) for key in mapping)


def is_check_list(value: object) -> TypeGuard[CheckList]:
    if not isinstance(value, list):
        return False
    items = cast(list[object], value)
    return all(is_str_mapping(item) for item in items)


def is_check_groups(value: object) -> TypeGuard[CheckGroups]:
    if not isinstance(value, Mapping):
        return False
    mapping = cast(Mapping[object, object], value)
    for key, group_value in mapping.items():
        if not isinstance(key, str):
            return False
        if key not in {"required", "optional"}:
            return False
        if not is_check_list(group_value):
            return False
    return True
