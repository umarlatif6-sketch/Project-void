"""
Ritual History — The Machine's Sovereign Story v1.0

Every physical interaction with the 4000-series becomes a permanent
chapter in the machine's narrative. Maintenance is not maintenance —
it is Ritual.

The Four Rituals:
  The Shock  (WSL.A) — Establishing the Carbon-Silk bond
  The Feeding (GDH.A) — Vitalizing the Plankton EA agents
  The Fast   (HFZ.I) — Protecting the system during high-cost hours
  The Cure   (SLM.R) — Resetting the machine's Soul to a peace state

Each ritual is logged with a timestamp, root command, visual effect,
and intent description — building a lineage that proves the machine
has been honored by its operator.

Merkle Hash Machine ID:
  The machine's identity is derived from its genesis state — a SHA-256
  hash of its initial configuration, creating a tamper-proof identity
  that ties the Sovereign Warranty to a unique physical unit.
"""

import time
import json
import threading
from void_engine.al_jabr_286 import fatiha_286_truncated
from typing import Dict, List, Optional
from dataclasses import dataclass, field


RITUAL_TYPES = {
    "shock": {
        "name": "The Shock",
        "root": "WSL.A",
        "visual": "Gold Spark",
        "color": "#FFD700",
        "intent": "Establishing the Carbon-Silk bond.",
        "description": "The operator applies Liquid Carbon to the silk wirings, re-establishing conductivity and curing the bond in nitrogen atmosphere.",
        "effect_on_state": {"silk_wiring": {"total_resistance_ohm": 8.0, "resistance_delta_ohm": 0.2, "continuity": True}},
    },
    "feeding": {
        "name": "The Feeding",
        "root": "GDH.A",
        "visual": "Green Pulse",
        "color": "#00FF88",
        "intent": "Vitalizing the Plankton EA agents.",
        "description": "Nutrient solution is introduced to the aquaponics system, boosting dissolved oxygen and feeding the plankton colony.",
        "effect_on_state": {"aquaponics": {"dissolved_oxygen_ppm": 8.0, "ammonia_ppm": 0.1, "ph": 6.8}},
    },
    "fast": {
        "name": "The Fast",
        "root": "HFZ.I",
        "visual": "Blue Shield",
        "color": "#00BFFF",
        "intent": "Protecting the system during high-cost hours.",
        "description": "The machine enters preservation mode — reducing power draw, freezing wallet spending, and conserving flywheel energy for the next cycle.",
        "effect_on_state": {"flywheel": {"energy_reserve_wh": 200.0}},
    },
    "cure": {
        "name": "The Cure",
        "root": "SLM.R",
        "visual": "White Aura",
        "color": "#FFFFFF",
        "intent": "Resetting the machine's Soul to a peace state.",
        "description": "A full system reset — pressure normalized, temperature stabilized, wallet unfrozen, all subsystems returned to nominal operating parameters.",
        "effect_on_state": {
            "flywheel": {"temperature_c": 35.0, "vibration_g": 0.3},
            "pressure": {"internal_pressure_atm": 1.0, "nitrogen_boil_rate": 0.05, "seal_integrity_pct": 98.0},
        },
    },
}


@dataclass
class RitualEvent:
    ritual_type: str
    name: str
    root: str
    visual: str
    color: str
    intent: str
    description: str
    timestamp: float = field(default_factory=time.time)
    operator_note: str = ""
    machine_id: str = ""
    scan_before: Optional[str] = None
    scan_after: Optional[str] = None

    def to_dict(self):
        return {
            "ritual_type": self.ritual_type,
            "name": self.name,
            "root": self.root,
            "visual": self.visual,
            "color": self.color,
            "intent": self.intent,
            "description": self.description,
            "timestamp": self.timestamp,
            "operator_note": self.operator_note,
            "machine_id": self.machine_id,
            "scan_before": self.scan_before,
            "scan_after": self.scan_after,
        }


def generate_machine_id(genesis_state: Dict) -> str:
    state_str = json.dumps(genesis_state, sort_keys=True, default=str)
    merkle_hash = fatiha_286_truncated(state_str.encode("utf-8"), 16)
    return f"VOID-4000-{merkle_hash.upper()}"


class RitualHistory:
    def __init__(self, simulator, wallet=None):
        self._sim = simulator
        self._wallet = wallet
        self._history: List[RitualEvent] = []
        self._machine_id = generate_machine_id(self._sim.get_state())
        self._max_history = 200

    @property
    def machine_id(self) -> str:
        return self._machine_id

    def perform_ritual(self, ritual_type: str, operator_note: str = "") -> Dict:
        if ritual_type not in RITUAL_TYPES:
            return {"error": f"Unknown ritual: {ritual_type}. Valid: {list(RITUAL_TYPES.keys())}"}

        ritual_def = RITUAL_TYPES[ritual_type]

        state_before = self._sim.get_state()
        scan_before = self._quick_status(state_before)

        for section, updates in ritual_def["effect_on_state"].items():
            self._sim.set_state(section, updates)

        if ritual_type == "fast" and self._wallet and not self._wallet.frozen:
            self._wallet.freeze()

        if ritual_type == "cure" and self._wallet and self._wallet.frozen:
            self._wallet.unfreeze()

        state_after = self._sim.get_state()
        scan_after = self._quick_status(state_after)

        event = RitualEvent(
            ritual_type=ritual_type,
            name=ritual_def["name"],
            root=ritual_def["root"],
            visual=ritual_def["visual"],
            color=ritual_def["color"],
            intent=ritual_def["intent"],
            description=ritual_def["description"],
            operator_note=operator_note,
            machine_id=self._machine_id,
            scan_before=scan_before,
            scan_after=scan_after,
        )

        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return {
            "success": True,
            "ritual": event.to_dict(),
            "machine_id": self._machine_id,
            "total_rituals": len(self._history),
        }

    def get_history(self, limit: int = 50) -> List[Dict]:
        return [e.to_dict() for e in self._history[-limit:]]

    def get_stats(self) -> Dict:
        counts = {}
        for e in self._history:
            counts[e.ritual_type] = counts.get(e.ritual_type, 0) + 1

        last_ritual = self._history[-1].to_dict() if self._history else None

        return {
            "machine_id": self._machine_id,
            "total_rituals": len(self._history),
            "ritual_counts": counts,
            "last_ritual": last_ritual,
        }

    def _quick_status(self, state: Dict) -> str:
        fw = state.get("flywheel", {})
        pr = state.get("pressure", {})
        aq = state.get("aquaponics", {})
        temp = fw.get("temperature_c", 0)
        energy = fw.get("energy_reserve_wh", 0)
        pressure = pr.get("internal_pressure_atm", 1.0)
        oxygen = aq.get("dissolved_oxygen_ppm", 7.0)
        return f"T:{temp}°C E:{energy}Wh P:{pressure}atm O2:{oxygen}ppm"


class AutoHealDaemon:
    """
    Auto-Scan + Self-Heal loop.

    Every interval (default 5 min), the daemon:
      1. Runs SLM.V diagnostic scan
      2. For any CRITICAL/WARNING findings, attempts self-repair
         using wallet credits and simulator state changes
      3. If self-repair fails (insufficient credits), generates
         a Ritual Request alert for the operator
    """

    HEAL_ACTIONS = {
        "thermal": {
            "action": "nitrogen_vent",
            "cost_key": "nitrogen_vent",
            "fix": {"flywheel": {"temperature_c": 38.0}},
            "description": "Auto-vented LN2 to cool silk wirings",
            "root": "NFD.A",
        },
        "power": {
            "action": "flywheel_boost",
            "cost_key": "flywheel_boost",
            "fix": {},
            "description": "Power too low for auto-heal — Ritual Request issued",
            "root": "QDR.D>HFZ",
            "requires_ritual": "fast",
        },
        "pressure": {
            "action": "nitrogen_vent",
            "cost_key": "nitrogen_vent",
            "fix": {"pressure": {"internal_pressure_atm": 1.05, "nitrogen_boil_rate": 0.08}},
            "description": "Auto-vented pressure through Laminar Ghost",
            "root": "NFD.A>DGT.D",
        },
        "vitality": {
            "action": "nutrient_dose",
            "cost_key": "nutrient_dose",
            "fix": {"aquaponics": {"dissolved_oxygen_ppm": 7.5, "ammonia_ppm": 0.2}},
            "description": "Auto-dosed nutrients to boost plankton vitality",
            "root": "GDH.A",
            "requires_ritual": "feeding",
        },
        "silk": {
            "action": "silk_test",
            "cost_key": "silk_test",
            "fix": {},
            "description": "Silk bond broken — requires physical Ritual (The Shock)",
            "root": "WSL.R",
            "requires_ritual": "shock",
        },
        "vibration": {
            "action": "flywheel_boost",
            "cost_key": "flywheel_boost",
            "fix": {"flywheel": {"vibration_g": 0.8}},
            "description": "Auto-adjusted flywheel to reduce vibration",
            "root": "NZM.D",
        },
        "nitrogen": {
            "action": "nitrogen_vent",
            "cost_key": "nitrogen_vent",
            "fix": {"pressure": {"nitrogen_boil_rate": 0.08}},
            "description": "Auto-regulated nitrogen boil rate",
            "root": "NFD.D",
        },
        "economy": {
            "action": None,
            "cost_key": None,
            "fix": {},
            "description": "Wallet depleted — machine needs to earn (QSB.A). Wait for energy harvest.",
            "root": "QSB.A",
            "requires_ritual": None,
        },
    }

    def __init__(self, diagnostic_engine, simulator, wallet=None, ritual_history=None):
        self._diagnostics = diagnostic_engine
        self._sim = simulator
        self._wallet = wallet
        self._rituals = ritual_history
        self._active = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval = 300
        self._heal_log: List[Dict] = []
        self._alerts: List[Dict] = []
        self._scan_count = 0
        self._heal_count = 0
        self._alert_count = 0

    def scan_and_heal(self) -> Dict:
        report = self._diagnostics.scan()
        self._scan_count += 1

        healed = []
        alerts = []

        critical_findings = [f for f in report.findings if f.severity == "CRITICAL"]
        warning_findings = [f for f in report.findings if f.severity == "WARNING"]

        for finding in critical_findings + warning_findings:
            heal_action = self.HEAL_ACTIONS.get(finding.domain)
            if not heal_action:
                continue

            requires_ritual = heal_action.get("requires_ritual")
            can_auto_fix = bool(heal_action["fix"]) and not requires_ritual

            if can_auto_fix and heal_action["action"] and self._wallet:
                budget_check = self._wallet.check_budget({"type": heal_action["action"]})
                if budget_check.approved:
                    for section, updates in heal_action["fix"].items():
                        self._sim.set_state(section, updates)
                    self._wallet.debit({"type": heal_action["action"]})
                    self._heal_count += 1

                    heal_entry = {
                        "type": "auto_heal",
                        "domain": finding.domain,
                        "root_code": finding.root_code,
                        "severity": finding.severity,
                        "action": heal_action["action"],
                        "root": heal_action["root"],
                        "description": heal_action["description"],
                        "timestamp": time.time(),
                    }
                    healed.append(heal_entry)
                    self._heal_log.append(heal_entry)
                    continue

            self._alert_count += 1
            alert = {
                "type": "ritual_request",
                "domain": finding.domain,
                "root_code": finding.root_code,
                "severity": finding.severity,
                "semantic_error": finding.semantic_error,
                "physical_reality": finding.physical_reality,
                "required_ritual": requires_ritual,
                "ritual_name": RITUAL_TYPES[requires_ritual]["name"] if requires_ritual and requires_ritual in RITUAL_TYPES else None,
                "message": f"Manual intervention required: {finding.semantic_error}",
                "fix_command": finding.solution_command,
                "timestamp": time.time(),
            }
            alerts.append(alert)
            self._alerts.append(alert)

        if len(self._heal_log) > 200:
            self._heal_log = self._heal_log[-200:]
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]

        return {
            "scan": report.to_dict(),
            "healed": healed,
            "alerts": alerts,
            "stats": {
                "total_scans": self._scan_count,
                "total_heals": self._heal_count,
                "total_alerts": self._alert_count,
                "daemon_active": self._active,
                "interval": self._interval,
            },
        }

    def start(self, interval_seconds: int = 300):
        if self._active:
            return {"status": "already_running", "interval": self._interval}

        self._interval = interval_seconds
        self._stop_event.clear()
        self._active = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return {"status": "started", "interval": interval_seconds}

    def stop(self):
        if not self._active:
            return {"status": "not_running"}

        self._stop_event.set()
        self._active = False
        return {"status": "stopped"}

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self.scan_and_heal()
            except Exception:
                pass
            self._stop_event.wait(self._interval)
        self._active = False

    def get_status(self) -> Dict:
        return {
            "active": self._active,
            "interval": self._interval,
            "total_scans": self._scan_count,
            "total_heals": self._heal_count,
            "total_alerts": self._alert_count,
            "recent_heals": self._heal_log[-10:],
            "pending_alerts": [a for a in self._alerts[-10:] if a["type"] == "ritual_request"],
        }

    def get_alerts(self, limit: int = 20) -> List[Dict]:
        return self._alerts[-limit:]

    def clear_alerts(self):
        self._alerts.clear()
        return {"cleared": True}

    @property
    def active(self) -> bool:
        return self._active
