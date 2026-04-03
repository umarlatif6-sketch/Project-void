"""
Adriana Skill Modules — Multi-Domain Capability Architecture
=============================================================
BaseSkill defines the contract every skill module must implement.
All skills register glyphs into the SCL lexicon and expose an
execute(intent) -> dict interface so the transpiler can invoke them
via resolved glyph chains.

Domain taxonomy (maps to adriana.lex extensions):
  intelligence — research, competitive analysis, financial signals
  signal       — content, brand, SEO, ad creative
  ledger       — legal, finance, invoicing, tax, data generation
  mesh         — people, recruitment, SDR, resume, interview
  aqua/soil    — life, environment, meal, travel, real estate, supply
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ─── Data Contracts ────────────────────────────────────────────────────────────

@dataclass
class GlyphEntry:
    """A single SCL glyph entry to be injected into the AdrianaLexicon."""
    glyph: str
    category: str   # entity | condition | action
    domain: str
    key: str
    description: str
    python_equivalent: str


@dataclass
class SkillResult:
    """Standardised return value from any skill's execute() call."""
    success: bool
    domain: str
    skill_id: str
    output: Dict[str, Any]
    scl_poem: str          # Entity → Condition → Action summary
    inner_voice: str       # Adriana-voice narration
    error: Optional[str] = None
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "domain": self.domain,
            "skill_id": self.skill_id,
            "output": self.output,
            "scl_poem": self.scl_poem,
            "inner_voice": self.inner_voice,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 3),
        }


# ─── Base Class ────────────────────────────────────────────────────────────────

class BaseSkill(ABC):
    """
    Abstract base for all Adriana skill modules.

    Subclasses must define:
      - domain (str)        : SCL domain key (intelligence / signal / ledger / mesh / aqua)
      - skill_id (str)      : unique short identifier
      - display_name (str)  : human-readable name
      - glyphs (list)       : GlyphEntry objects to register into the lexicon
      - execute(intent)     : core execution logic; returns SkillResult
      - describe()          : one-paragraph capability description in Adriana's voice
    """

    domain: str = ""
    skill_id: str = ""
    display_name: str = ""
    glyphs: List[GlyphEntry] = field(default_factory=list)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @abstractmethod
    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        """
        Execute the skill given a parsed intent dict.

        The intent dict mirrors ActionIntent.to_dict():
          {
            "entity":     {"key": ..., "domain": ..., "description": ...},
            "conditions": [...],
            "actions":    [...],
            "raw":        "...",
          }

        Returns a SkillResult.
        """

    @abstractmethod
    def describe(self) -> str:
        """Return a one-paragraph capability description in Adriana's voice."""

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_poem(self, entity_key: str, condition_key: str, action_key: str) -> str:
        """Build a 3-glyph SCL poem string from keys for display."""
        return f"{entity_key} → {condition_key} → {action_key}"

    def _narrate(self, what: str, result_summary: str) -> str:
        """Produce Adriana-voice narration wrapping a skill result."""
        return (
            f"The {self.domain} signal resolved. "
            f"{what} "
            f"The root speaks: {result_summary}"
        )

    def _timed_execute(self, intent: Dict[str, Any]) -> SkillResult:
        """Wrapper that measures execution time and catches exceptions."""
        start = time.time()
        try:
            result = self.execute(intent)
            result.elapsed_ms = (time.time() - start) * 1000
            return result
        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            logger.exception("[Skill:%s] execute() raised: %s", self.skill_id, exc)
            return SkillResult(
                success=False,
                domain=self.domain,
                skill_id=self.skill_id,
                output={},
                scl_poem="",
                inner_voice="",
                error=str(exc),
                elapsed_ms=elapsed,
            )


# ─── Registry ─────────────────────────────────────────────────────────────────

_REGISTRY: Dict[str, "BaseSkill"] = {}


def register_skill(skill: BaseSkill) -> None:
    """Register a skill instance into the global registry."""
    _REGISTRY[skill.skill_id] = skill
    logger.info("[SkillRegistry] Registered skill: %s (domain=%s)", skill.skill_id, skill.domain)


def get_skill(skill_id: str) -> Optional[BaseSkill]:
    return _REGISTRY.get(skill_id)


def list_skills() -> List[Dict]:
    """Return a registry manifest for the /adriana/skills endpoint."""
    result = []
    for sk in _REGISTRY.values():
        result.append({
            "skill_id": sk.skill_id,
            "display_name": sk.display_name,
            "domain": sk.domain,
            "description": sk.describe(),
            "glyphs": [
                {
                    "glyph": g.glyph,
                    "category": g.category,
                    "key": g.key,
                    "description": g.description,
                }
                for g in sk.glyphs
            ],
        })
    return result


def all_glyphs() -> List[GlyphEntry]:
    """Aggregate all skill glyphs for bulk lexicon injection."""
    glyphs = []
    for sk in _REGISTRY.values():
        glyphs.extend(sk.glyphs)
    return glyphs


def _get_openai_client():
    """
    Return an OpenAI client configured with the project's Replit integration keys.
    Uses AI_INTEGRATIONS_OPENAI_API_KEY + AI_INTEGRATIONS_OPENAI_BASE_URL.
    Raises ImportError / RuntimeError if unavailable.
    """
    import os
    from openai import OpenAI
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError("AI_INTEGRATIONS_OPENAI_API_KEY not set")
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _auto_load() -> None:
    """Import every skill submodule so that module-level register calls fire."""
    import importlib

    submodules = [
        "void_engine.skill_modules.intelligence",
        "void_engine.skill_modules.content_brand",
        "void_engine.skill_modules.legal_finance",
        "void_engine.skill_modules.people",
        "void_engine.skill_modules.life_environment",
    ]
    for mod in submodules:
        try:
            importlib.import_module(mod)
        except Exception as exc:
            logger.warning("[SkillLoader] Failed to load %s: %s", mod, exc)
