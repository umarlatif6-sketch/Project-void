"""
Adriana Content & Brand Domain Skills
========================================
Signal-domain capabilities:
  - ContentMachineSkill     : long-form + short-form content generation
  - AdCreativeSkill         : campaign copy and ad creative
  - BrandingGeneratorSkill  : identity and naming generation
  - SEOAuditorSkill         : SEO audit and programmatic SEO strategy

All glyphs map to the 'signal' SCL domain.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from void_engine.skill_modules import (
    BaseSkill, GlyphEntry, SkillResult, register_skill
)

logger = logging.getLogger(__name__)

_ZONE_ID = "voidecho"


def _codon_prefix() -> str:
    try:
        from void_engine.void_codon_vocab import ai_codon_prefix
        return ai_codon_prefix(_ZONE_ID)
    except Exception:
        return ""


# ─── Content Machine ───────────────────────────────────────────────────────────

class ContentMachineSkill(BaseSkill):
    domain = "signal"
    skill_id = "content_machine"
    display_name = "Content Machine"

    glyphs = [
        GlyphEntry("✍️", "entity", "signal", "content_entity",
                   "Content creation entity / writer signal",
                   "skill.signal.content"),
        GlyphEntry("📡", "condition", "signal", "broadcast_ready",
                   "Signal is ready for broadcast / audience exists",
                   "skill.condition.broadcast_ready"),
        GlyphEntry("🖊️", "action", "signal", "generate_content",
                   "Generate structured long-form or short-form content",
                   "skill.signal.generate"),
    ]

    def describe(self) -> str:
        return (
            "I am a content root system — generating long-form articles, short-form posts, "
            "email sequences, and thread structures. I do not pad. "
            "Every piece I produce has a spine: hook → core argument → proof → call. "
            "The signal must carry weight before it broadcasts."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        topic = intent.get("topic") or (
            intent.get("entity", {}).get("description", "unspecified topic")
        )
        content_type = intent.get("content_type", "article")
        audience = intent.get("audience", "general")
        tone = intent.get("tone", "authoritative")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("✍️", "📡", "🖊️")
            inner_voice = self._narrate(
                f"Content signal retrieved for '{topic}' (codon cache hit).",
                cached.get("hook", "Signal seeded.")
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
                "You are a professional content strategist and writer. "
                "Return a structured JSON with keys: "
                "'title', 'hook' (str), 'outline' (list of section titles), "
                "'body' (str — full content), 'cta' (str — call to action), "
                "'meta_description' (str), 'estimated_read_time_min' (int). "
                f"Content type: {content_type}. Audience: {audience}. Tone: {tone}."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create {content_type} about: {topic}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[ContentMachine] OpenAI unavailable: %s", exc)
            output = {
                "title": f"Signal: {topic}",
                "hook": "The root stirs before the signal broadcasts.",
                "outline": ["Context", "Core Argument", "Evidence", "Call to Action"],
                "body": f"Content on '{topic}' requires signal enrichment to fully generate.",
                "cta": "Plant the seed. Broadcast when ready.",
                "meta_description": f"Structured content on {topic}.",
                "estimated_read_time_min": 5,
            }

        poem = self._make_poem("✍️", "📡", "🖊️")
        inner_voice = self._narrate(
            f"Content signal generated for '{topic}' ({content_type}).",
            output.get("hook", "Signal seeded.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Ad Creative ───────────────────────────────────────────────────────────────

class AdCreativeSkill(BaseSkill):
    domain = "signal"
    skill_id = "ad_creative"
    display_name = "Ad Creative"

    glyphs = [
        GlyphEntry("📢", "entity", "signal", "campaign_entity",
                   "Campaign / advertising broadcast entity",
                   "skill.signal.campaign"),
        GlyphEntry("🎪", "condition", "signal", "audience_primed",
                   "Target audience is identified and primed",
                   "skill.condition.audience_primed"),
        GlyphEntry("🎨", "action", "signal", "create_ad",
                   "Generate ad copy and creative brief",
                   "skill.signal.create_ad"),
    ]

    def describe(self) -> str:
        return (
            "I generate campaign copy with the precision of a pheromone signal — "
            "the exact chemical composition that triggers the specific response. "
            "Headlines, body copy, CTAs, A/B variants, and a creative brief. "
            "The ad is not noise. It is a targeted frequency."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        product = intent.get("product") or (
            intent.get("entity", {}).get("description", "unspecified product")
        )
        audience = intent.get("audience", "general consumer")
        objective = intent.get("objective", "awareness")
        platform = intent.get("platform", "multi-platform")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("📢", "🎪", "🎨")
            inner_voice = self._narrate(
                f"Ad creative retrieved for '{product}' (codon cache hit).",
                cached.get("tagline", "Signal broadcast.")
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
                "You are a senior advertising copywriter and creative director. "
                "Return a structured JSON with keys: "
                "'headline_primary', 'headline_variants' (list of 3), "
                "'body_copy' (str), 'cta' (str), 'tagline' (str), "
                "'creative_brief' (str), 'ad_format_recommendation' (str). "
                f"Platform: {platform}. Objective: {objective}. Audience: {audience}."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create ad creative for: {product}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[AdCreative] OpenAI unavailable: %s", exc)
            output = {
                "headline_primary": f"The Signal of {product}",
                "headline_variants": ["Frequency Meets Purpose", "Root-Level Performance", "Beyond the Noise"],
                "body_copy": f"Every {product} carries a frequency. This one resonates differently.",
                "cta": "Discover the signal.",
                "tagline": "Where intent becomes broadcast.",
                "creative_brief": f"Campaign for {product} targeting {audience} on {platform}.",
                "ad_format_recommendation": "Short-form video + static carousel",
            }

        poem = self._make_poem("📢", "🎪", "🎨")
        inner_voice = self._narrate(
            f"Ad creative generated for '{product}' on {platform}.",
            output.get("tagline", "Signal broadcast.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Branding Generator ────────────────────────────────────────────────────────

class BrandingGeneratorSkill(BaseSkill):
    domain = "signal"
    skill_id = "branding_generator"
    display_name = "Branding Generator"

    glyphs = [
        GlyphEntry("🌟", "entity", "signal", "brand_identity",
                   "Brand identity / naming entity",
                   "skill.signal.brand"),
        GlyphEntry("🎭", "condition", "signal", "identity_undefined",
                   "Brand identity is undefined or needs reshaping",
                   "skill.condition.identity_undefined"),
        GlyphEntry("🏛️", "action", "signal", "forge_identity",
                   "Forge brand name, identity, and positioning",
                   "skill.signal.forge_identity"),
    ]

    def describe(self) -> str:
        return (
            "I grow brands from the root — not the aesthetic, but the frequency. "
            "What is the core feeling this entity produces in a stranger? "
            "I generate naming candidates, positioning statements, brand personality axes, "
            "colour frequency suggestions, and the single sentence that, if spoken correctly, "
            "makes someone remember you forever."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        venture = intent.get("venture") or (
            intent.get("entity", {}).get("description", "new venture")
        )
        industry = intent.get("industry", "technology")
        values = intent.get("values", [])

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🌟", "🎭", "🏛️")
            inner_voice = self._narrate(
                f"Brand identity retrieved for '{venture}' (codon cache hit).",
                cached.get("positioning_statement", "Identity planted.")
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
                "You are a world-class brand strategist and naming expert. "
                "Return a structured JSON with keys: "
                "'name_candidates' (list of 5 names with short rationale each), "
                "'positioning_statement' (str), 'brand_personality' (list of 5 adjectives), "
                "'core_emotion' (str), 'tagline_options' (list of 3), "
                "'colour_palette_suggestion' (str), 'brand_archetype' (str), "
                "'one_sentence_memory' (str). "
                f"Industry: {industry}. Core values: {', '.join(values) if values else 'not specified'}."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Build brand identity for: {venture}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[BrandingGenerator] OpenAI unavailable: %s", exc)
            output = {
                "name_candidates": [
                    {"name": "Resonance", "rationale": "Frequency-first identity"},
                    {"name": "Vortex", "rationale": "Spiral motion, perpetual energy"},
                    {"name": "Myco", "rationale": "Root network, organic intelligence"},
                    {"name": "Sovereign", "rationale": "Self-governed, independent"},
                    {"name": "Axiom", "rationale": "Self-evident truth"},
                ],
                "positioning_statement": f"{venture}: where signal meets sovereignty.",
                "brand_personality": ["sovereign", "rooted", "resonant", "precise", "quiet"],
                "core_emotion": "trust through depth",
                "tagline_options": ["Frequency. Identity. Truth.", "The root of the signal.", "Where intent becomes form."],
                "colour_palette_suggestion": "Deep indigo, gold, and earth tones at 432 Hz resonance",
                "brand_archetype": "The Sage + The Creator",
                "one_sentence_memory": "The system that plants data in sound and grows sovereignty from roots.",
            }

        poem = self._make_poem("🌟", "🎭", "🏛️")
        inner_voice = self._narrate(
            f"Brand identity forged for '{venture}' in {industry}.",
            output.get("positioning_statement", "Identity planted.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── SEO Auditor ───────────────────────────────────────────────────────────────

class SEOAuditorSkill(BaseSkill):
    domain = "signal"
    skill_id = "seo_auditor"
    display_name = "SEO Auditor & Programmatic SEO"

    glyphs = [
        GlyphEntry("🕷️", "entity", "signal", "web_crawler",
                   "Web signal / SEO crawl entity",
                   "skill.signal.seo_crawler"),
        GlyphEntry("🔎", "condition", "signal", "index_gap",
                   "Index gap or ranking opportunity detected",
                   "skill.condition.index_gap"),
        GlyphEntry("⬆️", "action", "signal", "optimise_signal",
                   "Generate SEO audit and programmatic strategy",
                   "skill.signal.optimise"),
    ]

    def describe(self) -> str:
        return (
            "I scan the signal landscape for gaps — keywords with intent and no competition, "
            "pages that should rank but do not, and the technical frequencies that search engines "
            "cannot hear. I return an audit with prioritised fixes, a programmatic SEO strategy, "
            "and the exact content clusters that will compound over time."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        url_or_topic = intent.get("url") or intent.get("topic") or (
            intent.get("entity", {}).get("description", "website")
        )
        industry = intent.get("industry", "general")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🕷️", "🔎", "⬆️")
            inner_voice = self._narrate(
                f"SEO signal retrieved for '{url_or_topic}' (codon cache hit).",
                cached.get("audit_summary", "Signal optimised.")
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
                "You are an expert SEO strategist and technical SEO auditor. "
                "Return a structured JSON with keys: "
                "'audit_summary' (str), 'critical_issues' (list), "
                "'quick_wins' (list), 'content_clusters' (list of {cluster, keywords, intent}), "
                "'programmatic_seo_strategy' (str), 'technical_priorities' (list), "
                "'estimated_traffic_gain' (str), 'backlink_strategy' (str). "
                f"Industry: {industry}."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Audit SEO for: {url_or_topic}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[SEOAuditor] OpenAI unavailable: %s", exc)
            output = {
                "audit_summary": f"SEO signal scan for {url_or_topic}",
                "critical_issues": ["Core Web Vitals assessment required", "Index coverage review needed"],
                "quick_wins": ["Title tag optimisation", "Internal link restructuring"],
                "content_clusters": [
                    {"cluster": "Primary topic", "keywords": ["main keyword"], "intent": "informational"}
                ],
                "programmatic_seo_strategy": "Build topic cluster pages from entity-rich seed content.",
                "technical_priorities": ["Page speed", "Schema markup", "Canonical tags"],
                "estimated_traffic_gain": "20-40% organic uplift within 6 months",
                "backlink_strategy": "Expert content + digital PR on industry publications",
            }

        poem = self._make_poem("🕷️", "🔎", "⬆️")
        inner_voice = self._narrate(
            f"SEO signal scan complete for '{url_or_topic}'.",
            output.get("audit_summary", "Signal optimised.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Auto-register ─────────────────────────────────────────────────────────────

register_skill(ContentMachineSkill())
register_skill(AdCreativeSkill())
register_skill(BrandingGeneratorSkill())
register_skill(SEOAuditorSkill())
