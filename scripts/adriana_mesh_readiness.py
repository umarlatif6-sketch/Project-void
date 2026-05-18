#!/usr/bin/env python3
"""Run real-model readiness checks for Adriana local mesh."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from scripts.adriana_local_mesh import run_mesh, load_profile_bundle

ROOT = Path(__file__).resolve().parents[1]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_ollama_tags(base_url: str, timeout_s: int) -> Dict[str, Any]:
    req = urllib.request.Request(url=f"{base_url.rstrip('/')}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "payload": payload}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}


def run_readiness(
    *,
    profile_name: str,
    profiles_path: Path,
    out_dir: Path,
    ollama_url: str,
    timeout_s: int,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle = load_profile_bundle(profiles_path, profile_name)
    cells = bundle["cells"]
    required_models = sorted({str(v.get("model") or "") for v in cells.values() if isinstance(v, dict) and v.get("model")})

    tags = _fetch_ollama_tags(ollama_url, timeout_s)
    installed_models: List[str] = []
    if tags.get("ok"):
        installed_models = sorted(
            str(m.get("name") or "")
            for m in (tags.get("payload", {}).get("models") or [])
            if isinstance(m, dict)
        )

    missing_models = [m for m in required_models if m not in installed_models]

    run_a = run_mesh(
        prompt="Readiness pass A: produce concise operator plan.",
        profile_name=profile_name,
        profiles_path=profiles_path,
        out_dir=out_dir,
        ollama_url=ollama_url,
        timeout_s=timeout_s,
        sandbox="readiness_a",
        peer_inputs=[],
        force_mock=False,
        write_artifact=True,
    )
    run_b = run_mesh(
        prompt="Readiness pass B: refine A and add explicit risk controls.",
        profile_name=profile_name,
        profiles_path=profiles_path,
        out_dir=out_dir,
        ollama_url=ollama_url,
        timeout_s=timeout_s,
        sandbox="readiness_b",
        peer_inputs=[Path(run_a["artifact_path"])],
        force_mock=False,
        write_artifact=True,
    )

    modes_a = [str(((run_a.get("stages") or {}).get(c) or {}).get("mode") or "") for c in ("router", "research", "voice", "critic")]
    modes_b = [str(((run_b.get("stages") or {}).get(c) or {}).get("mode") or "") for c in ("router", "research", "voice", "critic")]

    all_ollama = all(m == "ollama" for m in (modes_a + modes_b))
    readiness_ok = bool(tags.get("ok") and not missing_models and all_ollama)

    return {
        "ok": True,
        "generated_at": _utc_now(),
        "profile": profile_name,
        "ollama_url": ollama_url,
        "readiness_ok": readiness_ok,
        "checks": {
            "ollama_reachable": bool(tags.get("ok")),
            "required_models": required_models,
            "installed_models": installed_models,
            "missing_models": missing_models,
            "all_cells_used_ollama": all_ollama,
        },
        "runs": {
            "a": {
                "artifact_path": run_a.get("artifact_path"),
                "modes": modes_a,
            },
            "b": {
                "artifact_path": run_b.get("artifact_path"),
                "modes": modes_b,
            },
        },
        "notes": tags.get("error", "") if not tags.get("ok") else "",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run Adriana mesh real-model readiness checks")
    p.add_argument("--profile", default="cpu_light")
    p.add_argument("--profiles", default=str(ROOT / "data" / "adriana_mesh_profiles.json"))
    p.add_argument("--out-dir", default=str(ROOT / "data" / "adriana_mesh_runs"))
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p.add_argument("--timeout", type=int, default=20)
    args = p.parse_args()

    report = run_readiness(
        profile_name=args.profile,
        profiles_path=Path(args.profiles),
        out_dir=Path(args.out_dir),
        ollama_url=args.ollama_url,
        timeout_s=args.timeout,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out_dir) / f"adriana_readiness_report_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Adriana mesh readiness check complete")
    print(f"artifact: {out_path}")
    print(f"readiness_ok: {report['readiness_ok']}")
    if report.get("notes"):
        print(f"notes: {report['notes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
