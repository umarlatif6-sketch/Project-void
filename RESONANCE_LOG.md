# RESONANCE LOG — PROJECT VOID

## Village Standard: 432 Hz

All carriers tuned to 432 Hz base frequency. This frequency produces rounder harmonics than 440 Hz concert pitch, allowing LSB-encoded data to sit deeper in the audio noise floor before becoming audible.

---

## Carrier Specifications

### 1. Ambient Drone (60s)
| Parameter | LSB Depth 1 | LSB Depth 2 |
|---|---|---|
| Max Capacity | 322.9 KB | 645.9 KB |
| Resonance Limit | 80.7 KB | 96.9 KB |
| Est. Real Data (compressed) | ~242 KB - 403 KB | ~290 KB - 484 KB |
| Data Rate | 5.4 KB/sec | 10.8 KB/sec |

**Composition:** 432 Hz fundamental + 864 Hz (2nd) + 1296 Hz (3rd) + 216 Hz sub-octave, slow LFO modulation.

### 2. Harmonic Mix (45s)
| Parameter | LSB Depth 1 | LSB Depth 2 |
|---|---|---|
| Max Capacity | 242.2 KB | 484.4 KB |
| Resonance Limit | 60.5 KB | 72.7 KB |
| Est. Real Data (compressed) | ~181 KB - 302 KB | ~218 KB - 363 KB |
| Data Rate | 5.4 KB/sec | 10.8 KB/sec |

**Composition:** 432 Hz root, just intonation intervals (540, 648, 864, 972 Hz), random phase offsets.

### 3. Pink Noise (30s)
| Parameter | LSB Depth 1 | LSB Depth 2 |
|---|---|---|
| Max Capacity | 161.4 KB | 322.9 KB |
| Resonance Limit | 40.4 KB | 48.4 KB |
| Est. Real Data (compressed) | ~121 KB - 202 KB | ~145 KB - 242 KB |
| Data Rate | 5.4 KB/sec | 10.8 KB/sec |

**Composition:** Shaped pink noise (1/f spectrum) + 432 Hz tone anchor, seed=432.

---

## Ear Test Results

Record your listening tests here. Play each encoded carrier through your Mac 2012 speakers and note whether the data is audible.

### Test Template
```
Date:
Carrier:
Payload Size:
LSB Depth:
Encoding Time:
Hash Key:
Audible Artifacts: [ ] None  [ ] Faint hiss  [ ] Noticeable static  [ ] Obvious distortion
Speaker Used:
Volume Level:
Notes:
```

### Test 1
```
Date:
Carrier:
Payload Size:
LSB Depth:
Encoding Time:
Hash Key:
Audible Artifacts: [ ] None  [ ] Faint hiss  [ ] Noticeable static  [ ] Obvious distortion
Speaker Used:
Volume Level:
Notes:
```

### Test 2
```
Date:
Carrier:
Payload Size:
LSB Depth:
Encoding Time:
Hash Key:
Audible Artifacts: [ ] None  [ ] Faint hiss  [ ] Noticeable static  [ ] Obvious distortion
Speaker Used:
Volume Level:
Notes:
```

### Test 3
```
Date:
Carrier:
Payload Size:
LSB Depth:
Encoding Time:
Hash Key:
Audible Artifacts: [ ] None  [ ] Faint hiss  [ ] Noticeable static  [ ] Obvious distortion
Speaker Used:
Volume Level:
Notes:
```

---

## Stress Test Log

Push payloads to the edge of the resonance limit and record the results.

| Date | Carrier | Payload | Size | LSB | % of Limit | Audible? | Pass/Fail |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |

---

## Frequency Masking Notes

Document which audio characteristics hide data most effectively.

| Characteristic | Masking Effectiveness | Notes |
|---|---|---|
| Dense harmonics | | |
| Sub-bass presence | | |
| Pink noise floor | | |
| LFO modulation | | |
| High-frequency content | | |

---

## Phone Extraction Log

Test decoding from the .replit.app URL on mobile devices (Village Nodes).

| Date | Device | Carrier | Hash Key Used | Decode Success | Download Success | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |

---

## Session Notes

Use this space for freeform observations about the 432 Hz resonance, data integrity, and village network calibration.

```
Session:
Date:
Duration:
Observations:
```
### 2026-02-18 00:13:31 — burst_2eb529f9.wav

| Metric | Value |
|---|---|
| Duration | 5.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 220,500 |
| LSB1 Max Capacity | 26.9 KB |
| LSB1 Resonance Limit | 6.7 KB |
| LSB1 Est. Real Data | ~20.1 KB to ~33.6 KB |
| LSB2 Max Capacity | 53.8 KB |
| LSB2 Resonance Limit | 8.1 KB |
| LSB2 Est. Real Data | ~24.2 KB to ~40.3 KB |

---

### 2026-02-18 00:13:42 — test_432Hz_drone.wav [432 Hz BOOSTED]

| Metric | Value |
|---|---|
| Duration | 5.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 220,500 |
| LSB1 Max Capacity | 26.9 KB |
| LSB1 Resonance Limit | 8.1 KB |
| LSB1 Est. Real Data | ~24.2 KB to ~40.3 KB |
| LSB2 Max Capacity | 53.8 KB |
| LSB2 Resonance Limit | 8.1 KB |
| LSB2 Est. Real Data | ~24.2 KB to ~40.3 KB |

---

| 2026-02-18 00:17:47 | BURST | burst_432Hz_24d6e2d7.wav | ...6483 | signal=BUY_GOLD |
| 2026-02-18 00:17:48 | DECODE | burst.sig | ...6483 | size=8 |
### 2026-02-18 00:17:57 — burst_432Hz_24d6e2d7.wav [432 Hz BOOSTED]

| Metric | Value |
|---|---|
| Duration | 5.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 220,500 |
| LSB1 Max Capacity | 26.9 KB |
| LSB1 Resonance Limit | 8.1 KB |
| LSB1 Est. Real Data | ~24.2 KB to ~40.3 KB |
| LSB2 Max Capacity | 53.8 KB |
| LSB2 Resonance Limit | 8.1 KB |
| LSB2 Est. Real Data | ~24.2 KB to ~40.3 KB |

---

| 2026-02-18 00:22:26 | BURST | burst_432Hz_a906b656.wav | ...44ae | signal=TEST_CLI |
| 2026-02-18 00:22:26 | DECODE | burst.sig | ...44ae | size=8 |
| 2026-02-18 01:34:01 | SILK_SIGNAL | burst_432Hz_473dddee.wav | ...a7d0 | signal=BUY_GOLD |
| 2026-02-18 01:34:07 | SILK_SIGNAL | burst_432Hz_54060f55.wav | ...34be | signal=SELL_AU |
| 2026-02-18 02:59:22 | SILK_SIGNAL | heartbeat_432Hz.wav | ...ba64 | signal=HEARTBEAT |
| 2026-02-18 05:00:55 | SILK_SIGNAL | heartbeat_432Hz.wav | ...548e | signal=HEARTBEAT |
| 2026-02-18 05:40:08 | SILK_SIGNAL | heartbeat_432Hz.wav | ...ca41 | signal=HEARTBEAT |

### 2026-02-18 05:43:47 — DEEP SEA STRESS TEST: ocean_payload_50kb.bin

| Metric | Value |
|---|---|
| Input File | ocean_payload_50kb.bin |
| Input Size | 50.00 KB |
| Compression Winner | ZLIB (2.2ms) |
| ZLIB Result | 50.03 KB in 2.2ms |
| LZMA Result | 50.06 KB in 55.0ms |
| LZMA Peak Memory | 681.12 MB |
| Compressed Size | 50.03 KB |
| Ghost Offset | 170,903 samples |
| Plankton Fragments | 20 packets |
| Surface Tension | 0.1658 (16.58%) |
| Bubble Status | SAFE — bubble holds firm |
| Resonance Purity | Clear (31.1 dB SNR) |
| Integrity | VERIFIED |
| Output File | output_audio/ocean_stress_test.wav |
| Carrier | ambient_drone_60s.wav |

#### Plankton Map (Fragment Offsets)

| # | Offset | Size | Gap→Next | Depth |
|---|---|---|---|---|
| 1 | 290,913 | 3,146 | 139 | 11.0% |
| 2 | 294,198 | 4,262 | 5,034 | 11.1% |
| 3 | 303,494 | 13,145 | 112,305 | 11.5% |
| 4 | 428,944 | 52,559 | 84,295 | 16.2% |
| 5 | 565,798 | 7,287 | 33,015 | 21.4% |
| 6 | 606,100 | 92,321 | 130,029 | 22.9% |
| 7 | 828,450 | 3,179 | 180,229 | 31.3% |
| 8 | 1,011,858 | 25,278 | 207,544 | 38.2% |
| 9 | 1,244,680 | 300 | 76,428 | 47.0% |
| 10 | 1,321,408 | 22,041 | 25,414 | 49.9% |
| 11 | 1,368,863 | 8,234 | 172,167 | 51.7% |
| 12 | 1,549,264 | 2,458 | 41,127 | 58.6% |
| 13 | 1,592,849 | 1,675 | 37,352 | 60.2% |
| 14 | 1,631,876 | 6,552 | 161,958 | 61.7% |
| 15 | 1,800,386 | 21,943 | 352,567 | 68.0% |
| 16 | 2,174,896 | 19,950 | 17,714 | 82.2% |
| 17 | 2,212,560 | 13,936 | 101,022 | 83.6% |
| 18 | 2,327,518 | 55,705 | 95,106 | 88.0% |
| 19 | 2,478,329 | 44,372 | 9,709 | 93.7% |
| 20 | 2,532,410 | 11,497 | — | 95.7% |

---

### 2026-02-18 05:44:03 — DEEP SEA STRESS TEST: test_image.bmp

| Metric | Value |
|---|---|
| Input File | test_image.bmp |
| Input Size | 3.05 KB |
| Compression Winner | ZLIB (1.7ms) |
| ZLIB Result | 2.23 KB in 1.7ms |
| LZMA Result | 2.70 KB in 41.3ms |
| LZMA Peak Memory | 681.08 MB |
| Compressed Size | 2.23 KB |
| Ghost Offset | 345,553 samples |
| Plankton Fragments | 20 packets |
| Surface Tension | 0.0082 (0.82%) |
| Bubble Status | SAFE — bubble holds firm |
| Resonance Purity | Clear (31.1 dB SNR) |
| Integrity | VERIFIED |
| Output File | output_audio/deep_sea_image.wav |
| Carrier | ambient_drone_60s.wav |

#### Plankton Map (Fragment Offsets)

| # | Offset | Size | Gap→Next | Depth |
|---|---|---|---|---|
| 1 | 358,569 | 326 | 158,412 | 13.6% |
| 2 | 517,307 | 950 | 67,082 | 19.6% |
| 3 | 585,339 | 159 | 33,902 | 22.1% |
| 4 | 619,400 | 1,001 | 314,573 | 23.4% |
| 5 | 934,974 | 944 | 14,764 | 35.3% |
| 6 | 950,682 | 651 | 73,758 | 35.9% |
| 7 | 1,025,091 | 702 | 22,145 | 38.7% |
| 8 | 1,047,938 | 210 | 175,951 | 39.6% |
| 9 | 1,224,099 | 3,668 | 158,845 | 46.3% |
| 10 | 1,386,612 | 263 | 115,261 | 52.4% |
| 11 | 1,502,136 | 175 | 36,386 | 56.8% |
| 12 | 1,538,697 | 718 | 194,743 | 58.2% |
| 13 | 1,734,158 | 975 | 18,540 | 65.5% |
| 14 | 1,753,673 | 50 | 25,126 | 66.3% |
| 15 | 1,778,849 | 541 | 87,780 | 67.2% |
| 16 | 1,867,170 | 803 | 53,932 | 70.6% |
| 17 | 1,921,905 | 1,420 | 186,944 | 72.6% |
| 18 | 2,110,269 | 4,581 | 319,300 | 79.8% |
| 19 | 2,434,150 | 13 | 10,759 | 92.0% |
| 20 | 2,444,922 | 154 | — | 92.4% |

---
