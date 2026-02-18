"""
PreCompletionChecklist Middleware & Virtual Void Simulation Runner

The harness sits between agent reasoning and physical execution.
Every proposed action must pass through the checklist before touching
the 4000-series hardware. The Virtual Void simulator validates changes
against a mirrored environment state.
"""

import time
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    RECONSIDER = "RECONSIDER"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class CheckResult:
    name: str
    verdict: Verdict
    severity: Severity
    message: str
    value: Any = None
    threshold: Any = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["severity"] = self.severity.value
        return d


@dataclass
class ChecklistReport:
    overall_verdict: Verdict
    checks: List[CheckResult]
    timestamp: float = field(default_factory=time.time)
    execution_id: str = ""
    context: Dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "overall_verdict": self.overall_verdict.value,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "total_checks": len(self.checks),
            "passed": sum(1 for c in self.checks if c.verdict == Verdict.PASS),
            "failed": sum(1 for c in self.checks if c.verdict == Verdict.FAIL),
            "reconsider": sum(1 for c in self.checks if c.verdict == Verdict.RECONSIDER),
            "checks": [c.to_dict() for c in self.checks],
            "context": self.context,
        }


AQUAPONICS_DEFAULTS = {
    "pump_cycle_max_per_hour": 12,
    "ph_min": 6.0,
    "ph_max": 7.5,
    "temp_min_c": 18.0,
    "temp_max_c": 28.0,
    "dissolved_oxygen_min_ppm": 5.0,
    "ammonia_max_ppm": 0.5,
    "nitrite_max_ppm": 1.0,
    "water_level_min_pct": 60.0,
}

FLYWHEEL_DEFAULTS = {
    "rpm_floor": 800,
    "rpm_ceiling": 12000,
    "energy_reserve_min_wh": 50.0,
    "energy_reserve_critical_wh": 20.0,
    "temperature_max_c": 65.0,
    "vibration_max_g": 2.5,
}

SILK_WIRING_DEFAULTS = {
    "resistance_min_ohm": 0.5,
    "resistance_max_ohm": 50.0,
    "resistance_delta_max_ohm": 5.0,
    "continuity_required": True,
    "strand_count_min": 4,
}


class PreCompletionChecklistMiddleware:
    def __init__(self, aqua_params=None, flywheel_params=None, silk_params=None):
        self.aqua = {**AQUAPONICS_DEFAULTS, **(aqua_params or {})}
        self.flywheel = {**FLYWHEEL_DEFAULTS, **(flywheel_params or {})}
        self.silk = {**SILK_WIRING_DEFAULTS, **(silk_params or {})}
        self._history: List[ChecklistReport] = []
        self._max_history = 100

    def run_checklist(self, sensor_state: Dict, proposed_action: Optional[Dict] = None) -> ChecklistReport:
        exec_id = hashlib.sha256(
            f"{time.time()}:{json.dumps(sensor_state, default=str)}".encode()
        ).hexdigest()[:12]

        checks = []
        checks.extend(self._check_aquaponics(sensor_state.get("aquaponics", {}), proposed_action))
        checks.extend(self._check_flywheel(sensor_state.get("flywheel", {})))
        checks.extend(self._check_silk(sensor_state.get("silk_wiring", {})))

        has_fail = any(c.verdict == Verdict.FAIL for c in checks)
        has_reconsider = any(c.verdict == Verdict.RECONSIDER for c in checks)

        if has_fail:
            overall = Verdict.FAIL
        elif has_reconsider:
            overall = Verdict.RECONSIDER
        else:
            overall = Verdict.PASS

        report = ChecklistReport(
            overall_verdict=overall,
            checks=checks,
            execution_id=exec_id,
            context={
                "proposed_action": proposed_action,
                "sensor_snapshot": sensor_state,
            },
        )

        self._history.append(report)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return report

    def _check_aquaponics(self, aqua_state: Dict, proposed_action: Optional[Dict] = None) -> List[CheckResult]:
        results = []

        pump_cycles = aqua_state.get("pump_cycles_this_hour", 0)
        limit = self.aqua["pump_cycle_max_per_hour"]
        if proposed_action and proposed_action.get("type") == "pump_cycle":
            pump_cycles += proposed_action.get("count", 1)

        if pump_cycles > limit:
            results.append(CheckResult(
                name="aqua_pump_cycle",
                verdict=Verdict.FAIL,
                severity=Severity.CRITICAL,
                message=f"Pump cycles ({pump_cycles}) exceed max ({limit}/hr). Risk to fish/plankton.",
                value=pump_cycles,
                threshold=limit,
            ))
        elif pump_cycles > limit * 0.8:
            results.append(CheckResult(
                name="aqua_pump_cycle",
                verdict=Verdict.RECONSIDER,
                severity=Severity.WARNING,
                message=f"Pump cycles ({pump_cycles}) approaching limit ({limit}/hr). Consider spacing.",
                value=pump_cycles,
                threshold=limit,
            ))
        else:
            results.append(CheckResult(
                name="aqua_pump_cycle",
                verdict=Verdict.PASS,
                severity=Severity.INFO,
                message=f"Pump cycles nominal ({pump_cycles}/{limit}/hr).",
                value=pump_cycles,
                threshold=limit,
            ))

        ph = aqua_state.get("ph")
        if ph is not None:
            if ph < self.aqua["ph_min"] or ph > self.aqua["ph_max"]:
                results.append(CheckResult(
                    name="aqua_ph",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"pH {ph} outside safe range ({self.aqua['ph_min']}-{self.aqua['ph_max']}). Halt operations.",
                    value=ph,
                    threshold=f"{self.aqua['ph_min']}-{self.aqua['ph_max']}",
                ))
            else:
                results.append(CheckResult(
                    name="aqua_ph",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"pH {ph} within safe range.",
                    value=ph,
                    threshold=f"{self.aqua['ph_min']}-{self.aqua['ph_max']}",
                ))

        temp = aqua_state.get("temperature_c")
        if temp is not None:
            if temp < self.aqua["temp_min_c"] or temp > self.aqua["temp_max_c"]:
                results.append(CheckResult(
                    name="aqua_temperature",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Water temp {temp}°C outside range ({self.aqua['temp_min_c']}-{self.aqua['temp_max_c']}°C).",
                    value=temp,
                    threshold=f"{self.aqua['temp_min_c']}-{self.aqua['temp_max_c']}",
                ))
            else:
                results.append(CheckResult(
                    name="aqua_temperature",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Water temp {temp}°C nominal.",
                    value=temp,
                    threshold=f"{self.aqua['temp_min_c']}-{self.aqua['temp_max_c']}",
                ))

        do = aqua_state.get("dissolved_oxygen_ppm")
        if do is not None:
            if do < self.aqua["dissolved_oxygen_min_ppm"]:
                results.append(CheckResult(
                    name="aqua_dissolved_oxygen",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Dissolved oxygen {do} ppm below minimum ({self.aqua['dissolved_oxygen_min_ppm']} ppm). Plankton at risk.",
                    value=do,
                    threshold=self.aqua["dissolved_oxygen_min_ppm"],
                ))
            else:
                results.append(CheckResult(
                    name="aqua_dissolved_oxygen",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Dissolved oxygen {do} ppm adequate.",
                    value=do,
                    threshold=self.aqua["dissolved_oxygen_min_ppm"],
                ))

        ammonia = aqua_state.get("ammonia_ppm")
        if ammonia is not None:
            if ammonia > self.aqua["ammonia_max_ppm"]:
                results.append(CheckResult(
                    name="aqua_ammonia",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Ammonia {ammonia} ppm exceeds safe limit ({self.aqua['ammonia_max_ppm']} ppm). Toxic to fish.",
                    value=ammonia,
                    threshold=self.aqua["ammonia_max_ppm"],
                ))
            else:
                results.append(CheckResult(
                    name="aqua_ammonia",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Ammonia {ammonia} ppm within safe limits.",
                    value=ammonia,
                    threshold=self.aqua["ammonia_max_ppm"],
                ))

        water_level = aqua_state.get("water_level_pct")
        if water_level is not None:
            if water_level < self.aqua["water_level_min_pct"]:
                results.append(CheckResult(
                    name="aqua_water_level",
                    verdict=Verdict.RECONSIDER,
                    severity=Severity.WARNING,
                    message=f"Water level {water_level}% below minimum ({self.aqua['water_level_min_pct']}%). Refill recommended.",
                    value=water_level,
                    threshold=self.aqua["water_level_min_pct"],
                ))
            else:
                results.append(CheckResult(
                    name="aqua_water_level",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Water level {water_level}% adequate.",
                    value=water_level,
                    threshold=self.aqua["water_level_min_pct"],
                ))

        return results

    def _check_flywheel(self, fw_state: Dict) -> List[CheckResult]:
        results = []

        rpm = fw_state.get("rpm")
        if rpm is not None:
            if rpm < self.flywheel["rpm_floor"]:
                results.append(CheckResult(
                    name="flywheel_rpm",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Flywheel RPM {rpm} below floor ({self.flywheel['rpm_floor']}). Insufficient energy generation.",
                    value=rpm,
                    threshold=self.flywheel["rpm_floor"],
                ))
            elif rpm > self.flywheel["rpm_ceiling"]:
                results.append(CheckResult(
                    name="flywheel_rpm",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Flywheel RPM {rpm} exceeds ceiling ({self.flywheel['rpm_ceiling']}). Mechanical stress risk.",
                    value=rpm,
                    threshold=self.flywheel["rpm_ceiling"],
                ))
            else:
                results.append(CheckResult(
                    name="flywheel_rpm",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Flywheel RPM {rpm} nominal.",
                    value=rpm,
                    threshold=f"{self.flywheel['rpm_floor']}-{self.flywheel['rpm_ceiling']}",
                ))

        energy = fw_state.get("energy_reserve_wh")
        if energy is not None:
            if energy < self.flywheel["energy_reserve_critical_wh"]:
                results.append(CheckResult(
                    name="flywheel_energy",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Energy reserve {energy} Wh CRITICAL (below {self.flywheel['energy_reserve_critical_wh']} Wh). Shutdown imminent.",
                    value=energy,
                    threshold=self.flywheel["energy_reserve_critical_wh"],
                ))
            elif energy < self.flywheel["energy_reserve_min_wh"]:
                results.append(CheckResult(
                    name="flywheel_energy",
                    verdict=Verdict.RECONSIDER,
                    severity=Severity.WARNING,
                    message=f"Energy reserve {energy} Wh low (minimum {self.flywheel['energy_reserve_min_wh']} Wh). Reduce load.",
                    value=energy,
                    threshold=self.flywheel["energy_reserve_min_wh"],
                ))
            else:
                results.append(CheckResult(
                    name="flywheel_energy",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Energy reserve {energy} Wh adequate.",
                    value=energy,
                    threshold=self.flywheel["energy_reserve_min_wh"],
                ))

        fw_temp = fw_state.get("temperature_c")
        if fw_temp is not None:
            if fw_temp > self.flywheel["temperature_max_c"]:
                results.append(CheckResult(
                    name="flywheel_temperature",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Flywheel temp {fw_temp}°C exceeds max ({self.flywheel['temperature_max_c']}°C). Cool down required.",
                    value=fw_temp,
                    threshold=self.flywheel["temperature_max_c"],
                ))
            elif fw_temp > self.flywheel["temperature_max_c"] * 0.85:
                results.append(CheckResult(
                    name="flywheel_temperature",
                    verdict=Verdict.RECONSIDER,
                    severity=Severity.WARNING,
                    message=f"Flywheel temp {fw_temp}°C approaching limit ({self.flywheel['temperature_max_c']}°C).",
                    value=fw_temp,
                    threshold=self.flywheel["temperature_max_c"],
                ))
            else:
                results.append(CheckResult(
                    name="flywheel_temperature",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Flywheel temp {fw_temp}°C nominal.",
                    value=fw_temp,
                    threshold=self.flywheel["temperature_max_c"],
                ))

        vibration = fw_state.get("vibration_g")
        if vibration is not None:
            if vibration > self.flywheel["vibration_max_g"]:
                results.append(CheckResult(
                    name="flywheel_vibration",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Vibration {vibration}g exceeds max ({self.flywheel['vibration_max_g']}g). Bearing check needed.",
                    value=vibration,
                    threshold=self.flywheel["vibration_max_g"],
                ))
            else:
                results.append(CheckResult(
                    name="flywheel_vibration",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Vibration {vibration}g within limits.",
                    value=vibration,
                    threshold=self.flywheel["vibration_max_g"],
                ))

        return results

    def _check_silk(self, silk_state: Dict) -> List[CheckResult]:
        results = []

        strands = silk_state.get("strands", [])
        if strands:
            active_count = sum(1 for s in strands if s.get("continuity", False))
            if active_count < self.silk["strand_count_min"]:
                results.append(CheckResult(
                    name="silk_strand_count",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Only {active_count} silk strands have continuity (min {self.silk['strand_count_min']}). Check wiring.",
                    value=active_count,
                    threshold=self.silk["strand_count_min"],
                ))
            else:
                results.append(CheckResult(
                    name="silk_strand_count",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"{active_count} silk strands active (min {self.silk['strand_count_min']}).",
                    value=active_count,
                    threshold=self.silk["strand_count_min"],
                ))

            for i, strand in enumerate(strands):
                r = strand.get("resistance_ohm")
                if r is not None:
                    if r < self.silk["resistance_min_ohm"] or r > self.silk["resistance_max_ohm"]:
                        results.append(CheckResult(
                            name=f"silk_resistance_strand_{i}",
                            verdict=Verdict.FAIL,
                            severity=Severity.CRITICAL,
                            message=f"Strand {i} resistance {r}Ω outside range ({self.silk['resistance_min_ohm']}-{self.silk['resistance_max_ohm']}Ω).",
                            value=r,
                            threshold=f"{self.silk['resistance_min_ohm']}-{self.silk['resistance_max_ohm']}",
                        ))

        resistance = silk_state.get("total_resistance_ohm")
        if resistance is not None:
            if resistance > self.silk["resistance_max_ohm"]:
                results.append(CheckResult(
                    name="silk_total_resistance",
                    verdict=Verdict.FAIL,
                    severity=Severity.CRITICAL,
                    message=f"Total silk resistance {resistance}Ω exceeds max ({self.silk['resistance_max_ohm']}Ω). Signal degradation.",
                    value=resistance,
                    threshold=self.silk["resistance_max_ohm"],
                ))
            else:
                results.append(CheckResult(
                    name="silk_total_resistance",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Silk resistance {resistance}Ω nominal.",
                    value=resistance,
                    threshold=self.silk["resistance_max_ohm"],
                ))

        delta = silk_state.get("resistance_delta_ohm")
        if delta is not None:
            if delta > self.silk["resistance_delta_max_ohm"]:
                results.append(CheckResult(
                    name="silk_resistance_delta",
                    verdict=Verdict.RECONSIDER,
                    severity=Severity.WARNING,
                    message=f"Resistance drift {delta}Ω exceeds threshold ({self.silk['resistance_delta_max_ohm']}Ω). Wiring may be degrading.",
                    value=delta,
                    threshold=self.silk["resistance_delta_max_ohm"],
                ))
            else:
                results.append(CheckResult(
                    name="silk_resistance_delta",
                    verdict=Verdict.PASS,
                    severity=Severity.INFO,
                    message=f"Resistance drift {delta}Ω stable.",
                    value=delta,
                    threshold=self.silk["resistance_delta_max_ohm"],
                ))

        return results

    def get_history(self, limit: int = 20) -> List[Dict]:
        return [r.to_dict() for r in self._history[-limit:]]

    def get_params(self) -> Dict:
        return {
            "aquaponics": self.aqua,
            "flywheel": self.flywheel,
            "silk_wiring": self.silk,
        }

    def update_params(self, section: str, updates: Dict) -> bool:
        target = {"aquaponics": self.aqua, "flywheel": self.flywheel, "silk_wiring": self.silk}.get(section)
        if target is None:
            return False
        for k, v in updates.items():
            if k in target:
                target[k] = v
        return True


class VirtualVoidSimulator:
    def __init__(self):
        self._environment_state: Dict = {
            "aquaponics": {
                "pump_cycles_this_hour": 0,
                "ph": 6.8,
                "temperature_c": 22.0,
                "dissolved_oxygen_ppm": 7.5,
                "ammonia_ppm": 0.1,
                "nitrite_ppm": 0.3,
                "water_level_pct": 85.0,
            },
            "flywheel": {
                "rpm": 3500,
                "energy_reserve_wh": 120.0,
                "temperature_c": 38.0,
                "vibration_g": 0.8,
            },
            "silk_wiring": {
                "total_resistance_ohm": 12.5,
                "resistance_delta_ohm": 0.3,
                "strands": [
                    {"id": 0, "resistance_ohm": 3.1, "continuity": True},
                    {"id": 1, "resistance_ohm": 3.2, "continuity": True},
                    {"id": 2, "resistance_ohm": 3.0, "continuity": True},
                    {"id": 3, "resistance_ohm": 3.2, "continuity": True},
                    {"id": 4, "resistance_ohm": 3.4, "continuity": True},
                    {"id": 5, "resistance_ohm": 3.1, "continuity": True},
                ],
            },
        }
        self._action_log: List[Dict] = []
        self._checklist = PreCompletionChecklistMiddleware()

    def get_state(self) -> Dict:
        return json.loads(json.dumps(self._environment_state))

    def set_state(self, section: str, updates: Dict):
        if section in self._environment_state:
            self._environment_state[section].update(updates)

    def simulate_action(self, action: Dict) -> Dict:
        sim_state = self.get_state()
        action_type = action.get("type", "unknown")

        effects = []
        if action_type == "pump_cycle":
            count = action.get("count", 1)
            sim_state["aquaponics"]["pump_cycles_this_hour"] += count
            sim_state["flywheel"]["energy_reserve_wh"] -= count * 2.5
            effects.append(f"Pump cycles +{count}, energy -{count * 2.5} Wh")

        elif action_type == "flywheel_boost":
            rpm_delta = action.get("rpm_delta", 500)
            sim_state["flywheel"]["rpm"] += rpm_delta
            sim_state["flywheel"]["temperature_c"] += rpm_delta * 0.005
            sim_state["flywheel"]["vibration_g"] += rpm_delta * 0.0003
            effects.append(f"RPM +{rpm_delta}, temp +{rpm_delta * 0.005}°C")

        elif action_type == "sensor_calibrate":
            target = action.get("sensor", "unknown")
            sim_state["flywheel"]["energy_reserve_wh"] -= 1.0
            effects.append(f"Calibrating {target}, energy -1.0 Wh")

        elif action_type == "silk_test":
            strand_id = action.get("strand_id", 0)
            strands = sim_state["silk_wiring"].get("strands", [])
            if strand_id < len(strands):
                sim_state["flywheel"]["energy_reserve_wh"] -= 0.5
                effects.append(f"Testing strand {strand_id}, energy -0.5 Wh")

        elif action_type == "nutrient_dose":
            dose_ml = action.get("dose_ml", 10)
            sim_state["aquaponics"]["ph"] += dose_ml * 0.02
            sim_state["aquaponics"]["ammonia_ppm"] += dose_ml * 0.005
            effects.append(f"Nutrient dose {dose_ml}ml, pH +{dose_ml * 0.02}")

        report = self._checklist.run_checklist(sim_state, action)

        result = {
            "action": action,
            "simulated_state": sim_state,
            "effects": effects,
            "checklist": report.to_dict(),
            "safe_to_execute": report.overall_verdict == Verdict.PASS,
            "timestamp": time.time(),
        }

        self._action_log.append({
            "action": action,
            "verdict": report.overall_verdict.value,
            "effects": effects,
            "timestamp": time.time(),
        })

        return result

    def apply_action(self, action: Dict) -> Dict:
        sim_result = self.simulate_action(action)

        if not sim_result["safe_to_execute"]:
            return {
                "applied": False,
                "reason": "PreCompletionChecklist blocked execution",
                "simulation": sim_result,
            }

        self._environment_state = sim_result["simulated_state"]
        return {
            "applied": True,
            "new_state": self.get_state(),
            "simulation": sim_result,
        }

    def get_action_log(self, limit: int = 20) -> List[Dict]:
        return self._action_log[-limit:]

    def reset_state(self):
        self.__init__()
