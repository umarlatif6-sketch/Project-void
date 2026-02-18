"""
SilkLink Context Middleware & Aquaponics Boundary Hook

The Nervous System injects real-time sensor state into every agent
system prompt (Deterministic Context Injection) and intercepts
dangerous actions before they reach hardware (Boundary Hooks).
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict


@dataclass
class SensorReading:
    sensor_id: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    quality: str = "good"

    def to_dict(self):
        return asdict(self)


@dataclass
class BoundaryViolation:
    rule_name: str
    sensor_id: str
    current_value: float
    boundary_value: float
    direction: str
    message: str
    timestamp: float = field(default_factory=time.time)
    reconsideration_prompt: str = ""

    def to_dict(self):
        return asdict(self)


class SilkLinkContextMiddleware:
    def __init__(self):
        self._sensor_registry: Dict[str, SensorReading] = {}
        self._context_history: List[Dict] = []
        self._max_history = 50
        self._injection_count = 0

    def register_sensor(self, sensor_id: str, value: float, unit: str, quality: str = "good"):
        self._sensor_registry[sensor_id] = SensorReading(
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            quality=quality,
        )

    def bulk_update(self, readings: Dict[str, Dict]):
        for sensor_id, data in readings.items():
            self.register_sensor(
                sensor_id,
                data.get("value", 0),
                data.get("unit", ""),
                data.get("quality", "good"),
            )

    def inject_context(self, base_prompt: str = "") -> str:
        context_block = self._build_context_block()
        self._injection_count += 1

        injected = f"""{base_prompt}

--- SILKLINK DETERMINISTIC CONTEXT (injection #{self._injection_count}) ---
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{context_block}
--- END SILKLINK CONTEXT ---"""

        self._context_history.append({
            "injection_id": self._injection_count,
            "timestamp": time.time(),
            "sensor_count": len(self._sensor_registry),
            "context_length": len(context_block),
        })

        if len(self._context_history) > self._max_history:
            self._context_history = self._context_history[-self._max_history:]

        return injected

    def _build_context_block(self) -> str:
        if not self._sensor_registry:
            return "No sensors registered. Hardware state unknown."

        sections = {
            "silk": [],
            "aqua": [],
            "flywheel": [],
            "other": [],
        }

        for sid, reading in sorted(self._sensor_registry.items()):
            age = time.time() - reading.timestamp
            stale = " [STALE]" if age > 300 else ""
            line = f"  {sid}: {reading.value} {reading.unit} ({reading.quality}){stale}"

            if "silk" in sid.lower() or "resistance" in sid.lower() or "strand" in sid.lower():
                sections["silk"].append(line)
            elif "aqua" in sid.lower() or "ph" in sid.lower() or "pump" in sid.lower() or "water" in sid.lower() or "oxygen" in sid.lower() or "ammonia" in sid.lower():
                sections["aqua"].append(line)
            elif "flywheel" in sid.lower() or "rpm" in sid.lower() or "energy" in sid.lower():
                sections["flywheel"].append(line)
            elif "pressure" in sid.lower() or "air_curtain" in sid.lower() or "nitrogen" in sid.lower() or "seal" in sid.lower():
                sections.setdefault("pressure", []).append(line)
            else:
                sections["other"].append(line)

        blocks = []
        if sections["silk"]:
            blocks.append("SILK WIRING STATE:\n" + "\n".join(sections["silk"]))
        if sections["aqua"]:
            blocks.append("AQUAPONICS STATE:\n" + "\n".join(sections["aqua"]))
        if sections["flywheel"]:
            blocks.append("FLYWHEEL STATE:\n" + "\n".join(sections["flywheel"]))
        if sections.get("pressure"):
            blocks.append("PRESSURE / AC LOBBY STATE:\n" + "\n".join(sections["pressure"]))
        if sections["other"]:
            blocks.append("OTHER SENSORS:\n" + "\n".join(sections["other"]))

        return "\n\n".join(blocks)

    def get_all_readings(self) -> Dict:
        return {sid: r.to_dict() for sid, r in self._sensor_registry.items()}

    def get_sensor(self, sensor_id: str) -> Optional[Dict]:
        r = self._sensor_registry.get(sensor_id)
        return r.to_dict() if r else None

    def get_context_stats(self) -> Dict:
        return {
            "total_injections": self._injection_count,
            "registered_sensors": len(self._sensor_registry),
            "recent_history": self._context_history[-5:],
        }


BOUNDARY_RULES = [
    {
        "name": "pump_cycle_limit",
        "sensor_pattern": "aqua_pump_cycles",
        "max_value": 12,
        "message": "Pump cycle rate risks the fish and plankton ecosystem.",
        "reconsider": "Reduce pump frequency. Check if nutrient circulation is adequate at lower rate. Consider gravity-fed alternative.",
    },
    {
        "name": "ph_low_boundary",
        "sensor_pattern": "aqua_ph",
        "min_value": 6.0,
        "message": "Water pH has dropped below safe range for aquatic life.",
        "reconsider": "Add pH buffer (calcium carbonate). Do NOT adjust pumps — pH correction should be chemical, not mechanical.",
    },
    {
        "name": "ph_high_boundary",
        "sensor_pattern": "aqua_ph",
        "max_value": 7.5,
        "message": "Water pH exceeds safe range. Alkaline stress on plankton.",
        "reconsider": "Check for calcium buildup. Consider vinegar drip or CO2 injection to lower pH gradually.",
    },
    {
        "name": "flywheel_energy_floor",
        "sensor_pattern": "flywheel_energy",
        "min_value": 20.0,
        "message": "Flywheel energy reserve critically low.",
        "reconsider": "Reduce non-essential loads. Prioritize: aquaponics > silk monitoring > computation. Wait for flywheel to regenerate.",
    },
    {
        "name": "flywheel_overspeed",
        "sensor_pattern": "flywheel_rpm",
        "max_value": 12000,
        "message": "Flywheel approaching mechanical stress limit.",
        "reconsider": "Apply regenerative braking. Divert excess energy to battery buffer. Do NOT increase load while RPM is critical.",
    },
    {
        "name": "silk_resistance_drift",
        "sensor_pattern": "silk_resistance_delta",
        "max_value": 5.0,
        "message": "Silk wiring resistance drifting — possible degradation or environmental change.",
        "reconsider": "Run strand-by-strand continuity test. Check for moisture on silk contacts. Consider re-tensioning.",
    },
    {
        "name": "water_temperature_high",
        "sensor_pattern": "aqua_temperature",
        "max_value": 28.0,
        "message": "Water temperature exceeding plankton comfort zone.",
        "reconsider": "Activate cooling loop. Shade the tank. Reduce flywheel waste heat near water system.",
    },
    {
        "name": "ammonia_spike",
        "sensor_pattern": "aqua_ammonia",
        "max_value": 0.5,
        "message": "Ammonia levels toxic. Fish and plankton at immediate risk.",
        "reconsider": "Emergency water change (25%). Check biofilter. Reduce feeding. Do NOT cycle pumps faster — that won't fix ammonia.",
    },
    {
        "name": "pressure_high",
        "sensor_pattern": "pressure_internal",
        "max_value": 1.5,
        "message": "Internal pressure exceeding safe atmospheric limit. Nitrogen boil likely.",
        "reconsider": "Activate Air Curtain immediately (velocity >= 10 m/s). If already active, increase velocity. Check nitrogen supply valve for leaks.",
    },
    {
        "name": "pressure_seal_breach",
        "sensor_pattern": "pressure_internal",
        "max_value": 1.8,
        "message": "SEAL BREACH: Pressure has exceeded containment limit. Immediate action required.",
        "reconsider": "Emergency nitrogen vent. Activate Air Curtain at maximum velocity. Evacuate sensitive equipment from pressure zone.",
    },
    {
        "name": "air_curtain_insufficient",
        "sensor_pattern": "air_curtain_velocity",
        "min_value": 10.0,
        "message": "Air Curtain velocity below minimum effective threshold.",
        "reconsider": "Increase Air Curtain fan speed. Check power supply to curtain motor. Verify Flywheel energy is sufficient to sustain curtain operation.",
        "requires_condition": {"sensor_pattern": "pressure_internal", "min_value": 1.1},
    },
]


class AquaponicsBoundaryHook:
    def __init__(self, custom_rules: Optional[List[Dict]] = None):
        self.rules = BOUNDARY_RULES + (custom_rules or [])
        self._violations: List[BoundaryViolation] = []
        self._max_violations = 200
        self._intercept_count = 0

    def check_boundaries(self, sensor_state: Dict) -> List[BoundaryViolation]:
        violations = []

        flat_sensors = self._flatten_state(sensor_state)

        for rule in self.rules:
            if "requires_condition" in rule:
                cond = rule["requires_condition"]
                cond_pattern = cond["sensor_pattern"]
                cond_val = None
                for key, value in flat_sensors.items():
                    if cond_pattern in key.lower():
                        cond_val = value
                        break
                if cond_val is None:
                    continue
                if "min_value" in cond and cond_val < cond["min_value"]:
                    continue
                if "max_value" in cond and cond_val > cond["max_value"]:
                    continue

            pattern = rule["sensor_pattern"]
            matched_value = None
            matched_key = None

            for key, value in flat_sensors.items():
                if pattern in key.lower():
                    matched_value = value
                    matched_key = key
                    break

            if matched_value is None or matched_key is None:
                continue

            if "max_value" in rule and matched_value > rule["max_value"]:
                v = BoundaryViolation(
                    rule_name=rule["name"],
                    sensor_id=matched_key,
                    current_value=matched_value,
                    boundary_value=rule["max_value"],
                    direction="above",
                    message=rule["message"],
                    reconsideration_prompt=rule.get("reconsider", ""),
                )
                violations.append(v)

            if "min_value" in rule and matched_value < rule["min_value"]:
                v = BoundaryViolation(
                    rule_name=rule["name"],
                    sensor_id=matched_key,
                    current_value=matched_value,
                    boundary_value=rule["min_value"],
                    direction="below",
                    message=rule["message"],
                    reconsideration_prompt=rule.get("reconsider", ""),
                )
                violations.append(v)

        if violations:
            self._intercept_count += 1
            self._violations.extend(violations)
            if len(self._violations) > self._max_violations:
                self._violations = self._violations[-self._max_violations:]

        return violations

    def intercept_action(self, action: Dict, sensor_state: Dict) -> Dict:
        violations = self.check_boundaries(sensor_state)

        if not violations:
            return {
                "allowed": True,
                "action": action,
                "violations": [],
            }

        return {
            "allowed": False,
            "action": action,
            "violations": [v.to_dict() for v in violations],
            "reconsideration_prompts": [
                v.reconsideration_prompt for v in violations if v.reconsideration_prompt
            ],
            "intercept_id": self._intercept_count,
            "message": f"BOUNDARY HOOK: {len(violations)} violation(s) detected. Action blocked. Review reconsideration prompts.",
        }

    def _flatten_state(self, state: Dict, prefix: str = "") -> Dict:
        flat = {}
        for k, v in state.items():
            key = f"{prefix}_{k}" if prefix else k
            if isinstance(v, dict):
                flat.update(self._flatten_state(v, key))
            elif isinstance(v, (int, float)):
                flat[key] = v
        return flat

    def get_violation_history(self, limit: int = 20) -> List[Dict]:
        return [v.to_dict() for v in self._violations[-limit:]]

    def get_stats(self) -> Dict:
        return {
            "total_intercepts": self._intercept_count,
            "total_violations": len(self._violations),
            "active_rules": len(self.rules),
            "rule_names": [r["name"] for r in self.rules],
        }

    def add_rule(self, rule: Dict):
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r["name"] != rule_name]
        return len(self.rules) < before
