import io
import logging
from flask import Blueprint, request, jsonify, session, redirect, render_template, send_file
from routes.auth import login_required, admin_required
from void_engine.chronicle_adriana import (
    get_chronicle,
    post_chronicle_entry,
    delete_chronicle_entry,
    build_adriana_sdk_zip,
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


@chronicle_bp.route("/api/adriana/verify")
def adriana_verify():
    token_id = request.args.get("token_id")
    if not token_id:
        return jsonify({"licensed": False, "error": "token_id required"}), 400
    try:
        import os
        import psycopg2
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT bt.id, bt.tier, bt.token_hash,
                          bt.edition_number, bt.total_editions, bt.status,
                          tow.owner_id
                   FROM blueprint_tokens bt
                   LEFT JOIN token_ownership tow ON tow.token_id = bt.id
                   WHERE bt.id = %s
                   ORDER BY tow.purchased_at DESC
                   LIMIT 1""",
                (int(token_id),),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return jsonify({"licensed": False, "error": "Token not found"})

        is_sold = row[5] == "sold"
        has_owner = row[6] is not None
        licensed = is_sold and has_owner

        return jsonify({
            "licensed":  licensed,
            "tier":      row[1],
            "edition":   f"{row[3]}/{row[4]}" if row[3] and row[4] else None,
            "token_hash": row[2][:16] + "..." if row[2] else None,
            "sdk_url":   "/download/adriana-sdk",
        })
    except Exception as e:
        logger.error("Adriana verify error: %s", e)
        return jsonify({"licensed": False, "error": "Verification failed"}), 500


@chronicle_bp.route("/download/adriana-sdk")
def download_adriana_sdk():
    try:
        zip_bytes = build_adriana_sdk_zip()
        buf = io.BytesIO(zip_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name="adriana-sdk-v1.0.zip",
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
