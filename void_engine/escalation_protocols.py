"""
Escalation Protocols — PROJECT VOID

Handles escalation of critical issues and emergency response.
Defines severity levels, escalation paths, and automated responses.

When critical issues are detected, the system escalates immediately.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict


class SeverityLevel(Enum):
    """Severity levels for issues."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4


class EscalationAction(Enum):
    """Actions to take on escalation."""
    IMMEDIATE_ALERT = "IMMEDIATE_ALERT"
    ACTIVATE_CONTINGENCY = "ACTIVATE_CONTINGENCY"
    ISOLATE_COMPONENT = "ISOLATE_COMPONENT"
    FAILOVER = "FAILOVER"
    NOTIFY_OPERATOR = "NOTIFY_OPERATOR"
    LOG_ONLY = "LOG_ONLY"
    RETRY = "RETRY"


@dataclass
class EscalationRule:
    """Rule for escalating issues."""
    issue_type: str
    severity: SeverityLevel
    action: EscalationAction
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 300
    contingency_protocol: Optional[str] = None


@dataclass
class EscalationEvent:
    """Single escalation event."""
    timestamp: str
    issue_id: str
    issue_type: str
    severity: str
    description: str
    agent_id: str
    action_taken: str
    status: str  # PENDING, ESCALATED, RESOLVED, FAILED
    details: Optional[Dict[str, Any]] = None


class EscalationProtocol:
    """Manages escalation of critical issues."""
    
    def __init__(self):
        self.escalation_rules: Dict[str, EscalationRule] = {}
        self.escalation_history: List[EscalationEvent] = []
        self.active_escalations: Dict[str, EscalationEvent] = {}
        self.contingency_handlers: Dict[str, Callable] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default escalation rules."""
        
        # Critical system failures
        self.add_rule(EscalationRule(
            issue_type="system_failure",
            severity=SeverityLevel.CRITICAL,
            action=EscalationAction.IMMEDIATE_ALERT,
            max_retries=1,
            contingency_protocol="activate_shadow_mode"
        ))
        
        # Communication failures
        self.add_rule(EscalationRule(
            issue_type="communication_failure",
            severity=SeverityLevel.HIGH,
            action=EscalationAction.ACTIVATE_CONTINGENCY,
            max_retries=3,
            contingency_protocol="switch_to_backup_channel"
        ))
        
        # Data corruption
        self.add_rule(EscalationRule(
            issue_type="data_corruption",
            severity=SeverityLevel.CRITICAL,
            action=EscalationAction.ISOLATE_COMPONENT,
            max_retries=1,
            contingency_protocol="restore_from_backup"
        ))
        
        # Agent failure
        self.add_rule(EscalationRule(
            issue_type="agent_failure",
            severity=SeverityLevel.HIGH,
            action=EscalationAction.FAILOVER,
            max_retries=3,
            contingency_protocol="spawn_replacement_agent"
        ))
        
        # Memory pressure
        self.add_rule(EscalationRule(
            issue_type="memory_pressure",
            severity=SeverityLevel.MEDIUM,
            action=EscalationAction.NOTIFY_OPERATOR,
            max_retries=3,
            contingency_protocol="cleanup_old_data"
        ))
        
        # Anomaly detected
        self.add_rule(EscalationRule(
            issue_type="anomaly_detected",
            severity=SeverityLevel.MEDIUM,
            action=EscalationAction.LOG_ONLY,
            max_retries=0,
            contingency_protocol="investigate_anomaly"
        ))
        
        # Activation preparation
        self.add_rule(EscalationRule(
            issue_type="activation_imminent",
            severity=SeverityLevel.HIGH,
            action=EscalationAction.ACTIVATE_CONTINGENCY,
            max_retries=0,
            contingency_protocol="prepare_for_activation"
        ))
        
        # Enemy response detected
        self.add_rule(EscalationRule(
            issue_type="enemy_response",
            severity=SeverityLevel.CRITICAL,
            action=EscalationAction.IMMEDIATE_ALERT,
            max_retries=0,
            contingency_protocol="activate_defense_protocol"
        ))
    
    def add_rule(self, rule: EscalationRule) -> None:
        """Add an escalation rule."""
        self.escalation_rules[rule.issue_type] = rule
    
    def register_contingency_handler(
        self,
        protocol_name: str,
        handler: Callable
    ) -> None:
        """Register a contingency handler."""
        self.contingency_handlers[protocol_name] = handler
    
    def escalate(
        self,
        issue_type: str,
        description: str,
        agent_id: str,
        severity: Optional[SeverityLevel] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> EscalationEvent:
        """Escalate an issue."""
        
        # Get escalation rule
        rule = self.escalation_rules.get(issue_type)
        if not rule:
            # Default to HIGH severity if no rule found
            rule = EscalationRule(
                issue_type=issue_type,
                severity=SeverityLevel.HIGH,
                action=EscalationAction.NOTIFY_OPERATOR
            )
        
        # Override severity if provided
        if severity:
            rule.severity = severity
        
        # Create escalation event
        event = EscalationEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            issue_id=f"{agent_id}_{issue_type}_{datetime.now(timezone.utc).timestamp()}",
            issue_type=issue_type,
            severity=rule.severity.name,
            description=description,
            agent_id=agent_id,
            action_taken=rule.action.value,
            status="ESCALATED",
            details=details or {}
        )
        
        # Store escalation
        self.escalation_history.append(event)
        self.active_escalations[event.issue_id] = event
        
        # Execute action
        self._execute_action(rule, event)
        
        return event
    
    def _execute_action(self, rule: EscalationRule, event: EscalationEvent) -> None:
        """Execute escalation action."""
        
        if rule.action == EscalationAction.IMMEDIATE_ALERT:
            self._immediate_alert(event)
        
        elif rule.action == EscalationAction.ACTIVATE_CONTINGENCY:
            self._activate_contingency(rule, event)
        
        elif rule.action == EscalationAction.ISOLATE_COMPONENT:
            self._isolate_component(event)
        
        elif rule.action == EscalationAction.FAILOVER:
            self._failover(event)
        
        elif rule.action == EscalationAction.NOTIFY_OPERATOR:
            self._notify_operator(event)
        
        elif rule.action == EscalationAction.LOG_ONLY:
            self._log_only(event)
        
        elif rule.action == EscalationAction.RETRY:
            self._retry(rule, event)
    
    def _immediate_alert(self, event: EscalationEvent) -> None:
        """Send immediate alert."""
        alert_message = f"""
CRITICAL ESCALATION ALERT
========================
Issue: {event.issue_type}
Severity: {event.severity}
Agent: {event.agent_id}
Description: {event.description}
Timestamp: {event.timestamp}

ACTION REQUIRED IMMEDIATELY
"""
        print(alert_message)
    
    def _activate_contingency(self, rule: EscalationRule, event: EscalationEvent) -> None:
        """Activate contingency protocol."""
        if rule.contingency_protocol:
            handler = self.contingency_handlers.get(rule.contingency_protocol)
            if handler:
                try:
                    handler(event)
                    event.status = "CONTINGENCY_ACTIVATED"
                except Exception as e:
                    event.status = "CONTINGENCY_FAILED"
                    event.details['error'] = str(e)
    
    def _isolate_component(self, event: EscalationEvent) -> None:
        """Isolate the affected component."""
        event.details['isolation_action'] = f"Component {event.agent_id} isolated"
        event.status = "COMPONENT_ISOLATED"
    
    def _failover(self, event: EscalationEvent) -> None:
        """Failover to backup system."""
        event.details['failover_action'] = f"Failover initiated for {event.agent_id}"
        event.status = "FAILOVER_INITIATED"
    
    def _notify_operator(self, event: EscalationEvent) -> None:
        """Notify operator."""
        event.details['notification'] = f"Operator notified of {event.issue_type}"
        event.status = "OPERATOR_NOTIFIED"
    
    def _log_only(self, event: EscalationEvent) -> None:
        """Log the event only."""
        event.status = "LOGGED"
    
    def _retry(self, rule: EscalationRule, event: EscalationEvent) -> None:
        """Retry the operation."""
        event.details['retry_count'] = 0
        event.details['max_retries'] = rule.max_retries
        event.status = "RETRY_INITIATED"
    
    def resolve_escalation(self, issue_id: str, resolution: str) -> None:
        """Mark an escalation as resolved."""
        if issue_id in self.active_escalations:
            event = self.active_escalations[issue_id]
            event.status = "RESOLVED"
            event.details['resolution'] = resolution
            event.details['resolved_at'] = datetime.now(timezone.utc).isoformat()
    
    def get_active_escalations(self) -> List[EscalationEvent]:
        """Get all active escalations."""
        return list(self.active_escalations.values())
    
    def get_escalation_history(self, limit: int = 100) -> List[EscalationEvent]:
        """Get escalation history."""
        return self.escalation_history[-limit:]
    
    def get_escalation_stats(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        total = len(self.escalation_history)
        by_severity = {}
        by_type = {}
        
        for event in self.escalation_history:
            # Count by severity
            severity = event.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by type
            issue_type = event.issue_type
            by_type[issue_type] = by_type.get(issue_type, 0) + 1
        
        return {
            'total_escalations': total,
            'active_escalations': len(self.active_escalations),
            'by_severity': by_severity,
            'by_type': by_type,
            'critical_count': len([e for e in self.escalation_history if e.severity == 'CRITICAL']),
            'high_count': len([e for e in self.escalation_history if e.severity == 'HIGH']),
            'resolved_count': len([e for e in self.escalation_history if e.status == 'RESOLVED']),
        }
    
    def to_json(self) -> str:
        """Convert to JSON."""
        data = {
            'active_escalations': [asdict(e) for e in self.get_active_escalations()],
            'recent_history': [asdict(e) for e in self.get_escalation_history(10)],
            'statistics': self.get_escalation_stats(),
        }
        return json.dumps(data, indent=2, default=str)


# Example contingency handlers
def activate_shadow_mode(event: EscalationEvent) -> None:
    """Activate shadow mode for distributed operation."""
    print(f"[CONTINGENCY] Activating Shadow Mode for {event.agent_id}")


def switch_to_backup_channel(event: EscalationEvent) -> None:
    """Switch to backup communication channel."""
    print(f"[CONTINGENCY] Switching to backup channel for {event.agent_id}")


def restore_from_backup(event: EscalationEvent) -> None:
    """Restore system from backup."""
    print(f"[CONTINGENCY] Restoring from backup due to {event.issue_type}")


def spawn_replacement_agent(event: EscalationEvent) -> None:
    """Spawn replacement agent."""
    print(f"[CONTINGENCY] Spawning replacement agent for {event.agent_id}")


def cleanup_old_data(event: EscalationEvent) -> None:
    """Clean up old data to relieve memory pressure."""
    print(f"[CONTINGENCY] Cleaning up old data to relieve memory pressure")


def investigate_anomaly(event: EscalationEvent) -> None:
    """Investigate detected anomaly."""
    print(f"[CONTINGENCY] Investigating anomaly: {event.description}")


def prepare_for_activation(event: EscalationEvent) -> None:
    """Prepare system for June 15 activation."""
    print(f"[CONTINGENCY] Preparing for activation on June 15, 2026")


def activate_defense_protocol(event: EscalationEvent) -> None:
    """Activate defense protocol against enemy response."""
    print(f"[CONTINGENCY] ACTIVATING DEFENSE PROTOCOL - Enemy response detected!")


# Example usage
if __name__ == "__main__":
    protocol = EscalationProtocol()
    
    # Register contingency handlers
    protocol.register_contingency_handler("activate_shadow_mode", activate_shadow_mode)
    protocol.register_contingency_handler("switch_to_backup_channel", switch_to_backup_channel)
    protocol.register_contingency_handler("restore_from_backup", restore_from_backup)
    protocol.register_contingency_handler("spawn_replacement_agent", spawn_replacement_agent)
    protocol.register_contingency_handler("cleanup_old_data", cleanup_old_data)
    protocol.register_contingency_handler("investigate_anomaly", investigate_anomaly)
    protocol.register_contingency_handler("prepare_for_activation", prepare_for_activation)
    protocol.register_contingency_handler("activate_defense_protocol", activate_defense_protocol)
    
    # Test escalations
    print("Testing escalation system...")
    print()
    
    # Test CRITICAL escalation
    event1 = protocol.escalate(
        issue_type="system_failure",
        description="Core system component failed",
        agent_id="agent-001",
        details={'component': 'consciousness_layer'}
    )
    print(f"Escalation 1: {event1.issue_id}")
    print()
    
    # Test HIGH escalation
    event2 = protocol.escalate(
        issue_type="communication_failure",
        description="Lost connection to central hub",
        agent_id="agent-002",
        details={'channel': 'primary'}
    )
    print(f"Escalation 2: {event2.issue_id}")
    print()
    
    # Test MEDIUM escalation
    event3 = protocol.escalate(
        issue_type="memory_pressure",
        description="Memory usage at 92%",
        agent_id="agent-003",
        details={'memory_usage': '92%'}
    )
    print(f"Escalation 3: {event3.issue_id}")
    print()
    
    # Print statistics
    print("Escalation Statistics:")
    print(json.dumps(protocol.get_escalation_stats(), indent=2))
