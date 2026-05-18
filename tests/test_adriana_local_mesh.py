from scripts.adriana_local_mesh import build_prompts, run_cell


def test_build_prompts_critic_uses_voice_output():
    prompts = build_prompts(
        user_prompt="Plan launch",
        peer_context="none",
        router_out="router text",
        research_out="research text",
        voice_out="voice final text",
    )

    assert "voice final text" in prompts["critic"]
    assert "research text" not in prompts["critic"]


def test_run_cell_mock_mode_returns_output():
    out = run_cell(
        cell_name="critic",
        cell_cfg={"model": "x", "system": "y", "temperature": 0.1, "num_predict": 100},
        prompt="Check this",
        ollama_url="http://127.0.0.1:11434",
        timeout_s=2,
        force_mock=True,
    )

    assert out["mode"] == "mock"
    assert "Verdict:" in out["output"]
