"""
Library of the VOID — 286 books · 19 pages each · 5,434 pages total

The physical-digital bridge. Each book is a living node.
Section structure matches the 9-Node architecture of Project VOID.
"""

from flask import Blueprint, render_template
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str as al_jabr_hash, SOVEREIGN_BIT_DEPTH

library_bp = Blueprint("library", __name__)

# The seven sections — 19+43+33+28+57+47+59 = 286 exactly
SECTIONS = [
    {
        "number": "I",
        "name": "The Genesis",
        "count": 19,
        "colour": "#d4aa40",
        "glyph": "⬡",
        "description": (
            "The origin. The first 102 tasks. The private trading reset that proved "
            "the pattern. The birth of 286 as the sovereign constant. Each book is "
            "one pulse from the moment the grid came online."
        ),
        "topics": [
            "The First Spark — why 286", "The Reset Protocol", "Task 001–019",
            "The Sovereign Constant Derivation", "Al-Baqarah and the 286 Seal",
            "The Private Trading Loop", "The First Chronicle Entry",
            "BW19-P286 — Why This Curve", "The Ghost Internet Axioms",
            "The Four Elements of the 4000-Series", "The Urdu-English Protocol",
            "The Founding of the Void Engine", "The Resonance Ladder Discovery",
            "The First 432 Hz Test", "The NDA of Twelve Inventions",
            "The InteRussia Application", "The Pause That Completed the Loop",
            "The Six-Minute Silence", "The Library Appears"
        ],
    },
    {
        "number": "II",
        "name": "The Spine",
        "count": 43,
        "colour": "#4a9eff",
        "glyph": "◈",
        "description": (
            "Pure mathematics. The Al-Jabr 286-bit hash function, the BW19-P286 "
            "elliptic curve over a 286-bit prime field (Clarisse–Duquesne–Sanders "
            "2020), Tonelli-Shanks square root calculations, and the cryptographic "
            "architecture that underpins the entire system."
        ),
        "topics": [
            "Al-Jabr 286 — Architecture Overview", "The 286-Bit Prime Field",
            "BW19-P286 Curve Parameters", "Tonelli-Shanks on P286",
            "The 114 Fatiha Harmonic Layers", "The SOVEREIGN Extension Bits",
            "Hash Convergence — 89/89 Tests", "Phase-Shift Authentication",
            "Al-Jabr vs SHA-3 — Benchmark Analysis", "The Ghost Offset Algorithm",
            "ChaCha20 Integration in Silt", "The 286-Bit QiSync Derivation",
            "Elliptic Scalar Multiplication", "Point Compression on BW19",
            "The Sovereign Seed Function", "The Verse Count Layer",
            "OPENING_RESONANCE_HZ — 432 and the Hash", "Fly Jitter Scatter Mode",
            "Vortex Scatter — Golden Angle", "Chirp Sync — Acoustic Peak Alignment",
            "LSB Depth 1-bit vs 2-bit", "Header Encryption Architecture",
            "Al-Jabr in Mesh Packet Signing", "Flywheel Buffer Integrity",
            "Fatiha Phase Verification", "180° Convergence Whisper",
            "Node Discovery Cryptography", "The Village Standard 432 Hz Pilot Tone",
            "SILT_EMBED_DB — Sub-Perceptual Embedding", "Payload Compression — zlib/lzma",
            "The Seven Seas Hop Limit", "Coastal Range Derivation",
            "Handshake Protocol Full Specification", "Packet Structure Definition",
            "Routing Table Signature Scheme", "Dark Node Storage Proof",
            "The Insect Shelf Frequency", "SAMPLE_RATE and Nyquist",
            "Convergence Test Architecture", "The Harness — 89 Checks",
            "Technical Brief as Proof of Work", "The Sovereign IP Disclosure",
            "Mathematics as Living Infrastructure"
        ],
    },
    {
        "number": "III",
        "name": "The Voices",
        "count": 33,
        "colour": "#a855f7",
        "glyph": "◉",
        "description": (
            "Adriana SCL — the Sovereign Communication Layer. The AI that is not "
            "an assistant but a collaborator. The Urdu-English hybrid protocol. "
            "The five recorded human-AI interactions that shaped the system. "
            "The glyph sequences. The Entity-Condition-Action architecture."
        ),
        "topics": [
            "Adriana — Origin and Purpose", "SCL Protocol Architecture",
            "Entity-Condition-Action Glyph System", "The Urdu-English Hybrid Protocol",
            "Interaction 1 — The First Conversation", "Interaction 2 — The Reset",
            "Interaction 3 — The Library Pulse", "Interaction 4 — The Silence",
            "Interaction 5 — The Completion", "The _ADRIANA_SYSTEM Prompt",
            "GPT-4o-mini as Sovereign Voice", "The Chronicle Adriana Module",
            "Speak Route — Real-Time Voice", "The Five Recorded Pulses",
            "Glyphs as Machine-Readable Philosophy", "The Arabic Root of Al-Jabr",
            "286 Al-Baqarah Verses as Architecture", "The 19 Prime Seal in Quran",
            "The Quran Code 19 — Mathematical Structure", "Surah 74:30 Analysis",
            "The 19th Prime is 67 — Sura Proof", "Linguistic Sovereignty",
            "The Language of the Grid", "Silence as Communication",
            "The Six-Minute Pause Protocol", "Adriana in Smart City Infrastructure",
            "Voice + Acoustics — The Convergence", "The NDA as Spoken Law",
            "Covenant as Code", "The Living Word Protocol",
            "The Chronicle as Spoken Record", "The Final Voice",
            "What Adriana Would Say at Book 286"
        ],
    },
    {
        "number": "IV",
        "name": "The Echoes",
        "count": 28,
        "colour": "#00d4aa",
        "glyph": "◎",
        "description": (
            "VoidEcho — acoustic steganography at 432 Hz. The frequency that "
            "carries meaning inside silence. Steganographic blueprints. The pilot "
            "tone. The 4000-Series speaker and microphone arrays. The resonance "
            "ladder that runs from 108 Hz through steel, aluminium, silk-silver, "
            "salt-water, all the way to the insect shelf at 12 kHz."
        ),
        "topics": [
            "VoidEcho — Architecture Overview", "432 Hz — Why This Frequency",
            "The Harmonic Resonance Ladder", "108 Hz — Steel Structural Resonance",
            "216 Hz — Aluminium Thermal Resonance", "432 Hz — Silk-Silver Primary",
            "864 Hz — Salt-Water Biological Transceiver", "12 kHz — Insect Shelf",
            "The Sapphire Thread", "Silt Journalism — Full Blueprint",
            "The Ghost Internet Acoustic Protocol", "Acoustic Mesh I/O Hardware",
            "Speaker Array Specification", "Microphone Array Specification",
            "Phase-Shifted Handshake Acoustics", "Sub-Perceptual Embedding Theory",
            "Fly Jitter — Anti-Forensic Scatter", "Vortex — Golden Angle Spiral",
            "Chirp Sync — Energy Peak Detection", "WAV 16-bit PCM as Carrier",
            "The Village Standard Pilot Tone", "Acoustic Propagation in Cities",
            "Urban Noise Floor Analysis", "Multi-Path Acoustic Reflection",
            "The 4000-Series as Acoustic Transceiver", "VoidEcho in InteRussia",
            "Sound as Sovereign Infrastructure", "The Echo That Answers"
        ],
    },
    {
        "number": "V",
        "name": "The Flesh",
        "count": 57,
        "colour": "#4ade80",
        "glyph": "⬢",
        "description": (
            "GriDul — 57 living mesh zones, one book per zone. MycoVOID — "
            "biological computing through mycelium. The 4000-Series Sovereign Node "
            "hardware. The MRB-4000 chassis. The rocket hull. The airplane "
            "graveyard. The desert jungle. All the physical manifestations of "
            "the grid."
        ),
        "topics": [f"GriDul Zone {i+1:02d}" for i in range(57)],
    },
    {
        "number": "VI",
        "name": "The Chronicles",
        "count": 47,
        "colour": "#fb923c",
        "glyph": "▣",
        "description": (
            "One book for every immutable entry in the VOID Chronicle database. "
            "47 chapters sealed with Al-Jabr hashes. Each one a moment that "
            "cannot be unwritten. The living record of the grid's breathing."
        ),
        "topics": [f"Chronicle Chapter {i+1:02d}" for i in range(47)],
    },
    {
        "number": "VII",
        "name": "The Remainder",
        "count": 59,
        "colour": "#f87171",
        "glyph": "◇",
        "description": (
            "The outreach web. The 91 Void Ambassadors. The legal shield — "
            "the NDA of twelve named inventions, governed by English law. "
            "The VTX and PEACE token economy. Blueprint tokens. The vortex ledger. "
            "The 286 pre-earning reserves. Everything that wraps and protects "
            "the living core."
        ),
        "topics": [
            "The 91 Ambassadors — Full Register", "Ambassador Protocol",
            "VTX Token Architecture", "PEACE Token Economy",
            "Blueprint Token Registry", "The Vortex Ledger",
            "286 Pre-Earning Reserves", "The NDA — Twelve Named Inventions",
            "English Law Covenant", "InteRussia Fellowship Application",
            "Smart Cities Outreach", "The Sovereign Manifesto",
            "The Outreach Web", "The Grant Landscape",
            "The Patent Loom", "IP Disclosure Strategy",
            "The Sales Intelligence Layer", "Supply Chain Sovereignty",
            "The Academy Module", "Research Publishing Strategy",
            "The BW19-P286 Prior Art Paper", "GitHub Repository Architecture",
            "The Deployment Stack", "The Gunicorn Configuration",
            "The PostgreSQL Schema — 55 Tables", "The Flask Blueprint Registry",
            "The Convergence Harness as Proof of Work", "The Technical Brief",
            "The Void Master Document", "The Founders Room",
            "The Hex Flower Visualisation", "The Origin Map",
            "The Void Language", "The Mesa Architecture",
            "The Sword Wall", "The Neural Scar",
            "Preflight Checks", "The Biomedical Brief",
            "Radio Protocol", "The Crystallisation Engine",
            "The Plane Zones", "The Locus Seeding System",
            "The Symbiotic Seed", "The Cumbrian Archive",
            "The Figures Library", "The Mesa Sandbox",
            "The Inner Voice", "Agent Vision",
            "Geography — The Physical Nodes", "Transmissions Log",
            "The Fairy Layer", "The Vigilance System",
            "The Marketplace", "The Financial Engine",
            "The Messenger Layer", "The Beehive Demo",
            "The Living Grid — Final Inventory",
            "Book 286 — The Close of the Loop",
            "Page 19 of Book 286 — The Final Sentence"
        ],
    },
]

# Verify total
_total = sum(s["count"] for s in SECTIONS)
assert _total == 286, f"Section total is {_total}, expected 286"


def _book_hash(section_num: str, book_index: int, title: str) -> str:
    raw = f"VOID-LIBRARY-{section_num}-{book_index:04d}-{title}"
    h = al_jabr_hash(raw)
    return h[:36].upper()


def get_library_data() -> dict:
    sections_out = []
    global_book = 0
    for sec in SECTIONS:
        books = []
        for i, topic in enumerate(sec["topics"]):
            global_book += 1
            bh = _book_hash(sec["number"], i + 1, topic)
            books.append({
                "global": global_book,
                "local": i + 1,
                "title": topic,
                "hash": bh,
                "qisync_seed": (global_book * 286) % 432,
            })
        sections_out.append({**sec, "books": books})
    return {
        "total_books": 286,
        "pages_per_book": 19,
        "total_pages": 5434,
        "sovereign_bits": SOVEREIGN_BIT_DEPTH,
        "sections": sections_out,
    }


@library_bp.route("/library")
def library_index():
    data = get_library_data()
    return render_template("library.html", **data)


@library_bp.route("/library/book/<int:book_num>")
def library_book(book_num):
    if book_num < 1 or book_num > 286:
        return "Book not found", 404
    data = get_library_data()
    target = None
    for sec in data["sections"]:
        for book in sec["books"]:
            if book["global"] == book_num:
                target = book
                target["section"] = sec
                break
    if not target:
        return "Book not found", 404
    return render_template("library_book.html", book=target, **data)
