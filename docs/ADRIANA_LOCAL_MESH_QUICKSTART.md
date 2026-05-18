# Adriana Local Mesh Quickstart

This is a lightweight local multi-cell runner for Adriana behavior shaping.

## What it does

The runner executes four cells in sequence:

1. router
2. research
3. voice
4. critic

It writes each run to `data/adriana_mesh_runs/*.json` so sandboxes can share artifacts by passing prior run files as peer inputs.

## Files

- `scripts/adriana_local_mesh.py`
- `scripts/adriana_mesh_eval.py`
- `scripts/adriana_mesh_readiness.py`
- `data/adriana_mesh_profiles.json`
- `data/adriana_eval_prompts.json`
- `routes/adriana_mesh.py`

## Fast start (mock mode)

Use this when Ollama models are not installed yet.

```bash
/usr/bin/python3 scripts/adriana_local_mesh.py \
  --prompt "Design a one-week sales sprint for VOID" \
  --profile ultra_light \
  --sandbox sandbox_a \
  --mock
```

## Run with local Ollama

1. Pull models from your profile.

```bash
ollama pull gemma2:2b
ollama pull qwen2.5:3b
ollama pull phi3:mini
ollama pull llama3.2:3b
```

2. Run mesh with the CPU-light profile.

```bash
/usr/bin/python3 scripts/adriana_local_mesh.py \
  --prompt "Build a practical launch plan for Adriana mesh" \
  --profile cpu_light \
  --sandbox sandbox_a
```

## Connect sandboxes

Use prior artifact files from one sandbox as peer context in another.

```bash
/usr/bin/python3 scripts/adriana_local_mesh.py \
  --prompt "Refine plan with risk controls" \
  --profile cpu_light \
  --sandbox sandbox_b \
  --peer data/adriana_mesh_runs/mesh_YYYYMMDD_HHMMSS_sandbox_a.json
```

## Run 20-prompt evaluation harness

```bash
/usr/bin/python3 scripts/adriana_mesh_eval.py \
  --profile cpu_light \
  --mock
```

This writes an evaluation report to `data/adriana_mesh_runs/adriana_eval_report_<timestamp>.json`.

## Run real-model readiness check

```bash
/usr/bin/python3 scripts/adriana_mesh_readiness.py \
  --profile cpu_light
```

This verifies Ollama reachability, required model presence, two connected runs (`readiness_a` and `readiness_b`), and whether all cells used real Ollama mode without fallback.

## API routes

The mesh is exposed through these endpoints:

- `GET /api/adriana/mesh/profiles`
- `POST /api/adriana/mesh/run`
- `POST /api/adriana/mesh/eval`

## Notes

- If Ollama is unreachable, the runner falls back to mock output unless `--mock` is already set.
- Profile models are configurable in `data/adriana_mesh_profiles.json`.
- Keep profiles small (2B-3B) for CPU-only environments.
