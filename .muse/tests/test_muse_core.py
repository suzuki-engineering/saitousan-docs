from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / ".muse" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from evaluate_skill import evaluate_skill  # noqa: E402
from memory import (  # noqa: E402
    append_memory,
    append_usage,
    enqueue_hook_stop_event,
    enqueue_task,
    read_usage,
)
from skill_creator import SkillDraft, create_skill_candidate, slugify, test_class_name  # noqa: E402
from skill_policy import (  # noqa: E402
    SkillLocation,
    SkillRoot,
    find_skill,
    is_check_list,
    is_str_mapping,
    load_eval_config,
    parse_eval_yaml_subset,
)
from skill_refiner import recommendations  # noqa: E402
import skill_router  # noqa: E402
from skill_router import route  # noqa: E402

EXISTING_SKILL = "saitousan-live-poc-review"
EXISTING_EVAL = REPO_ROOT / ".muse" / "candidates" / EXISTING_SKILL / "eval.yaml"


class MuseCoreTest(unittest.TestCase):
    def test_eval_yaml_is_normalized(self) -> None:
        config = load_eval_config(EXISTING_EVAL)

        self.assertEqual(config.skill, EXISTING_SKILL)
        self.assertEqual(config.reusable_threshold, 0.9)
        self.assertTrue(
            any(check.id == "skill_contract_tests" and check.required for check in config.checks)
        )
        self.assertTrue(
            any(check.id == "required_files_exist" and check.required for check in config.checks)
        )

    def test_eval_yaml_subset_parser_supports_file_lists(self) -> None:
        parsed = parse_eval_yaml_subset(EXISTING_EVAL.read_text(encoding="utf-8"))
        checks = parsed["checks"]
        assert is_check_list(checks)

        file_check = checks[1]
        files = cast(list[str], file_check["files"])
        assert isinstance(files, list)
        self.assertIn(".muse/candidates/saitousan-live-poc-review/SKILL.md", files)

    def test_router_ignores_generic_prompt_and_finds_specific_skill(self) -> None:
        self.assertEqual(route("このタスクを実行して"), [])

        matches = route("Saitousan LIVE PoC のADRとPhase境界を検討して")
        self.assertTrue(matches)
        self.assertEqual(matches[0]["name"], EXISTING_SKILL)

    def test_router_excludes_quarantine_by_default(self) -> None:
        calls: list[bool] = []
        original_iter_skills = skill_router.iter_skills
        original_read_skill_text = skill_router.read_skill_text
        quarantine_skill = SkillLocation(
            name="unsafe-imported-skill",
            path=REPO_ROOT / ".muse/quarantine/unsafe-imported-skill",
            root=SkillRoot(
                "quarantine", "MUSE Quarantine", REPO_ROOT / ".muse/quarantine", 40, False
            ),
        )

        def fake_iter_skills(
            agent: str = "all", include_quarantine: bool = False
        ) -> list[SkillLocation]:
            calls.append(include_quarantine)
            if include_quarantine:
                return [quarantine_skill]
            return []

        try:
            skill_router.iter_skills = fake_iter_skills
            skill_router.read_skill_text = lambda skill: "unsafe quarantine import workflow"

            self.assertEqual(route("unsafe quarantine import workflow"), [])
            matches = route("unsafe quarantine import workflow", include_quarantine=True)

            self.assertTrue(matches)
            self.assertEqual(matches[0]["name"], "unsafe-imported-skill")
            self.assertEqual(matches[0]["root"], "quarantine")
            self.assertEqual(calls, [False, True])
        finally:
            skill_router.iter_skills = original_iter_skills
            skill_router.read_skill_text = original_read_skill_text

    def test_evaluator_runs_command_and_file_checks(self) -> None:
        skill = find_skill(EXISTING_SKILL)
        assert skill is not None

        result = evaluate_skill(skill)
        self.assertIn("required_files", result["passed"])
        self.assertIn("skill_contract_tests", result["passed"])
        self.assertIn("required_files_exist", result["passed"])
        self.assertEqual(result["status"], "reusable")

    def test_memory_appends_usage_and_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "sample-skill"
            path.mkdir()
            (path / "usage.jsonl").touch()
            (path / ".memory.md").write_text("# Memory: sample-skill\n", encoding="utf-8")
            skill = SkillLocation(
                name="sample-skill",
                path=path,
                root=SkillRoot("test", "Test Skill", Path(temporary_dir), 99),
            )

            append_usage(
                skill,
                task="unit_test",
                status="success",
                score=1.0,
                checks={"dry_run": True},
                source="test",
            )
            records = read_usage(skill)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].get("task"), "unit_test")
            self.assertEqual(records[0].get("status"), "success")

            append_memory(skill, heading="テスト", notes=["記録できる"])
            memory_text = skill.memory_md.read_text(encoding="utf-8")
            self.assertIn("## ", memory_text)
            self.assertIn("- 記録できる", memory_text)

    def test_memory_enqueues_deferred_muse_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            queue_path = Path(temporary_dir) / "muse-queue.jsonl"
            record = enqueue_task(
                task="作業完了後に Skill 候補化を検討する",
                notes=["本流チャットでは実行しない"],
                source="test",
                queue_path=queue_path,
            )

            self.assertEqual(record.get("kind"), "post_task_muse_review")
            self.assertEqual(record.get("status"), "queued")
            text = queue_path.read_text(encoding="utf-8")
            self.assertIn("Skill 候補化", text)

    def test_post_task_event_is_queued_for_muse_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            queue_path = Path(temporary_dir) / "muse-queue.jsonl"
            event_path = Path(temporary_dir) / "post-task-events.jsonl"
            record = enqueue_hook_stop_event(
                payload={
                    "hookEventName": "PostTask",
                    "session_id": "test-session",
                    "cwd": str(REPO_ROOT),
                },
                event_path=event_path,
                queue_path=queue_path,
            )

            self.assertEqual(record.get("kind"), "post_task_muse_review")
            self.assertEqual(record.get("source"), "hook-stop")
            self.assertIn("Codex task completed", str(record.get("task")))
            self.assertIn("event_log", "\n".join(record.get("notes", [])))

            text = queue_path.read_text(encoding="utf-8")
            self.assertIn("test-session", text)
            self.assertIn("post-task MUSE review", text)

    def test_skill_creator_writes_required_candidate_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            draft = SkillDraft(
                name="Debug Flow",
                purpose="Codex の再利用手順を候補化する。",
                inputs=["調査ログ"],
                outputs=["調査結果"],
                procedure=["ログを読む", "関連 docs を確認する", "結果を記録する"],
                safety=["secrets を保存しない"],
            )
            skill = create_skill_candidate(draft, candidate_root=Path(temporary_dir))

            self.assertEqual(skill.name, "debug-flow")
            self.assertTrue(skill.skill_md.is_file())
            self.assertTrue(skill.eval_yaml.is_file())
            self.assertTrue((skill.tests_dir / "test_skill_static.py").is_file())
            self.assertTrue(read_usage(skill))
            self.assertIn("## 手順", skill.skill_md.read_text(encoding="utf-8"))
            self.assertIn(
                ".muse/candidates/debug-flow/tests", skill.eval_yaml.read_text(encoding="utf-8")
            )

    def test_skill_creator_slug_and_test_class_names_are_stable(self) -> None:
        self.assertEqual(slugify("Kube Debug Flow"), "kube-debug-flow")
        self.assertEqual(test_class_name("123-debug"), "Generated123Debug")

    def test_skill_refiner_recommends_failed_and_manual_fixes(self) -> None:
        result: dict[str, object] = {
            "failed": ["unit_tests"],
            "manual": ["human_approval"],
        }

        notes = recommendations(result)
        self.assertTrue(any("failed check" in note for note in notes))
        self.assertTrue(any("自動検証できない" in note for note in notes))

    def test_find_skill_uses_codex_and_muse_roots_only(self) -> None:
        skill = find_skill(EXISTING_SKILL, agent="codex")
        assert skill is not None

        self.assertEqual(skill.root.key, "candidate")
        self.assertTrue(skill.relative_path.startswith(".muse/candidates/"))

        parsed = parse_eval_yaml_subset(
            "skill: sample\nchecks:\n  - name: one\n    required: true\n"
        )
        self.assertTrue(is_str_mapping(parsed))

    def test_skill_location_relative_path_is_posix_style(self) -> None:
        class WindowsLikePath:
            def relative_to(self, root: Path) -> PureWindowsPath:
                return PureWindowsPath(".muse/candidates/windows-skill")

        skill = SkillLocation(
            name="windows-skill",
            path=cast(Path, WindowsLikePath()),
            root=SkillRoot("candidate", "MUSE Candidate", REPO_ROOT / ".muse/candidates", 30),
        )

        self.assertEqual(skill.relative_path, ".muse/candidates/windows-skill")


if __name__ == "__main__":
    unittest.main()
