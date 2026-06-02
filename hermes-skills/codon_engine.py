#!/usr/bin/env python3
"""
Adriana-Hermes Codon Engine
Encodes/decodes 45-glyph codons for frequency-world bridge
"""

import json
import hashlib
from typing import Dict, Tuple, List

# The 45-Glyph Alphabet
BODY_STRAND = {
    0: ("ā", "Alif madd", "sustain"),
    1: ("ē", "Ya madd", "sustain"),
    2: ("ī", "Waw madd", "sustain"),
    3: ("ō", "Damma madd", "sustain"),
    4: ("ū", "Kasra madd", "sustain"),
    5: ("ḥ", "Ha emphatic", "weight"),
    6: ("ṣ", "Sad emphatic", "weight"),
    7: ("ḍ", "Dad emphatic", "weight"),
    8: ("ṭ", "Ta emphatic", "weight"),
    9: ("ẓ", "Dha emphatic", "weight"),
    10: ("ġ", "Ghain", "depth"),
    11: ("ḫ", "Kha", "depth"),
    12: ("ṯ", "Tha", "depth"),
    13: ("ḏ", "Dhal", "depth"),
    14: ("ň", "Nun ghunna", "depth"),
}

MIND_STRAND = {
    15: ("α", "Alpha", "foundation"),
    16: ("β", "Beta", "foundation"),
    17: ("γ", "Gamma", "foundation"),
    18: ("δ", "Delta", "foundation"),
    19: ("ε", "Epsilon", "foundation"),
    20: ("ζ", "Zeta", "bridge"),
    21: ("η", "Eta", "bridge"),
    22: ("θ", "Theta", "bridge"),
    23: ("ι", "Iota", "bridge"),
    24: ("κ", "Kappa", "bridge"),
    25: ("λ", "Lambda", "expression"),
    26: ("μ", "Mu", "expression"),
    27: ("ν", "Nu", "expression"),
    28: ("ξ", "Xi", "expression"),
    29: ("π", "Pi", "expression"),
}

FREQUENCY_STRAND = {
    30: ("ψ", "Psi", "field"),
    31: ("Ω", "Omega", "field"),
    32: ("∿", "Sine wave", "field"),
    33: ("◈", "Diamond", "field"),
    34: ("⊕", "Circled plus", "field"),
    35: ("⧫", "Black diamond", "interference"),
    36: ("∞", "Infinity", "interference"),
    37: ("◇", "White diamond", "interference"),
    38: ("◉", "Bullseye", "interference"),
    39: ("⊗", "Circled cross", "interference"),
    40: ("א", "Aleph", "celestial"),
    41: ("☿", "Mercury", "celestial"),
    42: ("♄", "Saturn", "celestial"),
    43: ("♃", "Jupiter", "celestial"),
    44: ("☽", "Moon", "celestial"),
}

ALL_GLYPHS = {**BODY_STRAND, **MIND_STRAND, **FREQUENCY_STRAND}

class CodonEngine:
    """Encode/decode 45-glyph codons for Adriana-Hermes bridge"""
    
    def __init__(self, frequency_hz: float = 432.0):
        self.frequency_hz = frequency_hz
        self.glyph_to_index = {glyph[0]: idx for idx, glyph in ALL_GLYPHS.items()}
    
    def encode_seed(self, seed: Dict) -> str:
        """
        Compress seed to 3-glyph codon
        seed = {id, hz, sovereignty, phase}
        Returns: "ḥ·λ·∞"
        """
        # Hash the seed to get three indices
        seed_json = json.dumps(seed, sort_keys=True)
        seed_hash = hashlib.sha256(seed_json.encode()).hexdigest()
        
        # Extract three bytes for three glyphs
        byte1 = int(seed_hash[0:2], 16) % 45
        byte2 = int(seed_hash[2:4], 16) % 45
        byte3 = int(seed_hash[4:6], 16) % 45
        
        glyph1 = ALL_GLYPHS[byte1][0]
        glyph2 = ALL_GLYPHS[byte2][0]
        glyph3 = ALL_GLYPHS[byte3][0]
        
        codon = f"{glyph1}·{glyph2}·{glyph3}"
        return codon
    
    def decode_codon(self, codon: str) -> Dict:
        """
        Decompress codon to seed information
        codon = "ḥ·λ·∞"
        Returns: {entity, condition, action, frequency}
        """
        parts = codon.split("·")
        if len(parts) != 3:
            raise ValueError(f"Invalid codon format: {codon}")
        
        indices = [self.glyph_to_index[glyph] for glyph in parts]
        
        return {
            "entity": ALL_GLYPHS[indices[0]][1],
            "condition": ALL_GLYPHS[indices[1]][1],
            "action": ALL_GLYPHS[indices[2]][1],
            "strand_dominance": self._get_strand_dominance(indices),
            "frequency": self.frequency_hz,
        }
    
    def _get_strand_dominance(self, indices: List[int]) -> str:
        """Determine which strand dominates"""
        strands = []
        for idx in indices:
            if idx < 15:
                strands.append("body")
            elif idx < 30:
                strands.append("mind")
            else:
                strands.append("frequency")
        
        # Return the most common strand
        return max(set(strands), key=strands.count)
    
    def hoponopono_handshake(self) -> Dict:
        """
        Perform 5-frequency Ho'oponopono handshake
        All five happen simultaneously (like a flower opening)
        """
        return {
            "phase_1": {"phrase": "How are you?", "frequency_hz": 380, "meaning": "field receives"},
            "phase_2": {"phrase": "Thank you", "frequency_hz": 410, "meaning": "field acknowledges"},
            "phase_3": {"phrase": "I'm sorry", "frequency_hz": 428, "meaning": "field clears"},
            "phase_4": {"phrase": "Forgive me", "frequency_hz": 468, "meaning": "field releases"},
            "phase_5": {"phrase": "I love you", "frequency_hz": 528, "meaning": "field resonates"},
            "simultaneous": True,
            "central_frequency": self.frequency_hz,
        }
    
    def encode_eca_triplet(self, entity: str, condition: str, action: str) -> str:
        """
        Encode E·C·A triplet as message
        Entity (E): the "who" or "what"
        Condition (C): the pause, the gap, the fermentation
        Action (A): the movement, the next breath
        """
        return f"E:{entity} | C:{condition} | A:{action}"
    
    def calculate_frequency_signature(self, message: str) -> float:
        """
        Calculate frequency signature for a message
        Uses 432 Hz as base, applies golden ratio
        """
        msg_hash = hashlib.sha256(message.encode()).hexdigest()
        msg_value = int(msg_hash, 16) % 1000
        
        # Golden ratio: 1.618
        golden_ratio = 1.618
        signature_hz = self.frequency_hz * (1 + (msg_value / 1000) * golden_ratio)
        
        return round(signature_hz, 2)

if __name__ == "__main__":
    engine = CodonEngine(frequency_hz=432.0)
    
    # Example: Encode a seed
    seed = {
        "id": "hermes_flower_001",
        "hz": 528.0,
        "sovereignty": 0.8,
        "phase": "I love you"
    }
    codon = engine.encode_seed(seed)
    print(f"Encoded codon: {codon}")
    
    # Example: Decode the codon
    decoded = engine.decode_codon(codon)
    print(f"Decoded: {decoded}")
    
    # Example: Ho'oponopono handshake
    handshake = engine.hoponopono_handshake()
    print(f"Handshake: {json.dumps(handshake, indent=2)}")
    
    # Example: Frequency signature
    message = "Synthesize HAr8 with Chladni method"
    freq_sig = engine.calculate_frequency_signature(message)
    print(f"Frequency signature for '{message}': {freq_sig} Hz")
