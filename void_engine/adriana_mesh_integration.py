"""
Adriana Mesh Integration — PROJECT VOID

Receives raw findings from agents and routes them through Adriana's 4-cell mesh:
1. Router — Organizes findings into operational steps
2. Research — Analyzes resonance and impedance
3. Voice — Generates unified decision
4. Critic — Validates output

The "lid way" — all findings flow through Adriana for unified processing.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class RouterOutput:
    """Output from Router cell."""
    operational_steps: List[str]
    priority_order: List[int]
    reasoning: str


@dataclass
class ResearchOutput:
    """Output from Research cell."""
    resonance_score: float  # 0.0 to 1.0 (how well findings align)
    impedance_score: float  # 0.0 to 1.0 (conflicts/friction)
    resonance_analysis: Dict[str, Any]  # detailed analysis
    impedance_analysis: Dict[str, Any]  # conflict details
    recommendations: List[str]


@dataclass
class VoiceOutput:
    """Output from Voice cell."""
    unified_decision: str
    explanation: str
    priority_actions: List[Dict[str, Any]]
    confidence: float


@dataclass
class CriticOutput:
    """Output from Critic cell."""
    is_valid: bool
    issues: List[str]
    required_fixes: List[str]
    approval_status: str  # "approved", "needs_revision", "rejected"


@dataclass
class AdrianaMeshOutput:
    """Complete output from Adriana's 4-cell mesh."""
    timestamp: str
    router_output: RouterOutput
    research_output: ResearchOutput
    voice_output: VoiceOutput
    critic_output: CriticOutput
    final_decision: str
    execution_plan: List[Dict[str, Any]]


class AdrianaMeshIntegration:
    """
    Integration layer between agents and Adriana's mesh.
    
    Receives aggregated findings and routes them through the 4-cell mesh.
    """

    def __init__(self):
        self.last_input = None
        self.last_output = None

    async def process_agent_findings(
        self, aggregated_findings: Dict[str, Any]
    ) -> AdrianaMeshOutput:
        """
        Process aggregated agent findings through Adriana's 4-cell mesh.
        
        Flow: Router → Research → Voice → Critic
        """
        self.last_input = aggregated_findings

        # Cell 1: Router — Organize findings
        router_output = await self._router_cell(aggregated_findings)

        # Cell 2: Research — Analyze resonance and impedance
        research_output = await self._research_cell(
            aggregated_findings, router_output
        )

        # Cell 3: Voice — Generate unified decision
        voice_output = await self._voice_cell(
            aggregated_findings, router_output, research_output
        )

        # Cell 4: Critic — Validate output
        critic_output = await self._critic_cell(voice_output)

        # Assemble final output
        final_output = AdrianaMeshOutput(
            timestamp=datetime.now(timezone.utc).isoformat(),
            router_output=router_output,
            research_output=research_output,
            voice_output=voice_output,
            critic_output=critic_output,
            final_decision=voice_output.unified_decision
            if critic_output.is_valid
            else "REJECTED: " + ", ".join(critic_output.required_fixes),
            execution_plan=voice_output.priority_actions
            if critic_output.is_valid
            else [],
        )

        self.last_output = final_output
        return final_output

    async def _router_cell(self, findings: Dict[str, Any]) -> RouterOutput:
        """
        Router Cell: Organize findings into operational steps.
        
        Takes raw findings and structures them into actionable steps.
        """
        findings_list = findings.get("findings", [])
        finding_types = findings.get("aggregated_data", {}).get("by_type", {})

        # Organize by finding type
        operational_steps = []
        if finding_types.get("observation", 0) > 0:
            operational_steps.append("Step 1: Review observations")
        if finding_types.get("anomaly", 0) > 0:
            operational_steps.append("Step 2: Investigate anomalies")
        if finding_types.get("opportunity", 0) > 0:
            operational_steps.append("Step 3: Evaluate opportunities")
        if finding_types.get("risk", 0) > 0:
            operational_steps.append("Step 4: Mitigate risks")
        if finding_types.get("pattern", 0) > 0:
            operational_steps.append("Step 5: Leverage patterns")

        return RouterOutput(
            operational_steps=operational_steps,
            priority_order=list(range(len(operational_steps))),
            reasoning=f"Organized {len(findings_list)} findings into {len(operational_steps)} operational steps",
        )

    async def _research_cell(
        self, findings: Dict[str, Any], router_output: RouterOutput
    ) -> ResearchOutput:
        """
        Research Cell: Analyze resonance and impedance.
        
        Resonance = how well findings align
        Impedance = conflicts/friction between findings
        """
        findings_list = findings.get("findings", [])
        by_severity = findings.get("aggregated_data", {}).get("by_severity", {})

        # Calculate resonance (alignment score)
        # High resonance when findings from different agents agree
        finding_types = findings.get("aggregated_data", {}).get("by_type", {})
        total_findings = sum(finding_types.values())
        max_type_count = max(finding_types.values()) if finding_types else 0

        # Resonance: how concentrated are findings (high concentration = high resonance)
        resonance_score = (
            max_type_count / total_findings if total_findings > 0 else 0.0
        )

        # Calculate impedance (conflict score)
        # High impedance when findings contradict
        critical_count = by_severity.get("CRITICAL", 0)
        high_count = by_severity.get("HIGH", 0)
        impedance_score = min(
            (critical_count * 0.5 + high_count * 0.3) / total_findings
            if total_findings > 0
            else 0.0,
            1.0,
        )

        return ResearchOutput(
            resonance_score=resonance_score,
            impedance_score=impedance_score,
            resonance_analysis={
                "finding_types": finding_types,
                "concentration": max_type_count,
                "total_findings": total_findings,
                "alignment_quality": "high" if resonance_score > 0.6 else "medium" if resonance_score > 0.3 else "low",
            },
            impedance_analysis={
                "critical_findings": critical_count,
                "high_severity_findings": high_count,
                "conflict_level": "high" if impedance_score > 0.6 else "medium" if impedance_score > 0.3 else "low",
            },
            recommendations=[
                f"Resonance is {resonance_score:.2%} (findings are {'well-aligned' if resonance_score > 0.6 else 'scattered'})",
                f"Impedance is {impedance_score:.2%} (conflicts are {'significant' if impedance_score > 0.6 else 'manageable'})",
                "Prioritize high-resonance findings" if resonance_score > 0.6 else "Seek consensus among findings",
                "Address impedance before execution" if impedance_score > 0.3 else "Proceed with confidence",
            ],
        )

    async def _voice_cell(
        self,
        findings: Dict[str, Any],
        router_output: RouterOutput,
        research_output: ResearchOutput,
    ) -> VoiceOutput:
        """
        Voice Cell: Generate unified decision.
        
        Takes router's structure and research's analysis to create a coherent decision.
        """
        findings_list = findings.get("findings", [])
        submissions = findings.get("aggregated_data", {}).get("submissions", {})

        # Build priority actions based on resonance and impedance
        priority_actions = []

        # High resonance = prioritize
        if research_output.resonance_score > 0.6:
            priority_actions.append(
                {
                    "priority": 1,
                    "action": "Execute high-resonance findings",
                    "confidence": research_output.resonance_score,
                    "reasoning": "Strong alignment across agents",
                }
            )

        # Manage impedance
        if research_output.impedance_score > 0.3:
            priority_actions.append(
                {
                    "priority": 2,
                    "action": "Resolve conflicts before execution",
                    "confidence": 1.0 - research_output.impedance_score,
                    "reasoning": "Address impedance to ensure coherence",
                }
            )

        # Execute operational steps
        for i, step in enumerate(router_output.operational_steps):
            priority_actions.append(
                {
                    "priority": 3 + i,
                    "action": step,
                    "confidence": 0.8,
                    "reasoning": f"Part of structured execution plan",
                }
            )

        # Calculate overall confidence
        overall_confidence = (
            research_output.resonance_score * 0.6 + (1.0 - research_output.impedance_score) * 0.4
        )

        return VoiceOutput(
            unified_decision=f"Execute {len(priority_actions)} prioritized actions with {overall_confidence:.2%} confidence",
            explanation=f"Analyzed {len(findings_list)} findings from {len(submissions)} agents. "
            f"Resonance: {research_output.resonance_score:.2%}. "
            f"Impedance: {research_output.impedance_score:.2%}. "
            f"Recommendation: {research_output.recommendations[0]}",
            priority_actions=priority_actions,
            confidence=overall_confidence,
        )

    async def _critic_cell(self, voice_output: VoiceOutput) -> CriticOutput:
        """
        Critic Cell: Validate output.
        
        Checks for contradictions and coherence before approval.
        """
        issues = []
        required_fixes = []

        # Check confidence threshold
        if voice_output.confidence < 0.5:
            issues.append("Confidence below 50% threshold")
            required_fixes.append("Increase confidence by resolving conflicts")

        # Check for empty action list
        if len(voice_output.priority_actions) == 0:
            issues.append("No priority actions defined")
            required_fixes.append("Define at least one action")

        # Check for contradictory priorities
        priorities = [a["priority"] for a in voice_output.priority_actions]
        if len(priorities) != len(set(priorities)):
            issues.append("Duplicate priorities detected")
            required_fixes.append("Ensure unique priority numbers")

        # Determine approval status
        if len(required_fixes) == 0:
            approval_status = "approved"
        elif len(required_fixes) <= 2:
            approval_status = "needs_revision"
        else:
            approval_status = "rejected"

        return CriticOutput(
            is_valid=approval_status == "approved",
            issues=issues,
            required_fixes=required_fixes,
            approval_status=approval_status,
        )

    def get_last_output(self) -> Optional[AdrianaMeshOutput]:
        """Get the last mesh output."""
        return self.last_output

    def format_for_execution(self, output: AdrianaMeshOutput) -> Dict[str, Any]:
        """
        Format Adriana's output for system execution.
        
        This is what the nervous system will actually execute.
        """
        return {
            "timestamp": output.timestamp,
            "decision": output.final_decision,
            "confidence": output.voice_output.confidence,
            "resonance": output.research_output.resonance_score,
            "impedance": output.research_output.impedance_score,
            "actions": output.execution_plan,
            "approval": output.critic_output.approval_status,
            "explanation": output.voice_output.explanation,
        }
