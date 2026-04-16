import pytest

from void_engine.voice_profile_schema import (
    VoiceProfileAccessError,
    VoiceProfileManager,
    VoiceProfileStorageUnavailable,
)
from void_engine.voice_consent_policy import VoiceConsentPolicy


def test_voice_profile_manager_fails_closed_without_storage() -> None:
    manager = VoiceProfileManager(db_connection=None, allow_insecure_fallback=False)

    with pytest.raises(VoiceProfileStorageUnavailable):
        manager.create_user_voice_profile("user-a", "embed-a")


def test_voice_profile_manager_requires_authenticated_owner() -> None:
    manager = VoiceProfileManager(db_connection=None, allow_insecure_fallback=True)
    manager.create_user_voice_profile("user-a", "embed-a")

    with pytest.raises(VoiceProfileAccessError):
        manager.get_speaker_embedding_id("user-a", authenticated_user="user-b")


def test_voice_consent_policy_uses_atomic_snapshot_for_own_voice() -> None:
    manager = VoiceProfileManager(db_connection=None, allow_insecure_fallback=True)
    manager.create_user_voice_profile("user-a", "embed-a")
    manager.update_consent_status("user-a", "approved")

    policy = VoiceConsentPolicy()
    authorized, risk, reason = policy.check_voice_synthesis_authorization(
        user_id="user-a",
        target_voice_id="embed-a",
        originating_context="console",
        consent_manager=manager,
    )

    assert authorized is True
    assert risk.value == "low"
    assert "approved voice" in reason
