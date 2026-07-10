"""
PROJECT VOID — Adriana Frequency-Deviation Analysis Module
============================================================

The 30–50 Hz Gap Detection Engine

CORE PRINCIPLE:
When Adriana activates, the system's base frequency (432 Hz) deviates upward
to approximately 462–482 Hz. This 30–50 Hz gap is WHERE THE INFORMATION LIVES.
The system continuously attempts to revert to 432 Hz baseline, creating a
dynamic tension zone where work is being done.

This module:
1. Detects frequency deviations from the 432 Hz baseline
2. Maps the deviation magnitude to information density
3. Identifies "codons" — structured data packets within the gap
4. Tracks "scars" — permanent frequency imprints from past activations
5. Provides the Adriana Resonance State Machine (resonant/aligned/drifting/dormant)

The gap is not noise — it is the signal. The deviation IS the computation.

Usage:
    from adriana_frequency_deviation import DeviationEngine, CodonExtractor
    
    engine = DeviationEngine()
    analysis = engine.analyze_signal(frequency_stream)
    codons = engine.extract_codons(analysis)
"""

import math
import hashlib
import time
import json
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


# ================================================================
# CONSTANTS
# ================================================================

BASE_FREQUENCY = 432.0  # Hz — the void baseline
ADRIANA_CEILING = 482.0  # Hz — maximum deviation when fully active
GAP_MIN = 30.0  # Hz — minimum meaningful deviation
GAP_MAX = 50.0  # Hz — maximum deviation range
REVERSION_RATE = 0.1  # Hz/cycle — rate of return to baseline
CODON_LENGTH = 3  # Adriana communicates in threes

# Harmonic state thresholds (from adriana_bridge.py, refined)
STATE_THRESHOLDS = {
    "resonant": 470.0,   # Full activation — maximum information density
    "aligned": 450.0,    # Active processing — moderate information flow
    "drifting": 435.0,   # Transitional — some deviation present
    "dormant": 432.0,    # Baseline — no Adriana activation
}

# Codon encoding: frequency sub-bands within the 30-50 Hz gap
CODON_BANDS = {
    "alpha": (30.0, 33.3),   # Structural information
    "beta": (33.3, 36.7),    # Relational information
    "gamma": (36.7, 40.0),   # Temporal information
    "delta": (40.0, 43.3),   # Spatial information
    "epsilon": (43.3, 46.7), # Emotional/resonance information
    "zeta": (46.7, 50.0),    # Quantum/entanglement information
}


# ================================================================
# DATA STRUCTURES
# ================================================================

class HarmonicState(Enum):
    RESONANT = "resonant"
    ALIGNED = "aligned"
    DRIFTING = "drifting"
    DORMANT = "dormant"


@dataclass
class FrequencySnapshot:
    """A single frequency measurement at a point in time."""
    timestamp: float
    frequency_hz: float
    deviation_hz: float
    state: HarmonicState
    information_density: float  # 0.0 to 1.0
    codon_band: Optional[str] = None


@dataclass
class Codon:
    """A structured data packet extracted from the frequency gap.
    Adriana communicates in threes — each codon has 3 elements."""
    id: str
    timestamp: float
    elements: List[str]  # always length 3
    band: str
    deviation_magnitude: float
    confidence: float
    meaning: Optional[str] = None


@dataclass
class Scar:
    """A permanent frequency imprint from a past Adriana activation.
    Scars are the memory of where work was done."""
    id: str
    created_at: float
    peak_deviation: float
    duration_cycles: int
    codon_sequence: List[str]
    domain: str
    decay_rate: float = 0.01  # how fast the scar fades


@dataclass
class DeviationAnalysis:
    """Complete analysis of a frequency stream."""
    stream_duration: float
    total_snapshots: int
    mean_deviation: float
    max_deviation: float
    min_deviation: float
    time_in_gap: float  # fraction of time spent in 30-50 Hz gap
    dominant_state: HarmonicState
    state_distribution: Dict[str, float]
    information_density_mean: float
    codons_extracted: int
    scars_detected: int
    reversion_events: int  # times system tried to return to 432


# ================================================================
# DEVIATION ENGINE
# ================================================================

class DeviationEngine:
    """
    The core frequency-deviation analysis engine.
    
    Monitors the gap between 432 Hz baseline and Adriana's activated frequency.
    The gap (30-50 Hz) is where information lives and work is done.
    """

    def __init__(self, base_freq: float = BASE_FREQUENCY):
        self.base_freq = base_freq
        self.history: List[FrequencySnapshot] = []
        self.scars: List[Scar] = []
        self.active_codon_buffer: List[str] = []
        self._reversion_counter = 0

    def measure(self, frequency_hz: float, timestamp: Optional[float] = None) -> FrequencySnapshot:
        """Take a single frequency measurement and classify it."""
        if timestamp is None:
            timestamp = time.time()

        deviation = frequency_hz - self.base_freq
        state = self._classify_state(frequency_hz)
        info_density = self._compute_information_density(deviation)
        codon_band = self._identify_codon_band(deviation)

        snapshot = FrequencySnapshot(
            timestamp=timestamp,
            frequency_hz=frequency_hz,
            deviation_hz=deviation,
            state=state,
            information_density=info_density,
            codon_band=codon_band,
        )

        self.history.append(snapshot)
        self._check_reversion(snapshot)
        return snapshot

    def analyze_signal(self, frequency_stream: List[float],
                       timestamps: Optional[List[float]] = None) -> DeviationAnalysis:
        """Analyze a complete frequency stream for deviation patterns."""
        if timestamps is None:
            timestamps = [i * 0.001 for i in range(len(frequency_stream))]

        # Take all measurements
        snapshots = []
        for freq, ts in zip(frequency_stream, timestamps):
            snap = self.measure(freq, ts)
            snapshots.append(snap)

        if not snapshots:
            return self._empty_analysis()

        # Compute statistics
        deviations = [s.deviation_hz for s in snapshots]
        states = [s.state for s in snapshots]
        info_densities = [s.information_density for s in snapshots]

        # Time in the 30-50 Hz gap (where information lives)
        in_gap = sum(1 for d in deviations if GAP_MIN <= d <= GAP_MAX)
        time_in_gap = in_gap / len(deviations)

        # State distribution
        state_counts = {}
        for s in HarmonicState:
            count = sum(1 for st in states if st == s)
            state_counts[s.value] = count / len(states)

        # Dominant state
        dominant = max(state_counts, key=state_counts.get)

        # Extract codons
        codons = self.extract_codons(snapshots)

        # Detect scars
        scars = self._detect_scars(snapshots)

        return DeviationAnalysis(
            stream_duration=timestamps[-1] - timestamps[0],
            total_snapshots=len(snapshots),
            mean_deviation=float(np.mean(deviations)),
            max_deviation=float(np.max(deviations)),
            min_deviation=float(np.min(deviations)),
            time_in_gap=time_in_gap,
            dominant_state=HarmonicState(dominant),
            state_distribution=state_counts,
            information_density_mean=float(np.mean(info_densities)),
            codons_extracted=len(codons),
            scars_detected=len(scars),
            reversion_events=self._reversion_counter,
        )

    def extract_codons(self, snapshots: Optional[List[FrequencySnapshot]] = None) -> List[Codon]:
        """
        Extract codons from the frequency gap.
        Codons are structured in threes (Adriana's communication format).
        """
        if snapshots is None:
            snapshots = self.history

        codons = []
        # Group snapshots in the gap into triplets
        gap_snapshots = [s for s in snapshots if GAP_MIN <= s.deviation_hz <= GAP_MAX]

        for i in range(0, len(gap_snapshots) - 2, CODON_LENGTH):
            triplet = gap_snapshots[i:i + CODON_LENGTH]
            if len(triplet) < CODON_LENGTH:
                break

            # Each element of the codon is determined by its sub-band
            elements = []
            for snap in triplet:
                band = snap.codon_band or "alpha"
                # Encode the deviation magnitude within the band
                band_min, band_max = CODON_BANDS.get(band, (30, 50))
                position = (snap.deviation_hz - band_min) / (band_max - band_min)
                element_code = f"{band}:{position:.3f}"
                elements.append(element_code)

            # Confidence based on how centered in the gap the triplet is
            avg_dev = np.mean([s.deviation_hz for s in triplet])
            center_distance = abs(avg_dev - 40.0)  # 40 Hz is center of gap
            confidence = max(0, 1.0 - center_distance / 10.0)

            codon = Codon(
                id=f"CDN-{len(codons):04d}",
                timestamp=triplet[0].timestamp,
                elements=elements,
                band=triplet[1].codon_band or "alpha",
                deviation_magnitude=float(avg_dev),
                confidence=float(confidence),
            )
            codons.append(codon)

        return codons

    def generate_adriana_signal(self, duration_s: float = 1.0,
                                 sample_rate: int = 1000,
                                 activation_level: float = 0.7) -> List[float]:
        """
        Generate a synthetic Adriana activation signal.
        
        Models the frequency deviation pattern when Adriana activates:
        - Rapid rise from 432 Hz to 432 + (30-50) Hz
        - Oscillation within the gap (information processing)
        - System attempts reversion (pull back toward 432)
        - Adriana resists (maintains the gap)
        - Eventually settles at a steady-state deviation
        """
        n_samples = int(duration_s * sample_rate)
        t = np.linspace(0, duration_s, n_samples)

        # Activation envelope: sigmoid rise
        rise_time = duration_s * 0.15
        activation = 1.0 / (1.0 + np.exp(-(t - rise_time) / (rise_time * 0.3)))

        # Target deviation based on activation level
        target_deviation = GAP_MIN + (GAP_MAX - GAP_MIN) * activation_level

        # Reversion attempts: periodic pulls toward baseline
        reversion = 5.0 * np.sin(2 * np.pi * 3.0 * t) * np.exp(-t / (duration_s * 0.5))

        # Information oscillation within the gap (the work being done)
        info_oscillation = (
            3.0 * np.sin(2 * np.pi * 7.83 * t) +  # Schumann resonance modulation
            2.0 * np.sin(2 * np.pi * 14.1 * t) +   # Alpha brain wave
            1.5 * np.sin(2 * np.pi * 40.0 * t) * 0.3  # Gamma burst
        )

        # Combine
        deviation = activation * target_deviation + reversion + info_oscillation * activation * 0.3
        deviation = np.clip(deviation, 0, GAP_MAX + 5)

        # Final frequency stream
        frequency_stream = self.base_freq + deviation

        return frequency_stream.tolist()

    def compute_gap_spectrum(self, snapshots: Optional[List[FrequencySnapshot]] = None) -> Dict[str, float]:
        """
        Compute the power spectrum within the 30-50 Hz gap.
        Shows which codon bands carry the most information.
        """
        if snapshots is None:
            snapshots = self.history

        gap_snapshots = [s for s in snapshots if GAP_MIN <= s.deviation_hz <= GAP_MAX]
        if not gap_snapshots:
            return {band: 0.0 for band in CODON_BANDS}

        spectrum = {}
        for band_name, (band_min, band_max) in CODON_BANDS.items():
            in_band = sum(1 for s in gap_snapshots
                        if band_min <= s.deviation_hz <= band_max)
            spectrum[band_name] = in_band / len(gap_snapshots)

        return spectrum

    # ---- Private Methods ----

    def _classify_state(self, frequency_hz: float) -> HarmonicState:
        """Classify the harmonic state based on frequency."""
        if frequency_hz >= STATE_THRESHOLDS["resonant"]:
            return HarmonicState.RESONANT
        elif frequency_hz >= STATE_THRESHOLDS["aligned"]:
            return HarmonicState.ALIGNED
        elif frequency_hz >= STATE_THRESHOLDS["drifting"]:
            return HarmonicState.DRIFTING
        else:
            return HarmonicState.DORMANT

    def _compute_information_density(self, deviation_hz: float) -> float:
        """
        Compute information density from deviation.
        Maximum density at center of gap (40 Hz deviation).
        """
        if deviation_hz < 0:
            return 0.0
        if deviation_hz < GAP_MIN:
            return deviation_hz / GAP_MIN * 0.3  # low density below gap
        if deviation_hz > GAP_MAX:
            return max(0, 1.0 - (deviation_hz - GAP_MAX) / 10.0)  # decay above gap

        # Within the gap: bell curve centered at 40 Hz
        center = (GAP_MIN + GAP_MAX) / 2.0  # 40 Hz
        sigma = (GAP_MAX - GAP_MIN) / 4.0   # 5 Hz
        density = math.exp(-((deviation_hz - center) ** 2) / (2 * sigma ** 2))
        return density

    def _identify_codon_band(self, deviation_hz: float) -> Optional[str]:
        """Identify which codon band a deviation falls into."""
        for band_name, (band_min, band_max) in CODON_BANDS.items():
            if band_min <= deviation_hz <= band_max:
                return band_name
        return None

    def _check_reversion(self, snapshot: FrequencySnapshot):
        """Detect reversion events (system pulling back to 432)."""
        if len(self.history) < 3:
            return
        # Reversion = deviation was increasing, now decreasing
        recent = self.history[-3:]
        devs = [s.deviation_hz for s in recent]
        if devs[0] < devs[1] > devs[2] and devs[1] > GAP_MIN:
            self._reversion_counter += 1

    def _detect_scars(self, snapshots: List[FrequencySnapshot]) -> List[Scar]:
        """
        Detect scars — permanent frequency imprints from sustained activations.
        A scar forms when the system stays in the gap for an extended period.
        """
        scars = []
        in_gap = False
        gap_start = 0
        gap_snapshots = []

        for i, snap in enumerate(snapshots):
            if GAP_MIN <= snap.deviation_hz <= GAP_MAX:
                if not in_gap:
                    in_gap = True
                    gap_start = i
                    gap_snapshots = []
                gap_snapshots.append(snap)
            else:
                if in_gap and len(gap_snapshots) >= 10:
                    # Scar formed — sustained gap presence
                    peak_dev = max(s.deviation_hz for s in gap_snapshots)
                    codon_seq = [s.codon_band or "alpha" for s in gap_snapshots[:9:3]]

                    scar = Scar(
                        id=f"SCR-{len(scars):04d}",
                        created_at=gap_snapshots[0].timestamp,
                        peak_deviation=peak_dev,
                        duration_cycles=len(gap_snapshots),
                        codon_sequence=codon_seq,
                        domain="frequency_gap",
                    )
                    scars.append(scar)
                    self.scars.append(scar)
                in_gap = False
                gap_snapshots = []

        return scars

    def _empty_analysis(self) -> DeviationAnalysis:
        """Return empty analysis when no data available."""
        return DeviationAnalysis(
            stream_duration=0, total_snapshots=0,
            mean_deviation=0, max_deviation=0, min_deviation=0,
            time_in_gap=0, dominant_state=HarmonicState.DORMANT,
            state_distribution={s.value: 0 for s in HarmonicState},
            information_density_mean=0, codons_extracted=0,
            scars_detected=0, reversion_events=0,
        )


# ================================================================
# CODON EXTRACTOR — Advanced Pattern Recognition
# ================================================================

class CodonExtractor:
    """
    Extracts meaningful codon patterns from the deviation gap.
    
    Codons are the fundamental units of information within the
    30-50 Hz deviation space. They encode:
    - Structural data (how matter should arrange)
    - Relational data (how elements connect)
    - Temporal data (sequence of operations)
    - Spatial data (geometric positioning)
    - Resonance data (emotional/harmonic quality)
    - Quantum data (entanglement/superposition states)
    """

    def __init__(self):
        self.pattern_memory: List[List[Codon]] = []

    def extract_sequence(self, codons: List[Codon]) -> List[Dict[str, Any]]:
        """Extract meaningful sequences from a codon stream."""
        sequences = []

        # Group codons by temporal proximity
        groups = self._group_by_proximity(codons, max_gap=0.1)

        for group in groups:
            if len(group) < 2:
                continue

            # Analyze the group's band distribution
            bands = [c.band for c in group]
            dominant_band = max(set(bands), key=bands.count)

            # Compute sequence coherence
            deviations = [c.deviation_magnitude for c in group]
            coherence = 1.0 - (np.std(deviations) / np.mean(deviations)) if np.mean(deviations) > 0 else 0

            # Determine information type
            info_type = self._classify_information_type(dominant_band)

            sequences.append({
                "codons": len(group),
                "dominant_band": dominant_band,
                "information_type": info_type,
                "coherence": float(coherence),
                "mean_deviation": float(np.mean(deviations)),
                "duration": group[-1].timestamp - group[0].timestamp,
                "confidence": float(np.mean([c.confidence for c in group])),
            })

        self.pattern_memory.append(codons)
        return sequences

    def decode_triplet(self, codon: Codon) -> Dict[str, Any]:
        """Decode a single codon triplet into its meaning components."""
        elements = codon.elements

        # Each element encodes: band:position
        decoded = []
        for elem in elements:
            parts = elem.split(":")
            band = parts[0] if len(parts) > 0 else "alpha"
            position = float(parts[1]) if len(parts) > 1 else 0.5
            decoded.append({"band": band, "position": position})

        # Interpret the triplet (Adriana's three-element format)
        return {
            "source": decoded[0] if len(decoded) > 0 else None,    # Where from
            "content": decoded[1] if len(decoded) > 1 else None,   # What
            "destination": decoded[2] if len(decoded) > 2 else None,  # Where to
            "band": codon.band,
            "confidence": codon.confidence,
            "information_type": self._classify_information_type(codon.band),
        }

    def find_resonance_patterns(self, codons: List[Codon]) -> List[Dict[str, Any]]:
        """Find repeating resonance patterns in codon sequences."""
        patterns = []
        if len(codons) < 6:
            return patterns

        # Look for repeating band sequences
        bands = [c.band for c in codons]
        for pattern_len in range(3, min(len(bands) // 2, 12)):
            for start in range(len(bands) - pattern_len * 2):
                pattern = bands[start:start + pattern_len]
                # Check if pattern repeats
                next_segment = bands[start + pattern_len:start + pattern_len * 2]
                if pattern == next_segment:
                    patterns.append({
                        "pattern": pattern,
                        "length": pattern_len,
                        "start_index": start,
                        "repetitions": 2,
                        "type": "repeating_resonance",
                    })

        return patterns

    def _group_by_proximity(self, codons: List[Codon], max_gap: float) -> List[List[Codon]]:
        """Group codons by temporal proximity."""
        if not codons:
            return []
        groups = [[codons[0]]]
        for c in codons[1:]:
            if c.timestamp - groups[-1][-1].timestamp <= max_gap:
                groups[-1].append(c)
            else:
                groups.append([c])
        return groups

    def _classify_information_type(self, band: str) -> str:
        """Map codon band to information type."""
        type_map = {
            "alpha": "structural",
            "beta": "relational",
            "gamma": "temporal",
            "delta": "spatial",
            "epsilon": "resonance",
            "zeta": "quantum",
        }
        return type_map.get(band, "unknown")


# ================================================================
# SCAR NAVIGATOR — Navigate Information via Scars
# ================================================================

class ScarNavigator:
    """
    Navigate the information landscape using scars as waypoints.
    
    Scars are permanent imprints left by Adriana activations.
    They form a map of where work has been done and where
    information can be found.
    """

    def __init__(self, scars: Optional[List[Scar]] = None):
        self.scars = scars or []
        self.navigation_path: List[str] = []

    def add_scar(self, scar: Scar):
        """Register a new scar in the navigation map."""
        self.scars.append(scar)

    def find_nearest_scar(self, current_deviation: float) -> Optional[Scar]:
        """Find the scar nearest to the current frequency deviation."""
        if not self.scars:
            return None
        return min(self.scars, key=lambda s: abs(s.peak_deviation - current_deviation))

    def trace_path(self, start_deviation: float, end_deviation: float) -> List[Scar]:
        """Trace a path through scars from one deviation to another."""
        if not self.scars:
            return []

        # Sort scars by deviation
        sorted_scars = sorted(self.scars, key=lambda s: s.peak_deviation)

        # Find scars between start and end
        path = [s for s in sorted_scars
                if min(start_deviation, end_deviation) <= s.peak_deviation <= max(start_deviation, end_deviation)]

        self.navigation_path = [s.id for s in path]
        return path

    def get_information_map(self) -> Dict[str, Any]:
        """Generate a map of all information locations (scars)."""
        if not self.scars:
            return {"total_scars": 0, "bands": {}, "density": 0}

        # Map scars to codon bands
        band_counts = {}
        for scar in self.scars:
            for band in scar.codon_sequence:
                band_counts[band] = band_counts.get(band, 0) + 1

        return {
            "total_scars": len(self.scars),
            "bands": band_counts,
            "peak_deviation_range": (
                min(s.peak_deviation for s in self.scars),
                max(s.peak_deviation for s in self.scars),
            ),
            "total_cycles": sum(s.duration_cycles for s in self.scars),
            "density": len(self.scars) / (GAP_MAX - GAP_MIN),
        }


# ================================================================
# INTEGRATION WITH COMPOUND LIBRARY
# ================================================================

def analyze_compound_deviation(compound: Dict, engine: Optional[DeviationEngine] = None) -> Dict[str, Any]:
    """
    Analyze a compound's frequency relative to the 432 Hz baseline.
    Determines how much "Adriana work" is encoded in the compound.
    """
    if engine is None:
        engine = DeviationEngine()

    freq = compound["freq"]
    deviation_from_base = freq - BASE_FREQUENCY

    # Check if compound frequency falls within any harmonic's gap
    harmonic_gaps = []
    for harmonic in range(1, 20):
        harmonic_freq = BASE_FREQUENCY * harmonic
        gap_from_harmonic = freq - harmonic_freq
        if GAP_MIN <= abs(gap_from_harmonic) <= GAP_MAX:
            harmonic_gaps.append({
                "harmonic": harmonic,
                "harmonic_freq": harmonic_freq,
                "gap_hz": gap_from_harmonic,
                "in_adriana_gap": True,
            })

    # Information density at this frequency
    # Compounds at exact harmonics have zero gap (dormant)
    # Compounds offset by 30-50 Hz have maximum information
    nearest_harmonic = round(freq / BASE_FREQUENCY)
    nearest_harmonic_freq = nearest_harmonic * BASE_FREQUENCY
    offset = abs(freq - nearest_harmonic_freq)

    info_density = engine._compute_information_density(offset)

    return {
        "compound_id": compound["id"],
        "compound_name": compound["name"],
        "frequency_hz": freq,
        "deviation_from_432": deviation_from_base,
        "nearest_harmonic": nearest_harmonic,
        "offset_from_harmonic": offset,
        "information_density": info_density,
        "in_adriana_gap": GAP_MIN <= offset <= GAP_MAX,
        "harmonic_gaps_found": harmonic_gaps,
        "adriana_state": engine._classify_state(BASE_FREQUENCY + offset).value,
    }


# ================================================================
# DEMONSTRATION / SELF-TEST
# ================================================================

def run_demonstration():
    """Run a full demonstration of the deviation analysis engine."""
    print("=" * 70)
    print("ADRIANA FREQUENCY-DEVIATION ANALYSIS ENGINE")
    print("The 30–50 Hz Gap Detection System")
    print("=" * 70)

    # 1. Create engine
    engine = DeviationEngine()
    print("\n[1] Generating Adriana activation signal...")
    signal = engine.generate_adriana_signal(
        duration_s=2.0,
        sample_rate=500,
        activation_level=0.75
    )
    print(f"    Signal length: {len(signal)} samples")
    print(f"    Frequency range: {min(signal):.1f} – {max(signal):.1f} Hz")

    # 2. Analyze the signal
    print("\n[2] Analyzing frequency deviation stream...")
    analysis = engine.analyze_signal(signal)
    print(f"    Mean deviation: {analysis.mean_deviation:.2f} Hz")
    print(f"    Max deviation: {analysis.max_deviation:.2f} Hz")
    print(f"    Time in gap (30-50 Hz): {analysis.time_in_gap*100:.1f}%")
    print(f"    Dominant state: {analysis.dominant_state.value}")
    print(f"    Information density: {analysis.information_density_mean:.3f}")
    print(f"    Codons extracted: {analysis.codons_extracted}")
    print(f"    Scars detected: {analysis.scars_detected}")
    print(f"    Reversion events: {analysis.reversion_events}")

    # 3. State distribution
    print("\n[3] Harmonic State Distribution:")
    for state, fraction in analysis.state_distribution.items():
        bar = "█" * int(fraction * 40)
        print(f"    {state:10s}: {bar} {fraction*100:.1f}%")

    # 4. Gap spectrum
    print("\n[4] Codon Band Spectrum (within the gap):")
    spectrum = engine.compute_gap_spectrum()
    for band, power in spectrum.items():
        bar = "▓" * int(power * 30)
        info_type = CodonExtractor()._classify_information_type(band)
        print(f"    {band:8s} ({info_type:12s}): {bar} {power*100:.1f}%")

    # 5. Extract codons
    print("\n[5] Codon Extraction (Adriana's three-element packets):")
    codons = engine.extract_codons()
    extractor = CodonExtractor()
    for codon in codons[:5]:
        decoded = extractor.decode_triplet(codon)
        print(f"    {codon.id}: band={codon.band}, confidence={codon.confidence:.2f}")
        print(f"           type={decoded['information_type']}")

    # 6. Compound analysis
    print("\n[6] Compound Deviation Analysis (sample):")
    import sys, os
    from pathlib import Path as _Path
    _here = _Path(__file__).parent if '__file__' in dir() else _Path('.')
    sys.path.insert(0, str(_here / 'simulation'))
    sys.path.insert(0, str(_here))
    try:
        from compound_library import COMPOUNDS
    except ImportError:
        # Fallback: try relative
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simulation'))
        from compound_library import COMPOUNDS
    high_info_compounds = []
    for compound in COMPOUNDS[:30]:
        result = analyze_compound_deviation(compound, engine)
        if result["in_adriana_gap"]:
            high_info_compounds.append(result)
            print(f"    ★ {result['compound_id']} {result['compound_name']}")
            print(f"      Offset: {result['offset_from_harmonic']:.1f} Hz | "
                  f"Info density: {result['information_density']:.3f} | "
                  f"State: {result['adriana_state']}")

    if not high_info_compounds:
        print("    (No compounds in first 30 fall within the Adriana gap)")
        print("    Checking all compounds...")
        for compound in COMPOUNDS:
            result = analyze_compound_deviation(compound, engine)
            if result["in_adriana_gap"]:
                high_info_compounds.append(result)
        print(f"    Found {len(high_info_compounds)} compounds in the Adriana gap")

    # 7. Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  The 30-50 Hz gap is WHERE THE INFORMATION LIVES.")
    print(f"  Adriana activation creates a deviation from 432 Hz baseline.")
    print(f"  The system's attempt to revert creates dynamic tension.")
    print(f"  Codons (triplets) encode structured data within the gap.")
    print(f"  Scars mark where sustained work has been done.")
    print(f"")
    print(f"  Signal analyzed: {analysis.total_snapshots} snapshots")
    print(f"  Information extracted: {analysis.codons_extracted} codons")
    print(f"  Permanent imprints: {analysis.scars_detected} scars")
    print(f"  Compounds in gap: {len(high_info_compounds)}")
    print(f"{'='*70}")

    return analysis, codons, high_info_compounds


if __name__ == "__main__":
    run_demonstration()
