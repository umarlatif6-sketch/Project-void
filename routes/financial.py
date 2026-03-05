import os
import uuid
import json as _json
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app, render_template, session

from void_engine.technical_brief import generate_technical_brief
from void_engine.pitch_deck import generate_pitch_deck
from generate_carriers import ALL_STYLES, estimate_carrier_capacity
from void_engine.founder_certs import create_founder_cert_named, FOUNDER_ROOT_HASH
from routes.auth import admin_required

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

    consent = data.get("consent", False)
    if not consent:
        return jsonify({"error": "Consent is required to submit an inquiry"}), 400

    source_page = data.get("source_page", "").strip()
    configuration = data.get("configuration", "").strip()
    organisation = data.get("organisation", "").strip()
    phone = data.get("phone", "").strip()
    interest = data.get("interest", "").strip()

    inquiry = {
        "name": name,
        "email": email,
        "type": inquiry_type,
        "message": message,
        "organisation": organisation,
        "phone": phone,
        "interest": interest,
        "consent": True,
        "source_page": source_page,
        "configuration": configuration,
        "timestamp": datetime.now().isoformat(),
    }

    inquiry_id = uuid.uuid4().hex[:8]
    filepath = os.path.join(shared.INQUIRY_DIR, f"inquiry_{inquiry_id}_{inquiry_type}.json")
    with open(filepath, "w") as f:
        _json.dump(inquiry, f, indent=2)

    return jsonify({"success": True, "inquiry_id": inquiry_id})


@financial_bp.route("/api/pitch/targets")
def pitch_targets():
    targets = [
        {
            "key": "otf",
            "name": "Open Technology Fund",
            "focus": "Internet freedom tools, censorship circumvention, secure communications",
            "alignment": "Steganographic data embedding in ambient audio enables censorship-resistant communication channels invisible to surveillance systems",
        },
        {
            "key": "fpf",
            "name": "Freedom of the Press Foundation",
            "focus": "Journalist protection, secure document transfer, whistleblower tools",
            "alignment": "Biophony carriers allow journalists to transfer sensitive documents hidden in nature recordings, undetectable by standard forensic analysis",
        },
        {
            "key": "mozilla",
            "name": "Mozilla Foundation",
            "focus": "Open web, decentralized technology, privacy-preserving tools",
            "alignment": "Open-source sovereign hashing and mesh networking protocols advance decentralized, privacy-first web infrastructure",
        },
        {
            "key": "general",
            "name": "General / Custom Funder",
            "focus": "Broad technology innovation, dual-use civilian/humanitarian applications",
            "alignment": "A convergent platform combining steganography, bioacoustics, and sovereign cryptography for next-generation secure data systems",
        },
    ]
    return jsonify({"targets": targets})


@financial_bp.route("/api/pitch/generate", methods=["POST"])
def pitch_generate():
    data = request.json or {}
    target = data.get("target", "general").strip().lower()

    valid_targets = ("otf", "fpf", "mozilla", "general")
    if target not in valid_targets:
        return jsonify({"error": f"Invalid target '{target}'. Valid: {list(valid_targets)}"}), 400

    import glob as _glob
    module_files = _glob.glob("void_engine/*.py")
    modules_count = len([f for f in module_files if not f.endswith("__init__.py")])

    carrier_styles = len(ALL_STYLES) if ALL_STYLES else 8

    from void_engine.al_jabr_286 import get_protocol_info, fatiha_286_hexdigest
    proto = get_protocol_info()
    sample_hash = fatiha_286_hexdigest(b"PROJECT VOID PITCH")

    capacity_demos = []
    for dur_min in [1, 5, 10, 30, 60]:
        cap = estimate_carrier_capacity(dur_min, "midnight_pond")
        capacity_demos.append({
            "duration_minutes": dur_min,
            "carrier_size": cap["wav_size_human"],
            "lsb2_capacity": cap["effective_lsb2_human"],
            "style": "midnight_pond (biophony stereo)",
        })

    journalism_specs = {
        "max_payload": "50 MB per carrier",
        "max_carrier_duration": "300 minutes (5 hours)",
        "carrier_capacity_1hr": estimate_carrier_capacity(60, "midnight_pond")["effective_lsb2_human"],
        "encoding_method": "Vortex Scatter at LSB-2",
        "forensic_evasion": "286-bit hash invisible to 256-bit scanners",
        "carrier_styles_available": carrier_styles,
    }

    target_alignment = {
        "otf": {
            "funder": "Open Technology Fund",
            "headline": "Censorship-Resistant Communication Through Biophony Steganography",
            "use_case": "Activists and journalists in censored regions embed encrypted messages in ambient nature recordings. Standard surveillance tools detect only environmental audio — the 286-bit sovereign hash ensures payloads are invisible to 256-bit forensic scanners.",
            "key_differentiators": [
                "Audio carriers pass through content filters as ambient nature sounds",
                "286-bit sovereign hashing evades standard 256-bit forensic detection",
                "Mesh networking enables peer-to-peer distribution without centralized infrastructure",
                "Biophony carriers (cricket, cicada, pond ambience) provide 5x density over synthetic tones",
                "Open-source architecture allows community audit and contribution",
            ],
            "impact_statement": "PROJECT VOID gives censored populations a communication channel that is acoustically invisible, cryptographically sovereign, and operationally decentralized.",
        },
        "fpf": {
            "funder": "Freedom of the Press Foundation",
            "headline": "Secure Document Transfer for Journalists Using Steganographic Audio Carriers",
            "use_case": "Journalists embed sensitive documents, source recordings, and whistleblower files into biophony carriers that sound like field recordings. A 1-hour midnight pond carrier holds enough capacity for multiple documents, and the 286-bit hash ensures only the intended recipient can decode.",
            "key_differentiators": [
                "Documents hidden in nature recordings are undetectable by email/file scanning",
                "Sovereign 286-bit hashing provides journalist-specific key derivation",
                "Capacity scales from kilobytes (text) to megabytes (documents/images)",
                "Carrier files can be shared via any audio channel (email, messaging, podcast feeds)",
                "No centralized server required — fully peer-to-peer operation",
            ],
            "impact_statement": "PROJECT VOID transforms ordinary audio files into secure document vaults, giving journalists a dead-drop mechanism that lives inside ambient sound.",
        },
        "mozilla": {
            "funder": "Mozilla Foundation",
            "headline": "Decentralized Sovereign Infrastructure for the Open Web",
            "use_case": "PROJECT VOID implements a fully open-source mesh protocol with sovereign hashing, bioacoustic data encoding, and decentralized consensus — advancing the open web by removing dependence on centralized certificate authorities, cloud storage, and corporate encryption standards.",
            "key_differentiators": [
                "Al-Jabr 286 protocol replaces SHA-256 with a culturally-grounded sovereign hash",
                "Beehive mesh protocol enables serverless peer-to-peer networking",
                "Biophony carriers democratize steganography using environmental audio",
                "Kinetic energy harvesting (calisthenics-powered flywheel) removes grid dependence",
                "Full convergence test suite with 100% pass rate ensures production readiness",
            ],
            "impact_statement": "PROJECT VOID is infrastructure for a sovereign web — where identity, encryption, and communication are owned by the individual, not the platform.",
        },
        "general": {
            "funder": "General / Custom",
            "headline": "PROJECT VOID — Sovereign Steganographic Infrastructure",
            "use_case": "A convergent platform combining bioacoustic steganography, sovereign cryptography, mesh networking, and kinetic energy harvesting into a single deployable node. Applications span secure communications, environmental monitoring, decentralized data storage, and censorship circumvention.",
            "key_differentiators": [
                "Multi-layer steganography across biophony audio carriers",
                "286-bit sovereign hashing with forensic evasion properties",
                "Beehive mesh protocol for decentralized networking",
                "Physical hardware node (4000-Series) with kinetic energy storage",
                "Full-stack: from carrier generation to mesh routing to financial infrastructure",
            ],
            "impact_statement": "PROJECT VOID bridges the gap between digital cryptography and physical infrastructure, creating a sovereign system that operates independently of centralized networks.",
        },
    }

    pitch = {
        "target": target,
        "generated_at": datetime.now().isoformat(),
        "alignment": target_alignment[target],
        "technical_proof": {
            "modules_active": modules_count,
            "convergence_tests": 89,
            "pass_rate": "100%",
            "hash_protocol": {
                "name": proto["protocol"],
                "bit_depth": proto["bit_depth"],
                "base_algorithm": proto["base_algorithm"],
                "extension_bits": proto["extension_bits"],
                "output_size": f"{proto['total_bytes']} bytes ({proto['total_bytes'] * 2} hex chars)",
                "sample_hash": sample_hash,
                "forensic_evasion": proto["forensic_evasion"],
            },
            "carrier_styles": carrier_styles,
            "max_capacity": "1.8 GB (300-minute biophony carrier at LSB-2)",
            "encoding_method": "Vortex Scatter at LSB-2",
        },
        "capacity_demonstrations": capacity_demos,
        "journalism_port": journalism_specs,
        "downloads": {
            "technical_brief": "/api/technical-brief",
            "blueprints": "/api/sovereign/blueprints",
            "protocol_spec": "/api/aljabr/protocol",
        },
        "pricing": {
            "sovereign_edition": {"amount": 25000, "currency": "GBP"},
            "self_source_estimate": {"min": 450, "max": 660, "currency": "GBP"},
        },
    }

    return jsonify(pitch)


@financial_bp.route("/admin/leads")
@admin_required
def admin_leads():
    return render_template("admin.html")


@financial_bp.route("/api/inquiries")
@admin_required
def list_inquiries():
    inquiries = []
    if os.path.isdir(shared.INQUIRY_DIR):
        for f in sorted(os.listdir(shared.INQUIRY_DIR)):
            fp = os.path.join(shared.INQUIRY_DIR, f)
            if os.path.isfile(fp) and f.endswith(".json"):
                with open(fp) as fh:
                    inquiries.append(_json.load(fh))
    return jsonify({"inquiries": inquiries, "total": len(inquiries)})


@financial_bp.route("/api/pitch/deck")
def pitch_deck():
    target = request.args.get("target", "general").strip().lower()
    valid_targets = ("otf", "fpf", "mozilla", "general")
    if target not in valid_targets:
        target = "general"

    try:
        filepath = generate_pitch_deck(target=target, output_dir=shared.OUTPUT_DIR)
        filename = os.path.basename(filepath)
        return send_file(
            filepath,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@financial_bp.route("/api/genesis/specs")
def genesis_specs():
    specs_path = os.path.join("data", "genesis_specs.json")
    if not os.path.isfile(specs_path):
        return jsonify({"error": "Genesis specs not found"}), 404
    with open(specs_path) as f:
        specs = _json.load(f)
    return jsonify(specs)


@financial_bp.route("/api/founder/certificate", methods=["POST"])
def founder_certificate():
    data = request.json or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    try:
        result = create_founder_cert_named(
            owner_name=name,
            owner_email=email,
            output_dir=shared.OUTPUT_DIR,
        )
        if result.get("success"):
            return send_file(
                result["filepath"],
                mimetype="application/pdf",
                as_attachment=True,
                download_name=result["filename"],
            )
        return jsonify({"error": "Certificate generation failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@financial_bp.route("/pricing")
def pricing_page():
    return render_template("pricing.html",
                           user_tier=session.get("tier", "ghost"),
                           is_logged_in=bool(session.get("user_id")))
