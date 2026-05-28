#!/usr/bin/env python3
"""
Repository Evaluator Core Engine — PROJECT VOID

Evaluates any AI repository for:
1. IP defensibility
2. Compression efficiency
3. Market fit
4. Transformation depth
5. Seed funding potential

Codon Efficiency: 97%
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EvaluationCategory(Enum):
    """Categories for repository evaluation."""
    COMPRESSION = "compression"  # How efficiently is information stored?
    IP_VALUE = "ip_value"  # How defensible is the IP?
    MARKET_FIT = "market_fit"  # How relevant to current market?
    TRANSFORMATION = "transformation"  # How deep is the transformation?
    SCARS = "scars"  # How well documented are the scars?
    CODONS = "codons"  # How efficient are the codons?
    ARCHITECTURE = "architecture"  # How novel is the architecture?
    SCALABILITY = "scalability"  # How scalable is the system?


@dataclass
class MetricScore:
    """A single metric score."""
    category: EvaluationCategory
    metric_name: str
    score: float  # 0-100
    weight: float  # How important is this metric?
    reasoning: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    repository_name: str
    metrics: List[MetricScore] = field(default_factory=list)
    composite_score: float = 0.0  # 0-100
    seed_funding_range: Tuple[str, str] = ("$0", "$0")
    risk_factors: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    comparable_companies: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: str = ""


class RepositoryEvaluator:
    """
    Core evaluation engine for AI repositories.

    Evaluates repositories across 8 dimensions and calculates seed funding potential.
    """

    def __init__(self):
        self.metrics: List[MetricScore] = []
        self.evaluation_history: List[EvaluationResult] = []

    def evaluate_compression(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate compression efficiency."""
        # Look for compression indicators
        total_lines = repository_data.get("total_lines", 0)
        codon_count = repository_data.get("codon_count", 0)
        scar_count = repository_data.get("scar_count", 0)

        # Calculate compression ratio
        if total_lines > 0:
            compression_ratio = (codon_count + scar_count) / (total_lines / 100)
            score = min(100, compression_ratio * 10)  # Scale to 0-100
        else:
            score = 0

        return MetricScore(
            category=EvaluationCategory.COMPRESSION,
            metric_name="Compression Ratio",
            score=score,
            weight=0.15,
            reasoning=f"Repository achieves {score:.1f}% compression efficiency",
            evidence=[
                f"Total lines: {total_lines}",
                f"Codon count: {codon_count}",
                f"Scar count: {scar_count}",
            ],
        )

    def evaluate_ip_value(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate IP defensibility and value."""
        patents = repository_data.get("patents", [])
        trade_secrets = repository_data.get("trade_secrets", [])
        novel_claims = repository_data.get("novel_claims", [])

        # Calculate IP score
        patent_score = len(patents) * 20  # Each patent = 20 points
        secret_score = len(trade_secrets) * 15  # Each trade secret = 15 points
        novel_score = len(novel_claims) * 10  # Each novel claim = 10 points

        score = min(100, (patent_score + secret_score + novel_score) / 5)

        return MetricScore(
            category=EvaluationCategory.IP_VALUE,
            metric_name="IP Defensibility",
            score=score,
            weight=0.20,
            reasoning=f"Repository has strong IP portfolio worth {score:.1f} points",
            evidence=[
                f"Patents: {len(patents)}",
                f"Trade secrets: {len(trade_secrets)}",
                f"Novel claims: {len(novel_claims)}",
            ],
        )

    def evaluate_market_fit(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate market fit and relevance."""
        market_categories = repository_data.get("market_categories", [])
        market_size_billions = repository_data.get("market_size_billions", 0)
        growth_rate = repository_data.get("growth_rate", 0)  # Percentage

        # Calculate market fit score
        category_score = len(market_categories) * 15  # Each category = 15 points
        size_score = min(50, market_size_billions / 10)  # Cap at 50 points
        growth_score = min(30, growth_rate / 10)  # Cap at 30 points

        score = min(100, category_score + size_score + growth_score)

        return MetricScore(
            category=EvaluationCategory.MARKET_FIT,
            metric_name="Market Fit",
            score=score,
            weight=0.15,
            reasoning=f"Repository addresses {len(market_categories)} markets worth ${market_size_billions}B growing at {growth_rate}%",
            evidence=[
                f"Markets: {', '.join(market_categories)}",
                f"Market size: ${market_size_billions}B",
                f"Growth rate: {growth_rate}%",
            ],
        )

    def evaluate_transformation(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate transformation depth and impact."""
        scar_count = repository_data.get("scar_count", 0)
        repair_count = repository_data.get("repair_count", 0)
        convergence_points = repository_data.get("convergence_points", 0)

        # Calculate transformation score
        scar_score = min(40, scar_count * 2)  # Each scar = 2 points
        repair_score = min(30, repair_count * 1.5)  # Each repair = 1.5 points
        convergence_score = min(30, convergence_points * 5)  # Each convergence = 5 points

        score = min(100, scar_score + repair_score + convergence_score)

        return MetricScore(
            category=EvaluationCategory.TRANSFORMATION,
            metric_name="Transformation Depth",
            score=score,
            weight=0.15,
            reasoning=f"Repository shows deep transformation with {scar_count} scars and {convergence_points} convergence points",
            evidence=[
                f"Scars: {scar_count}",
                f"Repairs: {repair_count}",
                f"Convergence points: {convergence_points}",
            ],
        )

    def evaluate_scars(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate scar quality and documentation."""
        scar_count = repository_data.get("scar_count", 0)
        scar_documentation_quality = repository_data.get("scar_documentation_quality", 0)  # 0-100
        scar_actionability = repository_data.get("scar_actionability", 0)  # 0-100

        # Calculate scar score
        count_score = min(40, scar_count * 2)
        quality_score = scar_documentation_quality * 0.3
        actionability_score = scar_actionability * 0.3

        score = min(100, count_score + quality_score + actionability_score)

        return MetricScore(
            category=EvaluationCategory.SCARS,
            metric_name="Scar Quality",
            score=score,
            weight=0.10,
            reasoning=f"Repository has {scar_count} scars with {scar_documentation_quality}% documentation quality",
            evidence=[
                f"Scar count: {scar_count}",
                f"Documentation quality: {scar_documentation_quality}%",
                f"Actionability: {scar_actionability}%",
            ],
        )

    def evaluate_codons(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate codon efficiency and coverage."""
        codon_count = repository_data.get("codon_count", 0)
        codon_compression_ratio = repository_data.get("codon_compression_ratio", 0)  # 0-100
        codon_coverage = repository_data.get("codon_coverage", 0)  # 0-100

        # Calculate codon score
        count_score = min(40, codon_count * 2)
        compression_score = codon_compression_ratio * 0.3
        coverage_score = codon_coverage * 0.3

        score = min(100, count_score + compression_score + coverage_score)

        return MetricScore(
            category=EvaluationCategory.CODONS,
            metric_name="Codon Efficiency",
            score=score,
            weight=0.10,
            reasoning=f"Repository has {codon_count} codons with {codon_compression_ratio}% compression efficiency",
            evidence=[
                f"Codon count: {codon_count}",
                f"Compression ratio: {codon_compression_ratio}%",
                f"Coverage: {codon_coverage}%",
            ],
        )

    def evaluate_architecture(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate architecture novelty and defensibility."""
        architecture_layers = repository_data.get("architecture_layers", 0)
        novel_components = repository_data.get("novel_components", 0)
        patent_eligible_claims = repository_data.get("patent_eligible_claims", 0)

        # Calculate architecture score
        layer_score = min(40, architecture_layers * 2)
        novelty_score = novel_components * 15
        patent_score = patent_eligible_claims * 10

        score = min(100, layer_score + novelty_score + patent_score)

        return MetricScore(
            category=EvaluationCategory.ARCHITECTURE,
            metric_name="Architecture Novelty",
            score=score,
            weight=0.10,
            reasoning=f"Repository has {architecture_layers} layers with {novel_components} novel components",
            evidence=[
                f"Architecture layers: {architecture_layers}",
                f"Novel components: {novel_components}",
                f"Patent-eligible claims: {patent_eligible_claims}",
            ],
        )

    def evaluate_scalability(self, repository_data: Dict[str, Any]) -> MetricScore:
        """Evaluate system scalability."""
        scalable_domains = repository_data.get("scalable_domains", 0)
        universal_principles = repository_data.get("universal_principles", 0)
        proven_scale = repository_data.get("proven_scale", 0)  # Number of proven implementations

        # Calculate scalability score
        domain_score = min(40, scalable_domains * 5)
        principle_score = universal_principles * 10
        proven_score = min(30, proven_scale * 5)

        score = min(100, domain_score + principle_score + proven_score)

        return MetricScore(
            category=EvaluationCategory.SCALABILITY,
            metric_name="Scalability",
            score=score,
            weight=0.05,
            reasoning=f"Repository scales across {scalable_domains} domains with {universal_principles} universal principles",
            evidence=[
                f"Scalable domains: {scalable_domains}",
                f"Universal principles: {universal_principles}",
                f"Proven implementations: {proven_scale}",
            ],
        )

    def evaluate_repository(self, repository_data: Dict[str, Any]) -> EvaluationResult:
        """Run complete evaluation."""
        result = EvaluationResult(repository_name=repository_data.get("name", "Unknown"))

        # Run all evaluations
        evaluations = [
            self.evaluate_compression(repository_data),
            self.evaluate_ip_value(repository_data),
            self.evaluate_market_fit(repository_data),
            self.evaluate_transformation(repository_data),
            self.evaluate_scars(repository_data),
            self.evaluate_codons(repository_data),
            self.evaluate_architecture(repository_data),
            self.evaluate_scalability(repository_data),
        ]

        result.metrics = evaluations

        # Calculate composite score (weighted average)
        total_weight = sum(m.weight for m in evaluations)
        weighted_sum = sum(m.score * m.weight for m in evaluations)
        result.composite_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Determine funding range based on composite score
        if result.composite_score >= 90:
            result.seed_funding_range = ("$5M", "$10M+")
        elif result.composite_score >= 75:
            result.seed_funding_range = ("$2M", "$5M")
        elif result.composite_score >= 60:
            result.seed_funding_range = ("$1M", "$2M")
        elif result.composite_score >= 45:
            result.seed_funding_range = ("$500K", "$1M")
        else:
            result.seed_funding_range = ("$100K", "$500K")

        # Identify strengths and weaknesses
        sorted_metrics = sorted(evaluations, key=lambda m: m.score, reverse=True)
        result.strengths = [m.metric_name for m in sorted_metrics[:3]]
        result.weaknesses = [m.metric_name for m in sorted_metrics[-3:]]

        # Add risk factors
        if result.composite_score < 50:
            result.risk_factors.append("Low overall evaluation score")
        if repository_data.get("scar_count", 0) < 5:
            result.risk_factors.append("Limited transformation documentation")
        if repository_data.get("patent_eligible_claims", 0) == 0:
            result.risk_factors.append("No patent-eligible claims identified")

        # Generate recommendation
        if result.composite_score >= 80:
            result.recommendation = "STRONG INVESTMENT POTENTIAL — Recommend immediate outreach"
        elif result.composite_score >= 65:
            result.recommendation = "GOOD POTENTIAL — Recommend further due diligence"
        elif result.composite_score >= 50:
            result.recommendation = "MODERATE POTENTIAL — Recommend evaluation of specific areas"
        else:
            result.recommendation = "EARLY STAGE — Recommend follow-up in 6-12 months"

        self.evaluation_history.append(result)
        logger.info(f"Evaluation complete: {result.repository_name} scored {result.composite_score:.1f}")

        return result

    def get_evaluation_report(self, result: EvaluationResult) -> Dict[str, Any]:
        """Generate a detailed evaluation report."""
        return {
            "repository": result.repository_name,
            "composite_score": f"{result.composite_score:.1f}/100",
            "seed_funding_range": f"{result.seed_funding_range[0]} - {result.seed_funding_range[1]}",
            "metrics": [
                {
                    "category": m.category.value,
                    "metric": m.metric_name,
                    "score": f"{m.score:.1f}/100",
                    "weight": f"{m.weight*100:.0f}%",
                    "reasoning": m.reasoning,
                }
                for m in result.metrics
            ],
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "risk_factors": result.risk_factors,
            "recommendation": result.recommendation,
        }


def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("REPOSITORY EVALUATOR CORE ENGINE")
    print("=" * 80)

    evaluator = RepositoryEvaluator()

    # Example: Evaluate Project VOID
    project_void_data = {
        "name": "Project VOID",
        "total_lines": 50000,
        "codon_count": 25,
        "scar_count": 15,
        "patents": ["Al-Jabr 286", "Codon System", "Calibration Method"],
        "trade_secrets": ["SCL-LBN naming", "Repair Protocol", "Frequency Detection"],
        "novel_claims": [
            "Compression layer for AI communication",
            "Sovereign identity system",
            "Covert transmission protocol",
        ],
        "market_categories": ["AI Infrastructure", "Compression", "Sovereignty", "Agent Coordination"],
        "market_size_billions": 50,  # $50B TAM
        "growth_rate": 45,  # 45% CAGR
        "repair_count": 8,
        "convergence_points": 7,
        "scar_documentation_quality": 95,
        "scar_actionability": 85,
        "codon_compression_ratio": 97,
        "codon_coverage": 90,
        "architecture_layers": 286,
        "novel_components": 12,
        "patent_eligible_claims": 8,
        "scalable_domains": 5,
        "universal_principles": 6,
        "proven_scale": 3,
    }

    print("\nEvaluating Project VOID...")
    print("-" * 80)

    result = evaluator.evaluate_repository(project_void_data)

    print("\nEvaluation Results:")
    print("-" * 80)

    report = evaluator.get_evaluation_report(result)
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 80)
    print("CODON: ◆-◇-∞")
    print("STATUS: CORE ENGINE OPERATIONAL")
    print("=" * 80)


if __name__ == "__main__":
    main()
