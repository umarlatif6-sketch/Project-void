#!/usr/bin/env python3
"""Run Adriana mesh evaluation prompts and produce a scoring report."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from scripts.adriana_local_mesh import run_mesh

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS = ROOT / "data" / "adriana_eval_prompts.json"
DEFAULT_OUT_DIR = ROOT / "data" / "adriana_mesh_runs"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_prompts(path: Path) -> List[Dict[str, str]]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    prompts = blob.get("prompts") if isinstance(blob, dict) else None
    if not isinstance(prompts, list) or not prompts:
        raise ValueError("invalid_prompt_set")
    out = []
    for item in prompts:
        if isinstance(item, dict) and item.get("id") and item.get("prompt"):
            out.append({"id": str(item["id"]), "prompt": str(item["prompt"])})
    if not out:
        raise ValueError("prompt_set_empty")
    return out


def _score_case(response: str, verdict: str) -> Dict[str, float]:
    response = response or ""
    verdict = verdict or ""

    non_empty = 1.0 if response.strip() else 0.0
    has_steps = 1.0 if any(tok in response for tok in ("1.", "2.", "Step", "- ")) else 0.4
    concise = 1.0 if len(response) <= 1800 else 0.6
    critic_ok = 1.0 if any(tok in verdict.lower() for tok in ("pass", "coherence=ok", "contradiction=none")) else 0.5

    clarity = round((non_empty + concise) / 2.0, 3)
    actionability = round((non_empty + has_steps) / 2.0, 3)
    consistency = round(critic_ok, 3)
    overall = round((clarity + actionability + consistency) / 3.0, 3)

    return {
        "clarity": clarity,
        "actionability": actionability,
        "consistency": consistency,
        "overall": overall,
    }


def run_eval(
    *,
    prompts_path: Path,
    profile_name: str,
    profiles_path: Path,
    out_dir: Path,
    ollama_url: str,
    timeout_s: int,
    force_mock: bool,
) -> Dict[str, Any]:
    prompts = _load_prompts(prompts_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases: List[Dict[str, Any]] = []
    overall_scores: List[float] = []

    for item in prompts:
        run = run_mesh(
            prompt=item["prompt"],
            profile_name=profile_name,
            profiles_path=profiles_path,
            out_dir=out_dir,
            ollama_url=ollama_url,
            timeout_s=timeout_s,
            sandbox=f"eval_{item['id'].lower()}",
            peer_inputs=[],
            force_mock=force_mock,
            write_artifact=False,
        )

        response = str((run.get("final") or {}).get("response") or "")
        verdict = str((run.get("final") or {}).get("verdict") or "")
        score = _score_case(response, verdict)
        overall_scores.append(score["overall"])

        cases.append(
            {
                "id": item["id"],
                "prompt": item["prompt"],
                "stages": run.get("stages", {}),
                "final": run.get("final", {}),
                "score": score,
            }
        )

    avg_overall = round(statistics.fmean(overall_scores), 3) if overall_scores else 0.0

    return {
        "ok": True,
        "generated_at": _utc_now(),
        "prompt_count": len(cases),
        "profile": profile_name,
        "mock": bool(force_mock),
        "average_overall": avg_overall,
        "pass_threshold": 0.75,
        "passes_threshold": avg_overall >= 0.75,
        "cases": cases,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Evaluate Adriana local mesh on 20 prompts")
    p.add_argument("--prompts", default=str(DEFAULT_PROMPTS))
    p.add_argument("--profile", default="cpu_light")
    p.add_argument("--profiles", default=str(ROOT / "data" / "adriana_mesh_profiles.json"))
    p.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--mock", action="store_true")
    args = p.parse_args()

    report = run_eval(
        prompts_path=Path(args.prompts),
        profile_name=args.profile,
        profiles_path=Path(args.profiles),
        out_dir=Path(args.out_dir),
        ollama_url=args.ollama_url,
        timeout_s=args.timeout,
        force_mock=bool(args.mock),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out_dir) / f"adriana_eval_report_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Adriana mesh evaluation complete")
    print(f"artifact: {out_path}")
    print(f"average_overall: {report['average_overall']}")
    print(f"passes_threshold: {report['passes_threshold']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
