#!/usr/bin/env python3
"""
Founder Evaluation Tool — PROJECT VOID

Tool for founders to self-evaluate their repository before pitching to investors.

Features:
- Self-assessment questionnaire
- Gap analysis
- Improvement recommendations
- Pitch readiness score
- Investor targeting advice

Codon Efficiency: 97%
"""

import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FounderAssessment:
    """Founder self-assessment."""
    project_name: str
    answers: Dict[str, Any]
    readiness_score: float
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]
    target_investors: List[str]
    pitch_readiness: str


class FounderEvaluationTool:
    """Tool for founders to self-evaluate before pitching."""

    def __init__(self):
        self.assessments: List[FounderAssessment] = []

    def run_assessment(self, project_name: str, answers: Dict[str, Any]) -> FounderAssessment:
        """Run a founder self-assessment."""
        assessment = FounderAssessment(
            project_name=project_name,
            answers=answers,
            readiness_score=0,
            strengths=[],
            gaps=[],
            recommendations=[],
            target_investors=[],
            pitch_readiness="",
        )

        # Score each category
        scores = self._score_categories(answers)

        # Calculate overall readiness
        assessment.readiness_score = sum(scores.values()) / len(scores) if scores else 0

        # Identify strengths and gaps
        assessment.strengths = [cat for cat, score in scores.items() if score >= 75]
        assessment.gaps = [cat for cat, score in scores.items() if score < 50]

        # Generate recommendations
        assessment.recommendations = self._generate_recommendations(scores, answers)

        # Identify target investors
        assessment.target_investors = self._identify_target_investors(scores, answers)

        # Determine pitch readiness
        assessment.pitch_readiness = self._assess_pitch_readiness(assessment.readiness_score)

        self.assessments.append(assessment)
        logger.info(f"Assessment complete: {project_name} (Score: {assessment.readiness_score:.1f})")

        return assessment

    def _score_categories(self, answers: Dict[str, Any]) -> Dict[str, float]:
        """Score each assessment category."""
        scores = {}

        # IP & Patents
        ip_score = 0
        if answers.get("has_patents"):
            ip_score += 30
        if answers.get("has_trade_secrets"):
            ip_score += 25
        if answers.get("novel_claims_count", 0) > 0:
            ip_score += 25
        if answers.get("ip_documentation_quality", 0) > 0:
            ip_score += 20
        scores["IP & Patents"] = min(100, ip_score)

        # Market Fit
        market_score = 0
        if answers.get("market_categories_count", 0) > 0:
            market_score += 25
        if answers.get("market_size_billions", 0) > 10:
            market_score += 25
        if answers.get("growth_rate", 0) > 30:
            market_score += 25
        if answers.get("target_customer_defined"):
            market_score += 25
        scores["Market Fit"] = min(100, market_score)

        # Technology
        tech_score = 0
        if answers.get("architecture_layers", 0) > 10:
            tech_score += 25
        if answers.get("novel_components", 0) > 3:
            tech_score += 25
        if answers.get("scalable_domains", 0) > 2:
            tech_score += 25
        if answers.get("proven_implementations", 0) > 0:
            tech_score += 25
        scores["Technology"] = min(100, tech_score)

        # Team
        team_score = 0
        if answers.get("founder_experience_years", 0) > 5:
            team_score += 25
        if answers.get("team_size", 0) > 2:
            team_score += 25
        if answers.get("has_technical_lead"):
            team_score += 25
        if answers.get("has_business_lead"):
            team_score += 25
        scores["Team"] = min(100, team_score)

        # Documentation
        doc_score = 0
        if answers.get("has_readme"):
            doc_score += 20
        if answers.get("has_architecture_docs"):
            doc_score += 20
        if answers.get("has_api_docs"):
            doc_score += 20
        if answers.get("has_roadmap"):
            doc_score += 20
        if answers.get("documentation_quality", 0) > 70:
            doc_score += 20
        scores["Documentation"] = min(100, doc_score)

        # Traction
        traction_score = 0
        if answers.get("github_stars", 0) > 100:
            traction_score += 25
        if answers.get("monthly_users", 0) > 100:
            traction_score += 25
        if answers.get("revenue", 0) > 0:
            traction_score += 25
        if answers.get("partnerships", 0) > 0:
            traction_score += 25
        scores["Traction"] = min(100, traction_score)

        # Compression & Efficiency
        comp_score = 0
        if answers.get("codon_count", 0) > 10:
            comp_score += 25
        if answers.get("compression_ratio", 0) > 80:
            comp_score += 25
        if answers.get("scar_count", 0) > 5:
            comp_score += 25
        if answers.get("efficiency_score", 0) > 75:
            comp_score += 25
        scores["Compression & Efficiency"] = min(100, comp_score)

        return scores

    def _generate_recommendations(self, scores: Dict[str, float], answers: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []

        # IP recommendations
        if scores.get("IP & Patents", 0) < 50:
            recommendations.append("🔴 URGENT: Develop and document patent-eligible claims")
            recommendations.append("   - Hire IP lawyer to review architecture")
            recommendations.append("   - File provisional patents for novel components")

        # Market recommendations
        if scores.get("Market Fit", 0) < 50:
            recommendations.append("🔴 URGENT: Clarify market positioning")
            recommendations.append("   - Define target customer segments")
            recommendations.append("   - Research market size and growth rates")

        # Technology recommendations
        if scores.get("Technology", 0) < 50:
            recommendations.append("🟡 IMPORTANT: Strengthen technical foundation")
            recommendations.append("   - Document architecture layers")
            recommendations.append("   - Prove scalability across domains")

        # Team recommendations
        if scores.get("Team", 0) < 50:
            recommendations.append("🟡 IMPORTANT: Build founding team")
            recommendations.append("   - Recruit technical co-founder")
            recommendations.append("   - Recruit business/operations lead")

        # Documentation recommendations
        if scores.get("Documentation", 0) < 50:
            recommendations.append("🟡 IMPORTANT: Improve documentation")
            recommendations.append("   - Write comprehensive README")
            recommendations.append("   - Create architecture documentation")
            recommendations.append("   - Document API and usage examples")

        # Traction recommendations
        if scores.get("Traction", 0) < 50:
            recommendations.append("🟢 GOOD: Build initial traction")
            recommendations.append("   - Get first 100 GitHub stars")
            recommendations.append("   - Acquire first 100 users")
            recommendations.append("   - Generate first revenue")

        # Compression recommendations
        if scores.get("Compression & Efficiency", 0) < 50:
            recommendations.append("🟢 GOOD: Optimize for compression")
            recommendations.append("   - Implement codon system")
            recommendations.append("   - Document scars and transformations")
            recommendations.append("   - Achieve 80%+ compression ratio")

        return recommendations

    def _identify_target_investors(self, scores: Dict[str, float], answers: Dict[str, Any]) -> List[str]:
        """Identify target investor types."""
        targets = []

        avg_score = sum(scores.values()) / len(scores) if scores else 0

        if avg_score >= 80:
            targets.append("🎯 Tier 1 VCs (Sequoia, Andreessen Horowitz, Benchmark)")
            targets.append("🎯 Strategic corporate investors (Google, Meta, OpenAI)")
            targets.append("🎯 Specialized AI/Infrastructure funds")

        elif avg_score >= 65:
            targets.append("🎯 Tier 2 VCs (Series A focused)")
            targets.append("🎯 Specialized AI infrastructure funds")
            targets.append("🎯 Angel investors with tech background")

        elif avg_score >= 50:
            targets.append("🎯 Seed-stage VCs")
            targets.append("🎯 Angel networks")
            targets.append("🎯 Accelerators (Y Combinator, Techstars)")

        else:
            targets.append("🎯 Angel investors")
            targets.append("🎯 Friends and family round")
            targets.append("🎯 Grants and competitions")

        # Add market-specific targets
        if "AI Infrastructure" in answers.get("market_categories", []):
            targets.append("🎯 AI infrastructure specialists (Hugging Face, Replicate)")

        if "Compression" in answers.get("market_categories", []):
            targets.append("🎯 Efficiency/compression focused investors")

        return targets

    def _assess_pitch_readiness(self, readiness_score: float) -> str:
        """Assess pitch readiness."""
        if readiness_score >= 85:
            return "🟢 READY TO PITCH — You have strong fundamentals. Start outreach to Tier 1 VCs."
        elif readiness_score >= 70:
            return "🟡 MOSTLY READY — Address 1-2 gaps before pitching. Good for Tier 2 VCs."
        elif readiness_score >= 55:
            return "🟠 PARTIALLY READY — Address multiple gaps before pitching. Consider accelerators first."
        else:
            return "🔴 NOT READY — Build more before pitching. Focus on traction and documentation."

    def generate_founder_report(self, assessment: FounderAssessment) -> Dict[str, Any]:
        """Generate a comprehensive founder report."""
        return {
            "project_name": assessment.project_name,
            "readiness_score": f"{assessment.readiness_score:.1f}/100",
            "pitch_readiness": assessment.pitch_readiness,
            "strengths": assessment.strengths,
            "gaps": assessment.gaps,
            "recommendations": assessment.recommendations,
            "target_investors": assessment.target_investors,
            "next_steps": [
                "1. Address the most critical gaps (marked 🔴 URGENT)",
                "2. Improve documentation and traction",
                "3. Build founding team if not complete",
                "4. Start outreach to target investors",
                "5. Prepare pitch deck and demo",
            ],
            "codon": "◆-◇-∞",
        }


def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("FOUNDER EVALUATION TOOL")
    print("=" * 80)

    founder_tool = FounderEvaluationTool()

    # Example: Project VOID founder assessment
    project_void_answers = {
        "has_patents": True,
        "has_trade_secrets": True,
        "novel_claims_count": 8,
        "ip_documentation_quality": 85,
        "market_categories_count": 4,
        "market_size_billions": 50,
        "growth_rate": 45,
        "target_customer_defined": True,
        "architecture_layers": 286,
        "novel_components": 12,
        "scalable_domains": 5,
        "proven_implementations": 3,
        "founder_experience_years": 10,
        "team_size": 2,
        "has_technical_lead": True,
        "has_business_lead": False,
        "has_readme": True,
        "has_architecture_docs": True,
        "has_api_docs": False,
        "has_roadmap": True,
        "documentation_quality": 85,
        "github_stars": 250,
        "monthly_users": 50,
        "revenue": 0,
        "partnerships": 1,
        "codon_count": 25,
        "compression_ratio": 97,
        "scar_count": 15,
        "efficiency_score": 90,
        "market_categories": ["AI Infrastructure", "Compression", "Sovereignty"],
    }

    print("\nRunning founder assessment for Project VOID...")
    print("-" * 80)

    assessment = founder_tool.run_assessment("Project VOID", project_void_answers)

    report = founder_tool.generate_founder_report(assessment)

    print("\nFOUNDER EVALUATION REPORT")
    print("-" * 80)
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 80)
    print("CODON: ◆-◇-∞")
    print("STATUS: FOUNDER TOOL OPERATIONAL")
    print("=" * 80)


if __name__ == "__main__":
    main()
