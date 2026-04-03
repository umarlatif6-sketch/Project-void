import io
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template, send_file
from routes.auth import login_required, admin_required
from void_engine.chronicle_adriana import (
    get_chronicle,
    post_chronicle_entry,
    delete_chronicle_entry,
    generate_adriana_sdk_zip,
    save_seed_capture,
    get_seed_captures,
)

logger = logging.getLogger(__name__)

chronicle_bp = Blueprint("chronicle", __name__)


@chronicle_bp.route("/chronicle")
def chronicle_page():
    try:
        entries = get_chronicle()
    except Exception as e:
        logger.error("Failed to load chronicle: %s", e)
        entries = []
    return render_template("chronicle.html", entries=entries)


@chronicle_bp.route("/api/chronicle")
def api_chronicle():
    try:
        entries = get_chronicle()
        return jsonify({"entries": entries, "count": len(entries)})
    except Exception as e:
        logger.error("Chronicle API error: %s", e)
        return jsonify({"error": "Failed to load chronicle"}), 500


# NOTE: /api/adriana/verify is the canonical implementation in routes/marketplace.py
# (api_adriana_verify). Chronicle blueprint does not duplicate it.


@chronicle_bp.route("/download/adriana-sdk")
def download_adriana_sdk():
    try:
        zip_bytes = generate_adriana_sdk_zip()
        buf = io.BytesIO(zip_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name="adriana-scl-v1.0.zip",
        )
    except Exception as e:
        logger.error("SDK download error: %s", e)
        return jsonify({"error": "Failed to build SDK"}), 500


@chronicle_bp.route("/admin/chronicle", methods=["GET"])
@admin_required
def admin_chronicle_get():
    try:
        entries = get_chronicle()
    except Exception as e:
        logger.error("Admin chronicle load error: %s", e)
        entries = []
    updated = request.args.get("updated")
    error = request.args.get("error")
    return render_template("admin_chronicle.html", entries=entries, updated=updated, error=error)


@chronicle_bp.route("/admin/chronicle", methods=["POST"])
@admin_required
def admin_chronicle_post():
    action = request.form.get("action", "add")

    if action == "delete":
        entry_id = request.form.get("entry_id")
        if not entry_id:
            return redirect("/admin/chronicle?error=missing_id")
        result = delete_chronicle_entry(int(entry_id))
        if "error" in result:
            return redirect(f"/admin/chronicle?error={result['error'][:40]}")
        return redirect("/admin/chronicle?updated=deleted")

    chapter_number = request.form.get("chapter_number", "0")
    title = (request.form.get("title") or "").strip()
    subtitle = (request.form.get("subtitle") or "").strip()
    glyph_sequence = (request.form.get("glyph_sequence") or "").strip()
    body_text = (request.form.get("body_text") or "").strip()

    if not title or not glyph_sequence or not body_text:
        return redirect("/admin/chronicle?error=missing_fields")

    try:
        chapter_number = int(chapter_number)
    except (ValueError, TypeError):
        chapter_number = 0

    result = post_chronicle_entry(
        chapter_number, title, subtitle, glyph_sequence, body_text,
        session.get("user_id"),
    )
    if "error" in result:
        return redirect(f"/admin/chronicle?error=db_error")
    return redirect("/admin/chronicle?updated=added")


@chronicle_bp.route("/admin/seed-capture", methods=["GET"])
@admin_required
def admin_seed_capture_get():
    updated = request.args.get("updated")
    error = request.args.get("error")
    result = request.args.get("result")
    return render_template(
        "admin_seed_capture.html",
        updated=updated,
        error=error,
        result=result,
    )


@chronicle_bp.route("/admin/seed-capture", methods=["POST"])
@admin_required
def admin_seed_capture_post():
    label = (request.form.get("label") or "").strip()
    text = (request.form.get("text") or "").strip()

    if not label or not text:
        return redirect("/admin/seed-capture?error=missing_fields")

    result = save_seed_capture(label, text, admin_id=session.get("user_id"))
    if "error" in result:
        logger.error("Seed capture error: %s", result["error"])
        return redirect("/admin/seed-capture?error=db_error")

    return redirect(
        f"/admin/seed-capture?updated=captured&result={result['hex_digest'][:20]}"
    )


@chronicle_bp.route("/void-seed/hex")
def void_seed_hex_page():
    try:
        captures = get_seed_captures(limit=100)
    except Exception as e:
        logger.error("Failed to load seed captures: %s", e)
        captures = []
    return render_template("void_seed_hex.html", captures=captures)
