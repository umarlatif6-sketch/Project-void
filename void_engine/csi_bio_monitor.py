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
