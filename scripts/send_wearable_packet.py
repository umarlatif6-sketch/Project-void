#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("VOID_WEARABLE_INGEST_URL", "http://127.0.0.1:5000/api/wearable/ingest")
TOKEN = os.environ.get("VOID_WEARABLE_INGEST_TOKEN", "")


def _checksum(device_profile: dict, sensor_values: dict, timestamp: float) -> str:
    canonical = {
        "device_profile": device_profile,
        "sensor_values": sensor_values,
        "timestamp": timestamp,
    }
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    if not TOKEN:
        print("missing VOID_WEARABLE_INGEST_TOKEN")
        return 1

    device_profile = {
        "device_id": "node-001",
        "device_type": "hybrid_skin_node",
        "sampling_hz": 128,
        "channels": [
            {"name": "eeg_alpha", "unit": "uV", "min": 0.0, "max": 1.0},
            {"name": "eeg_beta", "unit": "uV", "min": 0.0, "max": 1.0},
            {"name": "emg_rms", "unit": "mV", "min": 0.0, "max": 2.0},
            {"name": "gsr_uS", "unit": "uS", "min": 0.0, "max": 20.0},
        ],
    }
    sensor_values = {
        "eeg_alpha": 0.73,
        "eeg_beta": 0.58,
        "emg_rms": 0.31,
        "gsr_uS": 6.2,
    }

    packet_id = f"fw-node-001-{int(time.time())}"
    timestamp = time.time()
    payload = {
        "packet_id": packet_id,
        "device_profile": device_profile,
        "sensor_values": sensor_values,
        "timestamp": timestamp,
        "retry_count": 0,
    }
    payload["checksum_sha256"] = _checksum(device_profile, sensor_values, timestamp)

    body = json.dumps(payload).encode("utf-8")

    delays = [0.5, 1.0, 2.0]
    for attempt in range(0, 4):
        if attempt > 0:
            payload["retry_count"] = attempt
            body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            DEFAULT_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TOKEN}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                text = resp.read().decode("utf-8")
                print(text)
                return 0
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            print(f"attempt={attempt} status={exc.code} body={details}")
        except Exception as exc:  # noqa: BLE001
            print(f"attempt={attempt} error={exc}")

        if attempt < 3:
            time.sleep(delays[attempt])

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
