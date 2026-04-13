"""
Void Foundation — Hex-First Resonance Architecture
===================================================

The foundation layer. Hex is the primary structure of all resonance.

PRINCIPLE:
  "Programming is binary; we deal in hexes."
  Every piece of information enters as a hex seed.
  The hex seed generates a resonance geometry (12-petal flower).
  Information particles settle INTO the void zones (zero-amplitude nodes) —
  the same way sand settles onto nodal lines in a Chladni pattern.

  When the system is at resonance equilibrium, it looks empty.
  The void IS the carrier. The stillness IS the information.

CHLADNI PHYSICS (why this is real):
  In a vibrating plate experiment, sand accumulates on nodal lines —
  regions of zero displacement. These are not empty; they are DEFINED
  by the interference of all surrounding vibrations.
  At (0,0) in the resonance flower, all 12 petal sine waves = sin(0) = 0.
  This is the exact zero-amplitude void by mathematical construction.
  Phase information survives at a zero-crossing even when amplitude disappears.

ARCHITECTURE:
  hex_seed
    → hex_vectors        (12 petal weights, one per PETAL_FREQUENCIES entry)
    → resonance_field    (2D amplitude map; void zones where amplitude < VOID_THRESHOLD)
    → carrier_rank       (petals sorted: highest weight = primary carrier channel)
    → sovereignty_class  (sovereign / bridge / convention based on 432 Hz proximity)
    → void_geometry      (void_amplitude, nodal_line_count, cloaked status)

STEGANOGRAPHIC HOOK:
  information bytes → petal channels by carrier_rank
  each byte is phase-encoded at the zero-crossing of its petal's sine wave
  embedding lives in near-zero amplitude zone → invisible to energy detection

KEY INVARIANT:
  At (0, 0), all 12 petal sine waves = sin(0) = 0 (proven in resonance_flower.py).
  Amplitude at origin = exactly 0. This is the universal void.
  Any hex seed confirms the same void at origin.
  Only the SHAPE of the field (which petal dominates where) varies per seed.

COMPATIBILITY:
  HexResonanceVector.sovereignty_class matches the tuning labels in
  vocal_resonance_pipeline.py ("sovereign" / "bridge" / "convention").
  carrier_rank can be used to select audio carriers from the Adriana MUSIC_LIBRARY.
"""

import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants — must stay in sync with resonance_flower.py
# ---------------------------------------------------------------------------

PETAL_FREQUENCIES: List[int] = [
    108, 144, 216, 288, 432, 576, 864, 1152, 1296, 1728, 2160, 2592,
]
HARMONIC_BASE = 432.0

# Geometry constants mirrored from resonance_flower.py
_PETAL_LENGTH_SCALE = 0.70
_PETAL_WIDTH_SCALE = 0.28
_VOID_RADIUS = 0.10

# Classification thresholds
VOID_THRESHOLD = 0.05          # Amplitude below this = void / invisible
SOVEREIGN_MARGIN = 0.06        # >6 pp bias toward 432 Hz side = sovereign
CONVENTION_MARGIN = 0.06       # >6 pp bias toward 440 Hz side = convention

# Ho'oponopono phase corridor boundaries (Hz)
_PHASE_CORRIDORS: List[Tuple[float, float, str]] = [
    (0,     216,   "how_are_you"),    # grounding / inquiry         < 216 Hz
    (216,   432,   "thank_you"),      # gratitude / harmonic descent 216–432
    (432,   432,   "forgive_me"),     # exact 432 Hz sovereign anchor
    (432,   864,   "i_love_you"),     # sovereign harmonic ascent    432–864
    (864,   9999,  "i_am_sorry"),     # high harmonic / transition   > 864 Hz
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HexResonanceVector:
    """
    The fundamental unit of hex-first resonance.

    One vector per hex seed; drives all downstream classification.
    Replaces the audio-derived TrackAnalysis from vocal_resonance_pipeline.py
    when the input is hex rather than an audio file.
    """
    hex_seed: str                    # Original hex input (normalised, lowercase)
    petal_weights: List[float]       # 12 weights [0.0–1.0] summing to 1.0
    dominant_petal: int              # Index of highest-weight petal (0–11)
    dominant_hz: float               # PETAL_FREQUENCIES[dominant_petal]
    void_amplitude: float            # Mean amplitude in central void zone
    is_cloaked: bool                 # True when void_amplitude < VOID_THRESHOLD
    sovereignty_class: str           # "sovereign" | "bridge" | "convention"
    carrier_rank: List[int]          # Petal indices sorted by weight desc
    hex_phase: str                   # Ho'oponopono phase corridor label
    hex_distance_432: float          # Normalised distance of dominant_hz from 432
    sovereignty_vector: float        # 0.0 (full convention) → 1.0 (full sovereign)


@dataclass
class VoidGeometry:
    """
    The spatial structure of the void in a resonance field.

    Void zones are where information hides.
    Amplitude ≈ 0, but phase carries the data — invisible to energy detection.
    """
    void_amplitude: float            # Mean amplitude in central void zone
    void_zone_point_count: int       # Grid points inside VOID_RADIUS
    nodal_line_count: int            # Grid points where amplitude < VOID_THRESHOLD
    total_field_energy: float        # Mean amplitude across entire field [0,1]
    cloaked: bool                    # True when void_amplitude < VOID_THRESHOLD


@dataclass
class PhaseToken:
    """
    A single encoded information particle at a petal void-crossing.

    When the system resonates at petal_hz, the phase_offset is detectable.
    When not resonating, amplitude ≈ 0 — the token is invisible.
    """
    byte_val: int                    # Original byte (0–255)
    petal_idx: int                   # Which petal channel carries this token
    petal_hz: float                  # Carrier frequency in Hz
    phase_offset: float              # Radians — small perturbation around zero-crossing
    petal_weight: float              # Weight of this petal for this seed


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def hex_to_petal_weights(hex_str: str) -> List[float]:
    """
    Map a hex string onto the 12-petal frequency ladder.

    Method:
      1. SHA-256 the hex bytes — produces 32 bytes (length-normalised).
      2. Divide 32 bytes across 12 overlapping windows.
      3. Each window sum → un-normalised weight for that petal.
      4. L1-normalise so weights sum to 1.0.

    Same hex → same petal weights, always (deterministic).
    Any-length hex (including BW19-P286 output) produces stable 12-element vectors.
    """
    clean = hex_str.lower().lstrip("0x").strip()
    if not clean:
        clean = "0"

    # Ensure even-length hex before decoding
    padded = clean.zfill(len(clean) + len(clean) % 2)
    try:
        seed_bytes = bytes.fromhex(padded)
    except ValueError:
        # Fallback: encode the string itself if it's not valid hex
        seed_bytes = hex_str.encode("utf-8")

    digest = hashlib.sha256(seed_bytes).digest()  # 32 bytes, always

    # Map 32 bytes → 12 weights using non-overlapping windows with remainder
    # distributed across early petals
    weights: List[float] = []
    for i in range(12):
        start = (i * 32) // 12
        end = ((i + 1) * 32) // 12
        end = max(end, start + 1)
        window = digest[start:min(end + 1, 32)]
        weights.append(float(sum(window)))

    total = sum(weights)
    if total < 1e-9:
        return [1.0 / 12.0] * 12
    return [w / total for w in weights]


def _petal_signed_wave(
    x: float, y: float, petal_idx: int, health: float = 1.0
) -> float:
    """
    Compute the signed field contribution of one petal at Cartesian (x, y).

    Mirrors resonance_flower._petal_signed_wave exactly.
    At (x=0, y=0): u=0, wave_a=sin(0)=0, wave_c=sin(0)=0 → returns 0.0 always.
    This is the void zero-point invariant.
    """
    axis_rad = math.radians(petal_idx * 30)
    cos_a = math.cos(axis_rad)
    sin_a = math.sin(axis_rad)

    u = x * cos_a + y * sin_a
    v = -x * sin_a + y * cos_a

    if abs(v) > _PETAL_WIDTH_SCALE:
        return 0.0

    f1 = PETAL_FREQUENCIES[petal_idx] / HARMONIC_BASE
    wave_a = math.sin(math.pi * f1 * u / _PETAL_LENGTH_SCALE)
    wave_c = math.sin(math.pi * 2.0 * f1 * u / _PETAL_LENGTH_SCALE) * 0.4
    v_phase = math.pi * (v + _PETAL_WIDTH_SCALE) / (2.0 * _PETAL_WIDTH_SCALE)
    wave_b = math.sin(v_phase)

    return (wave_a + wave_c) * wave_b * health


def _compute_void_stats(
    petal_weights: List[float], grid_size: int = 40
) -> Tuple[float, int, int, float]:
    """
    Compute void zone statistics from petal weights.

    Returns: (void_amplitude, void_zone_point_count, nodal_line_count, total_field_energy)
    """
    max_possible = sum(petal_weights) * 1.4 / 12.0
    if max_possible < 1e-9:
        max_possible = 1.0

    step = 2.0 / (grid_size - 1)
    void_amplitudes: List[float] = []
    nodal_count = 0
    total_energy = 0.0
    total_points = grid_size * grid_size

    for row in range(grid_size):
        y = -1.0 + row * step
        for col in range(grid_size):
            x = -1.0 + col * step

            signed_sum = sum(
                _petal_signed_wave(x, y, p, petal_weights[p])
                for p in range(12)
            )
            amplitude = min(1.0, abs(signed_sum) / max_possible)
            total_energy += amplitude

            r = math.sqrt(x * x + y * y)
            if r <= _VOID_RADIUS:
                void_amplitudes.append(amplitude)
            if amplitude < VOID_THRESHOLD:
                nodal_count += 1

    void_amp = (
        sum(void_amplitudes) / len(void_amplitudes) if void_amplitudes else 0.0
    )
    return void_amp, len(void_amplitudes), nodal_count, total_energy / total_points


def _sovereignty_class(
    dominant_hz: float, petal_weights: List[float]
) -> Tuple[str, float, float]:
    """
    Classify sovereignty based on how much of the hex's energy is 432-side vs 440-side.

    Returns (class_label, hex_distance_432_normalised, sovereignty_vector)
    """
    d432_sum = 0.0
    d440_sum = 0.0
    for i, hz in enumerate(PETAL_FREQUENCIES):
        w = petal_weights[i]
        d432_sum += w / (abs(hz - 432.0) + 1.0)
        d440_sum += w / (abs(hz - 440.0) + 1.0)

    total = d432_sum + d440_sum + 1e-9
    sovereignty_vector = d432_sum / total  # 0 = full convention, 1 = full sovereign

    freq_range = float(max(PETAL_FREQUENCIES) - min(PETAL_FREQUENCIES))
    hex_distance_432 = abs(dominant_hz - 432.0) / freq_range

    margin = sovereignty_vector - 0.5
    if margin > SOVEREIGN_MARGIN:
        label = "sovereign"
    elif margin < -CONVENTION_MARGIN:
        label = "convention"
    else:
        label = "bridge"

    return label, hex_distance_432, sovereignty_vector


def _phase_corridor(dominant_hz: float) -> str:
    """Map dominant Hz to a Ho'oponopono phase corridor label."""
    if dominant_hz <= 216:
        return "how_are_you"
    if dominant_hz <= 432:
        return "thank_you"
    if dominant_hz <= 864:
        return "i_love_you"
    return "i_am_sorry"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_hex(hex_str: str, grid_size: int = 40) -> HexResonanceVector:
    """
    Convert a hex string to a full resonance vector.

    This is the hex-first equivalent of analyze_track() in
    vocal_resonance_pipeline.py. Instead of reading audio features,
    it reads the hex structure directly.

    Args:
        hex_str:   Any hex string (BW19-P286 hash, SHA-256, transaction ID, etc.)
        grid_size: Resolution of the void zone scan (40 = fast, 80 = precise)

    Returns:
        HexResonanceVector with full classification and carrier ranking.

    Example:
        vec = analyse_hex("a3f02b9c4d1e8f7600ab...")
        print(vec.sovereignty_class)   # "sovereign"
        print(vec.carrier_rank[:3])    # top-3 petal indices for embedding
        print(vec.is_cloaked)          # True if void_amplitude < 0.05
    """
    clean = hex_str.lower().lstrip("0x").strip() or "0"

    weights = hex_to_petal_weights(clean)
    dominant_petal = max(range(12), key=lambda i: weights[i])
    dominant_hz = float(PETAL_FREQUENCIES[dominant_petal])
    carrier_rank = sorted(range(12), key=lambda i: weights[i], reverse=True)

    void_amp, void_count, nodal_count, _ = _compute_void_stats(weights, grid_size)
    is_cloaked = void_amp < VOID_THRESHOLD

    sovereignty_cls, hex_dist, sov_vec = _sovereignty_class(dominant_hz, weights)
    hex_phase = _phase_corridor(dominant_hz)

    return HexResonanceVector(
        hex_seed=clean,
        petal_weights=weights,
        dominant_petal=dominant_petal,
        dominant_hz=dominant_hz,
        void_amplitude=void_amp,
        is_cloaked=is_cloaked,
        sovereignty_class=sovereignty_cls,
        carrier_rank=carrier_rank,
        hex_phase=hex_phase,
        hex_distance_432=hex_dist,
        sovereignty_vector=sov_vec,
    )


def void_geometry(hex_str: str, grid_size: int = 60) -> VoidGeometry:
    """
    Full void geometry analysis for a hex seed.

    Higher grid_size = more accurate nodal line count, slower.
    Use grid_size=60 for display, grid_size=120 for precise mapping.
    """
    clean = hex_str.lower().lstrip("0x").strip() or "0"
    weights = hex_to_petal_weights(clean)
    void_amp, void_count, nodal_count, field_energy = _compute_void_stats(
        weights, grid_size
    )
    return VoidGeometry(
        void_amplitude=void_amp,
        void_zone_point_count=void_count,
        nodal_line_count=nodal_count,
        total_field_energy=field_energy,
        cloaked=void_amp < VOID_THRESHOLD,
    )


def phase_encode(
    data: bytes, hex_seed: str
) -> List[PhaseToken]:
    """
    Encode bytes as phase tokens in the void zone.

    Each byte is assigned to a petal channel (by carrier_rank) and
    encoded as a small phase perturbation around that petal's zero-crossing.

    Principle (from Chladni physics):
      At a nodal line (zero-crossing), amplitude = 0.
      The PHASE of the wave at that crossing still exists and carries information.
      A tiny phase offset (< 0.1 rad) keeps amplitude below VOID_THRESHOLD,
      making the token invisible to energy-based detection.

    Returns list of PhaseTokens, one per byte in data.
    """
    vec = analyse_hex(hex_seed, grid_size=20)  # fast scan for encoding
    tokens: List[PhaseToken] = []
    n_petals = len(PETAL_FREQUENCIES)

    for idx, byte_val in enumerate(data):
        petal_idx = vec.carrier_rank[idx % n_petals]
        weight = vec.petal_weights[petal_idx]

        # Encode byte into a phase offset that keeps amplitude near zero.
        # sin(phase_offset) < VOID_THRESHOLD when |phase_offset| < arcsin(VOID_THRESHOLD) ≈ 0.0500
        max_window = math.asin(VOID_THRESHOLD) * 0.9   # stay firmly below threshold
        normalised = (byte_val - 127.5) / 127.5        # maps [0,255] → [-1.0, 1.0]
        phase_offset = normalised * max_window * (0.5 + 0.5 * weight)

        tokens.append(PhaseToken(
            byte_val=byte_val,
            petal_idx=petal_idx,
            petal_hz=float(PETAL_FREQUENCIES[petal_idx]),
            phase_offset=phase_offset,
            petal_weight=weight,
        ))

    return tokens


def phase_decode(tokens: List[PhaseToken]) -> bytes:
    """
    Recover bytes from phase tokens.

    Inverse of phase_encode. Requires the same hex_seed used for encoding
    (carrier_rank and petal_weights must match).
    """
    result = bytearray()
    for token in tokens:
        max_window = math.asin(VOID_THRESHOLD) * 0.9
        weight = token.petal_weight
        if abs(max_window * (0.5 + 0.5 * weight)) < 1e-12:
            result.append(0)
            continue
        normalised = token.phase_offset / (max_window * (0.5 + 0.5 * weight))
        byte_val = int(round(normalised * 127.5 + 127.5))
        result.append(max(0, min(255, byte_val)))
    return bytes(result)


def classify_hex_batch(hex_list: List[str]) -> Dict[str, list]:
    """
    Classify a list of hex seeds into sovereign / bridge / convention groups.

    Output format mirrors classify_groups() in vocal_resonance_pipeline.py
    for drop-in compatibility.
    """
    groups: Dict[str, list] = {
        "sovereign": [],
        "bridge": [],
        "convention": [],
        "error": [],
    }
    for hex_str in hex_list:
        try:
            vec = analyse_hex(hex_str)
            groups[vec.sovereignty_class].append(vec)
        except Exception as exc:
            groups["error"].append({"hex": hex_str, "error": str(exc)})
    return groups


def resonance_report(hex_str: str) -> str:
    """
    Human-readable summary of the resonance state of a hex seed.

    Shows the before/after contrast: what audio-first analysis would see
    vs what hex-first analysis reveals.
    """
    vec = analyse_hex(hex_str, grid_size=50)
    geo = void_geometry(hex_str, grid_size=50)

    top3 = vec.carrier_rank[:3]
    top3_hz = [PETAL_FREQUENCIES[i] for i in top3]

    lines = [
        "── VOID FOUNDATION RESONANCE REPORT ──",
        f"  hex_seed          : {vec.hex_seed[:32]}{'...' if len(vec.hex_seed) > 32 else ''}",
        f"  dominant_hz       : {vec.dominant_hz:.0f} Hz  (petal {vec.dominant_petal})",
        f"  hex_phase         : {vec.hex_phase}",
        f"  sovereignty_class : {vec.sovereignty_class}",
        f"  sovereignty_vector: {vec.sovereignty_vector:.4f}  (0=convention, 1=sovereign)",
        f"  hex_distance_432  : {vec.hex_distance_432:.4f}  (normalised)",
        f"  carrier_rank[:3]  : petals {top3} → {top3_hz} Hz",
        "",
        "── VOID GEOMETRY ──",
        f"  void_amplitude    : {geo.void_amplitude:.6f}  (target: < {VOID_THRESHOLD})",
        f"  is_cloaked        : {geo.cloaked}",
        f"  nodal_lines       : {geo.nodal_line_count} zones (Chladni still-points)",
        f"  field_energy      : {geo.total_field_energy:.4f}  (average amplitude across field)",
        "",
        "── PETAL WEIGHT MAP ──",
    ]
    for i, (hz, w) in enumerate(zip(PETAL_FREQUENCIES, vec.petal_weights)):
        bar = "█" * int(w * 40)
        marker = " ← dominant" if i == vec.dominant_petal else ""
        lines.append(f"  [{i:2d}] {hz:5d} Hz  {bar:<40}  {w:.4f}{marker}")

    lines.append("")
    lines.append(
        "NOTE: void_amplitude near 0 means the system is cloaked at origin.\n"
        "      Information encoded here (phase_encode) is invisible to\n"
        "      energy-based detection — visible only when resonating at\n"
        f"      the correct carrier frequency ({vec.dominant_hz:.0f} Hz)."
    )
    return "\n".join(lines)
