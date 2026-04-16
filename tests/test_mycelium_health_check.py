from scripts.mycelium_health_check import build_report


def test_mycelium_health_check_report_shape() -> None:
    report = build_report()

    assert report["report_type"] == "mycelium_health_check"
    assert report["overall_status"] in {"pass", "warn", "fail"}
    assert set(report["sections"].keys()) == {
        "continuity",
        "convergence",
        "thread_state",
        "foundation",
    }


def test_mycelium_health_check_uses_conservative_floor() -> None:
    report = build_report()
    convergence = report["sections"]["convergence"]["checks"]
    floor_check = next(item for item in convergence if item["name"] == "economic_reduction_floor")

    assert floor_check["status"] == "pass"
