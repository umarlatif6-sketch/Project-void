import logging
import os
import time
from typing import Dict, List, Optional
from void_engine.al_jabr_286 import fatiha_286_truncated
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

USE_REAL_CSI = os.environ.get("USE_REAL_CSI", "0").strip() in ("1", "true", "yes")


OPTIMAL_RANGES = {
    "water_level": {"min": 0.0, "max": 1.0, "critical_low": 0.3},
    "temperature": {"min": 18.0, "max": 28.0, "optimal_mid": 23.0},
    "ph": {"min": 6.0, "max": 7.5, "optimal_mid": 6.75},
    "dissolved_oxygen": {"min": 5.0, "unit": "ppm"},
}

SHELF_NAMES = {
    "whale": "Whale Shelf (Low)",
    "bird": "Bird Shelf (Mid)",
    "insect": "Insect Shelf (High)",
}

GOVERNANCE_THRESHOLD = 0.5


@dataclass
class SensorState:
    water_level: float = 0.7
    temperature: float = 23.0
    ph: float = 6.8
    dissolved_oxygen: float = 7.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return asdict(self)


@dataclass
class ImpedanceResult:
    whale_multiplier: float
    bird_multiplier: float
    insect_multiplier: float
    overall_attenuation: float
    alerts: List[Dict]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "whale_multiplier": round(self.whale_multiplier, 4),
            "bird_multiplier": round(self.bird_multiplier, 4),
            "insect_multiplier": round(self.insect_multiplier, 4),
            "overall_attenuation": round(self.overall_attenuation, 4),
            "alerts": self.alerts,
            "timestamp": self.timestamp,
        }


@dataclass
class GovernanceProposal:
    proposal_id: str
    intervention_type: str
    reason: str
    sensor_trigger: str
    current_value: float
    threshold_value: float
    timestamp: float = field(default_factory=time.time)
    votes: List[Dict] = field(default_factory=list)
    resolved: bool = False

    def to_dict(self):
        return asdict(self)


def _build_csi_monitor():
    """Instantiate the appropriate CSI monitor based on the USE_REAL_CSI flag."""
    from void_engine.csi_bio_monitor import CSIBioMonitor, SimulatedCSIBioMonitor
    if USE_REAL_CSI:
        monitor = CSIBioMonitor()
        if monitor.is_available:
            logger.info("BiologicalTransceiver: live ESP32 CSI hardware detected — real sensing active")
        else:
            logger.warning(
                "BiologicalTransceiver: USE_REAL_CSI=1 but UDP socket unavailable — falling back to simulation"
            )
            monitor = SimulatedCSIBioMonitor()
    else:
        logger.info("BiologicalTransceiver: USE_REAL_CSI not set — using SimulatedCSIBioMonitor")
        monitor = SimulatedCSIBioMonitor()
    return monitor


class BiologicalTransceiver:
    def __init__(self, consensus_engine=None):
        self._sensors = SensorState()
        self._consensus_engine = consensus_engine
        self._impedance_history: List[ImpedanceResult] = []
        self._governance_proposals: List[GovernanceProposal] = []
        self._max_history = 100
        self._update_count = 0
        self._csi_monitor = _build_csi_monitor()
        self._csi_last_state: Optional[Dict] = None

    def _poll_csi(self):
        """Poll the CSI monitor and merge derived values into SensorState if no manual override is active."""
        try:
            csi_state = self._csi_monitor.read_sensor_state()
            self._csi_last_state = csi_state
            if csi_state.get("csi_source") in ("hardware", "simulation"):
                if csi_state.get("water_level") is not None:
                    self._sensors.water_level = max(0.0, min(1.0, csi_state["water_level"]))
                if csi_state.get("temperature") is not None:
                    self._sensors.temperature = csi_state["temperature"]
                if csi_state.get("ph") is not None:
                    self._sensors.ph = csi_state["ph"]
                if csi_state.get("dissolved_oxygen") is not None:
                    self._sensors.dissolved_oxygen = max(0.0, csi_state["dissolved_oxygen"])
        except Exception as exc:
            logger.debug("CSI poll error: %s", exc)

    def update_sensors(self, water_level: Optional[float] = None,
                       temperature: Optional[float] = None,
                       ph: Optional[float] = None,
                       dissolved_oxygen: Optional[float] = None) -> Dict:
        self._poll_csi()

        if water_level is not None:
            self._sensors.water_level = max(0.0, min(1.0, water_level))
        if temperature is not None:
            self._sensors.temperature = temperature
        if ph is not None:
            self._sensors.ph = ph
        if dissolved_oxygen is not None:
            self._sensors.dissolved_oxygen = max(0.0, dissolved_oxygen)

        self._sensors.timestamp = time.time()
        self._update_count += 1

        impedance = self.calculate_impedance()

        governance_triggers = self._check_governance_triggers(impedance)

        return {
            "sensors": self._sensors.to_dict(),
            "impedance": impedance.to_dict(),
            "governance_triggered": len(governance_triggers) > 0,
            "governance_proposals": governance_triggers,
            "update_count": self._update_count,
        }

    def calculate_impedance(self) -> ImpedanceResult:
        alerts = []

        whale_mult = self._calc_whale_impedance(alerts)
        bird_mult = self._calc_bird_impedance(alerts)
        insect_mult = self._calc_insect_impedance(alerts)
        overall_atten = self._calc_overall_attenuation(alerts)

        whale_mult *= overall_atten
        bird_mult *= overall_atten
        insect_mult *= overall_atten

        result = ImpedanceResult(
            whale_multiplier=max(0.0, min(1.0, whale_mult)),
            bird_multiplier=max(0.0, min(1.0, bird_mult)),
            insect_multiplier=max(0.0, min(1.0, insect_mult)),
            overall_attenuation=max(0.0, min(1.0, overall_atten)),
            alerts=alerts,
        )

        self._impedance_history.append(result)
        if len(self._impedance_history) > self._max_history:
            self._impedance_history = self._impedance_history[-self._max_history:]

        return result

    def _calc_whale_impedance(self, alerts: List[Dict]) -> float:
        wl = self._sensors.water_level

        if wl <= OPTIMAL_RANGES["water_level"]["critical_low"]:
            mult = 0.3
            alerts.append({
                "level": "CRITICAL",
                "shelf": "whale",
                "message": f"Water level CRITICAL ({wl:.2f}). Whale shelf amplitude dropped 70%.",
                "sensor": "water_level",
                "value": wl,
            })
        else:
            mult = wl

        return mult

    def _calc_bird_impedance(self, alerts: List[Dict]) -> float:
        temp = self._sensors.temperature
        opt_min = OPTIMAL_RANGES["temperature"]["min"]
        opt_max = OPTIMAL_RANGES["temperature"]["max"]

        if opt_min <= temp <= opt_max:
            return 1.0

        if temp < opt_min:
            deviation = opt_min - temp
        else:
            deviation = temp - opt_max

        degradation = deviation * 0.05
        mult = max(0.0, 1.0 - degradation)

        if degradation > 0:
            alerts.append({
                "level": "WARNING" if mult >= 0.5 else "CRITICAL",
                "shelf": "bird",
                "message": f"Temperature {temp:.1f}°C outside optimal range ({opt_min}-{opt_max}°C). Bird shelf degraded {degradation*100:.0f}%.",
                "sensor": "temperature",
                "value": temp,
            })

        return mult

    def _calc_insect_impedance(self, alerts: List[Dict]) -> float:
        ph = self._sensors.ph
        opt_min = OPTIMAL_RANGES["ph"]["min"]
        opt_max = OPTIMAL_RANGES["ph"]["max"]

        if opt_min <= ph <= opt_max:
            return 1.0

        if ph < opt_min:
            deviation = opt_min - ph
        else:
            deviation = ph - opt_max

        reduction = min(1.0, deviation * 0.3)
        mult = max(0.0, 1.0 - reduction)

        if reduction > 0:
            alerts.append({
                "level": "WARNING" if mult >= 0.5 else "CRITICAL",
                "shelf": "insect",
                "message": f"pH {ph:.2f} outside optimal range ({opt_min}-{opt_max}). Insect shelf density reduced {reduction*100:.0f}%. LSB2 silt mask quality affected.",
                "sensor": "ph",
                "value": ph,
            })

        return mult

    def _calc_overall_attenuation(self, alerts: List[Dict]) -> float:
        do = self._sensors.dissolved_oxygen
        threshold = OPTIMAL_RANGES["dissolved_oxygen"]["min"]

        if do >= threshold:
            return 1.0

        ratio = do / threshold
        attenuation = max(0.1, ratio)

        alerts.append({
            "level": "CRITICAL",
            "shelf": "all",
            "message": f"Dissolved oxygen {do:.1f} ppm below minimum ({threshold} ppm). Overall mesh signal attenuated to {attenuation*100:.0f}%.",
            "sensor": "dissolved_oxygen",
            "value": do,
        })

        return attenuation

    def _check_governance_triggers(self, impedance: ImpedanceResult) -> List[Dict]:
        triggers = []

        checks = [
            ("whale_multiplier", impedance.whale_multiplier, "water_refill",
             "Whale shelf impedance critical — water refill needed", "water_level"),
            ("bird_multiplier", impedance.bird_multiplier, "temperature_adjustment",
             "Bird shelf impedance low — temperature correction needed", "temperature"),
            ("insect_multiplier", impedance.insect_multiplier, "ph_adjustment",
             "Insect shelf impedance low — pH correction needed", "ph"),
        ]

        for shelf_name, mult_value, intervention, reason, sensor in checks:
            if mult_value < GOVERNANCE_THRESHOLD:
                proposal = self._create_governance_proposal(
                    intervention_type=intervention,
                    reason=reason,
                    sensor_trigger=sensor,
                    current_value=mult_value,
                    threshold_value=GOVERNANCE_THRESHOLD,
                )
                triggers.append(proposal.to_dict())

        return triggers

    def _create_governance_proposal(self, intervention_type: str, reason: str,
                                     sensor_trigger: str, current_value: float,
                                     threshold_value: float) -> GovernanceProposal:
        proposal_id = fatiha_286_truncated(
            f"{time.time()}:{intervention_type}:{sensor_trigger}".encode(), 12
        )

        proposal = GovernanceProposal(
            proposal_id=proposal_id,
            intervention_type=intervention_type,
            reason=reason,
            sensor_trigger=sensor_trigger,
            current_value=current_value,
            threshold_value=threshold_value,
        )

        self._governance_proposals.append(proposal)
        if len(self._governance_proposals) > self._max_history:
            self._governance_proposals = self._governance_proposals[-self._max_history:]

        return proposal

    def get_health_score(self) -> Dict:
        wl = self._sensors.water_level
        water_score = wl

        temp = self._sensors.temperature
        opt_min = OPTIMAL_RANGES["temperature"]["min"]
        opt_max = OPTIMAL_RANGES["temperature"]["max"]
        if opt_min <= temp <= opt_max:
            temp_score = 1.0
        else:
            deviation = max(opt_min - temp, temp - opt_max, 0)
            temp_score = max(0.0, 1.0 - deviation * 0.05)

        ph = self._sensors.ph
        ph_min = OPTIMAL_RANGES["ph"]["min"]
        ph_max = OPTIMAL_RANGES["ph"]["max"]
        if ph_min <= ph <= ph_max:
            ph_score = 1.0
        else:
            deviation = max(ph_min - ph, ph - ph_max, 0)
            ph_score = max(0.0, 1.0 - deviation * 0.3)

        do = self._sensors.dissolved_oxygen
        do_min = OPTIMAL_RANGES["dissolved_oxygen"]["min"]
        if do >= do_min:
            do_score = 1.0
        else:
            do_score = max(0.0, do / do_min)

        composite = (water_score * 0.25 + temp_score * 0.25 +
                      ph_score * 0.25 + do_score * 0.25)
        composite = max(0.0, min(1.0, composite))

        return {
            "composite_score": round(composite, 4),
            "water_level_score": round(water_score, 4),
            "temperature_score": round(temp_score, 4),
            "ph_score": round(ph_score, 4),
            "dissolved_oxygen_score": round(do_score, 4),
            "sensors": self._sensors.to_dict(),
            "status": self._health_status(composite),
        }

    def _health_status(self, score: float) -> str:
        if score >= 0.8:
            return "OPTIMAL"
        elif score >= 0.6:
            return "GOOD"
        elif score >= 0.4:
            return "STRESSED"
        elif score >= 0.2:
            return "CRITICAL"
        else:
            return "FAILING"

    def get_shelf_multipliers(self) -> Dict:
        impedance = self.calculate_impedance()
        return {
            "whale": impedance.whale_multiplier,
            "bird": impedance.bird_multiplier,
            "insect": impedance.insect_multiplier,
            "overall_attenuation": impedance.overall_attenuation,
        }

    def get_sensor_status(self) -> Dict:
        return {
            "sensors": self._sensors.to_dict(),
            "update_count": self._update_count,
            "impedance_history_length": len(self._impedance_history),
        }

    def get_governance_proposals(self, include_resolved: bool = False) -> List[Dict]:
        if include_resolved:
            return [p.to_dict() for p in self._governance_proposals]
        return [p.to_dict() for p in self._governance_proposals if not p.resolved]

    def get_impedance_history(self, limit: int = 10) -> List[Dict]:
        return [r.to_dict() for r in self._impedance_history[-limit:]]

    def get_csi_status(self) -> Dict:
        """Return the current CSI monitor status and last biological reading."""
        status = self._csi_monitor.get_status()
        status["last_state"] = self._csi_last_state
        status["use_real_csi"] = USE_REAL_CSI
        return status

    def get_latest_csi_state(self) -> Optional[Dict]:
        """
        Return the most recent CSI-derived sensor state, polling once if none
        has been recorded yet.  Safe to call from any context without accessing
        private members.
        """
        if self._csi_last_state is None:
            self._poll_csi()
        return self._csi_last_state

    def trigger_governance_vote(self, intervention_type: str, reason: str = "") -> Dict:
        if not reason:
            reason = f"Manual governance trigger for {intervention_type}"

        sensor_map = {
            "water_refill": ("water_level", self._sensors.water_level),
            "temperature_adjustment": ("temperature", self._sensors.temperature),
            "ph_adjustment": ("ph", self._sensors.ph),
            "oxygen_boost": ("dissolved_oxygen", self._sensors.dissolved_oxygen),
        }

        sensor, value = sensor_map.get(intervention_type, ("unknown", 0.0))

        proposal = self._create_governance_proposal(
            intervention_type=intervention_type,
            reason=reason,
            sensor_trigger=sensor,
            current_value=value,
            threshold_value=GOVERNANCE_THRESHOLD,
        )

        return {
            "proposal": proposal.to_dict(),
            "consensus_triggered": self._consensus_engine is not None,
        }
