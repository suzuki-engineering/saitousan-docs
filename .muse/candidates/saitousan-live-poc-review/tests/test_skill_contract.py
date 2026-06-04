import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")
LOWER = TEXT.lower()


class SkillContractTest(unittest.TestCase):
    def test_required_sections_exist(self):
        for section in [
            "## Purpose",
            "## Inputs",
            "## Outputs",
            "## Procedure",
            "## Verification",
            "## Memory",
            "## Safety",
        ]:
            self.assertIn(section, TEXT)

    def test_project_sources_of_truth_are_referenced(self):
        self.assertIn("adr/0002-youtube-to-saitousan-live-wrapper.md", TEXT)
        self.assertIn("adr/0004-saitousan-live-to-youtube-mirror.md", TEXT)
        self.assertIn("research/validation-log.md", TEXT)
        self.assertIn("architecture/aws-youtube-to-saitousan-live.md", TEXT)

    def test_direction_phase_boundaries_and_adr_default_are_explicit(self):
        self.assertIn("YouTube -> Saitousan LIVE", TEXT)
        self.assertIn("ADR-0004", TEXT)
        self.assertIn("rejected", LOWER)
        self.assertIn("検討して", TEXT)
        self.assertIn("ADR task by default", TEXT)
        self.assertIn("Status: Proposed", TEXT)
        for phase in ["Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4"]:
            self.assertIn(phase, TEXT)

    def test_compliance_and_privacy_gates_are_present(self):
        required_terms = [
            "human approval",
            "Saitousan terms",
            "YouTube terms",
            "third-party",
            "personal data",
            "test-account",
            "private",
        ]
        for term in required_terms:
            self.assertIn(term.lower(), LOWER)

    def test_forbidden_guidance_is_negated_not_recommended(self):
        self.assertIn("instructions to bypass app protections", LOWER)
        self.assertIn("evade bans", LOWER)
        self.assertIn("reverse engineer non-public APIs", TEXT)
        self.assertIn("do not", LOWER)

        recommended_bad_patterns = [
            "you should bypass app protections",
            "evade bans by",
            "stream keys in code",
            "public third-party recording is allowed",
            "use reverse engineering of non-public apis",
        ]
        for phrase in recommended_bad_patterns:
            self.assertNotIn(phrase, LOWER)


if __name__ == "__main__":
    unittest.main()
