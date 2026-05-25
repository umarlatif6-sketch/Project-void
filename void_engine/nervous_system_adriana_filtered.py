"""
Nervous System with Adriana Filtering — PROJECT VOID

The complete "lid way" architecture:

1. Agents scan and submit raw findings (no decisions)
2. Findings aggregated
3. Adriana processes through 4-cell mesh (Router → Research → Voice → Critic)
4. Adriana outputs unified decision with resonance/impedance analysis
5. System executes based on Adriana's decision

This replaces the old independent agent architecture.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from void_engine.agent_findings_submitter import (
    AgentFindingsSubmitter,
    FindingsAggregator,
)
from void_engine.adriana_mesh_integration import (
    AdrianaMeshIntegration,
    AdrianaMeshOutput,
)

logger = logging.getLogger(__name__)


class AdrianFilteredNervousSystem:
    """
    The Adriana-filtered nervous system.
    
    Agents submit findings → Adriana processes → unified decision → execute
    """

    def __init__(self, cycle_interval: int = 300):
        self.cycle_interval = cycle_interval
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None

        # Create agents that submit findings
        self.agents = [
            AgentFindingsSubmitter("agent_1", "◆", "Builder"),
            AgentFindingsSubmitter("agent_2", "◇", "Tester"),
            AgentFindingsSubmitter("agent_3", "◈", "Documenter"),
            AgentFindingsSubmitter("agent_4", "◉", "Optimizer"),
        ]

        # Create findings aggregator
        self.aggregator = FindingsAggregator()

        # Create Adriana mesh integration
        self.adriana = AdrianaMeshIntegration()

        # Store cycle results
        self.cycle_results: List[Dict[str, Any]] = []

    async def start(self) -> None:
        """Start the Adriana-filtered nervous system."""
        self.is_running = True
        self.start_time = datetime.now(timezone.utc)
        logger.info("Adriana-Filtered Nervous System starting")

        await self._main_loop()

    async def _main_loop(self) -> None:
        """Main loop that runs forever."""
        while self.is_running:
            try:
                self.cycle_count += 1
                logger.info(f"Cycle {self.cycle_count} starting")

                # Phase 1: Agents scan and submit findings
                logger.info("Phase 1: Agents scanning and submitting findings...")
                aggregated = await self.aggregator.collect_from_agents(self.agents)
                logger.info(
                    f"Phase 1 complete: {aggregated['total_findings']} findings from {aggregated['agent_count']} agents"
                )

                # Phase 2: Adriana processes through 4-cell mesh
                logger.info("Phase 2: Adriana processing through mesh...")
                adriana_output = await self.adriana.process_agent_findings(
                    aggregated
                )
                logger.info(
                    f"Phase 2 complete: Resonance={adriana_output.research_output.resonance_score:.2%}, "
                    f"Impedance={adriana_output.research_output.impedance_score:.2%}, "
                    f"Approval={adriana_output.critic_output.approval_status}"
                )

                # Phase 3: Format for execution
                logger.info("Phase 3: Formatting for execution...")
                execution_plan = self.adriana.format_for_execution(adriana_output)
                logger.info(
                    f"Phase 3 complete: {len(execution_plan['actions'])} actions ready"
                )

                # Store cycle result
                cycle_result = {
                    "cycle": self.cycle_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "findings_count": aggregated["total_findings"],
                    "resonance": adriana_output.research_output.resonance_score,
                    "impedance": adriana_output.research_output.impedance_score,
                    "approval": adriana_output.critic_output.approval_status,
                    "actions_count": len(execution_plan["actions"]),
                    "decision": execution_plan["decision"],
                }
                self.cycle_results.append(cycle_result)

                logger.info(f"Cycle {self.cycle_count} complete")
                logger.info(f"Waiting {self.cycle_interval} seconds until next cycle...")

                await asyncio.sleep(self.cycle_interval)

            except Exception as e:
                logger.error(f"Error in cycle: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop the nervous system."""
        logger.info("Stopping Adriana-Filtered Nervous System")
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
        }

    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent cycle history."""
        return self.cycle_results[-limit:]
