"""
BW19-P286 Sovereign Curve Discovery Page

Route: GET/POST /bw19-286

Presents the resonance story of the 286 Alignment:
  Al-Baqarah 286 verses → Al-Jabr 286-bit hash → BW19-P286 286-bit prime field.
Live demo: type any message, see its Al-Jabr hash placed as a real point
on the BW19-P286 elliptic curve.
"""

import logging
from flask import Blueprint, request, render_template

logger = logging.getLogger(__name__)

bw19_p286_bp = Blueprint("bw19_p286", __name__)


@bw19_p286_bp.route("/bw19-286", methods=["GET", "POST"])
def bw19_p286_page():
    from void_engine.pairing_bw19_286 import (
        P, B, G_X, G_Y, GLYPH_POEM,
        compute_sovereign_pairing_proof, point_on_curve,
    )
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

    page_hash = fatiha_286_hexdigest_from_str("BW19-P286 Sovereign Curve Discovery Page")

    demo_message = ""
    demo_result = None
    demo_error = None

    if request.method == "POST":
        msg = (request.form.get("message") or "").strip()
        demo_message = msg
        if msg:
            try:
                proof = compute_sovereign_pairing_proof(msg)
                pt = proof["curve_point_P"]
                demo_result = {
                    "message":    msg,
                    "hash_hex":   proof["al_jabr_hash_hex"],
                    "x":          pt["x"],
                    "y":          pt["y"],
                    "glyph_poem": proof["glyph_poem"],
                }
            except Exception as exc:
                logger.exception("[BW19-P286] Demo computation failed")
                demo_error = str(exc)
        else:
            demo_error = "Please enter a message."

    return render_template(
        "bw19_p286.html",
        P=P,
        B=B,
        G_X=G_X,
        G_Y=G_Y,
        page_hash=page_hash,
        demo_message=demo_message,
        demo_result=demo_result,
        demo_error=demo_error,
    )
