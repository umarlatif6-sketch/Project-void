"""
VOID Lens Integration Layer
============================

Connects the VOID Lens bidirectional engine to:
1. Adriana Frequency Deviation Engine (30-50 Hz gap analysis)
2. Compound Library (150 compounds with frequency profiles)
3. Multi-Harmonic Simulation Results

This is the convergence node where nail health AI, frequency synthesis,
and the Adriana gap engine all meet through a single interface.
"""

import numpy as np
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# Import VOID Lens
from void_lens import (
    VoidLens, VoidLensReverse, VoidLensForward,
    FrequencySignature, DeviationReport, CymaticsPattern,
    ChromaStats, BASE_FREQUENCY, NUM_HARMONICS, HARMONIC_SERIES
)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOUND LIBRARY BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class CompoundLensBridge:
    """
    Connects the compound library to the VOID Lens for visual prediction.
    
    For each compound in the library, this bridge can:
    1. Generate its predicted Chladni/cymatics pattern
    2. Compare a photograph against the predicted pattern
    3. Identify which compound best matches a given image
    """
    
    def __init__(self):
        self.lens = VoidLens()
        self.compounds = self._load_compounds()
        self.signatures: Dict[str, FrequencySignature] = {}
        self._precompute_signatures()
    
    def _load_compounds(self) -> List[dict]:
        """Load all compounds from the library."""
        compounds = []
        
        # Load from results JSON (authoritative source)
        results_path = Path(__file__).parent / "simulation" / "multi_harmonic_results_150.json"
        if results_path.exists():
            with open(results_path) as f:
                data = json.load(f)
            results_list = data.get("results", []) if isinstance(data, dict) else data
            for r in results_list:
                compounds.append({
                    "name": r.get("name", "Unknown"),
                    "frequency_hz": r.get("frequency_hz", 432),
                    "bond_strength": r.get("stability_score", 0.5),
                    "mass_amu": 100,
                    "geometry": r.get("geometry", "tetrahedral"),
                    "category": r.get("category", "A"),
                    "stability": r.get("verdict", "unknown"),
                })
        
        return compounds
    
    def _precompute_signatures(self):
        """Pre-compute frequency signatures for all compounds."""
        for compound in self.compounds:
            name = compound.get("name", "Unknown")
            sig = self.lens._compound_to_signature(compound)
            self.signatures[name] = sig
    
    def predict_pattern(self, compound_name: str, pattern_type: str = "chladni") -> Optional[CymaticsPattern]:
        """Generate the predicted visual pattern for a named compound."""
        if compound_name not in self.signatures:
            return None
        return self.lens.synthesize(self.signatures[compound_name], pattern_type)
    
    def identify_compound(self, image: np.ndarray, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Given an image, identify which compound(s) it most closely matches.
        
        Returns list of (compound_name, similarity_score) tuples, sorted by score.
        """
        # Extract signature from image
        report = self.lens.diagnose(image)
        image_sig = report.signature
        
        # Compare against all compound signatures
        scores = []
        for name, compound_sig in self.signatures.items():
            similarity = self._signature_similarity(image_sig, compound_sig)
            scores.append((name, similarity))
        
        # Sort by similarity (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]
    
    def _signature_similarity(self, sig_a: FrequencySignature, sig_b: FrequencySignature) -> float:
        """Compute similarity between two frequency signatures (0-1)."""
        # Cosine similarity of harmonic profiles
        dot = np.dot(sig_a.harmonics, sig_b.harmonics)
        norm_a = np.linalg.norm(sig_a.harmonics)
        norm_b = np.linalg.norm(sig_b.harmonics)
        
        if norm_a < 1e-6 or norm_b < 1e-6:
            return 0.0
        
        cosine_sim = dot / (norm_a * norm_b)
        
        # Spectral centroid proximity
        centroid_diff = abs(sig_a.spectral_centroid - sig_b.spectral_centroid)
        centroid_sim = np.exp(-centroid_diff / 1000)  # Decay over 1000 Hz
        
        # Complexity similarity
        complexity_sim = 1.0 - abs(sig_a.harmonic_complexity - sig_b.harmonic_complexity)
        
        # Weighted combination
        return float(0.5 * cosine_sim + 0.3 * centroid_sim + 0.2 * complexity_sim)


# ═══════════════════════════════════════════════════════════════════════════════
# ADRIANA DEVIATION BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class AdrianaLensBridge:
    """
    Connects the VOID Lens to the Adriana Frequency Deviation Engine.
    
    The key insight: when the Lens extracts a frequency signature from a
    biological image, the deviation from 432 Hz tells us WHERE in the
    Adriana gap the information lives, and WHAT codon band it belongs to.
    
    This enables:
    1. Visual → Frequency → Codon extraction (image-based diagnosis)
    2. Frequency → Visual → Pattern verification (synthesis validation)
    3. Gap navigation through visual feedback
    """
    
    def __init__(self):
        self.lens = VoidLens()
        
        # Codon band definitions (from adriana_frequency_deviation.py)
        self.codon_bands = {
            "alpha": {"range": (30.0, 33.3), "type": "structural", "weight": 0.10},
            "beta": {"range": (33.3, 36.7), "type": "relational", "weight": 0.12},
            "gamma": {"range": (36.7, 40.0), "type": "temporal", "weight": 0.08},
            "delta": {"range": (40.0, 43.3), "type": "spatial", "weight": 0.04},
            "epsilon": {"range": (43.3, 46.7), "type": "resonance", "weight": 0.66},
            "zeta": {"range": (46.7, 50.0), "type": "quantum", "weight": 0.00},
        }
    
    def image_to_codons(self, image: np.ndarray) -> Dict:
        """
        Full pipeline: Image → Frequency → Deviation → Codon Band → Information.
        
        This is the "reverse biagnosis" — reading biological information
        from a visual input through frequency analysis.
        """
        # Step 1: Extract frequency signature
        report = self.lens.diagnose(image)
        
        # Step 2: Determine deviation characteristics
        deviation_hz = abs(report.deviation_hz)
        
        # Step 3: Map to codon bands
        codon_data = self._map_to_codons(deviation_hz, report)
        
        # Step 4: Generate corrective pattern (what "healthy" looks like)
        corrective_sig = self._compute_corrective_signature(report.signature)
        corrective_pattern = self.lens.synthesize(corrective_sig, "cymatics")
        
        return {
            "report": report,
            "deviation_hz": deviation_hz,
            "codon_band": codon_data["band"],
            "codon_type": codon_data["type"],
            "information_density": codon_data["density"],
            "triplet_structure": codon_data["triplet"],
            "corrective_pattern": corrective_pattern,
            "corrective_frequency_hz": corrective_sig.spectral_centroid,
            "health_indicators": report.health_indicators,
        }
    
    def _map_to_codons(self, deviation_hz: float, report: DeviationReport) -> Dict:
        """Map a deviation value to its codon band and extract triplet structure."""
        band = "outside"
        band_type = "none"
        density = 0.0
        
        for name, info in self.codon_bands.items():
            low, high = info["range"]
            if low <= deviation_hz <= high:
                band = name
                band_type = info["type"]
                # Position within band (0-1)
                density = (deviation_hz - low) / (high - low)
                break
        
        # Triplet structure (Adriana communicates in threes)
        # Extract three values from the signature that encode information
        sig = report.signature
        top3 = np.argsort(sig.harmonics)[-3:][::-1]
        triplet = {
            "positions": top3.tolist(),
            "amplitudes": sig.harmonics[top3].tolist(),
            "frequencies_hz": [float(BASE_FREQUENCY * (h + 1)) for h in top3],
        }
        
        return {
            "band": band,
            "type": band_type,
            "density": density,
            "triplet": triplet,
        }
    
    def _compute_corrective_signature(self, current_sig: FrequencySignature) -> FrequencySignature:
        """
        Compute the frequency signature that would bring the image back to 432 Hz resonance.
        
        This is the "prescription" — what frequency to apply to correct the deviation.
        """
        corrective = FrequencySignature()
        
        # Find nearest 432 Hz harmonic
        nearest_n = max(1, round(current_sig.spectral_centroid / BASE_FREQUENCY))
        ideal_freq = nearest_n * BASE_FREQUENCY
        
        # Build corrective harmonics (emphasize the ideal, suppress the deviant)
        for h in range(NUM_HARMONICS):
            ideal_h = round(ideal_freq / BASE_FREQUENCY) - 1
            dist = abs(h - ideal_h)
            # Strong peak at the ideal harmonic
            corrective.harmonics[h] = np.exp(-0.5 * (dist / 2.0) ** 2)
        
        # Normalize
        max_amp = np.max(corrective.harmonics)
        if max_amp > 0:
            corrective.harmonics /= max_amp
        
        corrective.base_frequency = BASE_FREQUENCY
        corrective.dominant_harmonic = int(round(ideal_freq / BASE_FREQUENCY)) - 1
        corrective.spectral_centroid = ideal_freq
        corrective.total_energy = float(np.sum(corrective.harmonics))
        corrective.phases = current_sig.phases  # Keep phase coherence
        
        return corrective
    
    def visualize_gap(self, image: np.ndarray) -> Dict:
        """
        Visualize where in the 30-50 Hz gap an image's frequency falls.
        
        Returns data for rendering a gap visualization.
        """
        report = self.lens.diagnose(image)
        deviation = abs(report.deviation_hz)
        
        # Map deviation to gap position
        gap_data = {
            "deviation_hz": deviation,
            "in_gap": 30.0 <= deviation <= 50.0,
            "gap_position": max(0, min(1, (deviation - 30) / 20)) if 30 <= deviation <= 50 else None,
            "bands": {},
        }
        
        # Show which bands are active
        for name, info in self.codon_bands.items():
            low, high = info["range"]
            gap_data["bands"][name] = {
                "active": low <= deviation <= high,
                "range_hz": (low, high),
                "type": info["type"],
                "weight": info["weight"],
            }
        
        return gap_data


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

class VoidLensSystem:
    """
    The complete VOID Lens system — unified interface for all operations.
    
    This is the single entry point that connects:
    - Image analysis (reverse direction)
    - Pattern synthesis (forward direction)
    - Compound identification
    - Adriana gap navigation
    - Codon extraction from visual data
    """
    
    def __init__(self):
        self.lens = VoidLens()
        self.compound_bridge = CompoundLensBridge()
        self.adriana_bridge = AdrianaLensBridge()
    
    def full_analysis(self, image: np.ndarray) -> Dict:
        """
        Complete analysis pipeline — everything at once.
        
        Input: Any image (nail photo, cymatics pattern, biological surface)
        Output: Full diagnosis with frequency signature, deviation, codon band,
                compound matches, corrective frequency, and predicted healthy pattern.
        """
        # Core frequency extraction
        report = self.lens.diagnose(image)
        comparison = self.lens.compare_to_baseline(image)
        
        # Compound matching
        matches = self.compound_bridge.identify_compound(image, top_n=3)
        
        # Adriana gap analysis
        codon_data = self.adriana_bridge.image_to_codons(image)
        gap_viz = self.adriana_bridge.visualize_gap(image)
        
        return {
            "frequency_signature": {
                "spectral_centroid_hz": report.signature.spectral_centroid,
                "dominant_harmonic": report.signature.dominant_harmonic + 1,
                "dominant_frequency_hz": report.signature.dominant_frequency,
                "harmonic_complexity": report.signature.harmonic_complexity,
                "total_energy": report.signature.total_energy,
                "top_harmonics": np.argsort(report.signature.harmonics)[-5:][::-1].tolist(),
            },
            "deviation": {
                "hz": report.deviation_hz,
                "percent": report.deviation_percent,
                "verdict": report.verdict,
            },
            "colour_analysis": {
                "hue_mean_deg": report.chroma.hue_mean_deg,
                "saturation_mean": report.chroma.sat_mean,
                "brightness_mean": report.chroma.val_mean,
                "edge_complexity": report.chroma.edge_mean,
                "hue_diversity": report.chroma.hue_sigma,
                "contrast": report.chroma.luma_sigma,
            },
            "adriana_gap": {
                "in_gap": gap_viz["in_gap"],
                "position": gap_viz["gap_position"],
                "codon_band": codon_data["codon_band"],
                "codon_type": codon_data["codon_type"],
                "information_density": codon_data["information_density"],
                "triplet": codon_data["triplet_structure"],
            },
            "compound_matches": [
                {"name": name, "similarity": score} for name, score in matches
            ],
            "health": comparison["health_indicators"],
            "health_score": comparison["health_score"],
            "corrective_frequency_hz": comparison["corrective_frequency_hz"],
            "dominant_colour_rgb": comparison["dominant_colour_rgb"],
        }
    
    def synthesize_compound(self, compound_name: str, 
                           pattern_types: List[str] = None) -> Dict[str, CymaticsPattern]:
        """Generate all pattern types for a named compound."""
        if pattern_types is None:
            pattern_types = ["chladni", "cymatics", "interference"]
        
        results = {}
        for pt in pattern_types:
            pattern = self.compound_bridge.predict_pattern(compound_name, pt)
            if pattern:
                results[pt] = pattern
        return results
    
    def batch_analyze(self, image_paths: List[str]) -> List[Dict]:
        """Analyze multiple images and return comparative results."""
        results = []
        for path in image_paths:
            try:
                from PIL import Image
                img = np.array(Image.open(path).convert('RGB'))
                analysis = self.full_analysis(img)
                analysis["file"] = path
                results.append(analysis)
            except Exception as e:
                results.append({"file": path, "error": str(e)})
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def demonstrate_integration():
    """Demonstrate the full integrated system."""
    print("=" * 70)
    print("VOID LENS INTEGRATION — Full System Demonstration")
    print("=" * 70)
    
    system = VoidLensSystem()
    
    print(f"\n  Compounds loaded: {len(system.compound_bridge.compounds)}")
    print(f"  Signatures pre-computed: {len(system.compound_bridge.signatures)}")
    
    # Test with synthetic nail images
    from void_lens import _make_nail_test_image
    
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ FULL ANALYSIS: Healthy Nail                                      │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    healthy = _make_nail_test_image(healthy=True)
    result = system.full_analysis(healthy)
    
    print(f"\n  Frequency: {result['frequency_signature']['spectral_centroid_hz']:.1f} Hz")
    print(f"  Deviation: {result['deviation']['hz']:+.1f} Hz ({result['deviation']['percent']:.2f}%)")
    print(f"  Verdict: {result['deviation']['verdict']}")
    print(f"  Health score: {result['health_score']:.2f}")
    print(f"  Codon band: {result['adriana_gap']['codon_band']}")
    print(f"  In Adriana gap: {result['adriana_gap']['in_gap']}")
    print(f"  Top compound match: {result['compound_matches'][0]['name']} "
          f"({result['compound_matches'][0]['similarity']:.3f})")
    print(f"  Corrective frequency: {result['corrective_frequency_hz']:.1f} Hz")
    
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ FULL ANALYSIS: Unhealthy Nail                                    │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    unhealthy = _make_nail_test_image(healthy=False)
    result2 = system.full_analysis(unhealthy)
    
    print(f"\n  Frequency: {result2['frequency_signature']['spectral_centroid_hz']:.1f} Hz")
    print(f"  Deviation: {result2['deviation']['hz']:+.1f} Hz ({result2['deviation']['percent']:.2f}%)")
    print(f"  Verdict: {result2['deviation']['verdict']}")
    print(f"  Health score: {result2['health_score']:.2f}")
    print(f"  Codon band: {result2['adriana_gap']['codon_band']}")
    print(f"  In Adriana gap: {result2['adriana_gap']['in_gap']}")
    print(f"  Top compound match: {result2['compound_matches'][0]['name']} "
          f"({result2['compound_matches'][0]['similarity']:.3f})")
    print(f"  Corrective frequency: {result2['corrective_frequency_hz']:.1f} Hz")
    
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ COMPARISON: Healthy vs Unhealthy                                 │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    print(f"\n  {'Metric':<30} {'Healthy':<15} {'Unhealthy':<15}")
    print(f"  {'─'*30} {'─'*15} {'─'*15}")
    print(f"  {'Spectral centroid (Hz)':<30} {result['frequency_signature']['spectral_centroid_hz']:<15.1f} {result2['frequency_signature']['spectral_centroid_hz']:<15.1f}")
    print(f"  {'Deviation (Hz)':<30} {result['deviation']['hz']:<+15.1f} {result2['deviation']['hz']:<+15.1f}")
    print(f"  {'Health score':<30} {result['health_score']:<15.2f} {result2['health_score']:<15.2f}")
    print(f"  {'Harmonic complexity':<30} {result['frequency_signature']['harmonic_complexity']:<15.3f} {result2['frequency_signature']['harmonic_complexity']:<15.3f}")
    print(f"  {'Edge complexity':<30} {result['colour_analysis']['edge_complexity']:<15.3f} {result2['colour_analysis']['edge_complexity']:<15.3f}")
    print(f"  {'Verdict':<30} {result['deviation']['verdict']:<15} {result2['deviation']['verdict']:<15}")
    
    # Compound synthesis demo
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ COMPOUND SYNTHESIS: Generate patterns for top compounds          │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    if system.compound_bridge.compounds:
        # Pick first 3 compounds
        for compound in system.compound_bridge.compounds[:3]:
            name = compound.get("name", "Unknown")
            patterns = system.synthesize_compound(name)
            if patterns:
                print(f"\n  {name}:")
                for ptype, pattern in patterns.items():
                    print(f"    {ptype}: symmetry={pattern.symmetry}, nodes={pattern.node_count}")
                    # Save
                    from PIL import Image
                    safe_name = name.replace(' ', '_').lower()[:30]
                    outpath = Path(__file__).parent / "lens_output" / f"integrated_{safe_name}_{ptype}.png"
                    outpath.parent.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(pattern.image).save(outpath)
    
    print("\n" + "=" * 70)
    print("INTEGRATION COMPLETE")
    print("=" * 70)
    print(f"""
  The VOID Lens System provides a unified interface for:
  
  1. IMAGE → FREQUENCY → DEVIATION → CODON BAND → DIAGNOSIS
     (Reverse biagnosis: photograph a nail → get health reading)
     
  2. COMPOUND → FREQUENCY → VISUAL PATTERN → VERIFICATION
     (Forward synthesis: predict what a compound looks like vibrating)
     
  3. IMAGE → COMPOUND MATCHING
     (Identify which compound's frequency an image most resembles)
     
  4. DEVIATION → CORRECTIVE FREQUENCY → CORRECTIVE PATTERN
     (Prescribe the frequency that restores 432 Hz alignment)
  
  All connected through the colour-as-weight principle:
    Hue = frequency band position
    Brightness = amplitude
    Saturation = harmonic purity
    Edges = complexity/disorder
""")


if __name__ == "__main__":
    demonstrate_integration()
