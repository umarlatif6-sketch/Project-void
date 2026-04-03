"""
Sovereign Manifesto — 18 Social Advantages + VoidEcho Export

Routes:
  GET  /sovereign-manifesto         — Manifesto page (18 Social Advantages)
  POST /sovereign-manifesto/export  — Hex-encode manifesto + generate 432 Hz WAV
"""

import io
import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, send_file, jsonify, session

logger = logging.getLogger(__name__)

sovereign_manifesto_bp = Blueprint("sovereign_manifesto", __name__)

SOCIAL_ADVANTAGES = [
    {
        "number": 1,
        "name": "Proof of Life",
        "module": "Al-Jabr 286 / Biological",
        "description": (
            "Every sovereign node generates a unique 286-bit proof anchored to biometric "
            "resonance, confirming presence without requiring a third-party identity authority. "
            "Your existence is your credential."
        ),
    },
    {
        "number": 2,
        "name": "Unhackable Secret",
        "module": "Lead Shield / Stega",
        "description": (
            "The Lead Shield encrypts Master Logic fields with a founder-held QiSync key "
            "before any hex entry is written. The public sees only the Al-Jabr hash — "
            "the plaintext is invisible to every observer without the founder key."
        ),
    },
    {
        "number": 3,
        "name": "Biological Basic Income",
        "module": "QiSync / VTX Ledger",
        "description": (
            "Participation in biometric resonance sessions (QiSync BioStance, Mastication) "
            "earns VTX tokens at rates tied to metabolic score and duration. "
            "The body becomes the proof-of-work engine."
        ),
    },
    {
        "number": 4,
        "name": "Cultural Immortality",
        "module": "Root-Chronicle / Adriana SCL",
        "description": (
            "Every proven consensus outcome is inscribed in the Root-Chronicle with a "
            "286-bit hash and an Adriana glyph poem. Future generations inherit ancestral "
            "wisdom on day zero — the culture cannot be deleted."
        ),
    },
    {
        "number": 5,
        "name": "Cognitive Sovereignty",
        "module": "Mesa / Inner Voice",
        "description": (
            "The Mesa Swarm and Inner Voice systems process decisions through distributed "
            "agent negotiation rather than centralised AI. Your reasoning remains local, "
            "auditable, and owned by you."
        ),
    },
    {
        "number": 6,
        "name": "Neighbourhood Mesh",
        "module": "Beehive / Silk Web",
        "description": (
            "The Beehive Protocol creates a hexagonal peer mesh where every Body node "
            "echoes the Brain's ledger, distributing trust across geography. "
            "No single failure point can silence the neighbourhood."
        ),
    },
    {
        "number": 7,
        "name": "Disaster Resilience",
        "module": "Keep Alive / Kinetic",
        "description": (
            "The flywheel energy reserve and nitrogen pressure monitoring ensure continuous "
            "operation during grid outages. Predictive Chronicle patterns pre-empt thermal "
            "cascades before they reach critical threshold."
        ),
    },
    {
        "number": 8,
        "name": "Emotional Logic",
        "module": "Adriana SCL / Consensus",
        "description": (
            "Adriana's 45-glyph lexicon encodes emotional and cultural states alongside "
            "machine commands, giving the consensus engine a vocabulary for grief, joy, "
            "and urgency — not just binary true/false."
        ),
    },
    {
        "number": 9,
        "name": "Inflation-Proof Living",
        "module": "VTX Ledger / Vortex Wallet",
        "description": (
            "VTX is minted through proof-of-resonance (data upload, mesh relay, biometrics) "
            "and burned on utility spend. The bonding-curve supply model means dilution "
            "follows real usage, not speculative printing."
        ),
    },
    {
        "number": 10,
        "name": "IP Sanctuary",
        "module": "Lead Shield / Prior Art",
        "description": (
            "The Prior Art archive and Lead Shield combination timestamps intellectual "
            "property with a 286-bit hash before public disclosure, creating an "
            "immutable, cryptographically sovereign proof-of-creation record."
        ),
    },
    {
        "number": 11,
        "name": "Universal Language Bridge",
        "module": "VOID Language / Adriana SCL",
        "description": (
            "The VOID Language glossary and Adriana glyph system provide a cross-cultural "
            "symbolic layer that translates resonance states without dependence on any "
            "single human language — communication survives linguistic collapse."
        ),
    },
    {
        "number": 12,
        "name": "Zero-Cost Intelligence",
        "module": "Mesa Swarm / Agent Vision",
        "description": (
            "The Mesa multi-agent swarm processes sensory, economic, and biological data "
            "locally on sovereign hardware. Intelligence is built in; no cloud subscription "
            "or API bill is required to think."
        ),
    },
    {
        "number": 13,
        "name": "Memento Protocol",
        "module": "Root-Chronicle / Episodic Memory",
        "description": (
            "Three memory layers — Short-Term (SLM.V), Episodic (NZM.M), and Ancestral "
            "(WSL.R) — give every node persistent recall across reboots, power cuts, and "
            "hardware generations. Identity survives hardware death."
        ),
    },
    {
        "number": 14,
        "name": "Sensory Democracy",
        "module": "Biophony / Agent Vision",
        "description": (
            "Acoustic ecology data and agent vision streams are open to every node on the "
            "mesh. Environmental intelligence is a commons — no one entity controls what "
            "the neighbourhood hears or sees."
        ),
    },
    {
        "number": 15,
        "name": "Truth in Frequency",
        "module": "VoidEcho / Audio Stega",
        "description": (
            "Documents embedded in 432 Hz audio via spectrogram steganography carry their "
            "own verification hash. The signal is the proof — no external certificate "
            "authority is required to confirm authenticity."
        ),
    },
    {
        "number": 16,
        "name": "Non-Extractive Data",
        "module": "Silt Ledger / Vigilance",
        "description": (
            "The Silt Ledger records data provenance on-chain. The Vigilance system rewards "
            "community members for reporting extraction attempts. Data earns for its "
            "creator, not for the platform that hosts it."
        ),
    },
    {
        "number": 17,
        "name": "Sovereign Archive",
        "module": "VoidEcho / VOID Chronicle",
        "description": (
            "The VOID Chronicle and VoidEcho together form an indestructible archive: "
            "history is encoded in sound, indexed by 286-bit hash, and distributed across "
            "the mesh. No central server deletion can erase the record."
        ),
    },
    {
        "number": 18,
        "name": "Autonomous Legacy",
        "module": "Genesis / Blueprint NFT",
        "description": (
            "Blueprint Tokens are cryptographic deeds to physical 4000-Series Sovereign "
            "Nodes. The token is the inheritance instrument — transferable, verifiable, "
            "and independent of any legal jurisdiction that may not survive the next century."
        ),
    },
]

MANIFESTO_TEXT = "\n\n".join(
    f"{a['number']}. {a['name']} [{a['module']}]\n{a['description']}"
    for a in SOCIAL_ADVANTAGES
)


@sovereign_manifesto_bp.route("/sovereign-manifesto")
def manifesto_page():
    return render_template(
        "sovereign_manifesto.html",
        advantages=SOCIAL_ADVANTAGES,
        total=len(SOCIAL_ADVANTAGES),
    )


@sovereign_manifesto_bp.route("/sovereign-manifesto/export", methods=["POST"])
def export_voidecho():
    """
    Hex-encode the Manifesto and generate a 432 Hz spectrogram VoidEcho WAV.
    Logs the export to the VOID_CHRONICLE.
    """
    try:
        hex_encoded = MANIFESTO_TEXT.encode("utf-8").hex()
        label = "SOVEREIGN_MANIFESTO_18_ADVANTAGES"
        from void_engine.audio_stega import encode_spectrogram
        wav_bytes = encode_spectrogram(label, duration=15.0)

        try:
            from void_engine.chronicle_adriana import save_seed_capture
            save_seed_capture(
                label="Sovereign Manifesto VoidEcho Export",
                text=(
                    f"HEX_DIGEST_SEAL_1: 0x4F62667573636174696F6E5F536869656C64\n"
                    f"HEX_DIGEST_SEAL_2: 0x31385F536F6369616C5F5363617273\n\n"
                    f"MANIFESTO HEX:\n{hex_encoded[:512]}...[truncated]"
                ),
            )
        except Exception as log_err:
            logger.warning("Could not log manifesto export to chronicle: %s", log_err)

        buf = io.BytesIO(wav_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="audio/wav",
            as_attachment=True,
            download_name="sovereign_manifesto_432hz.wav",
        )
    except Exception as e:
        logger.error("Manifesto VoidEcho export failed: %s", e)
        return jsonify({"error": "Export failed", "detail": str(e)}), 500


@sovereign_manifesto_bp.route("/sovereign-manifesto/hex")
def manifesto_hex():
    """Return the hex-encoded manifesto as JSON."""
    hex_encoded = MANIFESTO_TEXT.encode("utf-8").hex()
    return jsonify({
        "hex": hex_encoded,
        "byte_length": len(MANIFESTO_TEXT.encode("utf-8")),
        "void_seal_1": "0x4F62667573636174696F6E5F536869656C64",
        "void_seal_2": "0x31385F536F6369616C5F5363617273",
        "frequency_hz": 432,
        "advantages_count": len(SOCIAL_ADVANTAGES),
    })
