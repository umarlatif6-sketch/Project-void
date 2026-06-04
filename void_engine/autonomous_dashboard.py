"""
Autonomous Dashboard — PROJECT VOID

Real-time dashboard for monitoring autonomous nervous system activity.
Provides visibility into agent operations, system health, and recommendations.

Dashboard updates continuously and can be accessed via web interface or CLI.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class DashboardMetric:
    """Single dashboard metric."""
    name: str
    value: Any
    unit: str
    status: str  # NORMAL, WARNING, CRITICAL
    timestamp: str
    trend: str  # UP, DOWN, STABLE


class AutonomousDashboard:
    """Real-time dashboard for autonomous nervous system."""
    
    def __init__(self):
        self.dashboard_dir = Path('/home/ubuntu/Project-void/.nervous-system-logs/dashboard')
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_state: Dict[str, Any] = {
            'last_update': None,
            'current_cycle': 0,
            'system_status': 'INITIALIZING',
            'uptime_seconds': 0,
            'total_reports': 0,
            'latest_report': None,
            'metrics': {},
            'alerts': [],
            'recent_anomalies': [],
            'recommendations': [],
            'agent_status': {},
            'learning_patterns': [],
            'optimization_suggestions': [],
        }
    
    def update_system_status(self, status: str) -> None:
        """Update overall system status."""
        self.current_state['system_status'] = status
        self.current_state['last_update'] = datetime.now(timezone.utc).isoformat()
    
    def update_cycle(self, cycle_number: int) -> None:
        """Update current cycle number."""
        self.current_state['current_cycle'] = cycle_number
    
    def update_uptime(self, uptime_seconds: float) -> None:
        """Update system uptime."""
        self.current_state['uptime_seconds'] = uptime_seconds
    
    def add_metric(
        self,
        name: str,
        value: Any,
        unit: str,
        status: str = "NORMAL",
        trend: str = "STABLE"
    ) -> None:
        """Add or update a metric."""
        metric = {
            'value': value,
            'unit': unit,
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'trend': trend,
        }
        self.current_state['metrics'][name] = metric
    
    def add_alert(
        self,
        severity: str,
        message: str,
        agent_id: Optional[str] = None
    ) -> None:
        """Add an alert to the dashboard."""
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': severity,
            'message': message,
            'agent_id': agent_id,
        }
        self.current_state['alerts'].append(alert)
        
        # Keep only last 50 alerts
        if len(self.current_state['alerts']) > 50:
            self.current_state['alerts'] = self.current_state['alerts'][-50:]
    
    def add_anomaly(
        self,
        anomaly_type: str,
        description: str,
        severity: str,
        agent_id: str
    ) -> None:
        """Add a recent anomaly."""
        anomaly = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': anomaly_type,
            'description': description,
            'severity': severity,
            'agent_id': agent_id,
        }
        self.current_state['recent_anomalies'].append(anomaly)
        
        # Keep only last 20 anomalies
        if len(self.current_state['recent_anomalies']) > 20:
            self.current_state['recent_anomalies'] = self.current_state['recent_anomalies'][-20:]
    
    def add_recommendation(
        self,
        category: str,
        description: str,
        priority: str,
        impact: str
    ) -> None:
        """Add a recommendation."""
        rec = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'category': category,
            'description': description,
            'priority': priority,
            'impact': impact,
        }
        self.current_state['recommendations'].append(rec)
        
        # Keep only last 30 recommendations
        if len(self.current_state['recommendations']) > 30:
            self.current_state['recommendations'] = self.current_state['recommendations'][-30:]
    
    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        last_activity: str,
        cycles_completed: int
    ) -> None:
        """Update status of a specific agent."""
        self.current_state['agent_status'][agent_id] = {
            'status': status,
            'last_activity': last_activity,
            'cycles_completed': cycles_completed,
            'last_update': datetime.now(timezone.utc).isoformat(),
        }
    
    def set_latest_report(self, report: Dict[str, Any]) -> None:
        """Set the latest report."""
        self.current_state['latest_report'] = report
        self.current_state['total_reports'] = report.get('summary', {}).get('cycle_number', 0)
    
    def add_learning_pattern(self, pattern: Dict[str, Any]) -> None:
        """Add a learned pattern."""
        self.current_state['learning_patterns'].append(pattern)
        
        # Keep only last 10 patterns
        if len(self.current_state['learning_patterns']) > 10:
            self.current_state['learning_patterns'] = self.current_state['learning_patterns'][-10:]
    
    def add_optimization_suggestion(self, suggestion: str) -> None:
        """Add an optimization suggestion."""
        if suggestion not in self.current_state['optimization_suggestions']:
            self.current_state['optimization_suggestions'].append(suggestion)
        
        # Keep only last 10 suggestions
        if len(self.current_state['optimization_suggestions']) > 10:
            self.current_state['optimization_suggestions'] = self.current_state['optimization_suggestions'][-10:]
    
    def get_health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # Deduct for alerts
        critical_alerts = len([a for a in self.current_state['alerts'] if a['severity'] == 'CRITICAL'])
        high_alerts = len([a for a in self.current_state['alerts'] if a['severity'] == 'HIGH'])
        
        score -= critical_alerts * 10
        score -= high_alerts * 5
        
        # Deduct for anomalies
        critical_anomalies = len([a for a in self.current_state['recent_anomalies'] if a['severity'] == 'CRITICAL'])
        high_anomalies = len([a for a in self.current_state['recent_anomalies'] if a['severity'] == 'HIGH'])
        
        score -= critical_anomalies * 8
        score -= high_anomalies * 3
        
        # Adjust for system status
        if self.current_state['system_status'] == 'CRITICAL':
            score -= 20
        elif self.current_state['system_status'] == 'DEGRADED':
            score -= 10
        
        return max(0, min(100, score))
    
    def save_to_file(self) -> Path:
        """Save dashboard state to file."""
        self.current_state['last_update'] = datetime.now(timezone.utc).isoformat()
        self.current_state['health_score'] = self.get_health_score()
        
        filepath = self.dashboard_dir / 'current_state.json'
        with open(filepath, 'w') as f:
            json.dump(self.current_state, f, indent=2, default=str)
        
        return filepath
    
    def get_summary(self) -> Dict[str, Any]:
        """Get dashboard summary."""
        return {
            'system_status': self.current_state['system_status'],
            'current_cycle': self.current_state['current_cycle'],
            'uptime_seconds': self.current_state['uptime_seconds'],
            'health_score': self.get_health_score(),
            'total_reports': self.current_state['total_reports'],
            'active_alerts': len(self.current_state['alerts']),
            'recent_anomalies': len(self.current_state['recent_anomalies']),
            'pending_recommendations': len(self.current_state['recommendations']),
            'agents_online': len(self.current_state['agent_status']),
            'last_update': self.current_state['last_update'],
        }
    
    def to_html(self) -> str:
        """Generate HTML dashboard."""
        summary = self.get_summary()
        health_score = summary['health_score']
        health_color = 'green' if health_score >= 80 else 'orange' if health_score >= 50 else 'red'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Project Void - Autonomous Dashboard</title>
    <style>
        body {{
            font-family: monospace;
            background-color: #0a0e27;
            color: #00ff00;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .card {{
            border: 1px solid #00ff00;
            padding: 15px;
            background-color: #0f1535;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 1px solid #003300;
        }}
        .metric-name {{
            flex: 1;
        }}
        .metric-value {{
            font-weight: bold;
            color: #00ff00;
        }}
        .status-operational {{
            color: #00ff00;
        }}
        .status-degraded {{
            color: #ffff00;
        }}
        .status-critical {{
            color: #ff0000;
        }}
        .health-bar {{
            width: 100%;
            height: 30px;
            background-color: #003300;
            border: 1px solid #00ff00;
            position: relative;
            margin: 10px 0;
        }}
        .health-fill {{
            height: 100%;
            background-color: {health_color};
            width: {health_score}%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: black;
            font-weight: bold;
        }}
        .alert {{
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid;
        }}
        .alert-critical {{
            border-left-color: #ff0000;
            background-color: #330000;
        }}
        .alert-high {{
            border-left-color: #ffff00;
            background-color: #333300;
        }}
        .alert-medium {{
            border-left-color: #ffaa00;
            background-color: #332200;
        }}
        .timestamp {{
            color: #00aa00;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PROJECT VOID — AUTONOMOUS DASHBOARD</h1>
            <p>Real-time Nervous System Monitor</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>System Status</h3>
                <div class="metric">
                    <span class="metric-name">Status:</span>
                    <span class="metric-value status-{summary['system_status'].lower()}">{summary['system_status']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Health Score:</span>
                    <span class="metric-value">{health_score:.1f}%</span>
                </div>
                <div class="health-bar">
                    <div class="health-fill">{health_score:.0f}%</div>
                </div>
                <div class="metric">
                    <span class="metric-name">Current Cycle:</span>
                    <span class="metric-value">#{summary['current_cycle']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Uptime:</span>
                    <span class="metric-value">{summary['uptime_seconds'] / 3600:.1f}h</span>
                </div>
            </div>
            
            <div class="card">
                <h3>Activity</h3>
                <div class="metric">
                    <span class="metric-name">Total Reports:</span>
                    <span class="metric-value">{summary['total_reports']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Active Alerts:</span>
                    <span class="metric-value">{summary['active_alerts']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Recent Anomalies:</span>
                    <span class="metric-value">{summary['recent_anomalies']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Pending Recommendations:</span>
                    <span class="metric-value">{summary['pending_recommendations']}</span>
                </div>
                <div class="metric">
                    <span class="metric-name">Agents Online:</span>
                    <span class="metric-value">{summary['agents_online']}</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>Recent Alerts</h3>
            {self._render_alerts_html()}
        </div>
        
        <div style="text-align: center; margin-top: 40px; color: #00aa00;">
            <p>Last Updated: <span class="timestamp">{summary['last_update']}</span></p>
            <p>432.0 Hz Eternal — Project Void Autonomous System</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _render_alerts_html(self) -> str:
        """Render alerts as HTML."""
        if not self.current_state['alerts']:
            return '<p style="color: #00aa00;">No alerts</p>'
        
        html = ''
        for alert in self.current_state['alerts'][-10:]:  # Last 10 alerts
            severity_class = f"alert-{alert['severity'].lower()}"
            html += f"""
            <div class="alert {severity_class}">
                <strong>[{alert['severity']}]</strong> {alert['message']}
                <div class="timestamp">{alert['timestamp']}</div>
            </div>
            """
        
        return html
    
    def save_html_dashboard(self) -> Path:
        """Save HTML dashboard to file."""
        filepath = self.dashboard_dir / 'dashboard.html'
        with open(filepath, 'w') as f:
            f.write(self.to_html())
        
        return filepath


# Example usage
if __name__ == "__main__":
    dashboard = AutonomousDashboard()
    
    # Update dashboard
    dashboard.update_system_status('OPERATIONAL')
    dashboard.update_cycle(42)
    dashboard.update_uptime(151200)  # 42 hours
    
    # Add metrics
    dashboard.add_metric('cpu_usage', 45.2, '%', 'NORMAL', 'STABLE')
    dashboard.add_metric('memory_usage', 62.1, '%', 'NORMAL', 'UP')
    dashboard.add_metric('agent_count', 4, 'agents', 'NORMAL', 'STABLE')
    
    # Add alerts
    dashboard.add_alert('INFO', 'System initialized', 'system')
    dashboard.add_alert('INFO', 'Cycle 42 completed', 'agent-001')
    
    # Add recommendation
    dashboard.add_recommendation(
        'optimization',
        'Consider optimizing memory usage',
        'LOW',
        '5-10% improvement'
    )
    
    # Update agent status
    dashboard.update_agent_status('agent-001', 'ACTIVE', '2026-06-04T12:00:00Z', 42)
    dashboard.update_agent_status('agent-002', 'ACTIVE', '2026-06-04T12:00:00Z', 42)
    dashboard.update_agent_status('agent-003', 'ACTIVE', '2026-06-04T12:00:00Z', 42)
    dashboard.update_agent_status('agent-004', 'ACTIVE', '2026-06-04T12:00:00Z', 42)
    
    # Save dashboard
    dashboard.save_to_file()
    dashboard.save_html_dashboard()
    
    print("Dashboard saved!")
    print(f"Summary: {dashboard.get_summary()}")
