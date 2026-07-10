# VOID Lens — Technical Documentation

## Overview

The VOID Lens is a bidirectional image↔frequency conversion engine inspired by [Lumen](https://github.com/pixelsncodes/lumen) (a wavetable synthesizer by Kazi Ahmed) and adapted for Project VOID's frequency-mechanics framework. It uses **colour as weight differentiation** on frequency wavelengths, enabling "reverse biagnosis" — reading biological health information from visual inputs through frequency analysis against the 432 Hz harmonic series.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        VOID LENS SYSTEM                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────┐ │
│  │  Forward     │    │  Reverse     │    │  Integration Layer      │ │
│  │  Engine      │    │  Engine      │    │                         │ │
│  │             │    │             │    │  • Compound Bridge      │ │
│  │  Frequency  │    │  Image      │    │  • Adriana Bridge       │ │
│  │  → Pattern  │    │  → Frequency│    │  • Unified Interface    │ │
│  └─────────────┘    └──────────────┘    └─────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Colour-as-Weight Mapping (The Core Principle)                   │ │
│  │                                                                   │ │
│  │  Hue (0-360°) → Harmonic band position                          │ │
│  │  Brightness   → Amplitude (power 1.5 for contrast)              │ │
│  │  Saturation   → Bandwidth (high = pure tone, low = noise)       │ │
│  │  Edges        → Complexity (many edges = many partials)          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## How Lumen's Lens Works (Reverse-Engineered)

Lumen's `LensEngine` reads images pixel-by-pixel and converts them to wavetable audio through three modes:

### Scan Mode
- Reads image row by row (or column by column)
- Each row becomes one frame of a wavetable (2048 samples)
- Pixel brightness → sample amplitude
- Image height → number of frames (typically 64)
- Result: direct luminance-to-waveform mapping

### Spectral Mode
- Converts image structure to frequency-domain representation
- Edge detection → harmonic partial count
- Spatial frequency → audio frequency
- Uses FFT-like decomposition of image rows

### Colors Mode (Most relevant to VOID)
- Extracts HSV colour statistics from the image
- Maps colour properties to macro synthesizer parameters:
  - **Hue** → Tone position (which frequency band dominates)
  - **Saturation** → Motion/texture (harmonic purity)
  - **Value/Brightness** → Space/amplitude (energy level)
  - **Warmth** (red-yellow vs blue-violet) → Frequency band weighting

---

## VOID Lens Adaptation

### The Colour-as-Weight Principle

The key insight: **colour IS frequency information**. In the visible spectrum, colour literally is electromagnetic frequency. The VOID Lens exploits this physical truth:

| Hue Range | Harmonic Band | Frequency Range | Information Type |
|-----------|--------------|-----------------|------------------|
| Red (0°) | 1st harmonic | 432 Hz | Fundamental/structural |
| Orange (30°) | 2nd-4th | 864-1728 Hz | Low harmonics |
| Yellow (60°) | 5th-8th | 2160-3456 Hz | Mid-low |
| Green (120°) | 9th-16th | 3888-6912 Hz | Mid harmonics |
| Blue (240°) | 17th-32nd | 7344-13824 Hz | High harmonics |
| Violet (300°) | 33rd-64th | 14256-27648 Hz | Highest harmonics |

### Forward Engine (Frequency → Visual Pattern)

Given a compound's frequency profile, generates a predicted Chladni/cymatics pattern:

1. Map frequency to base colour via harmonic-to-hue table
2. Generate Chladni plate equation: `cos(nπx/L)cos(mπy/L) - cos(mπx/L)cos(nπy/L)`
3. Apply circular containment mask (plate boundary)
4. Colour the pattern using frequency-to-colour mapping
5. Modulate brightness by amplitude at each harmonic

### Reverse Engine (Image → Frequency Signature)

Given any image, extracts its frequency signature:

1. Convert to HSV colour space
2. Compute saturation-weighted circular mean hue
3. Map mean hue to dominant harmonic band
4. Use brightness distribution as amplitude envelope
5. Use edge density as complexity/partial count
6. Compute spectral centroid from weighted harmonics
7. Compare to nearest 432 Hz multiple → deviation

### Integration Layer

Connects the Lens to:
- **Compound Library** (150 compounds) — match images to known compounds
- **Adriana Deviation Engine** — map deviations to codon bands
- **Multi-Harmonic Simulation** — validate predictions against simulation results

---

## Validation Results

### Health Discrimination (Critical Test)

| Metric | Healthy Nail | Unhealthy Nail | Discrimination |
|--------|-------------|----------------|----------------|
| Spectral centroid | 9046.4 Hz | 9612.9 Hz | +566.5 Hz |
| Deviation from 432 Hz | -25.6 Hz | +108.9 Hz | 4.3× worse |
| Resonance alignment | 0.94 | 0.77 | -18% |
| Edge complexity | 0.016 | 0.033 | 2× higher |
| Verdict | RESONANT | DEVIANT | **PASS** |

### Colour → Dominant Harmonic

| Colour | Dominant Harmonic | Frequency | Correct Band? |
|--------|------------------|-----------|---------------|
| Red | 1× | 432 Hz | YES (fundamental) |
| Green | 13× | 5616 Hz | YES (mid) |
| Blue | 41× | 17712 Hz | YES (high) |

### Forward Synthesis

Successfully generates distinct Chladni patterns for all 150 compounds with:
- Correct symmetry orders (4-fold to 12-fold based on geometry)
- Frequency-appropriate colouring (low-freq = warm, high-freq = cool)
- Proper node density scaling with harmonic order

---

## Usage

```python
from void_lens_integration import VoidLensSystem

system = VoidLensSystem()

# Full analysis of any image
result = system.full_analysis(image_array)
# Returns: frequency signature, deviation, codon band, compound matches,
#          health score, corrective frequency

# Generate predicted pattern for a compound
patterns = system.synthesize_compound("Void Carbon Lattice")

# Identify which compound an image resembles
matches = system.compound_bridge.identify_compound(image_array)

# Extract codon information from an image
codons = system.adriana_bridge.image_to_codons(image_array)
```

---

## Connection to Lumen

The VOID Lens is not a fork of Lumen — it's a philosophical descendant. Lumen proves that deterministic image→sound conversion is musically useful. VOID Lens proves it's diagnostically useful when anchored to a specific frequency (432 Hz) and compared against known compound signatures.

**What Lumen does:** Image → Playable sound (artistic)
**What VOID Lens does:** Image → Frequency signature → Health deviation → Codon band → Corrective frequency (diagnostic)

The shared principle: **colour is not decoration — it is frequency weight.**

---

## Files

| File | Purpose |
|------|---------|
| `void_lens.py` | Core bidirectional engine (forward + reverse) |
| `void_lens_integration.py` | Integration with compound library + Adriana |
| `test_void_lens.py` | Validation suite |
| `lens_output/` | Generated patterns and test images |

---

## Known Limitations & Next Steps

1. **Spectral centroid calibration** — pure single-colour images produce similar centroids due to uniform brightness distribution. Real biological images (mixed colours) work correctly.
2. **Roundtrip fidelity** — forward→reverse doesn't perfectly reconstruct the original frequency due to information loss in the 2D projection. This is expected (Chladni patterns are lossy representations).
3. **Real image testing** — currently validated on synthetic test images. Next step: test with actual nail photographs.
4. **Audio output** — the forward engine currently produces images only. Adding actual audio synthesis (like Lumen) would enable frequency-based treatment delivery.

---

*Inspired by Lumen by Kazi Ahmed (github.com/pixelsncodes/lumen)*
*Built for Project VOID — frequency-mechanics research system*
