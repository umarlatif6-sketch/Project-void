import json
from pathlib import Path

from scripts.adriana_mesh_eval import run_eval


def test_run_eval_mock_with_temp_prompt_set(tmp_path: Path):
    prompts_path = tmp_path / "prompts.json"
    profiles_path = Path("data/adriana_mesh_profiles.json")
    out_dir = tmp_path / "runs"

    prompts_path.write_text(
        json.dumps(
            {
                "prompts": [
                    {"id": "E01", "prompt": "Create a short launch plan."},
                    {"id": "E02", "prompt": "Add risk controls."},
                ]
            }
        ),
        encoding="utf-8",
    )

    report = run_eval(
        prompts_path=prompts_path,
        profile_name="cpu_light",
        profiles_path=profiles_path,
        out_dir=out_dir,
        ollama_url="http://127.0.0.1:11434",
        timeout_s=5,
        force_mock=True,
    )

    assert report["ok"] is True
    assert report["prompt_count"] == 2
    assert "average_overall" in report
    assert len(report["cases"]) == 2
