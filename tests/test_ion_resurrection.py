from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "infrastructure" / "energy_systems" / "ion_resurrection.py"
    spec = importlib.util.spec_from_file_location("ion_resurrection", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["ion_resurrection"] = module
    spec.loader.exec_module(module)
    return module


def test_scan_for_drift_bounds():
    mod = _load_module()
    resurrector = mod.IonResurrector()
    sample = mod.BatterySample(
        chemistry="li_ion",
        open_circuit_voltage_v=2.7,
        nominal_voltage_v=3.7,
        internal_resistance_mohm=320.0,
        state_of_health_pct=52.0,
    )
    drift = resurrector.scan_for_drift(sample)
    assert 0.0 <= drift <= 1.0


def test_frequency_calibration_is_bounded():
    mod = _load_module()
    resurrector = mod.IonResurrector(target_frequency_hz=432.0)
    env = mod.EnvironmentProfile(temperature_c=60.0, relative_humidity_pct=95.0)
    out = resurrector.calibrate_frequency(env)
    assert 414.0 <= out <= 450.0


def test_execute_protocol_returns_state_and_plan():
    mod = _load_module()
    resurrector = mod.IonResurrector()
    sample = mod.BatterySample(
        chemistry="lead_acid",
        open_circuit_voltage_v=10.4,
        nominal_voltage_v=12.0,
        internal_resistance_mohm=280.0,
        state_of_health_pct=45.0,
    )
    env = mod.EnvironmentProfile(temperature_c=33.0, relative_humidity_pct=68.0)

    result = resurrector.execute_protocol(
        sample=sample,
        env=env,
        district_key="soan_valley",
        water_trend_slope_cm_per_year=-1.1,
    )

    assert result["ok"] is True
    assert result["state"] in {"RE-ANIMATED", "STABLE"}
    assert "pwm_plan" in result
    assert "gee_policy" in result
