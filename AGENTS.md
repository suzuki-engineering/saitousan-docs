# MUSE Operating Policy for Codex

This repository uses a MUSE-style Skill lifecycle for Codex work.

Codex should treat reusable workflows as long-lived, testable assets. Complete the user's task first, then decide whether the successful workflow should become a reusable Skill candidate.

## Default Flow

For each task:

1. Understand the goal, inputs, expected outputs, side effects, and success criteria.
2. Search existing project Skills before creating a new one.
3. If a relevant Skill exists, use it.
4. If no relevant Skill exists, solve the task normally.
5. After success, decide whether the workflow is reusable.
6. If reusable, create a Skill candidate with `SKILL.md`, `eval.yaml`, `tests/`, `usage.jsonl`, and `.memory.md`.
7. Register as reusable only after tests and deterministic checks pass.

Do not create a Skill before solving the task unless the user explicitly asks for Skill creation.

## Codex-Specific Layout

Project-level Codex guidance:

```text
AGENTS.md
.codex/CODEX.md
docs/CODEX.md
```

Reusable project Skills:

```text
.codex/skills/<skill-name>/
```

Skill candidates:

```text
.muse/candidates/
```

External or untrusted Skills:

```text
.muse/quarantine/
```

## Skill Creation Policy

Create a Skill only when all conditions are met:

1. The workflow is likely to be reused.
2. The workflow has at least three meaningful steps.
3. Inputs and outputs are clear.
4. The result can be verified by tests or deterministic checks.
5. The Skill does not contain secrets, credentials, tokens, or private user data.
6. The Skill does not duplicate an existing Skill.

Do not create a Skill when:

1. The task is one-off.
2. Success criteria are ambiguous.
3. The result cannot be tested.
4. The workflow depends on hidden credentials.
5. The operation has risky side effects and no human approval path.

## Evaluation Policy

Do not rely on LLM self-judgment as the final success signal.

Prefer this order:

1. Runtime checks: exit code, exceptions, timeout, output file existence.
2. Unit tests: schema, parsing, transformations, edge cases.
3. Integration tests: API response, dry-run behavior, external service connectivity.
4. Task-level acceptance criteria.
5. LLM judge for subjective quality only.
6. Human approval for production side effects.

Status model:

```text
score >= 0.9          reusable
0.6 <= score < 0.9    needs_refinement
score < 0.6           failed
```

## Skill Files

Each Skill should contain:

```text
SKILL.md
eval.yaml
tests/
usage.jsonl
.memory.md
```

Optional:

```text
scripts/
fixtures/
docs/
references/
assets/
```

## Memory

Record recurring failures, API quirks, environment notes, verified fixes, and usage lessons in `.memory.md`.

Append usage results to `usage.jsonl` as one JSON object per line.

## External Skill Policy

Do not install external Skills directly into `.codex/skills/` or `.claude/skills/`.

External Skills, marketplace plugins, GitHub repositories, and web snippets must first go into:

```text
.muse/quarantine/
```

Before promotion, review:

1. `SKILL.md`
2. scripts and hooks
3. MCP configuration
4. external network access
5. secret leakage risk
6. license
7. tests and dry-run behavior

## Safety

1. Never store credentials in Skills.
2. Do not run untrusted external scripts.
3. Prefer dry-run before production write/send operations.
4. Require human approval for email sending, Slack production posting, deployment, payment, merge, or destructive file operations.
5. Register only tested Skills as reusable.

## References

Read these for more detail:

```text
docs/MUSE.md
docs/USAGE.md
docs/CODEX.md
MUSE_ARCHITECTURE.md
```

