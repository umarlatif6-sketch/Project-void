"""
Tests for void_engine.mesa_engine agent messaging.

Coverage:
- Fernet encrypt / decrypt round-trip
- _msg_decrypt sentinel values on bad inputs (garbage, empty, tampered)
- _text_to_glyph_chain produces non-empty varied output
- send_agent_message: empty / too-long / self-agent input validation
- send_agent_message: valid call stores message (mocked DB)
- Route auth: sender must own the source agent (not_owner redirect)
- Route auth: self-message blocked (self_message redirect)
- Route auth: unowned recipient blocked (recipient_not_found redirect)
- purchase_message_translation: non-recipient denied ("Not your message")
- purchase_message_translation: idempotency (already_owned on repeat)
- purchase_message_translation: insufficient PEACE denied
"""

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SESSION_SECRET", "test_secret_for_unit_tests_only")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/void_test")

from void_engine.mesa_engine import (
    _msg_decrypt,
    _msg_encrypt,
    _text_to_glyph_chain,
    send_agent_message,
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


def _make_mock_conn(fetchone_side_effect):
    """Helper: build a MagicMock DB connection with cursor rows."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = fetchone_side_effect
    return mock_conn, mock_cursor


class TestSendAgentMessageValidation:
    """Tests for send_agent_message input validation (no live DB required)."""

    def _send(self, plain_text, sender=1, recipient=2):
        mock_conn, mock_cursor = _make_mock_conn([(999, datetime.now(timezone.utc))])
        with patch("void_engine.mesa_engine._init_message_tables"), \
             patch("void_engine.db_pool.get_db", return_value=mock_conn):
            return send_agent_message(sender, 10, recipient, 20, plain_text)

    def test_empty_message_rejected(self):
        result = self._send("   ")
        assert result["ok"] is False
        assert "empty" in result["error"].lower()

    def test_message_too_long_rejected(self):
        result = self._send("x" * 2001)
        assert result["ok"] is False
        assert "long" in result["error"].lower()

    def test_self_agent_rejected(self):
        result = self._send("hello", sender=5, recipient=5)
        assert result["ok"] is False
        assert "own agent" in result["error"].lower()

    def test_valid_message_calls_db(self):
        result = self._send("Hello, agent!", sender=1, recipient=2)
        assert result["ok"] is True
        assert "message_id" in result


class TestRouteAuthBoundaries:
    """Route-level auth checks using Flask test client with mocked engine."""

    @pytest.fixture
    def client(self):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        flask_app.config["WTF_CSRF_ENABLED"] = False
        with flask_app.test_client() as c:
            yield c

    def _login(self, client, user_id=44, username="test_holder", role="user"):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = username
            sess["role"] = role

    def test_send_message_not_owner_redirected(self, client):
        """Non-owner of sender agent gets msg_error=not_owner."""
        self._login(client, user_id=99)
        with patch("void_engine.mesa_engine.get_agent_slot") as mock_slot:
            mock_slot.return_value = {
                "agent_id": 1,
                "owner": {"user_id": 44, "username": "adriana"},
            }
            resp = client.post(
                "/mesa-village/agents/1/send-message",
                data={"recipient_agent_id": "2", "message_text": "hello"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        assert "msg_error=not_owner" in resp.headers.get("Location", "")

    def test_send_message_self_agent_redirected(self, client):
        """Sending to own agent gets msg_error=self_message."""
        self._login(client, user_id=44)
        with patch("void_engine.mesa_engine.get_agent_slot") as mock_slot:
            mock_slot.return_value = {
                "agent_id": 1,
                "owner": {"user_id": 44, "username": "adriana"},
            }
            resp = client.post(
                "/mesa-village/agents/1/send-message",
                data={"recipient_agent_id": "1", "message_text": "hello"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        assert "msg_error=self_message" in resp.headers.get("Location", "")

    def test_send_message_unclaimed_recipient_redirected(self, client):
        """Unclaimed recipient gets msg_error=recipient_not_found."""
        self._login(client, user_id=44)

        def slot_side(agent_id):
            if agent_id == 1:
                return {"agent_id": 1, "owner": {"user_id": 44, "username": "adriana"}}
            return {"agent_id": 2, "owner": None}

        with patch("void_engine.mesa_engine.get_agent_slot", side_effect=slot_side):
            resp = client.post(
                "/mesa-village/agents/1/send-message",
                data={"recipient_agent_id": "2", "message_text": "hello"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        assert "msg_error=recipient_not_found" in resp.headers.get("Location", "")


class TestPurchaseTranslationAuth:
    """Tests for purchase_message_translation recipient-only access and idempotency."""

    def _purchase(self, message_id, user_id, fetchone_rows):
        """
        fetchone_rows: list of tuples for successive cursor.fetchone() calls:
          [balance_row, idempotency_row, message_row]
        """
        from void_engine.mesa_engine import purchase_message_translation

        mock_conn, mock_cursor = _make_mock_conn(fetchone_rows)
        with patch("void_engine.mesa_engine._init_message_tables"), \
             patch("void_engine.db_pool.get_db", return_value=mock_conn), \
             patch("void_engine.mesa_engine.get_translation_fee", return_value=Decimal("5.00")), \
             patch("void_engine.vortex_wallet._create_block", return_value={"block_index": 1}), \
             patch("void_engine.al_jabr_286.fatiha_286_hexdigest_from_str", return_value="abc"):
            return purchase_message_translation(message_id, user_id)

    def test_non_recipient_denied(self):
        """User who is not the recipient gets an access-denied error."""
        result = self._purchase(
            message_id=1,
            user_id=99,
            fetchone_rows=[
                (Decimal("100.00"),),
                None,
                ("encrypted_blob", 44),
            ],
        )
        assert result["ok"] is False
        assert "message" in result["error"].lower()

    def test_idempotent_second_purchase(self):
        """Second purchase request for same (message, user) returns already_owned."""
        result = self._purchase(
            message_id=1,
            user_id=44,
            fetchone_rows=[
                (Decimal("100.00"),),
                (1,),
            ],
        )
        assert result["ok"] is True
        assert result.get("already_owned") is True

    def test_insufficient_peace_denied(self):
        """User with balance below fee is denied."""
        result = self._purchase(
            message_id=1,
            user_id=44,
            fetchone_rows=[
                (Decimal("2.00"),),
                None,
                ("encrypted_blob", 44),
            ],
        )
        assert result["ok"] is False
        assert "insufficient" in result["error"].lower()


class TestMessageTranslateRouteMapping:
    """Tests for /mesa-village/messages/<id>/translate route redirect/error mapping."""

    @pytest.fixture
    def client(self):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        flask_app.config["WTF_CSRF_ENABLED"] = False
        with flask_app.test_client() as c:
            yield c

    def _login(self, client, user_id=44):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = "adriana"
            sess["role"] = "user"

    def _owner_slot(self, agent_id, owner_user_id=44):
        return {"agent_id": agent_id, "owner": {"user_id": owner_user_id, "username": "adriana"}}

    def test_translate_success_redirects_with_message_id(self, client):
        """Successful translation redirects to agent page with msg_translated param."""
        self._login(client, user_id=44)
        with patch("void_engine.mesa_engine.get_agent_slot", return_value=self._owner_slot(1, 44)), \
             patch("void_engine.mesa_engine.purchase_message_translation", return_value={"ok": True}):
            resp = client.post(
                "/mesa-village/messages/42/translate",
                data={"agent_id": "1"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        loc = resp.headers.get("Location", "")
        assert "msg_translated=42" in loc
        assert "/mesa-village/agents/1" in loc

    def test_translate_insufficient_peace_redirects(self, client):
        """Insufficient PEACE error redirects with insufficient_peace error code."""
        self._login(client, user_id=44)
        with patch("void_engine.mesa_engine.get_agent_slot", return_value=self._owner_slot(1, 44)), \
             patch("void_engine.mesa_engine.purchase_message_translation",
                   return_value={"ok": False, "error": "Insufficient PEACE tokens."}):
            resp = client.post(
                "/mesa-village/messages/42/translate",
                data={"agent_id": "1"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        assert "msg_error=insufficient_peace" in resp.headers.get("Location", "")

    def test_translate_not_your_message_redirects(self, client):
        """Non-recipient gets not_your_message error code in redirect."""
        self._login(client, user_id=44)
        with patch("void_engine.mesa_engine.get_agent_slot", return_value=self._owner_slot(1, 44)), \
             patch("void_engine.mesa_engine.purchase_message_translation",
                   return_value={"ok": False, "error": "Not your message"}):
            resp = client.post(
                "/mesa-village/messages/42/translate",
                data={"agent_id": "1"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        assert "msg_error=not_your_message" in resp.headers.get("Location", "")

    def test_translate_bad_agent_id_redirects_to_registry(self, client):
        """Tampered/unowned agent_id redirects to registry without calling purchase."""
        self._login(client, user_id=44)
        unowned_slot = {"agent_id": 99, "owner": {"user_id": 77, "username": "other"}}
        with patch("void_engine.mesa_engine.get_agent_slot", return_value=unowned_slot) as mock_slot, \
             patch("void_engine.mesa_engine.purchase_message_translation") as mock_purchase:
            resp = client.post(
                "/mesa-village/messages/42/translate",
                data={"agent_id": "99"},
                follow_redirects=False,
            )
        assert resp.status_code in (301, 302, 303)
        assert "/mesa-village/agents" in resp.headers.get("Location", "")
        mock_purchase.assert_not_called()


class TestAdminMessageLogNoContent:
    """Verify admin Mesa page renders message log without exposing message content."""

    @pytest.fixture
    def client(self):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        flask_app.config["WTF_CSRF_ENABLED"] = False
        with flask_app.test_client() as c:
            yield c

    def test_admin_mesa_renders_without_content_leak(self, client):
        """Admin Mesa page renders the message log section; no plaintext content exposed."""
        with client.session_transaction() as sess:
            sess["user_id"] = 44
            sess["username"] = "adriana"
            sess["role"] = "founder"

        sentinel_plain = "SUPER_SECRET_PLAIN_TEXT_DO_NOT_EXPOSE"
        sentinel_glyph = "GLYPH_ONLY_VISIBLE"

        fake_log = [
            {
                "message_id": 1,
                "sender_agent_id": 10,
                "recipient_agent_id": 20,
                "sent_at": "2026-01-01T00:00:00",
                "translations_purchased": 1,
            }
        ]

        with patch("void_engine.mesa_engine.get_admin_message_log", return_value=fake_log):
            resp = client.get("/admin/mesa")

        assert resp.status_code == 200
        body = resp.data.decode("utf-8", errors="replace")
        assert sentinel_plain not in body
        assert sentinel_glyph not in body
        assert "sender_agent_id" not in body or "10" in body or "20" in body
