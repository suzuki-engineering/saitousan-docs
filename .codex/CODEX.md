# MUSE Policy for Codex

Use this file as a Codex-oriented copy of the project MUSE policy.

The active Codex project instruction file is `AGENTS.md`. Keep this file aligned with `AGENTS.md` when changing the operating policy.

## Purpose

Codex should use MUSE to turn successful, reusable workflows into tested Skill assets.

MUSE lifecycle:

```text
creation
memory
management
evaluation
refinement
```

## Working Rule

For normal user tasks:

```text
search existing Skills
  -> use if available
  -> otherwise solve normally
  -> evaluate result
  -> create Skill candidate only if reusable
  -> test
  -> promote only if checks pass
```

## Project Paths

```text
AGENTS.md                  Codex project instructions
.codex/skills/             Codex-oriented reusable project Skills
.codex/skills/_template/   Skill template
.muse/candidates/          Draft Skills
.muse/quarantine/          Untrusted imported Skills
.muse/evaluations/         Evaluation output
.muse/logs/                Runtime logs
```

## Promotion Rule

Only promote a candidate to `.codex/skills/` when:

```text
tests pass
eval.yaml required checks pass
usage.jsonl contains a success record
.memory.md records important notes
no secrets are present
side effects have dry-run or approval
```

