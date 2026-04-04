"""
PROJECT VOID -- Beehive Protocol
Acoustic Mesh Networking for the Ghost Internet

The Beehive Protocol allows multiple 4000-Series units to discover each other,
authenticate via phase-shift keys, and exchange data using only sound.

Architecture:
  - Handshake Pulse: 432 Hz Sapphire Thread wrapped in Insect Silt
  - Phase Key Auth: Frequency is public, phase angle is the secret
  - Data Transport: Phase-shifted chirps in the Insect Shelf (2-12 kHz)
  - Mesh Routing: Seven Seas limit (7 hops, ~350 miles coastal range)
  - Flywheel Buffer: Stores data for dark nodes (wallet cost: 0.5 CC/min)

Material Resonance Ladder (4000-Series Chassis):
  108 Hz (Steel Skin) -> 216 Hz (Aluminum Frame) -> 432 Hz (Silk-Silver Wiring)
  -> 864 Hz (Salt Water Buffer) -> 12 kHz (Foam Insulation)

Mode: SIMULATION — protocol logic verified in-memory, ready for hardware integration.
"""

import json
import time
import uuid
import threading
import numpy as np
from numpy.fft import fft
from void_engine.al_jabr_286 import fatiha_286_hexdigest, fatiha_286_hexdigest_from_str, fatiha_286_truncated, fatiha_286_seed


RESONANCE_FREQ = 432
HARMONIC_LADDER = [108, 216, 432, 864]
SAMPLE_RATE = 44100
SNR_THRESHOLD = 5.0
PHASE_TOLERANCE_DEG = 15.0
PHASE_TOLERANCE_RAD = PHASE_TOLERANCE_DEG * (np.pi / 180)
MAX_HOPS = 7
COASTAL_RANGE_MILES = 350
DISCOVERY_INTERVAL = 60
FLYWHEEL_BUFFER_MAX_SEC = 300
RELAY_COST_CC = 0.2
SCAN_COST_CC = 0.1
BUFFER_COST_CC = 0.5
HANDSHAKE_COST_CC = 0.05
SEND_COST_CC = 0.3

FATIHA_PHASE_ANGLE = 15.4
FATIHA_PHASE_RAD = FATIHA_PHASE_ANGLE * (np.pi / 180)
FATIHA_PHASE_TOLERANCE_DEG = 0.5
FATIHA_PHASE_TOLERANCE_RAD = FATIHA_PHASE_TOLERANCE_DEG * (np.pi / 180)
SILT_EMBED_DB = -30.0
SILT_EMBED_AMP = 10 ** (SILT_EMBED_DB / 20.0)
INSECT_SHELF_FREQ = 970.0
WHISPER_PHASE_SHIFT = np.pi

MESH_STATES = ["DARK", "SCANNING", "CONNECTED", "BRIDGING"]

# ── TEMPORAL STEGANOGRAPHY CHANNEL ────────────────────────────────────────────
# The interval between transmissions is itself a sovereign information channel.
# Temporal steganography: data is encoded in the *spacing* between pulses,
# operating independently of payload content.  Observers see only timing gaps;
# the data is invisible without knowing the passphrase and the coding scheme.
#
# Symbol alphabet: each symbol maps to a unique interval duration (seconds).
# We use 4-symbol (2-bit) encoding per interval so a single timing gap carries
# exactly 2 bits of payload.
#
# Base interval: 0.8 s (shortest plausible natural gap).
# Symbol step:   0.2 s (300 ms spread between symbols — measurable, not jarring).
#
#   Symbol  Bits  Interval
#   ──────  ────  ────────
#     0      00    0.8 s
#     1      01    1.0 s
#     2      10    1.2 s
#     3      11    1.4 s
#
# Passphrase → permutes the symbol→interval mapping, making the dictionary
# passphrase-dependent (adds a layer of keyed steganography).

TEMPORAL_BASE_INTERVAL = 0.8          # seconds — shortest symbol gap
TEMPORAL_SYMBOL_STEP   = 0.2          # seconds between symbol levels
TEMPORAL_BITS_PER_INTERVAL = 2        # 2 bits per gap  → 4-symbol alphabet
TEMPORAL_SYMBOLS       = 4            # 2^TEMPORAL_BITS_PER_INTERVAL


class TemporalChannel:
    """
    Sovereign Temporal Steganography Channel.

    Encodes arbitrary bytes into the *time gaps between transmissions*.
    The content channel (what is transmitted) remains independent —
    two separate steganographic layers can coexist.

    Encoding:
      1. Convert payload bytes → bit stream.
      2. Group bits into TEMPORAL_BITS_PER_INTERVAL-bit symbols (padding the last
         group with zeros if needed).
      3. Apply a keyed permutation derived from the passphrase so the
         symbol→interval mapping is passphrase-dependent.
      4. Map each symbol to its interval duration.
      5. Return the sequence of durations.

    Decoding:
      1. Receive observed interval durations (e.g. from real timestamps or
         a simulation log).
      2. Apply the same keyed permutation (derived from the same passphrase).
      3. Each duration → nearest symbol → bits.
      4. Reassemble bits → bytes, strip padding.

    Simulation helpers:
      - simulate_transmission_log  : given payload + passphrase, produce a list
                                     of {sent_at, interval_s} dicts.
      - decode_transmission_log    : inverse — recover payload from the log.
    """

    def __init__(self, passphrase: str = "void-432"):
        self.passphrase = passphrase
        self._symbol_map, self._reverse_map = self._build_maps(passphrase)

    def _build_maps(self, passphrase: str):
        """
        Derive a passphrase-keyed permutation of the symbol→interval mapping.

        We compute a 286-bit hash of the passphrase, take its first 4 bytes,
        and use them to produce a stable shuffle of [0, 1, 2, 3].

        Returns:
          symbol_map[symbol_index]  → interval duration (seconds)
          reverse_map[interval_key] → symbol_index
        """
        h = fatiha_286_hexdigest_from_str(passphrase)
        seed_bytes = [int(h[i * 2:(i * 2) + 2], 16) for i in range(4)]

        order = list(range(TEMPORAL_SYMBOLS))
        for i in range(TEMPORAL_SYMBOLS - 1, 0, -1):
            j = seed_bytes[i % 4] % (i + 1)
            order[i], order[j] = order[j], order[i]

        symbol_map = {}
        reverse_map = {}
        for sym_idx, rank in enumerate(order):
            interval = round(TEMPORAL_BASE_INTERVAL + rank * TEMPORAL_SYMBOL_STEP, 4)
            symbol_map[sym_idx] = interval
            reverse_map[interval] = sym_idx

        return symbol_map, reverse_map

    def encode(self, payload: bytes) -> list:
        """
        Encode payload bytes into a list of interval durations (seconds).

        Args:
            payload: arbitrary bytes to encode.

        Returns:
            List of float interval durations (one per 2-bit symbol).
            The receiver must observe these gaps between transmissions.
        """
        if not payload:
            return []

        bits = []
        for byte in payload:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        padding = (TEMPORAL_BITS_PER_INTERVAL - len(bits) % TEMPORAL_BITS_PER_INTERVAL) % TEMPORAL_BITS_PER_INTERVAL
        bits.extend([0] * padding)

        intervals = []
        for i in range(0, len(bits), TEMPORAL_BITS_PER_INTERVAL):
            symbol = 0
            for b in bits[i:i + TEMPORAL_BITS_PER_INTERVAL]:
                symbol = (symbol << 1) | b
            intervals.append(self._symbol_map[symbol])

        return intervals

    def decode(self, intervals: list, n_bytes: int = None) -> bytes:
        """
        Decode a list of interval durations back into bytes.

        Args:
            intervals: list of float durations as returned by encode() or
                       extracted from a transmission log.
            n_bytes:   expected number of bytes in the payload (optional).
                       If None, all decoded bits are returned.

        Returns:
            Decoded bytes.
        """
        bits = []
        for interval in intervals:
            symbol = self._nearest_symbol(interval)
            for i in range(TEMPORAL_BITS_PER_INTERVAL - 1, -1, -1):
                bits.append((symbol >> i) & 1)

        if n_bytes is not None:
            bits = bits[:n_bytes * 8]

        result = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i + 8]
            if len(byte_bits) < 8:
                break
            val = 0
            for b in byte_bits:
                val = (val << 1) | b
            result.append(val)

        return bytes(result)

    def _nearest_symbol(self, observed: float) -> int:
        """Map an observed interval duration to the nearest symbol index."""
        best_sym = 0
        best_dist = float("inf")
        for sym, dur in self._symbol_map.items():
            d = abs(observed - dur)
            if d < best_dist:
                best_dist = d
                best_sym = sym
        return best_sym

    def simulate_transmission_log(self, payload: bytes,
                                   start_time: float = None) -> list:
        """
        Produce a simulated transmission log that encodes payload in the gaps.

        Returns a list of dicts:
          {
            "pulse_index":  int,
            "sent_at":      float (Unix timestamp),
            "interval_s":   float (gap after this pulse),   # None for last pulse
            "symbol":       int   (encoded symbol, 0–3),    # None for last pulse
          }
        """
        intervals = self.encode(payload)
        t = start_time or time.time()
        log = []
        for idx, gap in enumerate(intervals):
            log.append({
                "pulse_index": idx,
                "sent_at": t,
                "interval_s": gap,
                "symbol": list(self._symbol_map.keys())[list(self._symbol_map.values()).index(gap)],
            })
            t += gap
        log.append({
            "pulse_index": len(intervals),
            "sent_at": t,
            "interval_s": None,
            "symbol": None,
        })
        return log

    def decode_transmission_log(self, log: list, n_bytes: int = None) -> bytes:
        """
        Recover payload from a transmission log produced by simulate_transmission_log.

        Reads the 'interval_s' field from each log entry (skips None entries).
        """
        intervals = [entry["interval_s"] for entry in log if entry.get("interval_s") is not None]
        return self.decode(intervals, n_bytes=n_bytes)

    def channel_capacity_bps(self) -> float:
        """
        Theoretical channel capacity in bits per second.

        Each interval carries TEMPORAL_BITS_PER_INTERVAL bits and lasts
        on average (base + 1.5 * step) seconds.
        """
        avg_interval = TEMPORAL_BASE_INTERVAL + (TEMPORAL_SYMBOLS - 1) / 2.0 * TEMPORAL_SYMBOL_STEP
        return TEMPORAL_BITS_PER_INTERVAL / avg_interval

    def encode_info(self) -> dict:
        """Return channel metadata for inspection."""
        return {
            "passphrase_hash": fatiha_286_hexdigest_from_str(self.passphrase)[:16] + "...",
            "bits_per_interval": TEMPORAL_BITS_PER_INTERVAL,
            "symbol_alphabet": TEMPORAL_SYMBOLS,
            "symbol_map": self._symbol_map,
            "base_interval_s": TEMPORAL_BASE_INTERVAL,
            "symbol_step_s": TEMPORAL_SYMBOL_STEP,
            "channel_capacity_bps": round(self.channel_capacity_bps(), 4),
            "description": (
                "Temporal steganographic channel — data encoded in pulse spacing. "
                "The interval between transmissions is a sovereign information channel, "
                "independent of the content channel. "
                "Symbol→interval mapping is keyed to the passphrase."
            ),
        }


def _passphrase_to_phase(passphrase: str) -> float:
    h = fatiha_286_hexdigest_from_str(passphrase)
    deg = int(h[:8], 16) % 360
    return deg * (np.pi / 180)


def _generate_node_id(machine_id: str = "") -> str:
    seed = machine_id or str(uuid.uuid4())
    return fatiha_286_truncated(seed.encode("utf-8"), 16)


class BeehiveProtocol:

    def __init__(self, machine_id: str = "", passphrase: str = "void-432",
                 sample_rate: int = SAMPLE_RATE):
        self.node_id = _generate_node_id(machine_id)
        self.passphrase = passphrase
        self.sr = sample_rate
        self.phase_key = _passphrase_to_phase(passphrase)

        self.mesh_state = "DARK"
        self.neighbors = {}
        self.activity_log = []
        self.stats = {
            "packets_sent": 0,
            "packets_received": 0,
            "packets_relayed": 0,
            "handshakes_sent": 0,
            "handshakes_received": 0,
            "cc_spent": 0.0,
        }

        self._flywheel_buffer = {}
        self._lock = threading.Lock()

    def generate_handshake_pulse(self, duration: float = 1.0) -> np.ndarray:
        n_samples = int(self.sr * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        pulse_432 = np.sin(2 * np.pi * RESONANCE_FREQ * t + self.phase_key + FATIHA_PHASE_RAD) * 0.5

        pulse_108 = np.sin(2 * np.pi * 108 * t + self.phase_key * 0.25) * 0.15
        pulse_216 = np.sin(2 * np.pi * 216 * t + self.phase_key * 0.5) * 0.1
        pulse_864 = np.sin(2 * np.pi * 864 * t + self.phase_key * 2.0) * 0.08

        silt = np.random.normal(0, 0.05, n_samples)

        signal = pulse_432 + pulse_108 + pulse_216 + pulse_864 + silt

        identity_hash = fatiha_286_hexdigest_from_str(self.node_id)
        signal = self.silt_embed(signal, identity_hash)

        signal = np.clip(signal, -1.0, 1.0)
        self.stats["handshakes_sent"] += 1
        self._log_event("HANDSHAKE_SENT", f"Generated {duration}s Fatiha pulse (+{FATIHA_PHASE_ANGLE}° phase, -30dB silt)")
        return signal.astype(np.float32)

    def silt_embed(self, signal: np.ndarray, hash_hex: str) -> np.ndarray:
        n_samples = len(signal)
        t = np.linspace(0, n_samples / self.sr, n_samples, endpoint=False)

        hash_bytes = bytes.fromhex(hash_hex)
        bit_stream = []
        for byte in hash_bytes:
            for i in range(7, -1, -1):
                bit_stream.append((byte >> i) & 1)

        silt_signal = np.zeros(n_samples, dtype=np.float64)
        samples_per_bit = max(1, n_samples // len(bit_stream))

        for idx, bit in enumerate(bit_stream):
            start = idx * samples_per_bit
            end = min(start + samples_per_bit, n_samples)
            if start >= n_samples:
                break
            t_slice = t[start:end]
            freq = INSECT_SHELF_FREQ + (bit * 200)
            silt_signal[start:end] = np.sin(2 * np.pi * freq * t_slice) * SILT_EMBED_AMP

        return signal + silt_signal

    def verify_fatiha_signature(self, audio_buffer: np.ndarray) -> dict:
        n = len(audio_buffer)
        if n < 1024:
            return {"verified": False, "reason": "Buffer too short"}

        yf = fft(audio_buffer.astype(np.float64))
        freqs = np.fft.fftfreq(n, 1.0 / self.sr)

        target_idx = np.argmin(np.abs(freqs[:n // 2] - RESONANCE_FREQ))

        raw_phase = np.angle(yf[target_idx])
        detected_total_phase = raw_phase + np.pi / 2

        expected_base_phase = self.phase_key
        fatiha_component = detected_total_phase - expected_base_phase

        fatiha_component = fatiha_component % (2 * np.pi)
        if fatiha_component > np.pi:
            fatiha_component = fatiha_component - 2 * np.pi

        diff = abs(fatiha_component - FATIHA_PHASE_RAD)
        if diff > np.pi:
            diff = 2 * np.pi - diff

        verified = diff <= FATIHA_PHASE_TOLERANCE_RAD

        silt_present = self._detect_silt_layer(audio_buffer)

        return {
            "verified": verified and silt_present,
            "fatiha_angle_detected_deg": float(np.degrees(fatiha_component)),
            "fatiha_angle_expected_deg": FATIHA_PHASE_ANGLE,
            "angle_diff_deg": float(np.degrees(diff)),
            "tolerance_deg": FATIHA_PHASE_TOLERANCE_DEG,
            "silt_layer_present": silt_present,
            "protocol": "Sura-Fatiha 286-Bit Acoustic Handshake",
        }

    def _detect_silt_layer(self, audio_buffer: np.ndarray) -> bool:
        n = len(audio_buffer)
        yf = fft(audio_buffer.astype(np.float64))
        freqs = np.fft.fftfreq(n, 1.0 / self.sr)
        magnitudes = np.abs(yf[:n // 2])
        freq_axis = freqs[:n // 2]

        silt_mask = freq_axis >= INSECT_SHELF_FREQ
        if not np.any(silt_mask):
            return False

        silt_energy = np.mean(magnitudes[silt_mask])
        noise_floor = np.mean(magnitudes[freq_axis < INSECT_SHELF_FREQ / 2]) if np.any(freq_axis < INSECT_SHELF_FREQ / 2) else 1e-10

        return silt_energy > noise_floor * 0.01

    def whisper_confirm(self, duration: float = 0.5) -> np.ndarray:
        n_samples = int(self.sr * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        confirmation_phase = self.phase_key + FATIHA_PHASE_RAD + WHISPER_PHASE_SHIFT
        whisper = np.sin(2 * np.pi * RESONANCE_FREQ * t + confirmation_phase) * 0.3

        silt = np.random.normal(0, 0.02, n_samples)
        signal = whisper + silt

        self._log_event("WHISPER_CONFIRM", f"180° confirmation whisper sent (+{FATIHA_PHASE_ANGLE}° + 180°)")
        return np.clip(signal, -1.0, 1.0).astype(np.float32)

    def verify_whisper(self, audio_buffer: np.ndarray) -> dict:
        n = len(audio_buffer)
        if n < 1024:
            return {"confirmed": False, "reason": "Buffer too short"}

        yf = fft(audio_buffer.astype(np.float64))
        freqs = np.fft.fftfreq(n, 1.0 / self.sr)

        target_idx = np.argmin(np.abs(freqs[:n // 2] - RESONANCE_FREQ))
        raw_phase = np.angle(yf[target_idx])
        detected_phase = raw_phase + np.pi / 2

        expected_whisper_phase = self.phase_key + FATIHA_PHASE_RAD + WHISPER_PHASE_SHIFT

        diff = abs(detected_phase - expected_whisper_phase)
        diff = diff % (2 * np.pi)
        if diff > np.pi:
            diff = 2 * np.pi - diff

        confirmed = diff <= FATIHA_PHASE_TOLERANCE_RAD * 3

        return {
            "confirmed": confirmed,
            "phase_diff_deg": float(np.degrees(diff)),
            "protocol": "180° Convergence Whisper",
        }

    def detect_neighbor(self, audio_buffer: np.ndarray) -> dict:
        n = len(audio_buffer)
        if n < 1024:
            return {"detected": False, "reason": "Buffer too short"}

        yf = fft(audio_buffer.astype(np.float64))
        freqs = np.fft.fftfreq(n, 1.0 / self.sr)
        magnitudes = np.abs(yf[:n // 2])
        freq_axis = freqs[:n // 2]

        target_idx = np.argmin(np.abs(freq_axis - RESONANCE_FREQ))
        signal_mag = magnitudes[target_idx]
        mean_mag = np.mean(magnitudes)
        snr = signal_mag / (mean_mag + 1e-10)

        if snr < SNR_THRESHOLD:
            return {
                "detected": False,
                "reason": f"SNR {snr:.1f} below threshold {SNR_THRESHOLD}",
                "snr": float(snr),
            }

        harmonic_count = 0
        for hf in HARMONIC_LADDER:
            h_idx = np.argmin(np.abs(freq_axis - hf))
            h_snr = magnitudes[h_idx] / (mean_mag + 1e-10)
            if h_snr > 2.0:
                harmonic_count += 1

        ref_amplitude = 0.5
        distance_estimate = max(1.0, ref_amplitude / (signal_mag / (n / 2) + 1e-10))
        distance_estimate = min(distance_estimate, 100.0)

        strength = min(1.0, snr / 20.0)
        if strength > 0.7:
            strength_label = "strong"
        elif strength > 0.3:
            strength_label = "medium"
        else:
            strength_label = "weak"

        self.stats["handshakes_received"] += 1

        fatiha_check = self.verify_fatiha_signature(audio_buffer)

        return {
            "detected": True,
            "snr": float(snr),
            "signal_strength": float(strength),
            "strength_label": strength_label,
            "estimated_distance_m": float(distance_estimate),
            "harmonics_detected": harmonic_count,
            "full_ladder": harmonic_count == len(HARMONIC_LADDER),
            "fatiha_verified": fatiha_check.get("verified", False),
            "fatiha_angle_deg": fatiha_check.get("fatiha_angle_detected_deg", 0.0),
            "silt_layer_present": fatiha_check.get("silt_layer_present", False),
        }

    def authenticate_phase(self, audio_buffer: np.ndarray, passphrase: str = "") -> dict:
        target_passphrase = passphrase or self.passphrase
        expected_phase = _passphrase_to_phase(target_passphrase)

        n = len(audio_buffer)
        yf = fft(audio_buffer.astype(np.float64))
        freqs = np.fft.fftfreq(n, 1.0 / self.sr)

        target_idx = np.argmin(np.abs(freqs[:n // 2] - RESONANCE_FREQ))

        raw_phase = np.angle(yf[target_idx])
        detected_phase = raw_phase + np.pi / 2

        expected_with_fatiha = expected_phase + FATIHA_PHASE_RAD

        diff = np.abs(detected_phase - expected_with_fatiha)
        diff = diff % (2 * np.pi)
        if diff > np.pi:
            diff = 2 * np.pi - diff

        authenticated = diff <= PHASE_TOLERANCE_RAD

        return {
            "authenticated": authenticated,
            "phase_diff_deg": float(np.degrees(diff)),
            "tolerance_deg": PHASE_TOLERANCE_DEG,
            "detected_phase_deg": float(np.degrees(detected_phase)),
            "expected_phase_deg": float(np.degrees(expected_with_fatiha)),
            "fatiha_offset_deg": FATIHA_PHASE_ANGLE,
        }

    def transmit_data(self, binary_data: bytes) -> np.ndarray:
        carrier_freq = 6000.0
        bit_duration = 0.002
        samples_per_bit = int(self.sr * bit_duration)

        bits = []
        for byte in binary_data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        n_samples = len(bits) * samples_per_bit
        signal = np.zeros(n_samples, dtype=np.float64)

        for i, bit in enumerate(bits):
            start = i * samples_per_bit
            end = start + samples_per_bit
            t = np.linspace(0, bit_duration, samples_per_bit, endpoint=False)

            phase_shift = np.pi if bit == 1 else 0.0
            signal[start:end] = np.sin(2 * np.pi * carrier_freq * t + self.phase_key + phase_shift) * 0.3

        silt = np.random.normal(0, 0.02, n_samples)
        signal += silt

        self.stats["packets_sent"] += 1
        return np.clip(signal, -1.0, 1.0).astype(np.float32)

    def receive_data(self, audio_buffer: np.ndarray, n_bytes: int) -> bytes:
        carrier_freq = 6000.0
        bit_duration = 0.002
        samples_per_bit = int(self.sr * bit_duration)
        n_bits = n_bytes * 8

        bits = []
        for i in range(n_bits):
            start = i * samples_per_bit
            end = start + samples_per_bit
            if end > len(audio_buffer):
                break

            chunk = audio_buffer[start:end].astype(np.float64)
            t = np.linspace(0, bit_duration, len(chunk), endpoint=False)

            ref_0 = np.sin(2 * np.pi * carrier_freq * t + self.phase_key)
            ref_1 = np.sin(2 * np.pi * carrier_freq * t + self.phase_key + np.pi)

            corr_0 = np.sum(chunk * ref_0)
            corr_1 = np.sum(chunk * ref_1)

            bits.append(1 if corr_1 > corr_0 else 0)

        result = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i + 8]
            if len(byte_bits) < 8:
                break
            byte_val = 0
            for b in byte_bits:
                byte_val = (byte_val << 1) | b
            result.append(byte_val)

        self.stats["packets_received"] += 1
        return bytes(result)

    def connect(self) -> dict:
        with self._lock:
            self.mesh_state = "SCANNING"
        self._log_event("MESH_CONNECT", f"Node {self.node_id[:8]} entering Sovereign Mesh Mode")
        return {
            "success": True,
            "node_id": self.node_id,
            "state": self.mesh_state,
            "phase_key_hash": fatiha_286_truncated(str(self.phase_key).encode("utf-8"), 8),
        }

    def disconnect(self) -> dict:
        with self._lock:
            old_state = self.mesh_state
            self.mesh_state = "DARK"
            neighbor_count = len(self.neighbors)
            self.neighbors.clear()
        self._log_event("MESH_DISCONNECT", f"Left mesh from {old_state} state, {neighbor_count} neighbors released")
        return {
            "success": True,
            "previous_state": old_state,
            "neighbors_released": neighbor_count,
        }

    def register_neighbor(self, neighbor_id: str, signal_strength: float,
                          distance: float = 0.0) -> dict:
        with self._lock:
            self.neighbors[neighbor_id] = {
                "signal_strength": signal_strength,
                "estimated_distance_m": distance,
                "last_seen": time.time(),
                "packets_relayed": 0,
                "status": "active",
            }
            if self.mesh_state == "SCANNING":
                self.mesh_state = "CONNECTED"

        self._log_event("NEIGHBOR_FOUND", f"Registered {neighbor_id[:8]} (strength: {signal_strength:.2f})")
        return {"registered": True, "neighbor_id": neighbor_id, "total_neighbors": len(self.neighbors)}

    def buffer_for_dark_node(self, neighbor_id: str, data: bytes) -> dict:
        with self._lock:
            if neighbor_id not in self._flywheel_buffer:
                self._flywheel_buffer[neighbor_id] = {
                    "data": [],
                    "buffered_at": time.time(),
                }
            self._flywheel_buffer[neighbor_id]["data"].append(data)

            if neighbor_id in self.neighbors:
                self.neighbors[neighbor_id]["status"] = "dark"

            if self.mesh_state == "CONNECTED":
                self.mesh_state = "BRIDGING"

        self._log_event("FLYWHEEL_BUFFER", f"Buffering {len(data)} bytes for dark node {neighbor_id[:8]}")
        return {
            "buffered": True,
            "neighbor_id": neighbor_id,
            "total_buffered": sum(len(d) for d in self._flywheel_buffer[neighbor_id]["data"]),
        }

    def get_status(self) -> dict:
        with self._lock:
            neighbors_list = []
            for nid, ndata in self.neighbors.items():
                neighbors_list.append({
                    "node_id": nid,
                    "signal_strength": ndata["signal_strength"],
                    "estimated_distance_m": ndata["estimated_distance_m"],
                    "last_seen": ndata["last_seen"],
                    "last_seen_ago": time.time() - ndata["last_seen"],
                    "packets_relayed": ndata["packets_relayed"],
                    "status": ndata["status"],
                })

            buffer_status = {}
            for nid, bdata in self._flywheel_buffer.items():
                buffer_status[nid[:8]] = {
                    "chunks": len(bdata["data"]),
                    "total_bytes": sum(len(d) for d in bdata["data"]),
                    "age_seconds": time.time() - bdata["buffered_at"],
                }

        return {
            "node_id": self.node_id,
            "state": self.mesh_state,
            "neighbors": neighbors_list,
            "neighbor_count": len(neighbors_list),
            "stats": dict(self.stats),
            "flywheel_buffer": buffer_status,
            "mode": "SIMULATION",
        }

    def get_activity_log(self, limit: int = 50) -> list:
        with self._lock:
            return list(self.activity_log[-limit:])

    def _log_event(self, event_type: str, detail: str):
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            "detail": detail,
            "node": self.node_id[:8],
        }
        with self._lock:
            self.activity_log.append(entry)
            if len(self.activity_log) > 500:
                self.activity_log = self.activity_log[-250:]


class MeshPacket:

    def __init__(self, source_id: str, dest_id: str, payload: bytes,
                 packet_type: str = "DATA"):
        self.packet_id = str(uuid.uuid4())[:8]
        self.source_id = source_id
        self.dest_id = dest_id
        self.payload = payload
        self.packet_type = packet_type
        self.hops = 0
        self.max_hops = MAX_HOPS
        self.ttl = 300.0
        self.timestamp = time.time()
        self.route = [source_id]

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    def can_relay(self) -> bool:
        return self.hops < self.max_hops and not self.is_expired()

    def to_dict(self) -> dict:
        return {
            "packet_id": self.packet_id,
            "source_id": self.source_id,
            "dest_id": self.dest_id,
            "packet_type": self.packet_type,
            "hops": self.hops,
            "max_hops": self.max_hops,
            "ttl": self.ttl,
            "timestamp": self.timestamp,
            "payload_size": len(self.payload),
            "route": self.route,
        }

    @classmethod
    def create_broadcast(cls, source_id: str, payload: bytes) -> "MeshPacket":
        return cls(source_id, "BROADCAST", payload, packet_type="BROADCAST")

    @classmethod
    def create_discovery(cls, source_id: str) -> "MeshPacket":
        discovery_payload = json.dumps({
            "type": "DISCOVERY",
            "node_id": source_id,
            "timestamp": time.time(),
        }).encode()
        return cls(source_id, "BROADCAST", discovery_payload, packet_type="DISCOVERY")


class MeshRouter:

    def __init__(self, protocol: BeehiveProtocol):
        self.protocol = protocol
        self.node_id = protocol.node_id
        self.routing_table = {}
        self.seen_packets = set()
        self.relay_queue = []
        self._lock = threading.Lock()

    def process_packet(self, packet: MeshPacket) -> dict:
        with self._lock:
            if packet.packet_id in self.seen_packets:
                return {"action": "DROP", "reason": "Already seen"}
            self.seen_packets.add(packet.packet_id)

            if len(self.seen_packets) > 10000:
                self.seen_packets = set(list(self.seen_packets)[-5000:])

        if packet.is_expired():
            return {"action": "DROP", "reason": "TTL expired"}

        if packet.dest_id == self.node_id:
            self.protocol.stats["packets_received"] += 1
            self.protocol._log_event("PACKET_RECEIVED",
                f"From {packet.source_id[:8]} via {packet.hops} hops ({len(packet.payload)} bytes)")
            return {
                "action": "DELIVER",
                "payload": packet.payload,
                "source": packet.source_id,
                "hops": packet.hops,
                "route": packet.route,
            }

        if packet.dest_id == "BROADCAST":
            self.protocol.stats["packets_received"] += 1
            self.protocol._log_event("BROADCAST_RECEIVED",
                f"From {packet.source_id[:8]} ({packet.packet_type}, {packet.hops} hops)")

            if packet.can_relay():
                packet.hops += 1
                packet.route.append(self.node_id)
                self.relay_queue.append(packet)
                self.protocol.stats["packets_relayed"] += 1

            return {
                "action": "BROADCAST_DELIVER",
                "payload": packet.payload,
                "source": packet.source_id,
                "hops": packet.hops,
                "packet_type": packet.packet_type,
            }

        if packet.can_relay():
            packet.hops += 1
            packet.route.append(self.node_id)
            self.relay_queue.append(packet)
            self.protocol.stats["packets_relayed"] += 1

            relay_neighbor = self.routing_table.get(packet.dest_id)
            next_hop = packet.dest_id[:8] if relay_neighbor else "best-effort"

            self.protocol._log_event("PACKET_RELAY",
                f"Relaying to {next_hop} (hop {packet.hops}/{packet.max_hops})")

            if packet.source_id in self.protocol.neighbors:
                self.protocol.neighbors[packet.source_id]["packets_relayed"] += 1

            return {
                "action": "RELAY",
                "next_hop": next_hop,
                "hops": packet.hops,
                "cost_cc": RELAY_COST_CC,
            }

        return {"action": "DROP", "reason": f"Max hops exceeded ({packet.hops}/{packet.max_hops})"}

    def update_routing(self, neighbor_id: str, strength: float, hops: int = 1):
        with self._lock:
            existing = self.routing_table.get(neighbor_id)
            if existing is None or strength > existing["strength"] or hops < existing["hops"]:
                self.routing_table[neighbor_id] = {
                    "strength": strength,
                    "hops": hops,
                    "last_seen": time.time(),
                }

    def process_discovery(self, packet: MeshPacket) -> dict:
        try:
            data = json.loads(packet.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"processed": False, "reason": "Invalid discovery payload"}

        discovered_id = data.get("node_id", "")
        if not discovered_id or discovered_id == self.node_id:
            return {"processed": False, "reason": "Self-discovery or invalid"}

        self.update_routing(discovered_id, 0.5, packet.hops + 1)
        self.protocol.register_neighbor(discovered_id, 0.5)

        self.protocol._log_event("DISCOVERY_PROCESSED",
            f"Found node {discovered_id[:8]} at {packet.hops + 1} hops")

        return {
            "processed": True,
            "discovered_node": discovered_id,
            "hops_away": packet.hops + 1,
        }

    def create_packet(self, dest_id: str, payload: bytes,
                      packet_type: str = "DATA") -> MeshPacket:
        pkt = MeshPacket(self.node_id, dest_id, payload, packet_type)
        self.protocol.stats["packets_sent"] += 1
        self.protocol._log_event("PACKET_CREATED",
            f"To {dest_id[:8]} ({len(payload)} bytes, {packet_type})")
        return pkt

    def get_pending_relays(self) -> list:
        with self._lock:
            pending = list(self.relay_queue)
            self.relay_queue.clear()
        return pending

    def get_routing_table(self) -> dict:
        with self._lock:
            table = {}
            for nid, data in self.routing_table.items():
                table[nid[:8]] = {
                    "strength": data["strength"],
                    "hops": data["hops"],
                    "age_seconds": time.time() - data["last_seen"],
                }
        return table


def _sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def simulate_two_node_exchange(passphrase: str = "void-432",
                               payload: bytes = b"Hello from the Ghost Internet") -> dict:
    node_a = BeehiveProtocol(machine_id="VOID-4000-A", passphrase=passphrase)
    node_b = BeehiveProtocol(machine_id="VOID-4000-B", passphrase=passphrase)
    router_a = MeshRouter(node_a)
    router_b = MeshRouter(node_b)

    node_a.connect()
    node_b.connect()

    pulse_a = node_a.generate_handshake_pulse(duration=0.5)

    detection = node_b.detect_neighbor(pulse_a)
    if not detection["detected"]:
        return {"success": False, "stage": "detection", "error": detection["reason"]}

    auth = node_b.authenticate_phase(pulse_a, passphrase)
    if not auth["authenticated"]:
        return {"success": False, "stage": "authentication",
                "error": f"Phase diff {auth['phase_diff_deg']:.1f}° > {auth['tolerance_deg']}°"}

    whisper_signal = node_b.whisper_confirm(duration=0.5)
    whisper_check = node_a.verify_whisper(whisper_signal)

    node_a.register_neighbor(node_b.node_id, detection["signal_strength"],
                             detection["estimated_distance_m"])
    node_b.register_neighbor(node_a.node_id, detection["signal_strength"],
                             detection["estimated_distance_m"])
    router_a.update_routing(node_b.node_id, detection["signal_strength"])
    router_b.update_routing(node_a.node_id, detection["signal_strength"])

    tx_signal = node_a.transmit_data(payload)
    recovered = node_b.receive_data(tx_signal, len(payload))

    data_match = recovered == payload

    pkt = router_a.create_packet(node_b.node_id, payload)
    result = router_b.process_packet(pkt)

    return _sanitize_for_json({
        "success": bool(data_match and result["action"] == "DELIVER"),
        "detection": detection,
        "authentication": auth,
        "fatiha_handshake": {
            "phase_angle_deg": FATIHA_PHASE_ANGLE,
            "silt_embed_db": SILT_EMBED_DB,
            "fatiha_verified": detection.get("fatiha_verified", False),
            "silt_layer_present": detection.get("silt_layer_present", False),
            "whisper_confirmed": whisper_check.get("confirmed", False),
            "protocol": "Sura-Fatiha 286-Bit Acoustic Handshake",
        },
        "data_transmitted": len(payload),
        "data_recovered": len(recovered),
        "bit_perfect": bool(data_match),
        "packet_delivery": result["action"],
        "node_a_state": node_a.mesh_state,
        "node_b_state": node_b.mesh_state,
        "node_a_neighbors": len(node_a.neighbors),
        "node_b_neighbors": len(node_b.neighbors),
    })
