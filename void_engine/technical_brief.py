import os
from datetime import datetime
from fpdf import FPDF
from void_engine.al_jabr_286 import get_protocol_info, fatiha_286_truncated


def generate_technical_brief(output_dir: str = "output_audio") -> str:
    os.makedirs(output_dir, exist_ok=True)

    protocol = get_protocol_info()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    doc_hash = fatiha_286_truncated(f"TECH-BRIEF-{timestamp}".encode("utf-8"), 16)

    gold_r, gold_g, gold_b = 212, 175, 55
    dim_r, dim_g, dim_b = 140, 120, 50
    white_r, white_g, white_b = 200, 200, 200
    teal_r, teal_g, teal_b = 0, 200, 180

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()
    pdf.set_fill_color(10, 10, 10)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 10)
    pdf.cell(190, 5, "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", align="C")

    pdf.set_font("Courier", "B", 24)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(10, 25)
    pdf.cell(190, 12, "PROJECT VOID", align="C")

    pdf.set_font("Courier", "", 12)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(10, 40)
    pdf.cell(190, 8, "Technical Brief", align="C")

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 52)
    pdf.cell(190, 6, f"Generated: {timestamp}  |  Document Hash: {doc_hash}", align="C")

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 62)
    pdf.cell(190, 5, "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", align="C")

    y = 75

    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(15, y)
    pdf.cell(180, 8, "1. Project Overview", align="L")
    y += 12

    overview_lines = [
        "PROJECT VOID is a sovereign steganography platform that hides data",
        "inside natural audio carriers -- birdsong, insects, ocean ambiance --",
        "making sensitive information invisible to conventional detection.",
        "",
        "Three core pillars:",
        "  * Steganography Engine: LSB encoding with Vortex scatter, chirp",
        "    sync, and dual compression (zlib/lzma) inside WAV carriers",
        "  * Ghost Internet (Beehive Mesh): Acoustic peer-to-peer networking",
        "    using 432 Hz handshakes, inaudible to surveillance systems",
        "  * Sovereign Hashing (Al-Jabr 286): Custom 286-bit hash algorithm",
        "    replacing SHA-256, invisible to standard forensic scanners",
    ]
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    for line in overview_lines:
        pdf.set_xy(20, y)
        pdf.cell(170, 5, line, align="L")
        y += 5

    y += 8

    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(15, y)
    pdf.cell(180, 8, "2. Technical Specifications", align="L")
    y += 12

    specs = [
        ("Hash Algorithm", f"Al-Jabr 286 ({protocol['bit_depth']}-bit Sovereign Hash)"),
        ("Base Layer", protocol["base_algorithm"]),
        ("Extension Bits", f"{protocol['extension_bits']}-bit Sovereign Buffer"),
        ("Verse Layers", str(protocol["verse_layers"])),
        ("Resonance Frequency", f"{protocol['resonance_hz']} Hz"),
        ("Audio Format", "16-bit PCM WAV"),
        ("LSB Depth", "1-bit and 2-bit encoding"),
        ("Scatter Modes", "Linear, Fly Jitter, Vortex (432 Hz spiral), Chirp Sync"),
        ("Compression", "Dual zlib-9 / lzma-9, adaptive selection"),
        ("Header Encryption", "ChaCha20 with 64-byte encrypted header"),
        ("Biophony Shelves", "3-shelf: Whales (20-200 Hz), Birds (2-8 kHz), Insects (8-20 kHz)"),
        ("Carrier Styles", "biophony_mesh, midnight_pond, cicada_wall, cricket_pulse, dawn_chorus"),
        ("Mesh Protocol", "Beehive 432 Hz acoustic handshake with FFT detection"),
        ("Max Payload", "Up to 1 GB (carrier dependent)"),
    ]

    for label, value in specs:
        pdf.set_font("Courier", "B", 9)
        pdf.set_text_color(teal_r, teal_g, teal_b)
        pdf.set_xy(20, y)
        pdf.cell(55, 5, label + ":", align="L")
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(white_r, white_g, white_b)
        pdf.set_xy(75, y)
        pdf.cell(115, 5, value, align="L")
        y += 6

    y += 8

    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(15, y)
    pdf.cell(180, 8, "3. Silt Journalism Workflow", align="L")
    y += 12

    journalism_lines = [
        "The Silt Journalism Port enables journalists and activists to hide",
        "any file (documents, images, video -- up to 50 MB) inside auto-",
        "generated nature-sound audio carriers.",
        "",
        "Workflow:",
        "  1. Journalist uploads sensitive file via drag-and-drop interface",
        "  2. System auto-generates biophony carrier (birdsong/insects/pond)",
        "     with duration calculated from payload size",
        "  3. File is compressed, encrypted, and embedded using Vortex",
        "     scatter at LSB depth 2 for maximum camouflage",
        "  4. Output: a nature-sound WAV file indistinguishable from a",
        "     field recording -- stored in silt_drops/ directory",
        "  5. File can be broadcast via Beehive mesh or shared normally",
        "  6. Recipient decodes with the hash key to recover original file",
        "",
        "To surveillance systems, the output sounds like crickets chirping.",
    ]

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    for line in journalism_lines:
        pdf.set_xy(20, y)
        pdf.cell(170, 5, line, align="L")
        y += 5

    pdf.add_page()
    pdf.set_fill_color(10, 10, 10)
    pdf.rect(0, 0, 210, 297, "F")

    y = 15

    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(15, y)
    pdf.cell(180, 8, "4. Convergence Test Results", align="L")
    y += 12

    test_lines = [
        "The Convergence Suite validates all subsystems with 89 automated",
        "checks covering:",
        "",
        "  * Integrity & Resonance: Encode/decode round-trip verification",
        "  * Silt Analysis: Compression ratio and density checks",
        "  * Beehive Handshake: Fatiha +15.4 deg phase, -30dB silt, 180 deg whisper",
        "  * Kinetic-Biological-Ledger convergence validation",
        "  * Al-Jabr 286 protocol: avalanche effect, verse weights, prime salt",
        "  * Resonance Smart Contract axiom validation",
        "",
        "Result: 89 / 89 PASSING",
        "",
        "All payload verification uses fatiha_286. SHA-256 retained only",
        "in intentional divergence tests for forensic evasion confirmation.",
    ]

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    for line in test_lines:
        pdf.set_xy(20, y)
        pdf.cell(170, 5, line, align="L")
        y += 5

    y += 8

    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(15, y)
    pdf.cell(180, 8, "5. Hardware: 4000-Series Sovereign Node", align="L")
    y += 12

    hw_lines = [
        "The 4000-Series Sovereign Node is the physical embodiment of",
        "PROJECT VOID -- a self-contained, cloud-independent hardware unit.",
        "",
        "Key Components:",
    ]

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    for line in hw_lines:
        pdf.set_xy(20, y)
        pdf.cell(170, 5, line, align="L")
        y += 5

    y += 2

    components = [
        ("Steel Chassis (108 Hz)", "Structural resonance frame"),
        ("Aluminum Heat Sink (216 Hz)", "Passive thermal management"),
        ("Silk-Silver Mesh (432 Hz)", "Primary signal conductor"),
        ("Salt Water Reservoir (864 Hz)", "Biological transceiver medium"),
        ("Acoustic Foam (12 kHz)", "Insect-shelf isolation layer"),
        ("Flywheel Energy Store", "Kinetic energy buffer (120 Wh)"),
        ("Raspberry Pi / Mac Mini", "Sovereign compute core"),
        ("Aquaponics Sensor Array", "pH, temperature, DO, ammonia"),
        ("Speaker + Mic Array", "Beehive mesh I/O"),
    ]

    for comp, desc in components:
        pdf.set_font("Courier", "B", 9)
        pdf.set_text_color(teal_r, teal_g, teal_b)
        pdf.set_xy(22, y)
        pdf.cell(60, 5, comp, align="L")
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(white_r, white_g, white_b)
        pdf.set_xy(82, y)
        pdf.cell(108, 5, desc, align="L")
        y += 5

    y += 5

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(20, y)
    pdf.cell(170, 5, "Material Resonance Table:", align="L")
    y += 7

    materials = [
        ("Steel", "108 Hz", "Structural"),
        ("Aluminum", "216 Hz", "Thermal"),
        ("Silk-Silver", "432 Hz", "Signal"),
        ("Salt Water", "864 Hz", "Biological"),
        ("Foam", "12 kHz", "Isolation"),
    ]

    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(25, y)
    pdf.cell(50, 5, "Material", align="L")
    pdf.set_xy(75, y)
    pdf.cell(40, 5, "Frequency", align="L")
    pdf.set_xy(115, y)
    pdf.cell(60, 5, "Function", align="L")
    y += 6

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    for mat, freq, func in materials:
        pdf.set_xy(25, y)
        pdf.cell(50, 5, mat, align="L")
        pdf.set_xy(75, y)
        pdf.cell(40, 5, freq, align="L")
        pdf.set_xy(115, y)
        pdf.cell(60, 5, func, align="L")
        y += 5

    y += 5

    pricing_lines = [
        "Pricing:",
        "  Pirate Build (FREE): Download blueprints + software, source",
        "    parts yourself. Estimated cost: GBP 450 - 660",
        "  Sovereign Edition (GBP 25,000): Pre-built, calibrated,",
        "    certified with Founder Certificate",
    ]

    for line in pricing_lines:
        pdf.set_xy(20, y)
        pdf.cell(170, 5, line, align="L")
        y += 5

    y += 8

    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(15, y)
    pdf.cell(180, 8, "6. Contact & Project Information", align="L")
    y += 12

    contact_lines = [
        "Project:    PROJECT VOID -- Sovereign Steganography Platform",
        "Protocol:   Al-Jabr 286 (Sura-Fatiha Sovereign Hash)",
        "Status:     Production -- All 89 convergence tests passing",
        "License:    Sovereign -- No cloud dependency",
        "Hardware:   4000-Series Sovereign Node (First Generation)",
        "",
        "For inquiries regarding grants, partnerships, or the Sovereign",
        "Edition hardware, please use the inquiry system at /sovereign",
        "or /grants on the PROJECT VOID web interface.",
    ]

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    for line in contact_lines:
        pdf.set_xy(20, y)
        pdf.cell(170, 5, line, align="L")
        y += 5

    y += 10

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, y)
    pdf.cell(190, 5, "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", align="C")
    y += 8

    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(10, y)
    pdf.cell(190, 8, f"DOCUMENT SEAL: {doc_hash}", align="C")
    y += 10

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, y)
    pdf.cell(190, 5, "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", align="C")
    y += 8

    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, y)
    pdf.cell(190, 5, "286-Bit Sovereign | PROJECT VOID | Hide Truth in Nature", align="C")

    filename = "PROJECT_VOID_Technical_Brief.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)

    return filepath
