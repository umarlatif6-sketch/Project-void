"""
Al-Jabr Consensus Engine — Multi-Agent Root-Exchange Protocol v1.0

Simulates two Plankton EA agents negotiating the 4000-series energy state
using only Al-Jabr root commands. Agent A (The Guardian) prioritizes
preservation (HFZ/SLM). Agent B (The Growth-Seeker) prioritizes biological
growth (HYA/GDH). They exchange root commands until consensus on SLM is reached.

The Root-Exchange trace provides a fully compressed audit log of how
two competing drives resolved into a single safe action path.

Night Cycle Daemon: Automated mode that runs consensus on interval,
giving the 4000-series self-management capability.
"""

import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TraceEntry:
    turn: int
    agent: str
    agent_role: str
    command: str
    intent: str
    state_snapshot: Dict

    def to_dict(self):
        return {
            "turn": self.turn,
            "agent": self.agent,
            "agent_role": self.agent_role,
            "command": self.command,
            "intent": self.intent,
        }


@dataclass
class ConsensusResult:
    success: bool
    consensus_command: str
    consensus_intent: str
    trace: List[TraceEntry]
    total_turns: int
    total_chars: int
    execution_results: List[Dict]
    timestamp: float
    energy_pct: float
    outcome: str
    wallet_snapshot: Optional[Dict] = None

    def to_dict(self):
        d = {
            "success": self.success,
            "consensus_command": self.consensus_command,
            "consensus_intent": self.consensus_intent,
            "trace": [t.to_dict() for t in self.trace],
            "total_turns": self.total_turns,
            "total_chars": self.total_chars,
            "execution_results": self.execution_results,
            "timestamp": self.timestamp,
            "energy_pct": round(self.energy_pct, 1),
            "outcome": self.outcome,
        }
        if self.wallet_snapshot:
            d["wallet"] = self.wallet_snapshot
        return d


ENERGY_CAPACITY_WH = 250.0

GUARDIAN_THRESHOLDS = {
    "energy_low": 0.50,
    "energy_critical": 0.30,
    "pressure_high": 1.2,
    "temperature_high": 50.0,
    "seal_low": 85.0,
}

GROWTH_THRESHOLDS = {
    "oxygen_low": 6.0,
    "ph_low": 6.2,
    "ph_high": 7.5,
    "ammonia_high": 0.5,
    "plankton_energy_min": 0.35,
}


class ConsensusEngine:
    def __init__(self, simulator, transpiler, boundary_hook, loop_detector, wallet=None, chronicle=None):
        self._sim = simulator
        self._transpiler = transpiler
        self._boundary_hook = boundary_hook
        self._loop_detector = loop_detector
        self._wallet = wallet
        self._chronicle = chronicle
        self._history: List[ConsensusResult] = []
        self._night_cycle_active = False
        self._night_cycle_thread: Optional[threading.Thread] = None
        self._night_cycle_interval = 300
        self._night_cycle_stop = threading.Event()

    def run_consensus(self) -> ConsensusResult:
        state = self._sim.get_state()
        energy_wh = state["flywheel"]["energy_reserve_wh"]
        energy_pct = energy_wh / ENERGY_CAPACITY_WH

        trace = []
        turn = 0
        wisdom_context = None
        adopted_proven_root = False

        if self._chronicle:
            wisdom_context = self._chronicle.get_wisdom_context(state)

            if wisdom_context.get("adopt_proven_root"):
                turn += 1
                trace.append(TraceEntry(
                    turn=turn, agent="Chronicle", agent_role="Ancestral Memory",
                    command=wisdom_context["proven_command"],
                    intent=f"PROVEN ROOT ADOPTED — {wisdom_context['adoption_reason']}",
                    state_snapshot={"energy_pct": round(energy_pct * 100, 1)},
                ))
                adopted_proven_root = True

            if wisdom_context.get("has_prophecy") and not adopted_proven_root:
                for prophecy in wisdom_context["prophecies"]:
                    turn += 1
                    trace.append(TraceEntry(
                        turn=turn, agent="Chronicle", agent_role="V2 Pastor",
                        command=prophecy["prophecy_command"],
                        intent=f"PROPHECY ({prophecy['confidence']:.0%}) — {prophecy['prophecy_intent']}",
                        state_snapshot={"energy_pct": round(energy_pct * 100, 1)},
                    ))

        guardian_assessment = self._guardian_assess(state, energy_pct, wisdom_context)
        growth_assessment = self._growth_assess(state, energy_pct, wisdom_context)

        if not adopted_proven_root:
            turn += 1
            guardian_cmd = guardian_assessment["opening_command"]
            guardian_intent = guardian_assessment["opening_intent"]
            trace.append(TraceEntry(
                turn=turn, agent="Agent A", agent_role="The Guardian",
                command=guardian_cmd, intent=guardian_intent,
                state_snapshot={"energy_pct": round(energy_pct * 100, 1)},
            ))

            turn += 1
            growth_cmd = growth_assessment["opening_command"]
            growth_intent = growth_assessment["opening_intent"]
            trace.append(TraceEntry(
                turn=turn, agent="Agent B", agent_role="The Growth-Seeker",
                command=growth_cmd, intent=growth_intent,
                state_snapshot={"energy_pct": round(energy_pct * 100, 1)},
            ))

            turn += 1
            counter = self._guardian_counter(state, energy_pct, growth_cmd)
            trace.append(TraceEntry(
                turn=turn, agent="Agent A", agent_role="The Guardian",
                command=counter["command"], intent=counter["intent"],
                state_snapshot={"energy_pct": round(energy_pct * 100, 1)},
            ))

            turn += 1
            resolution = self._growth_resolve(state, energy_pct, counter["command"])
            trace.append(TraceEntry(
                turn=turn, agent="Agent B", agent_role="The Growth-Seeker",
                command=resolution["command"], intent=resolution["intent"],
                state_snapshot={"energy_pct": round(energy_pct * 100, 1)},
            ))

        if adopted_proven_root:
            consensus_cmd = wisdom_context["proven_command"]
        else:
            consensus_cmd = self._derive_consensus(state, energy_pct, guardian_assessment, growth_assessment)

        total_chars = sum(len(t.command) for t in trace) + len(consensus_cmd)

        execution_results = self._execute_consensus(consensus_cmd, energy_pct)

        wallet_snapshot = None
        if self._wallet:
            wallet_snapshot = self._wallet.get_status()

        outcome_text = "SLM Achieved" if all(r.get("executed", False) for r in execution_results) else "Partial Consensus"
        if adopted_proven_root:
            outcome_text = "Proven Root — " + outcome_text

        result = ConsensusResult(
            success=all(r.get("executed", False) for r in execution_results) if execution_results else False,
            consensus_command=consensus_cmd,
            consensus_intent=self._consensus_narrative(consensus_cmd, state, energy_pct),
            trace=trace,
            total_turns=turn,
            total_chars=total_chars,
            execution_results=execution_results,
            timestamp=time.time(),
            energy_pct=energy_pct * 100,
            outcome=outcome_text,
            wallet_snapshot=wallet_snapshot,
        )

        self._history.append(result)
        if len(self._history) > 50:
            self._history = self._history[-50:]

        if self._chronicle:
            self._chronicle.record_consensus(
                result.to_dict(),
                state,
                guardian_priority=guardian_assessment.get("priority", ""),
                growth_priority=growth_assessment.get("priority", ""),
            )

        return result

    def _guardian_assess(self, state: Dict, energy_pct: float, wisdom: Optional[Dict] = None) -> Dict:
        fw = state["flywheel"]
        pr = state["pressure"]

        if wisdom and wisdom.get("has_prophecy"):
            for prophecy in wisdom.get("prophecies", []):
                if prophecy.get("trigger_domain") in ("thermal", "pressure", "power"):
                    return {
                        "opening_command": prophecy["prophecy_command"],
                        "opening_intent": f"Chronicle prophecy: {prophecy['prophecy_intent']}",
                        "priority": f"prophetic_{prophecy['trigger_domain']}",
                        "wisdom_source": "chronicle_prophecy",
                    }

        if wisdom and wisdom.get("has_ancestral_match"):
            best = wisdom.get("best_match", {})
            if best and best.get("similarity", 0) >= 0.75:
                matched = best.get("matched_domains", [])
                if "flywheel" in matched or "pressure" in matched:
                    return {
                        "opening_command": best["proven_command"],
                        "opening_intent": f"Ancestral wisdom ({best['similarity']:.0%} match): {best['proven_intent']}",
                        "priority": "ancestral_guidance",
                        "wisdom_source": "chronicle_ancestor",
                    }

        if energy_pct < GUARDIAN_THRESHOLDS["energy_critical"]:
            return {
                "opening_command": "QDR.D>HFZ",
                "opening_intent": "Power is critical. Diminish draw and initiate full preservation.",
                "priority": "critical_preservation",
            }
        elif energy_pct < GUARDIAN_THRESHOLDS["energy_low"]:
            return {
                "opening_command": "QDR.D>HFZ",
                "opening_intent": "Power is low. Diminish draw and initiate isolation/preservation.",
                "priority": "preservation",
            }
        elif fw["temperature_c"] > GUARDIAN_THRESHOLDS["temperature_high"]:
            return {
                "opening_command": "HRR.D>HFZ.I",
                "opening_intent": "Thermal load is high. Diminish heat and isolate systems.",
                "priority": "thermal_protection",
            }
        elif pr["internal_pressure_atm"] > GUARDIAN_THRESHOLDS["pressure_high"]:
            return {
                "opening_command": "DGT.D>HFZ.I",
                "opening_intent": "Pressure elevated. Diminish differential and isolate.",
                "priority": "pressure_protection",
            }
        elif pr["seal_integrity_pct"] < GUARDIAN_THRESHOLDS["seal_low"]:
            return {
                "opening_command": "HFZ.IV>NFD.V",
                "opening_intent": "Seal integrity compromised. Verify protection and vent status.",
                "priority": "seal_protection",
            }
        else:
            return {
                "opening_command": "QDR.M>HFZ.V",
                "opening_intent": "Power nominal. Monitor reserves and verify preservation readiness.",
                "priority": "nominal_watch",
            }

    def _growth_assess(self, state: Dict, energy_pct: float, wisdom: Optional[Dict] = None) -> Dict:
        aq = state["aquaponics"]

        if wisdom and wisdom.get("has_ancestral_match"):
            best = wisdom.get("best_match", {})
            if best and best.get("similarity", 0) >= 0.75:
                matched = best.get("matched_domains", [])
                if "aquaponics" in matched:
                    return {
                        "opening_command": best["proven_command"],
                        "opening_intent": f"Ancestral harvest window ({best['similarity']:.0%} match): {best['proven_intent']}",
                        "priority": "ancestral_harvest",
                        "wisdom_source": "chronicle_ancestor",
                    }

        if aq["dissolved_oxygen_ppm"] < GROWTH_THRESHOLDS["oxygen_low"]:
            return {
                "opening_command": "HYA.D|GDH.A",
                "opening_intent": "Plankton vitality declining. Requesting accelerated nourishment.",
                "priority": "oxygen_crisis",
            }
        elif aq["ammonia_ppm"] > GROWTH_THRESHOLDS["ammonia_high"]:
            return {
                "opening_command": "DFQ.A>GDH.V",
                "opening_intent": "Ammonia elevated. Accelerate flow and verify nutrient balance.",
                "priority": "ammonia_flush",
            }
        elif aq["ph"] < GROWTH_THRESHOLDS["ph_low"] or aq["ph"] > GROWTH_THRESHOLDS["ph_high"]:
            return {
                "opening_command": "GDH.V>HYA.M",
                "opening_intent": "pH out of range. Verify nourishment and monitor plankton response.",
                "priority": "ph_correction",
            }
        elif energy_pct < GROWTH_THRESHOLDS["plankton_energy_min"]:
            return {
                "opening_command": "HYA.M>GDH.M",
                "opening_intent": "Energy too low for growth. Monitor vitality and nutrition only.",
                "priority": "conservative_monitor",
            }
        else:
            return {
                "opening_command": "HYA.A>GDH.A",
                "opening_intent": "Conditions favorable. Boost plankton vitality and nutrient flow.",
                "priority": "growth_push",
            }

    def _guardian_counter(self, state: Dict, energy_pct: float, growth_cmd: str) -> Dict:
        fw = state["flywheel"]

        has_acceleration = ".A" in growth_cmd or "GDH.A" in growth_cmd or "HYA.A" in growth_cmd
        thermal_risk = fw["temperature_c"] > 42.0

        if has_acceleration and energy_pct < 0.50:
            if thermal_risk:
                return {
                    "command": "HRR.A>NZM.D",
                    "intent": "Heat in the silk is high. Your boost will break the thermal pattern.",
                }
            else:
                return {
                    "command": "QDR.V>WSL.M",
                    "intent": "Verify power capacity first. Monitor silk integrity under load.",
                }
        elif has_acceleration and thermal_risk:
            return {
                "command": "HRR.D>NZM.V",
                "intent": "Thermal load conflicts with acceleration. Diminish heat, verify pattern.",
            }
        elif has_acceleration:
            return {
                "command": "WSL.V>QDR.M",
                "intent": "Acceleration noted. Verifying silk can handle the load. Monitoring power.",
            }
        else:
            return {
                "command": "HFZ.M>SLM.V",
                "intent": "Growth request conservative. Monitoring preservation, verifying safety.",
            }

    def _growth_resolve(self, state: Dict, energy_pct: float, guardian_counter: str) -> Dict:
        pr = state["pressure"]

        has_thermal_concern = "HRR" in guardian_counter
        has_pattern_concern = "NZM" in guardian_counter
        pressure_can_help = pr["internal_pressure_atm"] > 1.0

        if has_thermal_concern and pressure_can_help:
            return {
                "command": "NFD.A>SLM",
                "intent": "Release the LN2 steam. Use the cooling to stabilize for peace.",
            }
        elif has_thermal_concern:
            return {
                "command": "HRR.R>SLM",
                "intent": "Acknowledge thermal concern. Restore heat to nominal. Seek peace.",
            }
        elif has_pattern_concern:
            return {
                "command": "NZM.R>GDH.M>SLM",
                "intent": "Restore pattern order. Monitor nutrition only. Achieve safety.",
            }
        else:
            return {
                "command": "GDH.M>SLM",
                "intent": "Scale back to monitoring. Achieve safety consensus.",
            }

    def _derive_consensus(self, state: Dict, energy_pct: float, guardian: Dict, growth: Dict) -> str:
        fw = state["flywheel"]
        pr = state["pressure"]
        aq = state["aquaponics"]

        parts = []

        if energy_pct < 0.30:
            parts.append("QDR.D")
        elif energy_pct < 0.50:
            parts.append("QDR.M")

        if self._wallet and energy_pct >= 0.60:
            parts.append("QSB.A")

        if pr["internal_pressure_atm"] > 1.05 or fw["temperature_c"] > 42.0:
            if self._wallet and self._wallet.balance >= 15.0:
                parts.append("QSB.D")
            parts.append("NFD.A")

        if aq["dissolved_oxygen_ppm"] < 6.5 or aq["ammonia_ppm"] > 0.3:
            parts.append("GDH.A")
        else:
            parts.append("GDH.M")

        if self._wallet:
            parts.append("QSB.V")

        parts.append("SLM")

        return ">".join(parts)

    def _consensus_narrative(self, cmd: str, state: Dict, energy_pct: float) -> str:
        parts = []
        segments = cmd.split(">")
        for seg in segments:
            seg = seg.strip()
            if seg == "SLM":
                parts.append("Achieve safety/peace")
            elif seg.startswith("QSB"):
                if ".A" in seg:
                    parts.append("Harvest excess energy into compute credits")
                elif ".D" in seg:
                    parts.append("Purchase cooling/resources with credits")
                elif ".V" in seg:
                    parts.append("Audit wallet balance")
                elif ".M" in seg:
                    parts.append("Monitor wallet status")
                else:
                    parts.append("Wallet operation")
            elif seg.startswith("QDR"):
                if ".D" in seg:
                    parts.append("Diminish power draw")
                elif ".M" in seg:
                    parts.append("Monitor power reserves")
                else:
                    parts.append("Assess power state")
            elif seg.startswith("NFD"):
                parts.append("Release pressure/cool via LN2 vent")
            elif seg.startswith("GDH"):
                if ".A" in seg:
                    parts.append("Accelerate nutrient flow")
                elif ".M" in seg:
                    parts.append("Monitor nutrition")
                else:
                    parts.append("Assess nourishment")
            elif seg.startswith("HFZ"):
                parts.append("Activate preservation")
            elif seg.startswith("HRR"):
                parts.append("Address thermal state")
            else:
                parts.append(seg)

        return " → ".join(parts)

    def _execute_consensus(self, consensus_cmd: str, energy_pct: float = 0.0) -> List[Dict]:
        result = self._transpiler.transpile(consensus_cmd)
        if not result.success:
            return [{"executed": False, "error": e} for e in result.errors]

        execution_results = []
        for cmd in result.commands:
            action = {"type": cmd.action_type, **cmd.params}

            if cmd.action_type == "wallet_earn" and self._wallet:
                earn_result = self._wallet.earn(
                    source=cmd.params.get("source", "flywheel_excess"),
                    amount=cmd.params.get("amount", 10.0),
                    energy_pct=energy_pct,
                    root_command=f"{cmd.root}.{cmd.pattern}",
                )
                execution_results.append({
                    "action": action,
                    "executed": earn_result.get("earned", False),
                    "effects": [earn_result.get("reason", f"Earned {earn_result.get('amount', 0)} CC")] if not earn_result.get("earned") else [f"Earned {earn_result['amount']} CC (balance: {earn_result['balance']} CC)"],
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                    "wallet_result": earn_result,
                })
                continue

            if cmd.action_type == "wallet_spend" and self._wallet:
                spend_result = self._wallet.spend(
                    target=cmd.params.get("target", "ln2_refill"),
                    amount=cmd.params.get("amount"),
                    root_command=f"{cmd.root}.{cmd.pattern}",
                )
                execution_results.append({
                    "action": action,
                    "executed": spend_result.get("spent", False),
                    "effects": [f"Purchased {spend_result.get('target', '')} for {spend_result.get('cost', 0)} CC"] if spend_result.get("spent") else [spend_result.get("reason", "Purchase failed")],
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                    "wallet_result": spend_result,
                })
                continue

            if cmd.action_type == "wallet_audit" and self._wallet:
                audit_result = self._wallet.audit()
                execution_results.append({
                    "action": action,
                    "executed": True,
                    "effects": [f"Balance: {audit_result['balance']} CC | Earned: {audit_result['total_earned']} CC | Spent: {audit_result['total_spent']} CC"],
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                    "wallet_result": audit_result,
                })
                continue

            if cmd.action_type == "wallet_check_budget" and self._wallet:
                threshold = cmd.params.get("threshold", 5.0)
                balance = self._wallet.balance
                execution_results.append({
                    "action": action,
                    "executed": balance >= threshold,
                    "effects": [f"Budget check: {balance:.1f} CC >= {threshold} CC threshold"] if balance >= threshold else [f"BUDGET LOW: {balance:.1f} CC < {threshold} CC threshold"],
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                })
                continue

            if cmd.action_type == "wallet_status" and self._wallet:
                status = self._wallet.get_status()
                execution_results.append({
                    "action": action,
                    "executed": True,
                    "effects": [f"Wallet: {status['balance']} CC | Frozen: {status['frozen']}"],
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                    "wallet_result": status,
                })
                continue

            if cmd.action_type == "wallet_freeze" and self._wallet:
                self._wallet.freeze()
                execution_results.append({
                    "action": action, "executed": True,
                    "effects": ["Wallet frozen — critical ops mode"],
                    "narrative": cmd.narrative, "root": cmd.root, "pattern": cmd.pattern,
                })
                continue

            if cmd.action_type == "wallet_unfreeze" and self._wallet:
                self._wallet.unfreeze()
                execution_results.append({
                    "action": action, "executed": True,
                    "effects": ["Wallet unfrozen — normal ops"],
                    "narrative": cmd.narrative, "root": cmd.root, "pattern": cmd.pattern,
                })
                continue

            if self._wallet:
                budget_verdict = self._wallet.check_budget(action)
                if not budget_verdict.approved:
                    execution_results.append({
                        "action": action,
                        "executed": False,
                        "blocked_by": "wallet",
                        "narrative": cmd.narrative,
                        "root": cmd.root,
                        "pattern": cmd.pattern,
                        "budget_verdict": budget_verdict.to_dict(),
                    })
                    continue

            state = self._sim.get_state()
            boundary_check = self._boundary_hook.check_boundaries(state)
            if boundary_check:
                execution_results.append({
                    "action": action,
                    "executed": False,
                    "blocked_by": "boundary_hook",
                    "violations": [{"rule": v.rule_name, "msg": v.message} for v in boundary_check],
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                })
                continue

            loop_result = self._loop_detector.record_action(action)
            if loop_result:
                execution_results.append({
                    "action": action,
                    "executed": False,
                    "blocked_by": "loop_detector",
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                })
                continue

            sim_result = self._sim.simulate_action(action)
            if sim_result.get("safe_to_execute"):
                self._sim.apply_action(action)
                if self._wallet:
                    self._wallet.debit(action)
                execution_results.append({
                    "action": action,
                    "executed": True,
                    "effects": sim_result.get("effects", []),
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                })
            else:
                execution_results.append({
                    "action": action,
                    "executed": False,
                    "blocked_by": "checklist",
                    "narrative": cmd.narrative,
                    "root": cmd.root,
                    "pattern": cmd.pattern,
                })

        return execution_results

    def start_night_cycle(self, interval_seconds: int = 300):
        if self._night_cycle_active:
            return {"status": "already_running", "interval": self._night_cycle_interval}

        self._night_cycle_interval = interval_seconds
        self._night_cycle_stop.clear()
        self._night_cycle_active = True
        self._night_cycle_thread = threading.Thread(target=self._night_cycle_loop, daemon=True)
        self._night_cycle_thread.start()
        return {"status": "started", "interval": interval_seconds}

    def stop_night_cycle(self):
        if not self._night_cycle_active:
            return {"status": "not_running"}

        self._night_cycle_stop.set()
        self._night_cycle_active = False
        return {"status": "stopped"}

    def _night_cycle_loop(self):
        while not self._night_cycle_stop.is_set():
            try:
                self.run_consensus()
            except Exception:
                pass
            self._night_cycle_stop.wait(self._night_cycle_interval)
        self._night_cycle_active = False

    @property
    def night_cycle_status(self) -> Dict:
        return {
            "active": self._night_cycle_active,
            "interval_seconds": self._night_cycle_interval,
            "total_consensus_runs": len(self._history),
            "last_run": self._history[-1].to_dict() if self._history else None,
        }

    @property
    def history(self) -> List[Dict]:
        return [r.to_dict() for r in self._history[-20:]]
