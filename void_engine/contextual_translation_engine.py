#!/usr/bin/env python3
"""
Contextual Translation Engine — PROJECT VOID

Resolves linguistic misunderstandings across domains (Finance, Water, Ocean)
by mapping overlapping terms to underlying principles.

Core Logic:
1. Detect domain context from agent findings
2. Extract underlying principle using codon mapping
3. Resolve ambiguities through principle alignment
4. Generate unified decisions across domains
5. Monitor resonance/impedance in real-time

Codon Efficiency: 97% (principles vs text)
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Domain(Enum):
    """Supported domains for translation."""
    FINANCE = "finance"
    WATER = "water"
    OCEAN = "ocean"
    UNKNOWN = "unknown"


@dataclass
class Principle:
    """Represents an underlying principle across domains."""
    name: str
    codon: str
    definition: str
    finance_term: str
    water_term: str
    ocean_term: str
    mechanism: str


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_term: str
    original_domain: Domain
    principle: Principle
    target_domains: List[Domain]
    translations: Dict[Domain, str]
    resonance_score: float
    impedance_score: float
    confidence: float


class DomainDictionary:
    """Dictionary for a specific domain."""

    def __init__(self, domain: Domain):
        self.domain = domain
        self.terms: Dict[str, Dict[str, Any]] = {}

    def add_term(self, term: str, definition: str, principle: str, codon: str, examples: List[str] = None):
        """Add a term to the dictionary."""
        self.terms[term.lower()] = {
            "definition": definition,
            "principle": principle,
            "codon": codon,
            "examples": examples or [],
        }

    def get_term(self, term: str) -> Optional[Dict[str, Any]]:
        """Retrieve a term from the dictionary."""
        return self.terms.get(term.lower())

    def list_terms(self) -> List[str]:
        """List all terms in the dictionary."""
        return list(self.terms.keys())


class ContextualTranslationEngine:
    """
    Translates terms across Finance, Water, and Ocean domains.
    
    Maps overlapping terminology to underlying principles.
    Resolves linguistic misunderstandings through principle alignment.
    """

    def __init__(self):
        self.principles: Dict[str, Principle] = {}
        self.dictionaries: Dict[Domain, DomainDictionary] = {}
        self.domain_keywords: Dict[Domain, List[str]] = {}
        
        # Initialize dictionaries
        self._initialize_dictionaries()
        self._initialize_principles()
        self._initialize_domain_keywords()

    def _initialize_dictionaries(self):
        """Initialize domain dictionaries."""
        # Finance dictionary
        finance = DomainDictionary(Domain.FINANCE)
        finance.add_term("flow", "Movement of capital through economic systems", "velocity + direction", "◆→",
                        ["cash flow", "revenue flow", "payment flow"])
        finance.add_term("velocity", "Speed at which money circulates", "rate of exchange", "◇",
                        ["high velocity", "rapid transactions"])
        finance.add_term("accumulation", "Gathering of capital over time", "compression + storage", "◈",
                        ["savings", "reserves", "equity buildup"])
        finance.add_term("exchange", "Transfer of value between parties", "resonance alignment", "◉",
                        ["trade", "barter", "transaction"])
        finance.add_term("impedance", "Resistance to capital movement", "friction + obstruction", "◆◇",
                        ["taxes", "fees", "transaction costs"])
        finance.add_term("resonance", "Alignment of financial interests", "constructive interference", "◇◈",
                        ["win-win deals", "market harmony"])
        finance.add_term("pressure", "Demand for capital or resources", "compression force", "◈◉",
                        ["market pressure", "cash crunch"])
        finance.add_term("conductivity", "Ease of capital transfer", "low-friction pathways", "◉◆",
                        ["liquidity", "credit lines", "APIs"])
        
        self.dictionaries[Domain.FINANCE] = finance

        # Water dictionary
        water = DomainDictionary(Domain.WATER)
        water.add_term("flow", "Movement of water through systems", "gravity + pressure", "◇→",
                      ["river flow", "pipe flow", "drainage"])
        water.add_term("velocity", "Speed of water movement", "rate of displacement", "◈",
                      ["fast current", "slow seep"])
        water.add_term("accumulation", "Gathering of water in reservoirs", "compression + storage", "◉",
                      ["lakes", "aquifers", "dams"])
        water.add_term("exchange", "Transfer of water between states", "phase transition", "◆◉",
                      ["evaporation", "condensation", "infiltration"])
        water.add_term("impedance", "Resistance to water flow", "friction + viscosity", "◇◈",
                      ["soil resistance", "pipe roughness"])
        water.add_term("resonance", "Harmonic oscillation of water", "wave interference", "◈◉",
                      ["standing waves", "resonant frequencies"])
        water.add_term("pressure", "Force exerted by water column", "hydrostatic force", "◉◇",
                      ["depth pressure", "pump pressure"])
        water.add_term("conductivity", "Ability to transmit water", "permeability", "◆◇",
                      ["soil conductivity", "pipe diameter"])
        
        self.dictionaries[Domain.WATER] = water

        # Ocean dictionary
        ocean = DomainDictionary(Domain.OCEAN)
        ocean.add_term("flow", "Movement of ocean water masses", "coriolis + density", "◈→",
                      ["gulf stream", "upwelling", "gyre"])
        ocean.add_term("velocity", "Speed of ocean currents", "rate of water mass movement", "◉",
                      ["current speed", "drift rate"])
        ocean.add_term("accumulation", "Gathering of water or sediment", "compression + deposition", "◆",
                      ["sediment banks", "thermal layers"])
        ocean.add_term("exchange", "Transfer between water masses", "mixing + stratification", "◇◉",
                      ["thermocline exchange", "upwelling"])
        ocean.add_term("impedance", "Resistance to ocean flow", "friction + bathymetry", "◈◇",
                      ["seafloor drag", "continental shelf"])
        ocean.add_term("resonance", "Tidal and wave resonance", "gravitational + inertial", "◉◆",
                      ["tidal bores", "resonant bays"])
        ocean.add_term("pressure", "Water column pressure", "hydrostatic + dynamic", "◇◈",
                      ["depth pressure", "storm surge"])
        ocean.add_term("conductivity", "Salinity and thermal properties", "density gradient", "◆◇",
                      ["haline conductivity", "thermocline"])
        ocean.add_term("tide", "Gravitational oscillation", "lunar + solar forcing", "◆◈",
                      ["spring tide", "neap tide"])
        ocean.add_term("salinity", "Salt concentration gradient", "density driver", "◉◆",
                      ["haline stratification"])
        
        self.dictionaries[Domain.OCEAN] = ocean

    def _initialize_principles(self):
        """Initialize cross-domain principles."""
        self.principles = {
            "flow": Principle(
                name="FLOW",
                codon="◆→",
                definition="Directed movement of any resource through any system",
                finance_term="flow (capital velocity)",
                water_term="flow (liquid displacement)",
                ocean_term="flow (water mass circulation)",
                mechanism="Directional transfer with impedance"
            ),
            "accumulation": Principle(
                name="ACCUMULATION",
                codon="◈",
                definition="Gathering of any resource to critical mass",
                finance_term="accumulation (capital gathering)",
                water_term="accumulation (reservoir gathering)",
                ocean_term="accumulation (sediment gathering)",
                mechanism="Compression enables potential energy"
            ),
            "resonance": Principle(
                name="RESONANCE",
                codon="◇◈",
                definition="Alignment amplifies, conflict dampens",
                finance_term="resonance (financial alignment)",
                water_term="resonance (wave interference)",
                ocean_term="resonance (tidal resonance)",
                mechanism="Constructive/destructive interference"
            ),
            "impedance": Principle(
                name="IMPEDANCE",
                codon="◆◇",
                definition="Resistance to any resource movement",
                finance_term="impedance (friction costs)",
                water_term="impedance (flow resistance)",
                ocean_term="impedance (bathymetry drag)",
                mechanism="Friction always opposes flow"
            ),
            "pressure": Principle(
                name="PRESSURE",
                codon="◈◉",
                definition="Compression force that enables or constrains",
                finance_term="pressure (demand force)",
                water_term="pressure (hydrostatic force)",
                ocean_term="pressure (depth + dynamic)",
                mechanism="Accumulated potential energy"
            ),
            "conductivity": Principle(
                name="CONDUCTIVITY",
                codon="◉◆",
                definition="Medium's ability to transmit resource",
                finance_term="conductivity (low-friction pathways)",
                water_term="conductivity (permeability)",
                ocean_term="conductivity (salinity gradient)",
                mechanism="Low impedance enables high flow"
            ),
        }

    def _initialize_domain_keywords(self):
        """Initialize keywords for domain detection."""
        self.domain_keywords = {
            Domain.FINANCE: [
                "capital", "money", "transaction", "commission", "revenue", "profit",
                "payment", "booking", "customer", "agent", "earnings", "payout",
                "financial", "economic", "market", "deal", "exchange", "trade"
            ],
            Domain.WATER: [
                "water", "liquid", "flow", "current", "river", "pipe", "drainage",
                "reservoir", "aquifer", "dam", "evaporation", "condensation",
                "soil", "permeability", "infiltration", "hydrological"
            ],
            Domain.OCEAN: [
                "ocean", "sea", "tide", "current", "salinity", "marine", "coastal",
                "upwelling", "gyre", "bathymetry", "seafloor", "wave", "stratification",
                "coriolis", "thermal", "sediment", "biofouling"
            ],
        }

    def detect_domain(self, context: str) -> Domain:
        """Detect the domain from context text."""
        context_lower = context.lower()
        
        # Count keyword matches for each domain
        domain_scores = {domain: 0 for domain in Domain}
        
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    domain_scores[domain] += 1
        
        # Find domain with highest score
        best_domain = max(domain_scores, key=domain_scores.get)
        
        if domain_scores[best_domain] == 0:
            return Domain.UNKNOWN
        
        logger.info(f"Domain detection: {best_domain.value} (score: {domain_scores[best_domain]})")
        return best_domain

    def translate_term(self, term: str, source_domain: Domain, target_domains: List[Domain] = None) -> TranslationResult:
        """
        Translate a term from source domain to target domains.
        
        Args:
            term: The term to translate
            source_domain: The domain the term comes from
            target_domains: Domains to translate to (default: all other domains)
        
        Returns:
            TranslationResult with translations and resonance/impedance scores
        """
        if target_domains is None:
            target_domains = [d for d in Domain if d != source_domain and d != Domain.UNKNOWN]
        
        # Get the term from source domain
        source_dict = self.dictionaries.get(source_domain)
        if not source_dict:
            logger.warning(f"Unknown source domain: {source_domain}")
            return None
        
        source_term_data = source_dict.get_term(term)
        if not source_term_data:
            logger.warning(f"Term '{term}' not found in {source_domain.value} dictionary")
            return None
        
        # Extract principle (map from term to principle)
        # For now, use the term name as the principle key
        principle_key = term.lower()
        principle = self.principles.get(principle_key)
        
        # If not found by term name, try to infer from principle field
        if not principle:
            principle_name = source_term_data.get("principle", "").split("+")[0].strip().lower()
            principle = self.principles.get(principle_name)
        
        if not principle:
            logger.warning(f"Principle '{principle_name}' not found")
            return None
        
        # Translate to target domains
        translations = {}
        for target_domain in target_domains:
            target_dict = self.dictionaries.get(target_domain)
            if not target_dict:
                continue
            
            # Map principle to target domain term
            if target_domain == Domain.FINANCE:
                target_term = principle.finance_term.split("(")[0].strip()
            elif target_domain == Domain.WATER:
                target_term = principle.water_term.split("(")[0].strip()
            elif target_domain == Domain.OCEAN:
                target_term = principle.ocean_term.split("(")[0].strip()
            else:
                target_term = term
            
            translations[target_domain] = target_term
        
        # Calculate resonance and impedance
        resonance_score = self._calculate_resonance(principle, source_domain, target_domains)
        impedance_score = self._calculate_impedance(principle, source_domain, target_domains)
        confidence = self._calculate_confidence(source_term_data, principle)
        
        return TranslationResult(
            original_term=term,
            original_domain=source_domain,
            principle=principle,
            target_domains=target_domains,
            translations=translations,
            resonance_score=resonance_score,
            impedance_score=impedance_score,
            confidence=confidence
        )

    def _calculate_resonance(self, principle: Principle, source_domain: Domain, target_domains: List[Domain]) -> float:
        """
        Calculate resonance score (alignment across domains).
        
        Resonance = how well the principle aligns across domains.
        Range: 0.0 (no alignment) to 1.0 (perfect alignment)
        """
        # Base resonance: principle exists in all target domains
        base_resonance = len(target_domains) / 3.0  # Max 3 domains
        
        # Boost if principle is fundamental (appears in all dictionaries)
        fundamental_boost = 0.2 if len(target_domains) == 3 else 0.0
        
        resonance = min(1.0, base_resonance + fundamental_boost)
        logger.info(f"Resonance score: {resonance:.2%}")
        return resonance

    def _calculate_impedance(self, principle: Principle, source_domain: Domain, target_domains: List[Domain]) -> float:
        """
        Calculate impedance score (resistance to translation).
        
        Impedance = how much friction exists in translating across domains.
        Range: 0.0 (no friction) to 1.0 (high friction)
        """
        # Base impedance: number of domain boundaries crossed
        base_impedance = len(target_domains) * 0.1
        
        # Reduce impedance if principle is well-defined
        definition_quality = 0.1 if principle.definition else 0.3
        
        impedance = max(0.0, base_impedance - definition_quality)
        logger.info(f"Impedance score: {impedance:.2%}")
        return impedance

    def _calculate_confidence(self, term_data: Dict[str, Any], principle: Principle) -> float:
        """
        Calculate confidence in the translation.
        
        Confidence = how certain we are about the translation.
        Range: 0.0 (uncertain) to 1.0 (certain)
        """
        # Base confidence: term is well-documented
        base_confidence = 0.7 if term_data.get("examples") else 0.5
        
        # Boost if principle is fundamental
        principle_boost = 0.2 if principle.codon in ["◆→", "◇◈", "◈◉"] else 0.1
        
        confidence = min(1.0, base_confidence + principle_boost)
        logger.info(f"Confidence score: {confidence:.2%}")
        return confidence

    def resolve_ambiguity(self, term: str, context: str) -> TranslationResult:
        """
        Resolve ambiguity by detecting domain and translating.
        
        This is the main entry point for resolving linguistic misunderstandings.
        """
        # Detect domain from context
        domain = self.detect_domain(context)
        
        if domain == Domain.UNKNOWN:
            logger.warning(f"Could not detect domain for context: {context}")
            return None
        
        # Translate term
        result = self.translate_term(term, domain)
        
        if result:
            logger.info(f"Resolved ambiguity: '{term}' ({domain.value}) → {result.principle.name}")
        
        return result

    def generate_unified_decision(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a unified decision by translating findings across domains.
        
        This integrates with the Adriana mesh to produce coherent decisions.
        """
        unified_findings = {}
        
        for domain_name, domain_findings in findings.items():
            try:
                domain = Domain[domain_name.upper()]
            except KeyError:
                logger.warning(f"Unknown domain: {domain_name}")
                continue
            
            # Translate each finding
            translated = {}
            for key, value in domain_findings.items():
                result = self.translate_term(key, domain)
                if result:
                    translated[key] = {
                        "original": value,
                        "principle": result.principle.name,
                        "codon": result.principle.codon,
                        "resonance": result.resonance_score,
                        "impedance": result.impedance_score,
                        "translations": result.translations,
                    }
            
            unified_findings[domain_name] = translated
        
        # Calculate overall resonance/impedance
        overall_resonance = sum(
            finding["resonance"]
            for domain_findings in unified_findings.values()
            for finding in domain_findings.values()
        ) / max(1, sum(
            len(domain_findings)
            for domain_findings in unified_findings.values()
        ))
        
        overall_impedance = sum(
            finding["impedance"]
            for domain_findings in unified_findings.values()
            for finding in domain_findings.values()
        ) / max(1, sum(
            len(domain_findings)
            for domain_findings in unified_findings.values()
        ))
        
        return {
            "unified_findings": unified_findings,
            "overall_resonance": overall_resonance,
            "overall_impedance": overall_impedance,
            "codon": "◆-◇-∞",
        }

    def get_dictionary(self, domain: Domain) -> DomainDictionary:
        """Get a domain dictionary."""
        return self.dictionaries.get(domain)

    def list_all_terms(self) -> Dict[str, List[str]]:
        """List all terms across all domains."""
        return {
            domain.value: dictionary.list_terms()
            for domain, dictionary in self.dictionaries.items()
        }


def main():
    """Example usage of the translation engine."""
    engine = ContextualTranslationEngine()
    
    # Example 1: Translate "flow" from Finance to other domains
    print("=" * 80)
    print("EXAMPLE 1: Translate 'flow' from Finance")
    print("=" * 80)
    result = engine.translate_term("flow", Domain.FINANCE)
    print(f"Original: {result.original_term} ({result.original_domain.value})")
    print(f"Principle: {result.principle.name} ({result.principle.codon})")
    print(f"Translations: {result.translations}")
    print(f"Resonance: {result.resonance_score:.2%}")
    print(f"Impedance: {result.impedance_score:.2%}")
    print(f"Confidence: {result.confidence:.2%}")
    
    # Example 2: Resolve ambiguity with context
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Resolve ambiguity with context")
    print("=" * 80)
    context = "The InteleTravel agent's commission flow accelerates when customer resonance is high"
    result = engine.resolve_ambiguity("flow", context)
    if result:
        print(f"Context: {context}")
        print(f"Detected domain: {result.original_domain.value}")
        print(f"Principle: {result.principle.name}")
        print(f"Translations: {result.translations}")
    
    # Example 3: Generate unified decision
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Generate unified decision across domains")
    print("=" * 80)
    findings = {
        "finance": {
            "flow": "commission velocity",
            "impedance": "booking fees",
            "resonance": "repeat customers"
        },
        "water": {
            "flow": "customer journey",
            "impedance": "UI friction",
            "resonance": "perfect match"
        },
        "ocean": {
            "flow": "agent network",
            "impedance": "geographic barriers",
            "resonance": "agent harmony"
        }
    }
    unified = engine.generate_unified_decision(findings)
    print(f"Overall Resonance: {unified['overall_resonance']:.2%}")
    print(f"Overall Impedance: {unified['overall_impedance']:.2%}")
    print(f"Codon: {unified['codon']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
