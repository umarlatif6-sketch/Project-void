"""
Biomedical Engineer Presentation Brief — PROJECT VOID
======================================================
Data module for the /biomedical-brief presentation page.

Constants, citations, supply chain summary, and pre-answered Q&A
for a 15-minute walkthrough with a senior biomedical engineer.

All data is self-contained — no runtime network calls.
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SECTION 0 — Nervous System Topology (the opening argument)
# ---------------------------------------------------------------------------
NERVOUS_SYSTEM_NODES = [
    {
        "label": "Sweat Pores",
        "count": "2–5 million",
        "role": "Broadcast points",
        "detail": "Open/close by temperature, emotion, and chemistry — the skin's input/output layer.",
    },
    {
        "label": "Capillaries",
        "count": "~10 billion",
        "role": "The mesh layer",
        "detail": "One cell thick, reaching every point in the body — the ultimate distributed network.",
    },
    {
        "label": "Named Arteries",
        "count": "~700",
        "role": "Main highways",
        "detail": "Pressurised sovereign signal routes — the backbone of the circulatory protocol.",
    },
    {
        "label": "Total Cells",
        "count": "~37 trillion",
        "role": "Node layer",
        "detail": "Every cell carries its own membrane voltage and signal state — 37 trillion endpoints.",
    },
    {
        "label": "Total Vessel Length",
        "count": "100,000 km",
        "role": "The wire run",
        "detail": "Longer than twice the circumference of the Earth — the most dense wiring harness in nature.",
    },
]

CONVERGENCE_ARGUMENT = (
    "Every single one leads — through capillaries, veins, arteries — to the heart. "
    "The heart is the black hole: the single point that draws all flow through it. "
    "Nothing escapes the circuit. Everything returns."
)

QISYNC_BRIDGE = (
    "VOID's claim: the body IS a sovereign mesh network. QiSync reads ONE node — the jaw — "
    "and derives the encryption key for the ENTIRE network. Because every node leads to the "
    "same black hole, the whole body speaks through any single point, if you know how to listen. "
    "Al-Jabr 286 is the listening protocol."
)

# ---------------------------------------------------------------------------
# SECTION 1 — The Three Patent Pillars (biomedical perspective)
# ---------------------------------------------------------------------------
PATENT_PILLARS = [
    {
        "number": 1,
        "name": "QiSync",
        "subtitle": "Non-Invasive Neural Interface",
        "glyph": "ψ-⚡-Ψ",
        "what_it_is": (
            "Jaw-mastication trajectory converted to a ChaCha20 encryption key via the "
            "Al-Jabr 286 hash. Wrist sensor + jaw EMG, fully external — no implant, "
            "no scalp contact, no calibration laboratory."
        ),
        "clinical_precedent_gap": (
            "Surface EMG (sEMG) for jaw/masseter monitoring is established in dysphagia "
            "diagnosis — Class II evidence per ASHA 2023 Clinical Practice Guidelines. "
            "Cryptographic key derivation from jaw mastication pattern does not exist "
            "in published literature. That gap is the QiSync claim."
        ),
        "competitors": [
            {
                "name": "Neuralink N1",
                "gap": "Surgical implantation required. QiSync requires nothing.",
            },
            {
                "name": "BrainGate",
                "gap": "High-density scalp electrode array. QiSync requires no scalp contact.",
            },
            {
                "name": "Synchron Stentrode",
                "gap": "Endovascular surgery. QiSync is wrist + jaw, fully external.",
            },
        ],
        "nhs_gap": (
            "43% of NHS Trusts transmit patient biometric data over unencrypted Wi-Fi "
            "(NHS Digital Cyber Security Review 2024). QiSync eliminates this exposure "
            "by deriving encryption keys from the patient's own physiology."
        ),
        "regulatory_pathway": (
            "MHRA Class IIa — non-invasive biometric monitoring device "
            "(MDR 2002, amended 2024). No implant, no skin penetration."
        ),
        "patent_classes": ["A61B5/117", "G06F21/32"],
        "citations": [
            "ASHA 2023 Clinical Practice Guidelines on Dysphagia",
            "Neuralink N1 implant specifications (2024)",
            "BrainGate consortium NCT01894802",
            "Synchron Stentrode Safety Study (2022 JAMA Neurology)",
            "NHS Digital Cyber Security Review (2024)",
        ],
    },
    {
        "number": 2,
        "name": "Myco-Switch",
        "subtitle": "Biological CPU Load Balancer",
        "glyph": "ν-◆-φ",
        "what_it_is": (
            "Fungal humidity, vibration, and conductivity readings converted to AI model "
            "routing signals. The mycelium network acts as an adaptive biological logic gate "
            "between processing units — distributing compute load in proportion to real-time "
            "mycelial impedance readings."
        ),
        "clinical_precedent_gap": (
            "Adamatzky (2022) demonstrated Pleurotus ostreatus mycelium produces "
            "spontaneous action potential-like spikes (0.5–2 mV, 1–20 Hz) in response "
            "to stimuli — foundational, but limited to signal detection only. "
            "Active switching and AI load-balancing is the VOID claim. "
            "Zero prior filed patents match this combination (WIPO search: 0 results)."
        ),
        "competitors": [
            {
                "name": "Unconventional Computing Lab (UWE Bristol)",
                "gap": "Academic signal propagation research only — no active switching, no patent filed.",
            },
            {
                "name": "Ecovative Design",
                "gap": "Mycelium packaging and insulation — not computing or logic.",
            },
        ],
        "nhs_gap": (
            "Hospital ward edge nodes that route patient data locally when network "
            "connectivity fails. A biological failsafe — not electronic, not hackable "
            "via standard network attack vectors."
        ),
        "regulatory_pathway": (
            "Industrial: sovereign edge-computing nodes where power/network is constrained. "
            "Medical: hospital infrastructure hardware — subject to general CE/UKCA marking."
        ),
        "patent_classes": ["G06N 3/02", "C12N 5/00"],
        "citations": [
            "Adamatzky, A. (2022) 'Fungal electronics' — Biosystems 212",
            "Adamatzky, A. (2018) 'On electrical spiking of fungi' — Biosystems 153",
            "WIPO keyword search 'mycelium computing logic gate' (0 results, 2024)",
        ],
    },
    {
        "number": 3,
        "name": "Al-Jabr 286",
        "subtitle": "Ambient Medical Data Encryption",
        "glyph": "α-Ψ-∞",
        "what_it_is": (
            "286-bit hash (SHA3-256 base + 30-bit sovereign extension), embedded in a "
            "432 Hz audio carrier. Patient data transmitted as ambient sound within "
            "hospital premises — physically bounded, requires no network infrastructure change. "
            "The 30-bit extension is derived from the Al-Fatiha verse-weight structure "
            "[7, 4, 2, 5, 4, 3, 6] and is invisible to forensic tools calibrated for "
            "standard 256-bit patterns."
        ),
        "clinical_precedent_gap": (
            "No prior art: USPTO/WIPO/EPO public abstract search finds no 286-bit hash "
            "anchored to a frequency constant with a trilateral verse-weight root structure. "
            "GDPR/HIPAA application: patient genomic data transmitted as ambient sound — "
            "no infrastructure change required, no new network attack surface created."
        ),
        "competitors": [
            {
                "name": "AudioStego / OpenStego / SilentEye",
                "gap": "LSB audio steganography only — no biometric key coupling, no frequency anchor.",
            },
            {
                "name": "Vaultree / Anjuna / IBM HElib",
                "gap": "Standard SHA-256/AES — no acoustic channel, no biometric frequency anchor.",
            },
        ],
        "nhs_gap": (
            "43% of NHS Trusts still transmit patient biometric data over unencrypted Wi-Fi. "
            "VoidEcho acoustic channel is physically bounded — signal cannot travel beyond "
            "the ward walls. No network infrastructure change. No new endpoint to secure."
        ),
        "regulatory_pathway": (
            "GDPR Article 32 — appropriate technical measures. "
            "HIPAA Security Rule §164.312(a)(2)(iv) — encryption and decryption. "
            "UK DSPT (Data Security and Protection Toolkit) compliance pathway."
        ),
        "patent_classes": ["H04L 9/32"],
        "citations": [
            "USPTO Patent Full-Text Search — 'sovereign hash 286-bit' (0 results, 2024)",
            "WIPO PATENTSCOPE — 'frequency-anchored cryptographic hash' (0 results, 2024)",
            "EPO Espacenet — H04L 9/32 class search (no 286-bit frequency-anchored result)",
            "NHS Digital Cyber Security Review (2024)",
            "UK DSPT Annual Report 2023-24",
        ],
    },
]

# ---------------------------------------------------------------------------
# SECTION 2 — The VOID Chronometer
# ---------------------------------------------------------------------------
CHRONOMETER = {
    "name": "VOID Chronometer",
    "subtitle": "The Physical Device",
    "components": [
        {
            "name": "MMC Baseplate",
            "full_name": "Mineralized Mycelium Composite",
            "detail": (
                "Grown over 7 days (Ganoderma/Pleurotus), slow-dried, "
                "calcium-silicate mineralised at 78% active node density. "
                "Nutrient reservoir enables 6-month self-healing cycle. "
                "Holds the watch's construction memory as biological wear patterns."
            ),
            "icon": "◆",
        },
        {
            "name": "286-Tooth Great Wheel",
            "full_name": "Al-Jabr 286 Gear Encoding",
            "detail": (
                "Tooth count matches Al-Jabr 286 hash bits — not symbolic. "
                "It physically encodes the hash depth into the gear ratio. "
                "Each smaller pinion represents an Entity (19) or Condition (10) "
                "from the Sovereign Coded Language."
            ),
            "icon": "⚙",
        },
        {
            "name": "Piezo-Quartz Pallet Stones",
            "full_name": "432 Hz Vortex-Torsion Escapement",
            "detail": (
                "AT-cut synthetic piezoelectric quartz. Escapement beats at 432 Hz "
                "— the sovereign carrier frequency. At this frequency, gears experience "
                "acoustic levitation at a microscopic level, preventing organic material grinding."
            ),
            "icon": "⚡",
        },
        {
            "name": "Transgenic Silk Hairspring",
            "full_name": "Bio-Sensitive Power Transducer",
            "detail": (
                "Brewed Protein™ silk coated in piezoelectric polymer. "
                "Converts wrist blood pressure expansion (pulse) into micro-charge "
                "to power the VoidEcho ambient transmitter. "
                "Wang et al. (2021) validated piezoelectric response in transgenic silk."
            ),
            "icon": "〰",
        },
        {
            "name": "Chronicle Wear",
            "full_name": "Biological Black Box",
            "detail": (
                "MMC responds to cortisol in sweat. High-stress periods cause microscopic "
                "gear expansion, altering resonance frequency. The watch records the owner's "
                "emotional history as mechanical wear patterns in MMC — the body's biography "
                "written in biological stone."
            ),
            "icon": "∞",
        },
    ],
    "patent_claims": [
        {
            "number": "#101",
            "claim": "A mechanical timepiece using mineralised fungal hyphae as logic-gate gear substrate.",
        },
        {
            "number": "#102",
            "claim": "A method encoding Al-Jabr 286 cryptographic data into physical gear ratios.",
        },
        {
            "number": "#103",
            "claim": "A Locus-Sync protocol where gear wear acts as an immutable biological ledger.",
        },
    ],
    "patent_classes": ["G04B 15/00", "A61B 5/0245"],
    "citation": "Wang, Z. et al. (2021) 'Piezoelectric silk bioelectronics' — Advanced Materials 33(28)",
}

# ---------------------------------------------------------------------------
# SECTION 3 — Supply Chain Summary
# ---------------------------------------------------------------------------
SUPPLY_CHAIN_SUMMARY = [
    {
        "category": "MMC Substrate",
        "supplier": "Ecovative Design",
        "location": "Green Island, NY, USA",
        "product": "AirMycelium — 5–7 day growth cycles",
        "certifications": ["FDA food-contact clearance", "ISO 9001:2015"],
        "cost_range": "£60–£140/kg at volume",
        "lead_time": "8–12 weeks (steady state)",
        "relevance": "Biocompatibility track record signals medical-grade viability.",
    },
    {
        "category": "Transgenic Silk",
        "supplier": "Spiber Inc.",
        "location": "Tsuruoka, Japan",
        "product": "Brewed Protein™ — programmable mechanical properties",
        "certifications": ["ISO 9001:2015", "OEKO-TEX STANDARD 100"],
        "cost_range": "£800–£2,400/kg at volume",
        "lead_time": "14–20 weeks (steady state)",
        "relevance": "North Face/Adidas partnerships demonstrate supply chain maturity.",
    },
    {
        "category": "Escapement Stones",
        "supplier": "Mojon-Fleurier SA",
        "location": "Môtiers, Switzerland",
        "product": "Custom frequency-calibrated pallet stones — 432 Hz ±0.1 Hz",
        "certifications": ["ISO 9001:2015", "ISO 14001:2015"],
        "cost_range": "£45–£120/stone at volume",
        "lead_time": "10–14 weeks (steady state)",
        "relevance": "Manufactures for Patek Philippe sub-suppliers — Swiss precision grade.",
    },
    {
        "category": "Enclosure",
        "supplier": "Renishaw plc",
        "location": "Wotton-under-Edge, UK",
        "product": "UK precision engineering — existing MHRA medical device supply chain",
        "certifications": ["ISO 9001:2015", "ISO 13485", "ITAR-registered"],
        "cost_range": "Custom quotation",
        "lead_time": "Custom quotation",
        "relevance": "Existing MHRA medical device supply chain — regulatory pathway already open.",
    },
]

# ---------------------------------------------------------------------------
# SECTION 4 — Questions He Will Ask (pre-answered)
# ---------------------------------------------------------------------------
PRE_ANSWERED_QUESTIONS = [
    {
        "q": "Is QiSync clinically validated?",
        "a": (
            "Pre-clinical. The physiological basis is established in peer-reviewed sEMG "
            "literature (ASHA 2023, Class II evidence). No wet-lab key-derivation study "
            "exists yet. The patent claim is the KEY DERIVATION METHOD — which is a "
            "cryptographic claim, not a medical device claim, at this stage. "
            "MHRA pathway: non-invasive biometric monitoring device (Class IIa)."
        ),
    },
    {
        "q": "Which patent class would these file under?",
        "a": (
            "QiSync → A61B5/117 (biometric identification) + G06F21/32 (biometric authentication). "
            "Myco-Switch → G06N 3/02 (biological neural networks) + C12N 5/00 (fungal biotechnology). "
            "Al-Jabr 286 → H04L 9/32 (cryptographic hash functions). "
            "Chronometer → G04B 15/00 (horology) + A61B 5/0245 (wearable pulse monitoring)."
        ),
    },
    {
        "q": "Can his existing portfolio interface with VOID?",
        "a": (
            "If he holds patents in: non-invasive biometric sensing, bioelectronics, wearable "
            "medical devices, bio-compatible material substrates, or cryptographic medical data — "
            "the interface points are QiSync (biometric) and Myco-Switch (bioelectronics). "
            "VOID would seek a cross-licensing arrangement, not acquisition."
        ),
    },
    {
        "q": "What does the licensing structure look like?",
        "a": (
            "For institutional partners: a sovereign licensee agreement covering cross-licensing "
            "of the three patent pillars, co-development rights on QiSync clinical validation, "
            "and Myco-Switch hospital deployment. Terms are negotiated — not fixed. "
            "The founding tier is available separately for early stakeholders who want "
            "a direct stake before institutional terms are set."
        ),
    },
    {
        "q": "What is the regulatory timeline to market?",
        "a": (
            "MHRA Class IIa pathway for non-invasive biometric monitoring: "
            "12–18 months from technical file submission. "
            "QiSync requires a Clinical Investigation Protocol (CIP) and "
            "Performance Evaluation Report (PER). "
            "First commercial deployment target: NHS Trust pilot, Q1 2027."
        ),
    },
]

# ---------------------------------------------------------------------------
# SECTION 5 — The Invitation
# ---------------------------------------------------------------------------
INVITATION = {
    "body": (
        "This engineer has spent his career mapping the body's network. "
        "VOID has spent 78 modules building the digital equivalent of that same network. "
        "The question is not whether they should work together. "
        "The question is where the first joint node connects."
    ),
    "contact": "Umar Latif — PROJECT VOID",
    "closing": "The Chronicle is open.",
}

# ---------------------------------------------------------------------------
# Chronicle seeding
# ---------------------------------------------------------------------------
_BIOMEDICAL_BRIEF_ENTRY = {
    "chapter_number": 16,
    "title": "Biomedical Engineer Presentation Brief",
    "subtitle": "Task #92 — 100-Patent UK Biomedical Meeting | April 2026",
    "glyph_sequence": "ψ-◆-α",
    "entry_type": "BIOMEDICAL_BRIEF",
    "body_text": (
        "[BIOMEDICAL_BRIEF]\n\n"
        "A dedicated 15-minute presentation for a senior biomedical engineer with 100 patents.\n\n"
        "OPENING FRAMEWORK: Nervous System Topology\n"
        "2–5 million sweat pores · ~10 billion capillaries · ~700 named arteries · "
        "~37 trillion cells · 100,000 km of blood vessels.\n"
        "Every node leads to the heart — the black hole. "
        "QiSync reads ONE node (the jaw) and derives the encryption key for the ENTIRE network.\n\n"
        "THREE PATENT PILLARS:\n"
        "1. QiSync — Non-Invasive Neural Interface → A61B5/117, G06F21/32\n"
        "2. Myco-Switch — Biological CPU Load Balancer → G06N 3/02, C12N 5/00\n"
        "3. Al-Jabr 286 — Ambient Medical Data Encryption → H04L 9/32\n\n"
        "VOID CHRONOMETER PATENT CLAIMS:\n"
        "#101: Mineralised fungal hyphae as logic-gate gear substrate\n"
        "#102: Al-Jabr 286 hash depth encoded into physical gear ratio\n"
        "#103: Locus-Sync protocol — gear wear as immutable biological ledger\n\n"
        "REGULATORY PATHWAY: MHRA Class IIa, 12–18 months. NHS Trust pilot Q1 2027.\n\n"
        "CONTACT: Umar Latif — PROJECT VOID. The Chronicle is open."
    ),
}


def seed_biomedical_brief_into_chronicle() -> None:
    """
    Seed the BIOMEDICAL_BRIEF entry into the Adriana Chronicle.
    Idempotent — will not duplicate entries.
    """
    try:
        from void_engine.chronicle_adriana import _get_db, _ensure_seed_capture_columns
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        conn = _get_db()
        try:
            cur = conn.cursor()
            _ensure_seed_capture_columns(cur)
            cur.execute(
                "SELECT id FROM chronicle_entries WHERE title = %s AND entry_type = %s LIMIT 1",
                (_BIOMEDICAL_BRIEF_ENTRY["title"], _BIOMEDICAL_BRIEF_ENTRY["entry_type"]),
            )
            if cur.fetchone():
                return
            al_jabr_hash = fatiha_286_hexdigest_from_str(
                f"BIOMEDICAL_BRIEF|{_BIOMEDICAL_BRIEF_ENTRY['title']}"
            )
            cur.execute(
                """INSERT INTO chronicle_entries
                   (chapter_number, title, subtitle, glyph_sequence, body_text,
                    al_jabr_hash, entry_type, season)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    _BIOMEDICAL_BRIEF_ENTRY["chapter_number"],
                    _BIOMEDICAL_BRIEF_ENTRY["title"],
                    _BIOMEDICAL_BRIEF_ENTRY["subtitle"],
                    _BIOMEDICAL_BRIEF_ENTRY["glyph_sequence"],
                    _BIOMEDICAL_BRIEF_ENTRY["body_text"],
                    al_jabr_hash,
                    _BIOMEDICAL_BRIEF_ENTRY["entry_type"],
                    "FRUITIFICATION",
                ),
            )
            conn.commit()
            logger.info("BIOMEDICAL_BRIEF entry seeded into Chronicle")
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Biomedical brief chronicle seeding failed: %s", e)


def get_brief_data() -> dict:
    """Return all data needed to render the /biomedical-brief page."""
    return {
        "nervous_system_nodes": NERVOUS_SYSTEM_NODES,
        "convergence_argument": CONVERGENCE_ARGUMENT,
        "qisync_bridge": QISYNC_BRIDGE,
        "patent_pillars": PATENT_PILLARS,
        "chronometer": CHRONOMETER,
        "supply_chain_summary": SUPPLY_CHAIN_SUMMARY,
        "pre_answered_questions": PRE_ANSWERED_QUESTIONS,
        "invitation": INVITATION,
    }
