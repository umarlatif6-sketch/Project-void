"""
VOID Lens — Bidirectional Image ↔ Frequency Engine
===================================================

Inspired by Lumen's Lens (pixelsncodes/lumen), adapted for Project VOID's
432 Hz frequency-mechanics framework.

FORWARD: Frequency signature → Visual pattern (cymatics visualization)
REVERSE: Image → Frequency signature → 432 Hz deviation analysis (diagnosis)

The key insight: COLOUR IS FREQUENCY WEIGHT.
- Hue determines which frequency band dominates
- Brightness determines amplitude at that frequency
- Saturation determines harmonic purity
- Texture (edges) determines harmonic complexity

Technical basis from Lumen's source (LensEngine.cpp):
- Scan mode: row luminance → waveform (brightness = amplitude)
- Spectral mode: column brightness → harmonic amplitudes (log-frequency mapping)
- Chroma stats: HSV analysis → synth parameters (hue→filter, sat→resonance, etc.)

VOID adaptation:
- Base frequency: 432 Hz (not arbitrary)
- Harmonic series: 432, 864, 1296, 1728, 2160... (not equal-tempered)
- Deviation measurement: compare extracted signature to 432 Hz ideal
- Codon extraction: triplet patterns in the deviation signal
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

BASE_FREQUENCY = 432.0  # Hz — the root of everything
NUM_HARMONICS = 64      # Number of harmonics to analyze (up to 64th harmonic of 432)
FRAME_LENGTH = 2048     # Samples per frame (matching Lumen)
NUM_FRAMES = 64         # Frames per analysis (matching Lumen)
ANALYSIS_SIZE = 256     # Chroma analysis resolution (matching Lumen)
WORKING_SIZE = 512      # Working image max dimension (matching Lumen)

# 432 Hz harmonic series
HARMONIC_SERIES = np.array([BASE_FREQUENCY * (i + 1) for i in range(NUM_HARMONICS)])

# Colour-to-frequency band mapping (hue in degrees → harmonic region)
# Based on visible light spectrum analogy:
#   Red (0°)     → 1st harmonic (432 Hz) — lowest, most fundamental
#   Orange (30°) → 2nd–4th harmonics (864–1728 Hz)
#   Yellow (60°) → 5th–8th harmonics (2160–3456 Hz)
#   Green (120°) → 9th–16th harmonics (3888–6912 Hz)
#   Blue (240°)  → 17th–32nd harmonics (7344–13824 Hz)
#   Violet (300°)→ 33rd–64th harmonics (14256–27648 Hz)
HUE_BANDS = [
    (0, 30, 0, 1),      # Red → fundamental
    (30, 60, 1, 4),     # Orange → low harmonics
    (60, 120, 4, 8),    # Yellow → mid-low harmonics
    (120, 180, 8, 16),  # Green → mid harmonics
    (180, 240, 16, 32), # Cyan-Blue → mid-high harmonics
    (240, 300, 32, 48), # Blue → high harmonics
    (300, 360, 48, 64), # Violet → highest harmonics
]

# Adriana gap parameters
ADRIANA_GAP_LOW = 30.0   # Hz above baseline
ADRIANA_GAP_HIGH = 50.0  # Hz above baseline

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ChromaStats:
    """Image colour statistics (matching Lumen's ChromaStats structure)."""
    hue_mean_deg: float = 0.0    # Saturation-weighted circular mean hue
    sat_mean: float = 0.0        # Mean saturation
    val_mean: float = 0.0        # Mean brightness (HSV V)
    luma_sigma: float = 0.0      # 2 × stddev(luminance), clamped 0–1
    edge_mean: float = 0.0       # Mean Sobel magnitude / 4, clamped 0–1
    hue_sigma: float = 0.0       # Circular hue dispersion (1 - R)


@dataclass
class FrequencySignature:
    """A frequency fingerprint extracted from an image or compound."""
    harmonics: np.ndarray = field(default_factory=lambda: np.zeros(NUM_HARMONICS))
    phases: np.ndarray = field(default_factory=lambda: np.zeros(NUM_HARMONICS))
    base_frequency: float = BASE_FREQUENCY
    dominant_harmonic: int = 1
    spectral_centroid: float = 432.0
    harmonic_complexity: float = 0.0  # 0 = pure sine, 1 = maximum complexity
    total_energy: float = 0.0
    
    @property
    def dominant_frequency(self) -> float:
        return self.base_frequency * (self.dominant_harmonic + 1)
    
    @property
    def deviation_from_432(self) -> float:
        """How far the spectral centroid deviates from the nearest 432 Hz harmonic."""
        nearest_harmonic = round(self.spectral_centroid / BASE_FREQUENCY)
        ideal = nearest_harmonic * BASE_FREQUENCY
        return self.spectral_centroid - ideal


@dataclass
class DeviationReport:
    """Diagnosis report: how an image's frequency signature deviates from 432 Hz."""
    signature: FrequencySignature = field(default_factory=FrequencySignature)
    chroma: ChromaStats = field(default_factory=ChromaStats)
    deviation_hz: float = 0.0
    deviation_percent: float = 0.0
    in_adriana_gap: bool = False
    gap_position: float = 0.0  # 0.0 = bottom of gap (30 Hz), 1.0 = top (50 Hz)
    health_indicators: Dict[str, float] = field(default_factory=dict)
    codon_band: str = ""  # Which codon band this deviation falls in
    verdict: str = ""     # RESONANT / DEVIANT / CRITICAL


@dataclass
class CymaticsPattern:
    """Visual pattern generated from a frequency signature (forward direction)."""
    image: np.ndarray = field(default_factory=lambda: np.zeros((256, 256, 3)))
    frequency: float = 432.0
    harmonic_order: int = 1
    symmetry: int = 6  # Rotational symmetry order
    node_count: int = 0
    pattern_type: str = ""  # chladni / cymatics / interference


# ═══════════════════════════════════════════════════════════════════════════════
# REVERSE ENGINE: Image → Frequency Signature → 432 Hz Deviation
# ═══════════════════════════════════════════════════════════════════════════════

class VoidLensReverse:
    """
    Extracts frequency signatures from images using colour-as-weight.
    
    Technical method (derived from Lumen's LensEngine.cpp):
    1. Downscale to 256×256 for analysis
    2. Convert to HSV colour space
    3. Compute ChromaStats (hue, saturation, value, edges)
    4. Map colour properties to frequency amplitudes:
       - Hue → which harmonic band (spectral position)
       - Brightness → amplitude at that harmonic
       - Saturation → harmonic purity (high sat = narrow band)
       - Edges → harmonic complexity (many edges = many partials)
    5. Compare resulting signature to 432 Hz harmonic series
    6. Measure deviation and classify
    """
    
    def __init__(self, baseline_hz: float = BASE_FREQUENCY):
        self.baseline_hz = baseline_hz
        self.harmonic_series = np.array([baseline_hz * (i + 1) for i in range(NUM_HARMONICS)])
    
    def analyze_image(self, image: np.ndarray) -> DeviationReport:
        """
        Full analysis pipeline: image → frequency signature → deviation report.
        
        Args:
            image: RGB image as numpy array (H, W, 3), values 0–255
            
        Returns:
            DeviationReport with full diagnosis
        """
        # Step 1: Prepare image
        img = self._prepare_image(image)
        
        # Step 2: Compute chroma statistics
        chroma = self._compute_chroma_stats(img)
        
        # Step 3: Extract frequency signature using colour-as-weight
        signature = self._extract_frequency_signature(img, chroma)
        
        # Step 4: Compute deviation from 432 Hz baseline
        report = self._compute_deviation(signature, chroma)
        
        return report
    
    def analyze_file(self, filepath: str) -> DeviationReport:
        """Analyze an image file."""
        from PIL import Image
        img = np.array(Image.open(filepath).convert('RGB'))
        return self.analyze_image(img)
    
    def _prepare_image(self, image: np.ndarray) -> np.ndarray:
        """Downscale to analysis size, matching Lumen's 256×256 chroma copy."""
        from PIL import Image
        h, w = image.shape[:2]
        
        # Never upscale (matching Lumen)
        if max(h, w) > WORKING_SIZE:
            scale = WORKING_SIZE / max(h, w)
            new_h, new_w = max(4, int(h * scale)), max(4, int(w * scale))
            pil_img = Image.fromarray(image).resize((new_w, new_h), Image.BILINEAR)
            image = np.array(pil_img)
        
        # Create 256×256 analysis copy
        pil_img = Image.fromarray(image).resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.BILINEAR)
        return np.array(pil_img)
    
    def _compute_chroma_stats(self, img: np.ndarray) -> ChromaStats:
        """
        Compute colour statistics matching Lumen's chromaStats() exactly.
        
        Lumen computes:
        - Saturation-weighted circular mean hue
        - Mean saturation, mean value
        - Luma sigma (2 × stddev of luminance)
        - Edge mean (Sobel magnitude / 4)
        - Hue sigma (circular dispersion)
        """
        # Convert RGB to HSV
        img_float = img.astype(np.float32) / 255.0
        
        # Luminance (Rec.709, matching Lumen's lumaOf)
        luma = 0.2126 * img_float[:,:,0] + 0.7152 * img_float[:,:,1] + 0.0722 * img_float[:,:,2]
        
        # HSV conversion
        r, g, b = img_float[:,:,0], img_float[:,:,1], img_float[:,:,2]
        cmax = np.maximum(np.maximum(r, g), b)
        cmin = np.minimum(np.minimum(r, g), b)
        delta = cmax - cmin
        
        # Hue (in degrees)
        hue = np.zeros_like(delta)
        mask_r = (cmax == r) & (delta > 0)
        mask_g = (cmax == g) & (delta > 0)
        mask_b = (cmax == b) & (delta > 0)
        hue[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
        hue[mask_g] = 60 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
        hue[mask_b] = 60 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)
        hue[hue < 0] += 360
        
        # Saturation (safe division)
        sat = np.where(cmax > 1e-7, delta / np.maximum(cmax, 1e-7), 0.0)
        
        # Value (brightness)
        val = cmax
        
        # Saturation-weighted circular mean hue (matching Lumen exactly)
        hue_rad = np.deg2rad(hue)
        hue_x = np.sum(sat * np.cos(hue_rad))
        hue_y = np.sum(sat * np.sin(hue_rad))
        hue_weight = np.sum(sat)
        
        stats = ChromaStats()
        
        if hue_weight > 1e-9:
            hm = np.degrees(np.arctan2(hue_y, hue_x))
            if hm < 0:
                hm += 360
            stats.hue_mean_deg = float(hm)
            r_val = np.sqrt(hue_x**2 + hue_y**2) / hue_weight
            stats.hue_sigma = float(np.clip(1.0 - r_val, 0, 1))
        
        stats.sat_mean = float(np.mean(sat))
        stats.val_mean = float(np.mean(val))
        
        # Luma sigma: 2 × stddev (matching Lumen)
        stats.luma_sigma = float(np.clip(2.0 * np.std(luma), 0, 1))
        
        # Edge mean: Sobel magnitude / 4 (matching Lumen)
        # Sobel on interior pixels
        if luma.shape[0] > 2 and luma.shape[1] > 2:
            # Sobel X
            gx = (-luma[:-2, :-2] + luma[:-2, 2:]
                  - 2*luma[1:-1, :-2] + 2*luma[1:-1, 2:]
                  - luma[2:, :-2] + luma[2:, 2:])
            # Sobel Y
            gy = (-luma[:-2, :-2] - 2*luma[:-2, 1:-1] - luma[:-2, 2:]
                  + luma[2:, :-2] + 2*luma[2:, 1:-1] + luma[2:, 2:])
            edge_mag = np.sqrt(gx**2 + gy**2)
            stats.edge_mean = float(np.clip(np.mean(edge_mag) / 4.0, 0, 1))
        
        return stats
    
    def _extract_frequency_signature(self, img: np.ndarray, chroma: ChromaStats) -> FrequencySignature:
        """
        Extract frequency signature using colour-as-weight differentiation.
        
        This is the VOID adaptation of Lumen's spectral mode:
        - Instead of arbitrary frequency mapping, we map to 432 Hz harmonics
        - Colour hue determines WHICH harmonic band
        - Brightness determines amplitude AT that harmonic
        - Saturation determines bandwidth (narrow = pure tone)
        
        Technical method:
        1. For each pixel, determine its hue → harmonic band
        2. Its brightness → amplitude contribution to that band
        3. Its saturation → how narrowly focused (high sat = single harmonic)
        4. Aggregate across all pixels → harmonic amplitude spectrum
        """
        img_float = img.astype(np.float32) / 255.0
        
        # Compute per-pixel HSV
        r, g, b = img_float[:,:,0], img_float[:,:,1], img_float[:,:,2]
        cmax = np.maximum(np.maximum(r, g), b)
        cmin = np.minimum(np.minimum(r, g), b)
        delta = cmax - cmin
        
        # Hue in degrees
        hue = np.zeros_like(delta)
        mask_r = (cmax == r) & (delta > 0)
        mask_g = (cmax == g) & (delta > 0)
        mask_b = (cmax == b) & (delta > 0)
        hue[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
        hue[mask_g] = 60 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
        hue[mask_b] = 60 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)
        hue[hue < 0] += 360
        
        sat = np.where(cmax > 1e-7, delta / np.maximum(cmax, 1e-7), 0.0)
        val = cmax
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        # Initialize harmonic amplitudes
        harmonics = np.zeros(NUM_HARMONICS)
        harmonic_counts = np.zeros(NUM_HARMONICS)
        
        # Method 1: Hue-band mapping (colour tells you WHERE in spectrum)
        for hue_low, hue_high, harm_low, harm_high in HUE_BANDS:
            # Find pixels in this hue band
            if hue_low < hue_high:
                mask = (hue >= hue_low) & (hue < hue_high)
            else:
                mask = (hue >= hue_low) | (hue < hue_high)
            
            if not np.any(mask):
                continue
            
            # Brightness of these pixels = amplitude contribution
            brightness_in_band = luma[mask]
            saturation_in_band = sat[mask]
            
            # High saturation = concentrated on fewer harmonics
            # Low saturation = spread across the band
            mean_sat = np.mean(saturation_in_band)
            mean_brightness = np.mean(brightness_in_band)
            
            # Distribute energy across harmonics in this band
            num_harmonics_in_band = harm_high - harm_low
            if num_harmonics_in_band <= 0:
                continue
                
            # Concentration factor: high saturation → energy in center of band
            # Low saturation → spread evenly
            center = (harm_low + harm_high) // 2
            for h in range(harm_low, min(harm_high, NUM_HARMONICS)):
                # Gaussian distribution centered on band center, width from saturation
                dist_from_center = abs(h - center) / max(1, num_harmonics_in_band / 2)
                # High saturation = narrow gaussian (concentrated)
                sigma = 0.3 + 0.7 * (1.0 - mean_sat)  # 0.3 (pure) to 1.0 (gray)
                weight = np.exp(-0.5 * (dist_from_center / sigma) ** 2)
                
                # Amplitude = brightness × weight × pixel count proportion
                pixel_proportion = np.sum(mask) / (ANALYSIS_SIZE * ANALYSIS_SIZE)
                harmonics[h] += mean_brightness * weight * pixel_proportion
                harmonic_counts[h] += 1
        
        # Method 2: Spectral mode (Lumen-style column analysis for fine detail)
        # Vertical scan: each column contributes to harmonic profile
        for col in range(0, ANALYSIS_SIZE, 4):  # Sample every 4th column
            column_luma = luma[:, col]
            # Log-frequency mapping (matching Lumen): top = high freq, bottom = low
            for h in range(NUM_HARMONICS):
                y_norm = 1.0 - np.log(h + 1) / np.log(NUM_HARMONICS)
                y = int(np.clip(y_norm * (ANALYSIS_SIZE - 1), 0, ANALYSIS_SIZE - 1))
                # 3×3 mean (matching Lumen's brightnessAt)
                y_lo = max(0, y - 1)
                y_hi = min(ANALYSIS_SIZE - 1, y + 1)
                local_brightness = np.mean(column_luma[y_lo:y_hi+1])
                # Power 1.5 (matching Lumen's contrast boost)
                harmonics[h] += local_brightness ** 1.5 * 0.3  # 0.3 weight for spectral contribution
        
        # Normalize
        max_amp = np.max(harmonics)
        if max_amp > 1e-6:
            harmonics = harmonics / max_amp
        
        # Generate deterministic phases (matching Lumen's seeded approach)
        # Use image hash as seed
        seed = hash(img.tobytes()[:1024]) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        phases = rng.uniform(0, 2 * np.pi, NUM_HARMONICS)
        
        # Compute derived metrics
        sig = FrequencySignature()
        sig.harmonics = harmonics
        sig.phases = phases
        sig.base_frequency = self.baseline_hz
        sig.dominant_harmonic = int(np.argmax(harmonics))
        
        # Spectral centroid (amplitude-weighted mean frequency)
        freqs = self.harmonic_series
        total_energy = np.sum(harmonics)
        if total_energy > 1e-6:
            sig.spectral_centroid = float(np.sum(freqs * harmonics) / total_energy)
        else:
            sig.spectral_centroid = self.baseline_hz
        
        # Harmonic complexity: spectral flatness (geometric mean / arithmetic mean)
        nonzero = harmonics[harmonics > 1e-6]
        if len(nonzero) > 1:
            geo_mean = np.exp(np.mean(np.log(nonzero)))
            arith_mean = np.mean(nonzero)
            sig.harmonic_complexity = float(geo_mean / arith_mean) if arith_mean > 0 else 0
        
        sig.total_energy = float(total_energy)
        
        return sig
    
    def _compute_deviation(self, signature: FrequencySignature, chroma: ChromaStats) -> DeviationReport:
        """
        Compute how far the extracted signature deviates from 432 Hz ideal.
        
        The deviation measurement:
        1. Find nearest 432 Hz harmonic to the spectral centroid
        2. Measure absolute deviation in Hz
        3. Check if deviation falls in Adriana's 30–50 Hz gap
        4. Classify into codon bands
        5. Generate health indicators
        """
        report = DeviationReport()
        report.signature = signature
        report.chroma = chroma
        
        # Deviation from nearest 432 Hz harmonic
        nearest_n = max(1, round(signature.spectral_centroid / self.baseline_hz))
        ideal_freq = nearest_n * self.baseline_hz
        deviation = signature.spectral_centroid - ideal_freq
        
        report.deviation_hz = float(deviation)
        report.deviation_percent = float(abs(deviation) / ideal_freq * 100)
        
        # Check Adriana gap (30–50 Hz above baseline)
        abs_dev = abs(deviation)
        if ADRIANA_GAP_LOW <= abs_dev <= ADRIANA_GAP_HIGH:
            report.in_adriana_gap = True
            report.gap_position = float((abs_dev - ADRIANA_GAP_LOW) / (ADRIANA_GAP_HIGH - ADRIANA_GAP_LOW))
            
            # Classify into codon bands
            if abs_dev < 33.3:
                report.codon_band = "alpha"  # Structural
            elif abs_dev < 36.7:
                report.codon_band = "beta"   # Relational
            elif abs_dev < 40.0:
                report.codon_band = "gamma"  # Temporal
            elif abs_dev < 43.3:
                report.codon_band = "delta"  # Spatial
            elif abs_dev < 46.7:
                report.codon_band = "epsilon"  # Resonance (dominant)
            else:
                report.codon_band = "zeta"   # Quantum
        
        # Health indicators derived from colour-frequency mapping
        report.health_indicators = {
            "structural_integrity": float(chroma.val_mean),  # Brightness = structure
            "inflammation_index": float(max(0, (chroma.hue_mean_deg - 310) / 50) 
                                       if chroma.hue_mean_deg > 310 or chroma.hue_mean_deg < 30 
                                       else 0),
            "stagnation_index": float(max(0, 1.0 - chroma.sat_mean - chroma.val_mean)),
            "complexity_score": float(chroma.edge_mean),
            "harmonic_purity": float(1.0 - signature.harmonic_complexity),
            "resonance_alignment": float(1.0 - min(1.0, report.deviation_percent / 5.0)),
            "energy_level": float(signature.total_energy / NUM_HARMONICS),
        }
        
        # Verdict
        if report.deviation_percent < 1.0:
            report.verdict = "RESONANT"  # Well-aligned with 432 Hz
        elif report.deviation_percent < 5.0:
            report.verdict = "DEVIANT"   # Noticeable deviation
        else:
            report.verdict = "CRITICAL"  # Significant misalignment
        
        return report


# ═══════════════════════════════════════════════════════════════════════════════
# FORWARD ENGINE: Frequency Signature → Visual Pattern
# ═══════════════════════════════════════════════════════════════════════════════

class VoidLensForward:
    """
    Generates visual patterns from frequency signatures.
    
    This is the synthesis direction: given a compound's frequency profile,
    generate the cymatics pattern it would produce on a Chladni plate.
    
    Technical method:
    1. Take harmonic amplitudes from compound/signature
    2. Generate 2D standing wave pattern for each harmonic
    3. Combine with appropriate symmetry
    4. Map amplitudes back to colour using the inverse of the extraction mapping:
       - Frequency band → hue
       - Amplitude → brightness
       - Purity → saturation
    """
    
    def __init__(self, resolution: int = 512):
        self.resolution = resolution
        self.baseline_hz = BASE_FREQUENCY
    
    def synthesize_pattern(self, signature: FrequencySignature, 
                          pattern_type: str = "chladni") -> CymaticsPattern:
        """
        Generate a visual pattern from a frequency signature.
        
        Args:
            signature: The frequency profile to visualize
            pattern_type: "chladni" (plate), "cymatics" (fluid), "interference"
            
        Returns:
            CymaticsPattern with the generated image
        """
        if pattern_type == "chladni":
            image = self._generate_chladni(signature)
        elif pattern_type == "cymatics":
            image = self._generate_cymatics(signature)
        else:
            image = self._generate_interference(signature)
        
        # Determine symmetry from dominant harmonic
        symmetry = self._compute_symmetry(signature)
        
        pattern = CymaticsPattern()
        pattern.image = image
        pattern.frequency = signature.dominant_frequency
        pattern.harmonic_order = signature.dominant_harmonic + 1
        pattern.symmetry = symmetry
        pattern.pattern_type = pattern_type
        
        # Count nodes (zero-crossings in the pattern)
        gray = np.mean(image, axis=2)
        mid = np.mean(gray)
        crossings = np.sum(np.abs(np.diff(np.sign(gray - mid), axis=0)) > 0)
        pattern.node_count = int(crossings)
        
        return pattern
    
    def frequency_to_colour(self, frequency_hz: float, amplitude: float = 1.0) -> Tuple[int, int, int]:
        """
        Convert a frequency to its colour representation.
        
        Inverse of the extraction mapping:
        - Frequency band → hue (which colour)
        - Amplitude → value/brightness (how bright)
        """
        # Find which harmonic this frequency represents
        harmonic_n = frequency_hz / self.baseline_hz
        
        # Map harmonic number to hue (inverse of HUE_BANDS)
        if harmonic_n <= 1:
            hue = 0  # Red = fundamental
        elif harmonic_n <= 4:
            hue = 30 + (harmonic_n - 1) / 3 * 30  # Orange range
        elif harmonic_n <= 8:
            hue = 60 + (harmonic_n - 4) / 4 * 60  # Yellow-Green
        elif harmonic_n <= 16:
            hue = 120 + (harmonic_n - 8) / 8 * 60  # Green-Cyan
        elif harmonic_n <= 32:
            hue = 180 + (harmonic_n - 16) / 16 * 60  # Cyan-Blue
        elif harmonic_n <= 48:
            hue = 240 + (harmonic_n - 32) / 16 * 60  # Blue-Violet
        else:
            hue = 300 + min(60, (harmonic_n - 48) / 16 * 60)  # Violet
        
        hue = hue % 360
        saturation = 0.8  # High saturation for pure tones
        value = amplitude
        
        # HSV to RGB
        return self._hsv_to_rgb(hue / 360, saturation, value)
    
    def _generate_chladni(self, signature: FrequencySignature) -> np.ndarray:
        """
        Generate Chladni plate pattern from frequency signature.
        
        Chladni patterns are the nodal lines of vibrating plates:
        f(x,y) = A * [cos(n*pi*x/L)*cos(m*pi*y/L) - cos(m*pi*x/L)*cos(n*pi*y/L)]
        
        Where n,m are the mode numbers derived from the harmonic content.
        """
        res = self.resolution
        image = np.zeros((res, res, 3), dtype=np.float32)
        
        # Create coordinate grid (normalized -1 to 1)
        x = np.linspace(-1, 1, res)
        y = np.linspace(-1, 1, res)
        X, Y = np.meshgrid(x, y)
        
        # Circular plate mask
        R = np.sqrt(X**2 + Y**2)
        plate_mask = R <= 1.0
        
        # Superimpose Chladni modes weighted by harmonic amplitudes
        pattern = np.zeros((res, res))
        
        for h in range(min(NUM_HARMONICS, 16)):  # Use top 16 harmonics
            amp = signature.harmonics[h]
            if amp < 0.01:
                continue
            
            # Mode numbers from harmonic index
            n = h // 4 + 1
            m = h % 4 + 1
            
            # Chladni pattern for this mode
            mode = (np.cos(n * np.pi * X) * np.cos(m * np.pi * Y) -
                   np.cos(m * np.pi * X) * np.cos(n * np.pi * Y))
            
            pattern += amp * mode
        
        # Normalize pattern to 0–1
        if np.max(np.abs(pattern)) > 1e-6:
            pattern = pattern / np.max(np.abs(pattern))
        
        # Map to colours using frequency-to-colour mapping
        # Nodal lines (near zero) = dark
        # Antinodes (peaks) = coloured by dominant frequency
        abs_pattern = np.abs(pattern)
        
        for h in range(min(NUM_HARMONICS, 8)):
            amp = signature.harmonics[h]
            if amp < 0.05:
                continue
            freq = self.baseline_hz * (h + 1)
            r, g, b = self.frequency_to_colour(freq, amp)
            
            # Weight this colour by how much this harmonic contributes
            weight = amp * abs_pattern
            image[:,:,0] += weight * r / 255
            image[:,:,1] += weight * g / 255
            image[:,:,2] += weight * b / 255
        
        # Apply plate mask
        image *= plate_mask[:,:,np.newaxis]
        
        # Normalize and convert to uint8
        max_val = np.max(image)
        if max_val > 0:
            image = image / max_val
        image = (np.clip(image, 0, 1) * 255).astype(np.uint8)
        
        return image
    
    def _generate_cymatics(self, signature: FrequencySignature) -> np.ndarray:
        """
        Generate cymatics (fluid) pattern — concentric rings with frequency-dependent spacing.
        """
        res = self.resolution
        image = np.zeros((res, res, 3), dtype=np.float32)
        
        x = np.linspace(-1, 1, res)
        y = np.linspace(-1, 1, res)
        X, Y = np.meshgrid(x, y)
        R = np.sqrt(X**2 + Y**2)
        theta = np.arctan2(Y, X)
        
        pattern = np.zeros((res, res))
        
        for h in range(min(NUM_HARMONICS, 12)):
            amp = signature.harmonics[h]
            if amp < 0.01:
                continue
            
            # Radial frequency from harmonic number
            radial_freq = (h + 1) * 3
            # Angular frequency for rotational symmetry
            angular_freq = h + 2
            
            # Bessel-like pattern (cymatics in circular container)
            radial = np.cos(radial_freq * np.pi * R)
            angular = np.cos(angular_freq * theta + signature.phases[h])
            
            mode = radial * angular * np.exp(-R * 0.5)  # Damping
            pattern += amp * mode
        
        # Normalize
        if np.max(np.abs(pattern)) > 1e-6:
            pattern = pattern / np.max(np.abs(pattern))
        
        # Colour by frequency content
        abs_pattern = np.abs(pattern)
        for h in range(min(8, NUM_HARMONICS)):
            amp = signature.harmonics[h]
            if amp < 0.05:
                continue
            freq = self.baseline_hz * (h + 1)
            r, g, b = self.frequency_to_colour(freq, amp)
            weight = amp * abs_pattern
            image[:,:,0] += weight * r / 255
            image[:,:,1] += weight * g / 255
            image[:,:,2] += weight * b / 255
        
        max_val = np.max(image)
        if max_val > 0:
            image = image / max_val
        return (np.clip(image, 0, 1) * 255).astype(np.uint8)
    
    def _generate_interference(self, signature: FrequencySignature) -> np.ndarray:
        """Generate interference pattern from multiple frequency sources."""
        res = self.resolution
        image = np.zeros((res, res, 3), dtype=np.float32)
        
        x = np.linspace(-1, 1, res)
        y = np.linspace(-1, 1, res)
        X, Y = np.meshgrid(x, y)
        
        pattern = np.zeros((res, res))
        
        # Place sources at harmonic-determined positions
        num_sources = min(6, int(np.sum(signature.harmonics > 0.1)))
        top_harmonics = np.argsort(signature.harmonics)[-num_sources:]
        
        for i, h in enumerate(top_harmonics):
            amp = signature.harmonics[h]
            if amp < 0.01:
                continue
            
            # Source position on unit circle
            angle = 2 * np.pi * i / num_sources
            sx, sy = 0.5 * np.cos(angle), 0.5 * np.sin(angle)
            
            # Distance from source
            dist = np.sqrt((X - sx)**2 + (Y - sy)**2)
            
            # Wave from this source
            wavelength = 2.0 / (h + 1)
            wave = amp * np.cos(2 * np.pi * dist / wavelength + signature.phases[h])
            wave *= np.exp(-dist * 0.3)  # Attenuation
            
            pattern += wave
        
        # Normalize
        if np.max(np.abs(pattern)) > 1e-6:
            pattern = pattern / np.max(np.abs(pattern))
        
        # Colour
        abs_pattern = (pattern + 1) / 2  # Map -1..1 to 0..1
        for h in top_harmonics:
            amp = signature.harmonics[h]
            freq = self.baseline_hz * (h + 1)
            r, g, b = self.frequency_to_colour(freq, amp)
            image[:,:,0] += abs_pattern * r / 255 * amp
            image[:,:,1] += abs_pattern * g / 255 * amp
            image[:,:,2] += abs_pattern * b / 255 * amp
        
        max_val = np.max(image)
        if max_val > 0:
            image = image / max_val
        return (np.clip(image, 0, 1) * 255).astype(np.uint8)
    
    def _compute_symmetry(self, signature: FrequencySignature) -> int:
        """Determine rotational symmetry from harmonic content."""
        # Dominant harmonic determines base symmetry
        dom = signature.dominant_harmonic + 1
        if dom <= 2:
            return 4  # Square symmetry
        elif dom <= 4:
            return 6  # Hexagonal
        elif dom <= 8:
            return 8  # Octagonal
        else:
            return 12  # Dodecagonal
    
    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV (0-1 range for all) to RGB (0-255)."""
        if s == 0:
            r = g = b = int(v * 255)
            return (r, g, b)
        
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        i = i % 6
        if i == 0: r, g, b = v, t, p
        elif i == 1: r, g, b = q, v, p
        elif i == 2: r, g, b = p, v, t
        elif i == 3: r, g, b = p, q, v
        elif i == 4: r, g, b = t, p, v
        else: r, g, b = v, p, q
        
        return (int(r * 255), int(g * 255), int(b * 255))


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION: Connect to Adriana Deviation Engine & Compound Library
# ═══════════════════════════════════════════════════════════════════════════════

class VoidLens:
    """
    Unified bidirectional lens combining forward and reverse engines.
    
    This is the main interface for Project VOID's image↔frequency conversion.
    """
    
    def __init__(self, baseline_hz: float = BASE_FREQUENCY):
        self.reverse = VoidLensReverse(baseline_hz)
        self.forward = VoidLensForward()
        self.baseline_hz = baseline_hz
    
    def diagnose(self, image: np.ndarray) -> DeviationReport:
        """
        REVERSE DIRECTION: Image → Frequency → Deviation from 432 Hz.
        
        Use for: nail photos, skin images, iris scans, tongue diagnosis,
        cymatics pattern verification, biological surface analysis.
        """
        return self.reverse.analyze_image(image)
    
    def diagnose_file(self, filepath: str) -> DeviationReport:
        """Diagnose from a file path."""
        return self.reverse.analyze_file(filepath)
    
    def synthesize(self, signature: FrequencySignature, 
                   pattern_type: str = "chladni") -> CymaticsPattern:
        """
        FORWARD DIRECTION: Frequency → Visual Pattern.
        
        Use for: visualizing compound stability, generating cymatics predictions,
        creating visual representations of the 30-50 Hz gap.
        """
        return self.forward.synthesize_pattern(signature, pattern_type)
    
    def compound_to_pattern(self, compound: dict, pattern_type: str = "chladni") -> CymaticsPattern:
        """
        Convert a compound from the library to its predicted visual pattern.
        
        Args:
            compound: Dict with keys from compound_library (frequency_hz, bond_strength, etc.)
            pattern_type: "chladni", "cymatics", or "interference"
        """
        sig = self._compound_to_signature(compound)
        return self.synthesize(sig, pattern_type)
    
    def compare_to_baseline(self, image: np.ndarray) -> dict:
        """
        Full comparison: extract image signature and compare to ideal 432 Hz.
        
        Returns a dict with:
        - deviation_hz: how far off from 432 Hz harmonic
        - health_score: 0-1 (1 = perfect resonance)
        - dominant_colour: what the image's frequency "looks like"
        - recommended_frequency: what frequency would bring it back to resonance
        """
        report = self.diagnose(image)
        
        # Recommended corrective frequency
        nearest_n = max(1, round(report.signature.spectral_centroid / self.baseline_hz))
        ideal = nearest_n * self.baseline_hz
        corrective = ideal - report.signature.spectral_centroid + ideal  # Push toward ideal
        
        # Health score (inverse of deviation)
        health_score = max(0, 1.0 - report.deviation_percent / 10.0)
        
        # What colour represents this frequency
        r, g, b = self.forward.frequency_to_colour(
            report.signature.spectral_centroid, 
            report.signature.harmonics[report.signature.dominant_harmonic]
        )
        
        return {
            "deviation_hz": report.deviation_hz,
            "deviation_percent": report.deviation_percent,
            "health_score": health_score,
            "dominant_colour_rgb": (r, g, b),
            "spectral_centroid_hz": report.signature.spectral_centroid,
            "nearest_432_harmonic": int(nearest_n),
            "ideal_frequency_hz": ideal,
            "corrective_frequency_hz": corrective,
            "in_adriana_gap": report.in_adriana_gap,
            "codon_band": report.codon_band,
            "verdict": report.verdict,
            "health_indicators": report.health_indicators,
        }
    
    def _compound_to_signature(self, compound: dict) -> FrequencySignature:
        """Convert a compound dict to a FrequencySignature."""
        sig = FrequencySignature()
        
        freq = compound.get("frequency_hz", BASE_FREQUENCY)
        bond = compound.get("bond_strength", 0.5)
        mass = compound.get("mass_amu", 100)
        
        # Primary harmonic from compound frequency
        primary_n = max(0, min(NUM_HARMONICS - 1, round(freq / self.baseline_hz) - 1))
        
        # Build harmonic profile based on compound properties
        for h in range(NUM_HARMONICS):
            # Distance from primary harmonic
            dist = abs(h - primary_n)
            # Bond strength determines how concentrated the energy is
            sigma = 1.0 + 5.0 * (1.0 - bond)  # Strong bond = narrow peak
            sig.harmonics[h] = np.exp(-0.5 * (dist / sigma) ** 2)
        
        # Mass affects which harmonics are suppressed (heavier = fewer high harmonics)
        mass_factor = np.exp(-np.arange(NUM_HARMONICS) * mass / 5000)
        sig.harmonics *= mass_factor
        
        # Normalize
        max_amp = np.max(sig.harmonics)
        if max_amp > 0:
            sig.harmonics /= max_amp
        
        sig.base_frequency = self.baseline_hz
        sig.dominant_harmonic = primary_n
        sig.spectral_centroid = freq
        sig.total_energy = float(np.sum(sig.harmonics))
        
        # Complexity from geometry
        geometry = compound.get("geometry", "tetrahedral")
        complexity_map = {
            "linear": 0.2, "planar": 0.4, "tetrahedral": 0.5,
            "octahedral": 0.7, "custom": 0.9
        }
        sig.harmonic_complexity = complexity_map.get(geometry, 0.5)
        
        # Deterministic phases from compound name
        name = compound.get("name", "unknown")
        seed = hash(name) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        sig.phases = rng.uniform(0, 2 * np.pi, NUM_HARMONICS)
        
        return sig


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def demonstrate():
    """Run a full demonstration of both directions."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    print("=" * 70)
    print("VOID LENS — Bidirectional Image ↔ Frequency Engine")
    print("=" * 70)
    
    lens = VoidLens()
    
    # ─── FORWARD DEMO: Compound → Visual Pattern ───
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ FORWARD: Frequency Signature → Visual Pattern                    │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    # Test with compounds from the library
    test_compounds = [
        {"name": "Void Carbon Lattice", "frequency_hz": 432, "bond_strength": 0.85, 
         "mass_amu": 12, "geometry": "tetrahedral", "category": "G"},
        {"name": "Harmonic Silicon", "frequency_hz": 864, "bond_strength": 0.75,
         "mass_amu": 28, "geometry": "tetrahedral", "category": "G"},
        {"name": "Chladni Diamond", "frequency_hz": 1728, "bond_strength": 0.95,
         "mass_amu": 12, "geometry": "tetrahedral", "category": "I"},
        {"name": "Quantum-Cymatics Hybrid", "frequency_hz": 4320, "bond_strength": 0.60,
         "mass_amu": 200, "geometry": "custom", "category": "J"},
    ]
    
    from PIL import Image
    
    for compound in test_compounds:
        pattern = lens.compound_to_pattern(compound, "chladni")
        print(f"\n  {compound['name']} ({compound['frequency_hz']} Hz)")
        print(f"    Pattern type: {pattern.pattern_type}")
        print(f"    Symmetry order: {pattern.symmetry}")
        print(f"    Node count: {pattern.node_count}")
        print(f"    Harmonic order: {pattern.harmonic_order}")
        
        # Save pattern
        img = Image.fromarray(pattern.image)
        safe_name = compound['name'].replace(' ', '_').lower()
        outpath = Path(__file__).parent / "lens_output" / f"forward_{safe_name}.png"
        outpath.parent.mkdir(parents=True, exist_ok=True)
        img.save(outpath)
        print(f"    Saved: {outpath}")
    
    # ─── REVERSE DEMO: Generate test image → Extract frequency ───
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ REVERSE: Image → Frequency Signature → 432 Hz Deviation         │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    # Create synthetic test images with known colour properties
    test_images = {
        "warm_red": _make_test_image(hue=10, sat=0.8, val=0.9),    # Should map to fundamental
        "cool_blue": _make_test_image(hue=240, sat=0.7, val=0.6),  # Should map to high harmonics
        "pure_green": _make_test_image(hue=120, sat=0.9, val=0.8), # Should map to mid harmonics
        "gray_complex": _make_test_image(hue=0, sat=0.1, val=0.5, add_noise=True),  # Complex
        "healthy_nail": _make_nail_test_image(healthy=True),
        "unhealthy_nail": _make_nail_test_image(healthy=False),
    }
    
    for name, img in test_images.items():
        report = lens.diagnose(img)
        comparison = lens.compare_to_baseline(img)
        
        print(f"\n  {name}:")
        print(f"    Spectral centroid: {report.signature.spectral_centroid:.1f} Hz")
        print(f"    Deviation from 432 Hz: {report.deviation_hz:+.1f} Hz ({report.deviation_percent:.2f}%)")
        print(f"    Dominant harmonic: {report.signature.dominant_harmonic + 1}× ({report.signature.dominant_frequency:.0f} Hz)")
        print(f"    Harmonic complexity: {report.signature.harmonic_complexity:.3f}")
        print(f"    In Adriana gap: {report.in_adriana_gap}")
        if report.codon_band:
            print(f"    Codon band: {report.codon_band}")
        print(f"    Verdict: {report.verdict}")
        print(f"    Health score: {comparison['health_score']:.2f}")
        print(f"    Corrective frequency: {comparison['corrective_frequency_hz']:.1f} Hz")
        
        # Save test image
        pil_img = Image.fromarray(img)
        outpath = Path(__file__).parent / "lens_output" / f"reverse_{name}.png"
        pil_img.save(outpath)
    
    # ─── ROUNDTRIP DEMO: Compound → Pattern → Re-extract → Compare ───
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ ROUNDTRIP: Compound → Pattern → Re-extract → Verify             │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    compound = test_compounds[0]  # Void Carbon Lattice, 432 Hz
    print(f"\n  Original: {compound['name']} at {compound['frequency_hz']} Hz")
    
    # Forward: compound → pattern
    pattern = lens.compound_to_pattern(compound, "cymatics")
    print(f"  Generated pattern: {pattern.symmetry}-fold symmetry, {pattern.node_count} nodes")
    
    # Reverse: pattern → frequency signature
    report = lens.diagnose(pattern.image)
    print(f"  Re-extracted centroid: {report.signature.spectral_centroid:.1f} Hz")
    print(f"  Deviation from original: {abs(report.signature.spectral_centroid - compound['frequency_hz']):.1f} Hz")
    print(f"  Verdict: {report.verdict}")
    
    # ─── SUMMARY ───
    print("\n" + "=" * 70)
    print("VOID LENS TECHNICAL SUMMARY")
    print("=" * 70)
    print(f"""
  Base frequency:     {BASE_FREQUENCY} Hz
  Harmonics analyzed: {NUM_HARMONICS} (up to {BASE_FREQUENCY * NUM_HARMONICS:.0f} Hz)
  Analysis resolution: {ANALYSIS_SIZE}×{ANALYSIS_SIZE} pixels
  Frame structure:    {NUM_FRAMES} frames × {FRAME_LENGTH} samples
  
  COLOUR → FREQUENCY MAPPING:
    Red (0°)      → 1st harmonic (432 Hz)     [fundamental/structural]
    Orange (30°)  → 2nd-4th (864-1728 Hz)     [low harmonics]
    Yellow (60°)  → 5th-8th (2160-3456 Hz)    [mid-low]
    Green (120°)  → 9th-16th (3888-6912 Hz)   [mid harmonics]
    Blue (240°)   → 17th-32nd (7344-13824 Hz) [high harmonics]
    Violet (300°) → 33rd-64th (14256-27648 Hz)[highest harmonics]
  
  BRIGHTNESS → AMPLITUDE (linear, power 1.5 for contrast)
  SATURATION → BANDWIDTH (high sat = narrow band = pure tone)
  EDGES → COMPLEXITY (many edges = many partials = disorder)
  
  ADRIANA GAP BANDS (30-50 Hz deviation):
    Alpha   (30.0-33.3 Hz): Structural information
    Beta    (33.3-36.7 Hz): Relational information
    Gamma   (36.7-40.0 Hz): Temporal information
    Delta   (40.0-43.3 Hz): Spatial information
    Epsilon (43.3-46.7 Hz): Resonance information (~66%)
    Zeta    (46.7-50.0 Hz): Quantum information
""")
    
    print("  Output saved to: void_engine/lens_output/")
    print("=" * 70)


def _make_test_image(hue: float, sat: float, val: float, 
                     add_noise: bool = False, size: int = 256) -> np.ndarray:
    """Create a synthetic test image with known HSV properties."""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(hue / 360, sat, val)
    img = np.full((size, size, 3), [int(r*255), int(g*255), int(b*255)], dtype=np.uint8)
    
    if add_noise:
        noise = np.random.randint(-30, 30, (size, size, 3))
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Add some structure (gradient)
    gradient = np.linspace(0.7, 1.3, size).reshape(-1, 1, 1)
    img = np.clip(img * gradient, 0, 255).astype(np.uint8)
    
    return img


def _make_nail_test_image(healthy: bool = True, size: int = 256) -> np.ndarray:
    """
    Create a synthetic nail image for testing.
    Healthy nail: uniform pink, smooth, bright
    Unhealthy nail: discoloured, textured, dark spots
    """
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Nail shape (oval)
    y, x = np.ogrid[-size//2:size//2, -size//2:size//2]
    nail_mask = (x**2 / (size*0.35)**2 + y**2 / (size*0.45)**2) <= 1
    
    if healthy:
        # Healthy: uniform pink (hue ~350°, high brightness)
        base_color = np.array([220, 180, 175])  # Warm pink
        img[nail_mask] = base_color
        # Slight gradient for natural look
        gradient = np.linspace(0.9, 1.1, size).reshape(-1, 1)
        for c in range(3):
            channel = img[:,:,c].astype(np.float32)
            channel *= gradient
            img[:,:,c] = np.clip(channel, 0, 255).astype(np.uint8)
    else:
        # Unhealthy: yellowed, dark spots, ridges
        base_color = np.array([200, 190, 130])  # Yellowish
        img[nail_mask] = base_color
        # Add dark spots (fungal indicators)
        rng = np.random.RandomState(42)
        for _ in range(5):
            cx, cy = rng.randint(size//4, 3*size//4, 2)
            radius = rng.randint(5, 15)
            spot_mask = ((x - cx + size//2)**2 + (y - cy + size//2)**2) <= radius**2
            combined = nail_mask & spot_mask
            img[combined] = [80, 70, 40]  # Dark brown spots
        # Add ridges (horizontal lines)
        for ridge_y in range(size//4, 3*size//4, 12):
            ridge_mask = nail_mask & (abs(y + size//2 - ridge_y) < 2)
            img[ridge_mask] = np.clip(img[ridge_mask].astype(np.int16) - 30, 0, 255).astype(np.uint8)
    
    return img


if __name__ == "__main__":
    demonstrate()
