# Vocal Resonance Pipeline

This guide runs the full workflow in one place:

1. Separate vocals from full songs (Moises-style baseline using FFmpeg center extraction)
2. Analyze and score each vocal stem (432 vs 440)
3. Classify and recommend best carriers (sovereign, bridge, convention)

Script:
- scripts/vocal_resonance_pipeline.py

## Requirements

- Python 3.11+
- ffmpeg available on PATH
- numpy installed (already in requirements.txt)

Check ffmpeg:

```bash
ffmpeg -version
```

## Quick Start (All Three Steps)

Run separation + scoring + classification + recommendations in one command:

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --target bridge \
  --top-n 10
```

Outputs:
- data/vocal_stems/vocals
- data/vocal_stems/accompaniment
- data/vocal_resonance_analysis.json
- data/vocal_resonance_analysis.csv

## Export Adriana-Style TypeScript Library

You can export direct `MUSIC_LIBRARY` rows for app reuse:

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --target bridge \
  --top-n 10 \
  --export-ts data/musicLibrary.generated.ts
```

With CDN URL prefix:

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --export-ts data/musicLibrary.generated.ts \
  --cdn-base-url https://cdn.example.com/audio
```

## Common Modes

Bridge recommendations (between 432 and 440):

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --target bridge \
  --top-n 12
```

Sovereign recommendations (432-leaning):

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --target sovereign \
  --top-n 12
```

Convention recommendations (440-leaning):

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --target convention \
  --top-n 12
```

## Reuse Existing Analysis (No Audio Reprocessing)

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --from-json data/vocal_resonance_analysis.json \
  --target bridge \
  --top-n 10
```

## Notes

- Separation method is FFmpeg center extraction. It is lightweight and reproducible for all users.
- If you want higher-quality stem separation later, swap the separation step with Demucs/Spleeter, then keep the same scoring/classification/recommendation stages.
- The scoring outputs are intentionally shaped to match your existing 33-track style fields: dominantHz, energy432, energy440, tuning, rms, centroidHz.
