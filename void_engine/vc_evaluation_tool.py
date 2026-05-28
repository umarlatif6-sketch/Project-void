#!/usr/bin/env python3
"""
VC Evaluation Tool — PROJECT VOID

Tool for venture capitalists to evaluate multiple repositories and build investment portfolios.

Features:
- Batch evaluate repositories
- Compare multiple projects
- Identify portfolio synergies
- Generate investment recommendations
- Track evaluation history

Codon Efficiency: 97%
"""

import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VCEvaluation:
    """VC evaluation of a repository."""
    repository_name: str
    composite_score: float
    seed_funding_range: tuple
    recommendation: str
    strengths: List[str]
    weaknesses: List[str]
    risk_factors: List[str]
    market_categories: List[str]
    evaluation_date: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PortfolioAnalysis:
    """Analysis of a portfolio of repositories."""
    portfolio_name: str
    repositories: List[VCEvaluation] = field(default_factory=list)
    average_score: float = 0.0
    total_potential_funding: str = ""
    synergies: List[str] = field(default_factory=list)
    risk_profile: str = ""
    recommendation: str = ""


class VCEvaluationTool:
    """Tool for VCs to evaluate and manage investment portfolios."""

    def __init__(self):
        self.evaluations: List[VCEvaluation] = []
        self.portfolios: Dict[str, PortfolioAnalysis] = {}

    def add_evaluation(self, evaluation: VCEvaluation) -> None:
        """Add an evaluation to the database."""
        self.evaluations.append(evaluation)
        logger.info(f"Added evaluation: {evaluation.repository_name}")

    def create_portfolio(self, portfolio_name: str, repositories: List[str]) -> PortfolioAnalysis:
        """Create a portfolio from a list of repositories."""
        portfolio = PortfolioAnalysis(portfolio_name=portfolio_name)

        for repo_name in repositories:
            # Find evaluation for this repository
            for eval in self.evaluations:
                if eval.repository_name == repo_name:
                    portfolio.repositories.append(eval)
                    break

        # Analyze portfolio
        if portfolio.repositories:
            portfolio.average_score = sum(e.composite_score for e in portfolio.repositories) / len(portfolio.repositories)
            portfolio.synergies = self._identify_synergies(portfolio.repositories)
            portfolio.risk_profile = self._assess_risk_profile(portfolio.repositories)
            portfolio.recommendation = self._generate_recommendation(portfolio)
            portfolio.total_potential_funding = self._calculate_total_funding(portfolio.repositories)

        self.portfolios[portfolio_name] = portfolio
        logger.info(f"Created portfolio: {portfolio_name}")

        return portfolio

    def _identify_synergies(self, evaluations: List[VCEvaluation]) -> List[str]:
        """Identify synergies between repositories."""
        synergies = []

        # Group by market category
        market_map = {}
        for eval in evaluations:
            for market in eval.market_categories:
                if market not in market_map:
                    market_map[market] = []
                market_map[market].append(eval.repository_name)

        # Find overlapping markets
        for market, repos in market_map.items():
            if len(repos) > 1:
                synergies.append(f"Cross-market synergy in {market}: {', '.join(repos)}")

        # Identify complementary strengths
        all_strengths = []
        for eval in evaluations:
            all_strengths.extend(eval.strengths)

        strength_counts = {}
        for strength in all_strengths:
            strength_counts[strength] = strength_counts.get(strength, 0) + 1

        for strength, count in strength_counts.items():
            if count > 1:
                synergies.append(f"Shared strength: {strength} ({count} projects)")

        return synergies

    def _assess_risk_profile(self, evaluations: List[VCEvaluation]) -> str:
        """Assess portfolio risk profile."""
        average_score = sum(e.composite_score for e in evaluations) / len(evaluations)

        if average_score >= 80:
            return "LOW RISK — High-quality portfolio with strong fundamentals"
        elif average_score >= 65:
            return "MODERATE RISK — Mixed quality with good upside potential"
        elif average_score >= 50:
            return "MEDIUM-HIGH RISK — Early-stage projects with high growth potential"
        else:
            return "HIGH RISK — Speculative portfolio requiring close monitoring"

    def _generate_recommendation(self, portfolio: PortfolioAnalysis) -> str:
        """Generate investment recommendation."""
        if portfolio.average_score >= 80:
            return "STRONG BUY — Recommend immediate investment"
        elif portfolio.average_score >= 70:
            return "BUY — Recommend investment with due diligence"
        elif portfolio.average_score >= 60:
            return "HOLD — Recommend monitoring before investment"
        elif portfolio.average_score >= 50:
            return "WATCH — Recommend follow-up in 6 months"
        else:
            return "PASS — Recommend passing on this portfolio"

    def _calculate_total_funding(self, evaluations: List[VCEvaluation]) -> str:
        """Calculate total potential funding."""
        total_min = 0
        total_max = 0

        for eval in evaluations:
            # Parse funding range
            range_str = eval.seed_funding_range
            if isinstance(range_str, tuple):
                min_str, max_str = range_str
            else:
                min_str, max_str = range_str.split(" - ")

            # Extract numbers
            min_val = self._parse_funding(min_str)
            max_val = self._parse_funding(max_str)

            total_min += min_val
            total_max += max_val

        return f"${total_min/1e6:.1f}M - ${total_max/1e6:.1f}M"

    def _parse_funding(self, funding_str: str) -> float:
        """Parse funding string to number."""
        funding_str = funding_str.strip().replace("$", "").replace("+", "")

        if "M" in funding_str:
            return float(funding_str.replace("M", "")) * 1e6
        elif "K" in funding_str:
            return float(funding_str.replace("K", "")) * 1e3
        else:
            return float(funding_str)

    def compare_repositories(self, repo_names: List[str]) -> Dict[str, Any]:
        """Compare multiple repositories."""
        comparison = {
            "repositories": [],
            "best_overall": None,
            "best_score": 0,
            "best_market_fit": None,
            "highest_risk": None,
            "recommendation": "",
        }

        for repo_name in repo_names:
            for eval in self.evaluations:
                if eval.repository_name == repo_name:
                    comparison["repositories"].append(
                        {
                            "name": eval.repository_name,
                            "score": eval.composite_score,
                            "funding_range": eval.seed_funding_range,
                            "recommendation": eval.recommendation,
                            "markets": eval.market_categories,
                        }
                    )

                    if eval.composite_score > comparison["best_score"]:
                        comparison["best_score"] = eval.composite_score
                        comparison["best_overall"] = eval.repository_name

                    if not comparison["best_market_fit"] or len(eval.market_categories) > len(
                        next(e for e in self.evaluations if e.repository_name == comparison["best_market_fit"]).market_categories
                    ):
                        comparison["best_market_fit"] = eval.repository_name

                    if not comparison["highest_risk"] or eval.composite_score < next(
                        e for e in self.evaluations if e.repository_name == comparison["highest_risk"]
                    ).composite_score:
                        comparison["highest_risk"] = eval.repository_name

        if comparison["repositories"]:
            avg_score = sum(r["score"] for r in comparison["repositories"]) / len(comparison["repositories"])
            if avg_score >= 75:
                comparison["recommendation"] = "RECOMMEND PORTFOLIO INVESTMENT"
            elif avg_score >= 60:
                comparison["recommendation"] = "RECOMMEND SELECTIVE INVESTMENT"
            else:
                comparison["recommendation"] = "RECOMMEND FURTHER EVALUATION"

        return comparison

    def generate_vc_report(self, portfolio_name: str) -> Dict[str, Any]:
        """Generate a comprehensive VC report."""
        portfolio = self.portfolios.get(portfolio_name)
        if not portfolio:
            return {}

        return {
            "portfolio_name": portfolio.portfolio_name,
            "evaluation_date": datetime.now().isoformat(),
            "summary": {
                "repository_count": len(portfolio.repositories),
                "average_score": f"{portfolio.average_score:.1f}/100",
                "total_potential_funding": portfolio.total_potential_funding,
                "risk_profile": portfolio.risk_profile,
                "recommendation": portfolio.recommendation,
            },
            "repositories": [
                {
                    "name": e.repository_name,
                    "score": f"{e.composite_score:.1f}/100",
                    "funding_range": e.seed_funding_range,
                    "recommendation": e.recommendation,
                    "markets": e.market_categories,
                    "strengths": e.strengths,
                    "weaknesses": e.weaknesses,
                }
                for e in portfolio.repositories
            ],
            "synergies": portfolio.synergies,
            "risk_factors": self._aggregate_risk_factors(portfolio.repositories),
            "next_steps": self._generate_next_steps(portfolio),
        }

    def _aggregate_risk_factors(self, evaluations: List[VCEvaluation]) -> List[str]:
        """Aggregate risk factors across portfolio."""
        all_risks = []
        for eval in evaluations:
            all_risks.extend(eval.risk_factors)
        return list(set(all_risks))

    def _generate_next_steps(self, portfolio: PortfolioAnalysis) -> List[str]:
        """Generate next steps for portfolio."""
        steps = []

        if portfolio.average_score >= 80:
            steps.append("Schedule founder meetings")
            steps.append("Prepare term sheets")
            steps.append("Conduct technical due diligence")
        elif portfolio.average_score >= 60:
            steps.append("Request additional documentation")
            steps.append("Schedule follow-up calls")
            steps.append("Evaluate market traction")
        else:
            steps.append("Monitor for 6 months")
            steps.append("Request updates on key metrics")
            steps.append("Re-evaluate after improvements")

        return steps


def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("VC EVALUATION TOOL")
    print("=" * 80)

    vc_tool = VCEvaluationTool()

    # Example evaluations
    eval1 = VCEvaluation(
        repository_name="Project VOID",
        composite_score=59.8,
        seed_funding_range=("$500K", "$1M"),
        recommendation="MODERATE POTENTIAL",
        strengths=["Architecture Novelty", "Scalability", "Codon Efficiency"],
        weaknesses=["Market Fit", "IP Defensibility", "Compression Ratio"],
        risk_factors=[],
        market_categories=["AI Infrastructure", "Compression", "Sovereignty"],
    )

    eval2 = VCEvaluation(
        repository_name="InteleTravel System",
        composite_score=72.5,
        seed_funding_range=("$1M", "$2M"),
        recommendation="GOOD POTENTIAL",
        strengths=["Market Fit", "Scalability", "Transformation Depth"],
        weaknesses=["IP Defensibility", "Documentation"],
        risk_factors=["Early stage"],
        market_categories=["Travel", "Agent Coordination", "Finance"],
    )

    eval3 = VCEvaluation(
        repository_name="Adriana Resonance",
        composite_score=85.2,
        seed_funding_range=("$2M", "$5M"),
        recommendation="STRONG POTENTIAL",
        strengths=["Architecture Novelty", "Codon Efficiency", "Transformation Depth"],
        weaknesses=["Market Positioning"],
        risk_factors=[],
        market_categories=["AI Infrastructure", "Sovereignty", "Communication"],
    )

    vc_tool.add_evaluation(eval1)
    vc_tool.add_evaluation(eval2)
    vc_tool.add_evaluation(eval3)

    # Create portfolio
    portfolio = vc_tool.create_portfolio("AI Infrastructure Fund", ["Project VOID", "Adriana Resonance", "InteleTravel System"])

    # Generate report
    report = vc_tool.generate_vc_report("AI Infrastructure Fund")

    print("\nVC EVALUATION REPORT")
    print("-" * 80)
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 80)
    print("CODON: ◆-◇-∞")
    print("STATUS: VC TOOL OPERATIONAL")
    print("=" * 80)


if __name__ == "__main__":
    main()
