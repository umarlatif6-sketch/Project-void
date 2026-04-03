"""
Myco-Switch — Biology as AI Load Balancer
==========================================
Reads a live "bio-state" from the mycelium / CSI monitor every 60 seconds
and routes requests to the appropriate AI model tier.

Model tiers (high → low energy):
  GEMINI_ULTRA  — High humidity + high vibration + active mycelium
  GEMINI_PRO    — Moderate activity
  GEMINI_FLASH  — Low-moderate energy
  LOCAL         — Dormancy state or Storm Mode

Storm Mode:
  When CSI detects environmental electrical stress (high-variance amplitude
  with rapid phase fluctuation) the switcher immediately locks to LOCAL mode
  regardless of other signals until the storm flag clears.
  Storm Mode is also evaluated at call-time in ModelRouter.apply_myco_override()
  so the switch is immediate — not deferred to the next background poll.

Incubation simulation profile:
  During the 90-day physical build gap the switcher runs a configurable
  daily energy cycle (dawn → peak → dusk → dormancy) so routing decisions
  are realistic even without real hardware.

Configurable via environment variables:
  MYCO_POLL_INTERVAL_S   — Poll cadence in seconds (default: 60)
  MYCO_HUMIDITY_HIGH     — High-humidity threshold (default: 0.65)
  MYCO_HUMIDITY_LOW      — Dormancy-humidity threshold (default: 0.35)
  MYCO_VIBRATION_HIGH    — High-vibration threshold (default: 0.55)
  MYCO_STORM_THRESHOLD   — Storm amplitude threshold (default: 0.75)
  MYCO_ENERGY_HIGH       — High-energy score threshold (default: 0.60)
  MYCO_ENERGY_MID        — Mid-energy score threshold (default: 0.40)
  MYCO_ENERGY_LOW        — Low-energy score threshold (default: 0.20)
  MYCO_SIM_PROFILE       — JSON string to override INCUBATION_PROFILE
"""

import json
import logging
import os
import random
import threading
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Model tier constants ────────────────────────────────────────────────────

MODEL_GEMINI_ULTRA = "gemini-ultra"
MODEL_GEMINI_PRO   = "gemini-pro"
MODEL_GEMINI_FLASH = "gemini-flash"
MODEL_LOCAL        = "local-adriana"

# ── Configurable thresholds (env-var overrideable) ──────────────────────────

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


POLL_INTERVAL_S    = _env_float("MYCO_POLL_INTERVAL_S", 60.0)
HUMIDITY_HIGH      = _env_float("MYCO_HUMIDITY_HIGH",   0.65)
HUMIDITY_LOW       = _env_float("MYCO_HUMIDITY_LOW",    0.35)
VIBRATION_HIGH     = _env_float("MYCO_VIBRATION_HIGH",  0.55)
STORM_AMP_VARIANCE = _env_float("MYCO_STORM_THRESHOLD", 0.75)
STORM_PHASE_SHIFT  = _env_float("MYCO_STORM_THRESHOLD", 0.80)
ENERGY_HIGH        = _env_float("MYCO_ENERGY_HIGH",     0.60)
ENERGY_MID         = _env_float("MYCO_ENERGY_MID",      0.40)
ENERGY_LOW         = _env_float("MYCO_ENERGY_LOW",      0.20)

# ── Simulated incubation profile ────────────────────────────────────────────
# Represents a typical 24-hour mycelium energy cycle during physical build gap.
# Each tuple: (hour_of_day_start, hour_of_day_end, humidity, vibration)
#
# Configurable via MYCO_SIM_PROFILE env var (JSON list of 4-element arrays).
# Example:
#   export MYCO_SIM_PROFILE='[[0,6,0.25,0.15],[6,12,0.70,0.65],[12,18,0.50,0.45],[18,24,0.28,0.18]]'

_DEFAULT_INCUBATION_PROFILE: List[Tuple] = [
    (0,  5,  0.30, 0.20),   # Night dormancy
    (5,  8,  0.45, 0.35),   # Dawn activation
    (8,  12, 0.65, 0.60),   # Morning peak
    (12, 14, 0.70, 0.70),   # Midday high
    (14, 18, 0.55, 0.50),   # Afternoon moderate
    (18, 21, 0.45, 0.38),   # Evening decline
    (21, 24, 0.32, 0.22),   # Night re-entry
]


def _load_incubation_profile() -> List[Tuple]:
    raw = os.environ.get("MYCO_SIM_PROFILE", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            profile = [tuple(entry) for entry in parsed if len(entry) >= 4]
            if profile:
                logger.info("MycoSwitch: loaded custom incubation profile from MYCO_SIM_PROFILE (%d bands)", len(profile))
                return profile
        except Exception as exc:
            logger.warning("MycoSwitch: MYCO_SIM_PROFILE parse error (%s), using default", exc)
    return _DEFAULT_INCUBATION_PROFILE


INCUBATION_PROFILE: List[Tuple] = _load_incubation_profile()


def _simulated_bio_state(t: Optional[float] = None) -> Dict:
    """
    Generate a simulated bio-state from the incubation profile.
    Adds a small Gaussian noise on top of the profile value.
    """
    if t is None:
        t = time.time()
    import datetime
    dt = datetime.datetime.fromtimestamp(t)
    hour = dt.hour + dt.minute / 60.0
    humidity, vibration = 0.40, 0.30
    for entry in INCUBATION_PROFILE:
        h_start, h_end, hum, vib = entry[0], entry[1], entry[2], entry[3]
        if h_start <= hour < h_end:
            humidity = float(hum)
            vibration = float(vib)
            break

    rng = random.Random(int(t / 30))
    humidity  = max(0.0, min(1.0, humidity  + rng.gauss(0, 0.025)))
    vibration = max(0.0, min(1.0, vibration + rng.gauss(0, 0.025)))

    energy = (humidity + vibration) / 2.0
    storm  = (humidity > STORM_AMP_VARIANCE and vibration > STORM_PHASE_SHIFT)

    return {
        "humidity":   round(humidity, 4),
        "vibration":  round(vibration, 4),
        "energy":     round(energy, 4),
        "storm":      storm,
        "source":     "simulation",
        "timestamp":  t,
    }


def _read_live_bio_state() -> Optional[Dict]:
    """
    Pull the most recent sensor state from BiologicalTransceiver via
    routes.shared (already-running singleton), derive normalised
    humidity / vibration / energy / storm values, and return them.

    Returns None if the shared context is not yet available.
    """
    try:
        import routes.shared as _shared
        csi_state = _shared.biological.get_latest_csi_state()
        if csi_state is None:
            return None

        moisture       = float(csi_state.get("moisture")       or 0.0)
        growth_density = float(csi_state.get("growth_density") or 0.0)
        humidity  = moisture
        vibration = growth_density
        energy    = (humidity + vibration) / 2.0
        storm     = (moisture > STORM_AMP_VARIANCE and growth_density > STORM_PHASE_SHIFT)

        return {
            "humidity":  round(humidity, 4),
            "vibration": round(vibration, 4),
            "energy":    round(energy, 4),
            "storm":     storm,
            "source":    "live",
            "timestamp": time.time(),
        }
    except Exception as exc:
        logger.debug("_read_live_bio_state failed: %s", exc)
        return None


def _select_model(bio: Dict) -> Tuple[str, str]:
    """
    Given a bio-state dict return (model_id, reason).

    Storm Mode always wins — locks to LOCAL until storm clears.

    Energy ladder (per task spec):
      High humidity + high vibration → Ultra (peak mycelium activity)
      energy >= ENERGY_HIGH          → Pro   (high but not peak)
      energy >= ENERGY_MID           → Flash (moderate activity)
      energy < ENERGY_MID            → Local (low energy / dormancy → zero external cost)
    """
    if bio.get("storm"):
        return MODEL_LOCAL, "storm-mode"

    energy    = bio.get("energy", 0.0)
    humidity  = bio.get("humidity", 0.0)
    vibration = bio.get("vibration", 0.0)

    if humidity >= HUMIDITY_HIGH and vibration >= VIBRATION_HIGH:
        return MODEL_GEMINI_ULTRA, "high-humidity+vibration"

    if energy >= ENERGY_HIGH:
        return MODEL_GEMINI_PRO, "high-energy"

    if energy >= ENERGY_MID:
        return MODEL_GEMINI_FLASH, "mid-energy"

    return MODEL_LOCAL, "dormancy"


# ── Singleton switcher ───────────────────────────────────────────────────────

class MycoSwitch:
    """
    Singleton that polls bio-state autonomously every POLL_INTERVAL_S seconds
    in a background daemon thread and maintains the current active model.

    Storm Mode is re-evaluated at call time in ModelRouter.apply_myco_override()
    to ensure immediate override regardless of the poll cycle.
    """

    def __init__(self):
        self._bio_state: Optional[Dict]  = None
        self._active_model: str          = MODEL_LOCAL
        self._switch_reason: str         = "initialising"
        self._last_poll: float           = 0.0
        self._last_switch_at: float      = time.time()
        self._switch_count: int          = 0
        self._storm_locked: bool         = False
        self._lock                       = threading.Lock()
        self._start_background_poll()

    def _start_background_poll(self) -> None:
        """Start a daemon thread that polls bio-state every POLL_INTERVAL_S seconds."""
        t = threading.Thread(target=self._background_loop, name="myco-switch-poll", daemon=True)
        t.start()
        logger.info("MycoSwitch: background poll thread started (interval=%.0fs)", POLL_INTERVAL_S)

    def _background_loop(self) -> None:
        """Autonomous 60-second bio-state polling loop."""
        while True:
            try:
                self._poll()
            except Exception as exc:
                logger.debug("MycoSwitch background poll error: %s", exc)
            time.sleep(POLL_INTERVAL_S)

    def _poll(self) -> None:
        """Poll the bio-state (live or simulated) and update model selection."""
        live = _read_live_bio_state()
        bio  = live if live is not None else _simulated_bio_state()

        new_model, reason = _select_model(bio)

        with self._lock:
            if new_model != self._active_model or bio.get("storm") != self._storm_locked:
                logger.info(
                    "MycoSwitch: %s → %s (%s) [humidity=%.2f vibration=%.2f energy=%.2f storm=%s]",
                    self._active_model, new_model, reason,
                    bio.get("humidity", 0), bio.get("vibration", 0),
                    bio.get("energy", 0), bio.get("storm"),
                )
                self._active_model   = new_model
                self._switch_reason  = reason
                self._last_switch_at = time.time()
                self._switch_count  += 1

            self._bio_state    = bio
            self._storm_locked = bool(bio.get("storm"))
            self._last_poll    = time.time()

    def _update_from_call_time(self, bio: Dict, myco_tier_id: str, reason: str) -> None:
        """
        Called from ModelRouter.apply_myco_override() to atomically update the
        switcher state from a call-time bio-state read.  This ensures the dashboard
        indicator and stored state reflect what was *actually* used for routing,
        not just what the background thread last saw.
        """
        with self._lock:
            self._bio_state = bio
            self._storm_locked = bool(bio.get("storm"))
            if myco_tier_id != self._active_model:
                logger.info(
                    "MycoSwitch[call-time]: %s → %s (%s) [humidity=%.2f vibration=%.2f energy=%.2f storm=%s]",
                    self._active_model, myco_tier_id, reason,
                    bio.get("humidity", 0), bio.get("vibration", 0),
                    bio.get("energy", 0), bio.get("storm"),
                )
                self._active_model   = myco_tier_id
                self._switch_reason  = reason
                self._last_switch_at = time.time()
                self._switch_count  += 1
            self._last_poll = time.time()

    def get_state(self) -> Dict:
        """
        Return current bio-state and active model.
        Returns cached data if fresh (< POLL_INTERVAL_S old).
        The background thread handles autonomous refreshes.
        """
        with self._lock:
            if self._bio_state is None:
                pass
        if self._bio_state is None:
            self._poll()
        return self._snapshot()

    def force_poll(self) -> Dict:
        """Force an immediate bio-state poll and return the result."""
        self._poll()
        return self._snapshot()

    def _snapshot(self) -> Dict:
        with self._lock:
            bio = self._bio_state or {}
            now = time.time()
            return {
                "bio_state": {
                    "humidity":  bio.get("humidity",  0.0),
                    "vibration": bio.get("vibration", 0.0),
                    "energy":    bio.get("energy",    0.0),
                    "storm":     bio.get("storm",     False),
                    "source":    bio.get("source",    "unknown"),
                    "timestamp": bio.get("timestamp", now),
                },
                "active_model":         self._active_model,
                "switch_reason":        self._switch_reason,
                "last_switch_at":       self._last_switch_at,
                "seconds_since_switch": round(now - self._last_switch_at, 1),
                "last_poll_at":         self._last_poll,
                "switch_count":         self._switch_count,
                "storm_locked":         self._storm_locked,
                "model_tier":           _model_tier_label(self._active_model),
            }


def _model_tier_label(model: str) -> str:
    return {
        MODEL_GEMINI_ULTRA: "Ultra",
        MODEL_GEMINI_PRO:   "Pro",
        MODEL_GEMINI_FLASH: "Flash",
        MODEL_LOCAL:        "Local",
    }.get(model, "Unknown")


# ── Module-level singleton ───────────────────────────────────────────────────

_MYCO_SWITCH: Optional[MycoSwitch] = None
_MYCO_LOCK   = threading.Lock()


def get_myco_switch() -> MycoSwitch:
    global _MYCO_SWITCH
    if _MYCO_SWITCH is None:
        with _MYCO_LOCK:
            if _MYCO_SWITCH is None:
                _MYCO_SWITCH = MycoSwitch()
    return _MYCO_SWITCH


def get_active_model() -> str:
    """Return the currently selected model ID (from the last background poll)."""
    return get_myco_switch()._active_model


def get_bio_state_snapshot() -> Dict:
    """Return the full bio-state + model snapshot."""
    return get_myco_switch().get_state()
