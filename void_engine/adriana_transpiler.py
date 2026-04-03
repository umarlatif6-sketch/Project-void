"""
Adriana Protocol Transpiler — Semantic Core Language (SCL) v1.0

Parses glyph-chain expressions (e.g. "α-θ-❄️") against the Adriana Lexicon
and generates executable action sequences for the VirtualVoidSimulator.

Grammar:
  expression  = triple ( "|" triple )*
  triple      = glyph ( "-" glyph )*
  glyph       = <any lexicon-registered symbol>

Pattern: [entity]-[condition]-[action]  (Subject-Condition-Action)
Multi-action: [entity]-[condition]-[action]-[action]
Branch: [triple]|[triple]  (conditional OR)

The transpiler resolves each glyph, validates the grammar,
generates simulator actions, and tracks compression metrics.
"""

import os
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class LexiconEntry:
    glyph: str
    category: str
    domain: str
    key: str
    description: str
    python_equivalent: str


@dataclass
class ResolvedGlyph:
    glyph: str
    entry: LexiconEntry
    position: int


@dataclass
class ActionIntent:
    entity: Optional[ResolvedGlyph]
    conditions: List[ResolvedGlyph]
    actions: List[ResolvedGlyph]
    raw_expression: str

    def to_dict(self):
        return {
            "entity": {
                "glyph": self.entity.glyph,
                "key": self.entity.entry.key,
                "domain": self.entity.entry.domain,
                "description": self.entity.entry.description,
            } if self.entity else None,
            "conditions": [{
                "glyph": c.glyph,
                "key": c.entry.key,
                "description": c.entry.description,
            } for c in self.conditions],
            "actions": [{
                "glyph": a.glyph,
                "key": a.entry.key,
                "domain": a.entry.domain,
                "description": a.entry.description,
                "maps_to": a.entry.python_equivalent,
            } for a in self.actions],
            "raw": self.raw_expression,
        }


@dataclass
class SimulatorCommand:
    action_type: str
    params: Dict
    source_intent: ActionIntent
    narrative: str

    def to_dict(self):
        return {
            "action_type": self.action_type,
            "params": self.params,
            "narrative": self.narrative,
            "source": self.source_intent.raw_expression,
        }


@dataclass
class TranspileResult:
    success: bool
    expression: str
    intents: List[ActionIntent]
    commands: List[SimulatorCommand]
    errors: List[str]
    compression: Dict
    narrative: str
    transpile_time_ms: float

    def to_dict(self):
        return {
            "success": self.success,
            "expression": self.expression,
            "intents": [i.to_dict() for i in self.intents],
            "commands": [c.to_dict() for c in self.commands],
            "errors": self.errors,
            "compression": self.compression,
            "narrative": self.narrative,
            "transpile_time_ms": round(self.transpile_time_ms, 3),
        }


ACTION_TYPE_MAP = {
    "action.pump_cycle": ("pump_cycle", {"count": 1}),
    "action.nutrient_dose": ("nutrient_dose", {"dose_ml": 5}),
    "action.sensor_calibrate": ("sensor_calibrate", {"sensor": "auto"}),
    "action.flywheel_boost": ("flywheel_boost", {"rpm_delta": 500}),
    "action.silk_test": ("silk_test", {"strand_id": 0}),
    "action.air_curtain_activate": ("air_curtain_activate", {"velocity_ms": 15}),
    "action.air_curtain_deactivate": ("air_curtain_deactivate", {}),
    "action.nitrogen_vent": ("nitrogen_vent", {"vent_rate": 0.1}),
    "action.retry": ("sensor_calibrate", {"sensor": "auto"}),
    "action.signal": ("sensor_calibrate", {"sensor": "silk_web"}),
    "action.pause": ("sensor_calibrate", {"sensor": "pause"}),
}

CONDITION_NARRATIVES = {
    "threshold_high": "exceeds safe threshold",
    "threshold_low": "has fallen below safe threshold",
    "rising": "is rising",
    "declining": "is declining",
    "critical": "has reached critical level",
    "balanced": "is within balanced range",
    "alarm": "has triggered an alarm",
    "nominal": "reads nominal",
    "absent": "is absent or zero",
    "approximate": "is near threshold boundary",
}


class AdrianaLexicon:
    def __init__(self, lexicon_path: Optional[str] = None):
        self._entries: Dict[str, LexiconEntry] = {}
        self._by_category: Dict[str, List[LexiconEntry]] = {
            "entity": [], "condition": [], "action": [],
        }
        self._by_domain: Dict[str, List[LexiconEntry]] = {}

        if lexicon_path is None:
            lexicon_path = os.path.join(os.path.dirname(__file__), "adriana.lex")
        self._load(lexicon_path)

    def _load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("=") or line.startswith("-"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 6:
                    continue
                entry = LexiconEntry(
                    glyph=parts[0],
                    category=parts[1],
                    domain=parts[2],
                    key=parts[3],
                    description=parts[4],
                    python_equivalent=parts[5],
                )
                self._entries[entry.glyph] = entry
                if entry.category in self._by_category:
                    self._by_category[entry.category].append(entry)
                self._by_domain.setdefault(entry.domain, []).append(entry)

    def resolve(self, glyph: str) -> Optional[LexiconEntry]:
        return self._entries.get(glyph)

    def all_glyphs(self) -> Dict[str, LexiconEntry]:
        return dict(self._entries)

    def by_category(self, category: str) -> List[LexiconEntry]:
        return self._by_category.get(category, [])

    def by_domain(self, domain: str) -> List[LexiconEntry]:
        return self._by_domain.get(domain, [])

    def get_lexicon_map(self) -> Dict:
        result = {}
        for cat in ("entity", "condition", "action"):
            result[cat] = []
            for e in self._by_category.get(cat, []):
                result[cat].append({
                    "glyph": e.glyph,
                    "domain": e.domain,
                    "key": e.key,
                    "description": e.description,
                    "python_equivalent": e.python_equivalent,
                })
        return result

    @property
    def size(self) -> int:
        return len(self._entries)


class AdrianaTranspiler:
    def __init__(self, lexicon: Optional[AdrianaLexicon] = None):
        self._lexicon = lexicon or AdrianaLexicon()
        self._transpile_count = 0
        self._total_compression_ratio = 0.0
        self._history: List[Dict] = []
        self._load_skill_glyphs()

    def _load_skill_glyphs(self) -> None:
        """
        Import all skill modules and inject their glyph entries into the lexicon.
        Best-effort — never raises (skill loading must not break core transpiler).
        """
        try:
            from void_engine.skill_modules import _auto_load, all_glyphs
            _auto_load()
            for ge in all_glyphs():
                if ge.glyph not in self._lexicon._entries:
                    entry = LexiconEntry(
                        glyph=ge.glyph,
                        category=ge.category,
                        domain=ge.domain,
                        key=ge.key,
                        description=ge.description,
                        python_equivalent=ge.python_equivalent,
                    )
                    self._lexicon._entries[entry.glyph] = entry
                    if entry.category in self._lexicon._by_category:
                        self._lexicon._by_category[entry.category].append(entry)
                    self._lexicon._by_domain.setdefault(entry.domain, []).append(entry)
        except Exception as exc:
            import logging as _log
            _log.getLogger(__name__).warning(
                "[Transpiler] Skill glyph loading failed (non-fatal): %s", exc
            )

    def resolve_skill(self, intent: "ActionIntent") -> Optional[Dict]:
        """
        Attempt to resolve a skill invocation for the given intent.

        Returns the SkillResult dict if a skill handles this intent,
        or None if no skill matches (falls back to simulator command path).
        """
        try:
            from void_engine.skill_modules.skill_router import invoke_skill
            intent_dict = intent.to_dict()
            result = invoke_skill(intent_dict)
            if result.get("success"):
                return result
        except Exception as exc:
            import logging as _log
            _log.getLogger(__name__).debug(
                "[Transpiler] Skill resolution skipped: %s", exc
            )
        return None

    def transpile(self, expression: str) -> TranspileResult:
        start = time.time()
        self._transpile_count += 1
        errors = []
        intents = []
        commands = []

        expression = expression.strip()
        if not expression:
            return TranspileResult(
                success=False, expression=expression, intents=[], commands=[],
                errors=["Empty expression"], compression={}, narrative="",
                transpile_time_ms=0,
            )

        branches = expression.split("|")

        for branch in branches:
            branch = branch.strip()
            if not branch:
                continue

            glyphs_raw = [g.strip() for g in branch.split("-") if g.strip()]
            resolved = []

            for i, g in enumerate(glyphs_raw):
                entry = self._lexicon.resolve(g)
                if entry is None:
                    errors.append(f"Unknown glyph '{g}' at position {i}")
                    continue
                resolved.append(ResolvedGlyph(glyph=g, entry=entry, position=i))

            if not resolved:
                errors.append(f"No valid glyphs in branch '{branch}'")
                continue

            entity = None
            conditions = []
            actions = []

            for rg in resolved:
                if rg.entry.category == "entity" and entity is None:
                    entity = rg
                elif rg.entry.category == "condition":
                    conditions.append(rg)
                elif rg.entry.category == "action":
                    actions.append(rg)
                elif rg.entry.category == "entity" and entity is not None:
                    actions_from_entity = rg
                    errors.append(f"Multiple entities in branch — '{rg.glyph}' treated as secondary context")

            intent = ActionIntent(
                entity=entity,
                conditions=conditions,
                actions=actions,
                raw_expression=branch,
            )
            intents.append(intent)

            # ── Skill dispatch for v1.1 skill-domain glyphs ───────────────
            # If ANY action in this branch maps to a skill.* equivalent,
            # attempt to dispatch the entire intent through the skill router
            # before falling back to the simulator command path.
            _has_skill_action = any(
                a.entry.python_equivalent.startswith("skill.")
                for a in actions
            )
            if _has_skill_action:
                skill_result = self.resolve_skill(intent)
                if skill_result is not None:
                    # Attach the skill result payload to the intent for
                    # downstream consumers (routes, narrators, etc.).
                    intent.skill_result = skill_result  # type: ignore[attr-defined]
                    # Manufacture a skill-dispatch command so callers receive
                    # at least one command and TranspileResult.success is True.
                    narrative = (
                        skill_result.get("inner_voice")
                        or f"Skill '{skill_result.get('skill_id', '?')}' executed."
                    )
                    cmd = SimulatorCommand(
                        action_type="skill_dispatch",
                        params={
                            "skill_id": skill_result.get("skill_id"),
                            "domain": skill_result.get("domain"),
                            "success": skill_result.get("success"),
                            "scl_poem": skill_result.get("scl_poem"),
                            "output": skill_result.get("output"),
                        },
                        source_intent=intent,
                        narrative=narrative,
                    )
                    commands.append(cmd)
                    continue  # don't also run simulator path for this branch

            for action_glyph in actions:
                equiv = action_glyph.entry.python_equivalent
                if equiv in ACTION_TYPE_MAP:
                    action_type, default_params = ACTION_TYPE_MAP[equiv]
                    params = dict(default_params)

                    if entity and action_type == "sensor_calibrate":
                        params["sensor"] = entity.entry.key

                    narrative = self._build_narrative(entity, conditions, action_glyph)

                    cmd = SimulatorCommand(
                        action_type=action_type,
                        params=params,
                        source_intent=intent,
                        narrative=narrative,
                    )
                    commands.append(cmd)
                else:
                    errors.append(f"No action mapping for '{equiv}' from glyph '{action_glyph.glyph}'")

        compression = self._calculate_compression(expression, intents, commands)
        overall_narrative = self._build_overall_narrative(intents)
        elapsed = (time.time() - start) * 1000

        result = TranspileResult(
            success=len(commands) > 0 and len(errors) == 0,
            expression=expression,
            intents=intents,
            commands=commands,
            errors=errors,
            compression=compression,
            narrative=overall_narrative,
            transpile_time_ms=elapsed,
        )

        if result.success:
            self._total_compression_ratio += compression.get("ratio", 1.0)
            self._notify_village_resonance(expression, commands, compression)

        self._history.append({
            "expression": expression,
            "success": result.success,
            "commands": len(commands),
            "compression_ratio": compression.get("ratio", 1.0),
            "timestamp": time.time(),
        })
        if len(self._history) > 100:
            self._history = self._history[-100:]

        return result

    def _build_narrative(self, entity, conditions, action_glyph):
        parts = []
        if entity:
            parts.append(f"When {entity.entry.description}")
        for cond in conditions:
            cond_text = CONDITION_NARRATIVES.get(cond.entry.key, cond.entry.description)
            parts.append(cond_text)
        parts.append(f"→ {action_glyph.entry.description}")
        return " ".join(parts)

    def _build_overall_narrative(self, intents):
        if not intents:
            return ""
        narratives = []
        for intent in intents:
            parts = []
            if intent.entity:
                parts.append(intent.entity.entry.description)
            for c in intent.conditions:
                parts.append(CONDITION_NARRATIVES.get(c.entry.key, c.entry.description))
            for a in intent.actions:
                parts.append(f"→ {a.entry.description}")
            narratives.append(" ".join(parts))
        return " | ".join(narratives)

    def _calculate_compression(self, expression, intents, commands):
        adriana_chars = len(expression)
        adriana_tokens = sum(1 for c in expression if c not in ("-", "|", " "))

        python_lines = []
        for intent in intents:
            entity_ref = intent.entity.entry.python_equivalent if intent.entity else "system"
            for cond in intent.conditions:
                python_lines.append(f"if {entity_ref} {cond.entry.python_equivalent}:")
            for action in intent.actions:
                python_lines.append(f"    {action.entry.python_equivalent}()")
            if not intent.conditions:
                for action in intent.actions:
                    python_lines.append(f"{action.entry.python_equivalent}()")

        python_code = "\n".join(python_lines) if python_lines else "pass"
        python_chars = len(python_code)
        python_tokens = len(python_code.split())

        ratio = python_chars / max(adriana_chars, 1)

        return {
            "adriana_chars": adriana_chars,
            "adriana_glyphs": sum(len(i.actions) + len(i.conditions) + (1 if i.entity else 0) for i in intents),
            "python_chars": python_chars,
            "python_tokens": python_tokens,
            "python_equivalent": python_code,
            "ratio": round(ratio, 2),
            "density": round(len(commands) / max(adriana_chars, 1) * 100, 2),
        }

    def _notify_village_resonance(
        self,
        expression: str,
        commands: List["SimulatorCommand"],
        compression: Dict,
    ) -> None:
        """
        Feed a successful transpile event into the village simulation.

        Each glyph chain represents an adriana-type agent action, contributing
        to zone activity and resonance within the VirtualVoidSimulator.  The
        call is best-effort and must not raise (transpile correctness is primary).
        """
        try:
            import routes.shared as _shared
            harness = getattr(_shared, "harness_sim", None)
            if harness is None:
                return

            # Derive zone key from first glyph token; fall back to 'adriana'
            first_token = expression.split("-")[0].strip() or "adriana"
            zone_id = re.sub(r"[^\w]", "_", first_token).lower() or "adriana"

            mesa_result = {
                "zone_id": zone_id,
                "agent_count": max(1, len(commands)),
                "activity_level": min(1.0, compression.get("density", 0.0) / 10.0),
                "resonance_score": compression.get("ratio", 1.0) * len(commands) * 4.32,
                "steps_run": 1,
                "agent_types": {"adriana": len(commands)},
            }
            harness.feed_village_resonance(zone_id, mesa_result)
        except Exception:
            pass

    @property
    def stats(self) -> Dict:
        avg_ratio = (self._total_compression_ratio / max(self._transpile_count, 1))
        return {
            "total_transpilations": self._transpile_count,
            "average_compression_ratio": round(avg_ratio, 2),
            "lexicon_size": self._lexicon.size,
            "recent_history": self._history[-10:],
        }

    @property
    def lexicon(self) -> AdrianaLexicon:
        return self._lexicon
