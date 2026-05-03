# Wearable Upgrade Week-1 Blueprint (Mycelium <-> Adriana)

Goal: build a wearable ingest lane and machine-control bridge in under 7 days using accessible components.

## Build Scope

- Skin/leather embedded sensing strip with conductive thread traces.
- Edge controller node for packetization and transport.
- Secure ingest into Project VOID via token-auth endpoint.
- Mycelium-to-Adriana translation into Machine 4000 actuation payload.

## Web-Verified Quick-Access Materials (checked 2026-05-03)

1. Conductive thread
- Stainless Thin Conductive Thread: https://www.adafruit.com/product/640 (HTTP 200)
- Stainless Medium Conductive Thread: https://www.adafruit.com/product/641 (HTTP 200)

2. Analog front-end / ADC
- ADS1115 16-bit ADC: https://www.adafruit.com/product/1085 (HTTP 200)

3. Motion and auxiliary sensing
- LSM6DSOX + LIS3MDL 9-DoF IMU: https://www.adafruit.com/product/4517 (HTTP 200)

4. Controller options
- ESP32-C3-DevKit-RUST-2: https://www.adafruit.com/product/5787 (HTTP 200)

5. Bio-sensing board options (higher capability)
- OpenBCI Ganglion: https://shop.openbci.com/products/ganglion-board (HTTP 200)
- OpenBCI Cyton (8-channel): https://shop.openbci.com/products/cyton-biosensing-board-8-channel (HTTP 200)

6. Skin-contact accessory option
- Grove GSR Sensor: https://www.seeedstudio.com/Grove-GSR-sensor-p-1614.html (HTTP 200)

Note: pages may show stock changes by region. Use at least two suppliers for critical parts.

## Minimum One-Week BOM (fast path)

- 1x ESP32-class controller (or equivalent)
- 1x ADS1115 ADC board
- 1x IMU board (optional but recommended)
- 1-2 spools conductive thread (thin + medium)
- Leather or silk substrate test strips (10 to 20 samples)
- Insulating backing tape / flexible liner
- Low-profile snap connectors or crimp pads
- USB power bank + charging cable

## 7-Day Execution Plan

Day 1: Materials and Jig Prep
- Acquire parts and prepare 10 substrate samples.
- Build a continuity jig for trace resistance checks.
- Define trace geometries (straight, loop, grid).

Day 2: Conductive Trace Build
- Stitch conductive traces into skin/leather/silk strips.
- Measure baseline ohm/cm for each sample.
- Reject outliers beyond your conductive target envelope.

Day 3: Sensor Bring-Up
- Integrate ADC and at least one signal lane (GSR or equivalent analog lane).
- Validate stable sampling at target rate.
- Add basic packet sender from controller.

Day 4: Secure Ingest
- Set VOID_WEARABLE_INGEST_TOKEN on server.
- Post packets to /api/wearable/ingest.
- Verify packets are accepted and logged.

Day 5: Translation Validation
- Confirm state outputs (stable/aligned/anomaly) from translator.
- Verify codon and resonance outputs map to expected scenarios.
- Check Machine 4000 payload behavior under low/high stress vectors.

Day 6: Wear Test and Durability
- Run motion + bend-cycle wear tests for 2-3 hours.
- Re-check resistance drift and packet loss.
- Harden weak points (strain relief and connector placement).

Day 7: Seal and Demo
- End-to-end demo: wearable packet -> secure ingest -> translation -> machine payload.
- Capture evidence pack: logs, resistance chart, false-trigger rate, uptime.
- Freeze Week-1 baseline and open Week-2 optimization backlog.

## Pass/Fail Gates for Week-1

- Ingest security: token-gated endpoint rejects unauthorized packets.
- Packet quality: at least 95% successful ingest over 30-minute test.
- Translator stability: deterministic state transitions under replayed vectors.
- Trace durability: no open-circuit events in 2-hour motion test.

## Integration Touchpoints

- Device schema: infrastructure/wearables/device_profile_schema.json
- Translator module: void_engine/wearable/mycelium_adriana_translator.py
- Secure ingest API: POST /api/wearable/ingest
- Admin audit API: GET /api/wearable/audit
