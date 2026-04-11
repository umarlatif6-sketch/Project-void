"""
VoidMessage — Text Message Hidden in Sound

Routes:
  GET  /voidmessage              — Main page (encode interface)
  POST /voidmessage/encode       — Hide a text message in audio, return download + code
  GET  /voidmessage/decode       — Decode page
  POST /voidmessage/decode       — Reveal hidden message from audio + code
  GET  /voidmessage/subscribe    — Subscription info page
  POST /voidmessage/checkout     — Stripe checkout for Seed/Signal tier
  GET  /voidmessage/checkout/success — Post-payment confirmation
"""

import os
import io
import json
import uuid
import wave
import logging
import secrets
import hashlib
import sqlite3
from datetime import datetime, timezone, timedelta
from flask import (
    Blueprint, render_template, request, jsonify, send_file,
    redirect, url_for, session
)

logger = logging.getLogger(__name__)

voidmessage_bp = Blueprint("voidmessage", __name__)

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "voidmessage.db")
_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output_audio", "voidmessage")
_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "voidmessage")

os.makedirs(_OUTPUT_DIR, exist_ok=True)
os.makedirs(_UPLOAD_DIR, exist_ok=True)

FREE_DAILY_LIMIT = 3
FREE_MAX_CHARS = 500
SEED_MAX_CHARS = 5000
SIGNAL_MAX_CHARS = 50000

TIERS = {
    "seed": {"price_pence": 900, "label": "Seed — £9/month", "max_chars": SEED_MAX_CHARS, "monthly_limit": 200},
    "signal": {"price_pence": 4900, "label": "Signal — £49/month", "max_chars": SIGNAL_MAX_CHARS, "monthly_limit": 0},
}


def _init_db():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vm_messages (
            id TEXT PRIMARY KEY,
            retrieval_code TEXT UNIQUE NOT NULL,
            output_path TEXT NOT NULL,
            sender_ip TEXT,
            created_at TEXT NOT NULL,
            tier TEXT DEFAULT 'free'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vm_subscriptions (
            id TEXT PRIMARY KEY,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            tier TEXT NOT NULL,
            email TEXT,
            sub_key TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vm_free_usage (
            ip TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def _get_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _free_usage_today(ip: str) -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = _get_db()
    row = db.execute("SELECT count FROM vm_free_usage WHERE ip=? AND date=?", (ip, today)).fetchone()
    db.close()
    return row["count"] if row else 0


def _increment_free_usage(ip: str):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = _get_db()
    db.execute("""
        INSERT INTO vm_free_usage (ip, date, count) VALUES (?, ?, 1)
        ON CONFLICT(ip) DO UPDATE SET
            count = CASE WHEN date=? THEN count+1 ELSE 1 END,
            date = ?
    """, (ip, today, today, today))
    db.commit()
    db.close()


def _get_sub_from_session() -> dict | None:
    sub_key = session.get("vm_sub_key")
    if not sub_key:
        return None
    db = _get_db()
    row = db.execute(
        "SELECT * FROM vm_subscriptions WHERE sub_key=? AND status='active'", (sub_key,)
    ).fetchone()
    db.close()
    return dict(row) if row else None


def _generate_carrier_wav() -> bytes:
    import numpy as np
    sample_rate = 44100
    duration = 20.0
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    audio = (
        0.45 * np.sin(2 * np.pi * 432.0 * t) +
        0.18 * np.sin(2 * np.pi * 864.0 * t) +
        0.09 * np.sin(2 * np.pi * 1296.0 * t) +
        0.04 * np.sin(2 * np.pi * 216.0 * t)
    )

    lfo = 1.0 + 0.15 * np.sin(2 * np.pi * 0.1 * t)
    audio *= lfo

    fade = int(1.5 * sample_rate)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)

    peak = max(abs(audio.max()), abs(audio.min()), 1e-9)
    audio = audio / peak * 0.8

    pcm = (audio * 32000).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _wav_to_16bit_mono(wav_bytes: bytes) -> bytes:
    import numpy as np
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        params = wf.getparams()
        sampwidth = params.sampwidth
        nchannels = params.nchannels
        framerate = params.framerate
        nframes = params.nframes
        raw = wf.readframes(nframes)

    if sampwidth == 2 and nchannels == 1:
        return wav_bytes

    if sampwidth == 2:
        samples = np.frombuffer(raw, dtype=np.int16)
    elif sampwidth == 4:
        samples = (np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2**31 * 32767).astype(np.int16)
    else:
        samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 127.5 - 1.0) * 32767
        samples = samples.astype(np.int16)

    if nchannels > 1:
        samples = samples.reshape(-1, nchannels).mean(axis=1).astype(np.int16)

    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(samples.tobytes())
    return out.getvalue()


def _hide_message_in_audio(message: str, carrier_wav_bytes: bytes, passphrase: str) -> bytes:
    from void_engine.stega import encode as stega_encode

    payload = message.encode("utf-8")

    carrier_path = os.path.join(_UPLOAD_DIR, f"carrier_{uuid.uuid4().hex}.wav")
    output_path = os.path.join(_OUTPUT_DIR, f"vm_{uuid.uuid4().hex}.wav")

    try:
        with open(carrier_path, "wb") as f:
            f.write(carrier_wav_bytes)

        stega_encode(
            carrier_path=carrier_path,
            payload=payload,
            file_name="message",
            extension=".txt",
            output_path=output_path,
            lsb_depth=1,
            passphrase=passphrase,
        )

        with open(output_path, "rb") as f:
            result = f.read()
        return result, output_path
    finally:
        if os.path.exists(carrier_path):
            os.remove(carrier_path)


def _reveal_message_from_audio(audio_wav_bytes: bytes, passphrase: str) -> str:
    from void_engine.stega import decode as stega_decode

    audio_path = os.path.join(_UPLOAD_DIR, f"decode_{uuid.uuid4().hex}.wav")
    try:
        with open(audio_path, "wb") as f:
            f.write(audio_wav_bytes)

        payload_bytes, _, _ = stega_decode(audio_path, passphrase=passphrase)
        return payload_bytes.decode("utf-8", errors="replace")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


def _store_code(record_id, retrieval_code, output_path, sender_ip, tier="free"):
    db = _get_db()
    db.execute(
        "INSERT INTO vm_messages (id, retrieval_code, output_path, sender_ip, created_at, tier) VALUES (?,?,?,?,?,?)",
        (record_id, retrieval_code, output_path, sender_ip, datetime.now(timezone.utc).isoformat(), tier)
    )
    db.commit()
    db.close()


def _get_passphrase_store():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vm_passphrases.json")


def _store_passphrase(code: str, passphrase: str):
    path = _get_passphrase_store()
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[code] = passphrase
    with open(path, "w") as f:
        json.dump(data, f)


def _lookup_passphrase(code: str) -> str | None:
    path = _get_passphrase_store()
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get(code)
    except Exception:
        return None


try:
    _init_db()
except Exception as _e:
    logger.error("[VoidMessage] DB init failed: %s", _e)


@voidmessage_bp.route("/voidmessage")
def index():
    sub = _get_sub_from_session()
    tier = sub["tier"] if sub else "free"
    ip = request.remote_addr or "unknown"
    free_used = _free_usage_today(ip)
    return render_template(
        "voidmessage.html",
        tier=tier,
        free_used=free_used,
        free_limit=FREE_DAILY_LIMIT,
    )


@voidmessage_bp.route("/voidmessage/encode", methods=["POST"])
def encode_message():
    ip = request.remote_addr or "unknown"
    sub = _get_sub_from_session()
    tier = sub["tier"] if sub else "free"

    message = (request.form.get("message") or "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    max_chars = FREE_MAX_CHARS if tier == "free" else TIERS.get(tier, {}).get("max_chars", FREE_MAX_CHARS)
    if len(message) > max_chars:
        return jsonify({"error": f"Message too long. Maximum {max_chars} characters for {tier} tier."}), 400

    if tier == "free":
        used = _free_usage_today(ip)
        if used >= FREE_DAILY_LIMIT:
            return jsonify({
                "error": "Free daily limit reached (3 messages/day). Upgrade to Seed for more.",
                "upgrade": True
            }), 429

    audio_file = request.files.get("audio")
    if audio_file and audio_file.filename:
        ext = os.path.splitext(audio_file.filename)[1].lower()
        if ext not in (".wav",):
            return jsonify({"error": "Audio must be a WAV file"}), 400
        if tier == "free":
            return jsonify({"error": "Custom audio requires a Seed or Signal subscription."}), 403
        carrier_bytes = audio_file.read()
        try:
            carrier_bytes = _wav_to_16bit_mono(carrier_bytes)
        except Exception as e:
            logger.warning("[VoidMessage] WAV conversion failed: %s", e)
    else:
        carrier_bytes = _generate_carrier_wav()

    try:
        passphrase = secrets.token_hex(24)
        encoded_bytes, output_path = _hide_message_in_audio(message, carrier_bytes, passphrase)

        retrieval_code = "VM-" + secrets.token_hex(6).upper()
        record_id = uuid.uuid4().hex

        _store_code(record_id, retrieval_code, output_path, ip, tier)
        _store_passphrase(retrieval_code, passphrase)

        if tier == "free":
            _increment_free_usage(ip)

        download_url = url_for("voidmessage.download_audio", code=retrieval_code)

        return jsonify({
            "retrieval_code": retrieval_code,
            "download_url": download_url,
            "message_length": len(message),
            "tier": tier,
        })

    except Exception as e:
        logger.error("[VoidMessage] Encode error: %s", e)
        return jsonify({"error": f"Encoding failed: {str(e)}"}), 500


@voidmessage_bp.route("/voidmessage/download/<code>")
def download_audio(code):
    code = code.strip().upper()
    db = _get_db()
    row = db.execute("SELECT output_path FROM vm_messages WHERE retrieval_code=?", (code,)).fetchone()
    db.close()
    if not row or not os.path.exists(row["output_path"]):
        return "File not found", 404
    return send_file(
        row["output_path"],
        as_attachment=True,
        download_name=f"voidmessage_{code}.wav",
        mimetype="audio/wav"
    )


@voidmessage_bp.route("/voidmessage/decode", methods=["GET", "POST"])
def decode_page():
    if request.method == "GET":
        code = request.args.get("code", "").strip().upper()
        return render_template("voidmessage_decode.html", prefill_code=code)

    code = (request.form.get("retrieval_code") or "").strip().upper()
    audio_file = request.files.get("audio")

    if not code:
        return jsonify({"error": "Retrieval code required"}), 400
    if not audio_file or not audio_file.filename:
        return jsonify({"error": "Audio file required"}), 400

    passphrase = _lookup_passphrase(code)
    if not passphrase:
        return jsonify({"error": "Invalid retrieval code — no record found"}), 404

    try:
        audio_bytes = audio_file.read()
        try:
            audio_bytes = _wav_to_16bit_mono(audio_bytes)
        except Exception:
            pass

        message = _reveal_message_from_audio(audio_bytes, passphrase)
        return jsonify({"message": message, "retrieval_code": code})

    except Exception as e:
        logger.error("[VoidMessage] Decode error: %s", e)
        return jsonify({"error": "Could not decode message — wrong file or code."}), 400


@voidmessage_bp.route("/voidmessage/subscribe")
def subscribe_page():
    sub = _get_sub_from_session()
    return render_template("voidmessage_subscribe.html", current_sub=sub, tiers=TIERS)


@voidmessage_bp.route("/voidmessage/checkout", methods=["POST"])
def checkout():
    tier = request.form.get("tier", "").strip().lower()
    if tier not in TIERS:
        return "Invalid tier", 400

    try:
        from routes.stripe_client import get_stripe_client
        sc = get_stripe_client()

        domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
        base_url = f"https://{domains[0]}"

        pending_id = uuid.uuid4().hex
        session["vm_pending_checkout"] = pending_id
        session["vm_pending_tier"] = tier

        price_data = {
            "currency": "gbp",
            "unit_amount": TIERS[tier]["price_pence"],
            "recurring": {"interval": "month"},
            "product_data": {"name": f"VoidMessage {tier.title()} — Hidden Messaging"},
        }

        cs = sc.checkout.Session.create(
            mode="subscription",
            line_items=[{"price_data": price_data, "quantity": 1}],
            success_url=f"{base_url}/voidmessage/checkout/success?pending={pending_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/voidmessage/subscribe",
            metadata={"tier": tier, "pending_id": pending_id},
        )
        return redirect(cs.url)

    except Exception as e:
        logger.error("[VoidMessage] Stripe checkout error: %s", e)
        return f"Payment setup failed: {e}", 500


@voidmessage_bp.route("/voidmessage/checkout/success")
def checkout_success():
    stripe_session_id = request.args.get("session_id", "")
    pending_id = request.args.get("pending", "")

    if not stripe_session_id:
        return redirect(url_for("voidmessage.index"))

    try:
        from routes.stripe_client import get_stripe_client
        sc = get_stripe_client()
        cs = sc.checkout.Session.retrieve(stripe_session_id)

        if cs.payment_status in ("paid", "no_payment_required"):
            tier = cs.metadata.get("tier", session.get("vm_pending_tier", "seed"))
            email = cs.customer_details.email if cs.customer_details else ""
            sub_key = secrets.token_hex(32)

            db = _get_db()
            db.execute("""
                INSERT INTO vm_subscriptions (id, stripe_customer_id, stripe_subscription_id, tier, email, sub_key, status, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                uuid.uuid4().hex,
                cs.customer or "",
                cs.subscription or "",
                tier,
                email,
                sub_key,
                "active",
                datetime.now(timezone.utc).isoformat()
            ))
            db.commit()
            db.close()

            session["vm_sub_key"] = sub_key
            session["vm_pending_checkout"] = None
            session["vm_pending_tier"] = None

            return render_template("voidmessage_success.html", tier=tier, email=email)

    except Exception as e:
        logger.error("[VoidMessage] Checkout success error: %s", e)

    return redirect(url_for("voidmessage.index"))
