# Parallel Agent Workflow
## Two Agents, One Repo, Zero Chaos

Use this every time you run multiple agents on the same project.

---

## Goal

Run multiple agents in parallel on the same GitHub repository while avoiding:
- merge conflicts
- duplicate work
- accidental regressions

---

## Core Rules

1. One agent = one branch.
2. One branch = one workstream.
3. No overlapping file ownership.
4. Small PRs merge faster than big PRs.
5. Rebase before merge, always.

---

## Recommended Split (Two Agents)

Agent A:
- backend/api
- db/schema
- engine/runtime

Agent B:
- frontend/templates
- docs/manuals
- tests/validation

Do not assign both agents to the same files.

---

## Branch Naming Standard

Use predictable names:
- feat/agent-a-backend-<date>
- feat/agent-b-ui-docs-<date>

Example:
- feat/agent-a-backend-2026-04-14
- feat/agent-b-ui-docs-2026-04-14

---

## Startup Commands (Copy/Paste)

### Agent A setup

```bash
git checkout main
git pull origin main
git checkout -b feat/agent-a-backend-2026-04-14
```

### Agent B setup

```bash
git checkout main
git pull origin main
git checkout -b feat/agent-b-ui-docs-2026-04-14
```

---

## Task Card Template (Give Each Agent)

Use this exact card:

```text
TASK OWNER: Agent A
SCOPE: Backend runtime + API reliability
DO NOT TOUCH: templates/, docs/, UI JS/CSS
SUCCESS CRITERIA:
1) Tests pass for touched modules
2) No unrelated file edits
3) PR description includes risk + rollback
```

```text
TASK OWNER: Agent B
SCOPE: Docs + UI + test additions
DO NOT TOUCH: core engine modules unless requested
SUCCESS CRITERIA:
1) UI works on mobile and desktop
2) Docs updated with usage examples
3) PR description includes screenshots/checklist
```

---

## PR Order Strategy

Merge lower-risk PR first.

Recommended:
1. Merge docs/UI PR.
2. Rebase backend PR onto updated main.
3. Resolve any drift.
4. Merge backend PR.

Why:
- docs/UI usually has fewer hidden runtime dependencies.

---

## Rebase and Sync Commands

On each branch before opening PR:

```bash
git fetch origin
git rebase origin/main
```

If conflicts appear:

```bash
# resolve files

git add <resolved-files>
git rebase --continue
```

Push branch after rebase:

```bash
git push --force-with-lease
```

---

## Fast Review Checklist

Use this before approving PRs:

1. Scope respected (no unauthorized files changed).
2. No duplicate implementation of existing logic.
3. Tests added/updated for changed behavior.
4. Config or env changes documented.
5. Rollback path is clear.

---

## Conflict Prevention Matrix

Mark ownership before starting:

- backend routes: Agent A
- core engine modules: Agent A
- templates/static: Agent B
- docs/manuals: Agent B
- test harness: Agent B (unless backend tests needed)
- deployment config: explicit owner only (A or B, not both)

---

## Daily Parallel Rhythm

1. 5 min: scope lock
2. 45-90 min: parallel build
3. 10 min: sync and drift check
4. 20 min: PR update and review
5. 5 min: next lock

---

## Three Non-Negotiables

1. Never let both agents edit the same high-risk file at once.
2. Never keep long-lived parallel branches without rebasing.
3. Never merge without a short integration sanity test.

---

## Scaling to 3+ Agents

Add by lane, not by randomness.

Agent C options:
- CI/test stabilization only
- performance profiling only
- data pipeline tooling only

Keep one integrator role (human or agent) to merge in sequence.

---

## One-Message Kickoff Prompt (Reusable)

Use this prompt when launching each agent:

```text
You are Agent <A/B>. Work only in your assigned scope.
Branch: <branch-name>
Scope: <scope>
Forbidden paths: <paths>
Deliverables:
1) code changes
2) tests/docs updates
3) concise PR summary with risks
Do not modify unrelated files.
```

---

## Close Protocol

At end of cycle:

1. Merge both PRs.
2. Tag release candidate.
3. Write one chronicle entry with:
- what shipped
- what changed in behavior
- unresolved risks
- next cycle focus

That is how you turn more phones into more throughput, not more entropy.
