"""
Convergence API

/api/convergence/run      (POST) Run the full stack convergence test and return summary
/api/convergence/report   (GET)  Return latest convergence report JSON
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

convergence_bp = Blueprint("convergence", __name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPORT_PATH = _REPO_ROOT / "data" / "full_stack_convergence_report.json"


@convergence_bp.route("/api/convergence/run", methods=["POST"])
def run_convergence():
    try:
        completed = subprocess.run(
            [sys.executable, "scripts/full_stack_convergence_test.py"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            logger.error("Convergence run failed: %s", completed.stderr.strip())
            return jsonify({
                "ok": False,
                "error": completed.stderr.strip() or completed.stdout.strip() or "Convergence run failed",
                "code": completed.returncode,
            }), 500

        if not _REPORT_PATH.exists():
            return jsonify({"ok": False, "error": "Report file missing after run"}), 500

        data = json.loads(_REPORT_PATH.read_text(encoding="utf-8"))
        return jsonify({
            "ok": True,
            "headline": data.get("headline", {}),
            "generated_at": data.get("generated_at"),
            "checkpoints": data.get("checkpoints", []),
            "stdout": completed.stdout.strip(),
        })
    except Exception as e:
        logger.exception("Convergence run crashed")
        return jsonify({"ok": False, "error": str(e)}), 500


@convergence_bp.route("/api/convergence/report", methods=["GET"])
def get_convergence_report():
    if not _REPORT_PATH.exists():
        return jsonify({"ok": False, "error": "No report found. Run /api/convergence/run first."}), 404
    try:
        data = json.loads(_REPORT_PATH.read_text(encoding="utf-8"))
        return jsonify({"ok": True, "report": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
