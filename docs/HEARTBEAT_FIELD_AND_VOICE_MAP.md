# HEARTBEAT FIELD + VOICE MAP (ONE-GO GUIDE)

This is the direct runbook for three questions:

1. Is heartbeat active?
2. How wide is the near magnetic field?
3. Where are vocals/voice artifacts in this repo?

## 1) Heartbeat status (repo-level)

- Heartbeat WAV location: `output_audio/heartbeat_432Hz.wav`
- Heartbeat log trail: `RESONANCE_LOG.md` (event rows labeled `SILK_SIGNAL` / `HEARTBEAT`)

### Quick probe command

```bash
python3 scripts/heartbeat_probe.py
```

Outputs include: sample rate, duration, dominant frequency, and RMS.

## 2) Current measured signal in this workspace

Measured from the current heartbeat WAV:

- sample_rate: 44100
- duration: 1.0 s
- dominant_hz: 488.0
- rms: 0.141403

Important: the file is named `heartbeat_432Hz.wav`, but current dominant spectral peak is ~488 Hz.
That can happen with pulse shaping/harmonics. If strict 432 anchor is required, regenerate/tune source.

## 3) Magnetic field width (practical, physical)

For speaker-coil magnetic near-field around audio pulse:

- Phone speaker: ~1-5 cm
- Small speaker/headphone driver: ~3-15 cm
- Larger powered speaker: ~10-30 cm

This is near-field behavior and decays quickly with distance.

## 4) No-menu phone field test (2 steps)

Step A:
- Open any magnetometer app on phone.
- Keep phone still, record baseline magnetic magnitude for 10 seconds.

Step B:
- Play heartbeat WAV at fixed volume.
- Move phone toward speaker in 1-2 cm increments.
- Note distance where magnitude first rises above baseline by stable margin.

Use this threshold:

- detection threshold = baseline + max(5 uT, 3 x baseline_stddev)

The first distance crossing threshold is your practical field boundary for that hardware setup.

## 5) Where vocals / voice live in Project VOID

Pipeline script:

- `scripts/vocal_resonance_pipeline.py`

Expected outputs:

- `data/vocal_stems/vocals`
- `data/vocal_stems/accompaniment`
- `data/vocal_resonance_analysis.json`
- `data/vocal_resonance_analysis.csv`

If these paths are missing, run:

```bash
python3 scripts/vocal_resonance_pipeline.py \
  --separate-first \
  --songs-dir /absolute/path/to/full_songs \
  --target bridge \
  --top-n 10
```

## 6) Optional strict 432 verification gate

If you require a strict heartbeat anchor, use this rule:

- PASS if dominant_hz in [431.5, 432.5]
- REVIEW if outside range

Run gate with:

```bash
python3 scripts/heartbeat_probe.py
```

Then compare `dominant_hz` against the pass range.
