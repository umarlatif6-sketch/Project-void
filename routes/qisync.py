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
_MAX_INGRESS_JSON_BYTES = 4096
_MAX_SESSION_ID_LENGTH = 64
_ALLOWED_TICK_KEYS = {"session_id", "stable", "confidence", "chew_delta", "client_ts", "nonce"}

# Freshness / replay-protection
_TICK_FRESHNESS_WINDOW_S = 30   # client_ts must be within ±30s of server time
_TICK_NONCE_MAX = 512           # max nonces held per session before rotation
_seen_tick_nonces: Dict[str, set] = {}  # session_key -> set of accepted nonces


def _coerce_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off", ""}:
            return False
    return default


def _validate_tick_payload_keys(data: dict) -> Optional[str]:
    unexpected = sorted(k for k in data.keys() if k not in _ALLOWED_TICK_KEYS)
    if unexpected:
        return f"unexpected fields in tick payload: {', '.join(unexpected)}"
    return None


def _is_valid_session_id(session_id: str) -> bool:
    if not isinstance(session_id, str):
        return False
    session_id = session_id.strip()
    if not session_id or len(session_id) > _MAX_SESSION_ID_LENGTH:
        return False
    try:
        uuid.UUID(session_id)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _prune_sessions():
    now = time.time()
    stale = [sid for sid, rec in _ACTIVE_SESSIONS.items()
             if now - rec["start_time"] > _SESSION_MAX_AGE]
    for sid in stale:
        _ACTIVE_SESSIONS.pop(sid, None)
        _seen_tick_nonces.pop(sid, None)


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


@qisync_bp.route("/api/qisync/tone")
def qisync_tone():
    """
    Generate and stream a 432 Hz (SOL) binaural WAV tuned to the Schumann
    resonance (7.83 Hz beat).  Named by session_id query param if provided.

    No authentication required — the WAV is downloadable by anyone.
    """
    from flask import Response, send_file
    import io

    session_id = request.args.get("session_id", "standalone")
    try:
        duration = max(10.0, min(300.0, float(request.args.get("duration", 60.0))))
    except (ValueError, TypeError):
        duration = 60.0

    try:
        from void_engine.binaural_tone import generate_sol_schumann_wav
        wav_bytes = generate_sol_schumann_wav(duration=duration)
    except Exception as exc:
        logger.error("Tone generation error: %s", exc)
        return jsonify({"error": "tone generation failed"}), 500

    user_id = session.get("user_id")
    if user_id:
        try:
            from void_engine.vortex_wallet import log_qisync_tone
            log_qisync_tone(user_id, session_id, tone_hz=432.0, beat_hz=7.83,
                            duration_sec=duration)
        except Exception as exc:
            logger.debug("Tone ledger log failed: %s", exc)

    filename = f"qisync_sol_schumann_{session_id}.wav"
    buf = io.BytesIO(wav_bytes)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="audio/wav",
        as_attachment=False,
        download_name=filename,
    )


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

    content_len = request.content_length or 0
    if content_len > _MAX_INGRESS_JSON_BYTES:
        return jsonify({"error": "request payload too large"}), 413

    data = request.get_json(silent=True) or {}
    stance = data.get("stance", "mabu")
    mode = data.get("mode", "csi")
    target_sec = _coerce_int(data.get("target_sec", 300), 300)

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

    content_len = request.content_length or 0
    if content_len > _MAX_INGRESS_JSON_BYTES:
        return jsonify({"error": "request payload too large"}), 413

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "invalid JSON payload"}), 400

    payload_key_error = _validate_tick_payload_keys(data)
    if payload_key_error:
        return jsonify({"error": payload_key_error}), 400

    session_id = data.get("session_id")
    if not _is_valid_session_id(session_id):
        return jsonify({"error": "valid session_id required"}), 400

    key = _session_key(user_id, session_id)
    rec = _ACTIVE_SESSIONS.get(key)
    if not rec:
        return jsonify({"error": "session not found or expired"}), 404
    if rec["ended"]:
        return jsonify({"error": "session already ended"}), 409

    now = time.time()

    # ── Freshness check ──────────────────────────────────────────────────────
    client_ts = data.get("client_ts")
    if client_ts is not None:
        client_ts_f = _coerce_float(client_ts, default=-1.0)
        if client_ts_f < 0 or abs(now - client_ts_f) > _TICK_FRESHNESS_WINDOW_S:
            return jsonify({"error": "tick timestamp out of freshness window"}), 400

    # ── Replay-nonce check ───────────────────────────────────────────────────
    nonce = data.get("nonce")
    if nonce is not None:
        nonce_str = str(nonce)[:128]
        seen = _seen_tick_nonces.setdefault(key, set())
        if nonce_str in seen:
            return jsonify({"error": "duplicate tick nonce rejected"}), 409
        seen.add(nonce_str)
        # Rotate oldest nonces to cap memory
        if len(seen) > _TICK_NONCE_MAX:
            _seen_tick_nonces[key] = set(list(seen)[_TICK_NONCE_MAX // 2 :])

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
        client_stable = _coerce_bool(data.get("stable", False), default=False)
        client_conf = max(0.0, min(1.0, _coerce_float(data.get("confidence", 0.0), 0.0)))
        client_chew = max(0, min(_MAX_CHEW_DELTA_PER_TICK, _coerce_int(data.get("chew_delta", 0), 0)))

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

    content_len = request.content_length or 0
    if content_len > _MAX_INGRESS_JSON_BYTES:
        return jsonify({"error": "request payload too large"}), 413

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not _is_valid_session_id(session_id):
        return jsonify({"error": "valid session_id required"}), 400

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

    # ── QiSync Founder Key derivation (non-blocking) ────────────────────────
    founder_key_result = None
    try:
        from void_engine.qisync_keygen import derive_founder_key
        chew_count = rec.get("chew_count", 0)
        mastic_freq = chew_count / max(elapsed, 1.0)  # chews per second
        jaw_pattern = f"{rec['stance']}-rhythm"
        key_data = derive_founder_key(
            mastication_frequency=round(mastic_freq, 4),
            chew_count=chew_count,
            jaw_pattern=jaw_pattern,
            stance=rec["stance"],
            metabolism_score=round(metabolism, 4),
            session_id=session_id,
        )
        founder_key_result = {
            "key_active": key_data["key_active"],
            "fingerprint_hash": key_data["fingerprint_hash"],
            "time_window": key_data["time_window"],
        }
    except Exception as exc:
        logger.debug("QiSync founder key derivation failed (non-fatal): %s", exc)

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
        "founder_key": founder_key_result,
    })


# =============================================================================
# RIPPLE 3 — MEMORY TRAINING STUDIO
# =============================================================================

import json as _json
from void_engine.db_pool import get_db as _get_db_memory

MEMORY_SCENES = [
    {
        "id": "scene_market",
        "title": "The Outdoor Market",
        "text": (
            "You enter a busy outdoor market on a warm Tuesday morning. "
            "To your left, a tall woman in a blue-and-white striped apron "
            "is arranging oranges into a pyramid. She is humming a slow tune. "
            "Beside her stands a young boy, perhaps eight, wearing red trainers, "
            "eating a green apple and watching pigeons. Directly ahead, a wooden "
            "sign reads 'Fresh Herbs — £1.50/bunch'. Three bundles of rosemary "
            "and two of thyme are lined up. An older man in a brown jacket sits "
            "on a folding stool reading a newspaper, his black dog leashed to the "
            "table leg. A conversation nearby: 'Did you see the match?' 'Terrible "
            "first half.' The smell of roasted almonds drifts from the right."
        ),
        "questions": [
            {"id": "q1", "text": "What colour was the woman's apron?", "answer": "blue-and-white striped"},
            {"id": "q2", "text": "What day of the week was it?", "answer": "tuesday"},
            {"id": "q3", "text": "What was the boy eating?", "answer": "green apple"},
            {"id": "q4", "text": "What colour were the boy's trainers?", "answer": "red"},
            {"id": "q5", "text": "What was the price of herbs?", "answer": "1.50"},
            {"id": "q6", "text": "How many bundles of thyme were there?", "answer": "two"},
            {"id": "q7", "text": "What was the dog leashed to?", "answer": "table leg"},
            {"id": "q8", "text": "What smell drifted from the right?", "answer": "roasted almonds"},
        ],
    },
    {
        "id": "scene_library",
        "title": "The Reading Room",
        "text": (
            "You walk into a quiet reading room at 3:00 PM. Four long tables "
            "run parallel to the windows. At the first table, a woman with "
            "short silver hair is annotating a red book with a pencil. An empty "
            "coffee cup sits to her right. At the second table, two teenagers "
            "whisper over a map spread between them; one has headphones around "
            "her neck. The third table is empty except for a forgotten yellow "
            "umbrella. At the fourth table near the back, a man in a green "
            "cardigan works at a laptop, a stack of five books beside him. "
            "A clock on the north wall shows 3:07. The librarian behind the "
            "desk has a name badge reading 'Fatima'. She stamps a book."
        ),
        "questions": [
            {"id": "q1", "text": "What time does the clock on the wall show?", "answer": "3:07"},
            {"id": "q2", "text": "What colour is the woman's hair?", "answer": "silver"},
            {"id": "q3", "text": "What colour was the book she was annotating?", "answer": "red"},
            {"id": "q4", "text": "What was left on the third table?", "answer": "yellow umbrella"},
            {"id": "q5", "text": "How many books were stacked beside the man?", "answer": "five"},
            {"id": "q6", "text": "What colour cardigan was the man wearing?", "answer": "green"},
            {"id": "q7", "text": "What is the librarian's name?", "answer": "fatima"},
            {"id": "q8", "text": "Where was the empty coffee cup?", "answer": "right"},
        ],
    },
    {
        "id": "scene_kitchen",
        "title": "The Morning Kitchen",
        "text": (
            "It is 7:22 AM in a small kitchen. A kettle on the right-hand "
            "burner begins to whistle. On the counter to the left, three "
            "eggs rest in a white bowl beside a bunch of fresh spinach. "
            "A calendar on the wall shows April; the 14th is circled in red. "
            "On the table: a blue mug half-full of tea, a folded newspaper "
            "showing a headline about local elections, and a phone face-down. "
            "A cat — grey, with white paws — sits on the windowsill looking "
            "outside. Someone is humming. A child's drawing is held to the "
            "fridge by a yellow magnet shaped like a sun."
        ),
        "questions": [
            {"id": "q1", "text": "What time is it?", "answer": "7:22"},
            {"id": "q2", "text": "What is on the right-hand burner?", "answer": "kettle"},
            {"id": "q3", "text": "What month is shown on the calendar?", "answer": "april"},
            {"id": "q4", "text": "Which date is circled?", "answer": "14th"},
            {"id": "q5", "text": "What colour is the mug?", "answer": "blue"},
            {"id": "q6", "text": "How many eggs are in the bowl?", "answer": "three"},
            {"id": "q7", "text": "What colour are the cat's paws?", "answer": "white"},
            {"id": "q8", "text": "What shape is the fridge magnet?", "answer": "sun"},
        ],
    },
]


def _score_recall(questions, answers):
    """
    Score recall answers. Returns 0.0-1.0.
    Simple fuzzy match: answer must contain the key term (case-insensitive).
    """
    if not questions or not answers:
        return 0.0
    correct = 0
    for q in questions:
        user_ans = str(answers.get(q["id"], "")).strip().lower()
        expected = q["answer"].lower()
        if expected in user_ans or user_ans in expected:
            correct += 1
    return round(correct / len(questions), 4)


def _compute_memory_level(user_id):
    """Compute cumulative memory level from completed sessions."""
    conn = _get_db_memory()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*), AVG(recall_score)
            FROM memory_sessions
            WHERE user_id = %s AND completed = TRUE
        """, (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            return 1
        total = int(row[0])
        avg_score = float(row[1]) if row[1] else 0.0
        level = max(1, int(total * avg_score * 2))
        return min(level, 100)
    finally:
        conn.close()


@qisync_bp.route("/qisync/memory")
def memory_studio():
    user_id = session.get("user_id")
    history = []
    memory_level = 1
    if user_id:
        memory_level = _compute_memory_level(user_id)
        conn = _get_db_memory()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_id, scene_duration_sec, recall_score,
                       memory_level, vtx_earned, completed_at
                FROM memory_sessions
                WHERE user_id = %s AND completed = TRUE
                ORDER BY completed_at DESC LIMIT 10
            """, (user_id,))
            for row in cur.fetchall():
                history.append({
                    "session_id": row[0],
                    "scene_duration_sec": row[1],
                    "recall_score": float(row[2]) if row[2] else 0.0,
                    "memory_level": row[3],
                    "vtx_earned": float(row[4]) if row[4] else 0.0,
                    "completed_at": row[5].isoformat() if row[5] else None,
                })
        except Exception as exc:
            logger.error("Memory history load error: %s", exc)
        finally:
            conn.close()
    return render_template("qisync_memory.html",
                           scenes=MEMORY_SCENES,
                           history=history,
                           memory_level=memory_level)


@qisync_bp.route("/api/qisync/memory/session-start", methods=["POST"])
def memory_session_start():
    import uuid as _uuid
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    scene_id = data.get("scene_id")
    try:
        duration_sec = max(60, min(1800, int(data.get("duration_sec") or 300)))
    except (ValueError, TypeError):
        duration_sec = 300

    scene = next((s for s in MEMORY_SCENES if s["id"] == scene_id), MEMORY_SCENES[0])
    sid = str(_uuid.uuid4())

    conn = _get_db_memory()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO memory_sessions (user_id, session_id, scene_text, scene_duration_sec)
            VALUES (%s, %s, %s, %s)
        """, (user_id, sid, scene["text"], duration_sec))
        conn.commit()
        return jsonify({
            "ok": True,
            "session_id": sid,
            "scene": {
                "id": scene["id"],
                "title": scene["title"],
                "text": scene["text"],
            },
            "duration_sec": duration_sec,
        })
    except Exception as exc:
        conn.rollback()
        logger.error("Memory session start error: %s", exc)
        return jsonify({"error": "failed to start session"}), 500
    finally:
        conn.close()


@qisync_bp.route("/api/qisync/memory/session-end", methods=["POST"])
def memory_session_end():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    sid = data.get("session_id")
    answers = data.get("answers") or {}
    scene_id = data.get("scene_id")

    if not sid:
        return jsonify({"error": "session_id required"}), 400

    scene = next((s for s in MEMORY_SCENES if s["id"] == scene_id), None)
    if not scene:
        return jsonify({"error": "invalid scene_id"}), 400

    conn = _get_db_memory()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, completed FROM memory_sessions
            WHERE session_id = %s AND user_id = %s
        """, (sid, user_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "session not found"}), 404
        if row[1]:
            return jsonify({"error": "session already completed"}), 409

        db_id = row[0]
        recall_score = _score_recall(scene["questions"], answers)
        memory_level = _compute_memory_level(user_id)

        cur.execute("""
            UPDATE memory_sessions
            SET completed = TRUE, recall_answers = %s,
                recall_score = %s, memory_level = %s, completed_at = NOW()
            WHERE id = %s
        """, (_json.dumps(answers), recall_score, memory_level, db_id))
        conn.commit()

        vtx_earned = 0.0
        reward = None
        try:
            from void_engine.vortex_wallet import mint_memory_session
            reward = mint_memory_session(user_id, sid, recall_score, memory_level)
            vtx_earned = reward.get("vtx_earned", 0)
            cur.execute(
                "UPDATE memory_sessions SET vtx_earned = %s WHERE id = %s",
                (vtx_earned, db_id)
            )
            conn.commit()
        except Exception as exc:
            logger.error("mint_memory_session failed: %s", exc)

        logger.info("Memory session ended: user=%s sid=%s score=%.4f vtx=%.4f",
                    user_id, sid, recall_score, vtx_earned)

        correct_answers = {q["id"]: q["answer"] for q in scene["questions"]}
        return jsonify({
            "ok": True,
            "session_id": sid,
            "recall_score": recall_score,
            "memory_level": memory_level,
            "vtx_earned": vtx_earned,
            "reward": reward,
            "correct_answers": correct_answers,
            "total_questions": len(scene["questions"]),
        })
    except Exception as exc:
        conn.rollback()
        logger.error("Memory session end error: %s", exc)
        return jsonify({"error": "failed to complete session"}), 500
    finally:
        conn.close()


@qisync_bp.route("/qisync/memory/insights")
def memory_insights():
    conn = _get_db_memory()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*), AVG(recall_score), AVG(memory_level)
            FROM memory_sessions WHERE completed = TRUE
        """)
        row = cur.fetchone()
        stats = {
            "total_sessions": int(row[0]) if row[0] else 0,
            "avg_recall": round(float(row[1]), 4) if row[1] else 0.0,
            "avg_level": round(float(row[2]), 1) if row[2] else 0.0,
        }
        cur.execute("""
            SELECT memory_level, COUNT(*) as user_count
            FROM (
                SELECT user_id, MAX(memory_level) as memory_level
                FROM memory_sessions WHERE completed = TRUE
                GROUP BY user_id
            ) sub
            GROUP BY memory_level ORDER BY memory_level ASC
        """)
        level_distribution = []
        for r in cur.fetchall():
            level_distribution.append({"level": r[0], "count": int(r[1])})
        cur.execute("""
            SELECT u.username, MAX(ms.memory_level) as top_level,
                   COUNT(ms.id) as sessions, AVG(ms.recall_score) as avg_score
            FROM memory_sessions ms
            JOIN users u ON u.id = ms.user_id
            WHERE ms.completed = TRUE
            GROUP BY u.username
            ORDER BY top_level DESC, avg_score DESC
            LIMIT 10
        """)
        leaderboard = []
        for r in cur.fetchall():
            leaderboard.append({
                "username": r[0], "top_level": int(r[1]),
                "sessions": int(r[2]),
                "avg_score": round(float(r[3]), 4) if r[3] else 0.0,
            })
        return render_template("memory_insights.html",
                               stats=stats,
                               level_distribution=level_distribution,
                               leaderboard=leaderboard)
    except Exception as exc:
        logger.error("Memory insights error: %s", exc)
        return render_template("memory_insights.html",
                               stats={}, level_distribution=[], leaderboard=[])
    finally:
        conn.close()


# =============================================================================
# AUDIO STEGANOGRAPHY — WaveWhisper + Spectrogram Layer
# =============================================================================

@qisync_bp.route("/api/qisync/stega/encode", methods=["POST"])
def qisync_stega_encode():
    """
    Encode a message into a 432 Hz audio carrier using one of two methods:
      method=spectrogram  — text painted visibly into the spectrogram (default)
      method=wavewhisper  — 14-segment display samples overlaid onto the tone

    Body (JSON or form):
      message  — string to hide, max 64 chars
      method   — "spectrogram" | "wavewhisper"
      duration — seconds of output audio (10–30, default 10)

    Returns: WAV audio stream
    """
    from flask import send_file
    import io

    data = request.get_json(silent=True) or request.form
    message = str(data.get("message", "VOID") or "VOID").strip()[:64]
    method = str(data.get("method", "spectrogram")).strip().lower()
    if method not in ("spectrogram", "wavewhisper"):
        method = "spectrogram"

    try:
        duration = max(5.0, min(30.0, float(data.get("duration", 10.0))))
    except (ValueError, TypeError):
        duration = 10.0

    if not message:
        return jsonify({"error": "message required"}), 400

    try:
        from void_engine.audio_stega import encode_message
        wav_bytes = encode_message(message, method=method, duration=duration)
    except Exception as exc:
        logger.error("Steganography encode failed: %s", exc)
        return jsonify({"error": "encode failed"}), 500

    safe_msg = "".join(c if c.isalnum() else "_" for c in message[:20])
    filename = f"void_stega_{method}_{safe_msg}.wav"
    buf = io.BytesIO(wav_bytes)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="audio/wav",
        as_attachment=False,
        download_name=filename,
    )


@qisync_bp.route("/api/qisync/stega/check-resonance", methods=["POST"])
def qisync_stega_check_resonance():
    """
    Check the 432 Hz resonance purity of an uploaded WAV file.

    Accepts multipart/form-data with field `file` (WAV).
    Returns JSON with snr_db, quality, and harmonic breakdown.
    """
    import tempfile, os
    f = request.files.get("file")
    if f is None:
        return jsonify({"error": "no file uploaded"}), 400
    if not f.filename.lower().endswith(".wav"):
        return jsonify({"error": "WAV files only"}), 400

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        from void_engine.stega import check_resonance_purity
        result = check_resonance_purity(tmp_path)
        return jsonify({"ok": True, "resonance": result})
    except Exception as exc:
        logger.error("Resonance check failed: %s", exc)
        return jsonify({"error": "resonance check failed"}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
