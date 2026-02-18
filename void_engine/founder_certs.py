import os
import hashlib
import sqlite3
from fpdf import FPDF

FOUNDER_ROOT_HASH = "89x-VOID-GEN1-PROTO-2026"
FOUNDER_GREETING = "Inherited Wisdom Detected. First Generation Status: ACTIVE. Greeting the Architect."


def create_founder_cert(customer_id: int, machine_hash: str, output_dir: str = "output_audio") -> dict:
    os.makedirs(output_dir, exist_ok=True)

    seal_input = f"GEN1-{customer_id}-{machine_hash}"
    seal = hashlib.sha256(seal_input.encode()).hexdigest()[:16]

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    pdf.set_fill_color(10, 10, 10)
    pdf.rect(0, 0, 210, 297, "F")

    gold_r, gold_g, gold_b = 212, 175, 55
    dim_r, dim_g, dim_b = 140, 120, 50
    white_r, white_g, white_b = 200, 200, 200

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 15)
    pdf.cell(190, 5, "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", align="C")

    pdf.set_font("Courier", "B", 22)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(10, 30)
    pdf.cell(190, 12, "VOID 4000: FIRST GENERATION", align="C")

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 45)
    pdf.cell(190, 5, "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", align="C")

    pdf.set_font("Courier", "", 11)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(10, 62)
    pdf.cell(190, 8, "This document hereby certifies that", align="C")

    machine_label = f"Machine #{customer_id:03d}"
    pdf.set_font("Courier", "B", 18)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(10, 78)
    pdf.cell(190, 10, machine_label, align="C")

    pdf.set_font("Courier", "", 11)
    pdf.set_text_color(white_r, white_g, white_b)
    pdf.set_xy(10, 94)
    pdf.cell(190, 8, "is recognized as a Sovereign Participant in the Original Lineage", align="C")

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 110)
    pdf.cell(190, 7, f"Machine Hash: {machine_hash}", align="C")

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 125)
    pdf.cell(190, 5, "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", align="C")

    y = 138
    articles = [
        ("Article 1 -- The Heritage",
         "This machine is part of the first 100 units built under the Adriana Protocol."),
        ("Article 2 -- The Wisdom",
         "It carries the Ancestral Chronicle of the prototype (02-16 to 02-18)."),
        ("Article 3 -- The Sovereign",
         "Guaranteed 100% local autonomy; no cloud leash."),
    ]

    for title, body in articles:
        pdf.set_font("Courier", "B", 11)
        pdf.set_text_color(gold_r, gold_g, gold_b)
        pdf.set_xy(25, y)
        pdf.cell(160, 8, title, align="L")
        y += 10

        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(white_r, white_g, white_b)
        pdf.set_xy(25, y)
        pdf.multi_cell(160, 6, body, align="L")
        y += 16

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 220)
    pdf.cell(190, 5, "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -", align="C")

    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(gold_r, gold_g, gold_b)
    pdf.set_xy(10, 235)
    pdf.cell(190, 8, f"SEAL OF THE ARCHITECT: {seal}", align="C")

    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 250)
    pdf.cell(190, 6, f"Cryptographic Verification: SHA-256 / {seal_input}", align="C")

    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 270)
    pdf.cell(190, 5, "~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", align="C")

    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(dim_r, dim_g, dim_b)
    pdf.set_xy(10, 280)
    pdf.cell(190, 5, f"Root Hash: {FOUNDER_ROOT_HASH}", align="C")

    filename = f"FOUNDER_CERT_{customer_id:03d}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)

    return {
        "success": True,
        "filename": filename,
        "seal": seal,
        "customer_id": customer_id,
    }


def batch_generate_certs(count: int = 100, base_hash: str = "x89-silk-carbon-void", output_dir: str = "output_audio") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    filenames = []

    for i in range(1, count + 1):
        machine_hash = hashlib.sha256(f"{base_hash}-{i}".encode()).hexdigest()[:16]
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
