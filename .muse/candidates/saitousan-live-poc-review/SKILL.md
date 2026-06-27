# Saitousan LIVE PoC Review

## Purpose

Use this Skill when planning, reviewing, or updating work for the Saitousan / Saitousan LIVE technical research project, especially tasks related to ADR-0002: sending YouTube Live or test video into Saitousan LIVE through an Android runtime wrapper.

This Skill helps the agent keep the project focused on staged PoC validation, documentation accuracy, cost control, and compliance gates before any public or production-like operation.

## Inputs

Required inputs:

- User request or task description.
- Target phase when known: `phase-0-emulator-check`, `phase-1-camera-injection`, `phase-2-youtube-input`, `phase-3-automation`, or `phase-4-remote-host`.
- Relevant project files, usually:
  - `README.md`
  - `adr/0002-youtube-to-saitousan-live-wrapper.md`
  - `adr/0004-saitousan-live-to-youtube-mirror.md`
  - `architecture/aws-youtube-to-saitousan-live.md`
  - `research/saitousan-live-technical-notes.md`
  - `research/validation-log.md`

Optional inputs:

- Local test results, screenshots, logs, device/emulator details, Appium output, FFmpeg output, AWS cost assumptions, or cloud provider constraints.
- Explicit user approval for actions with side effects.

## Outputs

When the user says `検討して`, `検討`, `方針を決めて`, or asks for a design/architecture/cost decision, default to creating or updating an ADR unless the user explicitly asks for a different format.

Produce one or more of the following:

- New or updated ADR as the default artifact for consideration/decision tasks.
- Updated architecture note, research note, or validation log when the task is evidence gathering rather than decision making.
- A phase-scoped PoC checklist with success/failure criteria.
- A compliance/risk note that separates facts, assumptions, and open questions.
- A cost-aware implementation recommendation.
- A list of next actions that avoids premature cloud or production work.

Do not produce:

- Credential files, tokens, cookies, stream keys, account secrets, or copied private app data.
- Instructions to bypass app protections, evade bans, scrape private data, or reverse engineer non-public APIs.
- Public streaming or recording steps involving third parties unless the user has explicitly confirmed legal/compliance approval.

## Procedure

1. **Classify the task**
   - Determine whether the request is research, ADR writing, local PoC planning, validation logging, cloud architecture, cost review, or implementation planning.
   - If the user says `検討して`, treat it as an ADR task by default: create the next numbered file under `adr/` with `Status: Proposed`, unless the user explicitly says the decision is accepted or asks for a memo only.
   - If the request may involve public streaming, account automation, third-party data, payment, deployment, or destructive actions, require human approval before proceeding.

2. **Read the project source of truth**
   - Start from `README.md` for repository purpose.
   - Use `adr/0002-youtube-to-saitousan-live-wrapper.md` as the accepted implementation direction.
   - Treat `adr/0004-saitousan-live-to-youtube-mirror.md` as rejected unless the user explicitly asks for historical comparison.
   - Use `architecture/aws-youtube-to-saitousan-live.md` only after local PoC requirements justify cloud discussion.
   - Update `research/validation-log.md` when the task records actual validation results.

3. **Respect the phase boundary**
   - Phase 0: Android emulator/app launch/Appium reachability only.
   - Phase 1: fixed video or virtual camera input into Android camera preview.
   - Phase 2: YouTube Live or test HLS input, latency, stability, and audio investigation.
   - Phase 3: Appium/ADB automation, start/stop repeatability, logs and screenshots.
   - Phase 4: remote host or AWS, admin UI, cost, recovery, and monitoring.
   - Do not introduce Next.js, EC2, SQS, Secrets Manager, or always-on cloud services before Phase 1/2 evidence supports them.

4. **Apply compliance and privacy gates**
   - Keep tests limited to owned accounts, test assets, private/non-public streams, and controlled environments.
   - Explicitly call out risks around Saitousan terms, YouTube terms, automated operation, virtualized environments, recording, redistribution, third-party likeness/voice, and personal information.
   - Prefer non-public local validation before any networked or public side effect.

5. **Separate facts from assumptions**
   - Label confirmed project decisions as `Fact` or `Decision`.
   - Label inferred implementation ideas as `Assumption` or `Hypothesis`.
   - Preserve unanswered items as `Open Question` rather than presenting them as known.

6. **Keep cost proportional to uncertainty**
   - Prefer local emulator/device experiments before AWS.
   - Prefer fixed video/test HLS before YouTube Live.
   - Prefer manual operation before full automation.
   - Avoid always-on GPU/Windows/Mac cloud hosts unless the project has passed earlier success criteria.

7. **Update documentation surgically**
   - Keep ADR history intact. Do not rewrite accepted/rejected decisions casually; create a new ADR if the decision changes.
   - Use the next available ADR number. If numbers are skipped, continue with the next highest number rather than filling gaps unless the user asks.
   - For validation results, append or fill `research/validation-log.md` with date, environment, steps, result, findings, and next actions.
   - When adding architecture notes, include success criteria and rollback/stop conditions.

8. **Triage bulk Issue/PR ADR work before writing**
   - Inventory all Issues and PRs, including merged and closed items, and synchronize the default branch before assigning ADR numbers.
   - Treat GitHub numbers used by PRs as PRs, not as missing Issues.
   - Reuse an existing open PR when it already contains the relevant ADR work; resolve numbering and dependency conflicts instead of creating duplicate ADRs.
   - Map every Issue to exactly one ADR, an existing ADR, or an explicit non-ADR rationale. Keep new decisions at `Status: Proposed` until the user explicitly accepts them.
   - Keep architectural boundaries, contracts, sequencing, and safety constraints in ADRs. Keep selectors, measured values, and transient runtime evidence in `research/validation-log.md`.
   - Recheck time-sensitive cloud, platform, and tool claims against official primary sources before finalizing a proposal.

## Verification

Run the checks defined in `eval.yaml` for this candidate Skill.

At minimum, verify that:

- `SKILL.md` contains Purpose, Inputs, Outputs, Procedure, Verification, Memory, and Safety sections.
- The Skill references the accepted ADR-0002 direction and the rejected ADR-0004 direction correctly.
- The Skill states that `検討して` defaults to creating or updating an ADR.
- The Skill includes phase boundaries and compliance gates.
- The Skill avoids secrets and does not instruct non-public API reverse engineering, protection bypass, public third-party recording, or automated production posting.
- Bulk triage verifies unique ADR numbers, matching filename/header IDs, valid statuses, local index links, and a complete Issue-to-ADR map.

## Memory

Record recurring failures and improvements in `.memory.md`, especially:

- Confusion between YouTube -> Saitousan LIVE and Saitousan LIVE -> YouTube directions.
- Attempts to jump to AWS/Next.js before local PoC evidence exists.
- Compliance or privacy risks discovered during planning.
- Emulator/Appium/virtual camera environment quirks.

## Safety

- Do not include secrets or credentials.
- Do not automate public streaming, deployment, payment, permission changes, or destructive operations without explicit human approval.
- Do not recommend bypassing app protections, reverse engineering non-public APIs, or evading account restrictions.
- Do not record, redistribute, or expose third-party video, audio, comments, profiles, notifications, or personal data without explicit approval and legal/compliance confirmation.
- Prefer dry-run, local-only, private, and test-account workflows until compliance gates are satisfied.
