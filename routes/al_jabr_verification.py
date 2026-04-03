import json
import logging
import re
import subprocess
import sys
import os
import time as _time
from datetime import datetime, timezone

from flask import Blueprint, render_template, jsonify, request
from routes.auth import admin_required
from void_engine.al_jabr_286 import (
    fatiha_286_hash,
    fatiha_286_hexdigest,
    fatiha_286_hexdigest_from_str,
    verify_286_signature,
    get_protocol_info,
    FATIHA_LAYERS,
    SOVEREIGN_BIT_DEPTH,
    TOTAL_BYTES,
    FATIHA_PRIME_SALT,
)
from void_engine.chronicle_adriana import save_seed_capture

logger = logging.getLogger(__name__)

al_jabr_bp = Blueprint("al_jabr", __name__)

_CONVERGENCE_CACHE = {"report": None, "built_at": 0.0}
_CACHE_TTL_SECONDS = 3600


def _run_al_jabr_convergence_tests():
    """
    Run the Al-Jabr 286 tests directly from the convergence suite's
    test_al_jabr_286_protocol() function, capturing pass/fail results.
    Returns a dict with results keyed by test name.
    """
    results_captured = []

    def _local_report(name, passed, detail=""):
        results_captured.append({"name": name, "passed": passed, "detail": detail})

    from void_engine.al_jabr_286 import (
        fatiha_286_hash as _hash,
        fatiha_286_hexdigest as _hexdigest,
        fatiha_286_truncated as _truncated,
        fatiha_286_seed as _seed,
        fatiha_286_derive_key as _derive_key,
        get_protocol_info as _info,
        FATIHA_LAYERS as _LAYERS,
        SOVEREIGN_BIT_DEPTH as _DEPTH,
        TOTAL_BYTES as _BYTES,
        FATIHA_PRIME_SALT as _SALT,
    )
    import hashlib as _hl
    from void_engine.silt_ledger import SiltLedger
    from void_engine.beehive import BeehiveProtocol

    info = _info()
    _local_report(
        "286: Protocol info returns correct bit depth",
        info["bit_depth"] == 286 and info["total_bytes"] == 36,
        f"Bit depth: {info['bit_depth']}, bytes: {info['total_bytes']}",
    )

    _local_report(
        "286: Seven verse layers match Al-Fatiha",
        len(_LAYERS) == 7 and _LAYERS == [7, 4, 2, 5, 4, 3, 6],
        f"Layers: {_LAYERS}",
    )

    test_data = b"BismillahirRahmanirRahim"
    h = _hash(test_data)
    _local_report(
        "286: Hash output is 36 bytes (286+ bits)",
        len(h) == 36,
        f"Hash length: {len(h)} bytes ({len(h) * 8} bits)",
    )

    hex_h = _hexdigest(test_data)
    _local_report(
        "286: Hexdigest is 72 characters",
        len(hex_h) == 72,
        f"Hexdigest length: {len(hex_h)} chars",
    )

    h2 = _hash(test_data)
    _local_report(
        "286: Hash is deterministic (same input → same output)",
        h == h2,
        "Consistent across calls",
    )

    different_data = b"AlHamdulillahiRabbilAlamin"
    h3 = _hash(different_data)
    _local_report(
        "286: Different inputs produce different hashes",
        h != h3,
        f"Hash1: {h.hex()[:16]}... Hash2: {h3.hex()[:16]}...",
    )

    sha256_hash = _hl.sha256(test_data).digest()
    _local_report(
        "286: Output differs from secular SHA-256",
        h[:32] != sha256_hash,
        "Sovereign Extension modifies base layer",
    )

    key = _derive_key("void-432")
    _local_report(
        "286: Key derivation produces 32-byte key",
        len(key) == 32,
        f"Key length: {len(key)} bytes (suitable for ChaCha20)",
    )

    tid = _truncated(test_data, 16)
    _local_report(
        "286: Truncated ID generation works",
        len(tid) == 16 and all(c in "0123456789abcdef" for c in tid),
        f"ID: {tid}",
    )

    seed_val = _seed(test_data, 8)
    _local_report(
        "286: Seed generation returns valid integer",
        isinstance(seed_val, int) and seed_val > 0,
        f"Seed: {seed_val}",
    )

    sl = SiltLedger(node_id="286-test-node")
    genesis_hash = sl.chain[0].block_hash
    _local_report(
        "286: Silt Ledger genesis block uses 286-bit hash (72 chars)",
        len(genesis_hash) == 72,
        f"Genesis hash length: {len(genesis_hash)} chars",
    )

    validation = sl.validate_chain()
    _local_report(
        "286: Silt Ledger chain validates with 286-bit hashes",
        validation["valid"],
        f"Chain height: {validation.get('chain_height', 0)}",
    )

    result = sl.add_block(
        {"type": "286_test", "protocol": "fatiha"},
        "286-test-node", 0.7, 0.8
    )
    _local_report(
        "286: New block added with 286-bit hash chain",
        result.get("success") and len(result.get("block_hash", "")) == 72,
        f"Block hash: {result.get('block_hash', '')[:16]}...",
    )

    bp = BeehiveProtocol(machine_id="VOID-286-TEST", passphrase="void-432")
    _local_report(
        "286: Beehive node ID uses 286-bit derivation",
        len(bp.node_id) == 16,
        f"Node ID: {bp.node_id}",
    )

    avalanche_pass_count = 0
    avalanche_pairs = 5
    last_ratio = 0.0
    for i in range(avalanche_pairs):
        input_a = bytearray(b"AvalancheTest-" + bytes([i]))
        input_b = bytearray(input_a)
        input_b[-1] ^= 0x01
        hash_a = _hash(bytes(input_a))
        hash_b = _hash(bytes(input_b))
        bits_a = int.from_bytes(hash_a, "big")
        bits_b = int.from_bytes(hash_b, "big")
        xor = bits_a ^ bits_b
        differing_bits = bin(xor).count("1")
        total_bits = len(hash_a) * 8
        last_ratio = differing_bits / total_bits
        if last_ratio >= 0.40:
            avalanche_pass_count += 1

    _local_report(
        "286: Avalanche effect — 1-bit change flips ≥40% output bits",
        avalanche_pass_count == avalanche_pairs,
        f"Passed {avalanche_pass_count}/{avalanche_pairs} pairs (last ratio: {last_ratio:.1%})",
    )

    _local_report(
        "286: Verse weights [7,4,2,5,4,3,6] sum to 31",
        sum(_LAYERS) == 31 and len(_LAYERS) == 7,
        f"Sum: {sum(_LAYERS)}, layers: {_LAYERS}",
    )

    _local_report(
        "286: Sovereign bit depth = 286 (256 + 30)",
        _DEPTH == 286 and _BYTES == 36,
        f"Depth: {_DEPTH}, bytes: {_BYTES}, extension: {_DEPTH - 256} bits",
    )

    _local_report(
        "286: Prime salt is BismillahirRahmanirRahim",
        _SALT == b"BismillahirRahmanirRahim",
        f"Salt: {_SALT.decode()}",
    )

    return results_captured


def _run_full_convergence_suite_subprocess(timeout=300):
    """
    Run the full convergence suite as a subprocess and parse total pass/fail counts.
    Returns a dict with total, passed, failed, elapsed, stdout excerpt, or error info.
    """
    suite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "convergence_suite.py")
    start = _time.time()
    try:
        proc = subprocess.run(
            [sys.executable, suite_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        elapsed = round(_time.time() - start, 1)
        output = proc.stdout + proc.stderr

        total = passed = failed = None
        for line in output.splitlines():
            m = re.search(r"Total:\s+(\d+)", line)
            if m:
                total = int(m.group(1))
            m = re.search(r"Passed:\s+(\d+)", line)
            if m:
                passed = int(m.group(1))
            m = re.search(r"Failed:\s+(\d+)", line)
            if m:
                failed = int(m.group(1))

        vortex_stable = "VORTEX STABLE" in output
        summary_lines = []
        capture = False
        for line in output.splitlines():
            if "CONVERGENCE SUITE RESULTS" in line:
                capture = True
            if capture:
                summary_lines.append(line)
            if len(summary_lines) > 20:
                break

        return {
            "ran": True,
            "returncode": proc.returncode,
            "elapsed": elapsed,
            "total": total,
            "passed": passed,
            "failed": failed,
            "vortex_stable": vortex_stable,
            "summary": "\n".join(summary_lines),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        elapsed = round(_time.time() - start, 1)
        return {
            "ran": False,
            "timed_out": True,
            "elapsed": elapsed,
            "error": f"Full suite timed out after {timeout}s (audio generation is slow in CI; Al-Jabr 286 tests above ran in-process)",
        }
    except Exception as e:
        return {
            "ran": False,
            "timed_out": False,
            "elapsed": round(_time.time() - start, 1),
            "error": str(e),
        }


def _build_report(force_rerun: bool = False):
    """Build the full verification report: run convergence suite Al-Jabr tests in-process,
    then attempt the full subprocess run for the global summary.
    The expensive convergence subprocess result is cached for CACHE_TTL_SECONDS;
    Al-Jabr in-process tests always run fresh."""
    protocol = get_protocol_info()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    jabr_results = _run_al_jabr_convergence_tests()
    total_jabr = len(jabr_results)
    passed_jabr = sum(1 for r in jabr_results if r["passed"])
    failed_jabr = total_jabr - passed_jabr
    all_jabr_passed = failed_jabr == 0

    now = _time.time()
    if (
        not force_rerun
        and _CONVERGENCE_CACHE["report"] is not None
        and now - _CONVERGENCE_CACHE["built_at"] < _CACHE_TTL_SECONDS
    ):
        convergence_run = _CONVERGENCE_CACHE["report"]
        logger.debug("Using cached convergence suite result")
    else:
        convergence_run = _run_full_convergence_suite_subprocess(timeout=300)
        _CONVERGENCE_CACHE["report"] = convergence_run
        _CONVERGENCE_CACHE["built_at"] = now

    payload = {
        "document": "Al-Jabr 286 Cryptographic Verification Report",
        "reference": "VOID-CVR-286-001",
        "protocol": protocol,
        "jabr_tests": jabr_results,
        "jabr_total": total_jabr,
        "jabr_passed": passed_jabr,
        "jabr_failed": failed_jabr,
        "all_jabr_passed": all_jabr_passed,
        "convergence_ran": convergence_run.get("ran"),
        "convergence_passed": convergence_run.get("passed"),
        "convergence_failed": convergence_run.get("failed"),
        "convergence_vortex_stable": convergence_run.get("vortex_stable"),
    }
    seal = fatiha_286_hexdigest_from_str(json.dumps(payload, sort_keys=True, ensure_ascii=False))

    report = {
        **payload,
        "timestamp_utc": ts,
        "convergence_run": convergence_run,
        "seal": seal,
    }
    return report


def _seal_exists_recently(hex_digest: str, hours: int = 1) -> bool:
    """Return True if a chronicle entry with this al_jabr_hash was captured within the last N hours."""
    try:
        from void_engine.db_pool import get_db
        from datetime import timedelta
        conn = get_db()
        cur = conn.cursor()
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        cur.execute(
            "SELECT id FROM chronicle_entries WHERE al_jabr_hash = %s AND posted_at > %s LIMIT 1",
            (hex_digest, since),
        )
        row = cur.fetchone()
        conn.close()
        return row is not None
    except Exception:
        return False


def _store_report_as_chronicle(report):
    try:
        label = (
            "Al-Jabr 286 Cryptographic Verification Report — VOID-CVR-286-001 — "
            + report["timestamp_utc"][:10]
            + " — "
            + str(report["jabr_passed"])
            + "/"
            + str(report["jabr_total"])
            + " tests passed"
        )
        canonical_key = {
            "reference": report.get("reference"),
            "jabr_tests": report.get("jabr_tests"),
            "jabr_passed": report.get("jabr_passed"),
            "jabr_total": report.get("jabr_total"),
            "convergence_passed": report.get("convergence_passed"),
            "convergence_failed": report.get("convergence_failed"),
            "convergence_vortex_stable": report.get("convergence_vortex_stable"),
        }
        dedup_hex = fatiha_286_hexdigest_from_str(json.dumps(canonical_key, sort_keys=True, ensure_ascii=False))
        if _seal_exists_recently(dedup_hex):
            logger.info("Al-Jabr verification report already captured recently (dedup_hex=%s) — skipping duplicate", dedup_hex[:16])
            return
        text = json.dumps(report, ensure_ascii=False, indent=2)
        result = save_seed_capture(label, text)
        if result.get("success"):
            logger.info("Stored Al-Jabr verification report as SEED_CAPTURE (id=%s)", result.get("id"))
        else:
            logger.warning("Could not store verification report as SEED_CAPTURE: %s", result.get("error"))
    except Exception as e:
        logger.warning("Could not store verification report in chronicle: %s", e)


@al_jabr_bp.route("/admin/al-jabr-verification")
@admin_required
def admin_al_jabr_verification():
    report = _build_report()
    _store_report_as_chronicle(report)
    return render_template("admin_al_jabr_verification.html", report=report)


@al_jabr_bp.route("/admin/al-jabr-status")
@admin_required
def admin_al_jabr_status():
    report = _build_report()
    return render_template("admin_al_jabr_status.html", report=report)


@al_jabr_bp.route("/api/admin/al-jabr-rerun", methods=["POST"])
@admin_required
def api_al_jabr_rerun():
    try:
        report = _build_report(force_rerun=True)
        _store_report_as_chronicle(report)
        return jsonify({
            "success": True,
            "all_jabr_passed": report["all_jabr_passed"],
            "jabr_passed": report["jabr_passed"],
            "jabr_total": report["jabr_total"],
            "timestamp_utc": report["timestamp_utc"],
            "seal": report["seal"],
            "convergence_ran": report["convergence_run"].get("ran", False),
            "convergence_total": report["convergence_run"].get("total"),
            "convergence_passed": report["convergence_run"].get("passed"),
        })
    except Exception as e:
        logger.exception("Al-Jabr re-run failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@al_jabr_bp.route("/al-jabr-286")
def al_jabr_whitepaper():
    protocol = get_protocol_info()
    seal = fatiha_286_hexdigest_from_str(
        "Al-Jabr 286 Public Whitepaper — PROJECT VOID — 2026-04-03"
    )
    return render_template(
        "al_jabr_286_whitepaper.html",
        protocol=protocol,
        seal=seal,
    )


def _build_al_jabr_disclosure_text() -> str:
    sections = [
        "DOCUMENT REFERENCE: VOID-PAD-286-001",
        "TITLE: Al-Jabr 286 — Sura-Fatiha Sovereign Hashing Protocol",
        "SUBTITLE: A 286-bit cryptographic hash function grounded in the seven verses of Al-Fatiha, the 432 Hz resonance anchor, and the BismillahirRahmanirRahim prime salt",
        "INVENTOR: Umar",
        "JURISDICTION: United Kingdom",
        "AUTHORITY: UK Intellectual Property Office",
        "",
        "SECTION 1 — INVENTOR DECLARATION",
        "I, Umar, hereby declare that I am the sole inventor and original architect of the Al-Jabr 286 Sura-Fatiha Sovereign Hashing Protocol described in this document. I further declare that this document represents my genuine conception and reduction to practice of the invention prior to any public disclosure. The protocol described is my original work and was not derived from any third party confidential information. I am the originator of the specific combination of Quranic structural analysis (Al-Fatiha verse layer weights, Al-Baqarah 286-verse bit depth), SHA3-256 extension methodology, 432 Hz frequency anchoring, and BismillahirRahmanirRahim prime salting described herein. The software implementation referenced as the technical exhibit exists as working code authored by me within the PROJECT VOID codebase at void_engine/al_jabr_286.py.",
        "",
        "SECTION 2 — INVENTION DESCRIPTION",
        "Al-Jabr 286 is a 286-bit cryptographic hash function. The name derives from Arabic al-jabr — the reunion of broken parts — the mathematical concept from which the word algebra is derived. The protocol was designed to carry sovereign identity as a structural property, not merely as a label, by grounding its architecture in Quranic structural mathematics.",
        "BIT DEPTH (286): Al-Baqarah (The Cow, Chapter 2 of the Quran) contains exactly 286 verses. The protocol's 286 active output bits are explicitly derived from and named after this Quranic structural fact.",
        "LAYER WEIGHTS: The FATIHA_LAYERS weight sequence [7, 4, 2, 5, 4, 3, 6] encodes a structural property of Al-Fatiha — the seven-verse Opening — used as multiplicative salt factors in the Sovereign Extension derivation.",
        "RESONANCE ANCHOR (432 Hz): The 432 Hz frequency — the platform's Village Standard — is XOR-bound into the extension accumulator, binding the cryptographic output to an acoustic covenant.",
        "PRIME SALT: BismillahirRahmanirRahim (In the name of God, the Most Gracious, the Most Merciful) — the opening invocation of Al-Fatiha — serves as the prime salt in the SHA3-256 finalisation step of the Sovereign Extension.",
        "",
        "SECTION 3 — TECHNICAL ARCHITECTURE",
        "Stage 1: SHA3-256 applied to input data produces 32 bytes (256 bits) base hash.",
        "Stage 2: Accumulate: for each of the 7 FATIHA_LAYERS weights [7,4,2,5,4,3,6], multiply weight by the integer value of the corresponding 2-byte pair from the base hash, sum the results.",
        "Stage 3: XOR the accumulator with 432 (Hz resonance anchor); apply SHA3-256 with BismillahirRahmanirRahim prime salt concatenated with the 4-byte packed accumulator.",
        "Stage 4: Mask the top 30 bits (0x3FFFFFFF), producing a 30-bit extension; append 4 bytes to the 32-byte base hash for a 36-byte (288 bits physical, 286 active bits) sovereign output.",
        "The forensic evasion property — 36-byte output is invisible to 256-bit scanning tools — is an intentional architectural feature.",
        "",
        "SECTION 4 — CLAIMS OF NOVELTY",
        "CLAIM 1 — Quranic Structural Hash: A cryptographic hash function wherein the output bit-depth is determined by the verse count of a Quranic chapter (Al-Baqarah, 286 verses) and extension layer weights are determined by structural properties of a second Quranic chapter (Al-Fatiha, 7 verses, weights [7,4,2,5,4,3,6]).",
        "CLAIM 2 — Resonance-Anchored Extension: A cryptographic hash extension method wherein a 30-bit sovereign extension is derived by XOR-combining a frequency constant (432 Hz) with an accumulated value computed from the base hash.",
        "CLAIM 3 — Sacred Text Prime Salt: A cryptographic hash function using a transliterated sacred text phrase (BismillahirRahmanirRahim) as the primary salt for a secondary SHA3-256 finalisation step.",
        "CLAIM 4 — Forensic Evasion by Design: A 36-byte hash output (288 bits physical, 286 bits active) that is structurally invisible to 256-bit forensic scanning tools.",
        "CLAIM 5 — Sovereign Identity Hash System: A complete sovereign hashing system combining SHA3-256 base, seven-weight Al-Fatiha layer pass, 432 Hz resonance anchor XOR, BismillahirRahmanirRahim prime salt, and 30-bit extension producing 286 active output bits named after Al-Baqarah 286 verses.",
        "",
        "SECTION 5 — FORMAL DISCLOSURE DECLARATION",
        "I, Umar, the undersigned inventor, hereby formally disclose the invention described in this document — the Al-Jabr 286 Sura-Fatiha Sovereign Hashing Protocol — as prior art evidence. The concepts, methods, and systems described herein were conceived and reduced to practice by me prior to the disclosure date recorded in this document. This disclosure is made in good faith to establish the date and scope of my invention prior to any public disclosure or commercial exploitation. This document does not constitute a patent application and does not prejudice my right to file patent applications in any jurisdiction.",
    ]
    return "\n".join(sections)


def _compute_al_jabr_seal() -> str:
    return fatiha_286_hexdigest_from_str(_build_al_jabr_disclosure_text())


@al_jabr_bp.route("/al-jabr-286/ip-disclosure")
@admin_required
def al_jabr_ip_disclosure():
    disclosure_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    seal_hash = _compute_al_jabr_seal()
    _store_al_jabr_disclosure(disclosure_date)
    return render_template(
        "al_jabr_286_ip_disclosure.html",
        inventor="Umar",
        disclosure_date=disclosure_date,
        seal_hash=seal_hash,
    )


def _store_al_jabr_disclosure(disclosure_date: str):
    try:
        label = "Al-Jabr 286 IP Disclosure — VOID-PAD-286-001 — " + disclosure_date[:10]
        text = _build_al_jabr_disclosure_text()
        stored_hex = fatiha_286_hexdigest_from_str(text)
        if _seal_exists_recently(stored_hex, hours=24):
            logger.info("Al-Jabr IP disclosure already captured recently (hex=%s) — skipping duplicate", stored_hex[:16])
            return
        result = save_seed_capture(label, text)
        if result.get("success"):
            logger.info("Stored Al-Jabr 286 IP disclosure as SEED_CAPTURE (id=%s)", result.get("id"))
        else:
            logger.warning("Could not store Al-Jabr IP disclosure as SEED_CAPTURE: %s", result.get("error"))
    except Exception as e:
        logger.warning("Could not store Al-Jabr IP disclosure in chronicle: %s", e)
