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
