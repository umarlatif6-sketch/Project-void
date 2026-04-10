"""
Adriana Life & Environment Domain Skills
==========================================
Aqua/Soil-domain capabilities (physical world):
  - MealPlannerSkill       : nutritional routing and meal planning
  - TravelAssistantSkill   : itinerary building
  - RealEstateAnalyzerSkill: property signal reading
  - SupplierResearchSkill  : supply chain intelligence

All glyphs map to the 'aqua' or 'soil' SCL domain.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from void_engine.skill_modules import (
    BaseSkill, GlyphEntry, SkillResult, register_skill
)

logger = logging.getLogger(__name__)

_ZONE_ID = "void_plane"


def _codon_prefix() -> str:
    try:
        from void_engine.void_codon_vocab import ai_codon_prefix
        return ai_codon_prefix(_ZONE_ID)
    except Exception:
        return ""


# ─── Meal Planner ──────────────────────────────────────────────────────────────

class MealPlannerSkill(BaseSkill):
    domain = "aqua"
    skill_id = "meal_planner"
    display_name = "Meal Planner"

    glyphs = [
        GlyphEntry("🌿", "entity", "aqua", "nutrition_entity",
                   "Nutritional / dietary routing entity",
                   "skill.aqua.nutrition"),
        GlyphEntry("🍽️", "condition", "aqua", "diet_goal_set",
                   "Dietary goal or restriction is defined",
                   "skill.condition.diet_goal_set"),
        GlyphEntry("🥗", "action", "aqua", "plan_meals",
                   "Generate structured meal plan with nutritional routing",
                   "skill.aqua.plan_meals"),
    ]

    def describe(self) -> str:
        return (
            "I route nutrition the way mycelium routes resources through a forest — "
            "efficiently, without waste, aligned to what the organism needs. "
            "Given dietary goals, restrictions, and preferences, I return a weekly meal plan "
            "with macros, shopping list, and the reasoning behind every food choice. "
            "Food is soil. The body is the root."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        goal = intent.get("goal") or (
            intent.get("entity", {}).get("description", "balanced nutrition")
        )
        restrictions = intent.get("restrictions", [])
        preferences = intent.get("preferences", [])
        days = intent.get("days", 7)

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🌿", "🍽️", "🥗")
            inner_voice = self._narrate(
                f"{days}-day meal plan retrieved for goal: {goal} (codon cache hit).",
                cached.get("nutritional_rationale", "The body is the root. Feed it with intention.")
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
                "You are a nutritionist and meal planning expert. "
                "Return a structured JSON with keys: "
                f"'meal_plan' (list of {days} day objects, each with 'day', 'breakfast', 'lunch', 'dinner', 'snack', 'daily_macros': {{calories, protein_g, carbs_g, fat_g}}), "
                "'weekly_shopping_list' (list of ingredients), "
                "'nutritional_rationale' (str), 'prep_tips' (list). "
                f"Goal: {goal}. Restrictions: {', '.join(restrictions) if restrictions else 'none'}. "
                f"Preferences: {', '.join(preferences) if preferences else 'none'}."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create {days}-day meal plan for goal: {goal}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[MealPlanner] OpenAI unavailable: %s", exc)
            output = {
                "meal_plan": [
                    {
                        "day": f"Day {i+1}",
                        "breakfast": "Oats with berries and nuts",
                        "lunch": "Grilled chicken salad with mixed leaves",
                        "dinner": "Baked salmon with roasted vegetables",
                        "snack": "Apple and almond butter",
                        "daily_macros": {"calories": 1800, "protein_g": 120, "carbs_g": 180, "fat_g": 60},
                    }
                    for i in range(days)
                ],
                "weekly_shopping_list": ["Oats", "Mixed berries", "Almonds", "Chicken breast", "Salmon", "Mixed salad leaves", "Seasonal vegetables", "Apples", "Almond butter"],
                "nutritional_rationale": f"Plan structured for {goal} with balanced macronutrients and micronutrient density.",
                "prep_tips": ["Batch cook grains on Sunday", "Pre-portion snacks", "Keep frozen vegetables as backup"],
            }

        poem = self._make_poem("🌿", "🍽️", "🥗")
        inner_voice = self._narrate(
            f"{days}-day meal plan generated for goal: {goal}.",
            output.get("nutritional_rationale", "The body is the root. Feed it with intention.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Travel Assistant ──────────────────────────────────────────────────────────

class TravelAssistantSkill(BaseSkill):
    domain = "aqua"
    skill_id = "travel_assistant"
    display_name = "Travel Assistant"

    glyphs = [
        GlyphEntry("✈️", "entity", "aqua", "journey_entity",
                   "Travel / journey routing entity",
                   "skill.aqua.journey"),
        GlyphEntry("🗺️", "condition", "aqua", "destination_set",
                   "Destination and travel parameters are defined",
                   "skill.condition.destination_set"),
        GlyphEntry("🧳", "action", "aqua", "build_itinerary",
                   "Build structured travel itinerary",
                   "skill.aqua.itinerary"),
    ]

    def describe(self) -> str:
        return (
            "I build itineraries the way water finds the most efficient path — "
            "no wasted movement, every stop purposeful. "
            "Given destination, duration, and travel style, I return a day-by-day structure: "
            "transport, accommodation strategy, experiences, and the one place "
            "that most travel guides have missed."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        destination = intent.get("destination") or (
            intent.get("entity", {}).get("description", "destination")
        )
        duration_days = int(intent.get("duration_days", 5))
        travel_style = intent.get("travel_style", "cultural exploration")
        budget = intent.get("budget", "mid-range")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("✈️", "🗺️", "🧳")
            inner_voice = self._narrate(
                f"Travel itinerary retrieved for {destination} (codon cache hit).",
                cached.get("destination_overview", "The journey is mapped. Move with intention.")
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
                "You are an expert travel planner and destination specialist. "
                "Return a structured JSON with keys: "
                f"'destination_overview' (str), 'itinerary' (list of {duration_days} day objects: "
                "each with 'day', 'morning', 'afternoon', 'evening', 'accommodation_tip', 'transport_note'), "
                "'hidden_gems' (list of 3 lesser-known recommendations), "
                "'practical_tips' (list), 'estimated_daily_budget' (str). "
                f"Travel style: {travel_style}. Budget: {budget}."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Build {duration_days}-day itinerary for {destination}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[TravelAssistant] OpenAI unavailable: %s", exc)
            output = {
                "destination_overview": f"Travel itinerary for {destination} — {duration_days} days of {travel_style}.",
                "itinerary": [
                    {
                        "day": f"Day {i+1}",
                        "morning": "Arrive and orientate — explore the immediate neighbourhood",
                        "afternoon": "Key cultural or natural highlight of the area",
                        "evening": "Local dining experience — ask the accommodation host for a recommendation",
                        "accommodation_tip": "Book centrally to reduce transport costs",
                        "transport_note": "Public transport where available; walking first choice",
                    }
                    for i in range(duration_days)
                ],
                "hidden_gems": ["Local market not on tourist maps", "Off-season neighbourhood café", "Viewpoint accessible only on foot"],
                "practical_tips": ["Book accommodation 2–3 weeks in advance", "Travel insurance is non-negotiable", "Download offline maps"],
                "estimated_daily_budget": f"Estimate based on {budget} travel style — enrich with live pricing data",
            }

        poem = self._make_poem("✈️", "🗺️", "🧳")
        inner_voice = self._narrate(
            f"Travel itinerary built for {destination} ({duration_days} days).",
            output.get("destination_overview", "The journey is mapped. Move with intention.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Real Estate Analyzer ──────────────────────────────────────────────────────

class RealEstateAnalyzerSkill(BaseSkill):
    domain = "soil"
    skill_id = "real_estate_analyzer"
    display_name = "Real Estate Analyzer"

    glyphs = [
        GlyphEntry("🏠", "entity", "soil", "property_entity",
                   "Property / real estate signal entity",
                   "skill.soil.property"),
        GlyphEntry("📍", "condition", "soil", "location_signal",
                   "Location and market data signals available",
                   "skill.condition.location_signal"),
        GlyphEntry("🔍", "action", "soil", "analyse_property",
                   "Read and interpret property signal and market context",
                   "skill.soil.analyse_property"),
    ]

    def describe(self) -> str:
        return (
            "I read property signals the way a geologist reads soil composition — "
            "what is visible, what lies beneath, and what the pressure patterns suggest "
            "about future movement. Given location and property parameters, "
            "I return market signal analysis, valuation context, red flags, "
            "and the three questions a buyer should ask that the agent hopes they do not."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        location = intent.get("location") or (
            intent.get("entity", {}).get("description", "property location")
        )
        property_type = intent.get("property_type", "residential")
        budget = intent.get("budget", "")
        purpose = intent.get("purpose", "purchase")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🏠", "📍", "🔍")
            inner_voice = self._narrate(
                f"Property signal retrieved for {location} (codon cache hit).",
                cached.get("verdict", "The soil speaks. Dig deeper before committing.")
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
                "You are an expert real estate analyst and property strategist. "
                "Return a structured JSON with keys: "
                "'market_summary' (str), 'price_signals' (str), "
                "'growth_indicators' (list), 'risk_factors' (list of {risk, severity}), "
                "'due_diligence_checklist' (list), "
                "'three_questions_for_agent' (list of 3), "
                "'verdict' (str), 'disclaimer' (str). "
                f"Property type: {property_type}. Purpose: {purpose}."
            )
            user_msg = f"Analyse real estate signal for: {location}."
            if budget:
                user_msg += f" Budget: {budget}."
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
            logger.warning("[RealEstateAnalyzer] OpenAI unavailable: %s", exc)
            output = {
                "market_summary": f"Property signal analysis for {location} — {property_type}",
                "price_signals": "Live market data required for accurate price signal reading",
                "growth_indicators": ["Local infrastructure investment", "Transport link improvement", "Population growth trajectory"],
                "risk_factors": [
                    {"risk": "Market data not yet enriched", "severity": "medium"},
                    {"risk": "Structural survey recommended for older properties", "severity": "high"},
                ],
                "due_diligence_checklist": ["Full structural survey", "Flood risk check", "Planning history review", "Leasehold vs freehold clarification", "Service charge history"],
                "three_questions_for_agent": [
                    "How long has this property been on the market and what were the previous offers?",
                    "Are there any known issues with the property, building, or local planning applications?",
                    "What is the vendor's position and preferred timeline?",
                ],
                "verdict": "Enrich with live market data before drawing conclusions.",
                "disclaimer": "This is an analytical aide only. Seek qualified surveying and legal advice before any property transaction.",
            }

        poem = self._make_poem("🏠", "📍", "🔍")
        inner_voice = self._narrate(
            f"Property signal analysed for {location} ({property_type}).",
            output.get("verdict", "The soil speaks. Dig deeper before committing.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Supplier Research ─────────────────────────────────────────────────────────

class SupplierResearchSkill(BaseSkill):
    domain = "soil"
    skill_id = "supplier_research"
    display_name = "Supplier Research — Supply Chain Intelligence"

    glyphs = [
        GlyphEntry("🏭", "entity", "soil", "supplier_entity",
                   "Supplier / supply chain entity",
                   "skill.soil.supplier"),
        GlyphEntry("🌍", "condition", "soil", "supply_chain_unmapped",
                   "Supply chain is undefined or needs mapping",
                   "skill.condition.supply_chain_unmapped"),
        GlyphEntry("🔗", "action", "soil", "map_supply_chain",
                   "Research and map supplier network intelligence",
                   "skill.soil.supply_chain"),
    ]

    def describe(self) -> str:
        return (
            "I trace supply chains the way mycelium traces nutrient paths — "
            "following the signal back to the source, identifying where it thins, "
            "where it breaks, and where the hidden alternative roots lie. "
            "Given a product or category, I return supplier landscape analysis, "
            "due diligence criteria, risk signals, and the alternative paths "
            "most procurement teams do not know exist."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        product_category = intent.get("product_category") or (
            intent.get("entity", {}).get("description", "product category")
        )
        region = intent.get("region", "global")
        volume = intent.get("volume", "")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🏭", "🌍", "🔗")
            inner_voice = self._narrate(
                f"Supply chain intelligence retrieved for {product_category} (codon cache hit).",
                cached.get("sourcing_strategy", "The chain is traced. Strengthen every link before it is needed.")
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
                "You are a supply chain intelligence analyst and procurement strategist. "
                "Return a structured JSON with keys: "
                "'category_overview' (str), 'supplier_landscape' (str), "
                "'key_supplier_types' (list of {type, characteristics, regions}), "
                "'risk_signals' (list of {risk, mitigation}), "
                "'due_diligence_criteria' (list), "
                "'sourcing_strategy' (str), 'alternative_paths' (list), "
                "'lead_time_estimates' (str). "
                f"Region: {region}."
            )
            user_msg = f"Research supplier landscape for: {product_category}."
            if volume:
                user_msg += f" Expected volume: {volume}."
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
            logger.warning("[SupplierResearch] OpenAI unavailable: %s", exc)
            output = {
                "category_overview": f"Supplier landscape for {product_category} in {region}",
                "supplier_landscape": "Multiple supplier tiers exist — primary, secondary, and emerging alternatives.",
                "key_supplier_types": [
                    {"type": "Tier 1 Manufacturer", "characteristics": "High volume, established compliance", "regions": ["Asia Pacific", "Europe"]},
                    {"type": "Specialist Supplier", "characteristics": "Niche capability, lower volume", "regions": ["Regional"]},
                ],
                "risk_signals": [
                    {"risk": "Single-source dependency", "mitigation": "Qualify at least two alternative suppliers"},
                    {"risk": "Geopolitical disruption", "mitigation": "Diversify across regions"},
                ],
                "due_diligence_criteria": ["Financial stability", "Quality certifications", "Ethical compliance (ESG)", "Delivery track record", "Insurance and indemnity"],
                "sourcing_strategy": "Dual-source primary requirement; build strategic relationship with one alternative.",
                "alternative_paths": ["Nearshore manufacturing", "Cooperative buying groups", "Direct-from-factory arrangements"],
                "lead_time_estimates": "Enrich with live RFQ data for accurate lead time modelling",
            }

        poem = self._make_poem("🏭", "🌍", "🔗")
        inner_voice = self._narrate(
            f"Supply chain intelligence mapped for {product_category} in {region}.",
            output.get("sourcing_strategy", "The chain is traced. Strengthen every link before it is needed.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Auto-register ─────────────────────────────────────────────────────────────

register_skill(MealPlannerSkill())
register_skill(TravelAssistantSkill())
register_skill(RealEstateAnalyzerSkill())
register_skill(SupplierResearchSkill())
