"""
Adriana Skills API Routes
==========================
Routes:
  GET  /adriana/skills         — list all registered skills and glyph mappings
  POST /adriana/invoke         — invoke a skill by glyph chain or skill_id
  GET  /adriana/skills/prewarm — suggest pre-warm skill candidates from mycelium
"""

import logging
from flask import Blueprint, jsonify, request, session
from routes.auth import login_required, _check_rate_limit

logger = logging.getLogger(__name__)

adriana_skills_bp = Blueprint("adriana_skills", __name__)


def _ensure_skills_loaded() -> None:
    """Lazily load all skill modules into the registry."""
    from void_engine.skill_modules import _REGISTRY, _auto_load
    if not _REGISTRY:
        _auto_load()


@adriana_skills_bp.route("/adriana/skills", methods=["GET"])
def list_skills():
    """
    Return all registered Adriana skill modules with their glyph mappings.

    Response:
      {
        "total": int,
        "skills": [
          {
            "skill_id": str,
            "display_name": str,
            "domain": str,
            "description": str,
            "glyphs": [{glyph, category, key, description}, ...]
          }, ...
        ],
        "domains": {domain: [skill_id, ...], ...}
      }
    """
    _ensure_skills_loaded()

    try:
        from void_engine.skill_modules import list_skills as _list
        skills = _list()

        domains: dict = {}
        for sk in skills:
            d = sk["domain"]
            domains.setdefault(d, []).append(sk["skill_id"])

        return jsonify({
            "success": True,
            "total": len(skills),
            "skills": skills,
            "domains": domains,
        })
    except Exception as exc:
        logger.exception("[AdrianSkills] list_skills failed: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@adriana_skills_bp.route("/adriana/invoke", methods=["POST"])
@login_required
def invoke_skill():
    """
    Invoke an Adriana skill by glyph chain or explicit skill_id.

    Request body (JSON):
      {
        "glyph_chain": "🔬-🌐-📚",   # optional — transpiled to intent
        "skill_id":    "deep_research", # optional — direct dispatch
        "intent":      {...},           # optional — raw intent dict
        "params":      {...},           # optional — extra params merged into intent
      }

    At least one of glyph_chain, skill_id, or intent must be provided.

    Response: SkillResult.to_dict()
    """
    if not _check_rate_limit():
        return jsonify({"success": False, "error": "Too many requests. Please wait and try again."}), 429

    _ensure_skills_loaded()

    data = request.json or {}
    glyph_chain = data.get("glyph_chain", "").strip()
    skill_id = data.get("skill_id", "").strip()
    raw_intent = data.get("intent") or {}
    params = data.get("params") or {}

    if not glyph_chain and not skill_id and not raw_intent:
        return jsonify({
            "success": False,
            "error": "Provide at least one of: glyph_chain, skill_id, or intent",
        }), 400

    intent: dict = {}

    if glyph_chain:
        try:
            from void_engine.adriana_transpiler import AdrianaTranspiler
            transpiler = AdrianaTranspiler()
            result = transpiler.transpile(glyph_chain)
            if result.intents:
                intent = result.intents[0].to_dict()
            else:
                intent = {"raw": glyph_chain}
        except Exception as exc:
            logger.warning("[AdrianInvoke] Transpile failed for '%s': %s", glyph_chain, exc)
            intent = {"raw": glyph_chain}

    if raw_intent:
        intent.update(raw_intent)

    if skill_id:
        intent["skill_id"] = skill_id

    if params:
        intent.update(params)

    try:
        from void_engine.skill_modules.skill_router import invoke_skill as _invoke
        result_dict = _invoke(intent)

        _log_invocation(glyph_chain or skill_id or "direct_intent", result_dict)

        status_code = 200 if result_dict.get("success") else 422
        return jsonify(result_dict), status_code
    except Exception as exc:
        logger.exception("[AdrianInvoke] invoke_skill raised: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@adriana_skills_bp.route("/adriana/skills/prewarm", methods=["GET"])
def prewarm_suggestions():
    """
    Return skill pre-warm suggestions from the Mycelium Buffer Spore.

    Response:
      {
        "suggestions": ["skill_id", ...],
        "mycelium_state": {...}
      }
    """
    _ensure_skills_loaded()

    try:
        from void_engine.skill_modules.skill_router import get_prewarm_suggestions
        suggestions = get_prewarm_suggestions()

        mycelium_state = {}
        try:
            from void_engine.mycelium_service import get_buffer_spore_state
            mycelium_state = get_buffer_spore_state()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "mycelium_state": mycelium_state,
        })
    except Exception as exc:
        logger.exception("[AdrianPrewarm] failed: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


def _log_invocation(trigger: str, result: dict) -> None:
    """Write skill invocation to application log (non-blocking)."""
    logger.info(
        "[AdrianSkills] Invoked via='%s' skill='%s' domain='%s' success=%s elapsed=%.1fms",
        trigger,
        result.get("skill_id", "?"),
        result.get("domain", "?"),
        result.get("success"),
        result.get("elapsed_ms", 0),
    )
