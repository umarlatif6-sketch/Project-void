"""
Manchester Gift — Five Element Gifts
=====================================
Route: GET /manchester-gift         — Gift overview page
Route: GET /api/manchester-gift/audio — Download the Formation Principle encoded WAV
"""

import io
import logging
from flask import Blueprint, render_template, send_file

logger = logging.getLogger(__name__)

manchester_gift_bp = Blueprint("manchester_gift", __name__)

_FORMATION_MESSAGE = (
    "THE FORMATION PRINCIPLE · 432 HZ · PROJECT VOID · 8 APRIL 2026 · "
    "ANY RESPONSIVE MATERIAL AT THE MOMENT OF FORMATION INHERITS THE GEOMETRY "
    "OF THE FREQUENCY PRESENT · THE FREQUENCY IS PRIOR · THE MATERIAL IS THE MEMORY · "
    "VOIDECHO · SPHERE KEY · PHYSICAL KEY CRYPTOGRAPHY · FOUNDED BY UMAR L"
)


@manchester_gift_bp.route("/manchester-gift")
def manchester_gift():
    return render_template("manchester_gift.html")


@manchester_gift_bp.route("/api/manchester-gift/audio")
def gift_audio():
    """Generate and return the Formation Principle encoded WAV."""
    try:
        from void_engine.audio_stega import encode_message
        wav_bytes = encode_message(_FORMATION_MESSAGE, method="spectrogram", duration=30.0)
        return send_file(
            io.BytesIO(wav_bytes),
            mimetype="audio/wav",
            as_attachment=True,
            download_name="formation_principle_432hz.wav"
        )
    except Exception as e:
        logger.exception("Gift audio generation failed")
        from flask import jsonify
        return jsonify({"error": str(e)}), 500
