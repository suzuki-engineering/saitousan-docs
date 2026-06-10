#!/usr/bin/env python3
"""MUSE memory and usage helpers."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from skill_policy import REPO_ROOT, SkillLocation, find_skill, is_str_mapping

LOG_DIR = REPO_ROOT / ".muse" / "logs"
QUEUE_PATH = LOG_DIR / "muse-queue.jsonl"
HOOK_STOP_TASK = (
    "Codex task completed; run post-task MUSE review if the completed workflow is reusable."
)


class UsageRecord(TypedDict, total=False):
    timestamp: str
    skill: str
    task: str
    status: str
    score: float
    checks: dict[str, object]
    error_type: str
    message: str
    source: str


class QueueRecord(TypedDict, total=False):
    timestamp: str
    kind: str
    task: str
    status: str
    notes: list[str]
    source: str


def now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def parse_check_values(values: list[str]) -> dict[str, object]:
    checks: dict[str, object] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"check must be KEY=VALUE: {value}")
        key, raw = value.split("=", 1)
        lowered = raw.strip().lower()
        if lowered in {"true", "yes", "1"}:
            parsed: object = True
        elif lowered in {"false", "no", "0"}:
            parsed = False
        else:
            parsed = raw
        checks[key.strip()] = parsed
    return checks


def append_usage(
    skill: SkillLocation,
    task: str,
    status: str,
    score: float,
    checks: dict[str, object] | None = None,
    message: str = "",
    error_type: str = "",
    source: str = "memory.py",
) -> UsageRecord:
    record: UsageRecord = {
        "timestamp": now_iso(),
        "skill": skill.name,
        "task": task,
        "status": status,
        "score": score,
        "checks": checks or {},
        "source": source,
    }
    if message:
        record["message"] = message
    if error_type:
        record["error_type"] = error_type

    with skill.usage_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def append_memory(skill: SkillLocation, heading: str, notes: list[str]) -> None:
    if not notes:
        return

    date_heading = datetime.now(UTC).astimezone().strftime("%Y-%m-%d")
    lines = ["", f"## {date_heading} - {heading}", ""]
    lines.extend(f"- {note}" for note in notes)
    lines.append("")

    with skill.memory_md.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def read_usage(skill: SkillLocation) -> list[UsageRecord]:
    if not skill.usage_jsonl.exists():
        return []
    records: list[UsageRecord] = []
    for line in skill.usage_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data: object = json.loads(line)
        if is_str_mapping(data):
            records.append(usage_record_from_mapping(data))
    return records


def usage_record_from_mapping(data: Mapping[str, object]) -> UsageRecord:
    record: UsageRecord = {}

    timestamp = data.get("timestamp")
    if isinstance(timestamp, str):
        record["timestamp"] = timestamp
    skill = data.get("skill")
    if isinstance(skill, str):
        record["skill"] = skill
    task = data.get("task")
    if isinstance(task, str):
        record["task"] = task
    status = data.get("status")
    if isinstance(status, str):
        record["status"] = status
    error_type = data.get("error_type")
    if isinstance(error_type, str):
        record["error_type"] = error_type
    message = data.get("message")
    if isinstance(message, str):
        record["message"] = message
    source = data.get("source")
    if isinstance(source, str):
        record["source"] = source

    score = data.get("score")
    if isinstance(score, int | float):
        record["score"] = float(score)

    checks = data.get("checks")
    if is_str_mapping(checks):
        record["checks"] = dict(checks)
    return record


def usage_summary(skill: SkillLocation) -> dict[str, object]:
    records = read_usage(skill)
    latest = records[-1] if records else None
    successes = sum(1 for record in records if record.get("status") in {"success", "reusable"})
    failures = sum(1 for record in records if record.get("status") in {"failure", "failed"})
    return {
        "skill": skill.name,
        "path": skill.relative_path,
        "usage_count": len(records),
        "success_count": successes,
        "failure_count": failures,
        "latest": latest,
        "has_memory": skill.memory_md.exists(),
    }


def append_hook_event(event_name: str, payload: object) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{event_name}-events.jsonl"
    record: dict[str, object] = {
        "timestamp": now_iso(),
        "event": event_name,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def enqueue_task(
    task: str,
    kind: str = "post_task_muse_review",
    notes: list[str] | None = None,
    source: str = "memory.py",
    status: str = "queued",
    queue_path: Path = QUEUE_PATH,
) -> QueueRecord:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    record: QueueRecord = {
        "timestamp": now_iso(),
        "kind": kind,
        "task": task,
        "status": status,
        "source": source,
    }
    if notes:
        record["notes"] = notes

    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def hook_stop_notes(payload: object, event_path: Path) -> list[str]:
    notes = [
        "Completion event captured for Codex post-task MUSE review.",
        f"event_log: {display_path(event_path)}",
    ]
    if is_str_mapping(payload):
        for key in ("hookEventName", "session_id", "cwd", "transcript_path"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                notes.append(f"{key}: {value}")
    elif payload:
        notes.append("Non-object Stop hook payload recorded in event log.")
    return notes


def enqueue_hook_stop_event(
    payload: object,
    event_path: Path,
    queue_path: Path = QUEUE_PATH,
) -> QueueRecord:
    return enqueue_task(
        task=HOOK_STOP_TASK,
        notes=hook_stop_notes(payload, event_path),
        source="hook-stop",
        queue_path=queue_path,
    )


def read_stdin_json() -> object:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def require_skill(identifier: str) -> SkillLocation:
    skill = find_skill(identifier)
    if skill is None:
        raise SystemExit(f"skill not found: {identifier}")
    return skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MUSE memory helper")
    subcommands = parser.add_subparsers(dest="command", required=True)

    usage_parser = subcommands.add_parser("append-usage", help="Append one usage.jsonl record")
    usage_parser.add_argument("skill")
    usage_parser.add_argument("--task", required=True)
    usage_parser.add_argument("--status", required=True)
    usage_parser.add_argument("--score", type=float, required=True)
    usage_parser.add_argument("--check", action="append", default=[])
    usage_parser.add_argument("--message", default="")
    usage_parser.add_argument("--error-type", default="")
    usage_parser.add_argument("--source", default="memory.py")

    memory_parser = subcommands.add_parser("append-memory", help="Append notes to .memory.md")
    memory_parser.add_argument("skill")
    memory_parser.add_argument("--heading", required=True)
    memory_parser.add_argument("--note", action="append", required=True)

    summary_parser = subcommands.add_parser("summary", help="Print usage summary")
    summary_parser.add_argument("skill")

    queue_parser = subcommands.add_parser("enqueue", help="Append a deferred MUSE task")
    queue_parser.add_argument("--task", required=True)
    queue_parser.add_argument("--kind", default="post_task_muse_review")
    queue_parser.add_argument("--note", action="append", default=[])
    queue_parser.add_argument("--source", default="memory.py")

    subcommands.add_parser("hook-stop", help="Record and enqueue a Codex post-task event")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "append-usage":
        skill = require_skill(args.skill)
        record = append_usage(
            skill=skill,
            task=args.task,
            status=args.status,
            score=args.score,
            checks=parse_check_values(args.check),
            message=args.message,
            error_type=args.error_type,
            source=args.source,
        )
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0

    if args.command == "append-memory":
        skill = require_skill(args.skill)
        append_memory(skill, heading=args.heading, notes=args.note)
        print(json.dumps({"status": "ok", "skill": skill.name}, ensure_ascii=False))
        return 0

    if args.command == "summary":
        skill = require_skill(args.skill)
        print(json.dumps(usage_summary(skill), ensure_ascii=False, indent=2))
        return 0

    if args.command == "enqueue":
        record = enqueue_task(
            task=args.task,
            kind=args.kind,
            notes=args.note,
            source=args.source,
        )
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0

    if args.command == "hook-stop":
        payload = read_stdin_json()
        path = append_hook_event("stop", payload)
        queue_record = enqueue_hook_stop_event(payload, event_path=path)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "path": display_path(path),
                    "queue_path": display_path(QUEUE_PATH),
                    "queued": queue_record,
                },
                ensure_ascii=False,
            )
        )
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
