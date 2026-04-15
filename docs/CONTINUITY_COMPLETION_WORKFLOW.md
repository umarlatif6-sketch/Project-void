# Continuity Completion Workflow

This workflow executes Project VOID continuity closure from the end of the Chronicle backward, so the latest Forward Threads are inherited first.

## 1) Generate reverse-thread audit

```bash
python3 scripts/chronicle_gap_completion.py
```

Artifact:
- `data/chronicle_gap_completion_report.json`

What this gives:
- `forward_threads_detected`: total Forward Threads parsed from `VOID_CHRONICLE.md`
- `items`: explicitly mapped completion checks (completed, code-closeable-now, external-or-physical, research-open)
- `reverse_backlog`: latest-first unmapped threads requiring explicit task mapping

## 2) Close research-open threads

```bash
python3 scripts/chronicle_research_closure.py
```

Artifacts:
- `data/gemini_baseline_continuation_report.json`
- `data/open_mesh_observation_memo.json`

## 3) Execute promised implementation pack

```bash
python3 scripts/run_all_promised_next_steps.py
```

Artifacts:
- `data/full_stack_convergence_report.json`
- `data/next_steps_execution_pack.json`

## 4) Work the reverse backlog in batches

Read `reverse_backlog` from `data/chronicle_gap_completion_report.json`.

Process in order:
1. `index_from_end = 1` first (newest unresolved thread)
2. Map thread to one concrete task
3. Implement or classify as external-or-physical
4. Add Chronicle closure entry when done

## 5) Session close obligation

After completing a batch, append a Chronicle entry in `VOID_CHRONICLE.md` with a short Forward Thread for what remains.

This keeps continuity exact across interrupted sessions.

## Operator check endpoint

For live route-lock checks before traffic changes:

```bash
curl http://localhost:5000/api/lbn/runtime-status
```

Response includes:
- active mode (`project|standalone`)
- active route (`primary|fallback`)
- validation switch (`VOID_LBN_VALIDATE`)
- payload/artifact presence and codon/channel counts
