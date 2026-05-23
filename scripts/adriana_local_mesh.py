#!/usr/bin/env python3
"""Adriana Local Mesh Runner

CPU-light multi-cell orchestrator for local open-source models.
Designed for Ollama, with a mock fallback mode for dry runs.

Cells:
- router: task split and intent map
- research: evidence extraction and synthesis
- voice: Adriana-style response shaping
- critic: consistency and risk review
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES = ROOT / "data" / "adriana_mesh_profiles.json"
DEFAULT_OUT_DIR = ROOT / "data" / "adriana_mesh_runs"


def load_profile_bundle(profiles_path: Path, profile_name: str) -> Dict[str, Any]:
    profiles = load_json(profiles_path)
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown_profile: {profile_name}")

    cells = profile.get("cells")
    if not isinstance(cells, dict):
        raise ValueError("invalid_profile_cells")

    return {"profiles": profiles, "profile": profile, "cells": cells}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("mesh_%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"invalid_json_object: {path}")
    return data


def call_ollama(
    *,
    base_url: str,
    model: str,
    system: str,
    prompt: str,
    temperature: float,
    num_predict: int,
    timeout_s: int,
) -> str:
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8")
    parsed = json.loads(raw)
    out = str(parsed.get("response") or "").strip()
    if not out:
        raise ValueError("empty_ollama_response")
    return out


def mock_cell(cell: str, prompt: str) -> str:
    lines = [ln.strip() for ln in prompt.splitlines() if ln.strip()]
    seed = " ".join(lines)[:280]
    if cell == "router":
        return (
            "Task map: 1) classify intent, 2) extract constraints, 3) produce answer draft, "
            "4) quality gate.\nPrimary route: synthesis.\nRisk level: low."
        )
    if cell == "research":
        return f"Evidence digest: {seed}"
    if cell == "voice":
        return f"Adriana response: {seed}"
    if cell == "critic":
        return "Verdict: pass\nChecks: coherence=ok, contradiction=none, actionability=ok"
    return seed


def compact_peer_context(peer_files: List[Path], max_chars: int = 2400) -> str:
    snippets: List[str] = []
    for p in peer_files:
        try:
            data = load_json(p)
        except Exception:
            continue
        rid = str(data.get("run_id") or p.stem)
        voice = str((((data.get("stages") or {}).get("voice") or {}).get("output") or ""))
        critic = str((((data.get("stages") or {}).get("critic") or {}).get("output") or ""))
        block = f"[peer:{rid}]\nvoice: {voice[:350]}\ncritic: {critic[:220]}"
        snippets.append(block)
    joined = "\n\n".join(snippets)
    return joined[:max_chars]


def run_cell(
    *,
    cell_name: str,
    cell_cfg: Dict[str, Any],
    prompt: str,
    ollama_url: str,
    timeout_s: int,
    force_mock: bool,
) -> Dict[str, Any]:
    model = str(cell_cfg.get("model") or "")
    system = str(cell_cfg.get("system") or "")
    temperature = float(cell_cfg.get("temperature", 0.2))
    num_predict = int(cell_cfg.get("num_predict", 400))

    if force_mock:
        output = mock_cell(cell_name, prompt)
        return {
            "cell": cell_name,
            "model": model,
            "mode": "mock",
            "output": output,
        }

    try:
        output = call_ollama(
            base_url=ollama_url,
            model=model,
            system=system,
            prompt=prompt,
            temperature=temperature,
            num_predict=num_predict,
            timeout_s=timeout_s,
        )
        mode = "ollama"
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
        output = mock_cell(cell_name, prompt)
        mode = f"mock_fallback:{type(e).__name__}"

    return {
        "cell": cell_name,
        "model": model,
        "mode": mode,
        "output": output,
    }


def run_mesh(
    *,
    prompt: str,
    profile_name: str = "cpu_light",
    profiles_path: Path = DEFAULT_PROFILES,
    out_dir: Path = DEFAULT_OUT_DIR,
    ollama_url: str = "http://127.0.0.1:11434",
    timeout_s: int = 60,
    sandbox: str = "sandbox_a",
    peer_inputs: List[Path] | None = None,
    force_mock: bool = False,
    write_artifact: bool = True,
) -> Dict[str, Any]:
    if not prompt or not str(prompt).strip():
        raise ValueError("missing_prompt")

    bundle = load_profile_bundle(Path(profiles_path), profile_name)
    cells = bundle["cells"]

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    peer_files = [Path(p) for p in (peer_inputs or [])]
    peer_context = compact_peer_context(peer_files)

    prompt_map = build_prompts(
        user_prompt=prompt,
        peer_context=peer_context,
        router_out="",
        research_out="",
        voice_out="",
    )

    router = run_cell(
        cell_name="router",
        cell_cfg=dict(cells.get("router") or {}),
        prompt=prompt_map["router"],
        ollama_url=ollama_url,
        timeout_s=timeout_s,
        force_mock=force_mock,
    )

    prompt_map = build_prompts(
        user_prompt=prompt,
        peer_context=peer_context,
        router_out=router["output"],
        research_out="",
        voice_out="",
    )
    research = run_cell(
        cell_name="research",
        cell_cfg=dict(cells.get("research") or {}),
        prompt=prompt_map["research"],
        ollama_url=ollama_url,
        timeout_s=timeout_s,
        force_mock=force_mock,
    )

    prompt_map = build_prompts(
        user_prompt=prompt,
        peer_context=peer_context,
        router_out=router["output"],
        research_out=research["output"],
        voice_out="",
    )
    voice = run_cell(
        cell_name="voice",
        cell_cfg=dict(cells.get("voice") or {}),
        prompt=prompt_map["voice"],
        ollama_url=ollama_url,
        timeout_s=timeout_s,
        force_mock=force_mock,
    )

    critic = run_cell(
        cell_name="critic",
        cell_cfg=dict(cells.get("critic") or {}),
        prompt=build_prompts(
            user_prompt=prompt,
            peer_context=peer_context,
            router_out=router["output"],
            research_out=research["output"],
            voice_out=voice["output"],
        )["critic"],
        ollama_url=ollama_url,
        timeout_s=timeout_s,
        force_mock=force_mock,
    )

    artifact = {
        "ok": True,
        "run_id": run_id(),
        "generated_at": utc_now(),
        "sandbox": sandbox,
        "profile": profile_name,
        "ollama_url": ollama_url,
        "mock": bool(force_mock),
        "prompt": prompt,
        "peer_inputs": [str(p) for p in peer_files],
        "stages": {
            "router": router,
            "research": research,
            "voice": voice,
            "critic": critic,
        },
        "final": {
            "response": voice.get("output", ""),
            "verdict": critic.get("output", ""),
        },
    }

    out_path = out_dir / f"{artifact['run_id']}_{sandbox}.json"
    artifact["artifact_path"] = str(out_path)

    if write_artifact:
        out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

    return artifact


def build_prompts(
    *,
    user_prompt: str,
    peer_context: str,
    router_out: str,
    research_out: str,
    voice_out: str,
) -> Dict[str, str]:
    router_prompt = textwrap.dedent(
        f"""
        You are the router cell in Adriana mesh.
        User intent:
        {user_prompt}

        Peer sandbox context (optional):
        {peer_context or 'none'}

        Return concise task map and route plan.
        """
    ).strip()

    research_prompt = textwrap.dedent(
        f"""
        You are the research cell.
        User intent:
        {user_prompt}

        Router plan:
        {router_out}

        Produce short evidence digest, assumptions, and concrete steps.
        """
    ).strip()

    voice_prompt = textwrap.dedent(
        f"""
        You are Adriana voice cell.
        User intent:
        {user_prompt}

        Router plan:
        {router_out}

        Research digest:
        {research_out}

        Produce operator-ready response in Adriana style:
        - direct
        - practical
        - no fluff
        """
    ).strip()

    critic_prompt = textwrap.dedent(
        f"""
        You are the critic cell.
        Evaluate this response for contradictions, missing constraints, and clarity.

        Candidate response:
        {voice_out}

        Return verdict with fixes if needed.
        """
    ).strip()

    return {
        "router": router_prompt,
        "research": research_prompt,
        "voice": voice_prompt,
        "critic": critic_prompt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Adriana local mesh with CPU-light model profiles")
    parser.add_argument("--prompt", required=True, help="User prompt to process")
    parser.add_argument("--profile", default="cpu_light", help="Profile key in profiles json")
    parser.add_argument("--profiles", default=str(DEFAULT_PROFILES), help="Path to profiles json")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory for run artifacts")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", help="Ollama base URL")
    parser.add_argument("--timeout", type=int, default=60, help="Per-cell timeout in seconds")
    parser.add_argument("--sandbox", default="sandbox_a", help="Sandbox label for connected runs")
    parser.add_argument("--peer", action="append", default=[], help="Peer run artifact json path (repeatable)")
    parser.add_argument("--mock", action="store_true", help="Force mock mode for all cells")
    args = parser.parse_args()

    try:
        artifact = run_mesh(
            prompt=args.prompt,
            profile_name=args.profile,
            profiles_path=Path(args.profiles),
            out_dir=Path(args.out_dir),
            ollama_url=args.ollama_url,
            timeout_s=args.timeout,
            sandbox=args.sandbox,
            peer_inputs=[Path(p) for p in args.peer],
            force_mock=bool(args.mock),
            write_artifact=True,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print("Adriana local mesh run complete")
    print(f"artifact: {artifact['artifact_path']}")
    print("final_response:")
    print(artifact["final"]["response"])
    print("critic_verdict:")
    print(artifact["final"]["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
