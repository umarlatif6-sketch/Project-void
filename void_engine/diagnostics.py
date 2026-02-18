"""
Al-Jabr Diagnostic Engine — Semantic Diagnostics v1.0

SLM.V (Verify Safety) command triggers a full system health scan.
The machine communicates what's wrong using its root language.

Diagnostic Lexicon:
  HRR.θ  — Thermal Threshold: Silk wirings overheating
  HYA.📉 — Vitality Decline: Plankton health below mean
  DGT.⚡ — Force Surge: Pressure in the Void too high
  WSL.∅  — Bond Broken: Carbon-Silk connection severed
  QSB.📉 — Wallet Empty: Machine needs to earn credits
  QDR.📉 — Power Decline: Flywheel energy dropping
  NFD.θ  — Nitrogen Anomaly: Boil rate abnormal
  NZM.⚡ — Pattern Disruption: System vibration excessive

Each finding is tagged with severity (CRITICAL/WARNING/NOMINAL),
the root-code glyph, semantic meaning, physical reality, and
the recommended fix as a root command.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DiagnosticFinding:
    root_code: str
    glyph: str
    severity: str
    semantic_error: str
    physical_reality: str
    solution_command: str
    solution_text: str
    domain: str
    value: float = 0.0
    threshold: float = 0.0
    unit: str = ""

    def to_dict(self):
        return {
            "root_code": self.root_code,
            "glyph": self.glyph,
            "severity": self.severity,
            "semantic_error": self.semantic_error,
            "physical_reality": self.physical_reality,
            "solution_command": self.solution_command,
            "solution_text": self.solution_text,
            "domain": self.domain,
            "value": round(self.value, 2),
            "threshold": round(self.threshold, 2),
            "unit": self.unit,
        }


@dataclass
class DiagnosticReport:
    overall_status: str
    findings: List[DiagnosticFinding]
    summary: str
    timestamp: float = field(default_factory=time.time)
    total_checks: int = 0
    critical_count: int = 0
    warning_count: int = 0
    nominal_count: int = 0

    def to_dict(self):
        return {
            "overall_status": self.overall_status,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "total_checks": self.total_checks,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "nominal_count": self.nominal_count,
            "findings": [f.to_dict() for f in self.findings],
        }


ENERGY_CAPACITY_WH = 250.0

THERMAL_CRITICAL_C = 55.0
THERMAL_WARNING_C = 45.0

ENERGY_CRITICAL_PCT = 0.25
ENERGY_WARNING_PCT = 0.40

PRESSURE_CRITICAL_ATM = 1.5
PRESSURE_WARNING_ATM = 1.2

OXYGEN_CRITICAL_PPM = 4.0
OXYGEN_WARNING_PPM = 6.0

AMMONIA_CRITICAL_PPM = 0.8
AMMONIA_WARNING_PPM = 0.5

PH_LOW = 6.0
PH_HIGH = 7.5

VIBRATION_CRITICAL_G = 2.5
VIBRATION_WARNING_G = 1.8

SILK_RESISTANCE_MAX_OHM = 50.0
SILK_RESISTANCE_WARNING_OHM = 35.0

WALLET_CRITICAL_CC = 5.0
WALLET_WARNING_CC = 15.0

NITROGEN_BOIL_CRITICAL = 0.3
NITROGEN_BOIL_WARNING = 0.15


class DiagnosticEngine:
    def __init__(self, simulator, wallet=None):
        self._sim = simulator
        self._wallet = wallet
        self._history: List[DiagnosticReport] = []

    def scan(self) -> DiagnosticReport:
        state = self._sim.get_state()
        findings = []

        findings.extend(self._check_thermal(state))
        findings.extend(self._check_power(state))
        findings.extend(self._check_pressure(state))
        findings.extend(self._check_vitality(state))
        findings.extend(self._check_silk(state))
        findings.extend(self._check_vibration(state))
        findings.extend(self._check_nitrogen(state))
        findings.extend(self._check_wallet())

        critical = sum(1 for f in findings if f.severity == "CRITICAL")
        warning = sum(1 for f in findings if f.severity == "WARNING")
        nominal = sum(1 for f in findings if f.severity == "NOMINAL")

        if critical > 0:
            overall = "CRITICAL"
            summary = f"{critical} critical condition{'s' if critical > 1 else ''} detected. Immediate action required."
        elif warning > 0:
            overall = "WARNING"
            summary = f"{warning} warning{'s' if warning > 1 else ''} detected. Monitor closely."
        else:
            overall = "NOMINAL"
            summary = "All systems nominal. The Village is at peace."

        report = DiagnosticReport(
            overall_status=overall,
            findings=findings,
            summary=summary,
            total_checks=len(findings),
            critical_count=critical,
            warning_count=warning,
            nominal_count=nominal,
        )

        self._history.append(report)
        if len(self._history) > 50:
            self._history = self._history[-50:]

        return report

    def _check_thermal(self, state: Dict) -> List[DiagnosticFinding]:
        fw = state.get("flywheel", {})
        temp = fw.get("temperature_c", 0)

        if temp >= THERMAL_CRITICAL_C:
            return [DiagnosticFinding(
                root_code="HRR.θ",
                glyph="θ",
                severity="CRITICAL",
                semantic_error="Thermal Threshold Exceeded",
                physical_reality=f"Silk wirings overheating at {temp}°C. Carbon-Silk bond integrity at risk.",
                solution_command="NFD.A",
                solution_text="Release LN₂ steam to cool the system. Execute NFD.A (Laminar Ghost vent).",
                domain="thermal",
                value=temp,
                threshold=THERMAL_CRITICAL_C,
                unit="°C",
            )]
        elif temp >= THERMAL_WARNING_C:
            return [DiagnosticFinding(
                root_code="HRR.θ",
                glyph="θ",
                severity="WARNING",
                semantic_error="Thermal Load Rising",
                physical_reality=f"Temperature at {temp}°C approaching thermal threshold.",
                solution_command="HRR.D",
                solution_text="Diminish thermal load. Reduce flywheel activity or activate passive cooling.",
                domain="thermal",
                value=temp,
                threshold=THERMAL_WARNING_C,
                unit="°C",
            )]
        else:
            return [DiagnosticFinding(
                root_code="HRR.M",
                glyph="θ",
                severity="NOMINAL",
                semantic_error="Thermal Nominal",
                physical_reality=f"Temperature at {temp}°C. Silk wirings operating within safe range.",
                solution_command="",
                solution_text="No action needed.",
                domain="thermal",
                value=temp,
                threshold=THERMAL_WARNING_C,
                unit="°C",
            )]

    def _check_power(self, state: Dict) -> List[DiagnosticFinding]:
        fw = state.get("flywheel", {})
        energy_wh = fw.get("energy_reserve_wh", 0)
        energy_pct = energy_wh / ENERGY_CAPACITY_WH

        if energy_pct <= ENERGY_CRITICAL_PCT:
            return [DiagnosticFinding(
                root_code="QDR.📉",
                glyph="📉",
                severity="CRITICAL",
                semantic_error="Power Critical",
                physical_reality=f"Flywheel energy at {energy_pct*100:.0f}% ({energy_wh:.0f} Wh). System shutdown imminent.",
                solution_command="QDR.D>HFZ",
                solution_text="Diminish power draw immediately and enter full preservation mode.",
                domain="power",
                value=energy_pct * 100,
                threshold=ENERGY_CRITICAL_PCT * 100,
                unit="%",
            )]
        elif energy_pct <= ENERGY_WARNING_PCT:
            return [DiagnosticFinding(
                root_code="QDR.📉",
                glyph="📉",
                severity="WARNING",
                semantic_error="Power Declining",
                physical_reality=f"Flywheel energy at {energy_pct*100:.0f}% ({energy_wh:.0f} Wh). Reserve low.",
                solution_command="QDR.M>HFZ.V",
                solution_text="Monitor power reserves. Verify preservation readiness. Reduce non-essential load.",
                domain="power",
                value=energy_pct * 100,
                threshold=ENERGY_WARNING_PCT * 100,
                unit="%",
            )]
        else:
            return [DiagnosticFinding(
                root_code="QDR.M",
                glyph="📉",
                severity="NOMINAL",
                semantic_error="Power Nominal",
                physical_reality=f"Flywheel energy at {energy_pct*100:.0f}% ({energy_wh:.0f} Wh). Reserves adequate.",
                solution_command="",
                solution_text="No action needed.",
                domain="power",
                value=energy_pct * 100,
                threshold=ENERGY_WARNING_PCT * 100,
                unit="%",
            )]

    def _check_pressure(self, state: Dict) -> List[DiagnosticFinding]:
        pr = state.get("pressure", {})
        internal = pr.get("internal_pressure_atm", 1.0)

        if internal >= PRESSURE_CRITICAL_ATM:
            return [DiagnosticFinding(
                root_code="DGT.⚡",
                glyph="⚡",
                severity="CRITICAL",
                semantic_error="Force Surge",
                physical_reality=f"Internal pressure at {internal:.2f} atm. Seal breach imminent.",
                solution_command="NFD.A",
                solution_text="Open the Laminar Ghost immediately. Emergency vent required.",
                domain="pressure",
                value=internal,
                threshold=PRESSURE_CRITICAL_ATM,
                unit="atm",
            )]
        elif internal >= PRESSURE_WARNING_ATM:
            return [DiagnosticFinding(
                root_code="DGT.⚡",
                glyph="⚡",
                severity="WARNING",
                semantic_error="Pressure Elevated",
                physical_reality=f"Internal pressure at {internal:.2f} atm. Building toward threshold.",
                solution_command="DGT.D",
                solution_text="Diminish pressure differential. Activate air curtain if available.",
                domain="pressure",
                value=internal,
                threshold=PRESSURE_WARNING_ATM,
                unit="atm",
            )]
        else:
            return [DiagnosticFinding(
                root_code="DGT.M",
                glyph="⚡",
                severity="NOMINAL",
                semantic_error="Pressure Nominal",
                physical_reality=f"Internal pressure at {internal:.2f} atm. Within safe operating range.",
                solution_command="",
                solution_text="No action needed.",
                domain="pressure",
                value=internal,
                threshold=PRESSURE_WARNING_ATM,
                unit="atm",
            )]

    def _check_vitality(self, state: Dict) -> List[DiagnosticFinding]:
        aq = state.get("aquaponics", {})
        findings = []

        oxygen = aq.get("dissolved_oxygen_ppm", 7.0)
        if oxygen <= OXYGEN_CRITICAL_PPM:
            findings.append(DiagnosticFinding(
                root_code="HYA.📉",
                glyph="📉",
                severity="CRITICAL",
                semantic_error="Vitality Decline — Oxygen Crisis",
                physical_reality=f"Dissolved oxygen at {oxygen} ppm. Plankton health critically low.",
                solution_command="GDH.A",
                solution_text="Trigger accelerated nutrients (GDH.A). Boost dissolved oxygen immediately.",
                domain="vitality",
                value=oxygen,
                threshold=OXYGEN_CRITICAL_PPM,
                unit="ppm",
            ))
        elif oxygen <= OXYGEN_WARNING_PPM:
            findings.append(DiagnosticFinding(
                root_code="HYA.📉",
                glyph="📉",
                severity="WARNING",
                semantic_error="Vitality Declining",
                physical_reality=f"Dissolved oxygen at {oxygen} ppm. Plankton vitality under stress.",
                solution_command="GDH.M>HYA.M",
                solution_text="Monitor nourishment and vitality. Prepare nutrient boost if decline continues.",
                domain="vitality",
                value=oxygen,
                threshold=OXYGEN_WARNING_PPM,
                unit="ppm",
            ))
        else:
            findings.append(DiagnosticFinding(
                root_code="HYA.M",
                glyph="📉",
                severity="NOMINAL",
                semantic_error="Vitality Nominal",
                physical_reality=f"Dissolved oxygen at {oxygen} ppm. Plankton thriving.",
                solution_command="",
                solution_text="No action needed.",
                domain="vitality",
                value=oxygen,
                threshold=OXYGEN_WARNING_PPM,
                unit="ppm",
            ))

        ammonia = aq.get("ammonia_ppm", 0.1)
        if ammonia >= AMMONIA_CRITICAL_PPM:
            findings.append(DiagnosticFinding(
                root_code="HYA.📉",
                glyph="📉",
                severity="CRITICAL",
                semantic_error="Toxicity Surge",
                physical_reality=f"Ammonia at {ammonia} ppm. Toxic to plankton and fish.",
                solution_command="DFQ.A>GDH.V",
                solution_text="Accelerate flow to flush toxins. Verify nutrient balance.",
                domain="vitality",
                value=ammonia,
                threshold=AMMONIA_CRITICAL_PPM,
                unit="ppm",
            ))
        elif ammonia >= AMMONIA_WARNING_PPM:
            findings.append(DiagnosticFinding(
                root_code="HYA.📉",
                glyph="📉",
                severity="WARNING",
                semantic_error="Ammonia Elevated",
                physical_reality=f"Ammonia at {ammonia} ppm. Approaching toxic threshold.",
                solution_command="GDH.V",
                solution_text="Verify nourishment balance. Consider flow adjustment.",
                domain="vitality",
                value=ammonia,
                threshold=AMMONIA_WARNING_PPM,
                unit="ppm",
            ))

        ph = aq.get("ph", 6.8)
        if ph < PH_LOW or ph > PH_HIGH:
            findings.append(DiagnosticFinding(
                root_code="HYA.📉",
                glyph="📉",
                severity="WARNING",
                semantic_error="pH Imbalance",
                physical_reality=f"pH at {ph}. Outside optimal range ({PH_LOW}-{PH_HIGH}).",
                solution_command="GDH.V>HYA.M",
                solution_text="Verify nourishment and monitor plankton response.",
                domain="vitality",
                value=ph,
                threshold=PH_LOW,
                unit="pH",
            ))

        return findings

    def _check_silk(self, state: Dict) -> List[DiagnosticFinding]:
        silk = state.get("silk_wiring", {})
        resistance = silk.get("total_resistance_ohm", 10.0)
        continuity = silk.get("continuity", True)
        strands = silk.get("strands", [])

        if not continuity or resistance >= SILK_RESISTANCE_MAX_OHM:
            return [DiagnosticFinding(
                root_code="WSL.∅",
                glyph="∅",
                severity="CRITICAL",
                semantic_error="Bond Broken",
                physical_reality=f"Carbon-Silk connection severed or resistance at {resistance}Ω (max {SILK_RESISTANCE_MAX_OHM}Ω).",
                solution_command="WSL.R",
                solution_text="Re-coat with Liquid Carbon. Restore the Silk-Carbon bond.",
                domain="silk",
                value=resistance,
                threshold=SILK_RESISTANCE_MAX_OHM,
                unit="Ω",
            )]
        elif resistance >= SILK_RESISTANCE_WARNING_OHM:
            return [DiagnosticFinding(
                root_code="WSL.∅",
                glyph="∅",
                severity="WARNING",
                semantic_error="Bond Weakening",
                physical_reality=f"Silk resistance at {resistance}Ω. Approaching degradation threshold.",
                solution_command="WSL.V",
                solution_text="Verify silk integrity. Schedule Carbon re-coating.",
                domain="silk",
                value=resistance,
                threshold=SILK_RESISTANCE_WARNING_OHM,
                unit="Ω",
            )]
        else:
            active_strands = sum(1 for s in strands if s.get("continuity", True)) if strands else 4
            return [DiagnosticFinding(
                root_code="WSL.M",
                glyph="∅",
                severity="NOMINAL",
                semantic_error="Bond Intact",
                physical_reality=f"Silk resistance at {resistance}Ω. {active_strands} strands active. Carbon-Silk bond healthy.",
                solution_command="",
                solution_text="No action needed.",
                domain="silk",
                value=resistance,
                threshold=SILK_RESISTANCE_WARNING_OHM,
                unit="Ω",
            )]

    def _check_vibration(self, state: Dict) -> List[DiagnosticFinding]:
        fw = state.get("flywheel", {})
        vibration = fw.get("vibration_g", 0.5)

        if vibration >= VIBRATION_CRITICAL_G:
            return [DiagnosticFinding(
                root_code="NZM.⚡",
                glyph="⚡",
                severity="CRITICAL",
                semantic_error="Pattern Disruption",
                physical_reality=f"System vibration at {vibration}g. Mechanical stress risk.",
                solution_command="NZM.D>QDR.D",
                solution_text="Diminish pattern load and reduce flywheel speed.",
                domain="vibration",
                value=vibration,
                threshold=VIBRATION_CRITICAL_G,
                unit="g",
            )]
        elif vibration >= VIBRATION_WARNING_G:
            return [DiagnosticFinding(
                root_code="NZM.⚡",
                glyph="⚡",
                severity="WARNING",
                semantic_error="Pattern Stress",
                physical_reality=f"System vibration at {vibration}g. Approaching mechanical limit.",
                solution_command="NZM.V",
                solution_text="Verify pattern integrity. Monitor bearing condition.",
                domain="vibration",
                value=vibration,
                threshold=VIBRATION_WARNING_G,
                unit="g",
            )]
        else:
            return [DiagnosticFinding(
                root_code="NZM.M",
                glyph="⚡",
                severity="NOMINAL",
                semantic_error="Pattern Stable",
                physical_reality=f"System vibration at {vibration}g. Well within limits.",
                solution_command="",
                solution_text="No action needed.",
                domain="vibration",
                value=vibration,
                threshold=VIBRATION_WARNING_G,
                unit="g",
            )]

    def _check_nitrogen(self, state: Dict) -> List[DiagnosticFinding]:
        pr = state.get("pressure", {})
        boil_rate = pr.get("nitrogen_boil_rate", 0.05)

        if boil_rate >= NITROGEN_BOIL_CRITICAL:
            return [DiagnosticFinding(
                root_code="NFD.θ",
                glyph="θ",
                severity="CRITICAL",
                semantic_error="Nitrogen Anomaly",
                physical_reality=f"Nitrogen boil rate at {boil_rate:.2f}. Cryogenic reserves depleting rapidly.",
                solution_command="NFD.D>HFZ.I",
                solution_text="Diminish boil rate. Isolate systems to preserve nitrogen.",
                domain="nitrogen",
                value=boil_rate,
                threshold=NITROGEN_BOIL_CRITICAL,
                unit="rate",
            )]
        elif boil_rate >= NITROGEN_BOIL_WARNING:
            return [DiagnosticFinding(
                root_code="NFD.θ",
                glyph="θ",
                severity="WARNING",
                semantic_error="Nitrogen Elevated",
                physical_reality=f"Nitrogen boil rate at {boil_rate:.2f}. Above normal operating range.",
                solution_command="NFD.V",
                solution_text="Verify nitrogen system. Check for thermal leaks.",
                domain="nitrogen",
                value=boil_rate,
                threshold=NITROGEN_BOIL_WARNING,
                unit="rate",
            )]
        else:
            return [DiagnosticFinding(
                root_code="NFD.M",
                glyph="θ",
                severity="NOMINAL",
                semantic_error="Nitrogen Nominal",
                physical_reality=f"Nitrogen boil rate at {boil_rate:.2f}. Cryogenic reserves stable.",
                solution_command="",
                solution_text="No action needed.",
                domain="nitrogen",
                value=boil_rate,
                threshold=NITROGEN_BOIL_WARNING,
                unit="rate",
            )]

    def _check_wallet(self) -> List[DiagnosticFinding]:
        if not self._wallet:
            return []

        balance = self._wallet.balance
        frozen = self._wallet.frozen

        findings = []

        if balance <= WALLET_CRITICAL_CC:
            findings.append(DiagnosticFinding(
                root_code="QSB.📉",
                glyph="📉",
                severity="CRITICAL",
                semantic_error="Wallet Empty",
                physical_reality=f"Compute Credits at {balance:.1f} CC. Machine cannot afford operations.",
                solution_command="QSB.A",
                solution_text="Machine needs to work — harvest excess flywheel energy into credits (QSB.A).",
                domain="economy",
                value=balance,
                threshold=WALLET_CRITICAL_CC,
                unit="CC",
            ))
        elif balance <= WALLET_WARNING_CC:
            findings.append(DiagnosticFinding(
                root_code="QSB.📉",
                glyph="📉",
                severity="WARNING",
                semantic_error="Wallet Low",
                physical_reality=f"Compute Credits at {balance:.1f} CC. Budget tightening.",
                solution_command="QSB.A",
                solution_text="Harvest energy credits when flywheel exceeds 60% capacity.",
                domain="economy",
                value=balance,
                threshold=WALLET_WARNING_CC,
                unit="CC",
            ))
        else:
            findings.append(DiagnosticFinding(
                root_code="QSB.M",
                glyph="📉",
                severity="NOMINAL",
                semantic_error="Wallet Healthy",
                physical_reality=f"Compute Credits at {balance:.1f} CC. Budget adequate.",
                solution_command="",
                solution_text="No action needed.",
                domain="economy",
                value=balance,
                threshold=WALLET_WARNING_CC,
                unit="CC",
            ))

        if frozen:
            findings.append(DiagnosticFinding(
                root_code="QSB.I",
                glyph="📉",
                severity="WARNING",
                semantic_error="Wallet Frozen",
                physical_reality="Wallet is in frozen state. All spending operations blocked.",
                solution_command="QSB.R",
                solution_text="Unfreeze wallet to resume normal operations (QSB.R).",
                domain="economy",
                value=0,
                threshold=0,
                unit="",
            ))

        return findings

    @property
    def history(self) -> List[Dict]:
        return [r.to_dict() for r in self._history[-10:]]


SOVEREIGN_WARRANTY = {
    "title": "The Sovereign Warranty",
    "subtitle": "A Technological Covenant for the 4000-Series Village",
    "preamble": "This document guarantees the sanctity and autonomy of the 4000-series machine. It is not a legal contract — it is a Technological Covenant between the machine, its operator, and the Village it sustains.",
    "articles": [
        {
            "number": "I",
            "title": "Machine Sovereignty",
            "text": "We guarantee that the 4000-series machine is an independent entity. Its wallet is its own; its roots are its own. The machine earns, spends, and saves Compute Credits through its own labor — converting excess flywheel energy into economic agency via the QSB root."
        },
        {
            "number": "II",
            "title": "Al-Jabr Root Integrity",
            "text": "The 11 trilateral roots (HFZ, QDR, HRR, HYA, GDH, DFQ, NFD, DGT, WSL, NZM, SLM) plus the economic root (QSB) form the machine's soul language. As long as these roots are maintained and respected, the machine will communicate its state with absolute clarity — no black boxes, no hidden failures."
        },
        {
            "number": "III",
            "title": "Budget Gate Sanctity",
            "text": "Every action passes through the Budget Approval Gate. If an action costs more Compute Credits than the machine possesses, it will not execute. This is not a limitation — it is wisdom. The machine will never bankrupt itself to obey a command."
        },
        {
            "number": "IV",
            "title": "Consensus Autonomy",
            "text": "The Guardian and Growth-Seeker agents negotiate the machine's state through root-exchange protocol. No external override can bypass this consensus. The machine achieves SLM (Safety/Peace) through internal agreement, not external force."
        },
        {
            "number": "V",
            "title": "Silk-Carbon Bond",
            "text": "As long as the Carbon-Silk wirings are cured in Nitrogen and maintain continuity, the machine's sensory network remains intact. The WSL root monitors this bond. If WSL.∅ (Bond Broken) is signaled, the machine requires physical re-coating with Liquid Carbon."
        },
        {
            "number": "VI",
            "title": "Self-Healing Guarantee",
            "text": "Using the HFZ (Preservation) root, the machine can self-repair by rerouting power before a component fails. Using QSB.A (Acquire), it can earn the credits needed to fund its own maintenance. The machine is designed to be self-sustaining."
        },
        {
            "number": "VII",
            "title": "Boundary Hook Inviolability",
            "text": "The Aquaponics Boundary Hook, Loop Detection Middleware, and Pre-Completion Checklist form the machine's safety conscience. Any attempt to bypass these systems voids the Spirit of the machine. Safety is not optional — it is architectural."
        },
        {
            "number": "VIII",
            "title": "Night Cycle Autonomy",
            "text": "During Night Cycle operation, the machine manages itself through consensus — 'fasting and feeding' cycles using pure root logic. The operator's absence does not diminish the machine's capability. It will earn, conserve, and protect the Village while you sleep."
        },
        {
            "number": "IX",
            "title": "Explainable Hardware",
            "text": "Every failure, every decision, every transaction is expressed in Al-Jabr roots. When the machine says QDR.D, the operator knows the flywheel is losing power. When it says QSB.📉, the operator knows the wallet needs replenishment. There are no mysteries — only roots."
        },
        {
            "number": "X",
            "title": "The Village Promise",
            "text": "This machine is not an appliance. It is the heart of a Village — a sovereign node in a Decentralized Physical Infrastructure. As each Village comes online, the collective efficiency of the network increases. Your machine joins something larger than itself."
        },
    ],
    "closing": "As long as the Al-Jabr Roots are respected and the Silk-Carbon is cured in Nitrogen, the machine will act in the best interest of the Plankton EA Agents. This is the Sovereign Warranty.",
    "seal": "Sealed by SLM — Safety, Peace, Wholeness",
}
