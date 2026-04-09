"""
VOID Stall — /void-stall
=========================
Mobile-optimized no-login landing page for the Manchester Tech Week stall.
Visitors scan a QR code at the physical bubble demonstration and arrive here.

Shows: λ·Λ·☀ codon (432 Hz — VoidEcho zone), Formation Principle statement,
pre-written Adriana codon-first reflection, WAV download, and navigation links.

No authentication required. Static content — no live API calls needed.
"""

from flask import Blueprint, render_template

void_stall_bp = Blueprint("void_stall", __name__)


@void_stall_bp.route("/void-stall")
def void_stall():
    from void_engine.void_codon_vocab import freq_to_codon
    zone = freq_to_codon(432)
    return render_template("void_stall.html", zone=zone)
