from pathlib import Path

from scripts import adriana_mesh_readiness as readiness


def test_run_readiness_handles_unreachable_ollama(tmp_path: Path):
    profiles_path = Path("data/adriana_mesh_profiles.json")
    out_dir = tmp_path / "runs"

    report = readiness.run_readiness(
        profile_name="cpu_light",
        profiles_path=profiles_path,
        out_dir=out_dir,
        ollama_url="http://127.0.0.1:9",
        timeout_s=1,
    )

    assert report["ok"] is True
    assert report["checks"]["ollama_reachable"] is False
    assert report["readiness_ok"] is False
    assert "runs" in report
    assert report["runs"]["a"]["artifact_path"]
    assert report["runs"]["b"]["artifact_path"]
