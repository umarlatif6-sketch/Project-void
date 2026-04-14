# Project VOID Lane Kickoff Prompts
## Date: 2026-04-14

Use these prompts as-is when launching agents.

---

## Lane A Prompt (Runtime/API)

```text
You are assigned to Project VOID lane A (Runtime + API Integrity).

Branch:
feat/void-lane-a-runtime-20260414

Allowed paths:
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

Forbidden paths:
- templates/
- static/
- docs/

Objectives:
1. Improve runtime integrity and API reliability in your lane scope.
2. Keep changes minimal and focused.
3. Avoid edits outside allowed paths.

Deliverables:
1. Code changes in lane scope only.
2. Any needed tests or validation updates tied to your changes.
3. PR summary including: scope, risk, rollback, and test evidence.

Rules:
- Do not modify unrelated files.
- Rebase onto main before opening PR.
- If a forbidden file is required, stop and report.
```

---

## Lane B Prompt (Audio/Voice/Signal)

```text
You are assigned to Project VOID lane B (Audio + Voice + Signal Pipeline).

Branch:
feat/void-lane-b-audio-20260414

Allowed paths:
- void_engine/radio_engine.py
- routes/radio.py
- routes/frequency_manual.py
- void_engine/void_language.py (TTS-related sections only)
- void_engine/stega.py
- void_engine/audio_stega.py
- void_engine/biophony.py
- void_engine/qalqala.py

Forbidden paths:
- routes/__init__.py (unless explicitly approved)
- payment/commercial routes not related to voice/audio
- docs/ (except brief notes in PR description)

Objectives:
1. Improve and stabilize audio/voice pipeline behavior.
2. Preserve existing APIs unless change is essential.
3. Keep provider fallback behavior clear.

Deliverables:
1. Code changes in lane scope only.
2. Validation notes for TTS/audio paths.
3. PR summary including: risk, rollback, and endpoint checks.

Rules:
- Do not edit files outside scope.
- Rebase before PR.
- If shared file conflicts with lane A, stop and report.
```

---

## Lane C Prompt (UI/Templates/Frontend)

```text
You are assigned to Project VOID lane C (UI + Templates + Frontend Behavior).

Branch:
feat/void-lane-c-ui-20260414

Allowed paths:
- templates/
- static/
- route handlers that are UI wrappers only

Forbidden paths:
- core engine logic in void_engine/
- db schema/init code
- app.py and routes/__init__.py

Objectives:
1. Improve interface behavior and readability without breaking existing flows.
2. Keep UI consistent with current style language.
3. Ensure mobile + desktop support.

Deliverables:
1. UI/template/frontend updates only.
2. Brief validation notes for affected pages.
3. PR summary with changed screens and regression risks.

Rules:
- No backend/core refactors.
- No unrelated style rewrites.
- Rebase before PR.
```

---

## Lane D Prompt (Docs/Tests/Validation)

```text
You are assigned to Project VOID lane D (Docs + Tests + Validation Packs).

Branch:
feat/void-lane-d-docs-tests-20260414

Allowed paths:
- docs/
- README.md
- tests/
- ceiling_test.py
- test reports and validation markdown files

Forbidden paths:
- production runtime logic in void_engine/
- route business logic changes unless explicitly requested

Objectives:
1. Align docs with real behavior and env configuration.
2. Improve test clarity and validation reproducibility.
3. Keep edits precise and actionable.

Deliverables:
1. Doc/test updates in scope only.
2. Any command examples verified for syntax.
3. PR summary with what changed and why.

Rules:
- Do not expand into runtime feature work.
- Rebase before PR.
- Flag any mismatch between docs and runtime behavior.
```

---

## Quick Branch Commands

```bash
# Lane A
git checkout main && git pull origin main && git checkout -b feat/void-lane-a-runtime-20260414

# Lane B
git checkout main && git pull origin main && git checkout -b feat/void-lane-b-audio-20260414

# Lane C
git checkout main && git pull origin main && git checkout -b feat/void-lane-c-ui-20260414

# Lane D
git checkout main && git pull origin main && git checkout -b feat/void-lane-d-docs-tests-20260414
```
