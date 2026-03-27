"""
QiSync BioStance & Mastication Tracker
=======================================
Server-side session management and authoritative scoring.

Key security properties:
  - Session must be registered via /session-start before ticks are accepted
  - Ticks are rate-limited to one per second per session (excess silently ignored)
  - Stance/mastication readings are derived from:
      (a) real CSI hardware via StanceDetector/MasticationDetector when available,
      (b) phone-sensor deltas reported by the browser when CSI is unavailable,
      (c) pure server-side simulation when neither is available
  - The client-reported stable/confidence/chew_delta values are ONLY used if
    the session is in phone or both mode AND no CSI hardware is active; even then
    chew_delta is capped per tick to prevent spam
  - Reward minting uses only server-accumulated scores from validated ticks

Flow:
  1. POST /api/qisync/session-start
  2. POST /api/qisync/tick  (max 1/sec enforced; CSI polled server-side)
  3. POST /api/qisync/session-end
"""

import time
import uuid
import logging
from typing import Dict, Optional

from flask import Blueprint, render_template, jsonify, session, request

logger = logging.getLogger(__name__)
qisync_bp = Blueprint("qisync", __name__)

# ── In-memory active session store ─────────────────────────────────────────
_ACTIVE_SESSIONS: Dict[str, dict] = {}
_SESSION_MAX_AGE = 7200     # 2 hours
_TICK_INTERVAL_S = 0.8      # minimum seconds between accepted ticks

VALID_STANCES = {"mabu", "pubu", "xiebu", "gongbu", "xvbu", "neutral"}
VALID_MODES = {"csi", "phone", "both"}
_MIN_REWARD_DURATION = 30   # seconds before any reward is issued
_MAX_CHEW_DELTA_PER_TICK = 3  # hard cap on client-reported chews per tick
# Phone-mode inputs are trusted at a fraction of the CSI weight, since the
# client can self-report arbitrary values. Confidence is scaled down before
# _apply_tick so phone-only reward farming yields scores in a lower tier.
_PHONE_TRUST_WEIGHT = 0.5  # 50 % of CSI confidence weight for phone inputs
# Per-session cap on the number of phone-reported stable ticks (prevents
# saturating stance_score via pure phone farming regardless of session length)
_MAX_PHONE_STABLE_TICKS = 200  # ~3.3 min at 1 Hz — enough for a real session


def _prune_sessions():
    now = time.time()
    stale = [sid for sid, rec in _ACTIVE_SESSIONS.items()
             if now - rec["start_time"] > _SESSION_MAX_AGE]
    for sid in stale:
        _ACTIVE_SESSIONS.pop(sid, None)


def _session_key(user_id, session_id: str) -> str:
    return f"{user_id}:{session_id}"


# ── CSI backend ────────────────────────────────────────────────────────────

def _get_biological():
    """Return the shared BiologicalTransceiver or None."""
    try:
        import routes.shared as _shared
        return _shared.biological
    except Exception:
        return None


def _make_csi_detectors(stance: str):
    """Instantiate StanceDetector and MasticationDetector for a session."""
    import random
    from void_engine.csi_bio_monitor import StanceDetector, MasticationDetector
    det = StanceDetector()
    mac = MasticationDetector()
    return det, mac


# Stance target variance ranges (amp_var_target, phase_rms_target) for
# server-side simulation. Each target is chosen to fall inside the stance's
# exclusive threshold region — avoiding the overlapping boundaries with the
# adjacent stance that is checked first in _STANCE_THRESHOLDS order.
#
# Detection order: mabu → pubu → xiebu → gongbu → xvbu (first match wins).
#
# xvbu [0.05,0.18] overlaps gongbu [0.10,0.28] at [0.10,0.18].
# To ensure xvbu wins, we target amp_var < 0.10 (exclusive region of xvbu).
_STANCE_SIM_TARGETS = {
    "mabu":    (0.425, 0.725),  # mid of [0.30,0.55] / [0.55,0.90]
    "pubu":    (0.700, 1.000),  # mid of [0.55,0.85] / [0.80,1.20]
    "xiebu":   (0.300, 0.550),  # mid of [0.20,0.40] / [0.40,0.70]
    "gongbu":  (0.190, 0.375),  # mid of [0.10,0.28] / [0.20,0.55]
    "xvbu":    (0.075, 0.150),  # in [0.05,0.10) / [0.10,0.20) — below gongbu lower bound
    "neutral": (0.01, 0.01),
}

_N_SUBCARRIERS = 32


def _make_packet_for_variance(amp_var_target: float, phase_rms_target: float,
                               rng, n: int = _N_SUBCARRIERS):
    """
    Generate a CSIPacket with an amplitude variance and phase RMS that are
    precisely controlled to fall within the target stance's threshold band.

    The normalization strategy eliminates sampling noise:
      1. Draw n Gaussian values with mean 0.
      2. Subtract the sample mean (zero-centre).
      3. Scale so that the sample variance equals amp_var_target exactly.
      4. Shift the mean to 1.0 (amplitudes around 1.0, all non-negative).

    The same approach is used for phases (zero-mean, exact RMS).
    """
    import math
    from void_engine.csi_bio_monitor import CSIPacket

    # Raw draws
    raw_amp = [rng.gauss(0.0, 1.0) for _ in range(n)]
    raw_ph = [rng.gauss(0.0, 1.0) for _ in range(n)]

    # Zero-centre
    a_mean = sum(raw_amp) / n
    p_mean = sum(raw_ph) / n
    raw_amp = [v - a_mean for v in raw_amp]
    raw_ph = [v - p_mean for v in raw_ph]

    # Compute current variances / RMS
    cur_amp_var = sum(v * v for v in raw_amp) / n
    cur_ph_rms = math.sqrt(sum(v * v for v in raw_ph) / n)

    # Scale to exact targets
    amp_scale = math.sqrt(amp_var_target / max(cur_amp_var, 1e-9))
    ph_scale = phase_rms_target / max(cur_ph_rms, 1e-9)

    # Add noise jitter (±2% of target) so packets are not identical across ticks
    amp_jitter = 1.0 + rng.uniform(-0.02, 0.02)
    ph_jitter = 1.0 + rng.uniform(-0.02, 0.02)

    amplitudes = [max(0.0, 1.0 + v * amp_scale * amp_jitter) for v in raw_amp]
    phases = [v * ph_scale * ph_jitter for v in raw_ph]

    return CSIPacket(amplitude=amplitudes, phase=phases,
                     ntc_raw=2048, timestamp=time.time())


def _poll_csi_detectors(rec: dict, stance: str) -> Optional[dict]:
    """
    Derive a stance/mastication reading via CSIPackets.

    When real ESP32 hardware is active (csi_source == "hardware"):
      - Read a real packet via the CSI monitor UDP socket.
      - Feed it to StanceDetector/MasticationDetector.
      - The real packet already carries the correct variance distribution.

    When hardware is absent (SimulatedCSIBioMonitor / csi_source == "simulation"):
      - Generate a synthetic CSIPacket whose amplitude variance and phase RMS
        are targeted at the selected stance's midpoint thresholds.
      - This ensures StanceDetector classifies correctly, matching what the
        frontend simulation also shows.

    Phone-only sessions never call this function.
    """
    import random
    bio = rec.get("_bio")
    det = rec.get("_stance_det")
    mac = rec.get("_mastic_det")
    if bio is None or det is None or mac is None:
        return None

    rng = rec.get("_rng")
    if rng is None:
        rng = random.Random()
        rec["_rng"] = rng

    try:
        csi_state = bio._csi_monitor.read_sensor_state()
        source = csi_state.get("csi_source")
        if source not in ("hardware", "simulation"):
            return None

        if source == "hardware":
            # Real hardware: read directly from the UDP monitor.
            # The last_packet from CSIBioMonitor contains real amplitude/phase arrays.
            last_pkt = bio._csi_monitor._last_packet
            if last_pkt is None:
                return None
            pkt = last_pkt
        else:
            # Simulation fallback: generate a packet whose variance matches the
            # stance, so StanceDetector classifies it correctly.
            targets = _STANCE_SIM_TARGETS.get(stance, _STANCE_SIM_TARGETS["mabu"])
            amp_target, phase_target = targets

            # Add small random walk to keep values inside the threshold band
            prev_amp = rec.get("_sim_amp", amp_target)
            prev_phase = rec.get("_sim_phase", phase_target)
            new_amp = max(targets[0] * 0.7, min(targets[0] * 1.3,
                          prev_amp + rng.gauss(0, 0.005)))
            new_phase = max(targets[1] * 0.7, min(targets[1] * 1.3,
                            prev_phase + rng.gauss(0, 0.005)))
            rec["_sim_amp"] = new_amp
            rec["_sim_phase"] = new_phase

            pkt = _make_packet_for_variance(new_amp, new_phase, rng)

        prev_chew = mac.chew_count
        det.feed_packet(pkt)
        mac.feed_packet(pkt)
        chew_delta = mac.chew_count - prev_chew

        stable = (det.current_stance == stance)
        confidence = det.confidence

        return {
            "stable": stable,
            "confidence": confidence,
            "chew_delta": chew_delta,
            "detected_stance": det.current_stance,
        }
    except Exception as exc:
        logger.debug("CSI poll in QiSync tick failed: %s", exc)
        return None


# ── Scoring helpers ────────────────────────────────────────────────────────

def _compute_metabolism(stance_score: float, mastic_score: float) -> float:
    return min(1.0, max(0.0, 0.65 * stance_score + 0.35 * mastic_score))


def _apply_tick(rec: dict, stable: bool, confidence: float, chew_delta: int) -> None:
    """Update accumulated stance and mastication scores for one validated tick."""
    if stable:
        rec["stance_score"] = min(1.0, rec["stance_score"] + 0.002 * max(0.1, confidence))
    else:
        rec["stance_score"] = max(0.0, rec["stance_score"] - 0.001)

    rec["chew_count"] = min(60, rec["chew_count"] + max(0, chew_delta))
    rec["mastic_score"] = min(1.0, rec["chew_count"] / 30.0)


# ── Routes ────────────────────────────────────────────────────────────────

@qisync_bp.route("/qisync")
def qisync_page():
    return render_template("qisync.html")


@qisync_bp.route("/api/qisync/csi-status")
def qisync_csi_status():
    try:
        import routes.shared as _shared
        csi = _shared.biological.get_csi_status()
        return jsonify({"ok": True, "csi": csi})
    except Exception as exc:
        logger.debug("csi-status error: %s", exc)
        return jsonify({"ok": False, "csi": None})


@qisync_bp.route("/api/qisync/session-start", methods=["POST"])
def qisync_session_start():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    stance = data.get("stance", "mabu")
    mode = data.get("mode", "csi")
    target_sec = int(data.get("target_sec", 300))

    if stance not in VALID_STANCES:
        stance = "mabu"
    if mode not in VALID_MODES:
        mode = "csi"
    target_sec = max(30, min(3600, target_sec))

    _prune_sessions()

    session_id = str(uuid.uuid4())
    key = _session_key(user_id, session_id)

    bio = _get_biological()
    csi_available = False
    stance_det = None
    mastic_det = None

    if mode in ("csi", "both") and bio is not None:
        try:
            csi_status = bio.get_csi_status()
            # CSI is available when the monitor is running in hardware or
            # simulation mode. The "available" field is False for simulation
            # (no real hardware present), but simulation is a valid source for
            # QiSync's server-side stance classification.
            csi_monitor_mode = csi_status.get("mode", "")
            csi_available = csi_monitor_mode in ("hardware", "simulation")
            if csi_available:
                stance_det, mastic_det = _make_csi_detectors(stance)
        except Exception as exc:
            logger.debug("CSI detector init failed: %s", exc)

    _ACTIVE_SESSIONS[key] = {
        "user_id": user_id,
        "session_id": session_id,
        "stance": stance,
        "mode": mode,
        "target_sec": target_sec,
        "start_time": time.time(),
        "stance_score": 0.0,
        "mastic_score": 0.0,
        "chew_count": 0,
        "tick_count": 0,
        "last_tick_time": 0.0,
        "phone_stable_ticks": 0,  # counter for per-session phone trust cap
        "ended": False,
        "csi_available": csi_available,
        "_bio": bio,
        "_stance_det": stance_det,
        "_mastic_det": mastic_det,
    }

    logger.info("QiSync session started: user=%s sid=%s stance=%s mode=%s csi=%s target=%ds",
                user_id, session_id, stance, mode, csi_available, target_sec)

    return jsonify({
        "ok": True,
        "session_id": session_id,
        "csi_available": csi_available,
    })


@qisync_bp.route("/api/qisync/tick", methods=["POST"])
def qisync_tick():
    """
    Called once per second by the client. The server:
      1. Enforces tick cadence (max 1/0.8s per session)
      2. Polls CSI detectors server-side if available
      3. Falls back to client-reported phone sensor data for phone/both modes
      4. Updates authoritative stance_score and mastic_score
      5. Returns the server-computed metabolism score
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    key = _session_key(user_id, session_id)
    rec = _ACTIVE_SESSIONS.get(key)
    if not rec:
        return jsonify({"error": "session not found or expired"}), 404
    if rec["ended"]:
        return jsonify({"error": "session already ended"}), 409

    now = time.time()
    elapsed = now - rec["start_time"]

    # Rate-limit: silently ignore ticks that arrive too quickly
    if now - rec["last_tick_time"] < _TICK_INTERVAL_S:
        metabolism = _compute_metabolism(rec["stance_score"], rec["mastic_score"])
        return jsonify({
            "ok": True,
            "rate_limited": True,
            "elapsed_sec": round(elapsed, 1),
            "stance_score": round(rec["stance_score"], 4),
            "mastic_score": round(rec["mastic_score"], 4),
            "metabolism_score": round(metabolism, 4),
            "chew_count": rec["chew_count"],
        })

    if elapsed > rec["target_sec"] + 60:
        return jsonify({"error": "session timed out — end the session"}), 409

    rec["last_tick_time"] = now
    rec["tick_count"] += 1

    # ── Determine readings ──────────────────────────────────────────────────
    mode = rec["mode"]
    stable = False
    confidence = 0.0
    chew_delta = 0
    detected_stance = "neutral"

    # Try CSI (hardware or simulation) for csi/both modes
    if mode in ("csi", "both") and rec.get("csi_available"):
        csi_reading = _poll_csi_detectors(rec, rec["stance"])
        if csi_reading is not None:
            stable = csi_reading["stable"]
            confidence = csi_reading["confidence"]
            chew_delta = csi_reading["chew_delta"]
            detected_stance = csi_reading.get("detected_stance", "neutral")

    # Phone sensor inputs: accepted for phone-only mode, and for both-mode
    # only when the CSI path did not return a valid reading (csi_available
    # but _poll_csi_detectors returned None, or explicitly phone-only).
    # This preserves reward integrity when CSI is active.
    csi_reading_obtained = (mode in ("csi", "both") and
                            rec.get("csi_available") and
                            detected_stance != "neutral" and confidence > 0.0)

    if mode == "phone" or (mode == "both" and not csi_reading_obtained):
        client_stable = bool(data.get("stable", False))
        client_conf = max(0.0, min(1.0, float(data.get("confidence", 0.0))))
        client_chew = max(0, min(_MAX_CHEW_DELTA_PER_TICK, int(data.get("chew_delta", 0))))

        # Enforce per-session phone stable-tick cap to limit farming
        phone_capped = (client_stable and
                        rec["phone_stable_ticks"] >= _MAX_PHONE_STABLE_TICKS)
        if client_stable and not phone_capped:
            rec["phone_stable_ticks"] += 1

        # Apply trust weight: phone-reported confidence counts at 50 % of CSI
        # so phone-only rewards top out in a lower tier than CSI-verified sessions
        trusted_conf = client_conf * _PHONE_TRUST_WEIGHT if not phone_capped else 0.0
        effective_stable = client_stable and not phone_capped

        if mode == "phone":
            stable = effective_stable
            confidence = trusted_conf
            chew_delta = client_chew
            detected_stance = rec["stance"] if effective_stable else "neutral"
        else:
            # Both + CSI gave no useful reading: use phone as fallback
            stable = stable or effective_stable
            confidence = max(confidence, trusted_conf)
            chew_delta = chew_delta + client_chew

    _apply_tick(rec, stable, confidence, chew_delta)

    metabolism = _compute_metabolism(rec["stance_score"], rec["mastic_score"])

    return jsonify({
        "ok": True,
        "elapsed_sec": round(elapsed, 1),
        "stance_score": round(rec["stance_score"], 4),
        "mastic_score": round(rec["mastic_score"], 4),
        "metabolism_score": round(metabolism, 4),
        "chew_count": rec["chew_count"],
        "detected_stance": detected_stance,
    })


@qisync_bp.route("/api/qisync/session-end", methods=["POST"])
def qisync_session_end():
    """
    End the session and mint VTX using the server's accumulated score.
    Any client-reported score is ignored.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    key = _session_key(user_id, session_id)
    rec = _ACTIVE_SESSIONS.get(key)
    if not rec:
        return jsonify({"error": "session not found or expired"}), 404
    if rec["ended"]:
        return jsonify({"error": "session already ended", "already_ended": True}), 409

    rec["ended"] = True
    elapsed = time.time() - rec["start_time"]

    if elapsed < _MIN_REWARD_DURATION:
        _ACTIVE_SESSIONS.pop(key, None)
        return jsonify({
            "ok": True,
            "rewarded": False,
            "reason": f"Minimum practice time is {_MIN_REWARD_DURATION}s (practiced {int(elapsed)}s)",
            "metabolism_score": 0.0,
        })

    metabolism = _compute_metabolism(rec["stance_score"], rec["mastic_score"])

    try:
        from void_engine.vortex_wallet import mint_qisync
        reward = mint_qisync(
            user_id,
            session_id,
            metabolism,
            rec["stance"],
            elapsed,
        )
    except Exception as exc:
        logger.error("mint_qisync failed: %s", exc)
        _ACTIVE_SESSIONS.pop(key, None)
        return jsonify({"error": "reward processing failed"}), 500

    _ACTIVE_SESSIONS.pop(key, None)

    logger.info("QiSync ended: user=%s sid=%s metabolism=%.3f elapsed=%.0fs vtx=%.4f",
                user_id, session_id, metabolism, elapsed, reward.get("vtx_earned", 0))

    return jsonify({
        "ok": True,
        "rewarded": True,
        "session_id": session_id,
        "metabolism_score": round(metabolism, 4),
        "stance_score": round(rec["stance_score"], 4),
        "mastic_score": round(rec["mastic_score"], 4),
        "chew_count": rec["chew_count"],
        "elapsed_sec": round(elapsed, 1),
        "stance": rec["stance"],
        "reward": reward,
    })
