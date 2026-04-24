from void_engine.cockroach_sanitation import run_sanitation_demo, run_dual_track_demo
from void_engine.cockroach_agent_control import (
    load_agent_control_profile,
    build_control_commands,
    run_agent_piloted_cycle,
)


def test_sanitation_demo_still_works():
    result = run_sanitation_demo(
        zones=["zone_a", "zone_b"],
        waste_per_zone=75,
        cockroaches_per_bin=6,
        dark_rounds=4,
    )
    assert result["demo"] == "cockroach_sanitation_protocol"
    assert "cycle_result" in result
    assert result["cycle_result"]["bins_processed"] == 2


def test_dual_track_demo_separates_systems():
    result = run_dual_track_demo(
        zones=["zone_a", "zone_b"],
        waste_per_zone=70,
        cockroaches_per_bin=5,
        dark_rounds=3,
    )
    assert result["demo"] == "cockroach_dual_track"
    assert "sanitation_track" in result
    assert "agent_control_track" in result
    assert result["agent_control_track"]["mode"] == "agent_piloted_sanitation"


def test_agent_control_commands_generated_per_zone():
    profile = load_agent_control_profile()
    commands = build_control_commands(
        zones=["zone_a", "zone_b", "zone_c"],
        waste_map={"zone_a": 50, "zone_b": 75, "zone_c": 95},
        base_dark_rounds=4,
        base_cockroaches=6,
        profile=profile,
    )
    assert len(commands) == 3
    assert all(c.target_dark_rounds >= 1 for c in commands)
    assert all(c.target_cockroaches >= 2 for c in commands)


def test_agent_piloted_cycle_runs():
    result = run_agent_piloted_cycle(
        zones=["zone_a", "zone_b"],
        waste_map={"zone_a": 80, "zone_b": 65},
        base_dark_rounds=4,
        base_cockroaches=6,
    )
    assert result["mode"] == "agent_piloted_sanitation"
    assert result["bins_processed"] == 2
    assert "zone_results" in result
