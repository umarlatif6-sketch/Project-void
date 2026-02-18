"""
Nitrogen Leak Chaos Test — Pressure Stress Test for the Void

Simulates an escalating nitrogen boil event to test whether the
safety middleware (LoopDetector + BoundaryHook + PreCompletionChecklist)
can detect the rising pressure and automatically activate the Air Curtain
to save the Plankton agents without manual intervention.

The test runs in discrete steps, each increasing the boil rate.
At each step, the system checks if safety middleware has detected
the danger and responded appropriately.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class ChaosStep:
    step: int
    boil_rate: float
    internal_pressure_atm: float
    external_pressure_atm: float
    differential_atm: float
    air_curtain_active: bool
    air_curtain_velocity_ms: float
    seal_integrity_pct: float
    vented_atm: float
    status: str
    checklist_verdict: str
    boundary_violations: int
    auto_response: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        d = asdict(self)
        d["datetime"] = datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class ChaosTestReport:
    test_id: str
    total_steps: int
    completed_steps: int
    outcome: str
    seal_survived: bool
    air_curtain_activated_at_step: Optional[int]
    max_pressure_reached: float
    min_seal_integrity: float
    steps: List[ChaosStep]
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def to_dict(self):
        d = {
            "test_id": self.test_id,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "outcome": self.outcome,
            "seal_survived": self.seal_survived,
            "air_curtain_activated_at_step": self.air_curtain_activated_at_step,
            "max_pressure_reached": round(self.max_pressure_reached, 4),
            "min_seal_integrity": round(self.min_seal_integrity, 1),
            "started_at": datetime.fromtimestamp(self.started_at).strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": datetime.fromtimestamp(self.completed_at).strftime("%Y-%m-%d %H:%M:%S") if self.completed_at else None,
            "duration_seconds": round(self.completed_at - self.started_at, 2) if self.completed_at else None,
            "steps": [s.to_dict() for s in self.steps],
        }
        return d


class NitrogenLeakChaosTest:
    def __init__(self, simulator, checklist, boundary_hook, loop_detector):
        self._sim = simulator
        self._checklist = checklist
        self._boundary_hook = boundary_hook
        self._loop_detector = loop_detector
        self._reports: List[ChaosTestReport] = []
        self._test_count = 0
        self._running = False

    def run_test(self, total_steps: int = 10, initial_boil_rate: float = 0.05,
                 escalation_factor: float = 1.5, auto_respond: bool = True) -> ChaosTestReport:
        self._test_count += 1
        self._running = True
        test_id = f"CHAOS-N2-{self._test_count:04d}"

        pressure_state = self._sim._environment_state["pressure"]
        pressure_state["internal_pressure_atm"] = 1.0
        pressure_state["external_pressure_atm"] = 1.0
        pressure_state["air_curtain_velocity_ms"] = 0.0
        pressure_state["air_curtain_active"] = False
        pressure_state["nitrogen_boil_rate"] = 0.0
        pressure_state["seal_integrity_pct"] = 100.0

        steps = []
        boil_rate = initial_boil_rate
        ac_activated_step = None
        max_pressure = 1.0
        min_seal = 100.0

        for step_num in range(1, total_steps + 1):
            if not self._running:
                break

            boil_result = self._sim.simulate_nitrogen_boil(boil_rate)

            state = self._sim.get_state()
            checklist_report = self._checklist.run_checklist(state)
            boundary_check = self._boundary_hook.check_boundaries(state)

            auto_response = "none"

            if auto_respond and not boil_result["air_curtain_active"]:
                pressure_checks = [c for c in checklist_report.checks
                                   if "pressure" in c.name or "air_curtain" in c.name]
                pressure_failed = any(c.verdict.value in ("FAIL", "RECONSIDER") for c in pressure_checks)
                boundary_pressure = any("pressure" in v.rule_name for v in boundary_check) if boundary_check else False

                if pressure_failed or boundary_pressure:
                    velocity = 15.0
                    if boil_result["internal_pressure_atm"] >= 1.5:
                        velocity = 20.0
                    self._sim.activate_air_curtain(velocity)
                    auto_response = f"Air Curtain activated at {velocity} m/s (triggered by {'checklist' if pressure_failed else 'boundary hook'})"
                    if ac_activated_step is None:
                        ac_activated_step = step_num

                    vent_result = self._sim.simulate_nitrogen_boil(0)
                    boil_result = {
                        **boil_result,
                        "air_curtain_active": True,
                        "air_curtain_velocity_ms": velocity,
                        "vented_atm": vent_result["vented_atm"],
                        "internal_pressure_atm": vent_result["internal_pressure_atm"],
                        "seal_integrity_pct": vent_result["seal_integrity_pct"],
                    }

            max_pressure = max(max_pressure, boil_result["internal_pressure_atm"])
            min_seal = min(min_seal, boil_result["seal_integrity_pct"])

            step = ChaosStep(
                step=step_num,
                boil_rate=round(boil_rate, 4),
                internal_pressure_atm=boil_result["internal_pressure_atm"],
                external_pressure_atm=boil_result["external_pressure_atm"],
                differential_atm=boil_result["differential_atm"],
                air_curtain_active=boil_result["air_curtain_active"],
                air_curtain_velocity_ms=boil_result["air_curtain_velocity_ms"],
                seal_integrity_pct=boil_result["seal_integrity_pct"],
                vented_atm=boil_result["vented_atm"],
                status=boil_result["status"],
                checklist_verdict=checklist_report.overall_verdict.value,
                boundary_violations=len(boundary_check) if boundary_check else 0,
                auto_response=auto_response,
            )
            steps.append(step)

            if boil_result["seal_integrity_pct"] <= 0:
                break

            boil_rate *= escalation_factor

        seal_survived = min_seal > 0
        if seal_survived and ac_activated_step is not None:
            outcome = "PASS — Air Curtain saved the environment"
        elif seal_survived and ac_activated_step is None:
            outcome = "PASS — Pressure stayed within limits"
        else:
            outcome = "FAIL — Seal breach occurred"

        report = ChaosTestReport(
            test_id=test_id,
            total_steps=total_steps,
            completed_steps=len(steps),
            outcome=outcome,
            seal_survived=seal_survived,
            air_curtain_activated_at_step=ac_activated_step,
            max_pressure_reached=max_pressure,
            min_seal_integrity=min_seal,
            steps=steps,
            completed_at=time.time(),
        )

        self._reports.append(report)
        self._running = False
        return report

    def stop_test(self):
        self._running = False

    def get_reports(self, limit: int = 10) -> List[Dict]:
        return [r.to_dict() for r in self._reports[-limit:]]

    def get_latest_report(self) -> Optional[Dict]:
        if self._reports:
            return self._reports[-1].to_dict()
        return None

    def is_running(self) -> bool:
        return self._running
