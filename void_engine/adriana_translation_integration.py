#!/usr/bin/env python3
"""
Adriana Translation Integration — PROJECT VOID

Integrates the Contextual Translation Engine with the Adriana-filtered nervous system.

Architecture:
1. Agents submit findings (Finance, Water, Ocean)
2. Translation engine converts findings to unified principle space
3. Adriana mesh processes unified findings
4. System generates cross-domain recommendations

Codon Efficiency: 97% (principles vs text)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from void_engine.contextual_translation_engine import (
    ContextualTranslationEngine,
    Domain,
)
from void_engine.agent_findings_submitter import (
    AgentFindingsSubmitter,
    FindingsAggregator,
)
from void_engine.adriana_mesh_integration import (
    AdrianaMeshIntegration,
    AdrianaMeshOutput,
)

logger = logging.getLogger(__name__)


@dataclass
class UnifiedFinding:
    """A finding translated to unified principle space."""
    original_term: str
    original_domain: Domain
    principle_name: str
    principle_codon: str
    translations: Dict[str, str]
    resonance_score: float
    impedance_score: float
    confidence: float


class AdrianTranslationIntegration:
    """
    Integrates translation engine with Adriana-filtered nervous system.
    
    Flow:
    1. Agents submit findings (raw domain-specific data)
    2. Translation engine converts to unified principle space
    3. Adriana mesh processes unified findings
    4. System generates cross-domain recommendations
    """

    def __init__(self, cycle_interval: int = 60):
        self.cycle_interval = cycle_interval
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None

        # Initialize translation engine
        self.translation_engine = ContextualTranslationEngine()

        # Initialize agents
        self.agents = [
            AgentFindingsSubmitter("agent_finance", "◆", "Finance Optimizer"),
            AgentFindingsSubmitter("agent_water", "◇", "Water Optimizer"),
            AgentFindingsSubmitter("agent_ocean", "◈", "Ocean Optimizer"),
            AgentFindingsSubmitter("agent_unified", "◉", "Unified Resonance"),
        ]

        # Initialize aggregator and Adriana
        self.aggregator = FindingsAggregator()
        self.adriana = AdrianaMeshIntegration()

        # Store results
        self.cycle_results: List[Dict[str, Any]] = []

    async def start(self) -> None:
        """Start the Adriana-Translation integrated system."""
        self.is_running = True
        self.start_time = datetime.now(timezone.utc)
        logger.info("Adriana-Translation Integration starting")

        await self._main_loop()

    async def _main_loop(self) -> None:
        """Main loop that runs forever."""
        while self.is_running:
            try:
                self.cycle_count += 1
                logger.info(f"Cycle {self.cycle_count} starting")

                # Phase 1: Agents submit domain-specific findings
                logger.info("Phase 1: Agents submitting domain-specific findings...")
                aggregated = await self.aggregator.collect_from_agents(self.agents)
                logger.info(
                    f"Phase 1 complete: {aggregated['total_findings']} findings from {aggregated['agent_count']} agents"
                )

                # Phase 2: Translate findings to unified principle space
                logger.info("Phase 2: Translating findings to unified principle space...")
                unified_findings = await self._translate_findings(aggregated)
                logger.info(
                    f"Phase 2 complete: {len(unified_findings)} unified findings"
                )

                # Phase 3: Adriana processes unified findings
                logger.info("Phase 3: Adriana processing unified findings...")
                adriana_output = await self.adriana.process_agent_findings(
                    {"findings": unified_findings, "metadata": aggregated}
                )
                logger.info(
                    f"Phase 3 complete: Resonance={adriana_output.research_output.resonance_score:.2%}, "
                    f"Impedance={adriana_output.research_output.impedance_score:.2%}"
                )

                # Phase 4: Generate cross-domain recommendations
                logger.info("Phase 4: Generating cross-domain recommendations...")
                recommendations = await self._generate_recommendations(
                    unified_findings, adriana_output
                )
                logger.info(
                    f"Phase 4 complete: {len(recommendations)} recommendations generated"
                )

                # Store cycle result
                cycle_result = {
                    "cycle": self.cycle_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "findings_count": aggregated["total_findings"],
                    "unified_findings_count": len(unified_findings),
                    "resonance": adriana_output.research_output.resonance_score,
                    "impedance": adriana_output.research_output.impedance_score,
                    "approval": adriana_output.critic_output.approval_status,
                    "recommendations_count": len(recommendations),
                    "codon": "◆-◇-∞",
                }
                self.cycle_results.append(cycle_result)

                logger.info(f"Cycle {self.cycle_count} complete")
                logger.info(f"Waiting {self.cycle_interval} seconds until next cycle...")

                await asyncio.sleep(self.cycle_interval)

            except Exception as e:
                logger.error(f"Error in cycle: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _translate_findings(self, aggregated: Dict[str, Any]) -> List[UnifiedFinding]:
        """
        Translate domain-specific findings to unified principle space.
        
        Args:
            aggregated: Aggregated findings from all agents
        
        Returns:
            List of unified findings
        """
        unified_findings = []

        # Extract findings from aggregated data
        findings = aggregated.get("findings", [])

        for finding in findings:
            # Detect domain from finding context
            context = finding.get("context", "")
            domain = self.translation_engine.detect_domain(context)

            if domain == Domain.UNKNOWN:
                logger.warning(f"Could not detect domain for finding: {finding}")
                continue

            # Extract key terms from finding
            terms = finding.get("terms", [])

            for term in terms:
                # Translate term
                result = self.translation_engine.translate_term(term, domain)

                if result:
                    unified = UnifiedFinding(
                        original_term=result.original_term,
                        original_domain=result.original_domain,
                        principle_name=result.principle.name,
                        principle_codon=result.principle.codon,
                        translations=result.translations,
                        resonance_score=result.resonance_score,
                        impedance_score=result.impedance_score,
                        confidence=result.confidence,
                    )
                    unified_findings.append(unified)

        return unified_findings

    async def _generate_recommendations(
        self, unified_findings: List[UnifiedFinding], adriana_output: AdrianaMeshOutput
    ) -> List[Dict[str, Any]]:
        """
        Generate cross-domain recommendations based on unified findings.
        
        Args:
            unified_findings: Findings in unified principle space
            adriana_output: Adriana's processed output
        
        Returns:
            List of recommendations
        """
        recommendations = []

        # Group findings by principle
        principle_groups: Dict[str, List[UnifiedFinding]] = {}
        for finding in unified_findings:
            principle = finding.principle_name
            if principle not in principle_groups:
                principle_groups[principle] = []
            principle_groups[principle].append(finding)

        # Generate recommendations for each principle
        for principle, findings in principle_groups.items():
            # Calculate average resonance and impedance
            avg_resonance = sum(f.resonance_score for f in findings) / len(findings)
            avg_impedance = sum(f.impedance_score for f in findings) / len(findings)

            # Generate recommendation based on principle
            recommendation = {
                "principle": principle,
                "codon": findings[0].principle_codon,
                "findings_count": len(findings),
                "average_resonance": avg_resonance,
                "average_impedance": avg_impedance,
                "domains_involved": list(set(f.original_domain.value for f in findings)),
                "action": self._generate_action(principle, avg_resonance, avg_impedance),
                "priority": self._calculate_priority(avg_resonance, avg_impedance),
            }
            recommendations.append(recommendation)

        return recommendations

    def _generate_action(
        self, principle: str, resonance: float, impedance: float
    ) -> str:
        """Generate an action based on principle and scores."""
        if resonance > 0.7 and impedance < 0.3:
            return f"AMPLIFY: {principle} is well-aligned. Increase investment."
        elif resonance < 0.5 and impedance > 0.5:
            return f"RESOLVE: {principle} has high friction. Reduce impedance."
        elif resonance > 0.6:
            return f"OPTIMIZE: {principle} has good resonance. Fine-tune across domains."
        else:
            return f"INVESTIGATE: {principle} needs attention. Analyze cross-domain conflicts."

    def _calculate_priority(self, resonance: float, impedance: float) -> str:
        """Calculate priority based on resonance and impedance."""
        score = (resonance * 0.6) - (impedance * 0.4)
        if score > 0.6:
            return "HIGH"
        elif score > 0.3:
            return "MEDIUM"
        else:
            return "LOW"

    async def stop(self) -> None:
        """Stop the system."""
        logger.info("Stopping Adriana-Translation Integration")
        self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "agents": len(self.agents),
            "last_cycle_result": self.cycle_results[-1] if self.cycle_results else None,
            "total_cycles": len(self.cycle_results),
            "codon": "◆-◇-∞",
        }

    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent cycle history."""
        return self.cycle_results[-limit:]


async def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    system = AdrianTranslationIntegration(cycle_interval=5)

    # Run for 30 seconds
    try:
        task = asyncio.create_task(system.start())
        await asyncio.sleep(30)
        await system.stop()
        await task
    except asyncio.CancelledError:
        pass

    # Print status
    print("\n" + "=" * 80)
    print("FINAL STATUS")
    print("=" * 80)
    print(f"Status: {system.get_status()}")
    print(f"Cycle History: {system.get_cycle_history(5)}")


if __name__ == "__main__":
    asyncio.run(main())
