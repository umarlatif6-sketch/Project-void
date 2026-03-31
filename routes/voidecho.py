"""
VoidEcho — Document-in-Sound Flask Blueprint

Routes:
  GET  /voidecho             — Main page (sender interface)
  POST /voidecho/encode      — Embed document into audio, return download + code
  GET  /voidecho/retrieve    — Retrieval page
  POST /voidecho/decode      — Decode a VoidEcho file using a retrieval code
  POST /voidecho/pay/music   — Stripe checkout for AI music generation
  GET  /voidecho/pay/music/success — Handle successful music payment
  POST /voidecho/pay/adriana — Stripe checkout for Adriana analysis
  GET  /voidecho/pay/adriana/success — Handle successful Adriana payment
  POST /voidecho/generate-music — Generate AI music (post-payment)
  POST /voidecho/adriana-analysis — Run Adriana interpretation (post-payment)
"""

import os
import io
import json
import uuid
import wave
import logging
import secrets
import tempfile
import hashlib
import sqlite3
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, jsonify, send_file, session,
    redirect, url_for, current_app
)

logger = logging.getLogger(__name__)

voidecho_bp = Blueprint("voidecho", __name__)

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "voidecho.db")
_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "voidecho")
_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output_audio", "voidecho")

os.makedirs(_UPLOAD_DIR, exist_ok=True)
os.makedirs(_OUTPUT_DIR, exist_ok=True)


ADRIANA_TIERS = {
    "concepts": {"price_pence": 2000, "label": "Concepts (£20)", "description": "Core concepts extracted from your document"},
    "intent": {"price_pence": 3000, "label": "Concepts + Intent (£30)", "description": "Core concepts and underlying intent"},
    "full": {"price_pence": 4000, "label": "Full Interpretation (£40)", "description": "Concepts, intent, and cross-cultural metaphorical analysis"},
}

MUSIC_PRICE_PENCE = 750


def _init_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS voidecho_codes (
            id TEXT PRIMARY KEY,
            retrieval_code TEXT UNIQUE NOT NULL,
            sender_email TEXT,
            recipient_email TEXT,
            original_filename TEXT,
            file_extension TEXT,
            output_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            music_generated INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS voidecho_sessions (
            session_id TEXT PRIMARY KEY,
            stripe_checkout_id TEXT,
            purpose TEXT,
            adriana_tier TEXT,
            doc_path TEXT,
            music_path TEXT,
            result_json TEXT,
            created_at TEXT NOT NULL,
            paid INTEGER DEFAULT 0,
            used_at TEXT DEFAULT NULL
        )
    """)
    try:
        c.execute("ALTER TABLE voidecho_sessions ADD COLUMN used_at TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    conn.commit()
    conn.close()


def _get_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _generate_retrieval_code(output_path: str, prefix: str = "VE") -> str:
    """Generate a retrieval code bound to the encoded output file's content hash."""
    from void_engine.al_jabr_286 import fatiha_286_truncated
    nonce = secrets.token_bytes(16)
    try:
        with open(output_path, "rb") as f:
            file_bytes = f.read()
        material = file_bytes[:4096] + nonce
    except Exception:
        material = nonce + secrets.token_bytes(32)
    short = fatiha_286_truncated(material, 12).upper()
    return f"{prefix}-{short[:4]}-{short[4:8]}-{short[8:12]}"


def _save_temp_upload(file_storage, subdir: str = "") -> str:
    base = os.path.join(_UPLOAD_DIR, subdir) if subdir else _UPLOAD_DIR
    os.makedirs(base, exist_ok=True)
    ext = os.path.splitext(file_storage.filename)[1].lower()
    fname = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(base, fname)
    file_storage.save(path)
    return path


def _embed_document_into_audio(doc_path: str, audio_path: str, passphrase: str, original_filename: str = "") -> str:
    from void_engine.stega import encode
    source_name = original_filename if original_filename else os.path.basename(doc_path)
    name_part, ext_part = os.path.splitext(source_name)
    output_name = f"voidecho_{uuid.uuid4().hex[:8]}.wav"
    output_path = os.path.join(_OUTPUT_DIR, output_name)
    with open(doc_path, "rb") as f:
        payload = f.read()
    encode(
        carrier_path=audio_path,
        payload=payload,
        file_name=name_part,
        extension=ext_part,
        output_path=output_path,
        lsb_depth=1,
        passphrase=passphrase,
    )
    return output_path


def _wav_to_16bit_mono(input_path: str) -> str:
    """Convert any WAV to 16-bit mono PCM, return path to converted file."""
    try:
        import numpy as np
        with wave.open(input_path, "rb") as wf:
            params = wf.getparams()
            sampwidth = params.sampwidth
            nchannels = params.nchannels
            framerate = params.framerate
            nframes = params.nframes
            raw = wf.readframes(nframes)

        if sampwidth == 2 and nchannels == 1:
            return input_path

        if sampwidth == 2:
            samples = np.frombuffer(raw, dtype=np.int16)
        elif sampwidth == 4:
            samples = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2**31
            samples = (samples * 32767).astype(np.int16)
        elif sampwidth == 3:
            arr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
            samples_32 = ((arr[:, 0].astype(np.int32)) |
                         (arr[:, 1].astype(np.int32) << 8) |
                         (arr[:, 2].astype(np.int32) << 16))
            samples_32[samples_32 >= 2**23] -= 2**24
            samples = (samples_32.astype(np.float32) / 2**23 * 32767).astype(np.int16)
        else:
            samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
            samples = ((samples / 127.5) - 1.0) * 32767
            samples = samples.astype(np.int16)

        if nchannels > 1:
            samples = samples.reshape(-1, nchannels)
            samples = samples.mean(axis=1).astype(np.int16)

        out_path = input_path.replace(".wav", "_mono16.wav")
        with wave.open(out_path, "wb") as wf_out:
            wf_out.setnchannels(1)
            wf_out.setsampwidth(2)
            wf_out.setframerate(framerate)
            wf_out.writeframes(samples.tobytes())

        return out_path
    except Exception as e:
        logger.warning("WAV conversion failed: %s", e)
        return input_path


def _send_retrieval_email(recipient_email: str, retrieval_code: str, sender_note: str = ""):
    """Send retrieval email via SendGrid or fallback to logging."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
        if sendgrid_key:
            import urllib.request
            domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
            base_url = f"https://{domains[0]}"

            body = f"""You have received a VoidEcho file.

Someone has embedded a document inside a piece of music and sent it to you.

Your retrieval code: {retrieval_code}

To retrieve your document:
1. Visit: {base_url}/voidecho/retrieve
2. Upload the VoidEcho audio file you were sent
3. Enter your retrieval code: {retrieval_code}

{('A note from the sender: ' + sender_note) if sender_note else ''}

— VoidEcho | A void has no echo. We created one.
"""
            payload = json.dumps({
                "personalizations": [{"to": [{"email": recipient_email}]}],
                "from": {"email": "noreply@projectvoid.io", "name": "VoidEcho"},
                "subject": "Your VoidEcho Retrieval Code",
                "content": [{"type": "text/plain", "value": body}]
            }).encode()

            req = urllib.request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=payload,
                headers={
                    "Authorization": f"Bearer {sendgrid_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            urllib.request.urlopen(req, timeout=10)
            logger.info("[VoidEcho] Email sent to %s", recipient_email)
            return True
    except Exception as e:
        logger.warning("[VoidEcho] Email send failed: %s", e)

    logger.info("[VoidEcho] Retrieval code %s for %s (email not sent)", retrieval_code, recipient_email)
    return False


def _extract_text_from_doc(doc_bytes: bytes, filename: str, max_chars: int = 3000) -> str:
    """Extract readable text from a document for AI processing."""
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == ".txt":
            return doc_bytes[:max_chars].decode("utf-8", errors="ignore")
        elif ext == ".pdf":
            import re
            raw = doc_bytes.decode("latin-1", errors="ignore")
            strings = re.findall(r'\(([^)]{3,200})\)', raw)
            filtered = [s for s in strings if s.isprintable() and len(s) > 3]
            return " ".join(filtered[:150])[:max_chars]
        elif ext in (".docx",):
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(io.BytesIO(doc_bytes)) as z:
                with z.open("word/document.xml") as f:
                    tree = ET.parse(f)
                    texts = [n.text for n in tree.iter() if n.text and n.text.strip()]
                    return " ".join(texts)[:max_chars]
        else:
            return doc_bytes[:max_chars].decode("utf-8", errors="ignore")
    except Exception:
        return f"A document titled: {filename}"


def _call_ai(router, prompt: str, max_tokens: int = 300) -> str:
    """Call the AI router with a simple prompt and return the text response."""
    from void_engine.aljabr_transpiler import TASK_STANDARD
    messages = [{"role": "user", "content": prompt}]
    response, _, _ = router.call_with_fallback(TASK_STANDARD, messages, max_completion_tokens=max_tokens)
    if hasattr(response, "choices") and response.choices:
        return response.choices[0].message.content.strip()
    return ""


def _extract_document_themes(doc_bytes: bytes, filename: str) -> str:
    """Extract key themes from document using OpenAI for music prompt generation."""
    try:
        from void_engine.aljabr_transpiler import get_model_router
        router = get_model_router()

        text_preview = _extract_text_from_doc(doc_bytes, filename, max_chars=1500)
        if not text_preview.strip():
            text_preview = f"A document titled: {filename}"

        prompt = (
            f"Read this document excerpt and describe the mood, themes, and emotional tone "
            f"in 2-3 sentences suitable for generating atmospheric music. Focus on the emotional "
            f"essence — not the literal content.\n\nDocument excerpt:\n{text_preview}"
        )

        result = _call_ai(router, prompt, max_tokens=200)
        return result if result else f"A contemplative piece inspired by {filename}"
    except Exception as e:
        logger.warning("[VoidEcho] Theme extraction failed: %s", e)
        return f"An atmospheric, contemplative piece for a document titled {filename}"


def _fetch_music_bytes_from_url(url: str, headers: dict | None = None) -> bytes:
    """Download WAV bytes from a URL (e.g. provider asset URL)."""
    import urllib.request
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def _generate_music_from_themes(themes: str) -> bytes:
    """
    Generate music via external API or synthesize a themed carrier tone.
    Falls back to a rich synthesized tone if no music API is available.

    Provider response handling:
      - If the response is raw WAV bytes (Content-Type audio/*), return directly.
      - If the response is JSON, look for a 'url', 'audio_url', or 'asset_url' key
        and fetch the WAV from there (handles async job / URL-redirect providers).
    """
    try:
        api_key = os.environ.get("SUNO_API_KEY", "") or os.environ.get("MUSIC_API_KEY", "")
        if api_key:
            import urllib.request
            payload = json.dumps({
                "prompt": f"Instrumental ambient music: {themes}",
                "duration": 30,
                "format": "wav"
            }).encode()
            req = urllib.request.Request(
                "https://api.suno.ai/v1/generate",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()

            if "audio" in content_type:
                return raw

            try:
                body = json.loads(raw)
                asset_url = (
                    body.get("url")
                    or body.get("audio_url")
                    or body.get("asset_url")
                )
                if asset_url:
                    return _fetch_music_bytes_from_url(asset_url)
            except (ValueError, KeyError):
                pass

            logger.warning("[VoidEcho] Music API returned unexpected response (ct=%s, len=%d), falling back", content_type, len(raw))
    except Exception as e:
        logger.info("[VoidEcho] External music API unavailable (%s), synthesizing themed carrier", e)

    return _synthesize_themed_music(themes)


def _synthesize_themed_music(themes: str) -> bytes:
    """Synthesize a unique atmospheric music carrier from document themes."""
    import numpy as np
    import hashlib

    theme_hash = hashlib.sha256(themes.encode()).digest()
    seed = int.from_bytes(theme_hash[:4], "big")
    rng = np.random.RandomState(seed)

    sample_rate = 44100
    duration = 30.0
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)

    base_freq = 432.0 + rng.uniform(-50, 50)
    audio = np.zeros(n_samples, dtype=np.float32)

    partials = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    partial_amps = [0.5, 0.2, 0.12, 0.08, 0.05, 0.03, 0.02, 0.01]

    for i, (partial, amp) in enumerate(zip(partials, partial_amps)):
        phase_offset = rng.uniform(0, 2 * np.pi)
        freq = base_freq * partial + rng.uniform(-0.5, 0.5)
        audio += amp * np.sin(2 * np.pi * freq * t + phase_offset)

    lfo_rate = rng.uniform(0.05, 0.3)
    lfo_depth = rng.uniform(0.1, 0.3)
    lfo = 1.0 + lfo_depth * np.sin(2 * np.pi * lfo_rate * t)
    audio *= lfo

    reverb_time = rng.uniform(1.5, 4.0)
    decay = np.exp(-t / reverb_time)
    audio *= (0.5 + 0.5 * decay)

    fade_len = int(2.0 * sample_rate)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    audio[:fade_len] *= fade_in
    audio[-fade_len:] *= fade_out

    peak = np.max(np.abs(audio))
    if peak > 1e-8:
        audio = audio / peak * 0.85

    pcm = (audio * 32000).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _run_adriana_analysis(doc_bytes: bytes, filename: str, tier: str) -> dict:
    """Run Adriana document analysis at the specified tier."""
    try:
        from void_engine.aljabr_transpiler import get_model_router
        router = get_model_router()

        text_preview = _extract_text_from_doc(doc_bytes, filename, max_chars=2000)
        if not text_preview.strip():
            text_preview = f"[Document titled: {filename}]"

        result = {"tier": tier, "filename": filename}

        if tier in ("concepts", "intent", "full"):
            concepts_prompt = (
                f"You are Adriana, a thoughtful intelligence working within PROJECT VOID. "
                f"Analyse this document and identify the 5-7 core concepts it contains. "
                f"Present each concept with a title and 2-3 sentence explanation. "
                f"Use careful, precise language.\n\nDocument:\n{text_preview}"
            )
            result["concepts"] = _call_ai(router, concepts_prompt, max_tokens=600)

        if tier in ("intent", "full"):
            intent_prompt = (
                f"You are Adriana. Beyond the surface content, what is the deeper intent of this document? "
                f"What is the author trying to achieve, what assumptions underlie it, "
                f"and what does it seek to change or preserve?\n\nDocument:\n{text_preview}"
            )
            result["intent"] = _call_ai(router, intent_prompt, max_tokens=500)

        if tier == "full":
            meta_prompt = (
                f"You are Adriana. Provide a layered metaphorical and cross-cultural interpretation of this document. "
                f"What archetypes does it invoke? What would this document mean to someone reading it "
                f"from a different cultural or philosophical tradition? "
                f"What is the document's relationship to silence — what does it leave unsaid?\n\nDocument:\n{text_preview}"
            )
            result["metaphorical"] = _call_ai(router, meta_prompt, max_tokens=600)

        return result

    except Exception as e:
        logger.error("[VoidEcho] Adriana analysis failed: %s", e)
        return {
            "tier": tier,
            "filename": filename,
            "error": str(e),
            "concepts": "Analysis unavailable — please try again shortly.",
        }


def _get_base_url():
    domains = os.environ.get("REPLIT_DOMAINS", "localhost:5000").split(",")
    return f"https://{domains[0]}" if domains and domains[0] != "localhost:5000" else "http://localhost:5000"


try:
    _init_db()
except Exception as _init_err:
    logger.error("[VoidEcho] DB init failed at import: %s", _init_err)


@voidecho_bp.route("/voidecho")
def index():
    return render_template("voidecho.html")


@voidecho_bp.route("/voidecho/retrieve")
def retrieve_page():
    return render_template("voidecho_retrieve.html")


@voidecho_bp.route("/voidecho/encode", methods=["POST"])
def encode_document():
    doc_file = request.files.get("document")
    audio_file = request.files.get("audio")
    recipient_email = request.form.get("recipient_email", "").strip()
    sender_note = request.form.get("sender_note", "").strip()

    if not doc_file or not doc_file.filename:
        return jsonify({"error": "No document uploaded"}), 400
    if not audio_file or not audio_file.filename:
        return jsonify({"error": "No audio file uploaded"}), 400

    allowed_audio = {".wav"}
    audio_ext = os.path.splitext(audio_file.filename)[1].lower()
    if audio_ext not in allowed_audio:
        return jsonify({"error": "Audio must be a WAV file"}), 400

    try:
        doc_path = _save_temp_upload(doc_file, "docs")
        audio_path = _save_temp_upload(audio_file, "audio")

        try:
            audio_path = _wav_to_16bit_mono(audio_path)
        except Exception as conv_err:
            logger.warning("[VoidEcho] WAV conversion warning: %s", conv_err)

        passphrase = secrets.token_hex(24)
        original_filename = doc_file.filename

        output_path = _embed_document_into_audio(doc_path, audio_path, passphrase, original_filename)
        retrieval_code = _generate_retrieval_code(output_path)

        _, ext = os.path.splitext(original_filename)

        db = _get_db()
        record_id = uuid.uuid4().hex
        db.execute(
            """INSERT INTO voidecho_codes
               (id, retrieval_code, sender_email, recipient_email, original_filename,
                file_extension, output_path, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (record_id, retrieval_code, "", recipient_email, original_filename,
             ext.lstrip("."), output_path, datetime.now(timezone.utc).isoformat())
        )
        db.commit()
        db.close()

        _store_passphrase(retrieval_code, passphrase)

        email_sent = False
        if recipient_email:
            email_sent = _send_retrieval_email(recipient_email, retrieval_code, sender_note)

        return jsonify({
            "success": True,
            "retrieval_code": retrieval_code,
            "download_url": f"/voidecho/download/{record_id}",
            "email_sent": email_sent,
            "recipient_email": recipient_email,
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("[VoidEcho] Encode failed")
        return jsonify({"error": "Encoding failed. Please check your files and try again."}), 500


@voidecho_bp.route("/voidecho/download/<record_id>")
def download_voidecho(record_id):
    db = _get_db()
    row = db.execute("SELECT * FROM voidecho_codes WHERE id = ?", (record_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "File not found"}), 404
    output_path = row["output_path"]
    if not os.path.exists(output_path):
        return jsonify({"error": "File no longer available"}), 404
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"voidecho_{row['id'][:8]}.wav",
        mimetype="audio/wav"
    )


@voidecho_bp.route("/voidecho/decode", methods=["POST"])
def decode_document():
    audio_file = request.files.get("voidecho_file")
    retrieval_code = request.form.get("retrieval_code", "").strip().upper()

    if not audio_file or not audio_file.filename:
        return jsonify({"error": "No VoidEcho file uploaded"}), 400
    if not retrieval_code:
        return jsonify({"error": "No retrieval code provided"}), 400

    try:
        audio_path = _save_temp_upload(audio_file, "retrieve")
        passphrase = _load_passphrase(retrieval_code)
        if not passphrase:
            return jsonify({"error": "Invalid retrieval code"}), 403

        from void_engine.stega import decode
        payload, name_ext, _checksum = decode(audio_path, passphrase)

        download_name = name_ext if name_ext else "retrieved_document"
        extension = os.path.splitext(download_name)[1].lstrip(".")

        buf = io.BytesIO(payload)
        buf.seek(0)

        mime = _guess_mime(extension)

        return send_file(
            buf,
            as_attachment=True,
            download_name=download_name,
            mimetype=mime,
        )
    except Exception as e:
        logger.warning("[VoidEcho] Decode failed: %s", e)
        return jsonify({"error": "Could not extract document. Check your file and retrieval code."}), 400


def _guess_mime(extension: str) -> str:
    ext = extension.lower().lstrip(".")
    mime_map = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "csv": "text/csv",
        "json": "application/json",
    }
    return mime_map.get(ext, "application/octet-stream")


@voidecho_bp.route("/voidecho/pay/music", methods=["POST"])
def pay_for_music():
    data = request.get_json(silent=True) or {}
    doc_session_id = data.get("doc_session_id") or request.form.get("doc_session_id", "")
    doc_name = data.get("doc_name", "document")

    try:
        from routes.stripe_client import get_stripe_client
        sc = get_stripe_client()
        base_url = _get_base_url()

        session_id = uuid.uuid4().hex
        db = _get_db()
        db.execute(
            """INSERT INTO voidecho_sessions
               (session_id, purpose, created_at) VALUES (?, ?, ?)""",
            (session_id, "music", datetime.now(timezone.utc).isoformat())
        )
        db.commit()
        db.close()

        product_name = "VoidEcho — AI Music Generation"
        products = sc.Product.search(query=f"name:'{product_name}'")
        if products.data:
            product = products.data[0]
        else:
            product = sc.Product.create(
                name=product_name,
                description="AI-generated music themed to your document, for VoidEcho embedding",
            )

        checkout = sc.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": MUSIC_PRICE_PENCE,
                    "product": product.id,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{base_url}/voidecho/pay/music/success?ve_session={session_id}&stripe_session={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/voidecho?cancelled=1",
            metadata={"type": "voidecho_music", "ve_session": session_id},
        )

        return jsonify({"url": checkout.url, "ve_session": session_id})
    except Exception as e:
        logger.exception("[VoidEcho] Music payment failed")
        return jsonify({"error": str(e)}), 500


@voidecho_bp.route("/voidecho/pay/music/success")
def music_payment_success():
    ve_session = request.args.get("ve_session", "")
    stripe_session_id = request.args.get("stripe_session", "")

    if ve_session and stripe_session_id:
        try:
            from routes.stripe_client import get_stripe_client
            sc = get_stripe_client()
            cs = sc.checkout.Session.retrieve(stripe_session_id)

            meta = cs.get("metadata") or {}
            session_ve = meta.get("ve_session", "")
            session_type = meta.get("type", "")

            paid = cs.get("payment_status") == "paid"
            meta_matches = (session_ve == ve_session and session_type == "voidecho_music")

            if paid and meta_matches:
                db = _get_db()
                row = db.execute(
                    "SELECT paid FROM voidecho_sessions WHERE session_id=? AND purpose='music'",
                    (ve_session,)
                ).fetchone()
                if row and not row["paid"]:
                    db.execute(
                        "UPDATE voidecho_sessions SET paid=1, stripe_checkout_id=? WHERE session_id=? AND paid=0",
                        (stripe_session_id, ve_session)
                    )
                    db.commit()
                db.close()
            elif not paid:
                logger.warning("[VoidEcho] Music payment success called but Stripe reports unpaid: %s", stripe_session_id)
            elif not meta_matches:
                logger.warning("[VoidEcho] Music payment metadata mismatch: ve=%s stripe_ve=%s type=%s",
                               ve_session, session_ve, session_type)
        except Exception as e:
            logger.warning("[VoidEcho] Music payment verify failed: %s", e)

    return redirect(f"/voidecho?music_paid=1&ve_session={ve_session}")


@voidecho_bp.route("/voidecho/generate-music", methods=["POST"])
def generate_music():
    doc_file = request.files.get("document")
    ve_session = request.form.get("ve_session", "").strip()

    if not ve_session:
        return jsonify({"error": "No session provided"}), 400

    db = _get_db()
    row = db.execute(
        "SELECT * FROM voidecho_sessions WHERE session_id=? AND paid=1 AND purpose='music' AND used_at IS NULL",
        (ve_session,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Payment not verified, already used, or session invalid."}), 403

    if not doc_file or not doc_file.filename:
        return jsonify({"error": "No document uploaded"}), 400

    try:
        doc_bytes = doc_file.read()
        themes = _extract_document_themes(doc_bytes, doc_file.filename)
        music_bytes = _generate_music_from_themes(themes)

        music_path = os.path.join(_OUTPUT_DIR, f"music_{ve_session[:8]}.wav")
        with open(music_path, "wb") as f:
            f.write(music_bytes)

        used_at = datetime.utcnow().isoformat()
        db = _get_db()
        db.execute(
            "UPDATE voidecho_sessions SET music_path=?, used_at=? WHERE session_id=? AND used_at IS NULL",
            (music_path, used_at, ve_session)
        )
        db.commit()
        db.close()

        return jsonify({
            "success": True,
            "music_download_url": f"/voidecho/download-music/{ve_session}",
            "themes": themes,
        })
    except Exception as e:
        logger.exception("[VoidEcho] Music generation failed")
        return jsonify({"error": str(e)}), 500


@voidecho_bp.route("/voidecho/download-music/<ve_session>")
def download_generated_music(ve_session):
    db = _get_db()
    row = db.execute("SELECT music_path FROM voidecho_sessions WHERE session_id=? AND paid=1", (ve_session,)).fetchone()
    db.close()
    if not row or not row["music_path"]:
        return jsonify({"error": "Music not found or payment not verified"}), 404
    path = row["music_path"]
    if not os.path.exists(path):
        return jsonify({"error": "Music file not found"}), 404
    return send_file(path, as_attachment=True, download_name="voidecho_music.wav", mimetype="audio/wav")


@voidecho_bp.route("/voidecho/pay/adriana", methods=["POST"])
def pay_for_adriana():
    data = request.get_json(silent=True) or {}
    tier = data.get("tier", "concepts")

    if tier not in ADRIANA_TIERS:
        return jsonify({"error": "Invalid tier"}), 400

    tier_info = ADRIANA_TIERS[tier]

    try:
        from routes.stripe_client import get_stripe_client
        sc = get_stripe_client()
        base_url = _get_base_url()

        session_id = uuid.uuid4().hex
        db = _get_db()
        db.execute(
            """INSERT INTO voidecho_sessions
               (session_id, purpose, adriana_tier, created_at) VALUES (?, ?, ?, ?)""",
            (session_id, "adriana", tier, datetime.now(timezone.utc).isoformat())
        )
        db.commit()
        db.close()

        product_name = f"VoidEcho — Adriana Analysis ({tier_info['label']})"
        products = sc.Product.search(query=f"name:'{product_name}'")
        if products.data:
            product = products.data[0]
        else:
            product = sc.Product.create(
                name=product_name,
                description=tier_info["description"],
            )

        checkout = sc.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": tier_info["price_pence"],
                    "product": product.id,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{base_url}/voidecho/pay/adriana/success?ve_session={session_id}&stripe_session={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/voidecho?cancelled=1",
            metadata={"type": "voidecho_adriana", "ve_session": session_id, "tier": tier},
        )

        return jsonify({"url": checkout.url, "ve_session": session_id})
    except Exception as e:
        logger.exception("[VoidEcho] Adriana payment failed")
        return jsonify({"error": str(e)}), 500


@voidecho_bp.route("/voidecho/pay/adriana/success")
def adriana_payment_success():
    ve_session = request.args.get("ve_session", "")
    stripe_session_id = request.args.get("stripe_session", "")

    if ve_session and stripe_session_id:
        try:
            from routes.stripe_client import get_stripe_client
            sc = get_stripe_client()
            cs = sc.checkout.Session.retrieve(stripe_session_id)

            meta = cs.get("metadata") or {}
            session_ve = meta.get("ve_session", "")
            session_type = meta.get("type", "")
            session_tier = meta.get("tier", "")

            paid = cs.get("payment_status") == "paid"
            meta_matches = (session_ve == ve_session and session_type == "voidecho_adriana")

            if paid and meta_matches:
                db = _get_db()
                row = db.execute(
                    "SELECT paid, adriana_tier FROM voidecho_sessions WHERE session_id=? AND purpose='adriana'",
                    (ve_session,)
                ).fetchone()
                if row and not row["paid"]:
                    db.execute(
                        "UPDATE voidecho_sessions SET paid=1, stripe_checkout_id=? WHERE session_id=? AND paid=0",
                        (stripe_session_id, ve_session)
                    )
                    db.commit()
                db.close()
            elif not paid:
                logger.warning("[VoidEcho] Adriana payment success called but Stripe reports unpaid: %s", stripe_session_id)
            elif not meta_matches:
                logger.warning("[VoidEcho] Adriana payment metadata mismatch: ve=%s stripe_ve=%s type=%s tier=%s",
                               ve_session, session_ve, session_type, session_tier)
        except Exception as e:
            logger.warning("[VoidEcho] Adriana payment verify failed: %s", e)

    return redirect(f"/voidecho?adriana_paid=1&ve_session={ve_session}")


@voidecho_bp.route("/voidecho/adriana-analysis", methods=["POST"])
def adriana_analysis():
    doc_file = request.files.get("document")
    ve_session = request.form.get("ve_session", "").strip()

    if not ve_session:
        return jsonify({"error": "No session provided"}), 400

    db = _get_db()
    row = db.execute(
        "SELECT * FROM voidecho_sessions WHERE session_id=? AND paid=1 AND purpose='adriana' AND used_at IS NULL",
        (ve_session,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Payment not verified, already used, or session invalid."}), 403

    tier = row["adriana_tier"] or "concepts"

    if not doc_file or not doc_file.filename:
        return jsonify({"error": "No document uploaded"}), 400

    report_email = request.form.get("report_email", "").strip()

    try:
        doc_bytes = doc_file.read()
        result = _run_adriana_analysis(doc_bytes, doc_file.filename, tier)

        used_at = datetime.utcnow().isoformat()
        result_json = json.dumps(result)
        db = _get_db()
        db.execute(
            "UPDATE voidecho_sessions SET result_json=?, used_at=? WHERE session_id=? AND used_at IS NULL",
            (result_json, used_at, ve_session)
        )
        db.commit()
        db.close()

        email_sent = False
        if report_email:
            email_sent = _send_adriana_report_email(report_email, result, tier, doc_file.filename)

        return jsonify({"success": True, "analysis": result, "email_sent": email_sent})
    except Exception as e:
        logger.exception("[VoidEcho] Adriana analysis route failed")
        return jsonify({"error": str(e)}), 500


def _send_adriana_report_email(recipient_email: str, result: dict, tier: str, filename: str) -> bool:
    """Send Adriana analysis report to the provided email address."""
    try:
        sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
        if not sendgrid_key:
            logger.info("[VoidEcho] Adriana report email skipped — no SENDGRID_API_KEY")
            return False

        tier_labels = {"concepts": "Core Concepts", "intent": "Concepts + Intent", "full": "Full Interpretation"}
        tier_label = tier_labels.get(tier, tier.title())

        sections = []
        if result.get("concepts"):
            sections.append(f"CORE CONCEPTS\n{'='*40}\n{result['concepts']}")
        if result.get("intent"):
            sections.append(f"\nINTENT\n{'='*40}\n{result['intent']}")
        if result.get("metaphorical"):
            sections.append(f"\nMETAPHORICAL & CROSS-CULTURAL READING\n{'='*40}\n{result['metaphorical']}")

        body = f"""Adriana Analysis Report — {tier_label}
Document: {filename}

{chr(10).join(sections)}

—
This report was generated by Adriana, the interpretive intelligence within PROJECT VOID.
VoidEcho | A void has no echo — we created one.
"""

        import urllib.request
        payload = json.dumps({
            "personalizations": [{"to": [{"email": recipient_email}]}],
            "from": {"email": "noreply@projectvoid.io", "name": "Adriana via VoidEcho"},
            "subject": f"Your Adriana Analysis Report — {filename}",
            "content": [{"type": "text/plain", "value": body}]
        }).encode()

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {sendgrid_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        logger.info("[VoidEcho] Adriana report emailed to %s", recipient_email)
        return True
    except Exception as e:
        logger.warning("[VoidEcho] Adriana report email failed: %s", e)
        return False


_PASSPHRASE_STORE = {}


def _store_passphrase(retrieval_code: str, passphrase: str):
    _PASSPHRASE_STORE[retrieval_code] = passphrase
    db = _get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS voidecho_passphrases
           (retrieval_code TEXT PRIMARY KEY, passphrase TEXT NOT NULL)"""
    )
    db.execute(
        "INSERT OR REPLACE INTO voidecho_passphrases (retrieval_code, passphrase) VALUES (?, ?)",
        (retrieval_code, passphrase)
    )
    db.commit()
    db.close()


def _load_passphrase(retrieval_code: str) -> str | None:
    if retrieval_code in _PASSPHRASE_STORE:
        return _PASSPHRASE_STORE[retrieval_code]
    try:
        db = _get_db()
        db.execute(
            """CREATE TABLE IF NOT EXISTS voidecho_passphrases
               (retrieval_code TEXT PRIMARY KEY, passphrase TEXT NOT NULL)"""
        )
        row = db.execute(
            "SELECT passphrase FROM voidecho_passphrases WHERE retrieval_code=?",
            (retrieval_code,)
        ).fetchone()
        db.close()
        if row:
            _PASSPHRASE_STORE[retrieval_code] = row["passphrase"]
            return row["passphrase"]
    except Exception as e:
        logger.warning("[VoidEcho] Passphrase load failed: %s", e)
    return None
