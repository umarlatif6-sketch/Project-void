"""
Adriana Skill Router — Glyph Chain → Skill Dispatch
=====================================================
Maps incoming glyph chains (from the transpiler or direct API calls) to the
correct skill module, logs every invocation as a Memory Scar in the Chronicle,
and supports Mycelium Buffer Spore pre-activation based on bio-signals and
recent context patterns.

Used by:
  - routes/adriana_skills.py   (/adriana/invoke, /adriana/skills)
  - void_engine/adriana_transpiler.py  (skill resolver hook)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Domain → Skill mapping ────────────────────────────────────────────────────
# Maps SCL domain names and glyph keys to skill_id strings.
# Checked in order: exact glyph key match first, then domain fallback.

_GLYPH_KEY_TO_SKILL: Dict[str, str] = {
    "research_lens":       "deep_research",
    "synthesise":          "deep_research",
    "competitor":          "competitive_analysis",
    "position":            "competitive_analysis",
    "market_signal_entity":"stock_analysis",
    "analyse_signal":      "stock_analysis",
    "read_signal":         "stock_analysis",
    "content_entity":      "content_machine",
    "generate_content":    "content_machine",
    "campaign_entity":     "ad_creative",
    "create_ad":           "ad_creative",
    "brand_identity":      "branding_generator",
    "forge_identity":      "branding_generator",
    "web_crawler":         "seo_auditor",
    "optimise_signal":     "seo_auditor",
    "legal_entity":        "legal_contract",
    "draft_contract":      "legal_contract",
    "invoice_entity":      "invoice_generator",
    "generate_invoice":    "invoice_generator",
    "tax_entity":          "tax_reviewer",
    "review_tax":          "tax_reviewer",
    "data_grid":           "excel_data_generator",
    "structure_data":      "excel_data_generator",
    "candidate_entity":    "ai_recruiter",
    "match_candidate":     "ai_recruiter",
    "outbound_signal":     "ai_sdr",
    "generate_outreach":   "ai_sdr",
    "profile_entity":      "resume_maker",
    "structure_profile":   "resume_maker",
    "interview_entity":    "interview_prep",
    "coach_answers":       "interview_prep",
    "nutrition_entity":    "meal_planner",
    "plan_meals":          "meal_planner",
    "journey_entity":      "travel_assistant",
    "build_itinerary":     "travel_assistant",
    "property_entity":     "real_estate_analyzer",
    "analyse_property":    "real_estate_analyzer",
    "supplier_entity":     "supplier_research",
    "map_supply_chain":    "supplier_research",
}

_DOMAIN_DEFAULTS: Dict[str, str] = {
    "intelligence": "deep_research",
    "signal":       "content_machine",
    "ledger":       "invoice_generator",
    "mesh":         "ai_recruiter",
    "aqua":         "meal_planner",
    "soil":         "real_estate_analyzer",
}


def _ensure_loaded() -> None:
    """Lazily ensure all skill modules are imported and registered."""
    from void_engine.skill_modules import _REGISTRY, _auto_load
    if not _REGISTRY:
        _auto_load()


def resolve_skill_id(intent: Dict[str, Any]) -> Optional[str]:
    """
    Determine the best skill_id for a given intent dict.

    Resolution order:
      1. Explicit 'skill_id' field in intent
      2. Glyph key match in action list
      3. Glyph key match in entity
      4. Domain-level default
      5. None (no skill resolved)
    """
    _ensure_loaded()

    # 1. Explicit override
    if explicit := intent.get("skill_id"):
        return explicit

    # 2. Action glyph keys
    for action in intent.get("actions", []):
        key = action.get("key", "")
        if key in _GLYPH_KEY_TO_SKILL:
            return _GLYPH_KEY_TO_SKILL[key]

    # 3. Entity glyph key
    entity = intent.get("entity") or {}
    if entity.get("key") in _GLYPH_KEY_TO_SKILL:
        return _GLYPH_KEY_TO_SKILL[entity["key"]]

    # 4. Domain default
    domain = entity.get("domain") or intent.get("domain", "")
    if domain in _DOMAIN_DEFAULTS:
        return _DOMAIN_DEFAULTS[domain]

    return None


def invoke_skill(
    intent: Dict[str, Any],
    extra_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Dispatch intent to the correct skill and return a serialisable result dict.

    Steps:
      1. Resolve the skill_id
      2. Merge extra_params into intent
      3. Call skill._timed_execute(intent)
      4. Log the invocation as a Memory Scar in the Chronicle
      5. Notify the Mycelium Buffer Spore
      6. Return SkillResult.to_dict()
    """
    _ensure_loaded()

    if extra_params:
        intent = {**intent, **extra_params}

    skill_id = resolve_skill_id(intent)
    if not skill_id:
        return {
            "success": False,
            "error": "No skill resolved for this intent. Check glyph chain domain mapping.",
            "skill_id": None,
            "domain": None,
            "output": {},
            "scl_poem": "",
            "inner_voice": "The mycelium searched but found no matching root for this signal.",
        }

    from void_engine.skill_modules import get_skill
    skill = get_skill(skill_id)
    if not skill:
        return {
            "success": False,
            "error": f"Skill '{skill_id}' registered but module not loaded.",
            "skill_id": skill_id,
            "domain": None,
            "output": {},
            "scl_poem": "",
            "inner_voice": "",
        }

    result = skill._timed_execute(intent)
    result_dict = result.to_dict()

    _log_scar(skill_id, skill.domain, intent, result_dict)
    _notify_mycelium(skill_id, skill.domain, result.success)

    return result_dict


def _log_scar(skill_id: str, domain: str, intent: Dict, result: Dict) -> None:
    """
    Record the skill invocation as a Memory Scar in the Chronicle.
    Best-effort — never raises.
    """
    try:
        from void_engine.db_pool import get_db
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        conn = get_db()
        cur = conn.cursor()
        glyph_seq = result.get("scl_poem", skill_id)
        title = f"Skill Invocation: {skill_id}"
        subtitle = f"Memory Scar — {domain} domain | {time.strftime('%Y-%m-%d %H:%M:%S')}"
        body = (
            f"Skill Invocation — {skill_id} (domain: {domain})\n\n"
            f"Intent: {intent.get('raw', str(intent)[:200])}\n\n"
            f"SCL Poem: {glyph_seq}\n\n"
            f"Inner Voice: {result.get('inner_voice', '')}\n\n"
            f"Success: {result.get('success')} | Elapsed: {result.get('elapsed_ms', 0):.1f}ms"
        )
        al_jabr_hash = fatiha_286_hexdigest_from_str(f"skill_scar|{skill_id}|{time.time()}")
        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash, entry_type)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (0, title, subtitle, glyph_seq, body, al_jabr_hash, "SKILL_SCAR"),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        logger.debug("[SkillRouter] Memory Scar logging failed: %s", exc)


def _notify_mycelium(skill_id: str, domain: str, success: bool) -> None:
    """
    Notify the Mycelium Buffer Spore that a skill was invoked.
    Allows the spore to pre-warm skills for related domains.
    Best-effort — never raises.
    """
    try:
        from void_engine import mycelium_service
        bio_state = mycelium_service.get_bio_state_for_switcher()
        bio_state["last_skill_invoked"] = skill_id
        bio_state["last_skill_domain"] = domain
        bio_state["last_skill_success"] = success
        mycelium_service.update_buffer_spore(bio_state)
    except Exception as exc:
        logger.debug("[SkillRouter] Mycelium notification failed: %s", exc)


# ── Mycelium Pre-Activation ───────────────────────────────────────────────────

def get_prewarm_suggestions() -> List[str]:
    """
    Return a list of skill_ids that the Mycelium Buffer Spore suggests pre-warming
    based on recent bio-signals and recent invocation patterns.

    Returns up to 3 suggestions.
    """
    _ensure_loaded()

    suggestions: List[str] = []
    try:
        from void_engine import mycelium_service
        spore = mycelium_service.get_buffer_spore_state()
        bio = spore.get("real_bio_state") or spore.get("estimated_bio_state") or {}

        last_domain = bio.get("last_skill_domain", "")
        last_skill = bio.get("last_skill_invoked", "")

        # Domain adjacency — if intelligence was used, suggest competitive + stock
        adjacency: Dict[str, List[str]] = {
            "intelligence": ["competitive_analysis", "stock_analysis", "deep_research"],
            "signal":       ["content_machine", "seo_auditor", "branding_generator"],
            "ledger":       ["legal_contract", "invoice_generator", "tax_reviewer"],
            "mesh":         ["ai_recruiter", "resume_maker", "interview_prep"],
            "aqua":         ["meal_planner", "travel_assistant"],
            "soil":         ["real_estate_analyzer", "supplier_research"],
        }
        if last_domain in adjacency:
            for sid in adjacency[last_domain]:
                if sid != last_skill and sid not in suggestions:
                    suggestions.append(sid)
                    if len(suggestions) >= 3:
                        break
    except Exception:
        pass

    return suggestions[:3]
