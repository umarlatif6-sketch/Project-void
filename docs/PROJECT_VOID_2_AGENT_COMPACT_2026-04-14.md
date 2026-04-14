# Project VOID 2-Agent Compact Workflow
## Date: 2026-04-14

This is the fast version for running two phones/two agents.

---

## Lane Split

Agent A:
- Runtime/API integrity
- Core backend ownership

Agent B:
- Audio/voice/signal pipeline
- TTS and media flow ownership

---

## Branches

- Agent A: feat/void-2a-runtime-20260414
- Agent B: feat/void-2b-audio-20260414

---

## Agent A Prompt (Copy/Paste)

```text
You are Agent A for Project VOID.

Branch:
feat/void-2a-runtime-20260414

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
1) Improve runtime stability and API integrity.
2) Keep changes minimal and lane-contained.
3) Avoid any UI/docs edits.

Deliverables:
1) code changes in allowed paths
2) validation notes for impacted endpoints
3) PR summary: risk + rollback + checks

Rules:
- Do not edit forbidden paths.
- Rebase onto main before PR.
- Stop and report if overlap with Agent B is required.
```

---

## Agent B Prompt (Copy/Paste)

```text
You are Agent B for Project VOID.

Branch:
feat/void-2b-audio-20260414

Allowed paths:
- void_engine/radio_engine.py
- routes/radio.py
- routes/frequency_manual.py
- void_engine/void_language.py (TTS-related sections only)
- void_engine/stega.py
- void_engine/audio_stega.py
- void_engine/biophony.py
- void_engine/qalqala.py
- void_engine/tts_provider.py (only if absolutely required)

Forbidden paths:
- app.py
- routes/__init__.py
- templates/
- docs/

Objectives:
1) Improve voice/audio reliability.
2) Preserve endpoint compatibility.
3) Keep backend-wide refactors out of scope.

Deliverables:
1) code changes in allowed paths
2) validation notes for audio/TTS paths
3) PR summary: risk + rollback + endpoint checks

Rules:
- Do not edit forbidden paths.
- Rebase onto main before PR.
- Stop and report if conflict with Agent A ownership appears.
```

---

## Quick Start Commands

```bash
# Agent A
git checkout main && git pull origin main && git checkout -b feat/void-2a-runtime-20260414

# Agent B
git checkout main && git pull origin main && git checkout -b feat/void-2b-audio-20260414
```

---

## Merge Order

1. Merge Agent B first (audio lane).
2. Rebase Agent A branch onto updated main.
3. Resolve drift if needed.
4. Merge Agent A.

---

## 5-Minute Integration Smoke Test

Run after both PRs:

1. GET /health
2. GET /speak
3. GET /radio
4. GET /frequency-manual
5. GET /api/tts/health?probe=1

If all pass, seal cycle.
