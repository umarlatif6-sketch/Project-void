"""
VOID Frequency Map — /freq-map
Single-surface platform navigation by frequency resonance.
No menus. No tabs. Codon labels only. Hover to expand. Click to navigate.
"""

import logging
from flask import Blueprint, render_template

logger = logging.getLogger(__name__)

freq_map_bp = Blueprint("freq_map", __name__)


@freq_map_bp.route("/freq-map")
def frequency_map():
    from void_engine.void_codon_vocab import PLATFORM_CODONS, get_by_band
    return render_template(
        "freq_map.html",
        all_zones=PLATFORM_CODONS,
        low_band=get_by_band("low"),
        mid_band=get_by_band("mid"),
        high_band=get_by_band("high"),
    )


@freq_map_bp.route("/api/freq-map/codons")
def freq_map_api():
    from flask import jsonify
    from void_engine.void_codon_vocab import PLATFORM_CODONS
    return jsonify({"ok": True, "zones": PLATFORM_CODONS})
