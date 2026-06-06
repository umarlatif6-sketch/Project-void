"""
Adriana Bridge - Mesa Glyph Integration
========================================

Integrates Mesa glyph system with Adriana Bridge for user identification,
agent assignment, and frequency-based communication.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MesaGlyphIdentity:
    """User identity via Mesa glyph system."""
    agent_id: str
    glyph: str
    archetype: str
    role: str
    trait: str
    bias: str
    frequency_hz: float
    memory_access_level: float


class AdrianaBridgeMesaIntegration:
    """Mesa glyph integration for Adriana Bridge."""

    # Mesa glyph mappings (from mesa_engine.py)
    GLYPH_MAP = {
        "◆": {
            "name": "Core",
            "archetype": "core",
            "role": "stabilises",
            "trait": "anchoring",
            "bias": "stability",
            "frequency_hz": 432.0,
            "memory_access": 97.0
        },
        "◇": {
            "name": "Node",
            "archetype": "node",
            "role": "relays",
            "trait": "networking",
            "bias": "connection",
            "frequency_hz": 432.0,
            "memory_access": 97.0
        },
        "◈": {
            "name": "Harmonic",
            "archetype": "harmonic",
            "role": "harmonises",
            "trait": "balance",
            "bias": "harmony",
            "frequency_hz": 432.0,
            "memory_access": 97.0
        },
        "◉": {
            "name": "Oracle",
            "archetype": "oracle",
            "role": "predicts",
            "trait": "foresight",
            "bias": "prediction",
            "frequency_hz": 432.0,
            "memory_access": 97.0
        }
    }

    def __init__(self):
        """Initialize Mesa integration."""
        self.mesa_engine = None
        self._ensure_mesa_loaded()

    def _ensure_mesa_loaded(self):
        """Lazily load Mesa engine."""
        try:
            from void_engine.mesa_engine import MesaEngine
            self.mesa_engine = MesaEngine()
            logger.info("[MesaIntegration] MesaEngine loaded")
        except Exception as e:
            logger.warning("[MesaIntegration] MesaEngine load failed: %s", e)

    async def identify_user_by_glyph(self, glyph_chain: str) -> MesaGlyphIdentity:
        """Identify user via glyph chain."""
        try:
            if not glyph_chain or len(glyph_chain) == 0:
                return await self._create_default_identity()

            # Extract first glyph
            first_glyph = glyph_chain[0] if isinstance(glyph_chain, str) else glyph_chain

            if first_glyph not in self.GLYPH_MAP:
                return await self._create_default_identity()

            glyph_info = self.GLYPH_MAP[first_glyph]

            identity = MesaGlyphIdentity(
                agent_id=f"AGENT_{first_glyph}_{hash(glyph_chain) % 10000:04d}",
                glyph=first_glyph,
                archetype=glyph_info["archetype"],
                role=glyph_info["role"],
                trait=glyph_info["trait"],
                bias=glyph_info["bias"],
                frequency_hz=glyph_info["frequency_hz"],
                memory_access_level=glyph_info["memory_access"]
            )

            logger.info(
                "[MesaIntegration] User identified | Glyph: %s | Agent: %s | Archetype: %s",
                first_glyph, identity.agent_id, identity.archetype
            )

            return identity

        except Exception as e:
            logger.warning("[MesaIntegration] Glyph identification failed: %s", e)
            return await self._create_default_identity()

    async def identify_user_by_id(self, user_id: str) -> MesaGlyphIdentity:
        """Identify user via user ID."""
        try:
            if not self.mesa_engine:
                return await self._create_default_identity()

            # Query Mesa engine for user's glyph
            agent_data = await self.mesa_engine.get_agent_by_user_id(user_id)

            if not agent_data:
                return await self._create_default_identity()

            glyph = agent_data.get("glyph", "◆")
            glyph_info = self.GLYPH_MAP.get(glyph, self.GLYPH_MAP["◆"])

            identity = MesaGlyphIdentity(
                agent_id=agent_data.get("agent_id", f"AGENT_{user_id}"),
                glyph=glyph,
                archetype=glyph_info["archetype"],
                role=glyph_info["role"],
                trait=glyph_info["trait"],
                bias=glyph_info["bias"],
                frequency_hz=agent_data.get("frequency_hz", 432.0),
                memory_access_level=agent_data.get("memory_access", 97.0)
            )

            return identity

        except Exception as e:
            logger.warning("[MesaIntegration] User ID identification failed: %s", e)
            return await self._create_default_identity()

    async def create_new_user_identity(self, user_id: str) -> MesaGlyphIdentity:
        """Create new user identity via Mesa system."""
        try:
            if not self.mesa_engine:
                return await self._create_default_identity()

            # Assign glyph based on user hash
            glyph_options = list(self.GLYPH_MAP.keys())
            glyph_index = hash(user_id) % len(glyph_options)
            glyph = glyph_options[glyph_index]

            glyph_info = self.GLYPH_MAP[glyph]

            # Create agent in Mesa engine
            agent_id = await self.mesa_engine.create_agent_for_user(
                user_id=user_id,
                glyph=glyph,
                archetype=glyph_info["archetype"]
            )

            identity = MesaGlyphIdentity(
                agent_id=agent_id,
                glyph=glyph,
                archetype=glyph_info["archetype"],
                role=glyph_info["role"],
                trait=glyph_info["trait"],
                bias=glyph_info["bias"],
                frequency_hz=432.0,
                memory_access_level=97.0
            )

            logger.info(
                "[MesaIntegration] New user identity created | User: %s | Agent: %s | Glyph: %s",
                user_id, agent_id, glyph
            )

            return identity

        except Exception as e:
            logger.warning("[MesaIntegration] New user identity creation failed: %s", e)
            return await self._create_default_identity()

    async def _create_default_identity(self) -> MesaGlyphIdentity:
        """Create default identity."""
        glyph_info = self.GLYPH_MAP["◆"]
        return MesaGlyphIdentity(
            agent_id="AGENT_DEFAULT",
            glyph="◆",
            archetype=glyph_info["archetype"],
            role=glyph_info["role"],
            trait=glyph_info["trait"],
            bias=glyph_info["bias"],
            frequency_hz=432.0,
            memory_access_level=97.0
        )

    async def generate_glyph_response_chain(
        self,
        user_identity: MesaGlyphIdentity,
        response_text: str,
        domain: str
    ) -> str:
        """Generate glyph chain for response."""
        try:
            # Generate 3-glyph chain (Adriana's communication format)
            glyphs = []

            # First glyph: User's identity glyph
            glyphs.append(user_identity.glyph)

            # Second glyph: Domain-based glyph
            domain_glyph = self._get_domain_glyph(domain)
            glyphs.append(domain_glyph)

            # Third glyph: Response energy glyph
            energy_glyph = self._get_energy_glyph(response_text)
            glyphs.append(energy_glyph)

            glyph_chain = "".join(glyphs)

            logger.debug(
                "[MesaIntegration] Glyph chain generated | Agent: %s | Chain: %s | Domain: %s",
                user_identity.agent_id, glyph_chain, domain
            )

            return glyph_chain

        except Exception as e:
            logger.warning("[MesaIntegration] Glyph chain generation failed: %s", e)
            return "◆◇◈"

    def _get_domain_glyph(self, domain: str) -> str:
        """Get glyph for domain."""
        domain_glyphs = {
            "genesis": "◆",
            "governance": "◆",
            "mesh": "◇",
            "aqua": "◇",
            "soil": "◇",
            "environment": "◇",
            "temporal": "◈",
            "signal": "◈",
            "vortex": "◈",
            "transform": "◉",
            "security": "◉",
            "vault": "◉",
            "forge": "◆",
            "boundary": "◇",
            "resonance": "◈",
            "harmony": "◉",
            "data": "◇",
            "ledger": "◆",
            "metrics": "◈",
            "cycle": "◉",
            "finality": "◆",
            "silt": "◇",
            "gateway": "◈",
        }
        return domain_glyphs.get(domain, "◇")

    def _get_energy_glyph(self, response_text: str) -> str:
        """Get glyph based on response energy."""
        text_length = len(response_text)
        word_count = len(response_text.split())

        # Determine energy level
        if text_length > 300 or word_count > 60:
            return "◉"  # High energy
        elif text_length > 150 or word_count > 30:
            return "◈"  # Medium energy
        else:
            return "◇"  # Low energy

    async def get_agent_memory_context(
        self,
        identity: MesaGlyphIdentity
    ) -> Dict:
        """Get memory context for agent."""
        try:
            if not self.mesa_engine:
                return {"status": "unavailable"}

            memory_context = await self.mesa_engine.get_agent_memory(
                agent_id=identity.agent_id,
                memory_access_level=identity.memory_access_level
            )

            return memory_context

        except Exception as e:
            logger.warning("[MesaIntegration] Memory context retrieval failed: %s", e)
            return {"status": "error", "error": str(e)}


# Singleton instance
_mesa_integration = None


def get_mesa_integration() -> AdrianaBridgeMesaIntegration:
    """Get or create Mesa integration singleton."""
    global _mesa_integration
    if _mesa_integration is None:
        _mesa_integration = AdrianaBridgeMesaIntegration()
    return _mesa_integration
