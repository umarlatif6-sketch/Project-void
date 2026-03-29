import hashlib
import hmac
import logging
import os
import re
from flask import Blueprint, request, jsonify, session, render_template
from routes.auth import login_required
from void_engine.hex_flower import parse_hex, detect_hex_in_message, stable_user_salt
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)

hex_flower_bp = Blueprint("hex_flower", __name__)

HEX_FLOWER_COST = 5
HEX_FLOWER_MAX_LEN = 512

_SHARE_SECRET = os.environ.get("SESSION_SECRET", "")
_SECRET_MISSING_WARN_LOGGED = False


def _get_share_secret():
    """Return the share secret or raise RuntimeError if unconfigured."""
    global _SECRET_MISSING_WARN_LOGGED
    if not _SHARE_SECRET:
        if not _SECRET_MISSING_WARN_LOGGED:
            logger.error(
                "SESSION_SECRET env var is not set — hex flower share links are disabled. "
                "Configure SESSION_SECRET to enable this feature."
            )
            _SECRET_MISSING_WARN_LOGGED = True
        raise RuntimeError("SESSION_SECRET not configured")
    return _SHARE_SECRET


def _canonical_hex(hex_input):
    """
    Return the cleaned, canonical hex string used as both the signing payload
    and the render input.  This is the single authoritative form — used
    consistently in generate, view, and page validation.
    """
    return (
        re.sub(r'^0x', '', hex_input, flags=re.IGNORECASE)
        .replace("-", "")
        .replace(" ", "")
        [:HEX_FLOWER_MAX_LEN]
    )


def _make_share_sig(canonical, resonance_state, user_salt):
    """
    Generate a server-side HMAC signature over the full canonical hex payload
    + resonance + user_salt so the shared view can reproduce the exact flower.

    Payload: canonical | resonance_state | str(user_salt)
    sig = HMAC-SHA256(SESSION_SECRET, payload)[:32]
    """
    secret = _get_share_secret()
    payload = f"{canonical}|{resonance_state}|{user_salt}"
    return hmac.new(
        secret.encode(),
        payload.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()[:32]


def _verify_share_sig(canonical, sig, resonance_state, user_salt):
    """
    Return True if the signature matches canonical hex + resonance + user_salt.
    Uses constant-time compare to prevent timing attacks.
    """
    try:
        expected = _make_share_sig(canonical, resonance_state, user_salt)
        return hmac.compare_digest(expected, sig)
    except RuntimeError:
        return False


def _get_resonance_state(user_id):
    """Derive the user's current resonance state from their fairy profile."""
    try:
        from routes.fairy import get_fairy_profile
        count = get_fairy_profile(user_id).get("count", 0)
        if count >= 30:
            return "resonant"
        if count >= 10:
            return "aligned"
        if count >= 3:
            return "drifting"
        return "dormant"
    except Exception:
        return "aligned"


def _log_hex_flower_event(user_id, hex_hash, burned, new_balance):
    """Log a hex flower burn event for audit purposes."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hex_flower_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                hex_hash_prefix TEXT,
                peace_burned NUMERIC(10,4),
                new_peace_balance NUMERIC(20,4),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            INSERT INTO hex_flower_log (user_id, hex_hash_prefix, peace_burned, new_peace_balance)
            VALUES (%s, %s, %s, %s)
        """, (user_id, hex_hash[:32], burned, new_balance))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error("hex_flower_log failed: %s", e)


@hex_flower_bp.route("/hex-flower")
def hex_flower_page():
    """
    Standalone Hex Flower page.
    - Shared views (/hex-flower?h=<hex>&u=<sig>&r=<resonance>&s=<salt>) are public.
    - Direct access requires login.
    """
    shared_hex_raw = request.args.get("h", "").strip()
    shared_sig = request.args.get("u", "").strip()
    shared_resonance = request.args.get("r", "aligned").strip()
    try:
        shared_salt = int(request.args.get("s", "0").strip())
    except ValueError:
        shared_salt = 0

    is_shared_view = False
    canonical = ""
    if shared_hex_raw and shared_sig:
        canonical = _canonical_hex(shared_hex_raw)
        is_shared_view = _verify_share_sig(canonical, shared_sig, shared_resonance, shared_salt)

    if not is_shared_view:
        if not session.get("user_id"):
            from flask import redirect, url_for
            return redirect(url_for("auth.login"))

    user_id = session.get("user_id")
    peace_balance = 0.0
    if user_id:
        try:
            from void_engine.vortex_wallet import get_peace_balance
            peace_balance = get_peace_balance(user_id)
        except Exception:
            pass

    return render_template(
        "hex_flower.html",
        peace_balance=peace_balance,
        hex_flower_cost=HEX_FLOWER_COST,
        shared_hex=canonical if is_shared_view else "",
        shared_resonance=shared_resonance if is_shared_view else "aligned",
        shared_salt=shared_salt if is_shared_view else 0,
        shared_sig=shared_sig if is_shared_view else "",
        is_shared_view=is_shared_view,
    )


@hex_flower_bp.route("/api/hex-flower/generate", methods=["POST"])
@login_required
def hex_flower_generate():
    """
    Generate a flower spec for a hex string.
    Costs HEX_FLOWER_COST PEACE tokens (burned from supply).
    Returns share_sig, resonance_state, canonical_hex, and user_salt so the
    share URL fully encodes all parameters needed to reproduce the exact flower.
    """
    data = request.get_json(silent=True) or {}
    hex_input = (data.get("hex") or "").strip()

    if not hex_input:
        return jsonify({"error": "hex string is required"}), 400

    canonical = _canonical_hex(hex_input)
    if len(canonical) < 6:
        return jsonify({"error": "hex string must be at least 6 characters"}), 400

    user_id = session.get("user_id")
    resonance_state = _get_resonance_state(user_id)
    user_salt = stable_user_salt(user_id)

    try:
        from void_engine.vortex_wallet import get_peace_balance
        balance = get_peace_balance(user_id)
    except Exception:
        balance = 0.0

    if balance < HEX_FLOWER_COST:
        return jsonify({
            "error": "insufficient_peace",
            "balance": balance,
            "cost": HEX_FLOWER_COST,
        }), 402

    new_balance = balance
    try:
        from void_engine.vortex_wallet import burn_peace_for_hex_flower
        burn_result = burn_peace_for_hex_flower(user_id, canonical)
        new_balance = burn_result.get("new_balance", 0.0)
        _log_hex_flower_event(user_id, canonical, HEX_FLOWER_COST, new_balance)
    except ValueError as e:
        return jsonify({
            "error": "insufficient_peace",
            "detail": str(e),
            "cost": HEX_FLOWER_COST,
        }), 402
    except Exception as e:
        logger.error("burn_peace_for_hex_flower failed: %s", e)
        return jsonify({"error": "burn failed, please try again"}), 500

    try:
        from routes.fairy import update_fairy_profile, get_fairy_profile
        profile = get_fairy_profile(user_id)
        update_fairy_profile(
            user_id,
            profile.get("style", ""),
            profile.get("topics", "hex flower, transaction visualisation"),
            profile.get("count", 0) + 1,
            profile.get("depth_level", 0),
        )
    except Exception:
        pass

    spec = parse_hex(canonical, resonance_state, user_salt=user_salt)

    try:
        share_sig = _make_share_sig(canonical, resonance_state, user_salt)
    except RuntimeError:
        share_sig = None

    return jsonify({
        "ok": True,
        "spec": spec,
        "resonance_state": resonance_state,
        "canonical_hex": canonical,
        "user_salt": user_salt,
        "cost": HEX_FLOWER_COST,
        "new_balance": new_balance,
        "share_sig": share_sig,
    })


@hex_flower_bp.route("/api/hex-flower/view", methods=["POST"])
def hex_flower_view():
    """
    Render a flower spec for a validated shared link — no PEACE cost.
    Validates the server-side HMAC signature, then renders using the exact
    canonical hex + resonance + user_salt bound in the signature.
    The response renders canonical (server-verified) input, not the raw
    user-supplied value, preventing replay/tamper with altered hex.
    Public endpoint (no login required) so anyone can view shared flowers.
    """
    data = request.get_json(silent=True) or {}
    hex_input = (data.get("hex") or "").strip()
    sig = (data.get("sig") or "").strip()
    resonance_state = (data.get("resonance_state") or "aligned").strip()
    try:
        user_salt = int(data.get("user_salt", 0))
    except (TypeError, ValueError):
        user_salt = 0

    if not hex_input or not sig:
        return jsonify({"error": "hex and sig are required"}), 400

    canonical = _canonical_hex(hex_input)
    if len(canonical) < 6:
        return jsonify({"error": "invalid hex"}), 400

    if not _verify_share_sig(canonical, sig, resonance_state, user_salt):
        return jsonify({"error": "invalid or expired share link"}), 403

    spec = parse_hex(canonical, resonance_state, user_salt=user_salt)

    return jsonify({"ok": True, "spec": spec, "resonance_state": resonance_state})


@hex_flower_bp.route("/api/hex-flower/preview", methods=["POST"])
@login_required
def hex_flower_preview():
    """
    Return a flower spec WITHOUT burning tokens.
    Used by Adriana's inline chat detection (no token charge for chat previews).
    """
    data = request.get_json(silent=True) or {}
    hex_input = (data.get("hex") or "").strip()

    canonical = _canonical_hex(hex_input)
    if not canonical or len(canonical) < 6:
        return jsonify({"error": "hex too short"}), 400

    user_id = session.get("user_id")
    resonance_state = _get_resonance_state(user_id)
    user_salt = stable_user_salt(user_id)
    spec = parse_hex(canonical, resonance_state, user_salt=user_salt)

    return jsonify({"ok": True, "spec": spec, "resonance_state": resonance_state})
