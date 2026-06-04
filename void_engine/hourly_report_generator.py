"""
Hourly Report Generator — PROJECT VOID

Generates comprehensive hourly reports from agent activities.
Includes metrics, observations, decisions, actions, and recommendations.

Reports are structured for both human reading and machine processing.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ReportSeverity(Enum):
    """Severity levels for anomalies and issues."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ReportStatus(Enum):
    """Overall system status."""
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    RECOVERING = "RECOVERING"


@dataclass
class Observation:
    """Single observation from an agent."""
    timestamp: str
    agent_id: str
    category: str
    description: str
    confidence: float  # 0.0 - 1.0
    data: Optional[Dict[str, Any]] = None


@dataclass
class Decision:
    """Single decision made by an agent."""
    timestamp: str
    agent_id: str
    decision_type: str
    rationale: str
    confidence: float  # 0.0 - 1.0
    action_required: bool
    priority: str  # HIGH, MEDIUM, LOW


@dataclass
class Action:
    """Single action executed by an agent."""
    timestamp: str
    agent_id: str
    action_type: str
    description: str
    status: str  # COMPLETED, PENDING, FAILED
    result: Optional[Dict[str, Any]] = None


@dataclass
class Anomaly:
    """Single anomaly detected by the system."""
    timestamp: str
    agent_id: str
    anomaly_type: str
    description: str
    severity: str
    impact: str
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class Recommendation:
    """Single recommendation for system improvement."""
    timestamp: str
    category: str
    description: str
    priority: str  # HIGH, MEDIUM, LOW
    estimated_impact: str
    implementation_effort: str  # LOW, MEDIUM, HIGH


@dataclass
class Metric:
    """Single system metric."""
    name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    status: str = "NORMAL"  # NORMAL, WARNING, CRITICAL


class HourlyReportGenerator:
    """Generates comprehensive hourly reports."""
    
    def __init__(self, cycle_number: int):
        self.cycle_number = cycle_number
        self.timestamp = datetime.now(timezone.utc)
        self.status = ReportStatus.OPERATIONAL
        self.observations: List[Observation] = []
        self.decisions: List[Decision] = []
        self.actions: List[Action] = []
        self.anomalies: List[Anomaly] = []
        self.recommendations: List[Recommendation] = []
        self.metrics: List[Metric] = []
        self.escalations: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {}
    
    def add_observation(
        self,
        agent_id: str,
        category: str,
        description: str,
        confidence: float = 0.8,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an observation to the report."""
        obs = Observation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            category=category,
            description=description,
            confidence=confidence,
            data=data,
        )
        self.observations.append(obs)
    
    def add_decision(
        self,
        agent_id: str,
        decision_type: str,
        rationale: str,
        confidence: float = 0.8,
        action_required: bool = False,
        priority: str = "MEDIUM"
    ) -> None:
        """Add a decision to the report."""
        decision = Decision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            decision_type=decision_type,
            rationale=rationale,
            confidence=confidence,
            action_required=action_required,
            priority=priority,
        )
        self.decisions.append(decision)
    
    def add_action(
        self,
        agent_id: str,
        action_type: str,
        description: str,
        status: str = "COMPLETED",
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an action to the report."""
        action = Action(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            status=status,
            result=result,
        )
        self.actions.append(action)
    
    def add_anomaly(
        self,
        agent_id: str,
        anomaly_type: str,
        description: str,
        severity: str = "MEDIUM",
        impact: str = "UNKNOWN",
        root_cause: Optional[str] = None,
        suggested_fix: Optional[str] = None
    ) -> None:
        """Add an anomaly to the report."""
        anomaly = Anomaly(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            anomaly_type=anomaly_type,
            description=description,
            severity=severity,
            impact=impact,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
        )
        self.anomalies.append(anomaly)
        
        # Check if escalation is needed
        if severity in ["CRITICAL", "HIGH"]:
            self._create_escalation(anomaly)
    
    def add_recommendation(
        self,
        category: str,
        description: str,
        priority: str = "MEDIUM",
        estimated_impact: str = "UNKNOWN",
        implementation_effort: str = "MEDIUM"
    ) -> None:
        """Add a recommendation to the report."""
        rec = Recommendation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=category,
            description=description,
            priority=priority,
            estimated_impact=estimated_impact,
            implementation_effort=implementation_effort,
        )
        self.recommendations.append(rec)
    
    def add_metric(
        self,
        name: str,
        value: float,
        unit: str,
        threshold: Optional[float] = None
    ) -> None:
        """Add a metric to the report."""
        status = "NORMAL"
        if threshold and value > threshold:
            status = "WARNING"
            if value > threshold * 1.2:
                status = "CRITICAL"
        
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            threshold=threshold,
            status=status,
        )
        self.metrics.append(metric)
    
    def _create_escalation(self, anomaly: Anomaly) -> None:
        """Create escalation for critical anomalies."""
        escalation = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'anomaly_id': f"{anomaly.agent_id}_{anomaly.anomaly_type}",
            'severity': anomaly.severity,
            'description': anomaly.description,
            'agent_id': anomaly.agent_id,
            'action_required': True,
        }
        self.escalations.append(escalation)
    
    def set_status(self, status: ReportStatus) -> None:
        """Set overall system status."""
        self.status = status
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate report summary."""
        self.summary = {
            'cycle_number': self.cycle_number,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'total_observations': len(self.observations),
            'total_decisions': len(self.decisions),
            'total_actions': len(self.actions),
            'total_anomalies': len(self.anomalies),
            'total_recommendations': len(self.recommendations),
            'total_metrics': len(self.metrics),
            'total_escalations': len(self.escalations),
            'critical_anomalies': len([a for a in self.anomalies if a.severity == "CRITICAL"]),
            'high_priority_recommendations': len([r for r in self.recommendations if r.priority == "HIGH"]),
        }
        return self.summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        self.generate_summary()
        
        return {
            'summary': self.summary,
            'observations': [asdict(o) for o in self.observations],
            'decisions': [asdict(d) for d in self.decisions],
            'actions': [asdict(a) for a in self.actions],
            'anomalies': [asdict(a) for a in self.anomalies],
            'recommendations': [asdict(r) for r in self.recommendations],
            'metrics': [asdict(m) for m in self.metrics],
            'escalations': self.escalations,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_human_readable(self) -> str:
        """Convert report to human-readable format."""
        lines = []
        
        lines.append("=" * 80)
        lines.append(f"HOURLY REPORT #{self.cycle_number}")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {self.timestamp.isoformat()}")
        lines.append(f"Status: {self.status.value}")
        lines.append("")
        
        # Summary
        summary = self.generate_summary()
        lines.append("SUMMARY")
        lines.append("-" * 80)
        for key, value in summary.items():
            if key not in ['cycle_number', 'timestamp', 'status']:
                lines.append(f"  {key}: {value}")
        lines.append("")
        
        # Observations
        if self.observations:
            lines.append("OBSERVATIONS")
            lines.append("-" * 80)
            for obs in self.observations:
                lines.append(f"  [{obs.agent_id}] {obs.category}: {obs.description}")
                lines.append(f"    Confidence: {obs.confidence:.1%}")
            lines.append("")
        
        # Decisions
        if self.decisions:
            lines.append("DECISIONS")
            lines.append("-" * 80)
            for dec in self.decisions:
                lines.append(f"  [{dec.agent_id}] {dec.decision_type} ({dec.priority})")
                lines.append(f"    Rationale: {dec.rationale}")
                lines.append(f"    Action Required: {dec.action_required}")
            lines.append("")
        
        # Actions
        if self.actions:
            lines.append("ACTIONS")
            lines.append("-" * 80)
            for act in self.actions:
                lines.append(f"  [{act.agent_id}] {act.action_type}: {act.description}")
                lines.append(f"    Status: {act.status}")
            lines.append("")
        
        # Anomalies
        if self.anomalies:
            lines.append("ANOMALIES")
            lines.append("-" * 80)
            for anom in self.anomalies:
                lines.append(f"  [{anom.severity}] {anom.anomaly_type}")
                lines.append(f"    Agent: {anom.agent_id}")
                lines.append(f"    Description: {anom.description}")
                if anom.suggested_fix:
                    lines.append(f"    Suggested Fix: {anom.suggested_fix}")
            lines.append("")
        
        # Recommendations
        if self.recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)
            for rec in self.recommendations:
                lines.append(f"  [{rec.priority}] {rec.category}: {rec.description}")
                lines.append(f"    Impact: {rec.estimated_impact}")
                lines.append(f"    Effort: {rec.implementation_effort}")
            lines.append("")
        
        # Metrics
        if self.metrics:
            lines.append("METRICS")
            lines.append("-" * 80)
            for metric in self.metrics:
                status_indicator = "✓" if metric.status == "NORMAL" else "⚠" if metric.status == "WARNING" else "✗"
                lines.append(f"  {status_indicator} {metric.name}: {metric.value} {metric.unit}")
                if metric.threshold:
                    lines.append(f"    Threshold: {metric.threshold} {metric.unit}")
            lines.append("")
        
        # Escalations
        if self.escalations:
            lines.append("ESCALATIONS")
            lines.append("-" * 80)
            for esc in self.escalations:
                lines.append(f"  [{esc['severity']}] {esc['description']}")
                lines.append(f"    Agent: {esc['agent_id']}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Create a report
    report = HourlyReportGenerator(cycle_number=1)
    
    # Add observations
    report.add_observation(
        agent_id="agent-001",
        category="system_health",
        description="All systems operational",
        confidence=0.95
    )
    
    # Add decisions
    report.add_decision(
        agent_id="agent-001",
        decision_type="continue_monitoring",
        rationale="System health is good",
        confidence=0.9,
        priority="LOW"
    )
    
    # Add actions
    report.add_action(
        agent_id="agent-001",
        action_type="health_check",
        description="Performed system health check",
        status="COMPLETED"
    )
    
    # Add metrics
    report.add_metric("cpu_usage", 45.2, "%", threshold=80)
    report.add_metric("memory_usage", 62.1, "%", threshold=85)
    
    # Add recommendation
    report.add_recommendation(
        category="optimization",
        description="Consider optimizing memory usage",
        priority="LOW",
        estimated_impact="5-10% improvement",
        implementation_effort="LOW"
    )
    
    # Print human-readable report
    print(report.to_human_readable())
    
    # Print JSON report
    print("\n\nJSON Report:")
    print(report.to_json())
