"""
Agent Findings Submitter — PROJECT VOID

Agents no longer make independent decisions.
Instead, they submit raw findings to Adriana for unified processing.

Each agent:
1. Scans the environment
2. Collects raw observations
3. Submits findings (not decisions)
4. Waits for Adriana's unified decision
5. Executes based on Adriana's output

This is the "lid way" — all findings flow through Adriana's 4-cell mesh.
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class FindingType(Enum):
    """Types of findings agents can submit."""
    OBSERVATION = "observation"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    PATTERN = "pattern"
    METRIC = "metric"
    STATE_CHANGE = "state_change"


class FindingSeverity(Enum):
    """Severity levels for findings."""
    LOW = 0.2
    MEDIUM = 0.5
    HIGH = 0.8
    CRITICAL = 1.0


@dataclass
class Finding:
    """A raw finding submitted by an agent."""
    finding_id: str
    agent_id: str
    agent_glyph: str
    finding_type: FindingType
    severity: FindingSeverity
    description: str
    location: str  # where in the system
    evidence: Dict[str, Any]  # raw data supporting the finding
    timestamp: str
    codon: str  # encoded as codon


@dataclass
class FindingSubmission:
    """A batch of findings submitted by an agent."""
    submission_id: str
    agent_id: str
    agent_glyph: str
    findings: List[Finding]
    submission_time: str
    agent_state: str  # what was the agent doing when it found these?


class AgentFindingsSubmitter:
    """
    Modified agent that submits raw findings instead of making decisions.
    
    Replaces the old decision-making flow with a submission-based flow.
    """

    def __init__(self, agent_id: str, glyph: str, role: str):
        self.agent_id = agent_id
        self.glyph = glyph
        self.role = role
        self.findings_queue = []
        self.last_submission = None

    async def scan_and_collect_findings(self) -> List[Finding]:
        """
        Scan the environment and collect raw findings (no filtering, no decisions).
        
        Returns all observations, anomalies, opportunities, risks, patterns, metrics.
        """
        findings = []

        # Scan repository state
        repo_findings = await self._scan_repository()
        findings.extend(repo_findings)

        # Scan Chronicle for patterns
        chronicle_findings = await self._scan_chronicle()
        findings.extend(chronicle_findings)

        # Scan peer agents
        peer_findings = await self._scan_peers()
        findings.extend(peer_findings)

        # Scan system metrics
        metric_findings = await self._scan_metrics()
        findings.extend(metric_findings)

        return findings

    async def _scan_repository(self) -> List[Finding]:
        """Scan repository and return raw findings."""
        findings = []

        # Example: detect file changes
        finding = Finding(
            finding_id=self._generate_id("repo_change"),
            agent_id=self.agent_id,
            agent_glyph=self.glyph,
            finding_type=FindingType.OBSERVATION,
            severity=FindingSeverity.LOW,
            description="Repository files have been modified",
            location="repository/",
            evidence={
                "files_modified": 5,
                "files_added": 2,
                "files_deleted": 0,
                "last_change": datetime.now(timezone.utc).isoformat(),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            codon=self._encode_finding_codon("repo_change"),
        )
        findings.append(finding)

        # Example: detect test failures
        finding = Finding(
            finding_id=self._generate_id("test_failure"),
            agent_id=self.agent_id,
            agent_glyph=self.glyph,
            finding_type=FindingType.ANOMALY,
            severity=FindingSeverity.MEDIUM,
            description="Some tests are failing",
            location="tests/",
            evidence={
                "total_tests": 150,
                "passing": 145,
                "failing": 5,
                "failed_modules": ["module_a", "module_b"],
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            codon=self._encode_finding_codon("test_failure"),
        )
        findings.append(finding)

        return findings

    async def _scan_chronicle(self) -> List[Finding]:
        """Scan Chronicle for patterns and return findings."""
        findings = []

        # Example: detect recurring pattern
        finding = Finding(
            finding_id=self._generate_id("pattern_detected"),
            agent_id=self.agent_id,
            agent_glyph=self.glyph,
            finding_type=FindingType.PATTERN,
            severity=FindingSeverity.MEDIUM,
            description="Recurring pattern detected in agent decisions",
            location="chronicle/",
            evidence={
                "pattern_type": "optimization_followed_by_test",
                "occurrences": 7,
                "success_rate": 0.86,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            codon=self._encode_finding_codon("pattern"),
        )
        findings.append(finding)

        return findings

    async def _scan_peers(self) -> List[Finding]:
        """Scan other agents for their state and return findings."""
        findings = []

        # Example: detect peer agent state
        finding = Finding(
            finding_id=self._generate_id("peer_state"),
            agent_id=self.agent_id,
            agent_glyph=self.glyph,
            finding_type=FindingType.OBSERVATION,
            severity=FindingSeverity.LOW,
            description="Peer agents are active",
            location="agents/",
            evidence={
                "active_agents": 3,
                "idle_agents": 1,
                "total_cycles": 42,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            codon=self._encode_finding_codon("peer_state"),
        )
        findings.append(finding)

        return findings

    async def _scan_metrics(self) -> List[Finding]:
        """Scan system metrics and return findings."""
        findings = []

        # Example: detect performance metric
        finding = Finding(
            finding_id=self._generate_id("performance_metric"),
            agent_id=self.agent_id,
            agent_glyph=self.glyph,
            finding_type=FindingType.METRIC,
            severity=FindingSeverity.LOW,
            description="System performance metrics",
            location="system/",
            evidence={
                "cpu_usage": 0.35,
                "memory_usage": 0.42,
                "cycle_time_ms": 245,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            codon=self._encode_finding_codon("metric"),
        )
        findings.append(finding)

        return findings

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique finding ID."""
        data = f"{self.agent_id}:{prefix}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _encode_finding_codon(self, finding_type: str) -> str:
        """Encode a finding as a codon."""
        data = f"{self.glyph}:{finding_type}:{int(time.time())}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def submit_findings(self, findings: List[Finding]) -> FindingSubmission:
        """
        Submit raw findings to Adriana (no filtering, no decisions).
        
        This is the key change: agents submit findings, not decisions.
        """
        submission_id = hashlib.sha256(
            f"{self.agent_id}:{len(findings)}:{time.time()}".encode()
        ).hexdigest()[:16]

        submission = FindingSubmission(
            submission_id=submission_id,
            agent_id=self.agent_id,
            agent_glyph=self.glyph,
            findings=findings,
            submission_time=datetime.now(timezone.utc).isoformat(),
            agent_state="scanning_complete",
        )

        self.last_submission = submission
        self.findings_queue.append(submission)

        return submission

    async def cycle(self) -> FindingSubmission:
        """
        Complete one full cycle: scan → collect findings → submit.
        
        No decision-making. No execution. Just submission.
        """
        # Scan and collect findings
        findings = await self.scan_and_collect_findings()

        # Submit findings to Adriana
        submission = await self.submit_findings(findings)

        return submission


class FindingsAggregator:
    """
    Collects findings from all agents and prepares them for Adriana.
    
    This is the bridge between agents and Adriana's mesh.
    """

    def __init__(self):
        self.submissions: Dict[str, FindingSubmission] = {}
        self.aggregated_findings: List[Finding] = []

    async def collect_from_agents(
        self, agents: List[AgentFindingsSubmitter]
    ) -> Dict[str, Any]:
        """
        Collect findings from all agents.
        
        Returns aggregated findings ready for Adriana processing.
        """
        # Run all agent cycles in parallel
        tasks = [agent.cycle() for agent in agents]
        submissions = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate findings
        all_findings = []
        for submission in submissions:
            if isinstance(submission, FindingSubmission):
                self.submissions[submission.submission_id] = submission
                all_findings.extend(submission.findings)

        self.aggregated_findings = all_findings

        # Prepare for Adriana
        aggregated = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_count": len(agents),
            "total_findings": len(all_findings),
            "findings_by_type": self._group_by_type(all_findings),
            "findings_by_severity": self._group_by_severity(all_findings),
            "findings": [asdict(f) for f in all_findings],
            "submissions": {
                k: {
                    "agent_id": v.agent_id,
                    "agent_glyph": v.agent_glyph,
                    "finding_count": len(v.findings),
                    "submission_time": v.submission_time,
                }
                for k, v in self.submissions.items()
            },
        }

        return aggregated

    def _group_by_type(self, findings: List[Finding]) -> Dict[str, int]:
        """Group findings by type."""
        groups = {}
        for finding in findings:
            key = finding.finding_type.value
            groups[key] = groups.get(key, 0) + 1
        return groups

    def _group_by_severity(self, findings: List[Finding]) -> Dict[str, int]:
        """Group findings by severity."""
        groups = {}
        for finding in findings:
            key = finding.severity.name
            groups[key] = groups.get(key, 0) + 1
        return groups

    def get_adriana_input(self) -> Dict[str, Any]:
        """
        Format aggregated findings for Adriana's mesh input.
        
        This is what Adriana will process through Router → Research → Voice → Critic.
        """
        return {
            "findings": self.aggregated_findings,
            "aggregated_data": {
                "total_findings": len(self.aggregated_findings),
                "by_type": self._group_by_type(self.aggregated_findings),
                "by_severity": self._group_by_severity(self.aggregated_findings),
                "submissions": self.submissions,
            },
        }
