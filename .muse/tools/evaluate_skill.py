#!/usr/bin/env python3
"""Evaluate a MUSE Skill using its eval.yaml checks."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

from skill_policy import (
    REPO_ROOT,
    REQUIRED_SKILL_ENTRIES,
    EvalCheck,
    SkillLocation,
    find_skill,
    load_eval_config,
    status_for_score,
)

SHELL_META_CHARS = set("|&;<>()$`\\\n")


class ThresholdResult(TypedDict):
    reusable: float
    needs_refinement: float


class CheckResultData(TypedDict):
    id: str
    type: str
    required: bool
    status: str
    description: str
    command: str | None
    returncode: int | None
    duration_seconds: float | None
    message: str
    stdout: str
    stderr: str


class UsageChecks(TypedDict):
    passed: list[str]
    failed: list[str]
    manual: list[str]


class EvaluationResult(TypedDict):
    skill: str
    path: str
    root: str
    status: str
    score: float
    thresholds: ThresholdResult
    passed: list[str]
    failed: list[str]
    manual: list[str]
    checks: list[CheckResultData]
    message: str


@dataclass
class CheckResult:
    id: str
    type: str
    required: bool
    status: str
    description: str = ""
    command: str | None = None
    returncode: int | None = None
    duration_seconds: float | None = None
    message: str = ""
    stdout: str = ""
    stderr: str = ""


def run_required_files_check(skill: SkillLocation) -> CheckResult:
    missing = [entry for entry in REQUIRED_SKILL_ENTRIES if not (skill.path / entry).exists()]
    if missing:
        return CheckResult(
            id="required_files",
            type="static",
            required=True,
            status="failed",
            description="MUSE Skill required files exist",
            message="missing: " + ", ".join(missing),
        )
    return CheckResult(
        id="required_files",
        type="static",
        required=True,
        status="passed",
        description="MUSE Skill required files exist",
    )


def run_check(check: EvalCheck, timeout: int, allow_shell: bool) -> CheckResult:
    if check.command:
        return run_command_check(check, timeout=timeout, allow_shell=allow_shell)

    files_value = check.raw.get("files")
    if isinstance(files_value, list):
        file_paths = [Path(str(value)) for value in cast(list[object], files_value)]
        missing = [
            str(file_path)
            for file_path in file_paths
            if not any(path.exists() for path in (REPO_ROOT / file_path, file_path))
        ]
        if not missing:
            return CheckResult(
                id=check.id,
                type=check.type,
                required=check.required,
                status="passed",
                description=check.description,
                message="all files exist",
            )
        return CheckResult(
            id=check.id,
            type=check.type,
            required=check.required,
            status="failed",
            description=check.description,
            message="missing: " + ", ".join(missing),
        )

    file_value = check.raw.get("file")
    if file_value is not None:
        file_path = Path(str(file_value))
        candidates = [REPO_ROOT / file_path, file_path]
        if any(path.exists() for path in candidates):
            return CheckResult(
                id=check.id,
                type=check.type,
                required=check.required,
                status="passed",
                description=check.description,
                message=f"file exists: {file_path}",
            )
        return CheckResult(
            id=check.id,
            type=check.type,
            required=check.required,
            status="failed",
            description=check.description,
            message=f"file missing: {file_path}",
        )

    return CheckResult(
        id=check.id,
        type=check.type,
        required=check.required,
        status="manual",
        description=check.description,
        message="no executable command or file assertion; requires manual verification",
    )


def run_command_check(check: EvalCheck, timeout: int, allow_shell: bool) -> CheckResult:
    command = check.command or ""
    if not allow_shell and any(char in command for char in SHELL_META_CHARS):
        return CheckResult(
            id=check.id,
            type=check.type,
            required=check.required,
            status="failed",
            description=check.description,
            command=command,
            message="command contains shell metacharacters; rerun with --allow-shell after review",
        )

    start = time.monotonic()
    try:
        if allow_shell:
            completed = subprocess.run(
                command,
                cwd=REPO_ROOT,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        else:
            args = shlex.split(command)
            if args and args[0] in {"python", "python3"}:
                args[0] = sys.executable
            completed = subprocess.run(
                args,
                cwd=REPO_ROOT,
                shell=False,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
    except FileNotFoundError as exc:
        return CheckResult(
            id=check.id,
            type=check.type,
            required=check.required,
            status="failed",
            description=check.description,
            command=command,
            message=str(exc),
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            id=check.id,
            type=check.type,
            required=check.required,
            status="failed",
            description=check.description,
            command=command,
            duration_seconds=round(time.monotonic() - start, 3),
            message=f"timeout after {timeout}s",
            stdout=tail(output_text(exc.stdout)),
            stderr=tail(output_text(exc.stderr)),
        )

    duration = round(time.monotonic() - start, 3)
    return CheckResult(
        id=check.id,
        type=check.type,
        required=check.required,
        status="passed" if completed.returncode == 0 else "failed",
        description=check.description,
        command=command,
        returncode=completed.returncode,
        duration_seconds=duration,
        stdout=tail(completed.stdout),
        stderr=tail(completed.stderr),
    )


def output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def tail(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def check_result_data(result: CheckResult) -> CheckResultData:
    return {
        "id": result.id,
        "type": result.type,
        "required": result.required,
        "status": result.status,
        "description": result.description,
        "command": result.command,
        "returncode": result.returncode,
        "duration_seconds": result.duration_seconds,
        "message": result.message,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def evaluate_skill(
    skill: SkillLocation,
    timeout: int = 120,
    allow_shell: bool = False,
    strict_manual: bool = False,
) -> EvaluationResult:
    eval_config = load_eval_config(skill.eval_yaml)
    results = [run_required_files_check(skill)]
    results.extend(
        run_check(check, timeout=timeout, allow_shell=allow_shell) for check in eval_config.checks
    )

    if strict_manual:
        results = [
            replace(result, status="failed", message=f"{result.message} (strict)")
            if result.required and result.status == "manual"
            else result
            for result in results
        ]

    required_results = [result for result in results if result.required]
    automated_required = [
        result for result in required_results if result.status in {"passed", "failed"}
    ]
    passed_required = [result for result in automated_required if result.status == "passed"]
    failed_required = [result for result in automated_required if result.status == "failed"]
    manual_required = [result for result in required_results if result.status == "manual"]

    score = len(passed_required) / len(automated_required) if automated_required else 0.0

    if failed_required:
        status = "failed"
        score = min(score, eval_config.needs_refinement_threshold - 0.001)
    elif manual_required:
        status = "needs_refinement"
        score = min(
            max(score, eval_config.needs_refinement_threshold),
            eval_config.reusable_threshold - 0.001,
        )
    else:
        status = status_for_score(
            score,
            reusable_threshold=eval_config.reusable_threshold,
            needs_refinement_threshold=eval_config.needs_refinement_threshold,
        )

    return {
        "skill": eval_config.skill if eval_config.skill != "unknown" else skill.name,
        "path": skill.relative_path,
        "root": skill.root.key,
        "status": status,
        "score": round(score, 3),
        "thresholds": {
            "reusable": eval_config.reusable_threshold,
            "needs_refinement": eval_config.needs_refinement_threshold,
        },
        "passed": [result.id for result in results if result.status == "passed"],
        "failed": [result.id for result in results if result.status == "failed"],
        "manual": [result.id for result in results if result.status == "manual"],
        "checks": [check_result_data(result) for result in results],
        "message": "",
    }


def append_usage(skill: SkillLocation, result: EvaluationResult) -> None:
    record: dict[str, object] = {
        "timestamp": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        "skill": result["skill"],
        "task": "evaluate_skill",
        "status": result["status"],
        "score": result["score"],
        "checks": {
            "passed": result["passed"],
            "failed": result["failed"],
            "manual": result["manual"],
        },
    }
    with skill.usage_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a MUSE Skill")
    parser.add_argument("skill", help="Skill name or path")
    parser.add_argument("--agent", choices=("all", "codex"), default="codex")
    parser.add_argument(
        "--include-quarantine", action="store_true", help="Also search .muse/quarantine"
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--allow-shell", action="store_true", help="Allow shell commands in eval.yaml after review"
    )
    parser.add_argument(
        "--strict-manual",
        action="store_true",
        help="Treat required checks without executable commands as failures",
    )
    parser.add_argument(
        "--record", action="store_true", help="Append the evaluation result to usage.jsonl"
    )
    args = parser.parse_args()

    skill = find_skill(args.skill, agent=args.agent, include_quarantine=args.include_quarantine)
    if skill is None:
        print(
            json.dumps(
                {"status": "failed", "message": f"skill not found: {args.skill}"},
                ensure_ascii=False,
            )
        )
        return 2

    result: EvaluationResult
    try:
        result = evaluate_skill(
            skill,
            timeout=args.timeout,
            allow_shell=args.allow_shell,
            strict_manual=args.strict_manual,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should report structured failure.
        result = {
            "skill": skill.name,
            "path": skill.relative_path,
            "root": skill.root.key,
            "status": "failed",
            "score": 0.0,
            "thresholds": {"reusable": 0.9, "needs_refinement": 0.6},
            "passed": list[str](),
            "failed": ["evaluate_skill"],
            "manual": list[str](),
            "checks": list[CheckResultData](),
            "message": str(exc),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if args.record:
        append_usage(skill, result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
