"""
Sphere Key — Physical Key Cryptography
=======================================
Route: GET  /sphere-key                  — Instruction manual + decoder UI
Route: POST /api/sphere-key/derive       — Upload sphere photo → derive key
Route: POST /api/sphere-key/decode       — Upload sphere photo + audio → document
Route: GET  /api/sphere-key/frequency-key — Derive key from frequency alone
"""

import os
import io
import uuid
import logging
import tempfile

from flask import Blueprint, render_template, request, jsonify, session, send_file

logger = logging.getLogger(__name__)

sphere_key_bp = Blueprint("sphere_key", __name__)

_ALLOWED_IMG = {"png", "jpg", "jpeg", "webp"}
_ALLOWED_AUD = {"wav"}
_MAX_IMG_BYTES = 10 * 1024 * 1024   # 10 MB
_MAX_AUD_BYTES = 100 * 1024 * 1024  # 100 MB


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


# ── Pages ─────────────────────────────────────────────────────────────────────

@sphere_key_bp.route("/sphere-key")
def sphere_key_page():
    return render_template("sphere_key.html")


# ── API ───────────────────────────────────────────────────────────────────────

@sphere_key_bp.route("/api/sphere-key/derive", methods=["POST"])
def derive_key():
    """Upload a sphere photograph. Returns the Al-Jabr 286 key hex."""
    img_file = request.files.get("sphere_image")
    if not img_file or not img_file.filename:
        return jsonify({"error": "sphere_image file required"}), 400
    if _ext(img_file.filename) not in _ALLOWED_IMG:
        return jsonify({"error": "Image must be PNG, JPG, or WEBP"}), 400

    img_bytes = img_file.read(_MAX_IMG_BYTES + 1)
    if len(img_bytes) > _MAX_IMG_BYTES:
        return jsonify({"error": "Image too large (max 10 MB)"}), 413

    try:
        from void_engine.sphere_key import derive_key_from_image
        key_hex = derive_key_from_image(img_bytes)
        return jsonify({
            "key": key_hex,
            "bits": len(key_hex) * 4,
            "algorithm": "Al-Jabr 286",
            "protocol": "VOID-SPHERE-KEY-v1",
        })
    except Exception as exc:
        logger.error("Sphere key derivation failed: %s", exc)
        return jsonify({"error": "Key derivation failed — check image quality"}), 500


@sphere_key_bp.route("/api/sphere-key/decode", methods=["POST"])
def sphere_decode():
    """
    Upload sphere photograph + VoidEcho WAV file.
    Derives the key from the sphere, decodes the hidden document,
    and returns it as a file download.
    """
    img_file  = request.files.get("sphere_image")
    wav_file  = request.files.get("audio_file")

    if not img_file or not wav_file:
        return jsonify({"error": "sphere_image and audio_file required"}), 400
    if _ext(img_file.filename) not in _ALLOWED_IMG:
        return jsonify({"error": "Image must be PNG, JPG, or WEBP"}), 400
    if _ext(wav_file.filename) not in _ALLOWED_AUD:
        return jsonify({"error": "Audio must be WAV format"}), 400

    img_bytes = img_file.read(_MAX_IMG_BYTES + 1)
    if len(img_bytes) > _MAX_IMG_BYTES:
        return jsonify({"error": "Image too large (max 10 MB)"}), 413

    wav_bytes = wav_file.read(_MAX_AUD_BYTES + 1)
    if len(wav_bytes) > _MAX_AUD_BYTES:
        return jsonify({"error": "Audio too large (max 100 MB)"}), 413

    try:
        from void_engine.sphere_key import derive_key_from_image
        key_hex = derive_key_from_image(img_bytes)
    except Exception as exc:
        logger.error("Key derivation error: %s", exc)
        return jsonify({"error": "Could not read sphere image"}), 500

    # Write WAV to temp file for stega decoder
    tmp_dir = tempfile.mkdtemp(prefix="sphere_decode_")
    wav_path = os.path.join(tmp_dir, f"input_{uuid.uuid4().hex[:8]}.wav")
    with open(wav_path, "wb") as f:
        f.write(wav_bytes)

    try:
        from void_engine.stega import decode
        result = decode(carrier_path=wav_path, passphrase=key_hex)

        doc_bytes  = result.get("payload") or b""
        doc_name   = result.get("file_name", "recovered_document")
        doc_ext    = result.get("extension", ".txt")
        if not doc_ext.startswith("."):
            doc_ext = "." + doc_ext

        return send_file(
            io.BytesIO(doc_bytes),
            as_attachment=True,
            download_name=f"{doc_name}{doc_ext}",
            mimetype="application/octet-stream",
        )
    except Exception as exc:
        logger.error("Sphere decode error: %s", exc)
        return jsonify({
            "error": "Decoding failed — sphere photograph may not match the encoding sphere, "
                     "or the audio was not encoded with the Sphere Key Protocol."
        }), 422
    finally:
        try:
            os.remove(wav_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass


@sphere_key_bp.route("/api/sphere-key/encode", methods=["POST"])
def sphere_encode():
    """
    Upload sphere photograph + document + carrier WAV.
    Encodes the document into the audio using the sphere-derived key.
    Returns the VoidEcho WAV file.
    """
    img_file  = request.files.get("sphere_image")
    doc_file  = request.files.get("document")
    wav_file  = request.files.get("carrier_audio")

    if not img_file or not doc_file or not wav_file:
        return jsonify({"error": "sphere_image, document, and carrier_audio required"}), 400
    if _ext(img_file.filename) not in _ALLOWED_IMG:
        return jsonify({"error": "Image must be PNG, JPG, or WEBP"}), 400
    if _ext(wav_file.filename) not in _ALLOWED_AUD:
        return jsonify({"error": "Carrier audio must be WAV format"}), 400

    img_bytes = img_file.read(_MAX_IMG_BYTES + 1)
    if len(img_bytes) > _MAX_IMG_BYTES:
        return jsonify({"error": "Image too large (max 10 MB)"}), 413

    try:
        from void_engine.sphere_key import derive_key_from_image
        key_hex = derive_key_from_image(img_bytes)
    except Exception as exc:
        logger.error("Key derivation error: %s", exc)
        return jsonify({"error": "Could not read sphere image"}), 500

    tmp_dir  = tempfile.mkdtemp(prefix="sphere_encode_")
    wav_path = os.path.join(tmp_dir, f"carrier_{uuid.uuid4().hex[:8]}.wav")
    doc_path = os.path.join(tmp_dir, f"doc_{uuid.uuid4().hex[:8]}{os.path.splitext(doc_file.filename)[1]}")
    out_path = os.path.join(tmp_dir, f"voidecho_sphere_{uuid.uuid4().hex[:8]}.wav")

    try:
        with open(wav_path, "wb") as f:
            f.write(wav_file.read())
        with open(doc_path, "wb") as f:
            f.write(doc_file.read())

        from void_engine.stega import encode
        name_part, ext_part = os.path.splitext(doc_file.filename)
        encode(
            carrier_path=wav_path,
            payload=open(doc_path, "rb").read(),
            file_name=name_part,
            extension=ext_part,
            output_path=out_path,
            lsb_depth=1,
            passphrase=key_hex,
        )

        return send_file(
            out_path,
            as_attachment=True,
            download_name="voidecho_sphere_encoded.wav",
            mimetype="audio/wav",
        )
    except Exception as exc:
        logger.error("Sphere encode error: %s", exc)
        return jsonify({"error": f"Encoding failed: {exc}"}), 500
    finally:
        for p in [wav_path, doc_path]:
            try:
                os.remove(p)
            except Exception:
                pass


@sphere_key_bp.route("/api/sphere-key/frequency-key")
def frequency_key():
    """Derive a key from a frequency value alone (no sphere required)."""
    hz = request.args.get("hz", 432.0, type=float)
    sphere_id = request.args.get("id", "")
    from void_engine.sphere_key import derive_key_from_frequency
    key_hex = derive_key_from_frequency(hz=hz, sphere_id=sphere_id)
    return jsonify({
        "key": key_hex,
        "hz": hz,
        "algorithm": "Al-Jabr 286",
        "protocol": "VOID-FREQ-KEY-v1",
    })
