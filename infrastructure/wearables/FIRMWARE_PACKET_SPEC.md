# Wearable Firmware Packet Spec (Week-1)

This spec is for edge devices posting to `POST /api/wearable/ingest`.

## Required Headers

- `Authorization: Bearer <VOID_WEARABLE_INGEST_TOKEN>`
- `Content-Type: application/json`

## JSON Payload

```json
{
  "packet_id": "fw-node-001-42",
  "device_profile": {
    "device_id": "node-001",
    "device_type": "hybrid_skin_node",
    "sampling_hz": 128,
    "channels": [
      {"name": "eeg_alpha", "unit": "uV", "min": 0.0, "max": 1.0},
      {"name": "eeg_beta", "unit": "uV", "min": 0.0, "max": 1.0},
      {"name": "emg_rms", "unit": "mV", "min": 0.0, "max": 2.0},
      {"name": "gsr_uS", "unit": "uS", "min": 0.0, "max": 20.0}
    ]
  },
  "sensor_values": {
    "eeg_alpha": 0.71,
    "eeg_beta": 0.62,
    "emg_rms": 0.28,
    "gsr_uS": 5.9
  },
  "timestamp": 1777777777.123,
  "retry_count": 0,
  "checksum_sha256": "<hex sha256 of canonical payload>"
}
```

## Checksum Canonicalization

Compute SHA-256 over the UTF-8 bytes of:

```python
json.dumps(
  {
    "device_profile": device_profile,
    "sensor_values": sensor_values,
    "timestamp": timestamp,
  },
  sort_keys=True,
  separators=(",", ":"),
  default=str,
)
```

## Retry Policy (Firmware)

1. Send packet with `retry_count = 0`.
2. If response is non-200 or network timeout, retry up to 3 times.
3. Keep same `packet_id` for retries; increment `retry_count` each attempt.
4. Backoff: 0.5s, 1.0s, 2.0s.
5. If all retries fail, store packet locally and re-attempt on next connectivity window.

## Fail-Closed Rules

- Unexpected top-level fields are rejected.
- Invalid checksum format or mismatch is rejected.
- Retry count outside 0..10 is rejected.
- Missing token config returns `503`.
