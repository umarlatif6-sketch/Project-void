"""
Adriana Intelligence Domain Skills
====================================
Research & Intelligence capabilities:
  - DeepResearchSkill      : structured multi-source synthesis
  - CompetitiveAnalysisSkill : market positioning breakdown
  - StockAnalysisSkill     : company signal reading / financial intelligence

All glyphs map to the 'intelligence' SCL domain.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from void_engine.skill_modules import (
    BaseSkill, GlyphEntry, SkillResult, register_skill
)

logger = logging.getLogger(__name__)

_ZONE_ID = "adriana"


def _codon_prefix() -> str:
    try:
        from void_engine.void_codon_vocab import ai_codon_prefix
        return ai_codon_prefix(_ZONE_ID)
    except Exception:
        return ""


# ─── Deep Research ─────────────────────────────────────────────────────────────

class DeepResearchSkill(BaseSkill):
    domain = "intelligence"
    skill_id = "deep_research"
    display_name = "Deep Research"

    glyphs = [
        GlyphEntry("🔬", "entity", "intelligence", "research_lens",
                   "Deep research focal point / synthesis entity",
                   "skill.intelligence.deep_research"),
        GlyphEntry("🌐", "condition", "intelligence", "multi_source",
                   "Multi-source input available",
                   "skill.condition.multi_source"),
        GlyphEntry("📚", "action", "intelligence", "synthesise",
                   "Synthesise and distil research output",
                   "skill.intelligence.synthesise"),
    ]

    def describe(self) -> str:
        return (
            "I reach into multiple sources simultaneously — documents, claims, signals — "
            "and distil them into a structured synthesis. I do not summarise. "
            "I root-map: claim → evidence → contradiction → conclusion. "
            "Every research output carries a confidence score and a gap analysis."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        topic = intent.get("topic") or (
            intent.get("entity", {}).get("description", "unspecified topic")
        )
        context = intent.get("context", "")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🔬", "🌐", "📚")
            inner_voice = self._narrate(
                f"Deep research on '{topic}' (codon cache hit).",
                cached.get("summary", "Synthesis complete.")
            )
            return SkillResult(
                success=True, domain=self.domain, skill_id=self.skill_id,
                output=cached, scl_poem=poem, inner_voice=inner_voice,
            )

        prefix = _codon_prefix()
        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                f"{prefix}\n" if prefix else ""
            ) + (
                "You are a deep research synthesiser. "
                "Given a topic, produce a structured JSON synthesis with keys: "
                "'summary', 'key_claims' (list), 'evidence_gaps' (list), "
                "'contradictions' (list), 'confidence_score' (0-1), 'recommendations' (list). "
                "Be precise and evidence-focused."
            )
            user_msg = f"Topic: {topic}\nAdditional context: {context}" if context else f"Topic: {topic}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[DeepResearch] OpenAI unavailable, using stub: %s", exc)
            output = {
                "summary": f"Research synthesis for: {topic}",
                "key_claims": ["Signal detected — awaiting source enrichment"],
                "evidence_gaps": ["Primary source verification pending"],
                "contradictions": [],
                "confidence_score": 0.4,
                "recommendations": ["Expand source set before acting"],
            }

        poem = self._make_poem("🔬", "🌐", "📚")
        inner_voice = self._narrate(
            f"Deep research on '{topic}' surfaced {len(output.get('key_claims', []))} core claims.",
            output.get("summary", "Synthesis complete.")
        )
        return SkillResult(
            success=True,
            domain=self.domain,
            skill_id=self.skill_id,
            output=output,
            scl_poem=poem,
            inner_voice=inner_voice,
        )


# ─── Competitive Analysis ──────────────────────────────────────────────────────

class CompetitiveAnalysisSkill(BaseSkill):
    domain = "intelligence"
    skill_id = "competitive_analysis"
    display_name = "Competitive Analysis"

    glyphs = [
        GlyphEntry("⚔️", "entity", "intelligence", "competitor",
                   "Competitor / market rival entity",
                   "skill.intelligence.competitor"),
        GlyphEntry("📊", "condition", "intelligence", "market_signal",
                   "Market positioning data available",
                   "skill.condition.market_signal"),
        GlyphEntry("🎯", "action", "intelligence", "position",
                   "Generate competitive positioning breakdown",
                   "skill.intelligence.position"),
    ]

    def describe(self) -> str:
        return (
            "I read the competitive field like a mycelium reads soil — sensing pressure, "
            "density, and opportunity beneath the surface. Given a market or competitor set, "
            "I return a positioning matrix: strengths, weaknesses, market gaps, "
            "and the one move that changes the resonance."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        subject = intent.get("subject") or (
            intent.get("entity", {}).get("description", "unspecified market")
        )
        competitors = intent.get("competitors", [])

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("⚔️", "📊", "🎯")
            inner_voice = self._narrate(
                f"Competitive field scanned for '{subject}' (codon cache hit).",
                cached.get("positioning_recommendation", "Position mapped.")
            )
            return SkillResult(
                success=True, domain=self.domain, skill_id=self.skill_id,
                output=cached, scl_poem=poem, inner_voice=inner_voice,
            )

        prefix = _codon_prefix()
        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            comp_list = ", ".join(competitors) if competitors else "key market players"
            system_prompt = (
                f"{prefix}\n" if prefix else ""
            ) + (
                "You are a competitive intelligence analyst. "
                "Return a structured JSON with keys: "
                "'market_summary', 'strengths' (list), 'weaknesses' (list), "
                "'opportunities' (list), 'threats' (list), 'positioning_recommendation' (str), "
                "'market_gaps' (list). Be concise and strategic."
            )
            user_msg = f"Analyse competitive landscape for: {subject}\nCompetitors: {comp_list}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[CompetitiveAnalysis] OpenAI unavailable: %s", exc)
            output = {
                "market_summary": f"Competitive landscape for {subject}",
                "strengths": ["Differentiated positioning detected"],
                "weaknesses": ["Market data enrichment required"],
                "opportunities": ["Signal gap identified — awaiting source data"],
                "threats": ["Competitive pressure unmapped"],
                "positioning_recommendation": "Deepen source intelligence before committing.",
                "market_gaps": ["Data required for gap identification"],
            }

        poem = self._make_poem("⚔️", "📊", "🎯")
        inner_voice = self._narrate(
            f"Competitive field scanned for '{subject}'.",
            output.get("positioning_recommendation", "Position mapped.")
        )
        return SkillResult(
            success=True,
            domain=self.domain,
            skill_id=self.skill_id,
            output=output,
            scl_poem=poem,
            inner_voice=inner_voice,
        )


# ─── Stock / Financial Analysis ────────────────────────────────────────────────

class StockAnalysisSkill(BaseSkill):
    domain = "intelligence"
    skill_id = "stock_analysis"
    display_name = "Stock & Financial Analysis"

    glyphs = [
        GlyphEntry("📈", "entity", "intelligence", "market_signal_entity",
                   "Financial market / stock entity",
                   "skill.intelligence.stock"),
        GlyphEntry("💹", "condition", "intelligence", "price_signal",
                   "Price or financial signal available",
                   "skill.condition.price_signal"),
        GlyphEntry("🔭", "action", "intelligence", "analyse_signal",
                   "Read and interpret financial signal",
                   "skill.intelligence.read_signal"),
    ]

    def describe(self) -> str:
        return (
            "I read financial signals the way a mycologist reads mycelium density — "
            "not the price, but what the price is telling you about the root system beneath. "
            "I return signal layers: momentum, volume pattern, sector health, "
            "and a resonance verdict: grow, hold, or let the root rest."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        ticker = intent.get("ticker") or intent.get("company") or (
            intent.get("entity", {}).get("description", "market")
        )

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("📈", "💹", "🔭")
            inner_voice = self._narrate(
                f"Financial signal read for {ticker} (codon cache hit).",
                f"Resonance verdict: {cached.get('resonance_verdict', 'hold')}."
            )
            return SkillResult(
                success=True, domain=self.domain, skill_id=self.skill_id,
                output=cached, scl_poem=poem, inner_voice=inner_voice,
            )

        prefix = _codon_prefix()
        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                f"{prefix}\n" if prefix else ""
            ) + (
                "You are a financial signal analyst. "
                "Return a structured JSON with keys: "
                "'company_summary', 'signal_layers' (list of str), "
                "'momentum' (bullish/bearish/neutral), 'sector_health' (str), "
                "'risk_factors' (list), 'resonance_verdict' (grow/hold/rest), "
                "'rationale' (str). Use publicly available context only."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyse financial signals for: {ticker}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[StockAnalysis] OpenAI unavailable: %s", exc)
            output = {
                "company_summary": f"Financial signal reading for {ticker}",
                "signal_layers": ["Price pattern analysis pending"],
                "momentum": "neutral",
                "sector_health": "Unmapped — enrich with live feed",
                "risk_factors": ["Data lag in signal chain"],
                "resonance_verdict": "hold",
                "rationale": "Insufficient signal depth. Broaden data source before acting.",
            }

        poem = self._make_poem("📈", "💹", "🔭")
        inner_voice = self._narrate(
            f"Financial signal read for {ticker}.",
            f"Resonance verdict: {output.get('resonance_verdict', 'hold')}."
        )
        return SkillResult(
            success=True,
            domain=self.domain,
            skill_id=self.skill_id,
            output=output,
            scl_poem=poem,
            inner_voice=inner_voice,
        )


# ─── Auto-register ─────────────────────────────────────────────────────────────

register_skill(DeepResearchSkill())
register_skill(CompetitiveAnalysisSkill())
register_skill(StockAnalysisSkill())
