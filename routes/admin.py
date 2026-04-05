import io
import os
import math
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, redirect, render_template, session, jsonify, send_file
from routes.auth import admin_required
from void_engine.db_pool import get_db
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


def _get_db():
    return get_db()


@admin_bp.route("/admin/market", methods=["GET"])
@admin_required
def admin_market_get():
    conn = _get_db()
    updated = request.args.get("updated")
    error = request.args.get("error")
    yield_error = request.args.get("yield_error")
    yield_posted = request.args.get("yield_posted")
    model_updated = request.args.get("model_updated")
    model_error = request.args.get("model_error")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, item_key, display_name, gbp_pence, vtx_cost, is_active, updated_at FROM market_configs ORDER BY id"
        )
        rows = cur.fetchall()
        configs = [
            {
                "id": r[0],
                "item_key": r[1],
                "display_name": r[2],
                "gbp_pence": r[3],
                "gbp_display": f"{r[3] / 100:.2f}",
                "vtx_cost": float(r[4]),
                "is_active": r[5],
                "updated_at": r[6].strftime("%Y-%m-%d %H:%M") if r[6] else "",
            }
            for r in rows
        ]
    except Exception as e:
        logger.error("Failed to load market_configs: %s", e)
        configs = []
    finally:
        conn.close()

    from void_engine.blueprint_nft import get_yield_events
    try:
        yield_events = get_yield_events(10)
    except Exception as e:
        logger.error("Failed to load yield_events: %s", e)
        yield_events = []

    from void_engine.aljabr_transpiler import get_model_router
    try:
        router = get_model_router()
        model_tier_configs = router.get_config_display()
        cost_summary = router.get_cost_summary()
        gemini_key_configured = router.gemini_api_key_status()
    except Exception as e:
        logger.error("Failed to load model router config: %s", e)
        model_tier_configs = []
        cost_summary = {"by_tier": [], "grand_total_usd": 0.0, "grand_total_calls": 0, "recent_calls": []}
        gemini_key_configured = False

    return render_template(
        "admin_market.html",
        configs=configs,
        updated=updated,
        error=error,
        yield_error=yield_error,
        yield_posted=yield_posted,
        yield_events=yield_events,
        model_tier_configs=model_tier_configs,
        cost_summary=cost_summary,
        model_updated=model_updated,
        model_error=model_error,
        gemini_key_configured=gemini_key_configured,
    )


def _safe_float(raw, default=None):
    """Parse a float, rejecting NaN/Infinity strings before conversion."""
    s = str(raw).strip().lower()
    if s in ("nan", "inf", "-inf", "+inf", "infinity", "-infinity"):
        return default
    try:
        val = float(s)
        if not math.isfinite(val):
            return default
        return val
    except (ValueError, TypeError):
        return default


@admin_bp.route("/admin/market", methods=["POST"])
@admin_required
def admin_market_post():
    item_key = (request.form.get("item_key") or "").strip()
    gbp_pounds = _safe_float(request.form.get("gbp_pounds", "0"))
    gbp_pence = None if gbp_pounds is None else round(gbp_pounds * 100)

    vtx_cost = _safe_float(request.form.get("vtx_cost", "0"))

    is_active = request.form.get("is_active") == "1"

    if not item_key or gbp_pence is None or vtx_cost is None or gbp_pence < 0 or vtx_cost < 0:
        return redirect("/admin/market?error=invalid_input")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE market_configs
               SET gbp_pence = %s, vtx_cost = %s, is_active = %s, updated_at = NOW()
               WHERE item_key = %s""",
            (gbp_pence, vtx_cost, is_active, item_key),
        )
        conn.commit()
        logger.info("Admin updated market_configs[%s]: gbp=%d vtx=%s active=%s", item_key, gbp_pence, vtx_cost, is_active)
    except Exception as e:
        logger.error("Failed to update market_configs: %s", e)
        conn.rollback()
        return redirect(f"/admin/market?error=db_error")
    finally:
        conn.close()

    return redirect(f"/admin/market?updated={item_key}")


@admin_bp.route("/admin/model-router", methods=["POST"])
@admin_required
def admin_model_router_post():
    from void_engine.aljabr_transpiler import get_model_router, TASK_PRECISION, TASK_STANDARD, TASK_BULK
    tier = (request.form.get("tier") or "").strip().upper()
    model = (request.form.get("model") or "").strip()
    base_url = (request.form.get("base_url") or "").strip() or None

    cost_per_1k = _safe_float(request.form.get("cost_per_1k_tokens", "0.0003"), default=0.0003)
    if cost_per_1k < 0:
        cost_per_1k = 0.0003

    if tier not in (TASK_PRECISION, TASK_STANDARD, TASK_BULK) or not model:
        return redirect("/admin/market?model_error=invalid_input")

    router = get_model_router()
    ok = router.save_tier_config(tier, model, base_url, cost_per_1k)
    if not ok:
        return redirect("/admin/market?model_error=save_failed")

    logger.info("Admin updated model router tier=%s model=%s base_url=%s", tier, model, base_url)
    return redirect(f"/admin/market?model_updated={tier}")


@admin_bp.route("/admin/test-gemini", methods=["POST"])
@admin_required
def admin_test_gemini():
    from void_engine.aljabr_transpiler import get_model_router
    router = get_model_router()
    success, message = router.test_gemini_connection()
    return jsonify({"success": success, "message": message})


@admin_bp.route("/admin/yield", methods=["POST"])
@admin_required
def admin_post_yield():
    from void_engine.blueprint_nft import post_yield_event
    try:
        amount_vtx = _safe_float(request.form.get("amount_vtx", "0"))
        if amount_vtx is None:
            raise ValueError("NaN/Infinity not allowed")
        amount_gbp_str = request.form.get("amount_gbp", "0").replace(",", "").replace("£", "").strip()
        amount_gbp_f = _safe_float(amount_gbp_str, default=0.0)
        amount_gbp = round(amount_gbp_f * 100)
        notes = (request.form.get("notes") or "").strip()
        idempotency_key = (request.form.get("idempotency_key") or "").strip() or None
    except (ValueError, TypeError):
        return redirect("/admin/market?yield_error=invalid_input")

    if amount_vtx <= 0:
        return redirect("/admin/market?yield_error=invalid_input")

    admin_id = session.get("user_id")
    result = post_yield_event(amount_vtx, notes or None, admin_id, amount_gbp, idempotency_key)
    if "error" in result:
        return redirect(f"/admin/market?yield_error={result['error']}")
    return redirect(f"/admin/market?yield_posted={result['event_id']}")


def _build_disclosure_text() -> str:
    """
    Assemble the full canonical text of the DBIN Prior Art Disclosure Document.
    This is the authoritative content payload hashed to produce the Al-Jabr 286
    integrity seal. Any material change to this text changes the seal.
    """
    sections = [
        "DOCUMENT REFERENCE: DBIN-PAD-001",
        "TITLE: Distributed Biological Intelligence Network (DBIN)",
        "SUBTITLE: Method of Using Living Plants as Distributed Biological Sensors Correlated with Human Biometric Output (Thermal, Piezoelectric, Acoustic) for Population-Level Health, Emotional, and Environmental Intelligence",
        "INVENTOR: Umar",
        "JURISDICTION: United Kingdom",
        "AUTHORITY: UK Intellectual Property Office",
        "",
        "SECTION 1 — INVENTOR DECLARATION",
        "I, Umar, hereby declare that I am the sole inventor and original architect of the invention described in this document, titled the Distributed Biological Intelligence Network (DBIN), and all associated methods, protocols, systems, and algorithms described herein.",
        "I further declare that: This document represents my genuine conception and reduction to practice of the invention prior to any public disclosure. The invention described is my original work and was not derived from any third party confidential information. I am the originator of the specific combination of plant bioelectrical sensing, human biometric correlation, distributed network aggregation, and the token economy incentive mechanism described herein. The software implementation referenced as technical exhibits exists as working code authored by me within the PROJECT VOID codebase.",
        "This disclosure is made for the purpose of establishing prior art evidence and does not constitute a patent filing. I reserve all rights to file formal patent applications based on this disclosure.",
        "",
        "SECTION 2 — INVENTION TITLE AND FIELD",
        "Title: Distributed Biological Intelligence Network — Method of Using Living Plants as Distributed Biological Sensors for Human Behavioural, Emotional, and Health State Inference",
        "Field of Invention: This invention pertains to the fields of biosensing, distributed computing, human-computer interaction, environmental intelligence, precision health monitoring, and decentralised token economies. It lies specifically at the intersection of plant electrophysiology, edge computing, piezoelectric energy harvesting, acoustic signal processing, and population-level health analytics.",
        "Classification (provisional): G01N 33/48 (biological material analysis), H04W 84/18 (peer-to-peer wireless networks), A61B 5/00 (measuring for diagnostic purposes), G06Q 20/06 (token-based payment systems).",
        "",
        "SECTION 3 — BACKGROUND OF THE INVENTION",
        "Current approaches to population-level health and emotional state monitoring rely predominantly on wearable devices, smartphone accelerometers, or self-reported data. These systems suffer from: consent friction (wearables require active user adoption and continuous charging), data centralisation (aggregated health data stored in centralised servers vulnerable to breach and misuse), environmental blindness (existing systems do not integrate ambient biological signals from the surrounding environment), and a participation incentive gap (no mechanism to reward individuals for contributing biometric data to public health networks).",
        "Plants have long been known to respond to their environment through bioelectrical signals (action potentials), changes in transpiration rate, volatile organic compound (VOC) emission, and root electrical conductivity. Prior art in plant electrophysiology (Backster, 1968; Masi et al., 2009; Chatterjee et al., 2016) demonstrates measurable plant responses to proximate stimuli. However, no prior art exists that combines plant bioelectrical sensing with structured human biometric output correlation, distributed node network aggregation, and a token economy incentive layer — the core of this invention.",
        "The Inventor conceived this invention as part of the PROJECT VOID platform — a sovereign, distributed computing framework built around acoustic steganography, off-grid energy harvesting, and biological mesh networking. The DBIN extends this framework to use the living environment itself as a passive sensor array.",
        "",
        "SECTION 4 — DETAILED DESCRIPTION OF THE INVENTION",
        "4.1 — Plant Bioelectrical Sensor Array (VPP Layer): Living plants (primary embodiment: houseplants, office vegetation, mycelium-colonised wooden substrates) serve as passive biosensors. The Inventor's Vegetative Pulse Protocol (VPP) defines three sensing modalities. Thermal modality: Infrared thermopile sensors at the plant canopy detect body heat signatures of nearby humans. Heart rate, stress arousal, and sleep deficit manifest as measurable changes in radiated thermal output (+-0.3 degrees C resolution sufficient for population-level trend detection). Piezoelectric modality: Piezoelectric transducers bonded to stem tissue detect micro-mechanical deformations caused by air pressure waves generated by human movement, breathing cadence, and voice. The KineticTransceiver module converts movement frequency signatures into biometric estimates using the same harmonic analysis principles as plant-mediated vibration. Acoustic modality: The Beehive Protocol captures acoustic signatures in the 432 Hz and sub-2 kHz range. Plant tissues act as resonant cavities, amplifying specific frequency signatures corresponding to human emotional arousal states (elevated voice frequency, altered breathing rhythm).",
        "4.2 — Human Biometric Correlation Engine: The VPP correlates plant response signatures with known human biometric outputs. Thermal variance above baseline maps to elevated cortisol proxy (stress marker). Piezoelectric high-frequency oscillation maps to elevated heart rate proxy. Acoustic amplitude envelope at 120-160 bpm frequency band maps to cardiovascular exertion proxy analogous to the MAX_GLOW heart rate window (120-160 bpm) defined in the KineticTransceiver module. VOC receptor output (future hardware iteration) maps to emotional state classification. The CSI Bio-Monitor provides the signal processing architecture: WiFi Channel State Information (CSI) amplitude variance and phase shift RMS are used as proxy signals for biological substrate changes — the same mathematical framework applies to plant electrophysiology when the ESP32 antenna is replaced by a bioelectrode in direct substrate contact.",
        "4.3 — Distributed Node Network and Aggregation: Individual plant nodes are networked using the Beehive Protocol acoustic mesh — each node transmits processed biometric estimates using 432 Hz phase-keyed acoustic pulses embedded with identity hashes (Al-Jabr 286). The network aggregates signals across nodes to derive population-level health, emotional, and environmental indices. The mesh supports up to seven hops (approximately 350 miles coastal range) using sound alone, enabling grid-independent operation. Solar harvesting powers each node autonomously — the dual-mode harvester switches between photovoltaic and thermal modes at 15 degrees C, ensuring year-round off-grid operation.",
        "4.4 — VTX Token Economy (Participation Incentive Layer): To address the participation incentive gap identified in the Background, the DBIN employs a token economy based on the VTX (Vortex Token) currency. Individuals who deploy plant sensor nodes receive VTX rewards proportional to: node uptime and signal quality, biometric data contribution volume, mesh relay activity (forwarding packets for dark/offline nodes), and physical exercise logged via the KineticTransceiver (creating a feedback loop between personal health behaviour and network value). VTX tokens are managed through the sovereign wallet and marketplace infrastructure described in the PROJECT VOID codebase, providing a complete end-to-end economic incentive system without reliance on centralised servers.",
        "",
        "SECTION 5 — CLAIMS OF NOVELTY",
        "CLAIM 1 — Plant-Human Biometric Correlation Method: A method of correlating living plant bioelectrical, thermal, and mechanical response signals with individual human biometric output (heart rate, emotional arousal, physical exertion state) in real-time using a multimodal sensing array comprising thermal, piezoelectric, and acoustic transducers interfacing directly with plant tissue or substrate.",
        "CLAIM 2 — Distributed Plant Sensor Node: A distributed sensor node comprising: (a) a living plant or mycelium-colonised substrate as primary sensing medium; (b) a piezoelectric transducer bonded to stem or root tissue; (c) a thermopile infrared sensor at canopy level; (d) an acoustic receiver tuned to 432 Hz and sub-2 kHz; (e) an edge processor executing the Vegetative Pulse Protocol; and (f) a mesh transceiver for acoustic or RF inter-node communication.",
        "CLAIM 3 — Acoustic Mesh Aggregation of Biological Signals: A method of aggregating biological sensor data across a distributed network of plant nodes using phase-keyed acoustic communication (the Beehive Protocol) wherein data packets are embedded in 432 Hz carrier pulses with sovereign identity hashes, enabling grid-independent, infrastructure-free population health monitoring over distances of up to 350 miles without internet connectivity.",
        "CLAIM 4 — Population-Level Health Index Derivation: A method of deriving population-level health, emotional, and environmental indices from aggregated plant node signals, comprising: normalisation of per-node biometric estimates; spatial averaging across node clusters; temporal smoothing to eliminate transient artefacts; and classification of the resulting signal into health state categories (stress index, cardiovascular activity index, emotional arousal index) without any individual identifying data being transmitted or stored.",
        "CLAIM 5 — Solar-Powered Off-Grid Node Architecture: A self-powered plant sensor node architecture wherein power is supplied exclusively by a dual-mode solar harvester that operates in photovoltaic mode above 15 degrees C and in selective-absorber thermal mode below 15 degrees C, with a flywheel energy buffer providing continuous power to the node processor and mesh transceiver during dark periods, enabling year-round autonomous operation without grid connection.",
        "CLAIM 6 — Token Economy Participation Incentive: A method of incentivising participation in a distributed biological sensing network through a sovereign digital token economy (VTX), wherein token rewards are algorithmically calculated as a function of node uptime, biometric data contribution quality, mesh relay activity, and the operator's personal physical exercise metrics as logged by a kinetic transceiver — creating a closed economic loop between personal health behaviour, network contribution, and financial reward.",
        "",
        "SECTION 6 — TECHNICAL EXHIBITS",
        "EXHIBIT E-001 — void_engine/al_jabr_286.py: Al-Jabr 286 Sovereign Hashing Protocol. A 286-bit cryptographic hash function derived from SHA3-256 extended by a 30-bit trilateral frequency anchor computed from the seven-verse structure of Al-Fatiha. Functions include fatiha_286_hexdigest(), fatiha_286_truncated(), verify_286_signature(). The 286-bit output is intentionally invisible to standard 256-bit forensic scanners. This constitutes a novel cryptographic primitive designed specifically for the DBIN.",
        "EXHIBIT E-002 — void_engine/csi_bio_monitor.py: ESP32 WiFi CSI Mycelium Bio-Monitor. Parses Channel State Information (CSI) packets from an ESP32-S3 mesh to derive biological state estimates. Key functions: derive_sensor_state_from_packet() mapping amplitude variance to moisture and phase shift RMS to growth density. The StanceDetector and MasticationDetector classes demonstrate CSI-based human behaviour inference. This is the technical precursor to the plant-substrate CSI sensing described in Claims 1 and 2.",
        "EXHIBIT E-003 — void_engine/beehive.py: Beehive Acoustic Mesh Protocol. Implements acoustic mesh networking for the distributed node network. The protocol uses 432 Hz phase-keyed pulses authenticated by Al-Jabr 286 identity hashes embedded as Insect Silt at -30 dB below the carrier. Supports up to seven hops (approximately 350 miles coastal range). Key components: generate_handshake_pulse(), verify_fatiha_signature(), silt_embed(), transmit_data(), and the flywheel buffer for dark node data persistence. This constitutes the distributed aggregation layer described in Claim 3.",
        "EXHIBIT E-004 — void_engine/kinetic.py: Kinetic Transceiver — Harmonic Movement Analysis. Converts physical exercise reps, duration, and heart rate into CC (Consensus Credit) token rewards using harmonic frequency analysis against a 432 Hz base frequency. The MAX_GLOW condition (heart rate 120-160 bpm + harmonic alignment) awards double token rewards. The _check_harmonic() method identifies movement frequencies within 5% of the 432 Hz harmonic series. This constitutes the physical exercise metric component of the token economy described in Claim 6, and provides the biometric correlation framework for the cardiovascular exertion proxy described in Section 4.2.",
        "EXHIBIT E-005 — hardware/solar_profile.py: Dual-Mode Solar Harvester Power Profile. Codifies the self-powered node architecture. At ambient temperatures at or above 15 degrees C, CIGS thin-film photovoltaic panels produce approximately 367 W peak electrical output (2.4 m2 panel area, 18% efficiency). Below 15 degrees C, selective-absorber thermal panels produce approximately 1,836 W thermal output, reducing substrate heating load. The crossover logic in get_solar_mode() ensures autonomous year-round operation. Node power draw budget: full compute 85 W, mesh relay 25 W, sleep 4.5 W. This constitutes the off-grid node power architecture described in Claim 5.",
        "EXHIBIT E-006 — void_engine/stega.py and void_engine/calculator.py: Acoustic Steganography and Signal Analysis Engine. The core PROJECT VOID steganography engine embeds arbitrary data in audio carrier waves using LSB encoding with vortex, chirp-sync, and jitter scatter modes. The find_harmonic_pockets() function identifies frequency ranges in audio carriers suitable for covert data embedding — directly applicable to plant acoustic resonance analysis. The carrier analysis module (analyze_carrier()) characterises bubble burst thresholds, surface tension, and spectral content of audio signals. These methods inform the acoustic modality of the VPP described in Section 4.1.",
        "",
        "SECTION 7 — FORMAL DISCLOSURE DECLARATION",
        "I, Umar, the undersigned inventor, hereby formally disclose the invention described in this document — the Distributed Biological Intelligence Network (DBIN) — as prior art evidence in accordance with the standards of the United Kingdom Intellectual Property Office. The concepts, methods, and systems described herein were conceived and reduced to practice by me prior to the disclosure date recorded in this document. The technical exhibits referenced are working implementations authored by me and exist in the PROJECT VOID codebase. This disclosure is made in good faith to establish the date and scope of my invention prior to any public disclosure or commercial exploitation. I understand that this document, once timestamped and integrity-sealed, constitutes evidence of inventorship and conception date for the purposes of patent priority and prior art defence. This document does not constitute a patent application and does not prejudice my right to file patent applications in any jurisdiction.",
        "The integrity of this document is verified by the Al-Jabr 286 Sovereign Hash embedded in the document header and PDF footer. Any modification to the document content will produce a different hash, invalidating this disclosure as tamper-evident evidence.",
    ]
    return "\n".join(sections)


def _compute_seal() -> str:
    """Compute the Al-Jabr 286 seal of the full canonical disclosure content."""
    return fatiha_286_hexdigest_from_str(_build_disclosure_text())


@admin_bp.route("/ip-disclosure", methods=["GET"])
@admin_required
def ip_disclosure_get():
    disclosure_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    seal_hash = _compute_seal()
    return render_template(
        "ip_disclosure.html",
        disclosure_date=disclosure_date,
        seal_hash=seal_hash,
    )


@admin_bp.route("/ip-disclosure/download", methods=["POST"])
@admin_required
def ip_disclosure_download():
    try:
        from fpdf import FPDF
    except ImportError:
        return jsonify({"error": "fpdf2 library not available"}), 500

    disclosure_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    seal_hash = _compute_seal()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    def _header_section():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, "PRIOR ART DISCLOSURE DOCUMENT — CONFIDENTIAL — ADMIN ACCESS ONLY", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, f"Document Reference: DBIN-PAD-001  |  Jurisdiction: United Kingdom  |  Authority: UK Intellectual Property Office", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_draw_color(100, 80, 200)
        pdf.set_line_width(0.8)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(6)

    def _section_title(num, title):
        pdf.ln(4)
        pdf.set_fill_color(240, 238, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(60, 40, 160)
        pdf.cell(0, 8, f"  {num}. {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)

    def _body_text(text, bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5.5, text)
        pdf.ln(1)

    def _bullet(text):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5.5, f"  \u2022  {text}")

    pdf.add_page()

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(100, 80, 200)
    pdf.cell(0, 6, "PRIOR ART DISCLOSURE DOCUMENT  |  UK IPO EVIDENCE  |  DBIN-PAD-001", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_draw_color(100, 80, 200)
    pdf.set_line_width(1.0)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(0, 9, "Distributed Biological Intelligence Network (DBIN)", align="C")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(60, 60, 80)
    pdf.multi_cell(0, 6, "Method of Using Living Plants as Distributed Biological Sensors\nCorrelated with Human Biometric Output for Population-Level Health,\nEmotional, and Environmental Intelligence", align="C")
    pdf.ln(6)

    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    meta_pairs = [
        ("Inventor", "Umar"),
        ("Disclosure Date", disclosure_date),
        ("Document Reference", "DBIN-PAD-001"),
        ("Jurisdiction", "United Kingdom"),
        ("Authority", "UK Intellectual Property Office"),
    ]
    col_w = 85
    for label, value in meta_pairs:
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_w, 6, label + ":", new_x="RIGHT", new_y="LAST")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    _section_title("1", "Inventor Declaration")
    _body_text("I, Umar, hereby declare that I am the sole inventor and original architect of the invention described in this document, titled the Distributed Biological Intelligence Network (DBIN), and all associated methods, protocols, systems, and algorithms described herein.")
    _body_text("I further declare that:")
    _bullet("This document represents my genuine conception and reduction to practice of the invention prior to any public disclosure.")
    _bullet("The invention described is my original work and was not derived from any third party's confidential information.")
    _bullet("I am the originator of the specific combination of plant bioelectrical sensing, human biometric correlation, distributed network aggregation, and the token economy incentive mechanism described herein.")
    _bullet("The software implementation referenced as technical exhibits exists as working code authored by me within the PROJECT VOID codebase.")
    pdf.ln(2)
    _body_text("This disclosure is made for the purpose of establishing prior art evidence and does not constitute a patent filing. I reserve all rights to file formal patent applications based on this disclosure.")

    _section_title("2", "Invention Title and Field")
    _body_text("Title: Distributed Biological Intelligence Network — Method of Using Living Plants as Distributed Biological Sensors for Human Behavioural, Emotional, and Health State Inference", bold=True)
    _body_text("Field of Invention: This invention pertains to the fields of biosensing, distributed computing, human-computer interaction, environmental intelligence, precision health monitoring, and decentralised token economies. It lies at the intersection of plant electrophysiology, edge computing, piezoelectric energy harvesting, acoustic signal processing, and population-level health analytics.")
    _body_text("Classification (provisional): G01N 33/48 (biological material analysis), H04W 84/18 (peer-to-peer wireless networks), A61B 5/00 (measuring for diagnostic purposes), G06Q 20/06 (token-based payment systems).")

    _section_title("3", "Background of the Invention")
    _body_text("Current approaches to population-level health monitoring rely on wearable devices, smartphone sensors, or self-reported data — suffering from consent friction, data centralisation, environmental blindness, and a participation incentive gap. Prior art in plant electrophysiology (Backster 1968; Masi et al. 2009; Chatterjee et al. 2016) demonstrates measurable plant responses to proximate stimuli. However, no prior art exists that combines plant bioelectrical sensing with structured human biometric output correlation, distributed node network aggregation, and a token economy incentive layer — the core of this invention.")

    pdf.add_page()
    _header_section()

    _section_title("4", "Detailed Description of the Invention")
    _body_text("4.1 — Plant Bioelectrical Sensor Array (VPP Layer)", bold=True)
    _body_text("Living plants serve as passive biosensors. The Vegetative Pulse Protocol (VPP) defines three sensing modalities:")
    _bullet("Thermal modality: Infrared thermopile sensors at plant canopy detect body heat signatures. Heart rate, stress arousal, and sleep deficit manifest as changes in radiated thermal output (+-0.3 deg C resolution).")
    _bullet("Piezoelectric modality: Piezoelectric transducers bonded to stem tissue detect micro-mechanical deformations from human movement, breathing cadence, and voice. The KineticTransceiver converts movement frequency signatures into biometric estimates.")
    _bullet("Acoustic modality: The Beehive Protocol captures acoustic signatures at 432 Hz and sub-2 kHz. Plant tissues act as resonant cavities amplifying frequency signatures corresponding to human emotional arousal.")
    pdf.ln(2)
    _body_text("4.2 — Human Biometric Correlation Engine", bold=True)
    _body_text("The VPP correlates plant response signatures with known human biometric outputs: thermal variance to cortisol proxy (stress), piezoelectric high-frequency oscillation to elevated heart rate, and acoustic amplitude envelope at 120-160 bpm to cardiovascular exertion.")
    pdf.ln(2)
    _body_text("4.3 — Distributed Node Network and Aggregation", bold=True)
    _body_text("Plant nodes communicate using the Beehive Protocol acoustic mesh — 432 Hz phase-keyed pulses embedded with Al-Jabr 286 identity hashes. The network aggregates signals across nodes for population-level indices over up to seven hops (~350 miles). Solar harvesting powers each node autonomously.")
    pdf.ln(2)
    _body_text("4.4 — VTX Token Economy (Participation Incentive Layer)", bold=True)
    _body_text("Individuals deploying plant sensor nodes receive VTX rewards proportional to node uptime, biometric data contribution, mesh relay activity, and personal exercise logged via the KineticTransceiver — creating a feedback loop between personal health behaviour and network value.")

    _section_title("5", "Claims of Novelty")
    claims = [
        ("Claim 1", "Plant-Human Biometric Correlation Method", "A method of correlating living plant bioelectrical, thermal, and mechanical response signals with individual human biometric output (heart rate, emotional arousal, physical exertion state) in real-time using a multimodal sensing array comprising thermal, piezoelectric, and acoustic transducers interfacing directly with plant tissue or substrate."),
        ("Claim 2", "Distributed Plant Sensor Node", "A distributed sensor node comprising: (a) a living plant or mycelium-colonised substrate as primary sensing medium; (b) a piezoelectric transducer bonded to stem or root tissue; (c) a thermopile infrared sensor at canopy level; (d) an acoustic receiver tuned to 432 Hz and sub-2 kHz; (e) an edge processor executing the Vegetative Pulse Protocol; and (f) a mesh transceiver for acoustic or RF inter-node communication."),
        ("Claim 3", "Acoustic Mesh Aggregation of Biological Signals", "A method of aggregating biological sensor data across a distributed network of plant nodes using phase-keyed acoustic communication (the Beehive Protocol) wherein data packets are embedded in 432 Hz carrier pulses with sovereign identity hashes, enabling grid-independent, infrastructure-free population health monitoring over distances of up to 350 miles without internet connectivity."),
        ("Claim 4", "Population-Level Health Index Derivation", "A method of deriving population-level health, emotional, and environmental indices from aggregated plant node signals, comprising: normalisation of per-node biometric estimates; spatial averaging across node clusters; temporal smoothing; and classification into health state categories without any individual identifying data being transmitted or stored."),
        ("Claim 5", "Solar-Powered Off-Grid Node Architecture", "A self-powered plant sensor node architecture wherein power is supplied exclusively by a dual-mode solar harvester that operates in photovoltaic mode above 15 deg C and in selective-absorber thermal mode below 15 deg C, with a flywheel energy buffer providing continuous power during dark periods, enabling year-round autonomous operation without grid connection."),
        ("Claim 6", "Token Economy Participation Incentive", "A method of incentivising participation in a distributed biological sensing network through a sovereign digital token economy (VTX), wherein token rewards are algorithmically calculated as a function of node uptime, biometric data contribution quality, mesh relay activity, and the operator's personal physical exercise metrics as logged by a kinetic transceiver — creating a closed economic loop between personal health behaviour, network contribution, and financial reward."),
    ]
    for num, subtitle, text in claims:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(60, 40, 160)
        pdf.cell(0, 6, f"{num} — {subtitle}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5.5, text)
        pdf.ln(3)

    pdf.add_page()
    _header_section()

    _section_title("6", "Technical Exhibits — Supporting Evidence")
    exhibits = [
        ("E-001", "void_engine/al_jabr_286.py", "Al-Jabr 286 Sovereign Hashing Protocol. A 286-bit cryptographic hash function derived from SHA3-256 extended by a 30-bit trilateral frequency anchor. Provides tamper-evident integrity seals for all DBIN data packets. Functions: fatiha_286_hexdigest(), fatiha_286_truncated(), verify_286_signature()."),
        ("E-002", "void_engine/csi_bio_monitor.py", "ESP32 WiFi CSI Mycelium Bio-Monitor. Parses CSI packets to derive biological state estimates. Maps amplitude variance to moisture and phase shift RMS to growth density. StanceDetector and MasticationDetector demonstrate CSI-based human behaviour inference — the technical precursor to plant-substrate CSI sensing."),
        ("E-003", "void_engine/beehive.py", "Beehive Acoustic Mesh Protocol. Implements acoustic mesh networking using 432 Hz phase-keyed pulses authenticated by Al-Jabr 286 hashes embedded at -30 dB. Supports 7 hops (~350 miles). Components: generate_handshake_pulse(), verify_fatiha_signature(), silt_embed(), transmit_data(), flywheel buffer."),
        ("E-004", "void_engine/kinetic.py", "Kinetic Transceiver — Harmonic Movement Analysis. Converts exercise reps, duration, and heart rate into CC token rewards using 432 Hz harmonic analysis. MAX_GLOW condition (HR 120-160 bpm + harmonic alignment) awards double rewards. Provides biometric correlation framework for cardiovascular exertion proxy."),
        ("E-005", "hardware/solar_profile.py", "Dual-Mode Solar Harvester Power Profile. Photovoltaic mode above 15 deg C (~367 W peak), selective-absorber thermal mode below 15 deg C (~1836 W thermal). Node power budget: full compute 85 W, mesh relay 25 W, sleep 4.5 W. Enables year-round autonomous operation."),
        ("E-006", "void_engine/stega.py / void_engine/calculator.py", "Acoustic Steganography and Signal Analysis Engine. find_harmonic_pockets() identifies frequency ranges for covert embedding — applicable to plant acoustic resonance analysis. analyze_carrier() characterises bubble burst thresholds and spectral content. Informs the acoustic modality of the VPP."),
    ]
    for label, path, desc in exhibits:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(60, 40, 160)
        pdf.cell(30, 6, label, new_x="RIGHT", new_y="LAST")
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, path, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(3)

    _section_title("7", "Formal Disclosure Declaration")
    _body_text("I, Umar, the undersigned inventor, hereby formally disclose the invention described in this document — the Distributed Biological Intelligence Network (DBIN) — as prior art evidence in accordance with UK Intellectual Property Office standards.")
    _bullet("The concepts, methods, and systems described herein were conceived and reduced to practice by me prior to the disclosure date recorded in this document.")
    _bullet("The technical exhibits referenced are working implementations authored by me and exist in the PROJECT VOID codebase.")
    _bullet("This disclosure is made in good faith to establish the date and scope of my invention prior to any public disclosure or commercial exploitation.")
    _bullet("This document constitutes evidence of inventorship and conception date for the purposes of patent priority and prior art defence.")
    _bullet("This document does not constitute a patent application and does not prejudice my right to file patent applications in any jurisdiction.")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 30, 30)
    sig_labels = [
        ("Inventor — Sole Architect", "Umar"),
        ("Disclosure Date and Time (UTC)", disclosure_date),
        ("Document Identifier", "DBIN-PAD-001"),
    ]
    for label, value in sig_labels:
        pdf.set_draw_color(150, 150, 150)
        pdf.set_line_width(0.3)
        pdf.line(20, pdf.get_y() + 10, 120, pdf.get_y() + 10)
        pdf.ln(12)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    _section_title("8", "Tamper-Evident Integrity Seal — Al-Jabr 286 Sovereign Hash")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5.5, "This 72-character hexadecimal string is the Al-Jabr 286 Sovereign Hash (286-bit) of the canonical disclosure document content. Protocol: SHA3-256 base + 30-bit trilateral frequency anchor (Sura Al-Fatiha verse structure). Any modification to the document content will produce a different hash, invalidating this disclosure as tamper-evident evidence.")
    pdf.ln(3)
    pdf.set_fill_color(240, 255, 245)
    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(20, 120, 60)
    pdf.multi_cell(0, 6, seal_hash, fill=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, f"Protocol: Al-Jabr 286  |  Base: SHA3-256  |  Extension: 30-bit Sovereign  |  Total: 288 bits (286 active)  |  Output: 72 hex chars")
    pdf.multi_cell(0, 5, f"Verification: compute fatiha_286_hexdigest(document_canonical_bytes) using void_engine/al_jabr_286.py")

    pdf.ln(6)
    pdf.set_draw_color(100, 80, 200)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, f"DBIN-PAD-001  |  PROJECT VOID  |  Confidential — Admin Access Only  |  Generated: {disclosure_date}  |  Seal: {seal_hash[:24]}...", align="C")

    buf = io.BytesIO()
    pdf_bytes = pdf.output()
    buf.write(pdf_bytes)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="DBIN_Prior_Art_Disclosure_DBIN-PAD-001.pdf",
    )
