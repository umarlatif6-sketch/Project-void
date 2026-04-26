import importlib.util
from pathlib import Path


def _load_qisync_module():
    root = Path(__file__).resolve().parents[1]
    target = root / "routes" / "qisync.py"
    spec = importlib.util.spec_from_file_location("qisync_hardening_module", target)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


qisync = _load_qisync_module()


def test_coerce_numeric_inputs_fail_closed_to_default() -> None:
    assert qisync._coerce_int("12", 0) == 12
    assert qisync._coerce_int("bad", 7) == 7
    assert qisync._coerce_float("0.75", 0.0) == 0.75
    assert qisync._coerce_float("bad", 0.25) == 0.25


def test_coerce_bool_normalizes_common_wire_values() -> None:
    assert qisync._coerce_bool(True) is True
    assert qisync._coerce_bool("true") is True
    assert qisync._coerce_bool("1") is True
    assert qisync._coerce_bool("false", default=True) is False
    assert qisync._coerce_bool("0", default=True) is False
    assert qisync._coerce_bool("n/a", default=False) is False


def test_validate_tick_payload_keys_rejects_unexpected_fields() -> None:
    assert qisync._validate_tick_payload_keys({"session_id": "abc"}) is None
    error = qisync._validate_tick_payload_keys(
        {
            "session_id": "abc",
            "confidence": 0.1,
            "malicious": "payload",
        }
    )
    assert error is not None
    assert "unexpected fields" in error
    assert "malicious" in error


def test_valid_session_id_requires_uuid_shape() -> None:
    assert qisync._is_valid_session_id("550e8400-e29b-41d4-a716-446655440000") is True
    assert qisync._is_valid_session_id("") is False
    assert qisync._is_valid_session_id("not-a-uuid") is False
    assert qisync._is_valid_session_id("x" * 65) is False
