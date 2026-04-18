import os
import sys
from unittest.mock import patch

import pytest


ROOT = os.path.join(os.path.dirname(__file__), "..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("SESSION_SECRET", "test_secret_for_unit_tests_only")
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/void_test")
os.environ.setdefault("VOID_RUN_STARTUP_MIGRATIONS", "false")


@pytest.fixture
def client():
    from app import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as test_client:
        yield test_client


def test_get_character_profile_returns_exported_profile(client):
    expected_profile = {
        "visitor_key": "user:44",
        "codons": [{"codon_text": "seed", "glyph_seq": "B-nn-D", "window_index": 1, "created_at": "2026-04-17T00:00:00Z"}],
        "buffer_messages": [{"role": "user", "content": "hello"}],
        "buffer_window_index": 2,
        "codon_count": 1,
        "buffer_message_count": 1,
    }

    with client.session_transaction() as session:
        session["user_id"] = 44

    with patch("routes.character_profile.export_character_profile", return_value=expected_profile) as mock_export:
        response = client.get("/api/profile/character")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "profile": expected_profile}
    mock_export.assert_called_once_with()


def test_delete_character_profile_returns_purge_result(client):
    expected_result = {
        "visitor_key": "user:44",
        "codons_deleted": 3,
        "buffer_cleared": True,
    }

    with client.session_transaction() as session:
        session["user_id"] = 44

    with patch("routes.character_profile.delete_character_profile", return_value=expected_result) as mock_delete:
        response = client.delete("/api/profile/character")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "result": expected_result}
    mock_delete.assert_called_once_with()


def test_post_character_profile_is_not_allowed(client):
    response = client.post("/api/profile/character", json={"unexpected": True})

    assert response.status_code == 405