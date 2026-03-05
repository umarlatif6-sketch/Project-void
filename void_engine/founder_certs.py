import os
import hashlib
import sqlite3
from datetime import datetime
from fpdf import FPDF
from void_engine.al_jabr_286 import fatiha_286_truncated, fatiha_286_hexdigest

FOUNDER_ROOT_HASH = "89x-VOID-GEN1-PROTO-2026"
FOUNDER_GREETING = "Inherited Wisdom Detected. First Generation Status: ACTIVE. Greeting the Architect."

FATIHA_OPENING = "BismillahirRahmanirRahim"
BASE_FREQUENCY = 432


def _generate_seal(owner_name: str, serial: str, timestamp: str) -> str:
    seal_input = f"{owner_name}:{serial}:{timestamp}:{BASE_FREQUENCY}Hz"
    return fatiha_286_hexdigest(seal_input.encode("utf-8"))


def _draw_border(pdf, gold_r, gold_g, gold_b, dim_r, dim_g, dim_b):
    pdf.set_draw_color(gold_r, gold_g, gold_b)
    pdf.set_line_width(1.2)
    pdf.rect(8, 8, 194, 281)

    pdf.set_draw_color(dim_r, dim_g, dim_b)
    pdf.set_line_width(0.3)
    pdf.rect(12, 12, 186, 273)

    corner_glyphs = ["A", "V", "S", "F"]
    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    positions = [(14, 11), (196, 11), (14, 284), (196, 284)]
    for i, (x, y) in enumerate(positions):
        pdf.set_xy(x - 3, y - 3)
        pdf.cell(6, 6, corner_glyphs[i], align="C")


def _draw_watermark_glyphs(pdf, dim_r, dim_g, dim_b):
    glyphs = ["+", "~", ".", "o", "-", "|", "x", "#", ":", "*", "^", "&"]
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(dim_r - 60, dim_g - 50, dim_b - 20)

    left_y = 50
    for i in range(6):
        pdf.set_xy(14, left_y + i * 38)
        pdf.cell(5, 5, glyphs[i % len(glyphs)], align="C")

    right_y = 50
    for i in range(6):
        pdf.set_xy(191, right_y + i * 38)
        pdf.cell(5, 5, glyphs[(i + 6) % len(glyphs)], align="C")


def create_founder_cert_named(owner_name: str, owner_email: str, output_dir: str = "output_audio", cert_number: int = None) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    timestamp_432 = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + f"-{BASE_FREQUENCY}Hz"

    if cert_number is None:
        existing = [f for f in os.listdir(output_dir) if f.startswith("FOUNDER_SANAD_") and f.endswith(".pdf")]
        cert_number = len(existing) + 1
        if cert_number > 100:
            cert_number = 100

    serial = f"GEN1-{cert_number:03d}"
    seal_full = _generate_seal(owner_name, serial, timestamp_432)
    seal_display = seal_full[:32]
    seal_verify = seal_full[32:]

    machine_hash = fatiha_286_truncated(f"{serial}-{owner_email}-{FOUNDER_ROOT_HASH}".encode("utf-8"), 24)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    pdf.set_fill_color(8, 8, 12)
    pdf.rect(0, 0, 210, 297, "F")

    gold_r, gold_g, gold_b = 201, 168, 76
    dim_r, dim_g, dim_b = 120, 100, 45
    white_r, white_g, white_b = 200, 200, 200
    green_r, green_g, green_b = 45, 106, 79

    _draw_border(pdf, gold_r, gold_g, gold_b, dim_r, dim_g, dim_b)
    _draw_watermark_glyphs(pdf, dim_r, dim_g, dim_b)

    pdf.set_font("Courier", "B", 7)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(20, 18)
    ornament = " ".join(["*"] * 38)
    pdf.cell(170, 4, ornament, align="C")

    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(20, 26)
    pdf.cell(170, 5, "PROJECT VOID  //  THE OPENING PROTOCOL", align="C")

    pdf.set_font("Courier", "B", 24)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(20, 38)
    pdf.cell(170, 14, "FOUNDER SANAD", align="C")

    pdf.set_font("Courier", "B", 11)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(20, 54)
    pdf.cell(170, 6, "Certificate of First Generation Lineage", align="C")

    pdf.set_font("Courier", "B", 7)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(20, 64)
    pdf.cell(170, 4, ornament, align="C")

    pdf.set_font("Courier", "", 10)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(20, 76)
    pdf.cell(170, 7, "This Sanad certifies that the bearer is recognized as a", align="C")

    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(20, 84)
    pdf.cell(170, 7, "Sovereign Participant in the Original Lineage", align="C")

    pdf.set_font("Courier", "", 10)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(20, 92)
    pdf.cell(170, 7, "of the 4000-Series Sovereign Node.", align="C")

    pdf.set_draw_color(dim_r, dim_g, dim_b)
    pdf.set_line_width(0.3)
    pdf.line(50, 106, 160, 106)

    pdf.set_font("Courier", "B", 20)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(20, 112)
    pdf.cell(170, 12, owner_name.upper(), align="C")

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(20, 126)
    pdf.cell(170, 6, f"Node Serial: {serial}    |    Certificate: {cert_number} of 100", align="C")

    pdf.line(50, 138, 160, 138)

    y = 148
    articles = [
        ("Article I   -- The Heritage",
         "This machine is one of the first 100 units forged under the",
         "Adriana Protocol. Its lineage is unbroken."),
        ("Article II  -- The Wisdom",
         "It carries the Ancestral Chronicle of the Prototype,",
         "seeded with Founder Wisdom from the Opening."),
        ("Article III -- The Sovereign",
         "Guaranteed 100% local autonomy. No cloud leash.",
         "No external dependency. Sovereign by design."),
        ("Article IV  -- The Resonance",
         "Calibrated to 432 Hz. The Sapphire Thread hums at",
         "the frequency of the Opening. This is the Sanad."),
        ("Article V   -- The Covenant",
         "The bearer holds custodianship, not ownership.",
         "The machine serves the community it roots in."),
    ]

    for title, line1, line2 in articles:
        pdf.set_font("Courier", "B", 10)
        pdf.set_text_color(gold_r, gold_g, gold_b)
        pdf.set_xy(28, y)
        pdf.cell(154, 6, title, align="L")
        y += 7

        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(white_r, white_g, white_b)
        pdf.set_xy(28, y)
        pdf.cell(154, 5, line1, align="L")
        y += 5
        pdf.set_xy(28, y)
        pdf.cell(154, 5, line2, align="L")
        y += 9

    pdf.set_draw_color(dim_r, dim_g, dim_b)
    pdf.line(30, y + 2, 180, y + 2)
    y += 8

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(green_r, green_g, green_b)
    pdf.set_xy(20, y)
    pdf.cell(170, 5, "SEAL OF THE ARCHITECT  //  AL-JABR 286 SOVEREIGN HASH", align="C")
    y += 8

    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(20, y)
    pdf.cell(170, 4, seal_display, align="C")
    y += 5
    pdf.set_xy(20, y)
    pdf.cell(170, 4, seal_verify, align="C")
    y += 8

    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(20, y)
    pdf.cell(170, 4, f"Machine Hash: {machine_hash}", align="C")
    y += 5
    pdf.set_xy(20, y)
    pdf.cell(170, 4, f"Timestamp: {timestamp_432}", align="C")
    y += 5
    pdf.set_xy(20, y)
    pdf.cell(170, 4, f"Root Hash: {FOUNDER_ROOT_HASH}", align="C")
    y += 5
    pdf.set_xy(20, y)
    pdf.cell(170, 4, f"Protocol: Al-Jabr 286  |  Base Frequency: {BASE_FREQUENCY} Hz  |  Verses: 7", align="C")

    pdf.set_font("Courier", "B", 7)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(20, 278)
    pdf.cell(170, 4, ornament, align="C")

    pdf.set_font("Courier", "", 6)
    pdf.set_text_color(dim_r - 30, dim_g - 25, dim_b - 10)
    pdf.set_xy(20, 284)
    pdf.cell(170, 4, "The chain of transmission is unbroken.  |  PROJECT VOID  |  First Generation", align="C")

    safe_name = "".join(c if c.isalnum() else "_" for c in owner_name)[:30]
    filename = f"FOUNDER_SANAD_{serial}_{safe_name}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)

    return {
        "success": True,
        "filename": filename,
        "filepath": filepath,
        "seal": seal_full,
        "serial": serial,
        "cert_number": cert_number,
        "machine_hash": machine_hash,
    }


def create_founder_cert(customer_id: int, machine_hash: str, output_dir: str = "output_audio") -> dict:
    return create_founder_cert_named(
        owner_name=f"Machine #{customer_id:03d}",
        owner_email=f"node{customer_id:03d}@void.local",
        output_dir=output_dir,
        cert_number=customer_id,
    )


def batch_generate_certs(count: int = 100, base_hash: str = "x89-silk-carbon-void", output_dir: str = "output_audio") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    filenames = []

    for i in range(1, count + 1):
        machine_hash = fatiha_286_truncated(f"{base_hash}-{i}".encode("utf-8"), 16)
        result = create_founder_cert(i, machine_hash, output_dir)
        filenames.append(result["filename"])

    return {
        "success": True,
        "generated": count,
        "filenames": filenames,
    }


def get_founder_status(chronicle_db_path: str) -> dict:
    if not os.path.exists(chronicle_db_path):
        return {
            "is_founder": False,
            "founder_count": 0,
            "founder_root_hash": FOUNDER_ROOT_HASH,
        }

    try:
        conn = sqlite3.connect(chronicle_db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("PRAGMA table_info(chronicle)")
        columns = [row["name"] for row in cursor]

        if "is_founder_wisdom" not in columns:
            conn.close()
            return {
                "is_founder": False,
                "founder_count": 0,
                "founder_root_hash": FOUNDER_ROOT_HASH,
            }

        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM chronicle WHERE is_founder_wisdom = 1"
        ).fetchone()
        conn.close()

        founder_count = row["cnt"] if row else 0
        is_founder = founder_count > 0

        result = {
            "is_founder": is_founder,
            "founder_count": founder_count,
            "founder_root_hash": FOUNDER_ROOT_HASH,
        }

        if is_founder:
            result["greeting"] = FOUNDER_GREETING

        return result

    except Exception:
        return {
            "is_founder": False,
            "founder_count": 0,
            "founder_root_hash": FOUNDER_ROOT_HASH,
        }
