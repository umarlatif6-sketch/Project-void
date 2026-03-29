"""
Prior Art Defensive Publications
==================================
Public, no-login-required pages that establish defensive publication records
for PROJECT VOID inventions.

Routes:
  /prior-art            — index listing both disclosures
  /prior-art/vtb        — Vibe-Triggered Biomineralization (VTB) protocol
  /prior-art/432-vortex — 432 Hz Vortex Encoding
"""

import logging
from flask import Blueprint, render_template

logger = logging.getLogger(__name__)
prior_art_bp = Blueprint("prior_art", __name__)

PUBLICATION_DATE = "29 March 2026"
PUBLICATION_DATE_ISO = "2026-03-29"
INVENTOR = "Umar"
SITE_URL = "https://project-void.replit.app"

WAYBACK_VTB = "https://web.archive.org/save/https://project-void.replit.app/prior-art/vtb"
WAYBACK_432 = "https://web.archive.org/save/https://project-void.replit.app/prior-art/432-vortex"

HASH_PLACEHOLDER_VTB = "VTB-PAD-2026-[PENDING-BLOCKCHAIN-TIMESTAMP]"
HASH_PLACEHOLDER_432 = "432V-PAD-2026-[PENDING-BLOCKCHAIN-TIMESTAMP]"


@prior_art_bp.route("/prior-art")
def prior_art_index():
    return render_template(
        "prior_art_index.html",
        publication_date=PUBLICATION_DATE,
        inventor=INVENTOR,
        site_url=SITE_URL,
    )


@prior_art_bp.route("/prior-art/vtb")
def prior_art_vtb():
    return render_template(
        "prior_art_vtb.html",
        publication_date=PUBLICATION_DATE,
        publication_date_iso=PUBLICATION_DATE_ISO,
        inventor=INVENTOR,
        site_url=SITE_URL,
        wayback_url=WAYBACK_VTB,
        hash_placeholder=HASH_PLACEHOLDER_VTB,
    )


@prior_art_bp.route("/prior-art/432-vortex")
def prior_art_432_vortex():
    return render_template(
        "prior_art_432vortex.html",
        publication_date=PUBLICATION_DATE,
        publication_date_iso=PUBLICATION_DATE_ISO,
        inventor=INVENTOR,
        site_url=SITE_URL,
        wayback_url=WAYBACK_432,
        hash_placeholder=HASH_PLACEHOLDER_432,
    )
