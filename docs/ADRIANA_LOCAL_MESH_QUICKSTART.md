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
- `data/adriana_mesh_profiles.json`

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

## Notes

- If Ollama is unreachable, the runner falls back to mock output unless `--mock` is already set.
- Profile models are configurable in `data/adriana_mesh_profiles.json`.
- Keep profiles small (2B-3B) for CPU-only environments.
