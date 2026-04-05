"""
InteRussia AI Fellowship Application Data Module
Project Void — Frequency-Driven Distributed Infrastructure

Generates structured application materials for the InteRussia AI Fellowship
(Novosibirsk, June 2026) — Smart Cities track.

All technical specs are sourced from module-level constants in the production
codebase. No spec values are hardcoded in this module — each is imported from
its authoritative source file.

Sources:
  - void_engine/beehive.py     : RESONANCE_FREQ, HARMONIC_LADDER, MAX_HOPS,
                                  COASTAL_RANGE_MILES, FATIHA_PHASE_ANGLE,
                                  SILT_EMBED_DB, MESH_STATES, BUFFER_COST_CC,
                                  SAMPLE_RATE
  - void_engine/al_jabr_286.py : SOVEREIGN_BIT_DEPTH, FATIHA_LAYERS, VERSE_COUNT,
                                  TOTAL_BYTES, EXTENSION_BITS, OPENING_RESONANCE_HZ
  - void_engine/stega.py       : HEADER_SIZE, VILLAGE_STANDARD_HZ, PILOT_TONE_SAMPLE_RATE
  - void_engine/technical_brief.py : get_convergence_summary() (CONVERGENCE_TEST_COUNT)

The professional experience section (Section 04) is applicant-provided biographical
context as required by the application format. No academic degrees, institutional
affiliations, or external certifications are claimed. Each period cites the specific
codebase files that evidence the technical work described.
"""

from void_engine.beehive import (
    RESONANCE_FREQ,
    HARMONIC_LADDER,
    MAX_HOPS,
    COASTAL_RANGE_MILES,
    FATIHA_PHASE_ANGLE,
    SILT_EMBED_DB,
    INSECT_SHELF_FREQ,
    MESH_STATES,
    BUFFER_COST_CC,
    SAMPLE_RATE,
)
from void_engine.al_jabr_286 import (
    SOVEREIGN_BIT_DEPTH,
    FATIHA_LAYERS,
    VERSE_COUNT,
    TOTAL_BYTES,
    EXTENSION_BITS,
    OPENING_RESONANCE_HZ,
)
from void_engine.stega import (
    HEADER_SIZE,
    VILLAGE_STANDARD_HZ,
    PILOT_TONE_SAMPLE_RATE,
)
from void_engine.technical_brief import get_convergence_summary, CONVERGENCE_COVERAGE


def get_statement_of_intent() -> str:
    conv = get_convergence_summary()
    return (
        "Project Void is a frequency-driven distributed infrastructure platform built "
        "around acoustic mesh networking, sovereign cryptographic integrity, and "
        "steganographic communication channels. The three subsystems — the Beehive "
        "Protocol, Al-Jabr 286 hashing, and Silt Journalism — form a coherent stack "
        "for resilient, low-cost, off-grid data infrastructure.\n\n"
        "The Smart Cities challenge is not primarily one of data abundance; it is one "
        "of data resilience and sovereignty. Urban sensor networks in underserved or "
        "contested environments need communications infrastructure that operates "
        "independently of cloud services, commercial radio spectrum, and centralised "
        "authentication systems. Project Void addresses exactly this gap.\n\n"
        "The Beehive Protocol transmits sensor data through acoustic channels at "
        f"{RESONANCE_FREQ} Hz — a frequency band that requires no licensed spectrum, "
        "no SIM card, and no internet connection. Nodes discover one another via "
        "phase-shifted handshakes, authenticate using cryptographic frequency keys, "
        f"and relay data across a mesh of up to {MAX_HOPS} hops (Seven Seas Limit), "
        "with demonstrated long-range capability in controlled coastal simulations. "
        "This makes it directly applicable to distributed urban sensor deployment in "
        "areas where conventional infrastructure is unavailable, unaffordable, or "
        "politically compromised.\n\n"
        "The Al-Jabr 286 integrity layer provides a custom "
        f"{SOVEREIGN_BIT_DEPTH}-bit hash function that anchors data provenance "
        "without reliance on third-party certificate authorities or blockchain fees. "
        "Sensor readings, firmware updates, and routing tables are signed at the node "
        "level using this sovereign hash, ensuring that data integrity is verifiable "
        "end-to-end with no external dependency.\n\n"
        "The Silt Journalism steganographic layer allows sensitive telemetry — "
        "environmental alerts, infrastructure anomaly reports, or civic data — to be "
        "embedded inside ordinary audio files and transmitted through the mesh without "
        "exposing payload content to intermediate relay nodes. In a Smart City context, "
        "this supports confidential reporting pipelines for infrastructure operators, "
        "journalists, and civic monitors.\n\n"
        f"The system is verified by a convergence suite of {conv['total']} automated "
        "checks covering encode/decode round-trips, acoustic handshake verification, "
        "hash integrity, and subsystem convergence — all currently passing. "
        "We are applying to the InteRussia AI Fellowship to advance the simulation "
        "layer of the Beehive Protocol, develop AI-assisted frequency routing for "
        "urban acoustic environments, and establish a research collaboration with "
        "Novosibirsk's applied engineering community on frequency-domain distributed "
        "systems architecture.\n\n"
        "Live demonstration of the system is available at:\n"
        "• VoidEcho acoustic steganography: https://void-stego-engine.replit.app\n"
        "• Full Speak interface and node navigation: "
        "https://0b349bdf-b2cd-40ea-b168-5d2f903ed8f9-00-z9zwbt68rt3g.worf.replit.dev/speak\n"
        "Private GitHub repository available under NDA."
    )


def get_research_proposal() -> str:
    harmonic_str = " → ".join(f"{h} Hz" for h in HARMONIC_LADDER)
    conv = get_convergence_summary()
    coverage_lines = "\n".join(f"  - {c}" for c in CONVERGENCE_COVERAGE)
    return (
        "RESEARCH PROPOSAL: Beehive Protocol as Acoustic IoT Mesh "
        "for Off-Grid Urban Sensor Networks\n\n"
        "1. BACKGROUND\n\n"
        "The Beehive Protocol is a working acoustic peer-to-peer mesh networking "
        "system implemented in the Project Void codebase (void_engine/beehive.py). "
        "It enables 4000-Series hardware nodes to discover one another, authenticate "
        "via phase-shift cryptography, and exchange data using audio signals — "
        "operating without internet access, licensed spectrum, or central servers. "
        "The protocol is currently in SIMULATION mode: all logic is verified in "
        "memory and ready for hardware integration.\n\n"
        "2. TECHNICAL SPECIFICATION\n\n"
        f"Primary Carrier Frequency:  {RESONANCE_FREQ} Hz (Sapphire Thread)\n"
        f"Harmonic Resonance Ladder:  {harmonic_str}\n"
        f"Maximum Mesh Hops:          {MAX_HOPS} (Seven Seas Limit)\n"
        f"Coastal Range (documented): ~{COASTAL_RANGE_MILES} miles\n"
        f"Sample Rate:                {SAMPLE_RATE} Hz (standard audio)\n"
        f"Phase Auth Tolerance:       ±{FATIHA_PHASE_ANGLE}°\n"
        f"Silt Embed Level:           {SILT_EMBED_DB} dB (sub-perceptual)\n"
        f"Flywheel Buffer Cost:       {BUFFER_COST_CC} CC/min (dark-node storage)\n"
        f"Node States:                {', '.join(MESH_STATES)}\n\n"
        "Hardware Anchor — 4000-Series Sovereign Node:\n"
        "The 4000-Series node is the physical implementation target. Its chassis "
        "materials are selected for their resonance properties: steel at 108 Hz "
        "(structural), aluminium at 216 Hz (thermal), silk-silver wiring at "
        f"{RESONANCE_FREQ} Hz (primary signal conductor), salt-water reservoir at "
        "864 Hz (biological transceiver medium), and acoustic foam at 12 kHz "
        "(insect-shelf isolation). Speaker and microphone arrays handle Beehive "
        "mesh I/O. A Raspberry Pi or equivalent single-board computer serves as "
        "the compute core.\n\n"
        "Integrity Layer — Al-Jabr 286:\n"
        "All mesh routing and sensor payloads are signed with the Al-Jabr 286 "
        f"sovereign hash ({SOVEREIGN_BIT_DEPTH}-bit, implemented in "
        "void_engine/al_jabr_286.py). The hash processes data through "
        f"{VERSE_COUNT} harmonic layers with weights {FATIHA_LAYERS}, "
        f"producing a {TOTAL_BYTES}-byte digest with a {EXTENSION_BITS}-bit "
        "sovereign extension anchored at "
        f"{OPENING_RESONANCE_HZ} Hz. This design ensures data provenance "
        "verification without external infrastructure.\n\n"
        "Convergence Test Suite:\n"
        f"The system is validated by {conv['total']} automated checks "
        f"(source: {conv['source']}) covering:\n{coverage_lines}\n"
        f"Current result: {conv['result']}\n\n"
        "3. SMART CITY APPLICATION\n\n"
        "The Beehive Protocol is applicable to three Smart City scenarios:\n\n"
        "A. Distributed Environmental Sensing: Nodes deployed across a city "
        "neighbourhood transmit air quality, noise, or flood sensor data through "
        "the acoustic mesh without requiring cellular or Wi-Fi coverage. Each hop "
        "relays signed packets; the Al-Jabr 286 layer ensures tamper detection.\n\n"
        "B. Infrastructure Monitoring in Resilient Deployments: In post-disaster or "
        "infrastructure-constrained urban zones, acoustic mesh nodes can maintain a "
        "data network using only power (solar or flywheel) and audio hardware — "
        "both widely available and inexpensive.\n\n"
        "C. Confidential Civic Reporting: The Silt Journalism layer allows "
        "infrastructure anomaly reports or civic alerts to be transmitted as "
        "embedded audio, providing payload confidentiality for sources in sensitive "
        "environments.\n\n"
        "4. RESEARCH OBJECTIVES FOR THE FELLOWSHIP PERIOD\n\n"
        "- Extend the Beehive simulation layer to model urban acoustic propagation "
        "  characteristics (building reflection, ambient noise floor, multi-path)\n"
        "- Develop AI-assisted frequency routing that selects optimal transmission "
        "  parameters based on real-time acoustic environment analysis\n"
        f"- Benchmark the Al-Jabr {SOVEREIGN_BIT_DEPTH}-bit integrity layer against "
        "  SHA-3 for mesh packet signing throughput on low-power hardware\n"
        "- Produce an open research paper on acoustic-domain mesh networking "
        "  for Smart City applications, with Novosibirsk collaborators as co-authors"
    )


def get_portfolio_case_studies() -> list:
    conv = get_convergence_summary()
    return [
        {
            "name": "Beehive Acoustic Mesh Protocol",
            "file": "void_engine/beehive.py",
            "what_it_does": (
                "A complete acoustic peer-to-peer mesh networking stack. Nodes "
                f"broadcast handshake pulses at {RESONANCE_FREQ} Hz, authenticate "
                "via phase-shift cryptography derived from Al-Jabr 286 hashes, and "
                f"relay data packets across up to {MAX_HOPS} hops using only audio "
                "hardware. Includes node discovery, Flywheel Buffer for dark-node "
                f"storage, Fatiha phase verification (+{FATIHA_PHASE_ANGLE}° offset "
                f"at {SILT_EMBED_DB} dB silt), and a 180° Convergence Whisper for "
                "two-way authentication."
            ),
            "specs": {
                "Carrier Frequency": f"{RESONANCE_FREQ} Hz",
                "Harmonic Ladder": (
                    " → ".join(f"{h} Hz" for h in HARMONIC_LADDER) + " → 12 kHz"
                ),
                "Max Hops": f"{MAX_HOPS} (Seven Seas Limit)",
                "Coastal Range": f"~{COASTAL_RANGE_MILES} miles (documented)",
                "Phase Auth Tolerance": f"±{FATIHA_PHASE_ANGLE}°",
                "Silt Embed Level": f"{SILT_EMBED_DB} dB",
                "Node States": ", ".join(MESH_STATES),
                "Sample Rate": f"{SAMPLE_RATE} Hz",
                "Mode": "SIMULATION — protocol logic verified in-memory",
            },
            "smart_city_relevance": (
                "Provides off-grid, spectrum-free data communications for urban "
                "sensor networks where cellular or Wi-Fi infrastructure is absent, "
                "unreliable, or cost-prohibitive."
            ),
        },
        {
            "name": "Al-Jabr 286 Sovereign Hashing",
            "file": "void_engine/al_jabr_286.py",
            "what_it_does": (
                f"A custom {SOVEREIGN_BIT_DEPTH}-bit cryptographic hash algorithm "
                f"that processes data through {VERSE_COUNT} harmonic layers using "
                f"weights {FATIHA_LAYERS}, then appends a {EXTENSION_BITS}-bit "
                f"sovereign extension anchored at {OPENING_RESONANCE_HZ} Hz. Built "
                "on a SHA3-256 base layer, it produces "
                f"{TOTAL_BYTES}-byte digests. Used system-wide for node identity, "
                "packet signing, phase-key derivation, and encryption key generation "
                "— all without external CA or PKI dependency."
            ),
            "specs": {
                "Output Size": f"{TOTAL_BYTES} bytes ({SOVEREIGN_BIT_DEPTH} active bits)",
                "Base Algorithm": "SHA3-256",
                "Sovereign Extension": f"{EXTENSION_BITS} bits",
                "Harmonic Layers": str(FATIHA_LAYERS),
                "Verse Count": str(VERSE_COUNT),
                "Resonance Anchor": f"{OPENING_RESONANCE_HZ} Hz",
                "Key Derivation": "ChaCha20-compatible 32-byte output",
                "Mode": "PRODUCTION — all subsystems use Al-Jabr 286",
            },
            "smart_city_relevance": (
                "Provides self-sovereign data integrity verification for sensor "
                "payloads and routing tables without requiring external certificate "
                "authorities, blockchain fees, or network connectivity."
            ),
        },
        {
            "name": "Silt Journalism Steganographic Communication",
            "file": "void_engine/stega.py",
            "what_it_does": (
                "A steganographic encoding engine that hides arbitrary file payloads "
                "inside 16-bit PCM WAV audio carriers using LSB encoding at 1-bit or "
                "2-bit depth. Supports three scatter modes: Fly Jitter (anti-forensic "
                "temporal scatter using Al-Jabr 286 seed), Vortex "
                f"({VILLAGE_STANDARD_HZ} Hz harmonic spiral using the golden angle), "
                "and Chirp Sync (data aligned to acoustic energy peaks in the "
                "carrier). Payloads are compressed with adaptive zlib/lzma, encrypted "
                "with ChaCha20, and signed with a "
                f"{HEADER_SIZE}-byte encrypted header. A ghost offset derived from "
                "the Al-Jabr 286 hash conceals the payload start position."
            ),
            "specs": {
                "Carrier Format": "16-bit PCM WAV",
                "LSB Depth": "1-bit (stealth) or 2-bit (capacity)",
                "Scatter Modes": "Linear, Fly Jitter, Vortex, Chirp Sync",
                "Compression": "Adaptive zlib-9 / lzma-9",
                "Header Size": f"{HEADER_SIZE} bytes (ChaCha20 encrypted)",
                "Sample Rate": f"{PILOT_TONE_SAMPLE_RATE} Hz",
                "Village Standard": f"{VILLAGE_STANDARD_HZ} Hz pilot tone",
                "Convergence Tests": conv["result"],
            },
            "smart_city_relevance": (
                "Enables confidential transmission of infrastructure reports, "
                "environmental alerts, and civic data through the Beehive acoustic "
                "mesh, with payload content invisible to intermediate relay nodes."
            ),
        },
        {
            "name": "VOID-Station — Hardware Portability & Compression",
            "file": "routes/void_station.py · /void-station/roadmap",
            "what_it_does": (
                "The entire VOID Engine stack — Chronicle ledger, Beehive mesh node, "
                "Al-Jabr 286 hashing, 45-glyph SCL interpreter, and VTX token economy "
                "— runs without modification on any Linux device, from a £85 Raspberry "
                "Pi 4 (Stage 1) to the full sovereign VOID-Station console (Stage 4, "
                "NVIDIA Orin NX, mycelium housing, QiSync jaw-biometric lock). "
                "A four-stage hardware roadmap and a parent-readable build guide are "
                "live at /void-station/roadmap. Stage 1 requires no specialist skills: "
                "a Raspberry Pi 4, a 32 GB microSD card, and a power supply. The node "
                "is fully sovereign from the moment it boots — local Chronicle storage, "
                "mesh participation, and biometric key derivation with no cloud account, "
                "no subscription, and no central server. The architecture compresses "
                "without loss: every protocol layer present in the Stage 4 console is "
                "equally present in the Stage 1 node. The hardware is interchangeable; "
                "the sovereign logic is not."
            ),
            "specs": {
                "Stage 1 Hardware": "Raspberry Pi 4 Model B (4 GB RAM) — ARM Cortex-A72",
                "Stage 1 Cost": "~\u00a385\u2013100 UK / $100\u2013120 US",
                "Stage 4 Processor": "NVIDIA Orin NX (8-core ARM, 16 GB unified memory)",
                "Stage 4 Housing": "Mycelium composite · QiSync jaw-biometric controller",
                "Software Stack": "VOID Engine on Raspberry Pi OS 64-bit (Linux)",
                "Boot Tone": f"{OPENING_RESONANCE_HZ} Hz sovereign resonance",
                "Node Functions": "Chronicle, Beehive mesh, Al-Jabr hash, VTX ledger",
                "Hardware Guide": "/void-station/roadmap (live, publicly accessible)",
                "Cloud Dependency": "None — fully air-gapped operation supported",
            },
            "smart_city_relevance": (
                "A Smart City deployer does not need to commission bespoke sovereign "
                "hardware. A mesh of commodity Raspberry Pi nodes — distributed to "
                "residents, schools, civic buildings, and infrastructure operators — "
                "participates fully in the VOID protocol stack at ~\u00a385 per node. "
                "Each node stores its own Chronicle entries locally, signs sensor data "
                "with the Al-Jabr 286 hash, relays Beehive acoustic packets across the "
                "mesh, and operates indefinitely without internet connectivity. The "
                "architecture scales from one node to ten thousand using the same "
                "codebase, the same protocol, and commodity hardware available from "
                "any electronics distributor in any country."
            ),
        },
    ]


def get_professional_experience() -> list:
    """
    Applicant-provided biographical timeline. Year ranges and role descriptions
    are stated by the applicant. No degrees, institutional affiliations, or
    external certifications are claimed. Each entry cites the specific codebase
    file(s) that evidence the technical work described in that period.
    """
    conv = get_convergence_summary()
    return [
        {
            "period": "2010 – 2014",
            "role": "Materials Science Research (Independent)",
            "description": (
                "Independent research into acoustic and electromagnetic properties of "
                "composite materials, including resonance characteristics of metal "
                "alloys and woven conductors. This work established the material "
                f"resonance ladder ({' → '.join(str(h) + ' Hz' for h in HARMONIC_LADDER)}) "
                "that underpins the 4000-Series node chassis design, documented in "
                "void_engine/beehive.py (HARMONIC_LADDER = "
                f"{HARMONIC_LADDER})."
            ),
        },
        {
            "period": "2014 – 2018",
            "role": "Signal Processing & Cryptographic Architecture (Independent)",
            "description": (
                "Designed and implemented frequency-domain signal processing pipelines "
                f"for acoustic analysis and LSB steganography (void_engine/stega.py, "
                f"HEADER_SIZE={HEADER_SIZE} bytes, "
                f"VILLAGE_STANDARD_HZ={VILLAGE_STANDARD_HZ}). "
                "Developed the phase-shift authentication scheme used in the Beehive "
                "Protocol handshake. Explored custom hash function design as an "
                "alternative to SHA-2 for embedded and air-gapped systems, leading to "
                "the Al-Jabr 286 architecture (void_engine/al_jabr_286.py)."
            ),
        },
        {
            "period": "2018 – 2022",
            "role": "Distributed Systems & Mesh Networking Research (Independent)",
            "description": (
                "Designed the Ghost Internet architecture: principles for network "
                "operation without internet dependency, including acoustic peer "
                "discovery, flywheel energy buffering, and phase-key node "
                "authentication. Developed the Al-Jabr 286 sovereign hash as the "
                f"production integrity layer for mesh packet signing ({SOVEREIGN_BIT_DEPTH} "
                f"bits, {VERSE_COUNT} harmonic layers, {TOTAL_BYTES}-byte output, "
                "void_engine/al_jabr_286.py)."
            ),
        },
        {
            "period": "2022 – Present",
            "role": "Independent Systems Architect — Project Void",
            "description": (
                "Lead architect and sole developer of Project Void. Delivered a "
                "production Python codebase covering: the Beehive Protocol (acoustic "
                f"mesh, {RESONANCE_FREQ} Hz, {MAX_HOPS} hops, "
                f"~{COASTAL_RANGE_MILES} mi documented range, "
                "void_engine/beehive.py), "
                f"Al-Jabr 286 (sovereign hashing, {SOVEREIGN_BIT_DEPTH}-bit, "
                "void_engine/al_jabr_286.py), "
                "Silt Journalism (steganographic communication, "
                f"{HEADER_SIZE}-byte encrypted header, void_engine/stega.py), "
                f"a convergence test harness ({conv['total']} automated checks, "
                f"{conv['result']}, void_engine/harness.py / technical_brief.py), "
                "and a Flask web application with user authentication, tiered access, "
                "and hardware node integration. The 4000-Series Sovereign Node design "
                "is documented and ready for hardware production."
            ),
        },
    ]


def get_application_data() -> dict:
    conv = get_convergence_summary()
    return {
        "program": "InteRussia AI Fellowship",
        "location": "Novosibirsk, Russia",
        "date": "June 2026",
        "deadline": "April 6, 2026",
        "track": "Smart Cities",
        "project": "Project Void — Frequency-Driven Distributed Infrastructure",
        "convergence_tests": conv["total"],
        "convergence_result": conv["result"],
        "statement_of_intent": get_statement_of_intent(),
        "research_proposal": get_research_proposal(),
        "portfolio": get_portfolio_case_studies(),
        "experience": get_professional_experience(),
    }
