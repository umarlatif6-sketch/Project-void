# Story World Ingestion (Novel-Domain Resonance)

This flow lets you ingest high-value narrative intelligence from serial fiction ecosystems into the same 99-Names resonance pipeline used for Wikipedia.

## Scope

Use this for:
- Personal summaries and analogical notes
- Licensed exports
- Your own chapter annotations

Do not use this flow to ingest unlicensed copyrighted chapter text.

## Input Format

Preferred format is JSONL with one record per line:

```json
{"title":"...","text":"...","source":"user_notes","series":"...","chapter":"...","url":"...","tags":"..."}
```

Template file:
- [data/story_world_ingest_template.jsonl](data/story_world_ingest_template.jsonl)

## Run

```bash
python3 scripts/story_world_to_ecosystem_selective.py \
  --input data/story_world_ingest_template.jsonl \
  --output data/story_world_ecosystem.jsonl \
  --threshold 0.40 \
  --source-label story_world \
  --store-db
```

## Output

- `data/story_world_ecosystem.jsonl`: accepted records with tree payload
- `data/story_world_ecosystem.jsonl.story.checkpoint.json`: checkpoint and summary
- `knowledge_tree_nodes` table: persisted records when `--store-db` is used

Each accepted record now also contains:
- `analogies`: extracted analogy/metaphor sentences
- `perspectives`: extracted forward-looking/prospective sentences

This makes chapter-note intelligence directly queryable for chronicle synthesis.

## Build Chronicle Digest

```bash
python3 scripts/build_story_world_chronicle.py \
  --input data/story_world_ecosystem.jsonl \
  --output docs/STORY_WORLD_CHRONICLE.md
```

The chronicle groups signals by series and highlights top-fit entries, dominant domains,
and one primary analogy/perspective per entry.

## Optional: Build Graph

```bash
python3 scripts/build_ecosystem_resonance_graph.py \
  --corpus data/story_world_ecosystem.jsonl \
  --output data/story_world_resonance_graph.json
```

Then open the app and explore in the Knowledge Tree UI.
