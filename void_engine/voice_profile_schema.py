"""
Voice Profile Schema and Management for Project VOID.

Enables per-user voice sovereignty:
- Each user agent gets unique voice identity
- Adriana gets distinct sovereign voice profile
- Voice identity persists across sessions
- Voice is part of agent memory/identity continuity
"""

from typing import Optional, Dict
import json
import logging
import os
from threading import RLock
from datetime import datetime

logger = logging.getLogger(__name__)


class VoiceProfileAccessError(PermissionError):
    """Raised when a caller tries to access another user's voice profile."""


class VoiceProfileStorageUnavailable(RuntimeError):
    """Raised when the manager is in fail-closed mode without durable storage."""


# SQL Schema for voice_profiles table
VOICE_PROFILE_SCHEMA = """
CREATE TABLE IF NOT EXISTS voice_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255),
    speaker_embedding_id VARCHAR(255) NOT NULL,
    voice_name VARCHAR(255),
    voice_description TEXT,
    audio_characteristics JSONB,
    consent_status VARCHAR(50) DEFAULT 'pending',
    consent_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_voice_profiles_user_id ON voice_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_agent_id ON voice_profiles(agent_id);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_speaker_embedding ON voice_profiles(speaker_embedding_id);

-- Special entry for Adriana sovereign voice
INSERT INTO voice_profiles (user_id, agent_id, speaker_embedding_id, voice_name, voice_description, consent_status)
VALUES ('adriana_system', 'adriana_sovereign', 'adriana_sovereign_embedding', 'Adriana', 'System sovereign voice identity', 'approved')
ON CONFLICT (user_id) DO NOTHING;
"""

# Consent tracking table
VOICE_CONSENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS voice_consent_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    consent_action VARCHAR(50),
    consent_type VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES voice_profiles(user_id)
);

CREATE INDEX IF NOT EXISTS idx_voice_consent_user_id ON voice_consent_log(user_id);
"""


class VoiceProfile:
    """User voice profile with sovereignty and consent tracking."""

    def __init__(
        self,
        user_id: str,
        speaker_embedding_id: str,
        voice_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        audio_characteristics: Optional[Dict] = None,
    ):
        self.user_id = user_id
        self.speaker_embedding_id = speaker_embedding_id
        self.voice_name = voice_name or f"{user_id}_voice"
        self.agent_id = agent_id
        self.audio_characteristics = audio_characteristics or {}
        self.consent_status = "pending"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_active = True

    def to_dict(self) -> Dict:
        """Serialize voice profile to dictionary."""
        return {
            "user_id": self.user_id,
            "speaker_embedding_id": self.speaker_embedding_id,
            "voice_name": self.voice_name,
            "agent_id": self.agent_id,
            "audio_characteristics": self.audio_characteristics,
            "consent_status": self.consent_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
        }

    def to_json(self) -> str:
        """Serialize voice profile to JSON."""
        return json.dumps(self.to_dict())


class VoiceProfileManager:
    """Manage voice profiles with database abstraction."""

    def __init__(self, db_connection=None, allow_insecure_fallback: Optional[bool] = None):
        """
        Initialize voice profile manager.
        
        Args:
            db_connection: Database connection object (optional)
                          If None, manager fails closed unless insecure fallback is
                          explicitly allowed for local development.
        """
        self.db = db_connection
        self.fallback_storage = {}
        self._lock = RLock()
        if allow_insecure_fallback is None:
            allow_insecure_fallback = (
                os.environ.get("VOICE_PROFILE_ALLOW_INSECURE_FALLBACK", "false").strip().lower()
                == "true"
            )
        self.allow_insecure_fallback = allow_insecure_fallback

    def create_user_voice_profile(
        self,
        user_id: str,
        speaker_embedding_id: str,
        voice_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        audio_characteristics: Optional[Dict] = None,
    ) -> VoiceProfile:
        """
        Create new user voice profile.
        
        Args:
            user_id: Unique user identifier
            speaker_embedding_id: VoxCPM speaker embedding ID
            voice_name: Human-readable voice name
            agent_id: Associated agent ID
            audio_characteristics: Audio metadata (pitch, speed, etc.)
        
        Returns:
            VoiceProfile instance
        """
        profile = VoiceProfile(
            user_id=user_id,
            speaker_embedding_id=speaker_embedding_id,
            voice_name=voice_name,
            agent_id=agent_id,
            audio_characteristics=audio_characteristics,
        )

        if self.db:
            self._save_to_db(profile)
        else:
            self._ensure_storage_available("create voice profile")
            with self._lock:
                self.fallback_storage[user_id] = profile.to_dict()
            logger.warning("Voice profile created for %s using insecure fallback storage", user_id)

        return profile

    def get_user_voice_profile(self, user_id: str) -> Optional[VoiceProfile]:
        """Retrieve user voice profile."""
        if self.db:
            return self._get_from_db(user_id)
        else:
            self._ensure_storage_available("read voice profile")
            with self._lock:
                data = self.fallback_storage.get(user_id)
            if data:
                return self._dict_to_profile(dict(data))
            return None

    def get_user_voice_profile_atomic(
        self,
        user_id: str,
        authenticated_user: str,
    ) -> Optional[VoiceProfile]:
        """Atomically read a user's voice profile after verifying caller ownership."""
        self._authorize_access(user_id, authenticated_user)
        if self.db:
            return self._get_from_db(user_id)
        self._ensure_storage_available("read voice profile atomically")
        with self._lock:
            data = self.fallback_storage.get(user_id)
        if data:
            return self._dict_to_profile(dict(data))
        return None

    def get_speaker_embedding_id(
        self,
        user_id: str,
        authenticated_user: str,
    ) -> Optional[str]:
        """Get speaker embedding ID for the authenticated user only."""
        profile = self.get_user_voice_profile_atomic(user_id, authenticated_user)
        return profile.speaker_embedding_id if profile else None

    def update_consent_status(
        self,
        user_id: str,
        consent_status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Update voice consent status.
        
        Args:
            user_id: User identifier
            consent_status: 'approved', 'withdrawn', 'pending'
            ip_address: IP address of consent action
            user_agent: User agent string
        
        Returns:
            True if successful
        """
        if self.db:
            return self._update_consent_db(user_id, consent_status, ip_address, user_agent)
        else:
            self._ensure_storage_available("update voice consent")
            with self._lock:
                if user_id in self.fallback_storage:
                    self.fallback_storage[user_id]["consent_status"] = consent_status
                    self.fallback_storage[user_id]["updated_at"] = datetime.utcnow().isoformat()
                    logger.info(f"Consent updated for {user_id}: {consent_status}")
                    return True
            return False

    def list_all_voice_profiles(self) -> Dict[str, Dict]:
        """List all voice profiles (for admin/monitoring)."""
        if self.db:
            return self._list_from_db()
        else:
            self._ensure_storage_available("list voice profiles")
            with self._lock:
                return dict(self.fallback_storage)

    def _authorize_access(self, user_id: str, authenticated_user: str):
        if authenticated_user != user_id:
            raise VoiceProfileAccessError(
                f"Caller {authenticated_user!r} cannot access voice profile for {user_id!r}"
            )

    def _ensure_storage_available(self, action: str):
        if self.db:
            return
        if not self.allow_insecure_fallback:
            raise VoiceProfileStorageUnavailable(
                f"Cannot {action}: durable voice profile storage is unavailable and insecure fallback is disabled"
            )

    def _save_to_db(self, profile: VoiceProfile):
        """Save profile to database (stub for implementation)."""
        # This would be implemented with actual database calls
        logger.debug(f"DBI: Save voice profile {profile.user_id}")

    def _get_from_db(self, user_id: str) -> Optional[VoiceProfile]:
        """Get profile from database (stub for implementation)."""
        # This would be implemented with actual database calls
        logger.debug(f"DBI: Get voice profile {user_id}")
        return None

    def _update_consent_db(
        self,
        user_id: str,
        consent_status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Update consent in database (stub for implementation)."""
        # This would be implemented with actual database calls
        logger.debug(f"DBI: Update consent for {user_id}: {consent_status}")
        return True

    def _list_from_db(self) -> Dict[str, Dict]:
        """List profiles from database (stub for implementation)."""
        # This would be implemented with actual database calls
        return {}

    @staticmethod
    def _dict_to_profile(data: Dict) -> VoiceProfile:
        """Convert dictionary to VoiceProfile instance."""
        profile = VoiceProfile(
            user_id=data["user_id"],
            speaker_embedding_id=data["speaker_embedding_id"],
            voice_name=data.get("voice_name"),
            agent_id=data.get("agent_id"),
            audio_characteristics=data.get("audio_characteristics", {}),
        )
        profile.consent_status = data.get("consent_status", "pending")
        profile.is_active = data.get("is_active", True)
        return profile


# Singleton instance for application-wide use
_voice_profile_manager: Optional[VoiceProfileManager] = None


def get_voice_profile_manager(
    db_connection=None,
    allow_insecure_fallback: Optional[bool] = None,
) -> VoiceProfileManager:
    """Get or create singleton voice profile manager."""
    global _voice_profile_manager
    if _voice_profile_manager is None:
        _voice_profile_manager = VoiceProfileManager(
            db_connection,
            allow_insecure_fallback=allow_insecure_fallback,
        )
    return _voice_profile_manager


def initialize_voice_profiles(db_connection=None):
    """Initialize voice profiles schema in database."""
    if db_connection:
        try:
            cursor = db_connection.cursor()
            cursor.execute(VOICE_PROFILE_SCHEMA)
            cursor.execute(VOICE_CONSENT_SCHEMA)
            db_connection.commit()
            logger.info("Voice profiles schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voice profiles schema: {e}")
            raise
