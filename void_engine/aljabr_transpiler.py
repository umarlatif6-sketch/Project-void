"""
Al-Jabr Transpiler — Root-Pattern AI Logic v1.0

Classical Arabic root-and-pattern system for 10x+ compression.
Trilateral roots carry semantic "clouds" of meaning; patterns (verb forms)
shape how that meaning is applied. A single 3-letter root can trigger
an entire pre-verified logic sequence across the 4000-series machine.

Grammar:
  bare root   = HFZ           (full domain sequence — all relevant patterns)
  root.pat    = HFZ.I         (specific pattern: Isolate)
  multi-pat   = HFZ.IV        (multiple patterns: Isolate + Verify)
  chain       = HFZ>QDR       (sequential: first HFZ, then QDR)
  branch      = HFZ|SLM       (conditional OR)

Patterns:
  A = Accelerate   D = Diminish   I = Isolate   V = Verify
  M = Monitor      R = Restore    T = Transmit
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


TASK_PRECISION = "PRECISION"
TASK_STANDARD = "STANDARD"
TASK_BULK = "BULK"

_DEFAULT_MODEL_CONFIG = {
    TASK_PRECISION: {
        "model": "gpt-5-mini",
        "base_url": None,
        "label": "Precision",
        "description": "Logic checks, safety audits, Adriana dialect generation",
        "cost_per_1k_tokens": 0.0003,
    },
    TASK_STANDARD: {
        "model": "gpt-5-mini",
        "base_url": None,
        "label": "Standard",
        "description": "General reasoning, research, profile analysis",
        "cost_per_1k_tokens": 0.0003,
    },
    TASK_BULK: {
        "model": "gpt-5-mini",
        "base_url": None,
        "label": "Bulk",
        "description": "Agent simulation, gibberish decoding, batch analysis",
        "cost_per_1k_tokens": 0.0003,
    },
}

_DB_CONFIG_TABLE = "ai_model_router_config"
_DB_COST_TABLE = "ai_model_cost_log"


PATTERNS = {
    "A": {"name": "Accelerate", "verb": "increase / boost / amplify"},
    "I": {"name": "Isolate", "verb": "protect / shield / contain"},
    "V": {"name": "Verify", "verb": "check / validate / diagnose"},
    "M": {"name": "Monitor", "verb": "observe / read / sense"},
    "R": {"name": "Restore", "verb": "reset / heal / return to nominal"},
    "D": {"name": "Diminish", "verb": "reduce / slow / cool"},
    "T": {"name": "Transmit", "verb": "signal / send / broadcast"},
}

DEFAULT_BARE_PATTERNS = {
    "aqua": ["M", "V", "R"],
    "flywheel": ["M", "V", "R"],
    "silk": ["M", "V", "R"],
    "pressure": ["M", "V", "I"],
    "economy": ["V", "M"],
    "system": ["V"],
    "steganography": ["V", "M"],
    "chronicle": ["V", "M"],
    "radiance": ["V", "M"],
}


@dataclass
class RootEntry:
    root: str
    domain: str
    essence: str
    description: str


@dataclass
class RootPatternCommand:
    action_type: str
    params: Dict
    narrative: str
    root: str
    pattern: str
    pattern_name: str


@dataclass
class AlJabrResult:
    success: bool
    expression: str
    roots_resolved: List[Dict]
    commands: List[RootPatternCommand]
    errors: List[str]
    compression: Dict
    narrative: str
    transpile_time_ms: float

    def to_dict(self):
        return {
            "success": self.success,
            "expression": self.expression,
            "roots_resolved": self.roots_resolved,
            "commands": [
                {
                    "action_type": c.action_type,
                    "params": c.params,
                    "narrative": c.narrative,
                    "root": c.root,
                    "pattern": c.pattern,
                    "pattern_name": c.pattern_name,
                }
                for c in self.commands
            ],
            "errors": self.errors,
            "compression": self.compression,
            "narrative": self.narrative,
            "transpile_time_ms": round(self.transpile_time_ms, 3),
        }


ROOT_PATTERN_ACTIONS = {
    "HFZ": {
        "A": [("air_curtain_activate", {"velocity_ms": 20.0}, "Amplify Air Curtain — maximum shielding velocity")],
        "I": [("air_curtain_activate", {"velocity_ms": 15.0}, "Activate Air Curtain — isolate chamber from pressure differential")],
        "V": [
            ("sensor_calibrate", {"sensor": "pressure_internal"}, "Verify internal pressure reading"),
            ("sensor_calibrate", {"sensor": "air_curtain_velocity"}, "Verify Air Curtain velocity sensor"),
            ("sensor_calibrate", {"sensor": "seal_integrity"}, "Verify seal integrity sensor"),
        ],
        "M": [("sensor_calibrate", {"sensor": "pressure_internal"}, "Monitor chamber pressure state")],
        "R": [
            ("air_curtain_deactivate", {}, "Restore — deactivate Air Curtain to nominal"),
            ("nitrogen_vent", {"vent_rate": 0.1}, "Restore — gentle nitrogen vent to equalize pressure"),
        ],
        "D": [("air_curtain_deactivate", {}, "Diminish — power down Air Curtain")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit pressure status via Silk Web")],
    },
    "QDR": {
        "A": [("flywheel_boost", {"rpm_delta": 500}, "Accelerate flywheel — boost RPM by 500")],
        "I": [("sensor_calibrate", {"sensor": "flywheel_vibration"}, "Isolate flywheel — check vibration before load increase")],
        "V": [
            ("sensor_calibrate", {"sensor": "flywheel_rpm"}, "Verify flywheel RPM"),
            ("sensor_calibrate", {"sensor": "flywheel_energy"}, "Verify energy reserve (Wh)"),
        ],
        "M": [("sensor_calibrate", {"sensor": "flywheel_rpm"}, "Monitor flywheel RPM")],
        "R": [("flywheel_boost", {"rpm_delta": -200}, "Restore — reduce RPM toward nominal")],
        "D": [("flywheel_boost", {"rpm_delta": -500}, "Diminish — decelerate flywheel by 500 RPM")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit flywheel telemetry via Silk Web")],
    },
    "HRR": {
        "A": [("flywheel_boost", {"rpm_delta": 100}, "Accelerate — gentle RPM increase, monitor thermal")],
        "I": [("sensor_calibrate", {"sensor": "flywheel_temperature"}, "Isolate thermal — read temperature before action")],
        "V": [("sensor_calibrate", {"sensor": "flywheel_temperature"}, "Verify flywheel temperature is within range")],
        "M": [("sensor_calibrate", {"sensor": "flywheel_temperature"}, "Monitor flywheel thermal state")],
        "R": [("flywheel_boost", {"rpm_delta": -300}, "Restore — reduce RPM to cool flywheel")],
        "D": [("flywheel_boost", {"rpm_delta": -500}, "Diminish — emergency thermal reduction")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit thermal alert via Silk Web")],
    },
    "HYA": {
        "A": [("nutrient_dose", {"dose_ml": 10}, "Accelerate plankton vitality — nutrient boost")],
        "I": [("sensor_calibrate", {"sensor": "aqua_dissolved_oxygen"}, "Isolate plankton — check dissolved oxygen")],
        "V": [
            ("sensor_calibrate", {"sensor": "aqua_dissolved_oxygen"}, "Verify plankton dissolved oxygen level"),
            ("sensor_calibrate", {"sensor": "aqua_temperature"}, "Verify water temperature for plankton"),
        ],
        "M": [("sensor_calibrate", {"sensor": "aqua_dissolved_oxygen"}, "Monitor plankton life state")],
        "R": [
            ("pump_cycle", {"count": 1}, "Restore — fresh water circulation for plankton recovery"),
            ("nutrient_dose", {"dose_ml": 5}, "Restore — gentle nutrient dose for stabilization"),
        ],
        "D": [("sensor_calibrate", {"sensor": "aqua_ammonia"}, "Diminish — check ammonia (toxicity risk)")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit plankton vitality report via Silk Web")],
    },
    "GDH": {
        "A": [("nutrient_dose", {"dose_ml": 15}, "Accelerate nourishment — heavy nutrient dose")],
        "I": [("sensor_calibrate", {"sensor": "aqua_ph"}, "Isolate nourishment — verify pH before dosing")],
        "V": [
            ("sensor_calibrate", {"sensor": "aqua_ph"}, "Verify pH balance"),
            ("sensor_calibrate", {"sensor": "aqua_ammonia"}, "Verify ammonia level"),
        ],
        "M": [("sensor_calibrate", {"sensor": "aqua_ph"}, "Monitor pH and nutrient levels")],
        "R": [("sensor_calibrate", {"sensor": "aqua_ph"}, "Restore — recalibrate pH sensor to baseline")],
        "D": [("pump_cycle", {"count": 1}, "Diminish — flush excess nutrients via pump cycle")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit nutrient report via Silk Web")],
    },
    "DFQ": {
        "A": [("pump_cycle", {"count": 2}, "Accelerate flow — double pump cycle")],
        "I": [("sensor_calibrate", {"sensor": "aqua_water_level"}, "Isolate flow — check water level before pumping")],
        "V": [
            ("sensor_calibrate", {"sensor": "aqua_pump_cycles"}, "Verify pump cycle count this hour"),
            ("sensor_calibrate", {"sensor": "aqua_water_level"}, "Verify water level"),
        ],
        "M": [("sensor_calibrate", {"sensor": "aqua_pump_cycles"}, "Monitor pump cycle rate")],
        "R": [("pump_cycle", {"count": 1}, "Restore — single pump cycle for gentle circulation")],
        "D": [("sensor_calibrate", {"sensor": "aqua_pump_cycles"}, "Diminish — check if pump rate is too high")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit flow status via Silk Web")],
    },
    "WSL": {
        "A": [("silk_test", {"strand_id": 0}, "Accelerate — stress test primary silk strand")],
        "I": [("sensor_calibrate", {"sensor": "silk_total_resistance"}, "Isolate — measure total strand resistance")],
        "V": [
            ("silk_test", {"strand_id": 0}, "Verify strand 0 integrity"),
            ("silk_test", {"strand_id": 1}, "Verify strand 1 integrity"),
            ("sensor_calibrate", {"sensor": "silk_resistance_delta"}, "Verify resistance drift"),
        ],
        "M": [("sensor_calibrate", {"sensor": "silk_total_resistance"}, "Monitor silk strand resistance")],
        "R": [("silk_test", {"strand_id": 0}, "Restore — re-test primary strand after repair")],
        "D": [("sensor_calibrate", {"sensor": "silk_resistance_delta"}, "Diminish — check for resistance drift decay")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit silk wiring report via Silk Web")],
    },
    "NZM": {
        "A": [
            ("silk_test", {"strand_id": 0}, "Accelerate — test strand 0"),
            ("silk_test", {"strand_id": 1}, "Accelerate — test strand 1"),
            ("silk_test", {"strand_id": 2}, "Accelerate — test strand 2"),
        ],
        "I": [("sensor_calibrate", {"sensor": "silk_strand_count"}, "Isolate — count active strands")],
        "V": [
            ("sensor_calibrate", {"sensor": "silk_strand_count"}, "Verify active strand count"),
            ("sensor_calibrate", {"sensor": "silk_resistance_delta"}, "Verify resistance pattern uniformity"),
        ],
        "M": [("sensor_calibrate", {"sensor": "silk_strand_count"}, "Monitor strand network order")],
        "R": [("silk_test", {"strand_id": 0}, "Restore — recalibrate primary strand")],
        "D": [("sensor_calibrate", {"sensor": "silk_resistance_delta"}, "Diminish — detect resistance anomalies")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit network pattern report via Silk Web")],
    },
    "DGT": {
        "A": [("nitrogen_vent", {"vent_rate": 0.05}, "Accelerate — controlled micro-vent to test pressure response")],
        "I": [("air_curtain_activate", {"velocity_ms": 12.0}, "Isolate — light air curtain for pressure containment")],
        "V": [
            ("sensor_calibrate", {"sensor": "pressure_internal"}, "Verify internal pressure"),
            ("sensor_calibrate", {"sensor": "nitrogen_boil_rate"}, "Verify nitrogen boil rate"),
        ],
        "M": [("sensor_calibrate", {"sensor": "pressure_internal"}, "Monitor pressure differential")],
        "R": [("nitrogen_vent", {"vent_rate": 0.2}, "Restore — vent to equalize pressure differential")],
        "D": [("nitrogen_vent", {"vent_rate": 0.3}, "Diminish — aggressive vent to reduce internal pressure")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit pressure differential report via Silk Web")],
    },
    "NFD": {
        "A": [("nitrogen_vent", {"vent_rate": 0.5}, "Accelerate — maximum nitrogen vent")],
        "I": [("sensor_calibrate", {"sensor": "seal_integrity"}, "Isolate — check seal before venting")],
        "V": [
            ("sensor_calibrate", {"sensor": "seal_integrity"}, "Verify seal integrity before vent"),
            ("sensor_calibrate", {"sensor": "pressure_internal"}, "Verify current pressure before vent"),
        ],
        "M": [("sensor_calibrate", {"sensor": "nitrogen_boil_rate"}, "Monitor nitrogen state")],
        "R": [("nitrogen_vent", {"vent_rate": 0.1}, "Restore — gentle vent to return to nominal")],
        "D": [("nitrogen_vent", {"vent_rate": 0.3}, "Diminish — reduce pressure via controlled vent")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit vent status via Silk Web")],
    },
    "QSB": {
        "A": [("wallet_earn", {"source": "flywheel_excess", "amount": 10.0}, "Acquire — harvest excess flywheel energy into compute credits")],
        "I": [("wallet_freeze", {}, "Isolate — freeze wallet spending during critical operations")],
        "V": [
            ("wallet_audit", {}, "Verify wallet balance and transaction integrity"),
            ("wallet_check_budget", {"threshold": 5.0}, "Verify sufficient budget for next operation"),
        ],
        "M": [("wallet_status", {}, "Monitor wallet balance and earning rate")],
        "R": [("wallet_unfreeze", {}, "Restore — unfreeze wallet after critical period")],
        "D": [("wallet_spend", {"target": "ln2_refill", "amount": 15.0}, "Disburse — purchase LN2 cooling refill")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit wallet ledger via Silk Web")],
    },
    "SLM": {
        "A": None,
        "I": None,
        "V": [
            ("sensor_calibrate", {"sensor": "pressure_internal"}, "Verify pressure system integrity"),
            ("sensor_calibrate", {"sensor": "air_curtain_velocity"}, "Verify Air Curtain readiness"),
            ("sensor_calibrate", {"sensor": "seal_integrity"}, "Verify seal integrity"),
            ("sensor_calibrate", {"sensor": "aqua_dissolved_oxygen"}, "Verify plankton vitality"),
            ("sensor_calibrate", {"sensor": "aqua_ph"}, "Verify pH balance"),
            ("sensor_calibrate", {"sensor": "flywheel_rpm"}, "Verify flywheel RPM"),
            ("sensor_calibrate", {"sensor": "flywheel_energy"}, "Verify energy reserve"),
            ("sensor_calibrate", {"sensor": "silk_total_resistance"}, "Verify silk strand resistance"),
        ],
        "M": [
            ("sensor_calibrate", {"sensor": "pressure_internal"}, "Monitor pressure"),
            ("sensor_calibrate", {"sensor": "aqua_dissolved_oxygen"}, "Monitor plankton"),
            ("sensor_calibrate", {"sensor": "flywheel_rpm"}, "Monitor flywheel"),
            ("sensor_calibrate", {"sensor": "silk_total_resistance"}, "Monitor silk"),
        ],
        "R": None,
        "D": None,
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit full system status via Silk Web")],
    },
    "BTR": {
        "A": [("emergency_shutdown", {"target": "all", "severity": "critical"}, "Accelerate severance — emergency shutdown of all systems")],
        "I": [("emergency_shutdown", {"target": "signal", "severity": "isolate"}, "Isolate corrupted signal — sever from network")],
        "V": [("signal_integrity_check", {"target": "all"}, "Verify signal integrity across all channels")],
        "M": [("signal_integrity_check", {"target": "monitor"}, "Monitor for corrupted signals")],
        "R": [("signal_restore", {"target": "all"}, "Restore — reconnect severed signals after purge")],
        "D": [("emergency_shutdown", {"target": "partial", "severity": "controlled"}, "Diminish — controlled partial shutdown")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit severance alert via Silk Web")],
    },
    "TRK": {
        "A": [("flywheel_boost", {"rpm_delta": 300, "mode": "vortex"}, "Accelerate vortex — increase flywheel RPM for kinetic harvest")],
        "I": [("sensor_calibrate", {"sensor": "flywheel_vibration"}, "Isolate kinetic — check vibration before vortex engagement")],
        "V": [
            ("sensor_calibrate", {"sensor": "flywheel_rpm"}, "Verify vortex RPM"),
            ("sensor_calibrate", {"sensor": "flywheel_energy"}, "Verify kinetic energy reserve"),
        ],
        "M": [("sensor_calibrate", {"sensor": "flywheel_rpm"}, "Monitor vortex rotation state")],
        "R": [("flywheel_boost", {"rpm_delta": -150, "mode": "vortex"}, "Restore — reduce vortex RPM toward nominal")],
        "D": [("flywheel_boost", {"rpm_delta": -300, "mode": "vortex"}, "Diminish — decelerate vortex rotation")],
        "T": [("burst_generate", {"frequency": 432.0, "source": "vortex"}, "Transmit — generate burst signal from vortex energy")],
    },
    "SHR": {
        "A": [("sensor_calibrate", {"sensor": "all", "mode": "deep_scan"}, "Accelerate observation — deep scan all sensors")],
        "I": [("sensor_calibrate", {"sensor": "digital_moss", "mode": "isolate"}, "Isolate — focus Digital Moss on single-point reading")],
        "V": [
            ("sensor_calibrate", {"sensor": "digital_moss"}, "Verify Digital Moss sensor integrity"),
            ("resonance_purity_check", {"frequency": 432.0}, "Verify 432 Hz resonance purity"),
        ],
        "M": [
            ("sensor_calibrate", {"sensor": "digital_moss"}, "Monitor Digital Moss presence layer"),
            ("sensor_calibrate", {"sensor": "resonance_field"}, "Monitor resonance field strength"),
        ],
        "R": [("sensor_calibrate", {"sensor": "digital_moss", "mode": "recalibrate"}, "Restore — recalibrate Digital Moss baseline")],
        "D": [("sensor_calibrate", {"sensor": "digital_moss", "mode": "low_power"}, "Diminish — reduce sensor polling rate")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit sensor observation report via Silk Web")],
    },
    "KTM": {
        "A": [("stega_encode", {"mode": "vortex_scatter", "frequency": 432.0}, "Accelerate — encode payload using vortex scatter steganography")],
        "I": [("stega_encode", {"mode": "standard", "frequency": 432.0}, "Isolate — standard LSB encode with 432 Hz pocket")],
        "V": [
            ("stega_capacity_check", {"frequency": 432.0}, "Verify carrier steganographic capacity"),
            ("stega_decode", {"mode": "verify"}, "Verify — decode and validate hidden payload integrity"),
        ],
        "M": [("stega_capacity_check", {"frequency": 432.0}, "Monitor carrier capacity and payload density")],
        "R": [("stega_decode", {"mode": "full"}, "Restore — extract and recover hidden payload")],
        "D": [("stega_dither", {"intensity": 0.5}, "Diminish — apply dither to reduce steganographic footprint")],
        "T": [("stega_encode", {"mode": "burst", "frequency": 432.0}, "Transmit — encode and burst-transmit hidden payload")],
    },
    "JDR": {
        "A": [("chronicle_store", {"scope": "full", "include_state": True}, "Accelerate — write full state snapshot to Root-Chronicle")],
        "I": [("chronicle_store", {"scope": "minimal"}, "Isolate — store minimal consensus record only")],
        "V": [
            ("chronicle_recall", {"query": "latest"}, "Verify — recall latest chronicle entry for validation"),
            ("chronicle_recall", {"query": "genesis"}, "Verify genesis seed integrity"),
        ],
        "M": [("chronicle_recall", {"query": "stats"}, "Monitor chronicle size and entry count")],
        "R": [("chronicle_import_seed", {"source": "genesis"}, "Restore — import genesis seed to rebuild chronicle")],
        "D": [("chronicle_export", {"format": "compressed"}, "Diminish — export compressed chronicle archive")],
        "T": [("chronicle_export", {"format": "full"}, "Transmit — export full chronicle for external consumption")],
    },
    "ZHR": {
        "A": [("radiance_glow", {"intensity": 1.0, "source": "silk_pulse"}, "Accelerate radiance — maximum glow from silk pulse")],
        "I": [("radiance_glow", {"intensity": 0.5, "source": "algae"}, "Isolate — focus radiance on glow algae only")],
        "V": [
            ("radiance_check", {"source": "all"}, "Verify radiance state — check motion-to-light correlation"),
            ("radiance_motion_light_axiom", {"threshold": 300, "source": "TRK"}, "Verify ZHR axiom — if TRK.A > threshold then ZHR.A (motion→light)"),
        ],
        "M": [
            ("radiance_check", {"source": "algae"}, "Monitor glow algae luminescence"),
            ("radiance_density_correlation", {}, "Monitor data-density to radiance correlation"),
        ],
        "R": [("radiance_glow", {"intensity": 0.0, "source": "all"}, "Restore — dim all radiance to baseline")],
        "D": [("radiance_glow", {"intensity": 0.2, "source": "all"}, "Diminish — reduce radiance to low-power glow")],
        "T": [("sensor_calibrate", {"sensor": "silk_web"}, "Transmit radiance report via Silk Web")],
    },
}


class AlJabrManifest:
    def __init__(self, manifest_path: Optional[str] = None):
        self._roots: Dict[str, RootEntry] = {}
        self._by_domain: Dict[str, List[RootEntry]] = {}

        if manifest_path is None:
            manifest_path = os.path.join(os.path.dirname(__file__), "aljabr.roots")
        self._load(manifest_path)

    def _load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("=") or line.startswith("-"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 4:
                    continue
                entry = RootEntry(
                    root=parts[0],
                    domain=parts[1],
                    essence=parts[2],
                    description=parts[3],
                )
                self._roots[entry.root] = entry
                self._by_domain.setdefault(entry.domain, []).append(entry)

    def resolve(self, root: str) -> Optional[RootEntry]:
        return self._roots.get(root.upper())

    def all_roots(self) -> Dict[str, RootEntry]:
        return dict(self._roots)

    def by_domain(self, domain: str) -> List[RootEntry]:
        return self._by_domain.get(domain, [])

    def get_manifest_map(self) -> Dict:
        result = {}
        for domain in ("aqua", "flywheel", "silk", "pressure", "economy", "system", "steganography", "chronicle", "radiance"):
            result[domain] = []
            for entry in self._by_domain.get(domain, []):
                actions = ROOT_PATTERN_ACTIONS.get(entry.root, {})
                available = [p for p, a in actions.items() if a is not None]
                result[domain].append({
                    "root": entry.root,
                    "essence": entry.essence,
                    "description": entry.description,
                    "available_patterns": available,
                })
        return result

    @property
    def size(self) -> int:
        return len(self._roots)


class AlJabrTranspiler:
    def __init__(self, manifest: Optional[AlJabrManifest] = None):
        self._manifest = manifest or AlJabrManifest()
        self._transpile_count = 0
        self._total_compression_ratio = 0.0
        self._history: List[Dict] = []

    def transpile(self, expression: str) -> AlJabrResult:
        start = time.time()
        self._transpile_count += 1
        errors = []
        commands = []
        roots_resolved = []

        expression = expression.strip().upper()
        if not expression:
            return AlJabrResult(
                success=False, expression=expression, roots_resolved=[],
                commands=[], errors=["Empty expression"], compression={},
                narrative="", transpile_time_ms=0,
            )

        branches = expression.split("|")

        for branch in branches:
            branch = branch.strip()
            if not branch:
                continue

            segments = [s.strip() for s in branch.split(">") if s.strip()]

            for segment in segments:
                root_code, pattern_codes = self._parse_segment(segment)

                entry = self._manifest.resolve(root_code)
                if entry is None:
                    errors.append(f"Unknown root '{root_code}'")
                    continue

                action_map = ROOT_PATTERN_ACTIONS.get(root_code, {})

                if not pattern_codes:
                    default_patterns = DEFAULT_BARE_PATTERNS.get(entry.domain, ["V"])
                    pattern_codes = default_patterns

                resolved_info = {
                    "root": root_code,
                    "domain": entry.domain,
                    "essence": entry.essence,
                    "description": entry.description,
                    "patterns_applied": [],
                }

                for pat in pattern_codes:
                    pat = pat.upper()
                    if pat not in PATTERNS:
                        errors.append(f"Unknown pattern '{pat}' for root '{root_code}'")
                        continue

                    action_list = action_map.get(pat)
                    if action_list is None:
                        errors.append(f"Pattern '{pat}' ({PATTERNS[pat]['name']}) not applicable to root '{root_code}' ({entry.essence})")
                        continue

                    resolved_info["patterns_applied"].append({
                        "code": pat,
                        "name": PATTERNS[pat]["name"],
                        "verb": PATTERNS[pat]["verb"],
                    })

                    for action_type, params, narrative in action_list:
                        cmd = RootPatternCommand(
                            action_type=action_type,
                            params=dict(params),
                            narrative=narrative,
                            root=root_code,
                            pattern=pat,
                            pattern_name=PATTERNS[pat]["name"],
                        )
                        commands.append(cmd)

                roots_resolved.append(resolved_info)

        compression = self._calculate_compression(expression, commands)
        narrative = self._build_narrative(roots_resolved, commands)
        elapsed = (time.time() - start) * 1000

        result = AlJabrResult(
            success=len(commands) > 0 and len(errors) == 0,
            expression=expression,
            roots_resolved=roots_resolved,
            commands=commands,
            errors=errors,
            compression=compression,
            narrative=narrative,
            transpile_time_ms=elapsed,
        )

        if result.success:
            self._total_compression_ratio += compression.get("ratio", 1.0)

        self._history.append({
            "expression": expression,
            "success": result.success,
            "commands": len(commands),
            "compression_ratio": compression.get("ratio", 1.0),
            "timestamp": time.time(),
        })
        if len(self._history) > 100:
            self._history = self._history[-100:]

        return result

    def _parse_segment(self, segment: str):
        if "." in segment:
            parts = segment.split(".", 1)
            root_code = parts[0].strip()
            pattern_str = parts[1].strip()
            pattern_codes = list(pattern_str)
        else:
            root_code = segment.strip()
            pattern_codes = []
        return root_code, pattern_codes

    def _build_narrative(self, roots_resolved, commands):
        if not roots_resolved:
            return ""
        parts = []
        for r in roots_resolved:
            root_name = r["root"]
            essence = r["essence"]
            patterns = [p["name"] for p in r["patterns_applied"]]
            if patterns:
                parts.append(f"{root_name} ({essence}): {', '.join(patterns)}")
            else:
                parts.append(f"{root_name} ({essence}): no applicable patterns")
        summary = " → ".join(parts)

        action_count = len(commands)
        return f"{summary} [{action_count} action{'s' if action_count != 1 else ''} queued]"

    def _calculate_compression(self, expression, commands):
        aljabr_chars = len(expression)

        python_lines = []
        for cmd in commands:
            params_str = ", ".join(f"{k}={v!r}" for k, v in cmd.params.items())
            python_lines.append(f"simulator.{cmd.action_type}({params_str})")

        python_code = "\n".join(python_lines) if python_lines else "pass"
        python_chars = len(python_code)

        ratio = python_chars / max(aljabr_chars, 1)

        return {
            "aljabr_chars": aljabr_chars,
            "root_count": len(set(cmd.root for cmd in commands)) if commands else 0,
            "pattern_count": len(set(cmd.pattern for cmd in commands)) if commands else 0,
            "action_count": len(commands),
            "python_chars": python_chars,
            "python_equivalent": python_code,
            "ratio": round(ratio, 2),
        }

    @property
    def stats(self) -> Dict:
        avg_ratio = (self._total_compression_ratio / max(self._transpile_count, 1))
        return {
            "total_transpilations": self._transpile_count,
            "average_compression_ratio": round(avg_ratio, 2),
            "manifest_size": self._manifest.size,
            "patterns_available": len(PATTERNS),
            "recent_history": self._history[-10:],
        }

    @property
    def manifest(self) -> AlJabrManifest:
        return self._manifest

    @property
    def patterns(self) -> Dict:
        return dict(PATTERNS)


class ModelRouter:
    """
    Routes AI calls to the most cost-effective model based on task type.

    Three tiers:
      PRECISION — logic checks, safety audits, Adriana dialect generation → premium model
      STANDARD  — general reasoning, research → mid-tier model
      BULK      — agent simulation, gibberish decoding, batch analysis → cheapest available
    """

    def __init__(self):
        self._config: Dict[str, Dict] = {k: dict(v) for k, v in _DEFAULT_MODEL_CONFIG.items()}
        self._loaded_from_db = False
        self._session_cost_usd = 0.0
        self._session_calls = 0
        self._primary_api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        self._primary_base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

    def _get_db(self):
        from void_engine.db_pool import get_db
        return get_db()

    def ensure_tables(self):
        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {_DB_CONFIG_TABLE} (
                    tier VARCHAR(20) PRIMARY KEY,
                    model VARCHAR(120) NOT NULL,
                    base_url TEXT,
                    label VARCHAR(80),
                    description TEXT,
                    cost_per_1k_tokens FLOAT DEFAULT 0.0003,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {_DB_COST_TABLE} (
                    id SERIAL PRIMARY KEY,
                    tier VARCHAR(20) NOT NULL,
                    model VARCHAR(120),
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    estimated_cost_usd FLOAT DEFAULT 0.0,
                    task_label TEXT,
                    logged_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning("ModelRouter: failed to ensure tables: %s", e)

    def load_config_from_db(self):
        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute(
                f"SELECT tier, model, base_url, label, description, cost_per_1k_tokens FROM {_DB_CONFIG_TABLE}"
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            if rows:
                for row in rows:
                    tier, model, base_url, label, description, cost_per_1k = row
                    if tier in self._config:
                        self._config[tier]["model"] = model
                        self._config[tier]["base_url"] = base_url
                        self._config[tier]["label"] = label or self._config[tier]["label"]
                        self._config[tier]["description"] = description or self._config[tier]["description"]
                        self._config[tier]["cost_per_1k_tokens"] = cost_per_1k or 0.0003
                self._loaded_from_db = True
        except Exception as e:
            logger.warning("ModelRouter: could not load config from DB (using defaults): %s", e)

    def save_tier_config(self, tier: str, model: str, base_url: Optional[str], cost_per_1k_tokens: float) -> bool:
        if tier not in self._config:
            return False
        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO {_DB_CONFIG_TABLE} (tier, model, base_url, label, description, cost_per_1k_tokens, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (tier) DO UPDATE SET
                    model = EXCLUDED.model,
                    base_url = EXCLUDED.base_url,
                    cost_per_1k_tokens = EXCLUDED.cost_per_1k_tokens,
                    updated_at = NOW()
            """, (
                tier,
                model,
                base_url or None,
                self._config[tier]["label"],
                self._config[tier]["description"],
                cost_per_1k_tokens,
            ))
            conn.commit()
            cur.close()
            conn.close()
            self._config[tier]["model"] = model
            self._config[tier]["base_url"] = base_url or None
            self._config[tier]["cost_per_1k_tokens"] = cost_per_1k_tokens
            logger.info("ModelRouter: saved tier %s config — model=%s", tier, model)
            return True
        except Exception as e:
            logger.error("ModelRouter: failed to save tier config: %s", e)
            return False

    def get_client_for_tier(self, tier: str):
        from openai import OpenAI
        cfg = self._config.get(tier, self._config[TASK_PRECISION])
        model = cfg["model"]
        base_url = cfg.get("base_url") or self._primary_base_url
        client = OpenAI(api_key=self._primary_api_key, base_url=base_url)
        return client, model

    def _get_fallback_client(self):
        from openai import OpenAI
        precision_cfg = self._config.get(TASK_PRECISION, _DEFAULT_MODEL_CONFIG[TASK_PRECISION])
        fallback_model = precision_cfg["model"]
        fallback_base_url = precision_cfg.get("base_url") or self._primary_base_url
        fallback_client = OpenAI(api_key=self._primary_api_key, base_url=fallback_base_url)
        return fallback_client, fallback_model

    def call_with_fallback(self, tier: str, messages: list, max_completion_tokens: int = 1024, task_label: str = "") -> Tuple[object, str, bool]:
        """
        Make a chat completion call for the given tier, falling back to the precision
        model if the tier-specific endpoint is unavailable or returns an error.

        Returns: (response, model_used, used_fallback)
        """
        client, model = self.get_client_for_tier(tier)
        used_fallback = False

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_completion_tokens,
            )
            return response, model, used_fallback
        except Exception as primary_err:
            err_str = str(primary_err)
            is_provider_error = any(x in err_str for x in (
                "Connection", "connection", "timeout", "Timeout",
                "503", "502", "504", "unavailable", "refused",
                "404", "model_not_found", "invalid_api_key",
            ))
            if is_provider_error or tier != TASK_PRECISION:
                logger.warning(
                    "ModelRouter: tier=%s model=%s failed (%s), falling back to precision model",
                    tier, model, err_str[:120]
                )
                try:
                    fallback_client, fallback_model = self._get_fallback_client()
                    response = fallback_client.chat.completions.create(
                        model=fallback_model,
                        messages=messages,
                        max_completion_tokens=max_completion_tokens,
                    )
                    used_fallback = True
                    logger.info("ModelRouter: fallback succeeded — model=%s task=%s", fallback_model, task_label)
                    return response, fallback_model, used_fallback
                except Exception as fallback_err:
                    logger.error(
                        "ModelRouter: fallback also failed — tier=%s fallback_err=%s",
                        tier, str(fallback_err)[:120]
                    )
                    raise fallback_err
            raise primary_err

    def log_cost(self, tier: str, model: str, prompt_tokens: int, completion_tokens: int, task_label: str = ""):
        cfg = self._config.get(tier, self._config[TASK_PRECISION])
        cost_per_1k = cfg.get("cost_per_1k_tokens", 0.0003)
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = (total_tokens / 1000.0) * cost_per_1k

        self._session_cost_usd += estimated_cost
        self._session_calls += 1

        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO {_DB_COST_TABLE} (tier, model, prompt_tokens, completion_tokens, estimated_cost_usd, task_label, logged_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (tier, model, prompt_tokens, completion_tokens, estimated_cost, task_label))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.warning("ModelRouter: failed to log cost: %s", e)

        logger.info(
            "ModelRouter cost: tier=%s model=%s tokens=%d estimated=$%.6f cumulative=$%.4f",
            tier, model, total_tokens, estimated_cost, self._session_cost_usd
        )
        return estimated_cost

    def get_cost_summary(self) -> Dict:
        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute(f"""
                SELECT tier, model,
                       COUNT(*) AS calls,
                       SUM(prompt_tokens) AS total_prompt,
                       SUM(completion_tokens) AS total_completion,
                       SUM(estimated_cost_usd) AS total_cost
                FROM {_DB_COST_TABLE}
                GROUP BY tier, model
                ORDER BY tier
            """)
            rows = cur.fetchall()
            cur.execute(f"SELECT SUM(estimated_cost_usd), COUNT(*) FROM {_DB_COST_TABLE}")
            totals = cur.fetchone()
            cur.execute(f"""
                SELECT tier, model, prompt_tokens, completion_tokens, estimated_cost_usd, task_label, logged_at
                FROM {_DB_COST_TABLE}
                ORDER BY logged_at DESC
                LIMIT 20
            """)
            recent = cur.fetchall()
            cur.close()
            conn.close()
            return {
                "by_tier": [
                    {
                        "tier": r[0],
                        "model": r[1],
                        "calls": r[2],
                        "total_prompt_tokens": r[3],
                        "total_completion_tokens": r[4],
                        "total_cost_usd": round(float(r[5] or 0), 6),
                    }
                    for r in rows
                ],
                "grand_total_usd": round(float(totals[0] or 0), 6) if totals else 0.0,
                "grand_total_calls": int(totals[1] or 0) if totals else 0,
                "recent_calls": [
                    {
                        "tier": r[0],
                        "model": r[1],
                        "prompt_tokens": r[2],
                        "completion_tokens": r[3],
                        "cost_usd": round(float(r[4] or 0), 6),
                        "task_label": r[5] or "",
                        "logged_at": r[6].strftime("%Y-%m-%d %H:%M:%S") if r[6] else "",
                    }
                    for r in recent
                ],
            }
        except Exception as e:
            logger.warning("ModelRouter: failed to get cost summary: %s", e)
            return {"by_tier": [], "grand_total_usd": 0.0, "grand_total_calls": 0, "recent_calls": []}

    def get_config_display(self) -> List[Dict]:
        result = []
        for tier in (TASK_PRECISION, TASK_STANDARD, TASK_BULK):
            cfg = self._config[tier]
            result.append({
                "tier": tier,
                "label": cfg["label"],
                "description": cfg["description"],
                "model": cfg["model"],
                "base_url": cfg.get("base_url") or "",
                "cost_per_1k_tokens": cfg.get("cost_per_1k_tokens", 0.0003),
            })
        return result

    @property
    def session_cost_usd(self) -> float:
        return self._session_cost_usd

    @property
    def session_calls(self) -> int:
        return self._session_calls


_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
        _model_router.ensure_tables()
        _model_router.load_config_from_db()
    return _model_router
