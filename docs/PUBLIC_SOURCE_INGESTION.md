# Public Source Ingestion

This flow ingests public open-source or public-web material into the same resonance pipeline.

Use it for:
- Public GitHub repo summaries
- Public documentation notes
- Public architecture or benchmark digests
- Your own synthesis of open material

Do not use it to copy restricted or paywalled material.

## Run

```bash
python3 scripts/public_source_to_ecosystem_selective.py \
  --input data/public_source_voxcpm_template.jsonl \
  --output data/public_source_voxcpm_ecosystem.jsonl \
  --threshold 0.30 \
  --source-label public_source \
  --store-db
```

## Chronicle

```bash
python3 scripts/build_story_world_chronicle.py \
  --input data/public_source_voxcpm_ecosystem.jsonl \
  --output docs/PUBLIC_SOURCE_VOXCPM_CHRONICLE.md \
  --title "Public Source Chronicle"
```

## Unified Navigation

Open `/knowledge-tree` and use `Signals Navigator`.

- `Story world` shows your chapter-note intelligence
- `Public source` shows open-source/public-web signals
- `All signal feeds` mixes both

This lets you move across internal analogies and open-source architectures in one panel.