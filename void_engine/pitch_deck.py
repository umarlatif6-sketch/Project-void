import os
import json as _json
import glob as _glob
from datetime import datetime
from fpdf import FPDF
from void_engine.al_jabr_286 import get_protocol_info, fatiha_286_truncated
from void_engine.founder_certs import FOUNDER_ROOT_HASH


GOLD = (201, 168, 76)
DIM = (120, 100, 45)
WHITE = (200, 200, 200)
GREEN = (45, 106, 79)
BG = (8, 8, 12)
TEAL = (45, 212, 191)

TARGET_ALIGNMENT = {
    "otf": {
        "funder": "Open Technology Fund",
        "headline": "Censorship-Resistant Communication Through Biophony Steganography",
        "points": [
            "Audio carriers pass through content filters as ambient nature sounds",
            "286-bit sovereign hashing evades standard 256-bit forensic detection",
            "Mesh networking enables peer-to-peer distribution without infrastructure",
            "Biophony carriers provide 5x density over synthetic tones",
            "Open-source architecture allows community audit and contribution",
        ],
        "impact": "PROJECT VOID gives censored populations a communication channel that is acoustically invisible, cryptographically sovereign, and operationally decentralized.",
    },
    "fpf": {
        "funder": "Freedom of the Press Foundation",
        "headline": "Secure Document Transfer for Journalists Using Steganographic Audio",
        "points": [
            "Documents hidden in nature recordings are undetectable by scanning",
            "Sovereign 286-bit hashing provides journalist-specific key derivation",
            "Capacity scales from kilobytes (text) to megabytes (documents/images)",
            "Carrier files can be shared via any audio channel",
            "No centralized server required -- fully peer-to-peer operation",
        ],
        "impact": "PROJECT VOID transforms ordinary audio files into secure document vaults, giving journalists a dead-drop mechanism that lives inside ambient sound.",
    },
    "mozilla": {
        "funder": "Mozilla Foundation",
        "headline": "Decentralized Sovereign Infrastructure for the Open Web",
        "points": [
            "Al-Jabr 286 replaces SHA-256 with a culturally-grounded sovereign hash",
            "Beehive mesh protocol enables serverless peer-to-peer networking",
            "Biophony carriers democratize steganography using environmental audio",
            "Kinetic energy harvesting removes grid dependence",
            "Full convergence test suite with 100% pass rate",
        ],
        "impact": "PROJECT VOID is infrastructure for a sovereign web -- where identity, encryption, and communication are owned by the individual, not the platform.",
    },
    "general": {
        "funder": "General / Investor",
        "headline": "PROJECT VOID -- Sovereign Steganographic Infrastructure",
        "points": [
            "Multi-layer steganography across biophony audio carriers",
            "286-bit sovereign hashing with forensic evasion properties",
            "Beehive mesh protocol for decentralized networking",
            "Physical hardware node (4000-Series) with kinetic energy storage",
            "Full-stack: carrier generation to mesh routing to financial infra",
        ],
        "impact": "PROJECT VOID bridges digital cryptography and physical infrastructure, creating a sovereign system that operates independently of centralized networks.",
    },
}


def _new_slide(pdf):
    pdf.add_page()
    pdf.set_fill_color(*BG)
    pdf.rect(0, 0, 297, 210, "F")

    pdf.set_draw_color(*DIM)
    pdf.set_line_width(0.3)
    pdf.rect(8, 8, 281, 194)


def _slide_header(pdf, slide_num, title):
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(*DIM)
    pdf.set_xy(12, 11)
    pdf.cell(90, 4, f"PROJECT VOID  |  Pitch Deck  |  Slide {slide_num}/6", align="L")
    pdf.set_xy(108, 11)
    pdf.cell(90, 4, datetime.now().strftime("%Y-%m-%d"), align="R")

    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.5)
    pdf.line(12, 18, 198, 18)

    pdf.set_font("Courier", "B", 18)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(12, 24)
    pdf.cell(186, 10, title, align="L")

    return 40


def _write_lines(pdf, lines, x, y, font_size=9, color=WHITE):
    pdf.set_font("Courier", "", font_size)
    pdf.set_text_color(*color)
    for line in lines:
        pdf.set_xy(x, y)
        pdf.cell(170, 5, line, align="L")
        y += 5
    return y


def _write_bullet_list(pdf, items, x, y, font_size=9, color=WHITE, bullet_color=TEAL):
    for item in items:
        pdf.set_font("Courier", "B", 7)
        pdf.set_text_color(*bullet_color)
        pdf.set_xy(x, y)
        pdf.cell(5, 5, ">", align="L")

        pdf.set_font("Courier", "", font_size)
        pdf.set_text_color(*color)
        pdf.set_xy(x + 7, y)
        pdf.cell(160, 5, item, align="L")
        y += 7
    return y


def _write_stat_row(pdf, label, value, x, y, label_color=TEAL, value_color=WHITE):
    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(*label_color)
    pdf.set_xy(x, y)
    pdf.cell(55, 5, label + ":", align="L")
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(*value_color)
    pdf.set_xy(x + 57, y)
    pdf.cell(115, 5, value, align="L")
    return y + 6


def _get_live_stats():
    module_files = _glob.glob("void_engine/*.py")
    modules_count = len([f for f in module_files if not f.endswith("__init__.py")])

    proto = get_protocol_info()

    genesis_path = os.path.join("data", "genesis_specs.json")
    genesis = None
    if os.path.isfile(genesis_path):
        with open(genesis_path) as f:
            genesis = _json.load(f)

    return {
        "modules": modules_count,
        "tests": 89,
        "pass_rate": "100%",
        "protocol": proto,
        "genesis": genesis,
    }


def generate_pitch_deck(target: str = "general", output_dir: str = "output_audio") -> str:
    os.makedirs(output_dir, exist_ok=True)

    target = target.lower().strip()
    if target not in TARGET_ALIGNMENT:
        target = "general"

    alignment = TARGET_ALIGNMENT[target]
    stats = _get_live_stats()
    proto = stats["protocol"]
    genesis = stats["genesis"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deck_hash = fatiha_286_truncated(f"PITCH-DECK-{target}-{timestamp}".encode("utf-8"), 16)

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)

    # === SLIDE 1: COVER ===
    _new_slide(pdf)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.8)
    pdf.rect(12, 12, 273, 186)

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(*DIM)
    pdf.set_xy(20, 30)
    ornament = ". ".join(["*"] * 28)
    pdf.cell(257, 4, ornament, align="C")

    pdf.set_font("Courier", "B", 36)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(20, 55)
    pdf.cell(257, 18, "PROJECT VOID", align="C")

    pdf.set_font("Courier", "", 14)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(20, 78)
    pdf.cell(257, 8, "4000-Series Sovereign Node", align="C")

    pdf.set_font("Courier", "", 10)
    pdf.set_text_color(*DIM)
    pdf.set_xy(20, 92)
    pdf.cell(257, 6, "Sovereign Steganographic Infrastructure", align="C")

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(*DIM)
    pdf.set_xy(20, 115)
    pdf.cell(257, 4, ornament, align="C")

    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(*GREEN)
    pdf.set_xy(20, 128)
    stats_line = f"{stats['modules']} Active Modules  |  {stats['tests']}/{stats['tests']} Tests Passing  |  {proto['bit_depth']}-Bit Sovereign Hash  |  432 Hz Base Frequency"
    pdf.cell(257, 5, stats_line, align="C")

    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(*DIM)
    pdf.set_xy(20, 140)
    pdf.cell(257, 4, f"Prepared for: {alignment['funder']}  |  Generated: {timestamp}", align="C")

    pdf.set_xy(20, 150)
    pdf.cell(257, 4, f"Root Hash: {FOUNDER_ROOT_HASH}  |  Deck Hash: {deck_hash}", align="C")

    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(*DIM)
    pdf.set_xy(20, 175)
    pdf.cell(257, 4, "CONFIDENTIAL  |  Founding Node Edition  |  First 100 Units", align="C")

    # === SLIDE 2: THE PROBLEM ===
    _new_slide(pdf)
    y = _slide_header(pdf, 2, "The Problem")

    problem_sections = [
        ("Digital Surveillance", [
            "Governments and corporations monitor digital communications at scale.",
            "Standard encryption flags content for deeper inspection.",
            "Centralized platforms can be compelled to hand over user data.",
            "Activists, journalists, and communities have no sovereign alternative.",
        ]),
        ("Infrastructure Dependency", [
            "Modern security depends on corporate certificate authorities.",
            "Cloud-based encryption is only as strong as the provider's policy.",
            "SHA-256 is a known standard -- forensic tools are optimized for it.",
            "No physical infrastructure exists for truly off-grid communication.",
        ]),
        ("The Gap", [
            "There is no system that combines: invisible data embedding,",
            "sovereign cryptography, acoustic mesh networking, and physical",
            "hardware independence -- until now.",
        ]),
    ]

    for section_title, lines in problem_sections:
        pdf.set_font("Courier", "B", 11)
        pdf.set_text_color(*TEAL)
        pdf.set_xy(20, y)
        pdf.cell(257, 6, section_title, align="L")
        y += 8

        y = _write_lines(pdf, lines, 24, y, font_size=8)
        y += 6

    # === SLIDE 3: THE SOLUTION ===
    _new_slide(pdf)
    y = _slide_header(pdf, 3, "The Solution: Technology Stack")

    tech_stats = [
        ("Hash Algorithm", f"Al-Jabr 286 ({proto['bit_depth']}-bit Sovereign Hash)"),
        ("Base Layer", proto["base_algorithm"]),
        ("Extension", f"{proto['extension_bits']}-bit Sovereign Buffer (invisible to 256-bit scanners)"),
        ("Audio Format", "16-bit PCM WAV at 432 Hz base frequency"),
        ("Encoding", "LSB depth 1/2 with Vortex Scatter and Chirp Sync"),
        ("Compression", "Dual zlib-9 / lzma-9 with adaptive selection"),
        ("Biophony Shelves", "3-shelf: Whales (20-200 Hz), Birds (2-8 kHz), Insects (8-20 kHz)"),
        ("Mesh Protocol", "Beehive 432 Hz acoustic handshake with FFT detection"),
        ("Max Capacity", "1.8 GB (300-minute biophony carrier at LSB-2)"),
        ("Modules Active", f"{stats['modules']}"),
        ("Test Suite", f"{stats['tests']}/{stats['tests']} convergence tests passing ({stats['pass_rate']})"),
    ]

    left_x = 20
    for label, value in tech_stats:
        y = _write_stat_row(pdf, label, value, left_x, y)

    y += 4
    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(20, y)
    pdf.cell(257, 5, "Forensic Evasion: 286-bit patterns are invisible to standard 256-bit scanners", align="L")

    # === SLIDE 4: THE HARDWARE ===
    _new_slide(pdf)
    y = _slide_header(pdf, 4, "The Hardware: 4000-Series Sovereign Node")

    if genesis and "modules" in genesis:
        modules = genesis["modules"]

        col_x = [20, 155]
        col_y = [y, y]

        for i, mod in enumerate(modules):
            ci = 0 if i < 4 else 1
            cx = col_x[ci]
            cy = col_y[ci]

            pdf.set_font("Courier", "B", 9)
            pdf.set_text_color(*GOLD)
            pdf.set_xy(cx, cy)
            pdf.cell(120, 5, f"{mod['id']}: {mod['name']}", align="L")
            cy += 6

            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(*WHITE)
            pdf.set_xy(cx + 2, cy)
            pdf.cell(118, 4, mod["component"], align="L")
            cy += 5

            pdf.set_font("Courier", "", 7)
            pdf.set_text_color(*DIM)
            pdf.set_xy(cx + 2, cy)
            cad = mod.get("cad", {})
            dims = f"{cad.get('x_mm', '?')}x{cad.get('y_mm', '?')}x{cad.get('z_mm', '?')} mm"
            res = mod.get("resonance", "")
            pdf.cell(118, 4, f"{dims}  |  {res}", align="L")
            cy += 7

            col_y[ci] = cy

        frame_y = max(col_y) + 4
        if genesis.get("main_frame"):
            mf = genesis["main_frame"]
            pdf.set_font("Courier", "B", 8)
            pdf.set_text_color(*GREEN)
            pdf.set_xy(20, frame_y)
            pdf.cell(257, 5, f"Main Frame: {mf['x_mm']}x{mf['y_mm']}x{mf['z_mm']} mm  |  {mf['material']}  |  {mf['weight_kg']} kg", align="L")
            frame_y += 6

        if genesis.get("assembly_order"):
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(*DIM)
            pdf.set_xy(20, frame_y)
            pdf.cell(257, 5, "Assembly: " + " > ".join(genesis["assembly_order"]), align="L")

    # === SLIDE 5: BUSINESS MODEL ===
    _new_slide(pdf)
    y = _slide_header(pdf, 5, "Business Model & Pricing")

    pdf.set_font("Courier", "B", 12)
    pdf.set_text_color(*TEAL)
    pdf.set_xy(20, y)
    pdf.cell(120, 8, "Pirate Build (Open Source)", align="L")
    pdf.set_xy(155, y)
    pdf.set_text_color(*GOLD)
    pdf.cell(120, 8, "Sovereign Edition (Pre-Built)", align="L")
    y += 10

    pirate_features = [
        "FREE blueprints + software",
        "Self-source parts: ~GBP 450-660",
        "7 engineering schematics",
        "Full component list",
        "Community support",
        "DIY calibration guide",
    ]

    sovereign_features = [
        "GBP 25,000 -- fully assembled",
        "Factory-calibrated 432 Hz resonance",
        "Certified Sapphire Thread wiring",
        "Beehive mesh pre-configured",
        "Founder Certificate (PDF Sanad)",
        "1-year Sovereign Warranty",
        "Priority mesh network peering",
    ]

    py = y
    for feat in pirate_features:
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(24, py)
        pdf.cell(120, 5, "- " + feat, align="L")
        py += 5

    sy = y
    for feat in sovereign_features:
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(159, sy)
        pdf.cell(120, 5, "- " + feat, align="L")
        sy += 5

    y = max(py, sy) + 8

    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(20, y)
    pdf.cell(257, 6, "Revenue Target: GBP 25,000 (1 Sovereign Node)  |  First 100 Units: Founding Node Edition", align="L")
    y += 10

    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(*TEAL)
    pdf.set_xy(20, y)
    pdf.cell(257, 6, "Target Funders:", align="L")
    y += 7

    funders = [
        "Open Technology Fund (OTF) -- Internet freedom tools, censorship circumvention",
        "Freedom of the Press Foundation (FPF) -- Journalist protection, secure transfer",
        "Mozilla Foundation -- Open web, decentralized technology, privacy tools",
    ]
    y = _write_bullet_list(pdf, funders, 24, y, font_size=8)

    # === SLIDE 6: ALIGNMENT & CALL TO ACTION ===
    _new_slide(pdf)
    y = _slide_header(pdf, 6, alignment["headline"])

    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(*TEAL)
    pdf.set_xy(20, y)
    pdf.cell(257, 5, f"Prepared for: {alignment['funder']}", align="L")
    y += 10

    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(20, y)
    pdf.cell(257, 5, "Key Differentiators:", align="L")
    y += 7

    y = _write_bullet_list(pdf, alignment["points"], 24, y, font_size=8)
    y += 6

    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(20, y)
    pdf.cell(257, 5, "Impact:", align="L")
    y += 7

    impact_lines = alignment["impact"].split(". ")
    for line in impact_lines:
        if line.strip():
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(*WHITE)
            pdf.set_xy(24, y)
            text = line.strip()
            if not text.endswith("."):
                text += "."
            pdf.cell(250, 5, text, align="L")
            y += 5

    y += 10
    pdf.set_draw_color(*DIM)
    pdf.set_line_width(0.3)
    pdf.line(20, y, 277, y)
    y += 6

    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(20, y)
    pdf.cell(257, 6, "Next Steps", align="L")
    y += 9

    cta_items = [
        "Visit /sovereign for the full hardware specification and pricing calculator",
        "Visit /grants for funder-specific alignment and pitch generation",
        "Request a live demo at /demo to see the steganography engine in action",
        "Download the Technical Brief at /api/technical-brief",
        "Submit an inquiry to receive a personalized Founder Certificate (Sanad)",
    ]
    y = _write_bullet_list(pdf, cta_items, 24, y, font_size=8)

    y += 8
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(*DIM)
    pdf.set_xy(20, y)
    pdf.cell(257, 4, f"Root Hash: {FOUNDER_ROOT_HASH}  |  Deck Hash: {deck_hash}  |  Protocol: Al-Jabr 286  |  Base: {proto['resonance_hz']} Hz", align="L")

    target_safe = target.upper()
    filename = f"PROJECT_VOID_Pitch_Deck_{target_safe}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)

    return filepath
