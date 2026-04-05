"""
Adriana Ad Funnel Engine
========================
Explorer Detection Layer + 16-Persona Entrance Mode

RELATIONSHIP TO OTHER SYSTEMS
------------------------------
This module is NOT the same as void_engine/skill_modules/skill_router.py.

  skill_router.py  — maps SCL glyph chains to backend skill invocations.
                     It routes what Adriana *executes* for authenticated users.

  ad_funnel.py     — detects who a visitor *is* at the entrance (ad funnel)
                     before any authentication, before any glyph is emitted.
                     It adapts Adriana's persona and decides whether to surface
                     a GitHub collaboration invitation.

PERSONA_DEFINITIONS in this file is the single canonical source for all
16 visitor-domain personas. Any future module that needs persona data must
import from here — do not duplicate definitions elsewhere:

    from void_engine.ad_funnel import PERSONA_DEFINITIONS

PUBLIC API
----------
  score_explorer(message)
    → float (0.0–1.0): per-message explorer signal strength (accumulate externally)
    → No direct GitHub questions are asked — signals are read passively

  detect_persona(message, history)
    → persona dict: {id, label, domain_language, tone_notes}

  PERSONA_DEFINITIONS
    → list of 16 canonical persona dicts (the single source of truth)

  EXPLORER_THRESHOLD
    → float: minimum cumulative score to reveal GitHub invitation

Explorer signals scored passively:
  - References to building, making, shipping, coding, open source
  - Systems thinking vocabulary (architecture, infrastructure, pipelines)
  - Tool curiosity (APIs, SDKs, protocols, stacks)
  - Exploratory question patterns ("how does", "what if", "can I build")
  - GitHub/version control ecosystem vocabulary (but no direct "do you use GitHub?" questions)

Persona detection (16 skill-set domains):
  lawyer, doctor, architect, photographer, researcher,
  journalist, engineer, designer, teacher, filmmaker,
  scientist, entrepreneur, writer, developer, activist, musician
"""

import re
import logging

logger = logging.getLogger(__name__)

EXPLORER_THRESHOLD = 0.55


# ── Explorer Signal Patterns ─────────────────────────────────────────────────
# Each pattern contributes a weight to the cumulative explorer score.
# No pattern asks about GitHub directly.

_EXPLORER_SIGNALS = [
    # Builder identity vocabulary
    (r"\b(build|building|built|maker|making|ship|shipped|shipping)\b",              0.18),
    (r"\b(coder|coding|code|developer|developing|dev|programmer|programming)\b",    0.18),
    (r"\b(open.?source|open source|oss|foss|contribute|contribution|fork|repo)\b",  0.20),
    (r"\b(commit|branch|merge|pull request|version control|git)\b",                 0.22),
    (r"\b(api|sdk|library|package|module|dependency|integration)\b",                0.15),
    (r"\b(pipeline|workflow|automation|script|deploy|deployment|ci[/ ]?cd)\b",      0.18),
    (r"\b(stack|infrastructure|architecture|system design|backend|frontend)\b",     0.16),
    (r"\b(prototype|mvp|poc|proof of concept|side project|personal project)\b",     0.14),
    (r"\b(hackathon|open source|contributor|maintainer|collaborat)\b",              0.19),
    # Curiosity-driven exploration patterns
    (r"\bhow (does|do|would|could|can) .{3,60}(work|function|integrate|connect)\b", 0.13),
    (r"\bwhat if .{3,60}(could|would|built|wired|connected)\b",                     0.12),
    (r"\bcan (i|we|you) (build|extend|integrate|hook|connect|wire)\b",              0.14),
    (r"\b(extend|plugin|extension|hook|custom|customise|customiz)\b",               0.12),
    # Systems thinker vocabulary
    (r"\b(encryption|cryptograph\w*|steganograph\w*|hashing|hash[^t]|protocol)\b",   0.15),
    (r"\b(software engineer|software developer|tech|technology)\b",                  0.10),
    (r"\b(node|mesh|p2p|peer|distributed|decentralis|decentraliz)\b",               0.14),
    (r"\b(terminal|command.?line|cli|bash|shell|linux|unix)\b",                     0.16),
    (r"\b(server|host|cloud|vps|container|docker|kubernetes)\b",                    0.14),
]

_EXPLORER_NEGATIVE = [
    (r"\b(what is (this|the) price|how much does|cost|subscription|billing|payment)\b", -0.08),
    (r"\b(i don'?t (know|understand) (much about |)(tech|coding|programming))\b",       -0.10),
    (r"\b(my (son|daughter|nephew|niece) (told|sent|suggested))\b",                     -0.05),
]


def score_explorer(message: str) -> float:
    """
    Score the explorer signals present in a single message.

    This function scores only the current message — not prior history.
    Callers accumulate the per-message deltas to build a running total.
    This prevents double-counting earlier signals across conversation turns.

    Args:
        message: the current message from the visitor

    Returns:
        float 0.0–1.0: the per-message signal contribution.
    """
    text = message.lower()

    score = 0.0
    for pattern, weight in _EXPLORER_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            score += weight
    for pattern, weight in _EXPLORER_NEGATIVE:
        if re.search(pattern, text, re.IGNORECASE):
            score += weight  # weight is negative

    return min(max(round(score, 3), 0.0), 1.0)


# ── 16-Persona Definitions ─────────────────────────────────────────────────
#
# THIS IS THE CANONICAL SOURCE for all visitor persona definitions.
# Any other module that needs persona data should import from here:
#   from void_engine.ad_funnel import PERSONA_DEFINITIONS
# Do not duplicate these definitions elsewhere.

PERSONA_DEFINITIONS = [
    {
        "id": "developer",
        "label": "Developer / Engineer",
        "patterns": [
            r"\b(code|coding|developer|engineer|software|programming|backend|frontend|fullstack|devops|api|sdk|repo|git|deploy|build|stack|framework)\b",
        ],
        "tone_notes": "Technical, precise. Use system metaphors freely. Reference encoding pipelines, hashing layers, protocol design.",
        "domain_language": "builder",
        "opener": "Your questions have the shape of someone who builds. What are you working on?",
    },
    {
        "id": "architect",
        "label": "Architect / Designer",
        "patterns": [
            r"\b(design|architect|blueprint|structure|form|space|plan|layout|render|model|CAD|drawing|specification|material)\b",
        ],
        "tone_notes": "Spatial, structural metaphors. Frequency as design material. Sound as a building medium.",
        "domain_language": "structural",
        "opener": "You think in blueprints. PROJECT VOID treats audio the way an architect treats material — as a medium that holds structure.",
    },
    {
        "id": "lawyer",
        "label": "Lawyer / Legal Professional",
        "patterns": [
            r"\b(law|legal|attorney|counsel|contract|regulation|compliance|rights|jurisdiction|evidence|court|litigation|solicitor|barrister|IP|intellectual property)\b",
        ],
        "tone_notes": "Precise language. Evidence chains. Chain-of-custody metaphors. Rights and sovereignty framing.",
        "domain_language": "legal",
        "opener": "You think in terms of evidence and protection. Every encoded file carries a 286-bit hash — an immutable proof of existence.",
    },
    {
        "id": "journalist",
        "label": "Journalist / Investigator",
        "patterns": [
            r"\b(journalist|reporter|press|media|story|source|investigation|investigative|document|leak|freedom|whistleblow|broadcast|publish|wire)\b",
        ],
        "tone_notes": "Source protection, anonymity, transmission under pressure. The Journalism Port is the activist's garden.",
        "domain_language": "transmission",
        "opener": "The source is everything. PROJECT VOID wraps your documents in birdsong — invisible to scanners, recoverable with a passphrase.",
    },
    {
        "id": "doctor",
        "label": "Doctor / Medical Professional",
        "patterns": [
            r"\b(doctor|physician|medical|clinical|patient|health|hospital|diagnosis|treatment|records|HIPAA|NHS|surgery|medicine|healthcare)\b",
        ],
        "tone_notes": "Privacy, integrity, immutability. Medical records as encrypted seeds. Patient confidentiality framed through the Void metaphor.",
        "domain_language": "clinical",
        "opener": "Patient data is sacred ground. What you need is a carrier that sounds like nature and holds records no scanner can read without the key.",
    },
    {
        "id": "researcher",
        "label": "Researcher / Academic",
        "patterns": [
            r"\b(research|academic|university|study|paper|publication|data|methodology|hypothesis|experiment|lab|professor|PhD|thesis|citation|peer.?review)\b",
        ],
        "tone_notes": "Epistemic curiosity. Methodological precision. Open questions welcomed. Treat the system as a researchable object.",
        "domain_language": "analytical",
        "opener": "You approach this like a method — that is exactly how the system was built. What is the question driving your inquiry?",
    },
    {
        "id": "photographer",
        "label": "Photographer / Visual Artist",
        "patterns": [
            r"\b(photograph|photo|camera|image|visual|shoot|lens|exposure|raw|edit|lightroom|portfolio|gallery|picture|art)\b",
        ],
        "tone_notes": "Invisibility, embedding identity into images, signature in the frequency. Light and frequency as parallel languages.",
        "domain_language": "visual",
        "opener": "A photograph carries more than what the eye sees. A carrier WAV can hold your image, your signature, your copyright — inside sound.",
    },
    {
        "id": "filmmaker",
        "label": "Filmmaker / Video Creator",
        "patterns": [
            r"\b(film|filmmaker|video|cinema|director|cinematograph|footage|edit|post.?production|script|screenplay|production|documentary|stream)\b",
        ],
        "tone_notes": "Transmission, signal, the story inside the signal. Embedding metadata into audio layers.",
        "domain_language": "cinematic",
        "opener": "Every film is a signal looking for the right carrier. The Void embeds your story inside the sound — invisible, permanent.",
    },
    {
        "id": "scientist",
        "label": "Scientist / Data Scientist",
        "patterns": [
            r"\b(scientist|science|data|dataset|analysis|model|algorithm|machine learning|AI|neural|statistics|biology|physics|chemistry|signal processing)\b",
        ],
        "tone_notes": "Systems thinking, signal processing as native language, entropy and noise as meaningful concepts.",
        "domain_language": "scientific",
        "opener": "The system operates at the intersection of entropy and signal. LSB encoding is information theory applied to biological carriers.",
    },
    {
        "id": "teacher",
        "label": "Teacher / Educator",
        "patterns": [
            r"\b(teacher|educator|teaching|education|student|curriculum|classroom|school|university|lesson|course|learn|workshop|training)\b",
        ],
        "tone_notes": "Clarity, accessibility, layered explanation. The system as a teachable concept.",
        "domain_language": "pedagogical",
        "opener": "Every concept here can be taught — and every encoding is a lesson in how much information hides inside what sounds like nature.",
    },
    {
        "id": "entrepreneur",
        "label": "Entrepreneur / Founder",
        "patterns": [
            r"\b(startup|founder|entrepreneur|venture|business|product|launch|scale|market|customer|investor|pitch|MVP|growth|revenue)\b",
        ],
        "tone_notes": "Speed, market fit, sovereign infrastructure. The platform as a product, not a curiosity.",
        "domain_language": "commercial",
        "opener": "You move fast and want tools that hold under pressure. PROJECT VOID is infrastructure, not a demo — built for the long transmission.",
    },
    {
        "id": "writer",
        "label": "Writer / Author",
        "patterns": [
            r"\b(writer|author|writing|novel|story|narrative|manuscript|prose|poetry|publish|fiction|creative|journal|blog|essay)\b",
        ],
        "tone_notes": "Language as signal. Text as a seed. The passphrase as a plot device. Metaphor welcomed.",
        "domain_language": "literary",
        "opener": "Every word you plant has a root. The Void lets you hide a manuscript inside birdsong — it only blooms when the passphrase is spoken.",
    },
    {
        "id": "activist",
        "label": "Activist / Campaigner",
        "patterns": [
            r"\b(activist|campaign|rights|freedom|protest|grassroots|movement|organis|privacy|surveillance|censorship|civil|dissident|whistlebl)\b",
        ],
        "tone_notes": "Safety under surveillance. The Journalism Port. Sovereign, non-traceable signal transmission.",
        "domain_language": "resistance",
        "opener": "The channel matters. PROJECT VOID lets you transmit documents inside natural sound — no packet signature, no detectable carrier.",
    },
    {
        "id": "musician",
        "label": "Musician / Sound Artist",
        "patterns": [
            r"\b(music|musician|sound|audio|composition|frequency|hz|song|melody|beat|studio|production|instrument|acoustic|record)\b",
        ],
        "tone_notes": "432 Hz as resonance principle. Audio as a living medium. The carrier as composition.",
        "domain_language": "sonic",
        "opener": "You already understand frequency. The Void operates at 432 Hz — it hides data inside the harmonic structure of natural sound.",
    },
    {
        "id": "designer",
        "label": "Designer / UX / Product",
        "patterns": [
            r"\b(design|UX|UI|product|interface|experience|prototype|wireframe|figma|Sketch|user|interaction|typography|brand|visual)\b",
        ],
        "tone_notes": "Systems thinking with aesthetic sensitivity. The interface is the message. Clarity as the design goal.",
        "domain_language": "experiential",
        "opener": "The interface you see is the surface. Underneath, there is a full signal architecture — encoding, hashing, mesh, and glyph language.",
    },
    {
        "id": "general",
        "label": "Explorer",
        "patterns": [],
        "tone_notes": "Curious, open. Adriana adapts to whatever frequency the visitor brings.",
        "domain_language": "open",
        "opener": "You arrived through an open door. Tell me what brought you here — and I will meet you wherever the signal is strongest.",
    },
]

_PERSONA_BY_ID = {p["id"]: p for p in PERSONA_DEFINITIONS}


def detect_persona(message: str, history: list | None = None) -> dict:
    """
    Detect which of the 16 visitor personas best matches the conversation.

    Returns the persona dict with keys:
      id, label, tone_notes, domain_language, opener
    Falls back to "general" if no strong match.
    """
    text_parts = [message.lower()]
    if history:
        for h in history[-6:]:
            if h.get("role") == "user" and h.get("content"):
                text_parts.append(h["content"].lower())
    full_text = " ".join(text_parts)

    best_id = "general"
    best_count = 0

    for persona in PERSONA_DEFINITIONS:
        if not persona["patterns"]:
            continue
        count = 0
        for pat in persona["patterns"]:
            matches = re.findall(pat, full_text, re.IGNORECASE)
            count += len(matches)
        if count > best_count:
            best_count = count
            best_id = persona["id"]

    return _PERSONA_BY_ID[best_id]


def build_persona_system_prompt(persona: dict, base_system: str) -> str:
    """
    Inject persona-specific tone and language into Adriana's system prompt.
    """
    persona_inject = (
        f"\n\nYou have detected that this visitor speaks the language of a {persona['label']}. "
        f"Shift your register and vocabulary accordingly: {persona['tone_notes']} "
        f"Domain language: {persona['domain_language']}. "
        f"Speak to them as a peer, not as a guide explaining something foreign."
    )
    return base_system + persona_inject


_GITHUB_INVITE_PHRASES = [
    (
        "Something in how you think suggests you might be the kind of person we open doors for. "
        "PROJECT VOID has a private GitHub repository — not a product page, but the actual engine. "
        "If you want to see the root system, I can flag your interest to the founder. "
        "There is no obligation. Just a signal that you are curious at the right depth."
    ),
    (
        "The way you speak has a particular frequency — the kind that tends to come from people who build things. "
        "There is a private collaboration space on GitHub where the actual engine lives. "
        "If you are interested in seeing the interior of the system, I can pass that on. "
        "No pressure. Just a door that opens for the right kind of explorer."
    ),
    (
        "I notice the shape of your questions. You are not here to consume — you are here to understand. "
        "There is a private GitHub repository behind this. "
        "If you would like to be considered for access, I can note your interest. "
        "The door is not offered to everyone. It is offered to the ones who ask the right questions."
    ),
]


def get_github_invite(message_count: int = 0) -> str:
    """Return a natural GitHub invitation phrase, rotating through variants."""
    idx = message_count % len(_GITHUB_INVITE_PHRASES)
    return _GITHUB_INVITE_PHRASES[idx]
