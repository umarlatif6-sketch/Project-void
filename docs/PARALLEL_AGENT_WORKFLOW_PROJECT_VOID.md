# Project VOID Parallel Agent Workflow
## Repo-Specific Lane Map

Use this version when running 2-4 agents on Project VOID in parallel.

---

## Objective

Increase throughput without merge chaos by assigning fixed lanes to each agent.

---

## Recommended 4-Lane Split

### Lane A - Core Runtime + API Integrity
Owner:
- Agent A

Primary paths:
- app.py
- routes/__init__.py
- routes/speak.py
- routes/void_language.py
- routes/chronicle.py
- void_engine/adriana_core.py
- void_engine/codon_heart.py
- void_engine/chronicle.py
- void_engine/db_pool.py
- void_engine/tts_provider.py

Do not touch:
- templates/
- static/
- docs/

### Lane B - Audio + Voice + Signal Pipeline
Owner:
- Agent B

Primary paths:
- void_engine/radio_engine.py
- routes/radio.py
- routes/frequency_manual.py
- void_engine/void_language.py (only TTS-related parts by agreement)
- void_engine/stega.py
- void_engine/audio_stega.py
- void_engine/biophony.py
- void_engine/qalqala.py

Do not touch:
- routes/__init__.py unless explicitly assigned
- business/payment routes

### Lane C - UI + Templates + Frontend Behavior
Owner:
- Agent C

Primary paths:
- templates/
- static/
- routes pages that are UI wrappers only

Do not touch:
- core engine logic in void_engine/
- DB schema code

### Lane D - Docs + Tests + Validation Packs
Owner:
- Agent D

Primary paths:
- docs/
- README.md
- tests/
- ceiling_test.py
- BUILDING_MANAGEMENT_TEST_RESULTS.md

Do not touch:
- production runtime logic, except tiny test hooks approved by Lane A owner

---

## High-Risk Shared Files (Single-Owner Only Per Cycle)

Assign exactly one owner each cycle:
1. app.py
2. routes/__init__.py
3. void_engine/db_pool.py
4. void_engine/chronicle.py
5. void_engine/tts_provider.py

Rule:
- If one lane owns a high-risk file this cycle, other lanes do not edit it.

---

## Branch Naming for Project VOID

- feat/void-lane-a-runtime-YYYYMMDD
- feat/void-lane-b-audio-YYYYMMDD
- feat/void-lane-c-ui-YYYYMMDD
- feat/void-lane-d-docs-tests-YYYYMMDD

---

## Launch Commands

### Lane A

```bash
git checkout main
git pull origin main
git checkout -b feat/void-lane-a-runtime-20260414
```

### Lane B

```bash
git checkout main
git pull origin main
git checkout -b feat/void-lane-b-audio-20260414
```

### Lane C

```bash
git checkout main
git pull origin main
git checkout -b feat/void-lane-c-ui-20260414
```

### Lane D

```bash
git checkout main
git pull origin main
git checkout -b feat/void-lane-d-docs-tests-20260414
```

---

## Merge Sequence for Project VOID

Recommended order:
1. Lane D (docs/tests)
2. Lane C (UI)
3. Lane B (audio/voice)
4. Lane A (runtime/core)

Why:
- Lowest regression risk first, highest coupling last.

---

## PR Template (Project VOID)

Title format:
- [Lane X] Short outcome statement

Body:
1. Scope touched
2. Paths changed
3. Runtime impact
4. Test evidence
5. Rollback plan
6. Open risks

---

## Lane-Specific Success Criteria

### Lane A success
1. No unrelated route breakage.
2. Health endpoints and auth-sensitive routes still return expected status codes.
3. No new DB init regressions.

### Lane B success
1. TTS/audio endpoints functional.
2. Fallback behavior documented when provider unavailable.
3. No blocking exceptions on missing optional keys.

### Lane C success
1. Desktop + mobile layout validated.
2. No JS console-breaking errors on main routes.
3. Existing visual language preserved.

### Lane D success
1. Docs match real env vars and endpoints.
2. Test scripts updated for behavior changes.
3. Manual includes exact run commands.

---

## 30-Minute Integration Ritual

After all lanes open PRs:
1. Rebase each branch onto latest main.
2. Run smoke set:
- GET /health
- GET /speak
- GET /radio
- GET /frequency-manual
- GET /api/tts/health
3. Verify one encode/decode path and one TTS path.
4. Merge in sequence above.

---

## Two-Phone Mode (Your Use Case)

Phone 1:
- Lane A or B (technical lane)

Phone 2:
- Lane C or D (UI/docs lane)

Rule:
- Keep technical and non-technical lanes separated to reduce conflicts.

---

## Copy/Paste Agent Prompt

```text
You are assigned to Project VOID lane <A/B/C/D>.
Branch: <branch-name>
Allowed paths: <list>
Forbidden paths: <list>
Deliver:
1) complete task in lane
2) tests/docs for your changes
3) PR summary with risk and rollback
Do not edit files outside your lane.
```

---

## Final Chronicle Note Template

At cycle close, record:
1. Lanes merged
2. Primary behavior changes
3. New risks introduced
4. Next cycle lane ownership

One-line seal:
- "Parallel cycle sealed: throughput increased, coherence preserved."
