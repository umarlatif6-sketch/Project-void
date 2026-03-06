from flask import Blueprint, request, jsonify, session
from routes.auth import login_required, admin_required
from void_engine.vigilance import (
    submit_report, get_reports, get_report, review_report,
    get_leaderboard, get_stats, VALID_SEVERITIES, VALID_CATEGORIES,
)

vigilance_bp = Blueprint("vigilance", __name__)


@vigilance_bp.route("/api/vigilance/report", methods=["POST"])
@login_required
def api_submit_report():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    severity = (data.get("severity") or "").strip().lower()
    category = (data.get("category") or "").strip().lower() or None
    steps = (data.get("steps_to_reproduce") or "").strip() or None

    if not title or len(title) < 5:
        return jsonify({"error": "Title must be at least 5 characters"}), 400
    if not description or len(description) < 20:
        return jsonify({"error": "Description must be at least 20 characters"}), 400
    if severity not in VALID_SEVERITIES:
        return jsonify({"error": f"Invalid severity. Must be one of: {', '.join(VALID_SEVERITIES)}"}), 400

    result = submit_report(session["user_id"], title, description, severity, category, steps)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@vigilance_bp.route("/api/vigilance/reports")
@login_required
def api_list_reports():
    status_filter = request.args.get("status")
    reports = get_reports(status_filter=status_filter)
    for r in reports:
        r.pop("description", None)
        r.pop("steps_to_reproduce", None)
        r.pop("admin_notes", None)
    return jsonify({"reports": reports})


@vigilance_bp.route("/api/vigilance/my-reports")
@login_required
def api_my_reports():
    reports = get_reports(reporter_id=session["user_id"])
    return jsonify({"reports": reports})


@vigilance_bp.route("/api/vigilance/report/<int:report_id>")
@login_required
def api_get_report(report_id):
    report = get_report(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    user_id = session["user_id"]
    role = session.get("role", "user")
    if report["reporter_id"] != user_id and role not in ("admin", "founder"):
        safe = {k: report[k] for k in ("id", "title", "severity", "category", "status", "vtx_reward", "created_at", "reporter_username")}
        return jsonify(safe)
    return jsonify(report)


@vigilance_bp.route("/api/vigilance/leaderboard")
@login_required
def api_leaderboard():
    entries = get_leaderboard()
    return jsonify({"leaderboard": entries})


@vigilance_bp.route("/api/vigilance/stats")
@login_required
def api_stats():
    stats = get_stats()
    return jsonify(stats)


@vigilance_bp.route("/api/vigilance/review/<int:report_id>", methods=["POST"])
@admin_required
def api_review_report(report_id):
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    admin_notes = (data.get("admin_notes") or "").strip() or None

    result = review_report(report_id, session["user_id"], action, admin_notes)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)
