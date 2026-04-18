import pytest

from void_engine.voice_profile_schema import (
    VoiceProfileAccessError,
    VoiceProfileManager,
    VoiceProfileStorageUnavailable,
)
from void_engine.voice_consent_policy import VoiceConsentPolicy
from void_engine.tts_provider import _resolve_voxcpm_speaker_embedding


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


def test_voxcpm_resolution_requires_owner_and_approved_voice(monkeypatch: pytest.MonkeyPatch) -> None:
    from void_engine import voice_profile_schema as profile_module

    profile_module._voice_profile_manager = VoiceProfileManager(
        db_connection=None,
        allow_insecure_fallback=True,
    )
    profile_module._voice_profile_manager.create_user_voice_profile("user-a", "embed-a")
    profile_module._voice_profile_manager.update_consent_status("user-a", "approved")

    resolved = _resolve_voxcpm_speaker_embedding(
        voice="default_speaker",
        user_id="user-a",
        authenticated_user="user-a",
        speaker_db_path="",
        originating_context="console",
    )

    assert resolved == "embed-a"


def test_voxcpm_resolution_blocks_legacy_json_without_opt_in(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    speaker_db = tmp_path / "voices.json"
    speaker_db.write_text('{"user-a":"embed-a"}', encoding="utf-8")

    from void_engine import voice_profile_schema as profile_module

    profile_module._voice_profile_manager = VoiceProfileManager(
        db_connection=None,
        allow_insecure_fallback=True,
    )
    monkeypatch.delenv("VOXCPM_ALLOW_LEGACY_JSON_SPEAKER_DB", raising=False)

    with pytest.raises(RuntimeError):
        _resolve_voxcpm_speaker_embedding(
            voice="default_speaker",
            user_id="user-a",
            authenticated_user="user-a",
            speaker_db_path=str(speaker_db),
            originating_context="console",
        )
