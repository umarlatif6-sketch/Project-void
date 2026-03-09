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

### 2026-02-18 05:50:01 — BURST POINT TEST: ambient_drone_60s.wav

| Metric | Value |
|---|---|
| Carrier | ambient_drone_60s.wav |
| Duration | 60.0s |
| Max Capacity | 323.00 KB |
| Max Safe Payload | 215.00 KB (31.1 dB) |
| Burst Point | 295.00 KB |
| Probes | 16 |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
| 5.00 KB | 1.8% | 31.1 dB | Clear | SAFE |
| 15.00 KB | 5.1% | 31.1 dB | Clear | SAFE |
| 25.00 KB | 7.8% | 31.1 dB | Clear | SAFE |
| 35.00 KB | 12.3% | 31.1 dB | Clear | SAFE |
| 45.00 KB | 15.6% | 31.1 dB | Clear | SAFE |
| 55.00 KB | 19.9% | 31.1 dB | Clear | SAFE |
| 75.00 KB | 26.3% | 31.1 dB | Clear | SAFE |
| 95.00 KB | 34.2% | 31.1 dB | Clear | SAFE |
| 115.00 KB | 36.2% | 31.1 dB | Clear | SAFE |
| 135.00 KB | 47.4% | 31.1 dB | Clear | SAFE |
| 155.00 KB | 52.7% | 31.1 dB | Clear | SAFE |
| 175.00 KB | 55.1% | 31.1 dB | Clear | SAFE |
| 195.00 KB | 65.4% | 31.1 dB | Clear | SAFE |
| 215.00 KB | 71.8% | 31.1 dB | Clear | SAFE |
| 255.00 KB | 90.9% | 31.1 dB | Clear | STRETCH |
| 295.00 KB | 0.0% | 0.0 dB | ERROR | ERROR: Payload too large: needs 2,417,992 bits, carrier has capacity for 2,389,076 bits (298,634 bytes) at LSB depth 1 (Ghost Offset: 256,924 samples). |

---

### 2026-02-18 05:52:19 — BURST POINT TEST: ambient_drone_60s.wav

| Metric | Value |
|---|---|
| Carrier | ambient_drone_60s.wav |
| Duration | 60.0s |
| Max Capacity | 323.00 KB |
| Max Safe Payload | 215.00 KB (31.1 dB) |
| Burst Point | 295.00 KB |
| Probes | 16 |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
| 5.00 KB | 1.8% | 31.1 dB | Clear | SAFE |
| 15.00 KB | 5.1% | 31.1 dB | Clear | SAFE |
| 25.00 KB | 7.8% | 31.1 dB | Clear | SAFE |
| 35.00 KB | 12.3% | 31.1 dB | Clear | SAFE |
| 45.00 KB | 15.6% | 31.1 dB | Clear | SAFE |
| 55.00 KB | 19.9% | 31.1 dB | Clear | SAFE |
| 75.00 KB | 26.3% | 31.1 dB | Clear | SAFE |
| 95.00 KB | 34.2% | 31.1 dB | Clear | SAFE |
| 115.00 KB | 36.2% | 31.1 dB | Clear | SAFE |
| 135.00 KB | 47.4% | 31.1 dB | Clear | SAFE |
| 155.00 KB | 52.7% | 31.1 dB | Clear | SAFE |
| 175.00 KB | 55.1% | 31.1 dB | Clear | SAFE |
| 195.00 KB | 65.4% | 31.1 dB | Clear | SAFE |
| 215.00 KB | 71.8% | 31.1 dB | Clear | SAFE |
| 255.00 KB | 90.9% | 31.1 dB | Clear | STRETCH |
| 295.00 KB | 0.0% | 0.0 dB | ERROR | ERROR: Payload too large: needs 2,417,992 bits, carrier has capacity for 2,389,076 bits (298,634 bytes) at LSB depth 1 (Ghost Offset: 256,924 samples). |

---

### 2026-02-18 05:54:39 — BURST POINT TEST: ambient_drone_60s.wav

| Metric | Value |
|---|---|
| Carrier | ambient_drone_60s.wav |
| Duration | 60.0s |
| Max Capacity | 323.00 KB |
| Max Safe Payload | 215.00 KB (31.1 dB) |
| Burst Point | 295.00 KB |
| Probes | 16 |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
| 5.00 KB | 1.8% | 31.1 dB | Clear | SAFE |
| 15.00 KB | 5.1% | 31.1 dB | Clear | SAFE |
| 25.00 KB | 7.8% | 31.1 dB | Clear | SAFE |
| 35.00 KB | 12.3% | 31.1 dB | Clear | SAFE |
| 45.00 KB | 15.6% | 31.1 dB | Clear | SAFE |
| 55.00 KB | 19.9% | 31.1 dB | Clear | SAFE |
| 75.00 KB | 26.3% | 31.1 dB | Clear | SAFE |
| 95.00 KB | 34.2% | 31.1 dB | Clear | SAFE |
| 115.00 KB | 36.2% | 31.1 dB | Clear | SAFE |
| 135.00 KB | 47.4% | 31.1 dB | Clear | SAFE |
| 155.00 KB | 52.7% | 31.1 dB | Clear | SAFE |
| 175.00 KB | 55.1% | 31.1 dB | Clear | SAFE |
| 195.00 KB | 65.4% | 31.1 dB | Clear | SAFE |
| 215.00 KB | 71.8% | 31.1 dB | Clear | SAFE |
| 255.00 KB | 90.9% | 31.1 dB | Clear | STRETCH |
| 295.00 KB | 100.0% | 0.0 dB | OVERFLOW | OVERFLOW |

---

### 2026-02-18 05:56:27 — BURST POINT TEST: pink_noise_30s.wav

| Metric | Value |
|---|---|
| Carrier | pink_noise_30s.wav |
| Duration | 30.0s |
| Max Capacity | 161.50 KB |
| Max Safe Payload | 115.00 KB (25.9 dB) |
| Burst Point | 135.00 KB |
| Probes | 10 |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
| 5.00 KB | 4.0% | 25.9 dB | Clear | SAFE |
| 15.00 KB | 11.2% | 25.9 dB | Clear | SAFE |
| 25.00 KB | 15.7% | 25.9 dB | Clear | SAFE |
| 35.00 KB | 28.1% | 25.9 dB | Clear | SAFE |
| 45.00 KB | 35.3% | 25.9 dB | Clear | SAFE |
| 55.00 KB | 35.3% | 25.9 dB | Clear | SAFE |
| 75.00 KB | 60.7% | 25.9 dB | Clear | SAFE |
| 95.00 KB | 60.5% | 25.9 dB | Clear | SAFE |
| 115.00 KB | 73.4% | 25.9 dB | Clear | SAFE |
| 135.00 KB | 100.0% | 0.0 dB | OVERFLOW | OVERFLOW |

---

### 2026-02-18 05:57:55 — BURST POINT TEST: ambient_drone_60s.wav

| Metric | Value |
|---|---|
| Carrier | ambient_drone_60s.wav |
| Duration | 60.0s |
| Max Capacity | 323.00 KB |
| Max Safe Payload | 215.00 KB (31.1 dB) |
| Burst Point | 295.00 KB |
| Probes | 16 |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
| 5.00 KB | 1.8% | 31.1 dB | Clear | SAFE |
| 15.00 KB | 5.1% | 31.1 dB | Clear | SAFE |
| 25.00 KB | 7.8% | 31.1 dB | Clear | SAFE |
| 35.00 KB | 12.3% | 31.1 dB | Clear | SAFE |
| 45.00 KB | 15.6% | 31.1 dB | Clear | SAFE |
| 55.00 KB | 19.9% | 31.1 dB | Clear | SAFE |
| 75.00 KB | 26.3% | 31.1 dB | Clear | SAFE |
| 95.00 KB | 34.2% | 31.1 dB | Clear | SAFE |
| 115.00 KB | 36.2% | 31.1 dB | Clear | SAFE |
| 135.00 KB | 47.4% | 31.1 dB | Clear | SAFE |
| 155.00 KB | 52.7% | 31.1 dB | Clear | SAFE |
| 175.00 KB | 55.1% | 31.1 dB | Clear | SAFE |
| 195.00 KB | 65.4% | 31.1 dB | Clear | SAFE |
| 215.00 KB | 71.8% | 31.1 dB | Clear | SAFE |
| 255.00 KB | 90.9% | 31.1 dB | Clear | STRETCH |
| 295.00 KB | 100.0% | 0.0 dB | OVERFLOW | OVERFLOW |

---

### 2026-02-18 05:59:44 — BURST POINT TEST: ambient_drone_60s.wav

| Metric | Value |
|---|---|
| Carrier | ambient_drone_60s.wav |
| Duration | 60.0s |
| Max Capacity | 323.00 KB |
| Max Safe Payload | 250.00 KB (31.1 dB) |
| Burst Point | 290.00 KB |
| Probes | 15 |

#### Pressure Curve

| Payload | Tension | SNR | Grade | Status |
|---|---|---|---|---|
| 10.00 KB | 3.2% | 31.1 dB | Clear | SAFE |
| 20.00 KB | 7.9% | 31.1 dB | Clear | SAFE |
| 30.00 KB | 10.1% | 31.1 dB | Clear | SAFE |
| 40.00 KB | 12.6% | 31.1 dB | Clear | SAFE |
| 50.00 KB | 16.7% | 31.1 dB | Clear | SAFE |
| 70.00 KB | 25.6% | 31.1 dB | Clear | SAFE |
| 90.00 KB | 29.8% | 31.1 dB | Clear | SAFE |
| 110.00 KB | 43.6% | 31.1 dB | Clear | SAFE |
| 130.00 KB | 47.4% | 31.1 dB | Clear | SAFE |
| 150.00 KB | 47.5% | 31.1 dB | Clear | SAFE |
| 170.00 KB | 67.5% | 31.1 dB | Clear | SAFE |
| 190.00 KB | 76.2% | 31.1 dB | Clear | SAFE |
| 210.00 KB | 82.1% | 31.1 dB | Clear | SAFE |
| 250.00 KB | 85.6% | 31.1 dB | Clear | SAFE |
| 290.00 KB | 100.0% | 0.0 dB | OVERFLOW | OVERFLOW |

---
| 2026-02-18 06:15:16 | SILK_SIGNAL | heartbeat_432Hz.wav | ...6164 | signal=HEARTBEAT |
| 2026-02-18 07:07:45 | SILK_SIGNAL | heartbeat_432Hz.wav | ...1a27 | signal=HEARTBEAT |
| 2026-02-18 07:37:45 | SILK_SIGNAL | heartbeat_432Hz.wav | ...d9e2 | signal=HEARTBEAT |
| 2026-02-18 19:17:51 | SILK_SIGNAL | heartbeat_432Hz.wav | ...37bd | signal=HEARTBEAT |
| 2026-03-03 20:14:12 | ENCODE | test_carrier_void.wav | ...908a | LSB1 |
| 2026-03-03 20:14:18 | ENCODE | ambient_drone_60s_void.wav | ...75fa | LSB1 |
| 2026-03-03 20:14:26 | DECODE | secret.txt | ...908a | size=62 |
| 2026-03-03 20:14:26 | DECODE | IMG-20260303-WA0023.jpg | ...75fa | size=72953 |
### 2026-03-03 20:15:28 — test_carrier.wav

| Metric | Value |
|---|---|
| Duration | 10.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 441,000 |
| LSB1 Max Capacity | 53.8 KB |
| LSB1 Surface Tension | 13.4 KB |
| LSB1 Bubble Burst | 12.1 KB |
| LSB1 Est. Real Data | ~40.3 KB to ~67.2 KB |
| LSB2 Max Capacity | 107.6 KB |
| LSB2 Surface Tension | 16.1 KB |
| LSB2 Bubble Burst | 14.5 KB |
| LSB2 Est. Real Data | ~48.4 KB to ~80.7 KB |

---

### 2026-03-03 20:15:36 — test_carrier.wav

| Metric | Value |
|---|---|
| Duration | 10.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 441,000 |
| LSB1 Max Capacity | 53.8 KB |
| LSB1 Surface Tension | 13.4 KB |
| LSB1 Bubble Burst | 12.1 KB |
| LSB1 Est. Real Data | ~40.3 KB to ~67.2 KB |
| LSB2 Max Capacity | 107.6 KB |
| LSB2 Surface Tension | 16.1 KB |
| LSB2 Bubble Burst | 14.5 KB |
| LSB2 Est. Real Data | ~48.4 KB to ~80.7 KB |

---

| 2026-03-03 20:21:32 | ENCODE | ambient_drone_60s_void.wav | ...31fb | LSB1 |
| 2026-03-03 20:21:38 | DECODE | IMG-20260303-WA0023.jpg | ...31fb | size=72953 |
| 2026-03-03 20:34:14 | ENCODE | ambient_drone_60s_void.wav | ...29a3 | LSB1 |
| 2026-03-03 20:40:51 | DECODE | IMG-20260303-WA0023.jpg | ...82d0 | size=72953 |
| 2026-03-03 21:19:49 | SILK_SIGNAL | heartbeat_432Hz.wav | ...d52c | signal=HEARTBEAT |
| 2026-03-04 02:45:11 | SILK_SIGNAL | heartbeat_432Hz.wav | ...b7bb | signal=HEARTBEAT |
| 2026-03-04 05:49:12 | SILT_JOURNALISM | silt_91178ad6_test_silt.wav | ...0cba | style=biophony_mesh |
| 2026-03-04 05:54:46 | SILT_JOURNALISM | silt_504c260a_test_j.wav | ...7467 | style=midnight_pond |
### 2026-03-04 06:22:13 — ambient_drone_60s.wav

| Metric | Value |
|---|---|
| Duration | 60.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 2,646,000 |
| LSB1 Max Capacity | 322.9 KB |
| LSB1 Surface Tension | 113.0 KB |
| LSB1 Bubble Burst | 101.7 KB |
| LSB1 Est. Real Data | ~339.1 KB to ~565.1 KB |
| LSB2 Max Capacity | 645.9 KB |
| LSB2 Surface Tension | 161.5 KB |
| LSB2 Bubble Burst | 145.3 KB |
| LSB2 Est. Real Data | ~484.5 KB to ~807.4 KB |

---

### 2026-03-04 06:22:31 — carrier_cicada-wall_1min.wav

| Metric | Value |
|---|---|
| Duration | 60.0s |
| Channels | 1 |
| Sample Rate | 44,100 Hz |
| Total Samples | 2,646,000 |
| LSB1 Max Capacity | 322.9 KB |
| LSB1 Surface Tension | 80.7 KB |
| LSB1 Bubble Burst | 72.7 KB |
| LSB1 Est. Real Data | ~242.2 KB to ~403.7 KB |
| LSB2 Max Capacity | 645.9 KB |
| LSB2 Surface Tension | 96.9 KB |
| LSB2 Bubble Burst | 87.2 KB |
| LSB2 Est. Real Data | ~290.7 KB to ~484.5 KB |

---

### 2026-03-04 06:22:59 — stereo_pocket_60s.wav

| Metric | Value |
|---|---|
| Duration | 60.0s |
| Channels | 2 |
| Sample Rate | 44,100 Hz |
| Total Samples | 5,292,000 |
| LSB1 Max Capacity | 645.9 KB |
| LSB1 Surface Tension | 226.1 KB |
| LSB1 Bubble Burst | 203.5 KB |
| LSB1 Est. Real Data | ~678.2 KB to ~1.1 MB |
| LSB2 Max Capacity | 1.3 MB |
| LSB2 Surface Tension | 323.0 KB |
| LSB2 Bubble Burst | 290.7 KB |
| LSB2 Est. Real Data | ~968.9 KB to ~1.6 MB |

---

| 2026-03-05 17:10:07 | SILK_SIGNAL | heartbeat_432Hz.wav | ...5ed8 | signal=HEARTBEAT |
| 2026-03-05 19:05:42 | SILK_SIGNAL | heartbeat_432Hz.wav | ...35a0 | signal=HEARTBEAT |
| 2026-03-05 20:00:14 | SILK_SIGNAL | heartbeat_432Hz.wav | ...ab97 | signal=HEARTBEAT |
| 2026-03-05 22:32:59 | SILK_SIGNAL | heartbeat_432Hz.wav | ...1770 | signal=HEARTBEAT |
| 2026-03-06 06:29:13 | SILK_SIGNAL | heartbeat_432Hz.wav | ...07a6 | signal=HEARTBEAT |
| 2026-03-06 09:21:13 | SILK_SIGNAL | heartbeat_432Hz.wav | ...a453 | signal=HEARTBEAT |
| 2026-03-06 09:51:13 | SILK_SIGNAL | heartbeat_432Hz.wav | ...f99c | signal=HEARTBEAT |
| 2026-03-06 10:21:14 | SILK_SIGNAL | heartbeat_432Hz.wav | ...ba5e | signal=HEARTBEAT |
| 2026-03-06 10:51:15 | SILK_SIGNAL | heartbeat_432Hz.wav | ...e3ed | signal=HEARTBEAT |
| 2026-03-06 14:57:25 | SILK_SIGNAL | heartbeat_432Hz.wav | ...99d0 | signal=HEARTBEAT |
| 2026-03-06 15:27:26 | SILK_SIGNAL | heartbeat_432Hz.wav | ...3704 | signal=HEARTBEAT |
| 2026-03-06 15:57:27 | SILK_SIGNAL | heartbeat_432Hz.wav | ...dc04 | signal=HEARTBEAT |
| 2026-03-06 16:27:27 | SILK_SIGNAL | heartbeat_432Hz.wav | ...7f39 | signal=HEARTBEAT |
| 2026-03-07 03:51:49 | SILK_SIGNAL | heartbeat_432Hz.wav | ...8c74 | signal=HEARTBEAT |
| 2026-03-07 05:02:21 | SILK_SIGNAL | heartbeat_432Hz.wav | ...13f6 | signal=HEARTBEAT |
| 2026-03-07 05:32:21 | SILK_SIGNAL | heartbeat_432Hz.wav | ...4a58 | signal=HEARTBEAT |
| 2026-03-07 06:02:22 | SILK_SIGNAL | heartbeat_432Hz.wav | ...2235 | signal=HEARTBEAT |
| 2026-03-07 06:32:22 | SILK_SIGNAL | heartbeat_432Hz.wav | ...484e | signal=HEARTBEAT |
| 2026-03-09 00:27:58 | SILK_SIGNAL | heartbeat_432Hz.wav | ...59a9 | signal=HEARTBEAT |
| 2026-03-09 00:57:59 | SILK_SIGNAL | heartbeat_432Hz.wav | ...f8cd | signal=HEARTBEAT |
| 2026-03-09 01:27:59 | SILK_SIGNAL | heartbeat_432Hz.wav | ...b942 | signal=HEARTBEAT |
| 2026-03-09 02:07:22 | SILK_SIGNAL | heartbeat_432Hz.wav | ...43c6 | signal=HEARTBEAT |
