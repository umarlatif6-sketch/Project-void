"""
Admin route for Adriana Core — Fine-Tuned Inference Layer

Routes:
  GET  /admin/adriana-core        — Status dashboard
  POST /admin/adriana-core/test   — Live test prompt
  POST /admin/adriana-core/refresh-model — Re-check for latest fine-tuned model
"""

import logging
from flask import Blueprint, jsonify, render_template, request, session
from routes.auth import admin_required

logger = logging.getLogger(__name__)

adriana_core_admin_bp = Blueprint("adriana_core_admin", __name__)


@adriana_core_admin_bp.route("/admin/adriana-core", methods=["GET"])
@admin_required
def adriana_core_status():
    """Admin status dashboard for Adriana Core."""
    fine_tuned_model = None
    jobs = []
    router_config = []
    cost_summary = {"by_tier": [], "grand_total_usd": 0.0, "grand_total_calls": 0, "recent_calls": []}
    corpus_size = 0
    training_pairs = 0

    try:
        from void_engine.adriana_finetune import (
            get_latest_fine_tuned_model, list_jobs, init_finetune_tables
        )
        init_finetune_tables()
        fine_tuned_model = get_latest_fine_tuned_model()
        jobs = list_jobs(limit=10)
    except Exception as e:
        logger.warning("Could not load fine-tune jobs: %s", e)

    try:
        from void_engine.aljabr_transpiler import get_model_router
        router = get_model_router()
        router_config = router.get_config_display()
        cost_summary = router.get_cost_summary()
    except Exception as e:
        logger.warning("Could not load model router: %s", e)

    try:
        from void_engine.adriana_corpus import build_corpus
        corpus = build_corpus()
        corpus_size = len(corpus)
    except Exception as e:
        logger.warning("Could not build corpus: %s", e)

    if jobs:
        best = max(jobs, key=lambda j: j.get("training_pairs", 0) or 0)
        training_pairs = best.get("training_pairs", 0) or 0

    last_token_cost = _get_last_token_cost(cost_summary)

    return render_template(
        "admin_adriana_core.html",
        fine_tuned_model=fine_tuned_model,
        jobs=jobs,
        router_config=router_config,
        cost_summary=cost_summary,
        corpus_size=corpus_size,
        training_pairs=training_pairs,
        last_token_cost=last_token_cost,
    )


@adriana_core_admin_bp.route("/admin/adriana-core/test", methods=["POST"])
@admin_required
def adriana_core_test():
    """Live test: send a prompt through AdrianCore and return raw + expanded response."""
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "prompt is required"}), 400
    if len(prompt) > 1000:
        return jsonify({"error": "prompt too long (max 1000 chars)"}), 400

    try:
        from void_engine.adriana_core import query as adriana_core_query, _classify_to_codon
        codon, expansion = _classify_to_codon(prompt)
        result = adriana_core_query(prompt)
        return jsonify({
            "ok": result.get("ok", False),
            "response": result.get("response"),
            "codon_chain_before": codon,
            "codon_chain_after": result.get("codon_chain"),
            "expansion": expansion,
            "model_used": result.get("model_used"),
            "token_cost": result.get("token_cost", 0),
            "layer": result.get("layer"),
            "error": result.get("error"),
        })
    except Exception as e:
        logger.error("adriana_core_test failed: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@adriana_core_admin_bp.route("/admin/adriana-core/refresh-model", methods=["POST"])
@admin_required
def adriana_core_refresh_model():
    """Re-check DB for latest fine-tuned model and update ModelRouter PRECISION tier."""
    try:
        from void_engine.adriana_finetune import get_latest_fine_tuned_model
        from void_engine.aljabr_transpiler import get_model_router, TASK_PRECISION, _apply_fine_tuned_model_if_available

        model_id = get_latest_fine_tuned_model()
        if model_id:
            router = get_model_router()
            _apply_fine_tuned_model_if_available(router)
            return jsonify({"ok": True, "model_id": model_id, "message": f"PRECISION tier updated to {model_id}"})
        return jsonify({"ok": True, "model_id": None, "message": "No fine-tuned model found in database yet."})
    except Exception as e:
        logger.error("adriana_core_refresh_model failed: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


def _get_last_token_cost(cost_summary: dict) -> float:
    recent = cost_summary.get("recent_calls", [])
    adriana_calls = [c for c in recent if "adriana" in (c.get("task_label") or "").lower()]
    if adriana_calls:
        return adriana_calls[0].get("cost_usd", 0.0)
    return 0.0
