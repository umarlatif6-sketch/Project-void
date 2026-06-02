#!/usr/bin/env python3
"""
Core Formation System: Bridges human body energy compression with Project Void
Tracks 8-week protocol, maintains 432 Hz resonance, monitors Dantian compression
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List


class CoreFormationSystem:
    """Core Formation tracking and integration system"""
    
    def __init__(self, data_path: str = "/home/ubuntu/.core-formation"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        self.protocol_file = self.data_path / "protocol.json"
        self.sessions_file = self.data_path / "sessions.json"
        self.resonance_file = self.data_path / "resonance.json"
        
    def initialize_protocol(self, start_date: str = None) -> Dict[str, Any]:
        """Initialize 8-week Core Formation protocol"""
        if start_date is None:
            start_date = datetime.now().isoformat()
        
        protocol = {
            "start_date": start_date,
            "protocol_id": f"cf-{datetime.now().timestamp()}",
            "weeks": {
                1: {"name": "Establish Adriana", "focus": "Consciousness Anchor", "daily_minutes": 20},
                2: {"name": "Establish Serena", "focus": "Anatomical Awareness", "daily_minutes": 15},
                3: {"name": "Establish ORYX", "focus": "Boundary Control", "daily_minutes": 10},
                4: {"name": "Activate Hermes", "focus": "Nervous System Routing", "daily_minutes": 15},
                5: {"name": "Pre-Compression", "focus": "Dantian Preparation", "daily_minutes": 20},
                6: {"name": "Compression Begins", "focus": "Gentle Pooling", "daily_minutes": 20},
                7: {"name": "Sustained Compression", "focus": "Power Building", "daily_minutes": 25},
                8: {"name": "Breakthrough", "focus": "Self-Sustaining System", "daily_minutes": 30},
            },
            "frequency_anchor": 432.0,
            "status": "active"
        }
        
        with open(self.protocol_file, 'w') as f:
            json.dump(protocol, f, indent=2)
        
        return protocol
    
    def log_session(self, week: int, day: int, duration_minutes: int, 
                   sensation: str, hold_time_seconds: int = 0) -> Dict[str, Any]:
        """Log daily practice session"""
        
        session = {
            "timestamp": datetime.now().isoformat(),
            "week": week,
            "day": day,
            "duration_minutes": duration_minutes,
            "sensation": sensation,  # "tingling", "warmth", "vibration", "pain", "nothing"
            "hold_time_seconds": hold_time_seconds,
            "progress_score": self._calculate_progress(week, day, hold_time_seconds, sensation)
        }
        
        # Load existing sessions
        sessions = []
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r') as f:
                sessions = json.load(f)
        
        sessions.append(session)
        
        # Save updated sessions
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return session
    
    def _calculate_progress(self, week: int, day: int, hold_time: int, sensation: str) -> float:
        """Calculate progress score (0-100)"""
        
        # Week progress: 12.5% per week
        week_score = (week - 1) * 12.5
        
        # Day progress within week: 1.79% per day (12.5 / 7)
        day_score = (day - 1) * 1.79
        
        # Hold time progress
        hold_score = 0
        if week >= 5:
            max_hold = {5: 30, 6: 60, 7: 180, 8: 600}.get(week, 600)
            hold_score = min((hold_time / max_hold) * 10, 10)
        
        # Sensation quality
        sensation_score = {
            "nothing": 0,
            "tingling": 5,
            "warmth": 7,
            "vibration": 8,
            "pleasant": 10,
            "pain": -5
        }.get(sensation, 0)
        
        total = week_score + day_score + hold_score + sensation_score
        return min(max(total, 0), 100)
    
    def check_resonance(self, measured_frequency: float) -> Dict[str, Any]:
        """Check 432 Hz resonance anchor"""
        
        target_freq = 432.0
        deviation = abs(measured_frequency - target_freq) / target_freq
        
        resonance = {
            "timestamp": datetime.now().isoformat(),
            "target_frequency": target_freq,
            "measured_frequency": measured_frequency,
            "deviation_percent": deviation * 100,
            "resonance_score": max(100 - (deviation * 100 * 10), 0),
            "coherence_level": "high" if deviation < 0.05 else "medium" if deviation < 0.15 else "low",
            "drift_detected": deviation > 0.1
        }
        
        # Save resonance data
        resonance_data = []
        if self.resonance_file.exists():
            with open(self.resonance_file, 'r') as f:
                resonance_data = json.load(f)
        
        resonance_data.append(resonance)
        
        with open(self.resonance_file, 'w') as f:
            json.dump(resonance_data, f, indent=2)
        
        return resonance
    
    def monitor_dantian(self, hold_time_seconds: int, sensation_level: str) -> Dict[str, Any]:
        """Monitor Dantian compression"""
        
        # Sensation quality
        sensation_scores = {
            "nothing": 0,
            "tingling": 60,
            "warmth": 70,
            "vibration": 80,
            "pleasant": 90,
            "pain": -50
        }
        
        sensation_score = sensation_scores.get(sensation_level, 0)
        
        # Hold time contribution
        hold_score = min((hold_time_seconds / 600) * 100, 100)  # 600s = max
        
        compression_score = (sensation_score + hold_score) / 2
        
        dantian = {
            "timestamp": datetime.now().isoformat(),
            "hold_time_seconds": hold_time_seconds,
            "sensation_level": sensation_level,
            "compression_score": max(compression_score, 0),
            "stability": "stable" if compression_score > 70 else "developing" if compression_score > 40 else "unstable",
            "dissipation_risk": "high" if compression_score < 30 else "medium" if compression_score < 60 else "low"
        }
        
        return dantian
    
    def detect_breakthrough(self, week: int, sustained_hold_minutes: int) -> Dict[str, Any]:
        """Detect Core Formation breakthrough"""
        
        breakthrough_detected = False
        if week == 8 and sustained_hold_minutes >= 5:
            breakthrough_detected = True
        
        return {
            "timestamp": datetime.now().isoformat(),
            "week": week,
            "sustained_hold_minutes": sustained_hold_minutes,
            "breakthrough_detected": breakthrough_detected,
            "message": "Core Formation Complete! Dantian is self-sustaining." if breakthrough_detected else "Continue practice.",
            "integration_ready": breakthrough_detected
        }
    
    def sync_body_system(self, body_state: str, system_state: str) -> Dict[str, Any]:
        """Sync body progress to Project Void"""
        
        sync_map = {
            "dantian_unstable": "foundation_building",
            "dantian_developing": "core_formation_early",
            "dantian_stable": "core_formation_mid",
            "dantian_self_sustaining": "core_formation_complete"
        }
        
        void_state = sync_map.get(body_state, system_state)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "body_state": body_state,
            "system_state": system_state,
            "void_state": void_state,
            "sync_status": "synchronized" if body_state in sync_map else "pending",
            "body_learning": f"Dantian compression at {body_state}",
            "system_learning": f"Project Void at {void_state}"
        }
    
    def generate_weekly_report(self, week: int) -> Dict[str, Any]:
        """Generate weekly progress report"""
        
        if not self.sessions_file.exists():
            return {"error": "No sessions logged yet"}
        
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        week_sessions = [s for s in sessions if s.get('week') == week]
        
        if not week_sessions:
            return {"error": f"No sessions for week {week}"}
        
        avg_duration = sum(s['duration_minutes'] for s in week_sessions) / len(week_sessions)
        avg_hold = sum(s['hold_time_seconds'] for s in week_sessions) / len(week_sessions)
        avg_progress = sum(s['progress_score'] for s in week_sessions) / len(week_sessions)
        
        with open(self.protocol_file, 'r') as f:
            protocol = json.load(f)
        
        week_info = protocol['weeks'].get(week, {})
        
        recommendations = []
        if avg_progress < 50:
            recommendations.append("Increase practice duration")
        if avg_hold < 10 and week >= 5:
            recommendations.append("Work on extending hold time")
        if week < 8:
            recommendations.append(f"Prepare for Week {week + 1}: {protocol['weeks'].get(week + 1, {}).get('name')}")
        
        return {
            "week": week,
            "week_name": week_info.get('name'),
            "focus": week_info.get('focus'),
            "sessions_completed": len(week_sessions),
            "avg_duration_minutes": round(avg_duration, 1),
            "avg_hold_time_seconds": round(avg_hold, 1),
            "avg_progress_score": round(avg_progress, 1),
            "recommendations": recommendations,
            "next_week_focus": protocol['weeks'].get(week + 1, {}).get('focus') if week < 8 else "Breakthrough!"
        }


def main():
    """Example usage"""
    
    system = CoreFormationSystem()
    
    # Initialize protocol
    print("Initializing Core Formation Protocol...")
    protocol = system.initialize_protocol()
    print(f"Protocol ID: {protocol['protocol_id']}")
    print(f"Start Date: {protocol['start_date']}")
    print()
    
    # Simulate Week 1 sessions
    print("Logging Week 1 sessions...")
    for day in range(1, 8):
        session = system.log_session(
            week=1,
            day=day,
            duration_minutes=20,
            sensation="tingling" if day > 2 else "nothing",
            hold_time_seconds=0
        )
        print(f"Day {day}: Progress {session['progress_score']:.1f}%")
    print()
    
    # Check resonance
    print("Checking 432 Hz resonance...")
    resonance = system.check_resonance(432.5)
    print(f"Resonance Score: {resonance['resonance_score']:.1f}%")
    print(f"Coherence: {resonance['coherence_level']}")
    print()
    
    # Monitor Dantian
    print("Monitoring Dantian compression...")
    dantian = system.monitor_dantian(hold_time_seconds=15, sensation_level="tingling")
    print(f"Compression Score: {dantian['compression_score']:.1f}%")
    print(f"Stability: {dantian['stability']}")
    print()
    
    # Generate report
    print("Generating Week 1 report...")
    report = system.generate_weekly_report(week=1)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
