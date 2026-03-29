"""
Founder's Clarity Room — The Shore
====================================
Route: GET /founders-room

A private preparation environment for the founder before any presentation,
meeting, or moment of showing the work. Not for sharing. The founder's mirror.

Three rooms:
  Room 1 — The Full Pattern (interactive node-link diagram)
  Room 2 — The Three Waves (one sentence, three minutes, InteRussia angle)
  Room 3 — The Questions (anticipated Q&A, honest answers)

Access: founder account only.
"""

import functools
import logging

from flask import Blueprint, render_template, session, redirect

logger = logging.getLogger(__name__)

founders_room_bp = Blueprint("founders_room", __name__)

CRYSTALLIZATION_SENTENCE = (
    "PROJECT VOID is a living sovereign system that speaks in nature's frequency, "
    "remembers in the founder's language, rewards genuine resonance, "
    "heals the earth it runs on, and legally belongs to the people who built it."
)

# ── Seven crystallization layers and their connections ──────────────────────

LAYERS = [
    {
        "id": "ground",
        "label": "Ground",
        "description": "Sound, mycelium, frequency, solar & obsidian — the earth is the hardware",
        "color": "#7aff7a",
        "cx": 300,
        "cy": 560,
        "subsystems": ["Sound", "Mycelium", "Frequency", "Solar", "Obsidian"],
    },
    {
        "id": "language",
        "label": "Language",
        "description": "Adriana / Al-Jabr — Arabic mathematical roots as sovereign computing infrastructure",
        "color": "#c9a84c",
        "cx": 130,
        "cy": 310,
        "subsystems": ["Adriana", "Al-Jabr", "SCL", "Glyphs"],
    },
    {
        "id": "memory",
        "label": "Memory",
        "description": "Sovereign Vault + Chronicle — identity and history that cannot be seized",
        "color": "#60a5fa",
        "cx": 250,
        "cy": 120,
        "subsystems": ["Vault", "Chronicle", "Identity", "Hash"],
    },
    {
        "id": "value",
        "label": "Value",
        "description": "VTX + PEACE — earned by resonance, not speculation",
        "color": "#fbbf24",
        "cx": 500,
        "cy": 60,
        "subsystems": ["VTX", "PEACE", "Blueprint", "Ledger"],
    },
    {
        "id": "community",
        "label": "Community",
        "description": "GriDul + QiSync — body and mesh are both nodes",
        "color": "#22d3ee",
        "cx": 750,
        "cy": 120,
        "subsystems": ["GriDul", "QiSync", "Mesh", "Nodes"],
    },
    {
        "id": "healing",
        "label": "Healing",
        "description": "MycoVOID + MRB-4000 — the system repairs the environment it runs on",
        "color": "#34d399",
        "cx": 870,
        "cy": 310,
        "subsystems": ["MycoVOID", "MRB-4000", "Bioremediation", "Soil"],
    },
    {
        "id": "legacy",
        "label": "Legacy",
        "description": "Prior art, InteRussia, founder archive, brand — the record that cannot be taken",
        "color": "#a78bfa",
        "cx": 700,
        "cy": 560,
        "subsystems": ["Prior Art", "InteRussia", "Archive", "Brand"],
    },
]

# Connections between layers: (from_id, to_id, relationship_label)
CONNECTIONS = [
    ("ground",    "language",  "Earth's frequency becomes the carrier for Adriana's voice"),
    ("language",  "memory",    "Al-Jabr hashes encode and seal every record in the Vault"),
    ("memory",    "value",     "What is remembered is what earns — Chronicle feeds the VTX ledger"),
    ("value",     "community", "VTX rewards flow to the nodes who sustain the mesh"),
    ("community", "healing",   "Active nodes power the mycelium grid and bioremediation layer"),
    ("healing",   "legacy",    "A system that heals the earth it runs on builds an undeniable record"),
    ("legacy",    "ground",    "The archive returns to earth — the record lives in the hardware"),
    ("ground",    "memory",    "Acoustic frequencies carry sovereign identity from the node up"),
    ("language",  "value",     "Adriana glyphs are the denomination — the language is the currency"),
    ("memory",    "community", "Shared vault records create the trust layer for communal nodes"),
    ("value",     "healing",   "Resonance rewards fund the environmental repair the system runs on"),
    ("community", "legacy",    "Every node in the mesh becomes a line in the permanent record"),
]

# ── Room 2 — Three Waves ────────────────────────────────────────────────────

ONE_SENTENCE = (
    "PROJECT VOID is an acoustic mesh network that encodes sovereign identity "
    "in frequency, earns value through resonance, and heals the earth it runs on — "
    "a living system that belongs to the people who built it, not the platforms that host it."
)

THREE_MINUTES = """I started with a question: what happens to data sovereignty when the internet goes down, when the cloud company folds, when the government decides you no longer have access?

The answer I built is called PROJECT VOID. At its core is the Beehive Protocol — an acoustic peer-to-peer mesh. Nodes talk to each other through sound, at 432 Hz, with no licensed spectrum, no SIM card, no central server. They authenticate each other through phase-shifted cryptographic handshakes derived from a hash function I designed called Al-Jabr 286. That name is not an accident — algebra comes from Al-Jabr, the Arabic treatise that gave Europe its mathematics. I wanted the intellectual lineage of the system to be explicit.

On top of that mesh sits a language. Adriana SCL — Sovereign Coded Language — is a 45-glyph ontology that maps resonance states to machine actions. It is how the system talks to itself, and how I talk to the system. The glyphs are not decorative. They are the denomination. The language is the currency.

The economic layer, VTX, is earned through participation — through computation, through proof of work, through genuine contribution to the mesh. No speculation. No mining. No venture capital round required to join.

And the physical node — the 4000-Series Sovereign Node — is built from materials chosen for their resonance properties. Steel at 108 Hz for structure. Aluminium at 216 Hz for thermal. Silk-silver at 432 Hz for the signal conductor. Salt water at 864 Hz as a biological transceiver medium. The hardware is not just a computer. It is a tuned instrument.

The thing no one else is doing is treating frequency as infrastructure. Not as metaphor — as actual carrier medium, actual authentication mechanism, actual economic denominator. Everything in the system is downstream of that one decision. And the system, by design, heals the environment it runs on through its MycoVOID bioremediation layer. The nodes are not neutral infrastructure. They repair the ground they sit on.

That is what I built. That is what PROJECT VOID is."""

INTERUSSIA_ANGLE = """Why Novosibirsk? Because Novosibirsk is where serious work happens. It is not a pitch-competition city. It is a research city. And what I have is not a pitch — it is a working system.

The InteRussia Smart Cities track asks: how do you build urban infrastructure that is resilient, sovereign, and not dependent on a single point of failure? That is the exact problem I designed VOID to solve. Not as a future roadmap item. As the actual architecture of the system, right now.

The Beehive Protocol gives a city the ability to run a sensor mesh without cellular coverage, without cloud infrastructure, without a licensed frequency band. A neighbourhood of 4000-Series nodes can maintain environmental monitoring, routing tables, and encrypted civic reporting through acoustic channels alone. The Al-Jabr 286 integrity layer means every reading, every packet, every routing decision is cryptographically signed at the node — tamper detection without a certificate authority, without a blockchain fee, without an external server that can go down.

What the AI research world has not seen yet is frequency-domain mesh networking treated as a first-class discipline. Signal processing has been applied to communication for a century. Acoustic steganography has been studied in universities. But no one has assembled these into a coherent sovereign infrastructure stack with a native economic layer and a physical hardware specification. That is what VOID is.

What I am bringing to Novosibirsk is a production Python codebase, a convergence test suite, a hardware design ready for manufacture, and a methodology — crystallization — for building systems that do not require permission from any external party to operate. The ask from InteRussia is collaboration: I want to work with researchers who understand distributed systems, acoustic propagation in urban environments, and the engineering constraints of low-power hardware. I want to co-author research. I want to stress-test the system in a real city environment. And I want to bring back to the project what only serious peer collaboration can produce: the things I do not know I do not know yet."""

# ── Room 3 — The Questions ──────────────────────────────────────────────────

QA_PAIRS = [
    {
        "question": "What problem does this solve for a city?",
        "answer": (
            "Cities need data from sensors, infrastructure monitors, and civic channels "
            "that keeps flowing when the internet is down, when spectrum is congested, "
            "or when cloud services fail. The Beehive Protocol provides that — an acoustic "
            "mesh that transmits sensor data with no cellular dependency, no licensed "
            "spectrum, and no central server. In practical terms: air quality data, "
            "flood sensors, infrastructure anomaly reports — all routed through audio "
            "hardware at frequencies that require no regulatory approval to use."
        ),
    },
    {
        "question": "What has been independently validated?",
        "answer": (
            "The system has a convergence test suite — automated checks covering acoustic "
            "encode/decode round-trips, Al-Jabr 286 hash integrity, Beehive handshake "
            "verification, and steganographic payload concealment and recovery. "
            "All tests pass. The steganographic layer produces WAV files that are "
            "statistically indistinguishable from unmodified audio to standard forensic "
            "tools. The hash function produces consistent 286-bit digests verified across "
            "thousands of test vectors. I do not have third-party academic validation yet — "
            "that is part of what the fellowship period would produce."
        ),
    },
    {
        "question": "What is the single biggest technical achievement?",
        "answer": (
            "The Al-Jabr 286 hash function. A custom 286-bit sovereign hash built on a "
            "SHA3-256 base, processed through harmonic layers derived from Quranic verse "
            "structure, producing a digest that functions as both a cryptographic integrity "
            "anchor and a frequency-domain key. It is used system-wide: node identity, "
            "packet signing, phase-key derivation, encryption key generation — all from one "
            "sovereign hash with no external dependency. That design decision makes the "
            "entire system self-authenticating."
        ),
    },
    {
        "question": "How does the economy work?",
        "answer": (
            "VTX — Vortex Token — is earned through participation in the mesh: running a "
            "node, contributing computation, verifying routing packets, participating in "
            "GriDul movement sessions, or engaging with QiSync memory exercises. "
            "Each contribution is logged on the Vortex Ledger with an Al-Jabr 286 hash. "
            "Blueprint Tokens are cryptographic deeds — each one represents a manufacturing "
            "slot in a physical 4000-Series Sovereign Node. The economy is not speculative. "
            "There is no mining pool, no venture round, no inflation schedule. "
            "Value enters the system when real work is done."
        ),
    },
    {
        "question": "Why does it need to be sovereign rather than open-source?",
        "answer": (
            "It is both. The codebase is the system and the system runs on the codebase — "
            "that is public. The sovereignty is not about secrecy; it is about legal "
            "structure. An open-source project owned by no one can be forked, rebranded, "
            "and commercialised by a third party who contributes nothing and captures "
            "everything. Blueprint Tokens and the Vortex Ledger create a legal record of "
            "who built what, when. The sovereign architecture means the people who ran "
            "nodes, wrote code, and held the mesh together cannot be displaced by a company "
            "that shows up after the work is done."
        ),
    },
    {
        "question": "What is the Ask from InteRussia?",
        "answer": (
            "Collaboration on three things: extending the Beehive simulation to model real "
            "urban acoustic propagation conditions — building reflections, ambient noise "
            "floors, multi-path interference; developing AI-assisted frequency routing that "
            "selects transmission parameters based on real-time acoustic environment "
            "analysis; and co-authoring a research paper on acoustic-domain mesh networking "
            "for Smart City applications with Novosibirsk researchers as named co-authors. "
            "The fellowship stipend covers living and working costs in Novosibirsk for the "
            "duration. That is the ask — access to serious peers and a real research "
            "environment."
        ),
    },
    {
        "question": "What happens after Novosibirsk?",
        "answer": (
            "Hardware production begins. The 4000-Series Sovereign Node design is complete "
            "and ready for manufacture — the fellowship period is about hardening the "
            "simulation layer with real-world acoustic data before committing to production. "
            "After Novosibirsk, the first physical nodes ship to Blueprint Token holders. "
            "The mesh goes live. The VTX economy activates in earnest. The InteRussia "
            "research collaboration becomes a standing working group. Novosibirsk is the "
            "last step before the system leaves simulation and becomes infrastructure."
        ),
    },
    {
        "question": "Who else is doing this?",
        "answer": (
            "No one is doing this specific combination. Acoustic mesh networking exists as "
            "an academic field. Steganography is well-studied. Custom hash functions appear "
            "in academic cryptography. But no one has assembled these into a coherent "
            "sovereign infrastructure stack with a native economic layer, a physical "
            "hardware specification, a working codebase, and a convergence test suite that "
            "passes today. The closest analogues are LoRa mesh networks and delay-tolerant "
            "networking research — but those require licensed spectrum or proprietary "
            "hardware. VOID operates on audio, which is unregulated."
        ),
    },
    {
        "question": "What is the current state — is anything actually working?",
        "answer": (
            "The full software stack is working. The Beehive Protocol logic is verified "
            "in simulation — all handshake sequences, routing tables, and phase-key "
            "authentication operate correctly in memory. The Al-Jabr 286 hash is in "
            "production use across every subsystem. The steganographic encoder and decoder "
            "complete successful round-trips on real WAV files. The Flask application "
            "with user authentication, tiered access, VTX ledger, Blueprint Tokens, and "
            "GriDul is live. The 4000-Series hardware specification is documented and "
            "ready for manufacture. What remains is the transition from acoustic simulation "
            "to physical hardware testing — which is what the fellowship period is for."
        ),
    },
    {
        "question": "What does the crystallization methodology mean?",
        "answer": (
            "Crystallization is the name I give to the process of building a system until "
            "it reveals its own shape. You do not design the shape in advance. You follow "
            "each technical decision to its conclusion and observe what pattern emerges. "
            "PROJECT VOID crystallized into seven layers: Ground, Language, Memory, Value, "
            "Community, Healing, Legacy. Those are not categories I imposed — they are what "
            "appeared when I mapped how every component feeds every other component. "
            "The crystallization sentence is the result: one sentence that holds all seven "
            "layers simultaneously without losing any of them. That is the methodology. "
            "Build until it tells you what it is."
        ),
    },
]


def _founder_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if not session.get("is_founder"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated


@founders_room_bp.route("/founders-room")
@_founder_required
def founders_room():
    return render_template(
        "founders_room.html",
        crystallization_sentence=CRYSTALLIZATION_SENTENCE,
        layers=LAYERS,
        connections=CONNECTIONS,
        one_sentence=ONE_SENTENCE,
        three_minutes=THREE_MINUTES,
        interussia_angle=INTERUSSIA_ANGLE,
        qa_pairs=QA_PAIRS,
    )
