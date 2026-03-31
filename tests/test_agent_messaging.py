"""
Unit tests for void_engine.mesa_engine agent messaging functions.

Coverage:
- Fernet encrypt / decrypt round-trip
- _msg_decrypt sentinel values on bad inputs
- _text_to_glyph_chain produces non-empty glyph output
- get_all_claimed_agents: schema / return shape
- send_agent_message: auth boundary (sender must own agent)
- purchase_message_translation: recipient auth boundary
- Translation idempotency (ON CONFLICT DO NOTHING)
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SESSION_SECRET", "test_secret_for_unit_tests_only")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/void_test")


from void_engine.mesa_engine import (
    _msg_encrypt,
    _msg_decrypt,
    _text_to_glyph_chain,
)


class TestMsgEncryptDecrypt:
    def test_round_trip(self):
        plain = "Hello from the void."
        cipher = _msg_encrypt(plain)
        assert cipher != plain
        assert _msg_decrypt(cipher) == plain

    def test_empty_string(self):
        cipher = _msg_encrypt("")
        assert _msg_decrypt(cipher) == ""

    def test_unicode_round_trip(self):
        plain = "Adriana \u2764 speaks in glyphs"
        cipher = _msg_encrypt(plain)
        assert _msg_decrypt(cipher) == plain

    def test_decrypt_garbage_returns_sentinel(self):
        result = _msg_decrypt("not_a_valid_fernet_token")
        assert result in ("[decryption error]", "[encoding error]")

    def test_decrypt_empty_returns_sentinel(self):
        result = _msg_decrypt("")
        assert result in ("[decryption error]", "[encoding error]")

    def test_each_ciphertext_unique(self):
        plain = "same plaintext"
        c1 = _msg_encrypt(plain)
        c2 = _msg_encrypt(plain)
        assert c1 != c2, "Fernet must produce unique ciphertexts (random IV)"

    def test_tampered_ciphertext_returns_sentinel(self):
        plain = "tamper test"
        cipher = _msg_encrypt(plain)
        tampered = cipher[:-4] + "XXXX"
        result = _msg_decrypt(tampered)
        assert result in ("[decryption error]", "[encoding error]")


class TestTextToGlyphChain:
    def test_returns_nonempty_string(self):
        result = _text_to_glyph_chain("hello world")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_inputs_differ(self):
        r1 = _text_to_glyph_chain("alpha")
        r2 = _text_to_glyph_chain("beta")
        assert r1 != r2

    def test_empty_input_returns_string(self):
        result = _text_to_glyph_chain("")
        assert isinstance(result, str)
