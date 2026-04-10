"""
Chronicle Seed — Admin page and seed loader endpoint.

Routes:
  GET  /admin/chronicle-seed              Admin seed generator page (admin_required)
  POST /admin/chronicle-seed              Trigger seed generation (admin_required)
  GET  /admin/chronicle-seed/download/wav Download seed WAV (admin_required)
  GET  /admin/chronicle-seed/download/png Download Chladni PNG (admin_required)
  POST /seed/load                         Upload WAV/PNG, extract codon chain, return context summary
                                          NOTE: WAV extraction requires passphrase; PNG extraction reads
                                          embedded tEXt metadata from the uploaded file itself.
                                          No server-side codon chain is ever returned unauthenticated.
"""

import io
import json
import logging
import os
import time

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
)
from routes.auth import admin_required

logger = logging.getLogger(__name__)

chronicle_seed_bp = Blueprint("chronicle_seed", __name__)

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seeds")
SEED_WAV_FILENAME = "chronicle_seed.wav"
SEED_PNG_FILENAME = "chronicle_seed_chladni.png"
SEED_META_FILENAME = "chronicle_seed_meta.json"

CARRIER_WAV = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "input_files",
    "carrier_drone_1min.wav",
)

SEED_PASSPHRASE = os.environ.get("VOID_SEED_PASSPHRASE", "void-seed-432")


def _seed_wav_path() -> str:
    os.makedirs(SEED_DIR, exist_ok=True)
    return os.path.join(SEED_DIR, SEED_WAV_FILENAME)


def _seed_png_path() -> str:
    os.makedirs(SEED_DIR, exist_ok=True)
    return os.path.join(SEED_DIR, SEED_PNG_FILENAME)


def _seed_meta_path() -> str:
    os.makedirs(SEED_DIR, exist_ok=True)
    return os.path.join(SEED_DIR, SEED_META_FILENAME)


def _load_seed_meta() -> dict | None:
    meta_path = _seed_meta_path()
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_seed_meta(meta: dict):
    with open(_seed_meta_path(), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)



def _do_generate_seed() -> dict:
    """
    Full pipeline:
      1. Build codon chain from chronicles (DB + VOID_CHRONICLE.md via distillation)
      2. Encode into carrier WAV (LSB depth 2, max capacity mode)
      3. Render Chladni PNG from seed WAV, embedding codon chain in PNG tEXt metadata
      4. Save lightweight metadata (stats only, NOT the codon chain)
      5. Return stats dict
    """
    from void_engine.chronicle_seed import generate_chronicle_seed
    from void_engine.stega import encode_seed, get_seed_wav_capacity
    from void_engine.chladni_render import render_chladni_png

    seed_data = generate_chronicle_seed()
    codon_chain = seed_data["codon_chain"]
    seed_header = seed_data["seed_header"]

    if not os.path.exists(CARRIER_WAV):
        carrier_candidates = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "input_files", f)
            for f in ["ambient_drone_60s.wav", "carrier_drone_1min.wav", "test_carrier.wav"]
        ]
        carrier = None
        for c in carrier_candidates:
            if os.path.exists(c):
                carrier = c
                break
        if not carrier:
            raise FileNotFoundError(
                "No carrier WAV found. Expected carrier_drone_1min.wav in input_files/."
            )
    else:
        carrier = CARRIER_WAV

    capacity_info = get_seed_wav_capacity(carrier, lsb_depth=2)
    bytes_available = capacity_info["bytes_available"]

    wav_out = _seed_wav_path()
    encode_result = encode_seed(
        carrier_path=carrier,
        codon_chain=codon_chain,
        output_path=wav_out,
        passphrase=SEED_PASSPHRASE,
        lsb_depth=2,
    )

    png_out = _seed_png_path()
    render_chladni_png(
        wav_path=wav_out,
        output_path=png_out,
        size=512,
        codon_chain=codon_chain,
    )

    seed_header_tokens = seed_data.get("seed_header_tokens", max(1, len(seed_header) // 4))

    meta = {
        "timestamp": seed_data["timestamp"],
        "original_size_bytes": seed_data["original_size_bytes"],
        "codon_chain_length": seed_data["codon_chain_length"],
        "entry_count": seed_data["entry_count"],
        "md_codon_count": seed_data.get("md_codon_count", 0),
        "codon_count": len(seed_data["codons"]),
        "bytes_used": encode_result["bytes_used"],
        "bytes_available": bytes_available,
        "capacity_pct": encode_result["capacity_pct"],
        "seed_header_tokens": seed_header_tokens,
        "seed_header": seed_header,
        "sqlite_entry_count": seed_data.get("sqlite_entry_count", 0),
        "carrier_wav": carrier,
    }
    _save_seed_meta(meta)
    return meta


@chronicle_seed_bp.route("/admin/chronicle-seed", methods=["GET"])
@admin_required
def admin_chronicle_seed_get():
    meta = _load_seed_meta()
    wav_exists = os.path.exists(_seed_wav_path())
    png_exists = os.path.exists(_seed_png_path())
    error = request.args.get("error")
    generated = request.args.get("generated")
    return render_template(
        "admin_chronicle_seed.html",
        meta=meta,
        wav_exists=wav_exists,
        png_exists=png_exists,
        error=error,
        generated=generated,
    )


@chronicle_seed_bp.route("/admin/chronicle-seed", methods=["POST"])
@admin_required
def admin_chronicle_seed_post():
    try:
        _do_generate_seed()
        return redirect("/admin/chronicle-seed?generated=1")
    except Exception as e:
        logger.error("Chronicle seed generation error: %s", e, exc_info=True)
        err_msg = str(e)[:80].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return redirect(f"/admin/chronicle-seed?error={err_msg}")


@chronicle_seed_bp.route("/admin/chronicle-seed/download/wav", methods=["GET"])
@admin_required
def admin_chronicle_seed_download_wav():
    wav_path = _seed_wav_path()
    if not os.path.exists(wav_path):
        return jsonify({"error": "Seed WAV not yet generated"}), 404
    return send_file(
        wav_path,
        mimetype="audio/wav",
        as_attachment=True,
        download_name="chronicle_seed.wav",
    )


@chronicle_seed_bp.route("/admin/chronicle-seed/download/png", methods=["GET"])
@admin_required
def admin_chronicle_seed_download_png():
    png_path = _seed_png_path()
    if not os.path.exists(png_path):
        return jsonify({"error": "Chladni PNG not yet generated"}), 404
    return send_file(
        png_path,
        mimetype="image/png",
        as_attachment=True,
        download_name="chronicle_seed_chladni.png",
    )


@chronicle_seed_bp.route("/seed/load", methods=["POST"])
def seed_load():
    """
    Accept a WAV or PNG upload, extract the codon chain, expand it, and
    return a plain-text context summary suitable for pasting into a new AI chat.

    For WAV: decode LSB-encoded codon chain using the standard passphrase embedded
             in the WAV itself at encoding time.
    For PNG: read the codon chain from the PNG's embedded tEXt metadata chunk
             (key: "VoidSeedChain"). The codon chain is NOT read from server-side
             state — it must be present in the uploaded file.

    This endpoint does NOT expose any server-side codon chain or project context
    to callers who do not upload a valid seed file containing it.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send multipart/form-data with field 'file'."}), 400

    f = request.files["file"]
    filename = (f.filename or "").lower().strip()

    codon_chain = None

    if filename.endswith(".wav"):
        try:
            tmp_path = os.path.join(SEED_DIR, f"upload_{int(time.time())}.wav")
            os.makedirs(SEED_DIR, exist_ok=True)
            f.save(tmp_path)
            try:
                from void_engine.stega import decode_seed
                codon_chain = decode_seed(tmp_path, passphrase=SEED_PASSPHRASE, lsb_depth=2)
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.error("Seed WAV decode error: %s", e)
            return jsonify({"error": f"WAV decode failed: {str(e)[:200]}"}), 422

    elif filename.endswith(".png"):
        try:
            png_bytes = f.read()
        except Exception as e:
            return jsonify({"error": f"Failed to read uploaded PNG: {str(e)[:100]}"}), 400

        from void_engine.chladni_render import extract_codon_chain_from_png
        codon_chain = extract_codon_chain_from_png(png_bytes)

        if not codon_chain:
            return jsonify({
                "error": (
                    "This PNG does not contain an embedded codon chain. "
                    "Only Chronicle Seed PNGs generated by this platform are supported. "
                    "Re-generate the seed or upload the WAV file instead."
                )
            }), 422
    else:
        return jsonify({"error": "Unsupported file type. Upload a .wav or .png seed file."}), 400

    try:
        from void_engine.chronicle_seed import expand_codon_chain
        context_summary = expand_codon_chain(codon_chain)
    except Exception as e:
        logger.error("Codon expansion error: %s", e)
        context_summary = f"VOID SEED CHAIN:\n{codon_chain}"

    return jsonify({
        "ok": True,
        "context_summary": context_summary,
        "token_estimate": max(1, len(context_summary) // 4),
    })
