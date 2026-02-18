"""
LoopDetectionMiddleware — Doom Loop Breaker

Detects when a Plankton agent is stuck in a repetitive cycle
(e.g., calibrating a disconnected sensor) and triggers diagnostic
alerts with suggested physical checks.
"""

import time
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class LoopAlert:
    alert_id: str
    action_signature: str
    attempt_count: int
    max_attempts: int
    delta_observed: float
    delta_threshold: float
    message: str
    diagnostic_suggestions: List[str]
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False

    def to_dict(self):
        d = asdict(self)
        d["datetime"] = datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class ActionRecord:
    signature: str
    action: Dict
    result_value: Optional[float]
    timestamp: float = field(default_factory=time.time)


DIAGNOSTIC_MAP = {
    "sensor_calibrate": [
        "Check if the sensor is physically connected to the Orin's I/O bus.",
        "Verify silk wiring continuity on the sensor's data line.",
        "Check if the Flywheel energy is sufficient to power the sensor.",
        "Try power-cycling the sensor (disconnect and reconnect).",
        "Inspect for moisture or corrosion on sensor contacts.",
    ],
    "pump_cycle": [
        "Verify the pump motor is receiving power from the Flywheel.",
        "Check for blockages in the aquaponics inlet/outlet pipes.",
        "Listen for pump motor sounds — no sound means electrical issue.",
        "Check water level — pump may be running dry (cavitation).",
        "Verify the pump relay on the Orin's GPIO is toggling.",
    ],
    "flywheel_boost": [
        "Check the flywheel's mechanical coupling to the generator.",
        "Verify the drive belt tension (if belt-driven).",
        "Inspect for bearing wear — unusual sounds indicate failure.",
        "Check the motor controller's fault indicators.",
        "Verify power supply to the boost controller.",
    ],
    "nutrient_dose": [
        "Check if the dosing pump reservoir has liquid.",
        "Verify the dosing tube is not kinked or blocked.",
        "Confirm the solenoid valve is receiving the open signal.",
        "Check if pH/nutrient sensors are reading correctly after dose.",
        "Inspect for crystallization in the dosing nozzle.",
    ],
    "silk_test": [
        "Visually inspect the silk strand for physical damage.",
        "Check the strand's connection points at both terminals.",
        "Measure strand resistance with a multimeter to verify the Orin's reading.",
        "Check for environmental factors (humidity, temperature) affecting conductivity.",
        "Try swapping the strand with a known-good one to isolate the issue.",
    ],
    "air_curtain_activate": [
        "Check the Air Curtain fan motor for power supply.",
        "Verify the Flywheel has enough energy reserve to sustain the curtain.",
        "Inspect the curtain vents for physical blockage or debris.",
        "Check the relay/controller board for fault indicators.",
        "Verify the pressure sensors are reading correctly — false positives waste energy.",
    ],
    "nitrogen_vent": [
        "Check the nitrogen supply valve — is it stuck open?",
        "Verify the pressure relief valve is not jammed.",
        "Inspect the seal gaskets for visible degradation.",
        "Check for ice formation around the vent (nitrogen condensation).",
        "Verify the external vent pipe is not obstructed.",
    ],
}

DEFAULT_DIAGNOSTICS = [
    "Step back and review the physical environment.",
    "Check if the target hardware component is powered and connected.",
    "Verify the Silk wiring path between the Orin and the component.",
    "Check Flywheel energy reserves — low energy can cause intermittent failures.",
    "Review the last successful operation timestamp to identify when things changed.",
]


class LoopDetectionMiddleware:
    def __init__(self, max_attempts: int = 5, delta_threshold: float = 0.01,
                 cooldown_seconds: float = 60.0, window_seconds: float = 300.0):
        self.max_attempts = max_attempts
        self.delta_threshold = delta_threshold
        self.cooldown_seconds = cooldown_seconds
        self.window_seconds = window_seconds

        self._action_history: Dict[str, List[ActionRecord]] = defaultdict(list)
        self._alerts: List[LoopAlert] = []
        self._max_alerts = 100
        self._suppressed_signatures: Dict[str, float] = {}
        self._total_detections = 0

    def _compute_signature(self, action: Dict) -> str:
        normalized = json.dumps(
            {k: v for k, v in sorted(action.items()) if k != "timestamp"},
            default=str,
        )
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def record_action(self, action: Dict, result_value: Optional[float] = None) -> Optional[LoopAlert]:
        sig = self._compute_signature(action)
        now = time.time()

        self._action_history[sig].append(ActionRecord(
            signature=sig,
            action=action,
            result_value=result_value,
            timestamp=now,
        ))

        cutoff = now - self.window_seconds
        self._action_history[sig] = [
            r for r in self._action_history[sig] if r.timestamp > cutoff
        ]

        recent = self._action_history[sig]
        if len(recent) < self.max_attempts:
            return None

        if sig in self._suppressed_signatures:
            if now - self._suppressed_signatures[sig] < self.cooldown_seconds:
                return None

        values = [r.result_value for r in recent if r.result_value is not None]
        if len(values) >= 2:
            max_delta = max(values) - min(values)
        else:
            max_delta = 0.0

        if max_delta > self.delta_threshold:
            return None

        self._total_detections += 1
        self._suppressed_signatures[sig] = now

        action_type = action.get("type", "unknown")
        diagnostics = DIAGNOSTIC_MAP.get(action_type, DEFAULT_DIAGNOSTICS)

        target = action.get("sensor", action.get("target", action_type))

        alert = LoopAlert(
            alert_id=f"LOOP-{self._total_detections:04d}",
            action_signature=sig,
            attempt_count=len(recent),
            max_attempts=self.max_attempts,
            delta_observed=max_delta,
            delta_threshold=self.delta_threshold,
            message=(
                f"DOOM LOOP DETECTED: You have attempted '{action_type}' on '{target}' "
                f"{len(recent)} times in {self.window_seconds}s with no meaningful change "
                f"(delta: {max_delta:.4f}, threshold: {self.delta_threshold}). "
                f"Step back. Check the physical layer."
            ),
            diagnostic_suggestions=diagnostics,
        )

        self._alerts.append(alert)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]

        return alert

    def check_action(self, action: Dict) -> Dict:
        sig = self._compute_signature(action)
        now = time.time()

        cutoff = now - self.window_seconds
        recent = [r for r in self._action_history.get(sig, []) if r.timestamp > cutoff]

        risk_level = "clear"
        warning = None

        if len(recent) >= self.max_attempts:
            risk_level = "blocked"
            warning = f"Action has been attempted {len(recent)} times in the last {self.window_seconds}s. Doom loop likely."
        elif len(recent) >= self.max_attempts - 1:
            risk_level = "warning"
            warning = f"One more attempt will trigger doom loop detection ({len(recent)}/{self.max_attempts})."
        elif len(recent) >= self.max_attempts // 2:
            risk_level = "caution"
            warning = f"Action repeated {len(recent)} times. Monitor for loop behavior."

        return {
            "signature": sig,
            "recent_attempts": len(recent),
            "max_attempts": self.max_attempts,
            "risk_level": risk_level,
            "warning": warning,
        }

    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                if alert.action_signature in self._suppressed_signatures:
                    del self._suppressed_signatures[alert.action_signature]
                return True
        return False

    def get_active_alerts(self) -> List[Dict]:
        return [a.to_dict() for a in self._alerts if not a.resolved]

    def get_all_alerts(self, limit: int = 20) -> List[Dict]:
        return [a.to_dict() for a in self._alerts[-limit:]]

    def get_stats(self) -> Dict:
        active = sum(1 for a in self._alerts if not a.resolved)
        return {
            "total_detections": self._total_detections,
            "active_alerts": active,
            "resolved_alerts": len(self._alerts) - active,
            "tracked_signatures": len(self._action_history),
            "suppressed_count": len(self._suppressed_signatures),
            "config": {
                "max_attempts": self.max_attempts,
                "delta_threshold": self.delta_threshold,
                "cooldown_seconds": self.cooldown_seconds,
                "window_seconds": self.window_seconds,
            },
        }

    def clear_history(self):
        self._action_history.clear()
        self._suppressed_signatures.clear()
