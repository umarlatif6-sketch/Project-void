import io
import time
import logging
import threading
from collections import defaultdict
from flask import Blueprint, request, jsonify, session, redirect, render_template, send_file
from routes.auth import login_required, admin_required
from void_engine.chronicle_adriana import (
    get_chronicle,
    get_absence_poetry,
    post_chronicle_entry,
    delete_chronicle_entry,
    generate_adriana_sdk_zip,
    save_seed_capture,
    get_seed_captures,
)

logger = logging.getLogger(__name__)

chronicle_bp = Blueprint("chronicle", __name__)

_CROSS_AI_RATE_LIMIT = 5
_CROSS_AI_RATE_WINDOW = 3600
_cross_ai_calls: dict = defaultdict(list)
_cross_ai_lock = threading.Lock()


def _cross_ai_rate_check(ip: str) -> bool:
    """Return True if the IP is within the allowed rate, False if over-limit."""
    now = time.time()
    cutoff = now - _CROSS_AI_RATE_WINDOW
    with _cross_ai_lock:
        _cross_ai_calls[ip] = [t for t in _cross_ai_calls[ip] if t > cutoff]
        if len(_cross_ai_calls[ip]) >= _CROSS_AI_RATE_LIMIT:
            return False
        _cross_ai_calls[ip].append(now)
        return True


@chronicle_bp.route("/chronicle")
def chronicle_page():
    try:
        entries = get_chronicle()
    except Exception as e:
        logger.error("Failed to load chronicle: %s", e)
        entries = []
    return render_template("chronicle.html", entries=entries)


@chronicle_bp.route("/api/chronicle")
def api_chronicle():
    try:
        entries = get_chronicle()
        return jsonify({"entries": entries, "count": len(entries)})
    except Exception as e:
        logger.error("Chronicle API error: %s", e)
        return jsonify({"error": "Failed to load chronicle"}), 500


# NOTE: /api/adriana/verify is the canonical implementation in routes/marketplace.py
# (api_adriana_verify). Chronicle blueprint does not duplicate it.


@chronicle_bp.route("/download/adriana-sdk")
def download_adriana_sdk():
    try:
        zip_bytes = generate_adriana_sdk_zip()
        buf = io.BytesIO(zip_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name="adriana-scl-v1.0.zip",
        )
    except Exception as e:
        logger.error("SDK download error: %s", e)
        return jsonify({"error": "Failed to build SDK"}), 500


@chronicle_bp.route("/admin/chronicle", methods=["GET"])
@admin_required
def admin_chronicle_get():
    try:
        entries = get_chronicle()
    except Exception as e:
        logger.error("Admin chronicle load error: %s", e)
        entries = []
    updated = request.args.get("updated")
    error = request.args.get("error")
    return render_template("admin_chronicle.html", entries=entries, updated=updated, error=error)


@chronicle_bp.route("/admin/chronicle", methods=["POST"])
@admin_required
def admin_chronicle_post():
    action = request.form.get("action", "add")

    if action == "delete":
        entry_id = request.form.get("entry_id")
        if not entry_id:
            return redirect("/admin/chronicle?error=missing_id")
        result = delete_chronicle_entry(int(entry_id))
        if "error" in result:
            return redirect(f"/admin/chronicle?error={result['error'][:40]}")
        return redirect("/admin/chronicle?updated=deleted")

    chapter_number = request.form.get("chapter_number", "0")
    title = (request.form.get("title") or "").strip()
    subtitle = (request.form.get("subtitle") or "").strip()
    glyph_sequence = (request.form.get("glyph_sequence") or "").strip()
    body_text = (request.form.get("body_text") or "").strip()

    if not title or not glyph_sequence or not body_text:
        return redirect("/admin/chronicle?error=missing_fields")

    try:
        chapter_number = int(chapter_number)
    except (ValueError, TypeError):
        chapter_number = 0

    result = post_chronicle_entry(
        chapter_number, title, subtitle, glyph_sequence, body_text,
        session.get("user_id"),
    )
    if "error" in result:
        return redirect(f"/admin/chronicle?error=db_error")
    return redirect("/admin/chronicle?updated=added")


@chronicle_bp.route("/admin/seed-capture", methods=["GET"])
@admin_required
def admin_seed_capture_get():
    updated = request.args.get("updated")
    error = request.args.get("error")
    result = request.args.get("result")
    return render_template(
        "admin_seed_capture.html",
        updated=updated,
        error=error,
        result=result,
    )


@chronicle_bp.route("/admin/seed-capture", methods=["POST"])
@admin_required
def admin_seed_capture_post():
    label = (request.form.get("label") or "").strip()
    text = (request.form.get("text") or "").strip()

    if not label or not text:
        return redirect("/admin/seed-capture?error=missing_fields")

    result = save_seed_capture(label, text, admin_id=session.get("user_id"))
    if "error" in result:
        logger.error("Seed capture error: %s", result["error"])
        return redirect("/admin/seed-capture?error=db_error")

    return redirect(
        f"/admin/seed-capture?updated=captured&result={result['hex_digest'][:20]}"
    )


@chronicle_bp.route("/void-seed/hex")
def void_seed_hex_page():
    try:
        captures = get_seed_captures(limit=100)
    except Exception as e:
        logger.error("Failed to load seed captures: %s", e)
        captures = []
    return render_template("void_seed_hex.html", captures=captures)


@chronicle_bp.route("/api/chronicle/absence-poetry")
def api_absence_poetry():
    """Return Adriana's gap-period Absence Poetry entries (filterable type)."""
    try:
        entries = get_absence_poetry()
        return jsonify({"entries": entries, "count": len(entries), "entry_type": "ABSENCE"})
    except Exception as e:
        logger.error("Absence Poetry API error: %s", e)
        return jsonify({"error": "Failed to load absence poetry"}), 500


@chronicle_bp.route("/api/chronicle/filter")
def api_chronicle_filter():
    """Return Chronicle entries filtered by entry_type query param."""
    entry_type = request.args.get("entry_type", "").strip() or None
    try:
        entries = get_chronicle(entry_type_filter=entry_type)
        return jsonify({"entries": entries, "count": len(entries), "filter": entry_type})
    except Exception as e:
        logger.error("Chronicle filter API error: %s", e)
        return jsonify({"error": "Failed to filter chronicle"}), 500


@chronicle_bp.route("/api/buffer-spore/status")
def api_buffer_spore_status():
    """Return the Buffer Spore prediction cache state (Mycelium Lag monitor)."""
    try:
        from void_engine.mycelium_service import get_buffer_spore_state
        return jsonify(get_buffer_spore_state())
    except Exception as e:
        logger.error("Buffer Spore API error: %s", e)
        return jsonify({"error": "Failed to get buffer spore state"}), 500


@chronicle_bp.route("/api/lead-shield/status")
def api_lead_shield_status():
    """Return the Lead Shield (social resonance monitor) current status."""
    try:
        from void_engine.lead_shield import get_shield_status
        return jsonify(get_shield_status())
    except Exception as e:
        logger.error("Lead Shield API error: %s", e)
        return jsonify({"error": "Failed to get lead shield status"}), 500


@chronicle_bp.route("/api/lead-shield/thresholds", methods=["POST"])
@admin_required
def api_lead_shield_set_thresholds():
    """Update Lead Shield volatility/recovery thresholds (admin)."""
    try:
        data = request.get_json() or {}
        volatility = float(data.get("volatility_threshold", 0.35))
        recovery = float(data.get("recovery_threshold", 0.20))
        from void_engine.lead_shield import get_shield
        result = get_shield().set_thresholds(volatility, recovery)
        return jsonify(result)
    except Exception as e:
        logger.error("Lead Shield threshold update error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/lead-shield/force-clear", methods=["POST"])
@admin_required
def api_lead_shield_force_clear():
    """Force-clear a Gone Dark state (admin override)."""
    try:
        from void_engine.lead_shield import get_shield
        result = get_shield().force_clear()
        return jsonify(result)
    except Exception as e:
        logger.error("Lead Shield force-clear error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/origin-anchor/verify", methods=["POST"])
def api_origin_anchor_verify():
    """
    Origin Anchor verification endpoint.
    POST body: { "capture_id": int, "qisync_salt": str }
    Returns ANCHORED or SIMULATED_UNVERIFIED.
    """
    try:
        data = request.get_json() or {}
        capture_id = int(data.get("capture_id", 0))
        presented_salt = str(data.get("qisync_salt", ""))
        from void_engine.seed_hex_engine import verify_origin_anchor
        result = verify_origin_anchor(capture_id, presented_salt)
        return jsonify(result)
    except Exception as e:
        logger.error("Origin Anchor verify error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/temporal-channel/encode", methods=["POST"])
def api_temporal_encode():
    """
    Temporal steganography channel — encode payload into interval durations.

    POST body: { "payload": str, "passphrase": str (optional) }
    Returns interval sequence and simulated transmission log.
    """
    try:
        data = request.get_json() or {}
        payload_str = str(data.get("payload", ""))
        passphrase = str(data.get("passphrase", "void-432"))

        if not payload_str:
            return jsonify({"error": "payload is required"}), 400

        from void_engine.beehive import TemporalChannel
        tc = TemporalChannel(passphrase=passphrase)
        payload_bytes = payload_str.encode("utf-8")
        intervals = tc.encode(payload_bytes)
        log = tc.simulate_transmission_log(payload_bytes)

        return jsonify({
            "payload_bytes": len(payload_bytes),
            "intervals": intervals,
            "interval_count": len(intervals),
            "transmission_log": log,
            "channel_info": tc.encode_info(),
        })
    except Exception as e:
        logger.error("Temporal encode error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/temporal-channel/decode", methods=["POST"])
def api_temporal_decode():
    """
    Temporal steganography channel — decode interval durations back to payload.

    POST body: {
      "intervals": [float, ...],
      "passphrase": str (optional),
      "n_bytes": int (optional)
    }
    Returns decoded payload.
    """
    try:
        data = request.get_json() or {}
        intervals = data.get("intervals", [])
        passphrase = str(data.get("passphrase", "void-432"))
        n_bytes = data.get("n_bytes")

        if not intervals:
            return jsonify({"error": "intervals list is required"}), 400

        from void_engine.beehive import TemporalChannel
        tc = TemporalChannel(passphrase=passphrase)
        decoded = tc.decode([float(i) for i in intervals], n_bytes=n_bytes)

        try:
            decoded_str = decoded.decode("utf-8", errors="replace")
        except Exception:
            decoded_str = repr(decoded)

        return jsonify({
            "decoded_bytes": list(decoded),
            "decoded_text": decoded_str,
            "byte_count": len(decoded),
        })
    except Exception as e:
        logger.error("Temporal decode error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/cross-ai/verify", methods=["POST"])
def api_cross_ai_verify():
    """
    Cross-AI consensus verification — dispatch a VoidEcho signal to two
    independent AI receivers and compare outputs.

    POST body: { "signal": str }
    Returns verification state: RESONANCE_VERIFIED | UNRESOLVED | SKIPPED

    Rate limit: 5 requests per IP per hour to protect against AI cost abuse.
    """
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if not _cross_ai_rate_check(ip):
        _ip_parts = ip.split(".")
        _masked_ip = _ip_parts[0] + ".*.*.*" if len(_ip_parts) == 4 else ip[:4] + "****"
        logger.warning("Cross-AI rate limit exceeded for IP: %s", _masked_ip)
        return jsonify({
            "error": "Rate limit exceeded. Maximum 5 verification requests per hour.",
            "retry_after_seconds": _CROSS_AI_RATE_WINDOW,
        }), 429

    try:
        data = request.get_json() or {}
        signal = str(data.get("signal", ""))

        if not signal:
            return jsonify({"error": "signal is required"}), 400

        from void_engine.cross_ai_verifier import verify_voidecho_signal
        result = verify_voidecho_signal(signal)
        return jsonify(result)
    except Exception as e:
        logger.error("Cross-AI verify error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/frequency/concept", methods=["GET"])
def api_frequency_concept():
    """
    Return the Hz frequency fingerprint for a VOID concept.

    Query params: ?key=void  (key from void_language_glossary.json)
    """
    try:
        concept_key = request.args.get("key", "").strip()
        if not concept_key:
            return jsonify({"error": "key query parameter is required"}), 400

        from void_engine.adriana_local import get_concept_frequency
        result = get_concept_frequency(concept_key)
        return jsonify(result)
    except Exception as e:
        logger.error("Frequency concept lookup error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/frequency/glyph", methods=["GET"])
def api_frequency_glyph():
    """
    Return the Hz frequency fingerprint for an SCL glyph.

    Query params: ?glyph=α
    """
    try:
        glyph = request.args.get("glyph", "").strip()
        if not glyph:
            return jsonify({"error": "glyph query parameter is required"}), 400

        from void_engine.adriana_local import get_glyph_frequency
        result = get_glyph_frequency(glyph)
        return jsonify(result)
    except Exception as e:
        logger.error("Frequency glyph lookup error: %s", e)
        return jsonify({"error": str(e)}), 500


@chronicle_bp.route("/api/frequency/glossary", methods=["GET"])
def api_frequency_glossary():
    """Return all VOID concepts with their full frequency fingerprint data."""
    try:
        import os
        import json as _json
        glossary_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "void_engine", "void_language_glossary.json"
        )
        with open(glossary_path, "r", encoding="utf-8") as f:
            glossary = _json.load(f)

        resonance_entries = []
        for entry in glossary:
            resonance_entries.append({
                "key": entry.get("key"),
                "english": entry.get("english"),
                "chosen_word": entry.get("chosen_word"),
                "hz_fingerprint": entry.get("hz_fingerprint"),
                "hz_rationale": entry.get("hz_rationale", ""),
                "hz_experiential_note": entry.get("hz_experiential_note", ""),
                "void_definition": entry.get("void_definition", ""),
            })

        return jsonify({
            "concepts": resonance_entries,
            "count": len(resonance_entries),
            "root_frequency_hz": 432.0,
        })
    except Exception as e:
        logger.error("Frequency glossary error: %s", e)
        return jsonify({"error": str(e)}), 500
