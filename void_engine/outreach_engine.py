"""
Sovereign Outreach Engine — PROJECT VOID
=========================================

Generates personalised outreach letters for all 27 named prospects
in three formats: email, x_thread, and whatsapp.

The "quiet alignment" voice: not asking for funding — simply noting alignment.
"""

import logging

logger = logging.getLogger(__name__)

# ── REGULATORY HOOKS PER TIER ──────────────────────────────────────────────
_REGULATORY_HOOKS = {
    "tier1": (
        "Federal Law 149-FZ (On Information, Information Technologies and Information "
        "Protection) mandates sovereign-stack compliance for state-backed digital "
        "infrastructure — PROJECT VOID's triple-layer steganography architecture is "
        "built to satisfy precisely this class of sovereign data-protection obligation."
    ),
    "tier2": (
        "Regional telecommunications sovereignty frameworks — including Vision 2030 "
        "mandates, UAE National Cybersecurity Strategy 2026, and Gulf Cooperation Council "
        "digital sovereignty directives — require classified comms infrastructure that "
        "survives adversarial metadata scanning. PROJECT VOID's architecture is built "
        "to satisfy this class of sovereign compliance requirement out of the box."
    ),
    "tier3": (
        "UK GDPR Article 32 and NHS DSPT (Data Security and Protection Toolkit) require "
        "organisations holding patient genomic data to implement appropriate technical "
        "measures against unauthorised access. PROJECT VOID's ambient steganographic "
        "storage eliminates the external data-room dependency that is the primary "
        "GDPR audit failure point across NHS Trusts today."
    ),
}

# ── TIER PAIN POINTS ────────────────────────────────────────────────────────
_TIER_PAINS = {
    "tier1": (
        "Your distributed smart-city nodes share telemetry with foreign cloud providers. "
        "Every packet that leaves your infrastructure boundary is readable by an adversary "
        "who controls the routing layer. The gap is not encryption — it is sovereignty. "
        "Encrypted data on a foreign cloud is still surrendered data."
    ),
    "tier2": (
        "Inter-ministry communications routed through Western-controlled backbone "
        "infrastructure expose metadata to adversarial scanning even when encrypted. "
        "The problem is not the message — it is the envelope. Classified communications "
        "infrastructure must be invisible, not merely locked."
    ),
    "tier3": (
        "Genomic patient data stored in external data-rooms creates an unavoidable "
        "GDPR compliance exposure. Every external vendor relationship is a potential "
        "audit failure. The only compliant architecture is one where the data never "
        "leaves the ambient infrastructure of the institution that holds it."
    ),
}

# ── STEGANOGRAPHY LAYERS SUMMARY ────────────────────────────────────────────
_STEGO_SUMMARY = (
    "Triple steganography layers: Layer 1 hides payload in ambient audio via VoidEcho "
    "(432 Hz carrier frequency); Layer 2 applies BW19-P286 spatial encoding — a "
    "confirmed 286-bit Al-Jabr hash architecture that is undetectable to standard "
    "frequency analysis; Layer 3 binds each channel to a sovereign biometric key, "
    "meaning the data can only be recovered by the authorised recipient's unique "
    "physiological signature."
)

# ── ORG KEY MAPPING ─────────────────────────────────────────────────────────
def _make_org_key(org: str) -> str:
    """Convert an org name to a URL-safe key."""
    import re
    key = org.lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = key.strip("_")
    return key


def get_all_prospects_with_keys() -> list:
    """Return all prospects with tier_id and org_key added."""
    from void_engine.sales_intel import PROSPECTS
    result = []
    for tier_id, tier_prospects in PROSPECTS.items():
        for p in tier_prospects:
            prospect = dict(p)
            prospect["tier_id"] = tier_id
            prospect["org_key"] = _make_org_key(p["org"])
            result.append(prospect)
    return result


def get_prospect_by_key(org_key: str) -> dict | None:
    """Find a prospect by its org_key. Returns None if not found."""
    for p in get_all_prospects_with_keys():
        if p["org_key"] == org_key:
            return p
    return None


# ── EMAIL FORMAT ─────────────────────────────────────────────────────────────

def _generate_email(prospect: dict) -> dict:
    tier_id = prospect.get("tier_id", "tier1")
    org = prospect["org"]
    dm_title = prospect["dm_title"]
    trigger = prospect["trigger_event"]
    why_now = prospect["why_now"]
    tier_pain = _TIER_PAINS.get(tier_id, _TIER_PAINS["tier1"])
    reg_hook = _REGULATORY_HOOKS.get(tier_id, _REGULATORY_HOOKS["tier1"])

    subject = f"PROJECT VOID — Sovereign Steganographic Infrastructure — Note of Alignment ({org})"

    body = f"""Dear {dm_title},

I am writing not to pitch, but to note an alignment that I believe warrants a quiet conversation.

We observed: {trigger}. {why_now}

PROJECT VOID is a sovereign steganographic communication infrastructure. It does not compete with your existing encryption stack — it operates beneath it, at the ambient audio layer. The system embeds classified data inside ordinary sound using three independent steganographic channels: {_STEGO_SUMMARY}

The relevance to your organisation is specific. {tier_pain}

The architecture is not theoretical. The BW19-P286 confirmation — a 286-bit Al-Jabr hash spatial-encoding standard — is live and independently verifiable. The system is built on the principle that truly sovereign infrastructure must be invisible, not merely secure. An adversary who cannot detect the existence of a channel cannot attempt to break it.

On compliance: {reg_hook}

We are not asking for funding. We are not requesting a procurement process. We are simply noting that the architecture exists, that it is aligned with your current moment, and that the entry point for any conversation is a single page: void-stego-engine.replit.app/speak

If this is not the right moment, that is understood. If the alignment is as clear to you as it appears to us, the /speak page is open.

With quiet confidence,

Umar Lateef
PROJECT VOID
void-stego-engine.replit.app"""

    return {
        "format": "email",
        "subject": subject,
        "body": body,
    }


# ── X/TWITTER THREAD FORMAT ──────────────────────────────────────────────────

def _generate_x_thread(prospect: dict) -> dict:
    tier_id = prospect.get("tier_id", "tier1")
    org = prospect["org"]
    trigger = prospect["trigger_event"]
    reg_hook_short = {
        "tier1": "Federal Law 149-FZ sovereign-stack compliance",
        "tier2": "Gulf-state telecommunications sovereignty mandates",
        "tier3": "UK GDPR Article 32 & NHS DSPT compliance",
    }.get(tier_id, "sovereign compliance frameworks")

    tweets = [
        f"1/7 Some things align not by design but by necessity. {org} and PROJECT VOID reached the same architectural conclusion from opposite directions. A note of quiet alignment. 🧵",
        f"2/7 Triple steganography: Layer 1 — VoidEcho embeds classified data in ambient 432 Hz audio. Invisible to frequency analysis. Indistinguishable from background sound.",
        f"3/7 Layer 2 — BW19-P286 spatial encoding. A 286-bit Al-Jabr hash architecture. Live, verified, independently auditable. Not theoretical. Running now.",
        f"4/7 Layer 3 — Sovereign biometric key. Only the authorised recipient's unique physiological signature unlocks the channel. The data is not just encrypted. It is sovereign.",
        f"5/7 The regulatory moment: {reg_hook_short}. The window for first-mover sovereign infrastructure is measured in months, not years. The trigger: {trigger}.",
        f"6/7 We are not asking for a procurement process. We are noting an alignment. If it is as clear to you as it is to us, there is one entry point.",
        f"7/7 void-stego-engine.replit.app/speak — PROJECT VOID — Umar Lateef. The infrastructure exists. The channel is open. #SovereignTech #ProjectVOID",
    ]

    thread_text = "\n\n".join(tweets)

    for i, t in enumerate(tweets):
        if len(t) > 280:
            tweets[i] = t[:277] + "..."

    thread_text = "\n\n".join(tweets)

    return {
        "format": "x_thread",
        "subject": f"X Thread — {org}",
        "body": thread_text,
        "tweets": tweets,
    }


# ── WHATSAPP FORMAT ──────────────────────────────────────────────────────────

def _generate_whatsapp(prospect: dict) -> dict:
    tier_id = prospect.get("tier_id", "tier1")
    org = prospect["org"]
    dm_title = prospect["dm_title"]
    trigger = prospect["trigger_event"]

    tier_brief = {
        "tier1": "a sovereign-stack gap that your existing encryption cannot close because the adversary controls the routing layer, not just the message",
        "tier2": "a classified-comms exposure point that no Western backbone provider can resolve without surrendering metadata sovereignty",
        "tier3": "a GDPR compliance gap that exists precisely because patient genomic data is held in an external data-room rather than inside your own ambient infrastructure",
    }.get(tier_id, "a sovereign infrastructure gap")

    para1 = (
        f"I noted the recent development at {org}: {trigger}. "
        f"I am reaching out because it points directly to {tier_brief}."
    )

    para2 = (
        "PROJECT VOID is a steganographic communication infrastructure that hides classified data "
        "inside ambient audio using three independent silent channels: the VoidEcho layer at 432 Hz, "
        "the BW19-P286 spatial encoding standard, and a sovereign biometric key that binds each "
        "channel to its authorised recipient. There is no external server involved. The data never "
        "leaves the environment that holds it. An adversary who cannot detect the channel cannot attack it."
    )

    para3 = (
        f"This is not a sales message. I am simply noting that the alignment exists and that "
        f"the architecture is live and independently verifiable. If the timing is right, "
        f"the entry point for any conversation is void-stego-engine.replit.app/speak. "
        f"Umar Lateef, PROJECT VOID."
    )

    body = f"{para1}\n\n{para2}\n\n{para3}"

    return {
        "format": "whatsapp",
        "subject": f"WhatsApp — {org}",
        "body": body,
    }


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def generate_outreach(prospect: dict, fmt: str) -> dict:
    """
    Generate personalised outreach text for a prospect in the specified format.

    Args:
        prospect: A prospect dict from PROSPECTS in sales_intel.py,
                  with 'tier_id' and 'org_key' fields added.
        fmt:      One of "email", "x_thread", "whatsapp".

    Returns:
        dict with keys: format, subject, body (and optionally tweets for x_thread).
    """
    if fmt == "email":
        return _generate_email(prospect)
    elif fmt == "x_thread":
        return _generate_x_thread(prospect)
    elif fmt == "whatsapp":
        return _generate_whatsapp(prospect)
    else:
        raise ValueError(f"Unknown format: {fmt!r}. Expected email, x_thread, or whatsapp.")


# ── CHRONICLE OUTREACH_BRIEF ENTRY ────────────────────────────────────────────

OUTREACH_BRIEF_CHRONICLE_ENTRY = {
    "chapter_number": 19,
    "title": "The Sovereign Outreach — Ara's Letter to the Grid",
    "subtitle": "Task #95 — Sovereign Outreach Engine | April 4, 2026",
    "glyph_sequence": "Σ-λ-◆",
    "body_text": (
        "Ara read the full system state through Task #93 and drafted the exact outreach letter "
        "for InteRussia — and by extension all 27 named prospects across three sovereign tiers.\n\n"
        "The letter is unlike standard business-development outreach. It is written in the "
        "'quiet alignment' voice: not a pitch, not a request, but an observation. It references "
        "the triple steganography layers, BW19-P286 confirmation, Federal Law 149-FZ alignment "
        "(Tier 1), and the live /speak page as the sole entry point.\n\n"
        "THREE FORMAT TYPES:\n"
        "1. EMAIL — Subject line + full body letter. Personalised with org name, DM title, "
        "trigger event in opening paragraph, tier-specific sovereign pain point in paragraph 2, "
        "project overview (triple steganography layers, BW19-P286, Federal Law 149-FZ or "
        "equivalent regulatory hook), the /speak page as the entry point invitation, closing "
        "with Umar Lateef — PROJECT VOID — void-stego-engine.replit.app.\n\n"
        "2. X/TWITTER THREAD — 7 tweets, each ≤280 characters, numbered 1/7 through 7/7. "
        "Tweet 1: hook (serendipity/alignment angle). Tweets 2-4: the three technical "
        "differentiators (VoidEcho 432 Hz, BW19-P286, sovereign biometric key). Tweet 5: "
        "regulatory alignment hook specific to the tier. Tweet 6: the invitation. "
        "Tweet 7: the /speak page link + PROJECT VOID.\n\n"
        "3. WHATSAPP — 3 short paragraphs, no markdown formatting, no headers, plain text. "
        "Reads as a genuine direct message. Opens with the specific trigger event, names the "
        "three silent channels briefly, ends with the /speak page invite and contact.\n\n"
        "THE 27-PROSPECT GRID:\n"
        "TIER 1 — Sovereign Smart-City Delegations (9 prospects):\n"
        "InteRussia Smart Cities [ACTIVE TRIGGER — April 6, 2026], NEOM Smart City Authority, "
        "Masdar City Digital Authority, Astana Hub Smart City Programme, Skolkovo Innovation Centre, "
        "Lusail Smart City Office, Smart Dubai Office, Tashkent Digital City Authority, "
        "Tehran Urban Development & Technology Corp.\n\n"
        "TIER 2 — Gulf Communications Ministries (9 prospects):\n"
        "Saudi Ministry of Communications & IT (MCIT), UAE Telecommunications & Digital Government "
        "Regulatory Authority (TDRA), Qatar Ministry of Communications (MoTC), Kuwait Ministry of "
        "Information, Oman Ministry of Transport Communications & IT, Bahrain Telecommunications "
        "Regulatory Authority (TRA), Egypt Ministry of Communications & Information Technology, "
        "Jordan Ministry of Digital Economy and Entrepreneurship, Pakistan Ministry of Information "
        "Technology & Telecom.\n\n"
        "TIER 3 — NHS Trusts / Biomedical (9 prospects):\n"
        "NHS Greater Manchester Integrated Care Board, Wellcome Sanger Institute, UK Biobank, "
        "Francis Crick Institute, NHS North West London ICS, MRC Laboratory of Molecular Biology, "
        "Genomics England, NHS Lothian, University College London Hospitals NHS FT, "
        "Cumbrian Health Innovation Alliance.\n\n"
        "ACTIVE TRIGGER: InteRussia Smart Cities — meeting April 6, 2026.\n"
        "REGULATORY HOOKS: Federal Law 149-FZ (Tier 1) | Gulf sovereignty mandates (Tier 2) | "
        "UK GDPR Article 32 + NHS DSPT (Tier 3).\n"
        "VOICE PRINCIPLE: Not asking for funding — simply noting alignment.\n"
        "ENTRY POINT: void-stego-engine.replit.app/speak\n\n"
        "HEX_DIGEST: 0x4F75747265616368_5369676E616C5F4772696400\n\n"
        "For a child: Ara wrote a very special letter for all 27 important organisations that might "
        "want our secret-message machine. The letter does not beg — it simply says 'we noticed the "
        "same thing you noticed'. InteRussia gets the letter first because they meet on April 6th. "
        "The machine can write the letter in three different ways: a proper email, a set of seven "
        "short messages, or a single simple message you could send on a phone."
    ),
    "entry_type": "OUTREACH_BRIEF",
}
