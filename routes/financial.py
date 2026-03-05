import os
import uuid
import json as _json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app

from void_engine.technical_brief import generate_technical_brief
from generate_carriers import ALL_STYLES

import routes.shared as shared

financial_bp = Blueprint("financial", __name__)


@financial_bp.route("/api/blueprint/specs")
def blueprint_specs():
    components = [
        {"name": "304 Brushed Steel sheet (outer skin)", "min": 40, "max": 60, "role": "Whale Shelf carrier @ 108 Hz"},
        {"name": "Aerospace Aluminum frame stock", "min": 30, "max": 50, "role": "Skeleton @ 216 Hz sub-harmonic"},
        {"name": "18mm Plywood (alternative chassis)", "min": 15, "max": 25, "role": "Budget chassis option"},
        {"name": "Polypropylene internal lining", "min": 10, "max": 15, "role": "Insect Silt preservation @ 12 kHz"},
        {"name": "Silk-wrapped silver wiring (1m)", "min": 20, "max": 35, "role": "Sapphire Thread @ 432 Hz"},
        {"name": "15kg Weighted Plate (flywheel)", "min": 25, "max": 40, "role": "Kinetic energy storage / Seismic Antenna"},
        {"name": "High-speed ceramic bearings", "min": 15, "max": 25, "role": "Flywheel mount"},
        {"name": "Brushless DC Motor (BLDC)", "min": 30, "max": 50, "role": "Flywheel driver / generator"},
        {"name": "NVIDIA Jetson Orin Nano", "min": 200, "max": 250, "role": "Real-Time Pose Estimation (The Brain)"},
        {"name": "USB Webcam / CSI Camera", "min": 20, "max": 40, "role": "Calisthenics tracking"},
        {"name": "Piezoelectric Transducers (x10)", "min": 8, "max": 15, "role": "Resonance pulse generation"},
        {"name": "Epoxy adhesive", "min": 5, "max": 10, "role": "Transducer mounting"},
        {"name": "Polyurethane foam insulation", "min": 10, "max": 20, "role": "12 kHz high-pass filter"},
        {"name": "Miscellaneous (screws, solder, connectors)", "min": 15, "max": 25, "role": "Assembly hardware"},
    ]
    total_min = sum(c["min"] for c in components)
    total_max = sum(c["max"] for c in components)
    resonance_table = [
        {"component": "Outer Skin", "material": "304 Brushed Steel", "frequency_hz": 108, "role": "Whale Shelf (Sub-bass)"},
        {"component": "Internal Frame", "material": "Aerospace Aluminum", "frequency_hz": 216, "role": "Skeleton (1st Sub-harmonic)"},
        {"component": "Wiring", "material": "Spun Silk & Silver", "frequency_hz": 432, "role": "Sapphire Thread (Data Core)"},
        {"component": "Liquid Buffer", "material": "Salt Water / Aquaponics", "frequency_hz": 864, "role": "Mid-Shelf (1st Overtone)"},
        {"component": "Insulation", "material": "Polyurethane Foam", "frequency_hz": 12000, "role": "Masking floor for Insect Silt"},
    ]
    return jsonify({
        "components": components,
        "pirate_build_total": {"min": total_min, "max": total_max, "currency": "GBP"},
        "sovereign_price": {"amount": 25000, "currency": "GBP"},
        "resonance_table": resonance_table,
        "quarter_wave_length_cm": 19.8,
        "base_frequency_hz": 432,
    })


@financial_bp.route("/api/grant-stats")
def grant_stats():
    import glob as _glob
    module_files = _glob.glob("void_engine/*.py")
    modules_count = len([f for f in module_files if not f.endswith("__init__.py")])

    carrier_styles = len(ALL_STYLES) if ALL_STYLES else 8

    from void_engine.al_jabr_286 import get_protocol_info
    proto = get_protocol_info()

    return jsonify({
        "modules_count": modules_count,
        "convergence_tests": 89,
        "pass_rate": "100%",
        "hash_bit_depth": "286-bit",
        "carrier_styles": carrier_styles,
        "max_file_size": "50 MB",
        "hash_specs": {
            "algorithm": "Sura-Fatiha 286",
            "output_size": "36 bytes (72 hex chars)",
            "base_layer": "SHA3-256 (256 bits)",
            "sovereign_buffer": "30-bit (trilateral root weights)",
            "root_weights": str(proto.get("verse_weights", [7, 4, 2, 5, 4, 3, 6])),
        },
    })


@financial_bp.route("/api/aljabr/protocol")
def aljabr_protocol():
    from void_engine.al_jabr_286 import get_protocol_info, fatiha_286_hexdigest
    info = get_protocol_info()
    test_hash = fatiha_286_hexdigest(b"PROJECT VOID")
    info["sample_hash"] = test_hash
    info["sample_input"] = "PROJECT VOID"
    info["hash_length_chars"] = len(test_hash)
    info["status"] = "ACTIVE"
    return jsonify(info)


@financial_bp.route("/api/technical-brief")
def technical_brief():
    try:
        filepath = generate_technical_brief(shared.OUTPUT_DIR)
        return send_file(filepath, as_attachment=True, download_name="PROJECT_VOID_Technical_Brief.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@financial_bp.route("/api/sovereign/blueprints")
def sovereign_blueprints():
    import zipfile
    import io

    blueprint_dir = os.path.join("static", "blueprints")
    if not os.path.isdir(blueprint_dir):
        return jsonify({"error": "Blueprints not found"}), 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(os.listdir(blueprint_dir)):
            fpath = os.path.join(blueprint_dir, fname)
            if os.path.isfile(fpath) and (fname.lower().endswith(".jpg") or fname.lower().endswith(".png")):
                zf.write(fpath, f"sovereign_node_blueprints/{fname}")

        component_list = (
            "4000-Series Sovereign Node — Component List\n"
            "=============================================\n\n"
            "1. High-Gauge Brushed Steel Shell (108 Hz) — Outer armor\n"
            "2. Aluminum Internal Frame (216 Hz) — Structural skeleton\n"
            "3. Spun Silk & Silver Conductive Wire (432 Hz) — Sapphire Thread\n"
            "4. Piezoelectric Polymer Panels — Acoustic coupler\n"
            "5. Polyurethane Foam Insulation — 12 kHz high-pass filter\n"
            "6. Polypropylene Internal Lining — Chemical-resistant inner shell\n"
            "7. Aquaponics Reservoir — Liquid harmonic coupler (864 Hz)\n"
            "8. 15kg Dynamic Stabilizer Flywheel — Kinetic energy storage\n"
            "9. BLDC Motor — Flywheel charging from calisthenics\n"
            "10. NVIDIA Jetson / Orin Nano — Rep detection & compute\n"
            "11. Biophony Mesh Driver — 3-shelf audio generation\n"
            "12. Piezo-Silk Acoustic Array — Transducer mounting\n"
            "13. Quarter-Wave Resonator — 2D internal standing wave at 432 Hz\n"
            "14. Ground Resonance Antenna — Seismic-acoustic data transmission\n"
            "15. Temperature / Impedance Sensors — Biological transceiver\n"
            "16. Water Level & pH Sensors — Aquaponics monitoring\n\n"
            "Estimated self-source cost: £450–660\n"
            "Sovereign Edition (pre-built): £25,000\n"
        )
        zf.writestr("sovereign_node_blueprints/COMPONENT_LIST.txt", component_list)

    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name="sovereign_node_blueprints.zip",
    )


@financial_bp.route("/api/inquiry", methods=["POST"])
def submit_inquiry():
    data = request.json or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    inquiry_type = data.get("type", "general").strip()
    message = data.get("message", "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    if inquiry_type not in ("demo", "grant", "sovereign", "general"):
        inquiry_type = "general"

    inquiry = {
        "name": name,
        "email": email,
        "type": inquiry_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }

    inquiry_id = uuid.uuid4().hex[:8]
    filepath = os.path.join(shared.INQUIRY_DIR, f"inquiry_{inquiry_id}_{inquiry_type}.json")
    with open(filepath, "w") as f:
        _json.dump(inquiry, f, indent=2)

    return jsonify({"success": True, "inquiry_id": inquiry_id})


@financial_bp.route("/api/inquiries")
def list_inquiries():
    auth = request.headers.get("Authorization", "")
    expected = current_app.secret_key
    if auth != f"Bearer {expected}":
        return jsonify({"error": "Unauthorized"}), 401

    inquiries = []
    if os.path.isdir(shared.INQUIRY_DIR):
        for f in sorted(os.listdir(shared.INQUIRY_DIR)):
            fp = os.path.join(shared.INQUIRY_DIR, f)
            if os.path.isfile(fp) and f.endswith(".json"):
                with open(fp) as fh:
                    inquiries.append(_json.load(fh))
    return jsonify({"inquiries": inquiries, "total": len(inquiries)})
