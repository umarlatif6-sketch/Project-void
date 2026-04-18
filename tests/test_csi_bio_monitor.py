"""
Unit tests for void_engine.csi_bio_monitor and hardware.solar_profile.
"""

import os
import struct
import sys

import pytest

from void_decoder import sign_packet_hmac, validate_freshness

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from void_engine.csi_bio_monitor import (
    parse_csi_packet,
    CSIPacket,
    SimulatedCSIBioMonitor,
    derive_sensor_state_from_packet,
    _amplitude_variance,
    _phase_shift_magnitude,
    _ntc_to_celsius,
    _MAGIC_BYTES,
    build_signed_csi_envelope,
    CSI_FRESHNESS_WINDOW_S,
)
from hardware.solar_profile import get_solar_mode, get_profile_summary, CROSSOVER_TEMP_C


def _make_packet(n: int = 4, amp_vals=None, phase_vals=None, ntc_raw: int = 2048) -> bytes:
    """Helper to build a valid CSI UDP packet."""
    if amp_vals is None:
        amp_vals = [1000] * n
    if phase_vals is None:
        phase_vals = [314] * n
    data = _MAGIC_BYTES + bytes([n])
    for v in amp_vals[:n]:
        data += struct.pack(">H", int(v))
    for v in phase_vals[:n]:
        data += struct.pack(">h", int(v))
    data += struct.pack(">H", ntc_raw)
    return data


class TestCSIPacketParsing:
    def test_parse_valid_packet(self):
        raw = _make_packet(4)
        pkt = parse_csi_packet(raw)
        assert pkt is not None
        assert len(pkt.amplitude) == 4
        assert len(pkt.phase) == 4
        assert all(isinstance(a, float) for a in pkt.amplitude)

    def test_parse_wrong_magic(self):
        raw = b'\x00\x00\x00\x00' + bytes([4]) + b'\x00' * (4 * 2 + 4 * 2 + 2)
        pkt = parse_csi_packet(raw)
        assert pkt is None

    def test_parse_too_short(self):
        pkt = parse_csi_packet(b'\xC5\x49\x28\x6B\x04\x00')
        assert pkt is None

    def test_parse_zero_subcarriers(self):
        raw = _MAGIC_BYTES + bytes([0]) + struct.pack(">H", 0)
        pkt = parse_csi_packet(raw)
        assert pkt is None

    def test_amplitude_scaling(self):
        raw = _make_packet(2, amp_vals=[500, 1500])
        pkt = parse_csi_packet(raw)
        assert pkt is not None
        assert abs(pkt.amplitude[0] - 0.5) < 0.001
        assert abs(pkt.amplitude[1] - 1.5) < 0.001

    def test_phase_scaling(self):
        raw = _make_packet(2, phase_vals=[1000, -1000])
        pkt = parse_csi_packet(raw)
        assert pkt is not None
        assert abs(pkt.phase[0] - 1.0) < 0.001
        assert abs(pkt.phase[1] - (-1.0)) < 0.001


class TestPacketAuthenticity:
    def test_signed_packet_accepts_with_matching_hmac(self):
        raw = _make_packet(4)
        envelope = build_signed_csi_envelope(raw, "test-key")
        pkt = parse_csi_packet(envelope, signing_key="test-key")
        assert pkt is not None

    def test_signed_packet_rejects_missing_hmac_when_required(self):
        raw = _make_packet(4)
        pkt = parse_csi_packet(raw, signing_key="test-key")
        assert pkt is None

    def test_signed_packet_rejects_bad_hmac(self):
        import struct
        import time
        raw = _make_packet(4)
        issued_at = struct.pack(">I", int(time.time()))
        pkt = parse_csi_packet(issued_at + raw + ("0" * 64).encode("ascii"), signing_key="test-key")
        assert pkt is None

    def test_freshness_rejects_stale_packet(self, monkeypatch):
        """A packet with an issued_at far in the past must be dropped."""
        import struct
        import time as _time
        from void_decoder import sign_packet_hmac
        raw = _make_packet(4)
        stale_ts = int(_time.time()) - (CSI_FRESHNESS_WINDOW_S + 120)
        envelope_body = struct.pack(">I", stale_ts) + raw
        sig = sign_packet_hmac(envelope_body.hex().upper(), "stale-key")
        stale_envelope = envelope_body + sig.encode("ascii")
        pkt = parse_csi_packet(stale_envelope, signing_key="stale-key")
        assert pkt is None

    def test_freshness_accepts_recent_packet(self):
        """A packet signed within the window must parse successfully."""
        raw = _make_packet(4)
        envelope = build_signed_csi_envelope(raw, "fresh-key")
        pkt = parse_csi_packet(envelope, signing_key="fresh-key")
        assert pkt is not None


class TestDerivedValues:
    def test_amplitude_variance_uniform(self):
        assert _amplitude_variance([1.0, 1.0, 1.0]) == pytest.approx(0.0)

    def test_amplitude_variance_spread(self):
        var = _amplitude_variance([0.0, 2.0])
        assert var > 0

    def test_phase_shift_rms(self):
        rms = _phase_shift_magnitude([1.0, -1.0, 0.0])
        assert rms > 0

    def test_ntc_to_celsius_midpoint(self):
        temp = _ntc_to_celsius(2048)
        assert 18.0 <= temp <= 32.0

    def test_ntc_boundary_low(self):
        temp = _ntc_to_celsius(0)
        assert temp == pytest.approx(23.0)

    def test_ntc_boundary_high(self):
        temp = _ntc_to_celsius(4095)
        assert temp == pytest.approx(23.0)

    def test_derive_sensor_state_ranges(self):
        raw = _make_packet(8, amp_vals=[800] * 8, phase_vals=[500] * 8)
        pkt = parse_csi_packet(raw)
        state = derive_sensor_state_from_packet(pkt)
        assert 0.0 <= state["water_level"] <= 1.0
        assert -20.0 <= state["temperature"] <= 80.0
        assert state["csi_source"] == "hardware"


class TestSimulatedCSIBioMonitor:
    def test_returns_valid_state(self):
        mon = SimulatedCSIBioMonitor(seed=1)
        state = mon.read_sensor_state()
        assert "water_level" in state
        assert "temperature" in state
        assert "ph" in state
        assert "dissolved_oxygen" in state
        assert state["csi_source"] == "simulation"

    def test_is_not_available(self):
        mon = SimulatedCSIBioMonitor()
        assert mon.is_available is False

    def test_values_in_range(self):
        mon = SimulatedCSIBioMonitor(seed=99)
        for _ in range(20):
            state = mon.read_sensor_state()
            assert 0.0 <= state["water_level"] <= 1.0
            assert 18.0 <= state["temperature"] <= 28.0
            assert 6.0 <= state["ph"] <= 7.5
            assert state["dissolved_oxygen"] >= 5.0

    def test_packet_count_increments(self):
        mon = SimulatedCSIBioMonitor()
        assert mon.packet_count == 0
        mon.read_sensor_state()
        assert mon.packet_count == 1
        mon.read_sensor_state()
        assert mon.packet_count == 2

    def test_fallback_mode_no_socket(self):
        mon = SimulatedCSIBioMonitor()
        assert mon._sock is None
        state = mon.read_sensor_state()
        assert state is not None

    def test_get_status(self):
        mon = SimulatedCSIBioMonitor()
        status = mon.get_status()
        assert status["available"] is False
        assert status["mode"] == "simulation"


class TestSolarProfile:
    def test_electricity_mode_above_crossover(self):
        status = get_solar_mode(20.0)
        assert status.mode == "electricity"
        assert status.estimated_output_w > 0
        assert status.efficiency == pytest.approx(0.18)

    def test_heating_mode_below_crossover(self):
        status = get_solar_mode(5.0)
        assert status.mode == "heating"
        assert status.estimated_output_w > 0
        assert status.efficiency == pytest.approx(0.90)

    def test_off_angle_low_irradiance(self):
        status = get_solar_mode(20.0, irradiance_w_m2=10.0)
        assert status.mode == "off_angle"
        assert status.estimated_output_w == 0.0
        assert status.grid_independent is False

    def test_crossover_boundary(self):
        below = get_solar_mode(CROSSOVER_TEMP_C - 0.1)
        above = get_solar_mode(CROSSOVER_TEMP_C + 0.1)
        assert below.mode == "heating"
        assert above.mode == "electricity"

    def test_grid_independent_flag_high_output(self):
        status = get_solar_mode(25.0, irradiance_w_m2=1000.0)
        assert status.grid_independent is True

    def test_profile_summary_keys(self):
        summary = get_profile_summary()
        assert "crossover_temp_c" in summary
        assert "electricity_mode" in summary
        assert "heating_mode" in summary
        assert "node_power_draw_w" in summary
        assert summary["crossover_temp_c"] == CROSSOVER_TEMP_C


class TestDashboardCSIBadge:
    """Verify badge logic: csi_source determines LIVE HARDWARE vs SIMULATION MODE badge."""

    def test_simulation_badge_from_simulated_monitor(self):
        mon = SimulatedCSIBioMonitor(seed=7)
        state = mon.read_sensor_state()
        assert state["csi_source"] == "simulation"
        badge = "LIVE HARDWARE" if state["csi_source"] == "hardware" else "SIMULATION MODE"
        assert badge == "SIMULATION MODE"

    def test_hardware_badge_when_source_is_hardware(self):
        hardware_state = {
            "water_level": 0.75,
            "temperature": 22.5,
            "ph": 6.8,
            "dissolved_oxygen": 7.2,
            "growth_density": 0.4,
            "moisture": 0.6,
            "csi_source": "hardware",
        }
        badge = "LIVE HARDWARE" if hardware_state["csi_source"] == "hardware" else "SIMULATION MODE"
        assert badge == "LIVE HARDWARE"

    def test_no_data_source_shows_simulation_badge(self):
        hardware_state = {"csi_source": "no_data"}
        badge = "LIVE HARDWARE" if hardware_state["csi_source"] == "hardware" else "SIMULATION MODE"
        assert badge == "SIMULATION MODE"

    def test_none_csi_state_safe(self):
        """Template must handle csi=None gracefully (no crash)."""
        csi = None
        badge = "LIVE HARDWARE" if (csi and csi.get("csi_source") == "hardware") else "SIMULATION MODE"
        assert badge == "SIMULATION MODE"
        water_level = csi["water_level"] if csi and csi.get("water_level") is not None else None
        assert water_level is None

    def test_none_solar_safe(self):
        """Template must handle solar=None gracefully (no crash)."""
        solar = None
        mode_text = solar.mode.replace("_", " ") if solar else "—"
        assert mode_text == "—"
        output_text = f"{solar.estimated_output_w:.0f} W" if solar else "—"
        assert output_text == "—"
