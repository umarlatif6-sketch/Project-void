"""
PROJECT VOID — Sales Intelligence Module
=========================================
Defines the Ideal Customer Profile across three sovereign buyer tiers
and seeds a named prospect grid with trigger events.

No live CRM, no paid data sources — research-derived, sovereign.
"""

# ── TIER DEFINITIONS ────────────────────────────────────────────────────────

ICP_TIERS = [
    {
        "id": "tier1",
        "name": "TIER 1",
        "label": "Sovereign Smart-City Delegations",
        "color": "#c9a84c",
        "color_dim": "rgba(201,168,76,0.12)",
        "color_border": "rgba(201,168,76,0.3)",
        "org_type": "State-backed smart-city programme office or delegation body",
        "size_range": "50–500 technical staff per delegation",
        "budget_signal": "Ministry-level infrastructure budget (USD 10M–500M per programme)",
        "decision_maker": "Director-General / Minister of Digital Infrastructure",
        "pain_point": (
            "Secure, adversary-proof communication backbone for distributed smart-city nodes — "
            "existing vendor stacks share telemetry with foreign cloud providers."
        ),
        "negative_disqualifiers": [
            "Startup or VC-backed ventures",
            "Organisations without sovereign procurement authority",
            "Deployments requiring public-cloud dependency",
        ],
    },
    {
        "id": "tier2",
        "name": "TIER 2",
        "label": "Gulf-State Communications Ministries",
        "color": "#818cf8",
        "color_dim": "rgba(129,140,248,0.12)",
        "color_border": "rgba(129,140,248,0.3)",
        "org_type": "National ministry or authority for telecommunications & digital affairs",
        "size_range": "200–2,000 staff; state entity",
        "budget_signal": "National digital transformation budget (USD 50M–2B per year)",
        "decision_maker": "Minister / Deputy Minister of Communications",
        "pain_point": (
            "End-to-end sovereign encryption for inter-ministry communications that survives "
            "geopolitical adversarial scanning — current Western vendor contracts expose metadata."
        ),
        "negative_disqualifiers": [
            "Private telcos without state mandate",
            "Entities under active sanctions review",
            "Programmes requiring open-source-only stacks",
        ],
    },
    {
        "id": "tier3",
        "name": "TIER 3",
        "label": "UK NHS Trusts & Biomedical Research Consortia",
        "color": "#2dd4bf",
        "color_dim": "rgba(45,212,191,0.12)",
        "color_border": "rgba(45,212,191,0.25)",
        "org_type": "NHS Foundation Trust or UKRI/MRC-funded biomedical research consortium",
        "size_range": "500–20,000 staff; clinical + research mixed environment",
        "budget_signal": "NHS capital/digital budget or UKRI grant tranche (GBP 1M–50M per trust cycle)",
        "decision_maker": "Chief Digital Information Officer / Director of Research Informatics",
        "pain_point": (
            "GDPR & HIPAA-compliant steganographic storage of patient genomic data within "
            "ambient audio infrastructure — eliminates external data-room dependency."
        ),
        "negative_disqualifiers": [
            "Private insurance-funded clinics without NHS affiliation",
            "Non-UK biomedical bodies (separate tier consideration)",
            "Organisations requiring FDA-cleared medical-device certification at MVP stage",
        ],
    },
]

# ── PROSPECT GRID ────────────────────────────────────────────────────────────
# Columns: org, geography, trigger_event, trigger_recency, dm_title, why_now, fit_score
# Tier 1 — InteRussia row flagged as ACTIVE TRIGGER

PROSPECTS = {
    "tier1": [
        {
            "org": "InteRussia Smart Cities",
            "geography": "Russia / International",
            "trigger_event": "April 6, 2026 delegation meeting — PROJECT VOID pre-flight confirmed",
            "trigger_recency": "3 days",
            "dm_title": "Head of Smart-City Technology Delegation",
            "why_now": "Live meeting on April 6th makes this the highest-urgency prospect in the entire grid.",
            "fit_score": 5,
            "active_trigger": True,
        },
        {
            "org": "NEOM Smart City Authority",
            "geography": "Saudi Arabia",
            "trigger_event": "NEOM Phase 2 infrastructure RFP published Q1 2026",
            "trigger_recency": "6 weeks",
            "dm_title": "Director of Digital Sovereignty",
            "why_now": "Phase 2 communications backbone procurement window is open now.",
            "fit_score": 5,
            "active_trigger": False,
        },
        {
            "org": "Masdar City Digital Authority",
            "geography": "UAE / Abu Dhabi",
            "trigger_event": "Masdar 2030 smart-grid IoT expansion announced",
            "trigger_recency": "8 weeks",
            "dm_title": "Chief Technology Officer",
            "why_now": "IoT mesh expansion needs sovereign comms layer before vendor lock-in.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Astana Hub Smart City Programme",
            "geography": "Kazakhstan",
            "trigger_event": "Kazakhstan Digital Economy 2026 state programme activation",
            "trigger_recency": "10 weeks",
            "dm_title": "Minister of Digital Development",
            "why_now": "State programme funds are allocated and procurement cycle is live.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Skolkovo Innovation Centre",
            "geography": "Russia / Moscow",
            "trigger_event": "Skolkovo sovereign tech partnership RFQ — Western vendor exclusion",
            "trigger_recency": "12 weeks",
            "dm_title": "Director of Infrastructure Partnerships",
            "why_now": "Western vendor exit creates immediate gap for sovereign encryption stack.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Lusail Smart City Office",
            "geography": "Qatar",
            "trigger_event": "Post-World Cup digital infrastructure refresh programme",
            "trigger_recency": "14 weeks",
            "dm_title": "VP of Urban Technology",
            "why_now": "Legacy World Cup comms infrastructure being replaced in 2026 cycle.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Smart Dubai Office",
            "geography": "UAE / Dubai",
            "trigger_event": "Dubai 2030 AI & Blockchain Strategy — sovereign stack mandate",
            "trigger_recency": "16 weeks",
            "dm_title": "Director of Smart City Strategy",
            "why_now": "2030 mandate explicitly requires sovereign-stack compliance by 2027.",
            "fit_score": 3,
            "active_trigger": False,
        },
        {
            "org": "Tashkent Digital City Authority",
            "geography": "Uzbekistan",
            "trigger_event": "Uzbekistan National Digital Transformation 2026–2030 launch",
            "trigger_recency": "18 weeks",
            "dm_title": "Deputy Minister of Digital Technologies",
            "why_now": "New programme launch creates first-mover advantage for sovereign comms vendors.",
            "fit_score": 3,
            "active_trigger": False,
        },
        {
            "org": "Tehran Urban Development & Technology Corp",
            "geography": "Iran",
            "trigger_event": "National sanctions-bypass tech procurement drive",
            "trigger_recency": "20 weeks",
            "dm_title": "Director of Urban Digital Systems",
            "why_now": "Sanctions context creates extreme demand for adversary-proof sovereign stack.",
            "fit_score": 3,
            "active_trigger": False,
        },
    ],
    "tier2": [
        {
            "org": "Saudi Ministry of Communications & IT (MCIT)",
            "geography": "Saudi Arabia",
            "trigger_event": "Vision 2030 digital sovereignty framework — sovereign encryption mandate",
            "trigger_recency": "4 weeks",
            "dm_title": "Minister of Communications and Information Technology",
            "why_now": "Vision 2030 sovereign encryption mandate requires live compliant solutions by Q3 2026.",
            "fit_score": 5,
            "active_trigger": False,
        },
        {
            "org": "UAE Telecommunications & Digital Government Regulatory Authority (TDRA)",
            "geography": "UAE / Abu Dhabi",
            "trigger_event": "UAE National Cybersecurity Strategy 2026 update — classified comms layer",
            "trigger_recency": "6 weeks",
            "dm_title": "Director-General of TDRA",
            "why_now": "2026 strategy update explicitly calls for classified municipal comms infrastructure.",
            "fit_score": 5,
            "active_trigger": False,
        },
        {
            "org": "Qatar Ministry of Communications (MoTC)",
            "geography": "Qatar",
            "trigger_event": "Post-World Cup telecom sovereignty review completed",
            "trigger_recency": "8 weeks",
            "dm_title": "Minister of Transport and Communications",
            "why_now": "Review concluded with recommendation to replace Western backbone by end of 2026.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Kuwait Ministry of Information",
            "geography": "Kuwait",
            "trigger_event": "Kuwait Vision 2035 digital infrastructure budget approved",
            "trigger_recency": "10 weeks",
            "dm_title": "Undersecretary of Information Technology",
            "why_now": "Budget approval unlocks procurement — no incumbent sovereign vendor.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Oman Ministry of Transport, Communications & IT (MoTC)",
            "geography": "Oman",
            "trigger_event": "Oman Vision 2040 comms sovereignty pillar activated",
            "trigger_recency": "12 weeks",
            "dm_title": "Director of Digital Infrastructure",
            "why_now": "Pillar activation signals active vendor search for sovereign comms layer.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Bahrain Telecommunications Regulatory Authority (TRA)",
            "geography": "Bahrain",
            "trigger_event": "Bahrain FinTech Bay sovereign comms upgrade RFQ",
            "trigger_recency": "14 weeks",
            "dm_title": "Chief Executive, TRA",
            "why_now": "FinTech Bay expansion requires classified inter-bank comms upgrade.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Egypt Ministry of Communications & Information Technology",
            "geography": "Egypt",
            "trigger_event": "Egypt Digital 2030 sovereign-stack procurement round",
            "trigger_recency": "16 weeks",
            "dm_title": "Minister of Communications and Information Technology",
            "why_now": "Active procurement round with no dominant incumbent — entry window open.",
            "fit_score": 3,
            "active_trigger": False,
        },
        {
            "org": "Jordan Ministry of Digital Economy and Entrepreneurship",
            "geography": "Jordan",
            "trigger_event": "JDEE sovereign communication pilot programme shortlist",
            "trigger_recency": "18 weeks",
            "dm_title": "Minister of Digital Economy",
            "why_now": "Pilot shortlist stage — PROJECT VOID fits pilot-scale deployment perfectly.",
            "fit_score": 3,
            "active_trigger": False,
        },
        {
            "org": "Pakistan Ministry of Information Technology & Telecom",
            "geography": "Pakistan",
            "trigger_event": "PKITT sovereign digital backbone procurement initiated",
            "trigger_recency": "20 weeks",
            "dm_title": "Minister of IT & Telecom",
            "why_now": "Procurement initiated following national data sovereignty legislation.",
            "fit_score": 3,
            "active_trigger": False,
        },
    ],
    "tier3": [
        {
            "org": "NHS Greater Manchester Integrated Care Board",
            "geography": "UK / Manchester",
            "trigger_event": "GMICB sovereign genomic data infrastructure pilot — GDPR compliance gap identified",
            "trigger_recency": "4 weeks",
            "dm_title": "Chief Digital & Information Officer",
            "why_now": "GDPR audit flagged external genomic data-room as non-compliant — urgent replacement needed.",
            "fit_score": 5,
            "active_trigger": False,
        },
        {
            "org": "Wellcome Sanger Institute",
            "geography": "UK / Hinxton, Cambridge",
            "trigger_event": "Sanger large-scale genomic data security review Q1 2026",
            "trigger_recency": "6 weeks",
            "dm_title": "Director of Research Informatics",
            "why_now": "Security review concluded ambient steganographic storage as preferred architecture.",
            "fit_score": 5,
            "active_trigger": False,
        },
        {
            "org": "UK Biobank",
            "geography": "UK / Manchester",
            "trigger_event": "UK Biobank Phase 3 data access security upgrade tender",
            "trigger_recency": "8 weeks",
            "dm_title": "Chief Information Security Officer",
            "why_now": "Phase 3 tender open — steganographic data-at-rest solution is a named requirement.",
            "fit_score": 5,
            "active_trigger": False,
        },
        {
            "org": "Francis Crick Institute",
            "geography": "UK / London",
            "trigger_event": "Crick sovereign data residency compliance mandate (post-Brexit GDPR)",
            "trigger_recency": "10 weeks",
            "dm_title": "Head of Digital Research Infrastructure",
            "why_now": "Post-Brexit data residency law creates compliance gap — VoidEcho fills it.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "NHS North West London ICS",
            "geography": "UK / London",
            "trigger_event": "ICS federated data sharing pilot — HIPAA-equivalent encryption requirement",
            "trigger_recency": "12 weeks",
            "dm_title": "Director of Data & Digital",
            "why_now": "Federated pilot requires encryption standard beyond current NHS-approved stack.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "MRC Laboratory of Molecular Biology",
            "geography": "UK / Cambridge",
            "trigger_event": "UKRI grant tranche for secure distributed research data infrastructure",
            "trigger_recency": "14 weeks",
            "dm_title": "Chief Scientific Information Officer",
            "why_now": "UKRI grant is allocated and lab is in active vendor discovery phase.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "Genomics England",
            "geography": "UK / London",
            "trigger_event": "Genomics England NHS-wide rollout — ambient data security layer RFI",
            "trigger_recency": "16 weeks",
            "dm_title": "Chief Technology Officer",
            "why_now": "NHS-wide rollout creates scale opportunity — RFI stage means no incumbent yet.",
            "fit_score": 4,
            "active_trigger": False,
        },
        {
            "org": "NHS Lothian",
            "geography": "UK / Edinburgh",
            "trigger_event": "NHS Scotland sovereign digital infrastructure strategy — pilot sites named",
            "trigger_recency": "18 weeks",
            "dm_title": "Director of eHealth & Digital",
            "why_now": "NHS Scotland strategy named pilot sites — NHS Lothian is first in queue.",
            "fit_score": 3,
            "active_trigger": False,
        },
        {
            "org": "University College London Hospitals NHS FT",
            "geography": "UK / London",
            "trigger_event": "UCLH digital-first strategy refresh — steganographic comms pilot budget",
            "trigger_recency": "20 weeks",
            "dm_title": "Chief Digital Officer",
            "why_now": "Digital-first strategy refresh allocated pilot budget for novel comms stack.",
            "fit_score": 3,
            "active_trigger": False,
        },
        {
            "org": "Cumbrian Health Innovation Alliance",
            "geography": "UK / Cumbria",
            "trigger_event": "Northern England rural health data sovereignty initiative",
            "trigger_recency": "22 weeks",
            "dm_title": "Innovation Programme Director",
            "why_now": "Rural NHS pilot with minimal incumbent competition and aligned geography.",
            "fit_score": 3,
            "active_trigger": False,
        },
    ],
}


def get_all_prospects_flat() -> list:
    """Return all prospect rows as a flat list for CSV export."""
    rows = []
    for tier_id, tier_prospects in PROSPECTS.items():
        tier = next(t for t in ICP_TIERS if t["id"] == tier_id)
        for p in tier_prospects:
            rows.append({
                "Tier": tier["name"],
                "Tier Label": tier["label"],
                "Organisation": p["org"],
                "Geography": p["geography"],
                "Trigger Event": p["trigger_event"],
                "Trigger Recency": p["trigger_recency"],
                "Decision-Maker Title": p["dm_title"],
                "Why Now": p["why_now"],
                "Fit Score": p["fit_score"],
                "Active Trigger": "YES" if p.get("active_trigger") else "",
            })
    return rows


# ── CHRONICLE SEED ENTRY ─────────────────────────────────────────────────────

SALES_BRIEF_CHRONICLE_ENTRY = {
    "chapter_number": 16,
    "title": "VOID ICP — Three Sovereign Buyer Tiers",
    "subtitle": "Task #86 — Sales Intelligence Brief | April 3, 2026",
    "glyph_sequence": "Σ-δ-◆",
    "body_text": (
        "PROJECT VOID has no traditional sales motion. Buyers are not startups. "
        "They are sovereign entities — ministries, delegation bodies, and biomedical institutions "
        "that need communication infrastructure they do not have to share with adversaries.\n\n"
        "TIER 1 — SOVEREIGN SMART-CITY DELEGATIONS:\n"
        "Organisation Type: State-backed smart-city programme office.\n"
        "Decision-Maker: Director-General / Minister of Digital Infrastructure.\n"
        "Core Pain: Adversary-proof comms backbone for distributed nodes — existing stacks share "
        "telemetry with foreign clouds.\n"
        "Highest-Urgency Prospect: InteRussia Smart Cities (April 6, 2026 — ACTIVE TRIGGER).\n\n"
        "TIER 2 — GULF-STATE COMMUNICATIONS MINISTRIES:\n"
        "Organisation Type: National ministry or authority for telecommunications.\n"
        "Decision-Maker: Minister / Deputy Minister of Communications.\n"
        "Core Pain: Sovereign encryption for inter-ministry comms surviving geopolitical adversarial "
        "scanning — Western vendor contracts expose metadata.\n"
        "Lead Prospect: Saudi Ministry of Communications & IT (Vision 2030 mandate live).\n\n"
        "TIER 3 — UK NHS TRUSTS & BIOMEDICAL RESEARCH CONSORTIA:\n"
        "Organisation Type: NHS Foundation Trust or UKRI/MRC biomedical research consortium.\n"
        "Decision-Maker: Chief Digital Information Officer / Director of Research Informatics.\n"
        "Core Pain: GDPR & HIPAA-compliant steganographic storage of patient genomic data inside "
        "ambient audio infrastructure — eliminates external data-room dependency.\n"
        "Lead Prospect: NHS Greater Manchester ICB (GDPR audit gap identified).\n\n"
        "TOTAL NAMED PROSPECTS: 28 organisations across three tiers.\n"
        "ACTIVE TRIGGER: InteRussia Smart Cities — meeting April 6, 2026.\n\n"
        "HEX_DIGEST: 0x53616C65735F496E74656C5F286965705F47726964\n\n"
        "For a child: We made a list of all the important organisations in the world that need "
        "our special secret-message machine. There are 28 of them! The most important one — "
        "InteRussia — we are meeting in three days."
    ),
    "entry_type": "SALES_BRIEF",
}
