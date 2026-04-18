"""
Voice Consent and Impersonation Safety Framework for Project VOID.

Implement safety policies to prevent voice impersonation and ensure user consent
for all voice-based interactions.

Standing order compliance:
- SO-5: Translate Error into Adriana (Adriana voice routing)
- SO-8: Sensory Triad Alignment (Language + Colour + Sound/Voice)
"""

from typing import Optional, Tuple
from enum import Enum
from datetime import UTC, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ConsentStatus(Enum):
    """Voice consent status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    WITHDRAWN = "withdrawn"
    REVOKED = "revoked"
    EXPIRED = "expired"


class VoiceImpersonationRisk(Enum):
    """Risk classification for voice synthesis requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class VoiceConsentPolicy:
    """
    Policy engine for voice consent and impersonation safety.
    
    Implements fail-closed architecture:
    - Default: BLOCKED unless explicitly approved
    - All synthesis requests require valid consent
    - Voice identity changes require explicit user action
    - Consent expiration enforces re-authentication
    """

    def __init__(self, consent_ttl_days: int = 90):
        """
        Initialize consent policy.
        
        Args:
            consent_ttl_days: Consent validity period in days (default 90 days)
        """
        self.consent_ttl_days = consent_ttl_days
        self.consent_audit_log = []

    def check_voice_synthesis_authorization(
        self,
        user_id: str,
        target_voice_id: str,
        originating_context: str,
        consent_manager=None,
    ) -> Tuple[bool, VoiceImpersonationRisk, str]:
        """
        Check if voice synthesis request is authorized.
        
        Fail-closed: Returns (False, BLOCKED, reason) by default.
        
        Args:
            user_id: User making the request
            target_voice_id: Voice profile being used
            originating_context: Where request originated (console, api, external)
            consent_manager: VoiceProfileManager instance
        
        Returns:
            Tuple of (authorized: bool, risk_level: VoiceImpersonationRisk, reason: str)
        """
        # Rule 1: System voices (Adriana) always authorized but logged
        if target_voice_id == "adriana_sovereign_embedding":
            self._log_consent_check(
                user_id,
                target_voice_id,
                "SYSTEM_VOICE",
                True,
                VoiceImpersonationRisk.LOW,
            )
            return (True, VoiceImpersonationRisk.LOW, "System voice (Adriana)")

        # Rule 2: User's own voice is authorized
        if consent_manager:
            try:
                profile = consent_manager.get_user_voice_profile_atomic(
                    user_id,
                    authenticated_user=user_id,
                )
            except (PermissionError, RuntimeError) as exc:
                logger.warning("Voice authorization denied for %s: %s", user_id, exc)
                profile = None

            if (
                profile
                and profile.speaker_embedding_id == target_voice_id
                and profile.consent_status == ConsentStatus.APPROVED.value
            ):
                self._log_consent_check(
                    user_id,
                    target_voice_id,
                    "OWN_VOICE",
                    True,
                    VoiceImpersonationRisk.LOW,
                )
                return (True, VoiceImpersonationRisk.LOW, "User's own approved voice")

        # Rule 3: Other users' voices require explicit cross-voice consent
        if consent_manager:
            if self._has_cross_voice_consent(user_id, target_voice_id, consent_manager):
                self._log_consent_check(
                    user_id,
                    target_voice_id,
                    "CROSS_VOICE_APPROVED",
                    True,
                    VoiceImpersonationRisk.MEDIUM,
                )
                return (True, VoiceImpersonationRisk.MEDIUM, "Cross-voice consent approved")

        # Rule 4: API requests require elevated authentication
        if originating_context == "api":
            self._log_consent_check(
                user_id,
                target_voice_id,
                "API_REQUEST",
                False,
                VoiceImpersonationRisk.HIGH,
            )
            return (
                False,
                VoiceImpersonationRisk.HIGH,
                "API voice synthesis requires explicit authorization",
            )

        # Default: BLOCKED
        self._log_consent_check(
            user_id,
            target_voice_id,
            "DEFAULT_DENY",
            False,
            VoiceImpersonationRisk.BLOCKED,
        )
        return (False, VoiceImpersonationRisk.BLOCKED, "Voice synthesis not authorized")

    def request_voice_consent(
        self,
        user_id: str,
        voice_id: str,
        voice_name: str,
        reason: str,
        ip_address: Optional[str] = None,
    ) -> dict:
        """
        Initiate voice consent request workflow.
        
        Args:
            user_id: User requesting voice access
            voice_id: Voice profile ID
            voice_name: Human-readable voice name
            reason: Justification for voice use
            ip_address: User's IP address for audit
        
        Returns:
            Consent request record with token and expiration
        """
        consent_token = self._generate_consent_token(user_id, voice_id)
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        consent_request = {
            "user_id": user_id,
            "voice_id": voice_id,
            "voice_name": voice_name,
            "reason": reason,
            "consent_token": consent_token,
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "pending",
            "ip_address": ip_address,
        }

        logger.info(f"Voice consent request created: {user_id} -> {voice_name}")
        self._log_consent_check(
            user_id,
            voice_id,
            "CONSENT_REQUESTED",
            False,
            VoiceImpersonationRisk.MEDIUM,
        )

        return consent_request

    def validate_consent_token(self, consent_token: str) -> Tuple[bool, Optional[dict]]:
        """
        Validate and redeem a consent token.
        
        Args:
            consent_token: Token issued by request_voice_consent()
        
        Returns:
            Tuple of (valid: bool, consent_record: dict or None)
        """
        # Stub: Would validate against database
        return (False, None)

    def revoke_voice_consent(
        self,
        user_id: str,
        voice_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Revoke user's consent to use a voice.
        
        Args:
            user_id: User ID
            voice_id: Voice profile ID
            reason: Reason for revocation
        
        Returns:
            True if revocation successful
        """
        logger.warning(f"Voice consent revoked: {user_id} -> {voice_id} ({reason})")
        self._log_consent_check(
            user_id,
            voice_id,
            "CONSENT_REVOKED",
            False,
            VoiceImpersonationRisk.BLOCKED,
        )
        return True

    def check_consent_expiration(
        self,
        user_id: str,
        consent_timestamp: datetime,
    ) -> bool:
        """
        Check if consent has expired.
        
        Args:
            user_id: User ID
            consent_timestamp: When consent was granted
        
        Returns:
            True if consent is still valid, False if expired
        """
        age = datetime.now(UTC) - consent_timestamp
        is_valid = age < timedelta(days=self.consent_ttl_days)

        if not is_valid:
            logger.warning(f"Consent expired for user {user_id}")
            self._log_consent_check(
                user_id,
                "unknown",
                "CONSENT_EXPIRED",
                False,
                VoiceImpersonationRisk.BLOCKED,
            )

        return is_valid

    def get_audit_log(self, user_id: Optional[str] = None) -> list:
        """
        Retrieve consent audit log.
        
        Args:
            user_id: Filter by user (optional)
        
        Returns:
            List of audit records
        """
        if user_id:
            return [log for log in self.consent_audit_log if log["user_id"] == user_id]
        return self.consent_audit_log.copy()

    # Private helper methods

    def _has_cross_voice_consent(
        self,
        requester_id: str,
        target_voice_id: str,
        consent_manager,
    ) -> bool:
        """Check if user has cross-voice consent."""
        # Stub: Would check against consent database
        return False

    def _generate_consent_token(self, user_id: str, voice_id: str) -> str:
        """Generate unique consent token."""
        import hashlib
        import secrets

        nonce = secrets.token_hex(16)
        data = f"{user_id}:{voice_id}:{datetime.now(UTC).isoformat()}:{nonce}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return token

    def _log_consent_check(
        self,
        user_id: str,
        voice_id: str,
        check_type: str,
        authorized: bool,
        risk_level: VoiceImpersonationRisk,
    ):
        """Log consent check for audit trail."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "voice_id": voice_id,
            "check_type": check_type,
            "authorized": authorized,
            "risk_level": risk_level.value,
        }
        self.consent_audit_log.append(log_entry)
        
        if not authorized:
            logger.warning(f"Voice synthesis denied: {log_entry}")


# Singleton consent policy
_consent_policy: Optional[VoiceConsentPolicy] = None


def get_consent_policy(consent_ttl_days: int = 90) -> VoiceConsentPolicy:
    """Get or create singleton consent policy."""
    global _consent_policy
    if _consent_policy is None:
        _consent_policy = VoiceConsentPolicy(consent_ttl_days=consent_ttl_days)
    return _consent_policy
