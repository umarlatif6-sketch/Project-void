# BURST REPORT — Void Stress Test Results

## Stress Test — 2026-02-18 06:04:14

- **Carrier**: ambient_drone_60s.wav
- **Duration**: 60.0s
- **Samples**: 2,646,000
- **Max Capacity**: 323.00 KB (LSB depth 1)
- **SNR Floor**: 15.0 dB
- **Tension Ceiling**: 40%
- **Probes**: 1

| Payload (MB) | Surface Tension % | SNR (dB) | Encode Time (s) | Grade |
|:---:|:---:|:---:|:---:|:---:|
| 1 | OVERFLOW | — | — | OVERFLOW |

**[BREAKPOINT FOUND]**: The Sapphire Bubble bursts at **1MB** for a 60s carrier.
- **Reason**: CAPACITY OVERFLOW

---

## Stress Test — 2026-02-18 06:04:35

- **Carrier**: ambient_drone_600s.wav
- **Duration**: 600.0s
- **Samples**: 26,460,000
- **Max Capacity**: 3.15 MB (LSB depth 1)
- **SNR Floor**: 15.0 dB
- **Tension Ceiling**: 40%
- **Probes**: 2

| Payload (MB) | Surface Tension % | SNR (dB) | Encode Time (s) | Grade |
|:---:|:---:|:---:|:---:|:---:|
| 1 | 38.9% | 31.1 | 60.4 | Clear |
| 2 | 81.5% | — | — | EXCEEDED |

**[BREAKPOINT FOUND]**: The Sapphire Bubble bursts at **2MB** for a 600s carrier.
- **Reason**: SURFACE TENSION exceeded 40% (reached 81.5%)

---

## Stress Test — 2026-04-06 05:33:36

- **Carrier**: _stress_carrier.wav
- **Duration**: 60.0s
- **Samples**: 2,646,000
- **Max Capacity**: 323.00 KB (LSB depth 1)
- **SNR Floor**: 15.0 dB
- **Tension Ceiling**: 40%
- **Probes**: 1

| Payload (MB) | Surface Tension % | SNR (dB) | Encode Time (s) | Grade |
|:---:|:---:|:---:|:---:|:---:|
| 1 | OVERFLOW | — | — | OVERFLOW |

**[BREAKPOINT FOUND]**: The Sapphire Bubble bursts at **1MB** for a 60s carrier.
- **Reason**: CAPACITY OVERFLOW

---
