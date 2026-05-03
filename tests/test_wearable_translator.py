from __future__ import annotations

from void_engine.wearable.mycelium_adriana_translator import (
    translate_sensor_packet,
    validate_device_profile,
)


def _profile() -> dict:
    return {
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


def test_validate_device_profile_ok():
    result = validate_device_profile(_profile())
    assert result["ok"] is True


def test_translate_sensor_packet_outputs_machine_payload():
    values = {
        "eeg_alpha": 0.8,
        "eeg_beta": 0.7,
        "emg_rms": 0.4,
        "gsr_uS": 6.0,
    }
    out = translate_sensor_packet(device_profile=_profile(), sensor_values=values)

    assert out["ok"] is True
    assert out["device_id"] == "node-001"
    assert out["chain"] == 286
    assert "machine_4000_payload" in out
    assert out["resonance_target_hz"] in {432, 442}


def test_translate_sensor_packet_fails_on_bad_profile():
    bad = {"device_id": "x"}
    out = translate_sensor_packet(device_profile=bad, sensor_values={})
    assert out["ok"] is False
