"""
ESP32 WiFi CSI Mycelium Bio-Monitor
====================================
Reads Channel State Information (CSI) from an ESP32-S3 mesh over UDP.
As mycelium colonises the wooden machine enclosure it alters the dielectric
properties of the substrate, producing measurable disturbances in WiFi signal
amplitude and phase.  This module parses those disturbances and derives
biological state estimates that populate the SensorState dataclass.

When no hardware is present the SimulatedCSIBioMonitor subclass generates
realistic values that match the existing aquaponics defaults, so the rest of
the engine is unaffected.
"""

import logging
import math
import os
import random
import socket
import struct
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── ESP32 CSI packet format ────────────────────────────────────────────────
# Each UDP packet is:
#   4 bytes  magic      (b'\xC5\xI0\x28\x6B')
#   1 byte   n_subcarriers
#   n * 2 bytes  amplitude  (uint16, scaled /1000 → float)
#   n * 2 bytes  phase      (int16, radians * 1000)
#   2 bytes  ntc_raw        (uint16, raw ADC for secondary temperature channel)

_MAGIC_BYTES = b'\xC5\x49\x28\x6B'

DEFAULT_UDP_HOST = "0.0.0.0"
DEFAULT_UDP_PORT = 5286
SOCKET_TIMEOUT_S = 0.1
MAX_SUBCARRIERS = 64


@dataclass
class CSIPacket:
    amplitude: List[float]
    phase: List[float]
    ntc_raw: int
    timestamp: float


def parse_csi_packet(data: bytes) -> Optional[CSIPacket]:
    """Parse a raw UDP payload into a CSIPacket.  Returns None on malformed input."""
    try:
        if len(data) < 6:
            return None
        if data[:4] != _MAGIC_BYTES:
            return None
        n = data[4]
        if n == 0 or n > MAX_SUBCARRIERS:
            return None
        expected_len = 4 + 1 + n * 2 + n * 2 + 2
        if len(data) < expected_len:
            return None

        offset = 5
        amplitudes = []
        for i in range(n):
            raw = struct.unpack_from(">H", data, offset + i * 2)[0]
            amplitudes.append(raw / 1000.0)

        offset += n * 2
        phases = []
        for i in range(n):
            raw = struct.unpack_from(">h", data, offset + i * 2)[0]
            phases.append(raw / 1000.0)

        offset += n * 2
        ntc_raw = struct.unpack_from(">H", data, offset)[0]

        return CSIPacket(amplitude=amplitudes, phase=phases, ntc_raw=ntc_raw, timestamp=time.time())
    except Exception as exc:
        logger.debug("CSI packet parse error: %s", exc)
        return None


def _amplitude_variance(amplitudes: List[float]) -> float:
    if len(amplitudes) < 2:
        return 0.0
    mean = sum(amplitudes) / len(amplitudes)
    variance = sum((a - mean) ** 2 for a in amplitudes) / len(amplitudes)
    return variance


def _phase_shift_magnitude(phases: List[float]) -> float:
    if not phases:
        return 0.0
    return math.sqrt(sum(p * p for p in phases) / len(phases))


def _ntc_to_celsius(ntc_raw: int, r_ref: float = 10000.0, b_coeff: float = 3950.0,
                    t_ref: float = 298.15) -> float:
    """Convert raw 12-bit ADC reading to temperature via Beta equation."""
    if ntc_raw <= 0 or ntc_raw >= 4095:
        return 23.0
    r_ntc = r_ref * ntc_raw / (4095 - ntc_raw)
    try:
        temp_k = 1.0 / (1.0 / t_ref + math.log(r_ntc / r_ref) / b_coeff)
        return temp_k - 273.15
    except (ValueError, ZeroDivisionError):
        return 23.0


def derive_sensor_state_from_packet(packet: CSIPacket) -> dict:
    """
    Derive biological sensor estimates from a single CSI packet.

    Mapping rationale:
      - Amplitude variance → moisture (high variance = more water in substrate)
      - Phase shift RMS    → growth density (mycelium hyphae rotate phase)
      - NTC channel        → temperature in °C
      - pH and dissolved_oxygen stay at defaults when no chemical sensors are wired
    """
    amp_var = _amplitude_variance(packet.amplitude)
    phase_rms = _phase_shift_magnitude(packet.phase)
    temperature = _ntc_to_celsius(packet.ntc_raw)

    moisture = min(1.0, max(0.0, amp_var / 2.0))
    growth_density = min(1.0, max(0.0, phase_rms / math.pi))

    water_level = 0.4 + moisture * 0.55
    water_level = min(1.0, max(0.0, water_level))

    return {
        "water_level": round(water_level, 4),
        "temperature": round(temperature, 2),
        "ph": 6.75,
        "dissolved_oxygen": 7.0,
        "growth_density": round(growth_density, 4),
        "moisture": round(moisture, 4),
        "csi_source": "hardware",
    }


class CSIBioMonitor:
    """
    Live CSI bio-monitor.  Opens a UDP socket and waits for packets from the
    ESP32 mesh.  Call read_sensor_state() to get the most recent estimate.
    Falls back gracefully when no packets arrive within the timeout.
    """

    def __init__(self, host: str = DEFAULT_UDP_HOST, port: int = DEFAULT_UDP_PORT,
                 timeout: float = SOCKET_TIMEOUT_S):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._last_packet: Optional[CSIPacket] = None
        self._packet_count = 0
        self._error_count = 0
        self._available = False
        self._open_socket()

    def _open_socket(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self._host, self._port))
            sock.settimeout(self._timeout)
            self._sock = sock
            self._available = True
            logger.info("CSIBioMonitor: UDP socket bound on %s:%d", self._host, self._port)
        except Exception as exc:
            logger.warning("CSIBioMonitor: could not open UDP socket: %s", exc)
            self._available = False

    def read_sensor_state(self) -> dict:
        """
        Return a dict compatible with SensorState fields.
        Reads up to one UDP packet per call.  If no packet arrives within the
        timeout the last known values are returned, or None if no data has ever
        been received.
        """
        if self._sock is None:
            return self._fallback_state()

        try:
            data, _ = self._sock.recvfrom(4096)
            packet = parse_csi_packet(data)
            if packet:
                self._last_packet = packet
                self._packet_count += 1
                return derive_sensor_state_from_packet(packet)
        except socket.timeout:
            pass
        except Exception as exc:
            self._error_count += 1
            logger.debug("CSIBioMonitor recv error: %s", exc)

        if self._last_packet:
            return derive_sensor_state_from_packet(self._last_packet)

        return self._fallback_state()

    def _fallback_state(self) -> dict:
        return {
            "water_level": 0.7,
            "temperature": 23.0,
            "ph": 6.75,
            "dissolved_oxygen": 7.0,
            "growth_density": None,
            "moisture": None,
            "csi_source": "no_data",
        }

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def packet_count(self) -> int:
        return self._packet_count

    def get_status(self) -> dict:
        return {
            "available": self._available,
            "host": self._host,
            "port": self._port,
            "packet_count": self._packet_count,
            "error_count": self._error_count,
            "last_packet_ts": self._last_packet.timestamp if self._last_packet else None,
        }

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None


# ── QiSync martial stance and mastication detection ───────────────────────────

STANCE_NAMES = {
    "mabu": "马步 mǎbù (Horse)",
    "pubu": "仆步 pūbù (Drop)",
    "xiebu": "歇步 xiēbù (Rest)",
    "gongbu": "弓步 gōngbù (Bow)",
    "xvbu": "虚步 xūbù (Empty)",
    "neutral": "Neutral",
}

# Approximate CSI variance + phase signature thresholds for each stance.
# In real deployment the ESP32 would be trained per-environment; here we use
# signal-variance bands as proxies (as per task spec).
_STANCE_THRESHOLDS = [
    # (stance_key, amp_var_min, amp_var_max, phase_rms_min, phase_rms_max)
    ("mabu",  0.30, 0.55, 0.55, 0.90),   # wide, low — high amp disturbance
    ("pubu",  0.55, 0.85, 0.80, 1.20),   # full drop — very high variance
    ("xiebu", 0.20, 0.40, 0.40, 0.70),   # cross-leg rest — moderate
    ("gongbu", 0.10, 0.28, 0.20, 0.55),  # forward lunge — moderate amp, low phase
    ("xvbu",  0.05, 0.18, 0.10, 0.38),   # light weight-empty — very low variance
]


class StanceDetector:
    """
    Classifies a CSI packet stream into one of the five foundation stances or
    neutral.  Uses a rolling window of amplitude variance and phase RMS over
    the last N packets.

    When no real hardware is present the :class:`SimulatedStanceDetector`
    subclass synthesises realistic variance trajectories.
    """

    WINDOW = 10

    def __init__(self):
        self._amp_vars: List[float] = []
        self._phase_rms: List[float] = []
        self._current_stance: str = "neutral"
        self._confidence: float = 0.0
        self._sample_count: int = 0

    def feed_packet(self, packet: CSIPacket) -> str:
        """Update with a new CSI packet and return the current detected stance."""
        amp_var = _amplitude_variance(packet.amplitude)
        p_rms = _phase_shift_magnitude(packet.phase)

        self._amp_vars.append(amp_var)
        self._phase_rms.append(p_rms)

        if len(self._amp_vars) > self.WINDOW:
            self._amp_vars = self._amp_vars[-self.WINDOW:]
            self._phase_rms = self._phase_rms[-self.WINDOW:]

        self._sample_count += 1
        self._classify()
        return self._current_stance

    def _classify(self) -> None:
        if not self._amp_vars:
            self._current_stance = "neutral"
            self._confidence = 0.0
            return

        avg_amp = sum(self._amp_vars) / len(self._amp_vars)
        avg_phase = sum(self._phase_rms) / len(self._phase_rms)

        for stance_key, av_min, av_max, pr_min, pr_max in _STANCE_THRESHOLDS:
            if av_min <= avg_amp < av_max and pr_min <= avg_phase < pr_max:
                amp_mid = (av_min + av_max) / 2.0
                phase_mid = (pr_min + pr_max) / 2.0
                amp_range = (av_max - av_min) / 2.0
                phase_range = (pr_max - pr_min) / 2.0
                amp_conf = max(0.0, 1.0 - abs(avg_amp - amp_mid) / amp_range)
                phase_conf = max(0.0, 1.0 - abs(avg_phase - phase_mid) / phase_range)
                self._confidence = (amp_conf + phase_conf) / 2.0
                self._current_stance = stance_key
                return

        self._current_stance = "neutral"
        self._confidence = 0.0

    @property
    def current_stance(self) -> str:
        return self._current_stance

    @property
    def confidence(self) -> float:
        return round(self._confidence, 3)

    def get_status(self) -> dict:
        return {
            "stance": self._current_stance,
            "stance_label": STANCE_NAMES.get(self._current_stance, self._current_stance),
            "confidence": self.confidence,
            "sample_count": self._sample_count,
            "mode": "hardware",
        }


class MasticationDetector:
    """
    Counts jaw-motion cycles from CSI micro-variance.

    Mastication produces a repeating low-amplitude modulation in the 0.5–3 Hz
    range.  We detect it by watching for zero-crossings around the rolling mean
    of amplitude variance; each crossing pair counts as one chew cycle.
    The target is 30 chews per food bolus per the metabolic research.
    """

    WINDOW = 60

    def __init__(self):
        self._amp_vars: List[float] = []
        self._chew_count: int = 0
        self._cycle_score: float = 0.0
        self._last_sign: Optional[int] = None
        self._sample_count: int = 0
        self._crossings: int = 0

    def feed_packet(self, packet: CSIPacket) -> int:
        """Feed a packet and return the cumulative chew count."""
        amp_var = _amplitude_variance(packet.amplitude)
        self._amp_vars.append(amp_var)

        if len(self._amp_vars) > self.WINDOW:
            self._amp_vars = self._amp_vars[-self.WINDOW:]

        self._sample_count += 1

        if len(self._amp_vars) >= 4:
            mean = sum(self._amp_vars) / len(self._amp_vars)
            sign = 1 if amp_var > mean else -1
            if self._last_sign is not None and sign != self._last_sign:
                self._crossings += 1
                if self._crossings % 2 == 0:
                    self._chew_count += 1
            self._last_sign = sign

        self._cycle_score = min(1.0, self._chew_count / 30.0)
        return self._chew_count

    @property
    def chew_count(self) -> int:
        return self._chew_count

    @property
    def cycle_score(self) -> float:
        """0–1 score: 1.0 = 30 or more quality chew cycles detected."""
        return round(self._cycle_score, 3)

    def reset(self):
        self._chew_count = 0
        self._crossings = 0
        self._last_sign = None
        self._cycle_score = 0.0
        self._amp_vars = []

    def get_status(self) -> dict:
        return {
            "chew_count": self._chew_count,
            "cycle_score": self.cycle_score,
            "sample_count": self._sample_count,
            "target_chews": 30,
        }


class SimulatedCSIBioMonitor(CSIBioMonitor):
    """
    Simulation fallback used when no ESP32 hardware is present.
    Generates realistic CSI-like values with gentle random walk behaviour
    that matches the existing aquaponics sensor defaults.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._available = False
        self._sock = None
        self._host = "127.0.0.1"
        self._port = DEFAULT_UDP_PORT
        self._last_packet = None
        self._packet_count = 0
        self._error_count = 0

        self._water_level = 0.70
        self._temperature = 23.0
        self._ph = 6.75
        self._dissolved_oxygen = 7.0
        self._growth_density = 0.35
        self._moisture = 0.55

        logger.info("SimulatedCSIBioMonitor: hardware absent — using simulation mode")

    def _open_socket(self):
        pass

    def read_sensor_state(self) -> dict:
        self._water_level = self._walk(self._water_level, 0.002, 0.3, 0.95)
        self._temperature = self._walk(self._temperature, 0.05, 18.0, 28.0)
        self._ph = self._walk(self._ph, 0.005, 6.0, 7.5)
        self._dissolved_oxygen = self._walk(self._dissolved_oxygen, 0.05, 5.0, 9.0)
        self._growth_density = self._walk(self._growth_density, 0.003, 0.0, 1.0)
        self._moisture = self._walk(self._moisture, 0.005, 0.0, 1.0)

        self._packet_count += 1

        return {
            "water_level": round(self._water_level, 4),
            "temperature": round(self._temperature, 2),
            "ph": round(self._ph, 3),
            "dissolved_oxygen": round(self._dissolved_oxygen, 2),
            "growth_density": round(self._growth_density, 4),
            "moisture": round(self._moisture, 4),
            "csi_source": "simulation",
        }

    def _walk(self, value: float, step: float, lo: float, hi: float) -> float:
        delta = self._rng.gauss(0, step)
        return max(lo, min(hi, value + delta))

    @property
    def is_available(self) -> bool:
        return False

    def get_status(self) -> dict:
        return {
            "available": False,
            "mode": "simulation",
            "packet_count": self._packet_count,
            "error_count": 0,
            "last_packet_ts": None,
        }
