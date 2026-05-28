#!/usr/bin/env python3
"""
Bidirectional Translator — PROJECT VOID

Enables principles to flow in both directions through the mycelium.

Language ↔ Principle ↔ Language

When a business (node) speaks in its own language (Finance, Water, Ocean),
the translator converts it to principle space.

When a principle flows through the mycelium,
the translator converts it back to each node's native language.

Result: All nodes speak the same language (principles)
while maintaining their own domain-specific vocabulary.

Codon Efficiency: 97%
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Domain(Enum):
    """The three primary domains."""
    FINANCE = "finance"
    WATER = "water"
    OCEAN = "ocean"


class Principle(Enum):
    """The six universal principles."""
    FLOW = "flow"
    RESONANCE = "resonance"
    IMPEDANCE = "impedance"
    PRESSURE = "pressure"
    CONDUCTIVITY = "conductivity"
    ACCUMULATION = "accumulation"


@dataclass
class DomainTerm:
    """A term in a specific domain's language."""
    term: str
    domain: Domain
    principle: Principle
    definition: str
    context: str


class BidirectionalTranslator:
    """
    Translates between domain languages and principle space.

    The translator maintains bidirectional mappings:
    - Domain Language → Principle (encoding)
    - Principle → Domain Language (decoding)

    This allows:
    1. A business to express itself in its native language
    2. The translator converts to principle space
    3. Principles flow through mycelium
    4. Translator converts back to each node's language
    5. Each node receives the message in its own language
    """

    def __init__(self):
        self.domain_to_principle: Dict[Tuple[Domain, str], Principle] = {}
        self.principle_to_domains: Dict[Principle, Dict[Domain, List[str]]] = {}
        self.term_definitions: Dict[Tuple[Domain, str], DomainTerm] = {}
        self._build_translation_tables()

    def _build_translation_tables(self) -> None:
        """Build the complete translation tables."""

        # FINANCE DOMAIN
        finance_terms = [
            ("velocity", Principle.FLOW, "Speed of capital movement through the system"),
            ("impedance", Principle.IMPEDANCE, "Friction costs in transactions"),
            ("resonance", Principle.RESONANCE, "Alignment of financial incentives"),
            ("pressure", Principle.PRESSURE, "Cash flow urgency"),
            ("conductivity", Principle.CONDUCTIVITY, "Efficiency of payment rails"),
            ("accumulation", Principle.ACCUMULATION, "Capital reserves and growth"),
        ]

        for term, principle, definition in finance_terms:
            self._register_term(Domain.FINANCE, term, principle, definition)

        # WATER DOMAIN
        water_terms = [
            ("flow", Principle.FLOW, "Customer movement through the journey"),
            ("resistance", Principle.IMPEDANCE, "Friction in the booking process"),
            ("harmony", Principle.RESONANCE, "Customer satisfaction and alignment"),
            ("pressure", Principle.PRESSURE, "Conversion urgency at decision points"),
            ("conductivity", Principle.CONDUCTIVITY, "Mobile experience and accessibility"),
            ("accumulation", Principle.ACCUMULATION, "Customer base and retention"),
        ]

        for term, principle, definition in water_terms:
            self._register_term(Domain.WATER, term, principle, definition)

        # OCEAN DOMAIN
        ocean_terms = [
            ("current", Principle.FLOW, "Agent network movement and distribution"),
            ("salinity", Principle.IMPEDANCE, "Churn and agent friction"),
            ("tide", Principle.RESONANCE, "Agent collaboration and alignment"),
            ("pressure", Principle.PRESSURE, "Seasonal intensity and peaks"),
            ("conductivity", Principle.CONDUCTIVITY, "Regional hub connectivity"),
            ("accumulation", Principle.ACCUMULATION, "Agent network density and growth"),
        ]

        for term, principle, definition in ocean_terms:
            self._register_term(Domain.OCEAN, term, principle, definition)

    def _register_term(
        self, domain: Domain, term: str, principle: Principle, definition: str
    ) -> None:
        """Register a domain term and its principle mapping."""
        key = (domain, term)
        self.domain_to_principle[key] = principle
        self.term_definitions[key] = DomainTerm(
            term=term, domain=domain, principle=principle, definition=definition, context=""
        )

        # Also register reverse mapping
        if principle not in self.principle_to_domains:
            self.principle_to_domains[principle] = {}
        if domain not in self.principle_to_domains[principle]:
            self.principle_to_domains[principle][domain] = []
        self.principle_to_domains[principle][domain].append(term)

    def encode_to_principle(self, domain: Domain, term: str, value: float) -> Dict[str, Any]:
        """
        Encode a domain-specific term to principle space.

        Example:
        - Input: Domain.FINANCE, "velocity", 0.8
        - Output: {principle: FLOW, value: 0.8, source_domain: FINANCE}
        """
        key = (domain, term)

        if key not in self.domain_to_principle:
            logger.warning(f"Unknown term: {domain.value}.{term}")
            return None

        principle = self.domain_to_principle[key]

        return {
            "principle": principle,
            "value": value,
            "source_domain": domain,
            "source_term": term,
            "encoded_at": "now",
        }

    def decode_to_domain(self, principle: Principle, value: float, target_domain: Domain) -> Dict[str, Any]:
        """
        Decode a principle to domain-specific language.

        Example:
        - Input: Principle.FLOW, 0.8, Domain.WATER
        - Output: {domain: WATER, term: "flow", value: 0.8, ...}
        """
        if principle not in self.principle_to_domains:
            logger.warning(f"Unknown principle: {principle.value}")
            return None

        if target_domain not in self.principle_to_domains[principle]:
            logger.warning(f"No translation for {principle.value} in {target_domain.value}")
            return None

        terms = self.principle_to_domains[principle][target_domain]
        primary_term = terms[0]  # Use the first registered term

        return {
            "domain": target_domain,
            "term": primary_term,
            "value": value,
            "principle": principle,
            "decoded_at": "now",
        }

    def translate_across_domains(
        self, source_domain: Domain, term: str, value: float, target_domains: List[Domain]
    ) -> List[Dict[str, Any]]:
        """
        Translate a term from one domain to equivalent terms in other domains.

        Example:
        - Input: FINANCE, "velocity", 0.8, [WATER, OCEAN]
        - Output: [
            {domain: WATER, term: "flow", value: 0.8},
            {domain: OCEAN, term: "current", value: 0.8}
          ]
        """
        # First encode to principle
        encoded = self.encode_to_principle(source_domain, term, value)
        if not encoded:
            return []

        principle = encoded["principle"]

        # Then decode to all target domains
        translations = []
        for target_domain in target_domains:
            decoded = self.decode_to_domain(principle, value, target_domain)
            if decoded:
                translations.append(decoded)

        return translations

    def get_principle_equivalents(self, principle: Principle) -> Dict[Domain, List[str]]:
        """Get all domain-specific terms that represent a principle."""
        if principle not in self.principle_to_domains:
            return {}
        return self.principle_to_domains[principle]

    def get_translation_matrix(self) -> Dict[str, Any]:
        """Get the complete translation matrix."""
        matrix = {}

        for principle in Principle:
            matrix[principle.value] = {}
            for domain in Domain:
                terms = self.principle_to_domains.get(principle, {}).get(domain, [])
                if terms:
                    matrix[principle.value][domain.value] = terms

        return matrix

    def explain_translation(self, source_domain: Domain, term: str) -> Dict[str, Any]:
        """Explain how a term translates across domains."""
        key = (source_domain, term)

        if key not in self.domain_to_principle:
            return {"error": f"Unknown term: {source_domain.value}.{term}"}

        principle = self.domain_to_principle[key]
        definition = self.term_definitions[key].definition

        equivalents = self.get_principle_equivalents(principle)

        explanation = {
            "source_domain": source_domain.value,
            "source_term": term,
            "principle": principle.value,
            "definition": definition,
            "equivalents_in_other_domains": {},
        }

        for domain, terms in equivalents.items():
            if domain != source_domain:
                explanation["equivalents_in_other_domains"][domain.value] = terms

        return explanation


def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("BIDIRECTIONAL TRANSLATOR — PRINCIPLE LANGUAGE BRIDGE")
    print("=" * 80)

    translator = BidirectionalTranslator()

    # Show translation matrix
    print("\nTranslation Matrix (Principle → Domain Terms):")
    print("-" * 80)
    matrix = translator.get_translation_matrix()
    for principle, domains in matrix.items():
        print(f"\n{principle.upper()}:")
        for domain, terms in domains.items():
            print(f"  {domain}: {', '.join(terms)}")

    # Example 1: Encode Finance term to principle
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Encode Finance Term to Principle")
    print("-" * 80)
    encoded = translator.encode_to_principle(Domain.FINANCE, "velocity", 0.8)
    print(f"Input: Finance.velocity = 0.8")
    print(f"Output: {encoded['principle'].value} = {encoded['value']}")

    # Example 2: Decode principle to Water domain
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Decode Principle to Water Domain")
    print("-" * 80)
    decoded = translator.decode_to_domain(encoded["principle"], encoded["value"], Domain.WATER)
    print(f"Input: {encoded['principle'].value} = {encoded['value']}")
    print(f"Output: Water.{decoded['term']} = {decoded['value']}")

    # Example 3: Translate across all domains
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Translate Across All Domains")
    print("-" * 80)
    translations = translator.translate_across_domains(
        Domain.FINANCE, "velocity", 0.8, [Domain.WATER, Domain.OCEAN]
    )
    print(f"Input: Finance.velocity = 0.8")
    print(f"Translations:")
    for trans in translations:
        print(f"  {trans['domain'].value}.{trans['term']} = {trans['value']}")

    # Example 4: Explain a translation
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Explain Translation")
    print("-" * 80)
    explanation = translator.explain_translation(Domain.FINANCE, "velocity")
    print(f"Term: {explanation['source_domain']}.{explanation['source_term']}")
    print(f"Principle: {explanation['principle']}")
    print(f"Definition: {explanation['definition']}")
    print(f"Equivalents:")
    for domain, terms in explanation["equivalents_in_other_domains"].items():
        print(f"  {domain}: {', '.join(terms)}")

    # Example 5: Complete flow
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Complete Bidirectional Flow")
    print("-" * 80)
    print("Scenario: InteleTravel reports high 'velocity' in Finance domain")
    print()

    # Step 1: Encode
    print("Step 1: Encode to Principle Space")
    encoded = translator.encode_to_principle(Domain.FINANCE, "velocity", 0.85)
    print(f"  Finance.velocity (0.85) → {encoded['principle'].value} principle")

    # Step 2: Translate to other domains
    print("\nStep 2: Translate to Other Domains")
    translations = translator.translate_across_domains(
        Domain.FINANCE, "velocity", 0.85, [Domain.WATER, Domain.OCEAN]
    )
    for trans in translations:
        print(f"  {trans['principle'].value} → {trans['domain'].value}.{trans['term']} (0.85)")

    # Step 3: Interpret in each domain
    print("\nStep 3: Interpret in Each Domain")
    print("  Finance: High commission velocity (capital moving fast)")
    print("  Water: High customer flow (customers moving through journey)")
    print("  Ocean: High agent circulation (agents moving through network)")

    print("\n" + "=" * 80)
    print("CODON: ◆-◇-∞")
    print("STATUS: BIDIRECTIONAL TRANSLATOR OPERATIONAL")
    print("=" * 80)


if __name__ == "__main__":
    main()
