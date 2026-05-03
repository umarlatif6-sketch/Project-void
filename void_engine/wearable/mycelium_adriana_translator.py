from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from void_engine.al_jabr_286 import BASE_FREQ, fatiha_286_hexdigest_from_str
from void_engine.openclaw_bridge import build_sovereign_bridge_packet

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "infrastructure" / "wearables" / "device_profile_schema.json"


def load_device_profile_schema() -> Dict[str, Any]:
    if not _SCHEMA_PATH.exists():
        raise FileNotFoundError(f"missing_schema: {_SCHEMA_PATH}")
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_device_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    schema = load_device_profile_schema()
    required = schema.get("required_fields", [])

    for field in required:
        if field not in profile:
            return {"ok": False, "error": f"missing_field:{field}"}

    device_type = str(profile.get("device_type") or "")
    if device_type not in set(schema.get("device_types", [])):
        return {"ok": False, "error": "invalid_device_type"}

    channels = profile.get("channels")
    if not isinstance(channels, list) or not channels:
        return {"ok": False, "error": "invalid_channels"}

    supported = set(schema.get("supported_channel_names", []))
    for ch in channels:
        if not isinstance(ch, dict):
            return {"ok": False, "error": "invalid_channel_item"}
        name = str(ch.get("name") or "")
        if not name or name not in supported:
            return {"ok": False, "error": f"unsupported_channel:{name}"}

    return {"ok": True}


def _norm(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    v = (value - low) / (high - low)
    return max(0.0, min(1.0, v))


def translate_sensor_packet(
    *,
    device_profile: Dict[str, Any],
    sensor_values: Dict[str, float],
    timestamp: float | None = None,
) -> Dict[str, Any]:
    check = validate_device_profile(device_profile)
    if not check.get("ok"):
        return {
            "ok": False,
            "error": check.get("error"),
        }

    ts = float(timestamp if timestamp is not None else time.time())

    channel_map: Dict[str, Dict[str, Any]] = {}
    for ch in device_profile.get("channels", []):
        channel_map[str(ch.get("name"))] = ch

    alpha = float(sensor_values.get("eeg_alpha", 0.0))
    beta = float(sensor_values.get("eeg_beta", 0.0))
    emg = float(sensor_values.get("emg_rms", 0.0))
    gsr = float(sensor_values.get("gsr_uS", 0.0))

    stress_score = 0.0
    focus_score = 0.0

    if "eeg_beta" in channel_map:
        b = channel_map["eeg_beta"]
        stress_score += 0.45 * _norm(beta, float(b.get("min", 0.0)), float(b.get("max", 1.0)))
    if "gsr_uS" in channel_map:
        g = channel_map["gsr_uS"]
        stress_score += 0.35 * _norm(gsr, float(g.get("min", 0.0)), float(g.get("max", 20.0)))
    if "emg_rms" in channel_map:
        m = channel_map["emg_rms"]
        stress_score += 0.20 * _norm(emg, float(m.get("min", 0.0)), float(m.get("max", 2.0)))

    if "eeg_alpha" in channel_map:
        a = channel_map["eeg_alpha"]
        focus_score += 0.55 * _norm(alpha, float(a.get("min", 0.0)), float(a.get("max", 1.0)))
    if "eeg_beta" in channel_map:
        b = channel_map["eeg_beta"]
        focus_score += 0.25 * _norm(beta, float(b.get("min", 0.0)), float(b.get("max", 1.0)))
    if "emg_rms" in channel_map:
        m = channel_map["emg_rms"]
        focus_score += 0.20 * (1.0 - _norm(emg, float(m.get("min", 0.0)), float(m.get("max", 2.0))))

    stress_score = round(max(0.0, min(1.0, stress_score)), 4)
    focus_score = round(max(0.0, min(1.0, focus_score)), 4)

    state = "stable"
    resonance_hz = 432
    codon = "B-bb-L"
    if stress_score >= 0.75:
        state = "anomaly"
        resonance_hz = 442
        codon = "B-kk-S"
    elif focus_score >= 0.72 and stress_score < 0.45:
        state = "aligned"
        resonance_hz = 432
        codon = "B-tt-M"

    payload = {
        "ok": True,
        "device_id": str(device_profile.get("device_id")),
        "device_type": str(device_profile.get("device_type")),
        "timestamp": ts,
        "scores": {
            "stress": stress_score,
            "focus": focus_score,
        },
        "state": state,
        "codon": codon,
        "resonance_target_hz": resonance_hz,
        "machine_4000_payload": {
            "actuator_mode": "warning" if resonance_hz == 442 else "steady",
            "led_pattern": "amber-pulse" if resonance_hz == 442 else "cyan-stable",
            "safety_gate": "closed" if resonance_hz == 442 else "open",
        },
        "sensor_values": sensor_values,
    }

    envelope = build_sovereign_bridge_packet(
        operator_objective="wearable mycelium adriana translation",
        channel="wearable",
    )
    if not envelope:
        seed = f"wearable|{payload['device_id']}|{ts}"
        envelope = {
            "packet_id": fatiha_286_hexdigest_from_str(seed)[:64],
            "chain": 286,
            "base_frequency_hz": BASE_FREQ,
            "bridge_mode": "sovereign_opaque_transport",
        }

    wrapped = dict(payload)
    wrapped["sovereign_packet_id"] = envelope.get("packet_id")
    wrapped["chain"] = envelope.get("chain", 286)
    wrapped["base_frequency_hz"] = envelope.get("base_frequency_hz", BASE_FREQ)
    wrapped["bridge_mode"] = envelope.get("bridge_mode", "sovereign_opaque_transport")
    wrapped["al_jabr_286_hash"] = fatiha_286_hexdigest_from_str(
        json.dumps(payload, sort_keys=True, default=str)
    )
    return wrapped
