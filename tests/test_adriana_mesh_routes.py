from flask import Flask

from routes.adriana_mesh import adriana_mesh_bp


def test_profiles_endpoint_lists_available_profiles():
    app = Flask(__name__)
    app.register_blueprint(adriana_mesh_bp)

    with app.test_client() as client:
        resp = client.get("/api/adriana/mesh/profiles")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "cpu_light" in data["profiles"]


def test_run_endpoint_validates_missing_prompt():
    app = Flask(__name__)
    app.register_blueprint(adriana_mesh_bp)

    with app.test_client() as client:
        resp = client.post("/api/adriana/mesh/run", json={"profile": "cpu_light"})

    assert resp.status_code == 400
    data = resp.get_json()
    assert data["ok"] is False
    assert data["error"] == "missing_prompt"


def test_eval_endpoint_runs_in_mock_mode():
    app = Flask(__name__)
    app.register_blueprint(adriana_mesh_bp)

    with app.test_client() as client:
        resp = client.post("/api/adriana/mesh/eval", json={"mock": True, "profile": "cpu_light"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["report"]["prompt_count"] == 20
