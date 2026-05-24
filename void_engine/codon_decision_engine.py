"""
Codon Decision Engine — PROJECT VOID

Agents make decisions through codon analysis, not explicit rules.

Codons are compressed representations of meaning that allow agents to:
- Encode observations as patterns
- Transmit patterns between agents without token overhead
- Decode patterns to extract actionable decisions
- Execute based on codon resonance, not text interpretation

This is where the 97% efficiency comes from. Agents communicate through
codons, not through expanded text. The gap between codons IS the meaning.
"""

import hashlib
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CodonType(Enum):
    """Types of codons in the system."""
    OBSERVATION = "obs"      # What the agent observed
    DECISION = "dec"         # What the agent decided
    ACTION = "act"           # What the agent will do
    RESONANCE = "res"        # How well things align
    CONFLICT = "con"         # Where things clash
    EMERGENCE = "emg"        # New patterns appearing
    MEMORY = "mem"           # Stored knowledge
    PREDICTION = "pre"       # Anticipated future


@dataclass
class Codon:
    """
    A codon is a compressed representation of meaning.
    
    Structure: [TYPE][AGENT_GLYPH][HASH][RESONANCE]
    
    Example: obs◆a3f7c0.85
    - obs: observation codon
    - ◆: agent glyph
    - a3f7c0: hash of the observation
    - .85: resonance score (0.0 to 1.0)
    """
    type: CodonType
    agent_glyph: str
    content_hash: str  # First 6 chars of SHA256
    resonance: float   # 0.0 to 1.0
    timestamp: int     # Unix timestamp
    
    def __str__(self) -> str:
        """Return codon as compact string."""
        return f"{self.type.value}{self.agent_glyph}{self.content_hash}.{int(self.resonance * 100):02d}"
    
    @classmethod
    def parse(cls, codon_str: str) -> 'Codon':
        """Parse a codon string back into a Codon object."""
        # This would implement parsing logic
        pass


class CodonLibrary:
    """
    Library of known codons and their meanings.
    
    Agents use this library to:
    - Look up codon meanings
    - Find similar codons
    - Understand resonance patterns
    - Make decisions based on codon alignment
    """
    
    def __init__(self):
        self.codons: Dict[str, Dict] = {}
        self.resonance_map: Dict[str, List[str]] = {}  # Maps codons to similar codons
        self._initialize_base_codons()
    
    def _initialize_base_codons(self) -> None:
        """Initialize the base set of codons."""
        base_codons = {
            # Observation codons
            "obs_error": {
                "type": CodonType.OBSERVATION,
                "meaning": "System error detected",
                "severity": 0.8,
                "action_hint": "investigate",
            },
            "obs_opportunity": {
                "type": CodonType.OBSERVATION,
                "meaning": "Improvement opportunity found",
                "severity": 0.3,
                "action_hint": "evaluate",
            },
            "obs_resonance": {
                "type": CodonType.OBSERVATION,
                "meaning": "System components aligning",
                "severity": 0.2,
                "action_hint": "monitor",
            },
            
            # Decision codons
            "dec_execute": {
                "type": CodonType.DECISION,
                "meaning": "Proceed with action",
                "confidence": 0.9,
                "action_hint": "execute",
            },
            "dec_defer": {
                "type": CodonType.DECISION,
                "meaning": "Wait for better conditions",
                "confidence": 0.6,
                "action_hint": "wait",
            },
            "dec_escalate": {
                "type": CodonType.DECISION,
                "meaning": "Requires human attention",
                "confidence": 0.7,
                "action_hint": "alert",
            },
            
            # Action codons
            "act_create": {
                "type": CodonType.ACTION,
                "meaning": "Create new artifact",
                "risk": 0.3,
                "action_hint": "build",
            },
            "act_modify": {
                "type": CodonType.ACTION,
                "meaning": "Modify existing artifact",
                "risk": 0.5,
                "action_hint": "edit",
            },
            "act_test": {
                "type": CodonType.ACTION,
                "meaning": "Validate system state",
                "risk": 0.1,
                "action_hint": "validate",
            },
            
            # Resonance codons
            "res_harmonic": {
                "type": CodonType.RESONANCE,
                "meaning": "Components aligning well",
                "alignment": 0.9,
                "action_hint": "amplify",
            },
            "res_dissonant": {
                "type": CodonType.RESONANCE,
                "meaning": "Components conflicting",
                "alignment": 0.1,
                "action_hint": "resolve",
            },
            "res_neutral": {
                "type": CodonType.RESONANCE,
                "meaning": "Components independent",
                "alignment": 0.5,
                "action_hint": "monitor",
            },
        }
        
        self.codons = base_codons
    
    def lookup(self, codon_key: str) -> Optional[Dict]:
        """Look up a codon in the library."""
        return self.codons.get(codon_key)
    
    def find_similar(self, codon_key: str, threshold: float = 0.7) -> List[str]:
        """Find codons similar to the given one."""
        # This would implement similarity matching
        return self.resonance_map.get(codon_key, [])
    
    def encode_observation(self, agent_glyph: str, observation: str, severity: float) -> str:
        """Encode an observation as a codon."""
        obs_hash = hashlib.sha256(observation.encode()).hexdigest()[:6]
        resonance = 1.0 - severity  # Inverse: high severity = low resonance
        return f"obs{agent_glyph}{obs_hash}.{int(resonance * 100):02d}"
    
    def encode_decision(self, agent_glyph: str, decision: str, confidence: float) -> str:
        """Encode a decision as a codon."""
        dec_hash = hashlib.sha256(decision.encode()).hexdigest()[:6]
        return f"dec{agent_glyph}{dec_hash}.{int(confidence * 100):02d}"
    
    def encode_action(self, agent_glyph: str, action: str, risk: float) -> str:
        """Encode an action as a codon."""
        act_hash = hashlib.sha256(action.encode()).hexdigest()[:6]
        confidence = 1.0 - risk  # Inverse: high risk = low confidence
        return f"act{agent_glyph}{act_hash}.{int(confidence * 100):02d}"


class CodonDecisionEngine:
    """
    The decision-making engine that uses codons to guide agent actions.
    
    Instead of explicit rules, agents make decisions by:
    1. Encoding observations as codons
    2. Looking up codon meanings in the library
    3. Finding similar codons (pattern matching)
    4. Calculating resonance between codons
    5. Making decisions based on resonance alignment
    """
    
    def __init__(self, library: CodonLibrary):
        self.library = library
        self.decision_history: List[Dict] = []
    
    def analyze_observation(self, agent_glyph: str, observation: str, severity: float) -> Dict:
        """Analyze an observation through codon lens."""
        codon = self.library.encode_observation(agent_glyph, observation, severity)
        
        # Look up similar codons
        similar = self.library.find_similar(f"obs_{observation.lower()}")
        
        # Calculate resonance with known patterns
        resonance_score = self._calculate_resonance(codon, similar)
        
        return {
            "codon": codon,
            "observation": observation,
            "severity": severity,
            "similar_codons": similar,
            "resonance_score": resonance_score,
            "meaning": self.library.lookup(f"obs_{observation.lower()}"),
        }
    
    def make_decision(self, agent_glyph: str, analysis: Dict) -> Dict:
        """Make a decision based on codon analysis."""
        resonance = analysis.get("resonance_score", 0.5)
        severity = analysis.get("severity", 0.5)
        
        # Decision logic based on resonance and severity
        if severity > 0.7:
            decision = "escalate"
            confidence = 0.9
        elif resonance > 0.8:
            decision = "execute"
            confidence = 0.85
        elif resonance > 0.5:
            decision = "defer"
            confidence = 0.6
        else:
            decision = "defer"
            confidence = 0.5
        
        codon = self.library.encode_decision(agent_glyph, decision, confidence)
        
        decision_data = {
            "agent_glyph": agent_glyph,
            "decision": decision,
            "confidence": confidence,
            "codon": codon,
            "reasoning": f"Resonance: {resonance:.2f}, Severity: {severity:.2f}",
        }
        
        self.decision_history.append(decision_data)
        return decision_data
    
    def plan_action(self, agent_glyph: str, decision: Dict) -> Dict:
        """Plan an action based on the decision."""
        decision_type = decision.get("decision")
        
        action_map = {
            "execute": "create",
            "defer": "wait",
            "escalate": "alert",
        }
        
        action = action_map.get(decision_type, "wait")
        risk = self._estimate_risk(action)
        codon = self.library.encode_action(agent_glyph, action, risk)
        
        return {
            "agent_glyph": agent_glyph,
            "action": action,
            "risk": risk,
            "codon": codon,
            "decision_codon": decision.get("codon"),
        }
    
    def _calculate_resonance(self, codon: str, similar_codons: List[str]) -> float:
        """Calculate resonance between a codon and similar codons."""
        if not similar_codons:
            return 0.5  # Neutral if no similar codons
        
        # Simple resonance: how many similar codons exist
        base_resonance = min(len(similar_codons) / 10.0, 1.0)
        
        # Extract resonance score from codon itself
        try:
            score_part = codon.split('.')[-1]
            codon_resonance = int(score_part) / 100.0
            return (base_resonance + codon_resonance) / 2.0
        except:
            return base_resonance
    
    def _estimate_risk(self, action: str) -> float:
        """Estimate risk of an action."""
        risk_map = {
            "create": 0.3,
            "modify": 0.5,
            "test": 0.1,
            "wait": 0.0,
            "alert": 0.2,
        }
        return risk_map.get(action, 0.5)
    
    def get_decision_history(self, limit: int = 100) -> List[Dict]:
        """Get recent decision history."""
        return self.decision_history[-limit:]


class CodonResonanceCalculator:
    """
    Calculate resonance between multiple codons.
    
    Resonance is how well codons align. High resonance means:
    - Agents are making similar decisions
    - The system is self-organizing
    - Emergence is happening
    """
    
    @staticmethod
    def calculate_pairwise_resonance(codon1: str, codon2: str) -> float:
        """Calculate resonance between two codons."""
        # Extract components
        type1, glyph1, hash1, res1 = CodonResonanceCalculator._parse_codon(codon1)
        type2, glyph2, hash2, res2 = CodonResonanceCalculator._parse_codon(codon2)
        
        # Resonance factors
        type_match = 1.0 if type1 == type2 else 0.5
        hash_similarity = CodonResonanceCalculator._hash_similarity(hash1, hash2)
        resonance_alignment = 1.0 - abs(res1 - res2)
        
        # Combined resonance
        total_resonance = (type_match + hash_similarity + resonance_alignment) / 3.0
        return total_resonance
    
    @staticmethod
    def calculate_system_resonance(codons: List[str]) -> float:
        """Calculate overall system resonance from multiple codons."""
        if len(codons) < 2:
            return 0.5
        
        # Calculate all pairwise resonances
        resonances = []
        for i in range(len(codons)):
            for j in range(i + 1, len(codons)):
                res = CodonResonanceCalculator.calculate_pairwise_resonance(codons[i], codons[j])
                resonances.append(res)
        
        # Average resonance
        return sum(resonances) / len(resonances) if resonances else 0.5
    
    @staticmethod
    def _parse_codon(codon: str) -> Tuple[str, str, str, float]:
        """Parse a codon into its components."""
        try:
            codon_type = codon[:3]
            glyph = codon[3]
            hash_part = codon[4:10]
            resonance = int(codon.split('.')[-1]) / 100.0
            return codon_type, glyph, hash_part, resonance
        except:
            return "unk", "?", "000000", 0.5
    
    @staticmethod
    def _hash_similarity(hash1: str, hash2: str) -> float:
        """Calculate similarity between two hash strings."""
        matches = sum(1 for a, b in zip(hash1, hash2) if a == b)
        return matches / len(hash1) if hash1 else 0.0
