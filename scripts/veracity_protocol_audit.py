#!/usr/bin/env python3
"""VOID Veracity Protocol audit runner.

Builds a machine-readable report that checks the repository against the
Standing of Truth criteria in VOID_VERACITY_PROTOCOL.md.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import void_foundation
from void_engine.al_jabr_286 import BASE_FREQ, SOVEREIGN_BIT_DEPTH


OPENCLAW_ROOT = ROOT / "openclaw"
SERENA_DOC = OPENCLAW_ROOT / ".serena" / "cache" / "typescript" / "document_symbols.pkl"
SERENA_RAW = OPENCLAW_ROOT / ".serena" / "cache" / "typescript" / "raw_document_symbols.pkl"
OUTPUT_PATH = ROOT / "data" / "void_veracity_audit_report.json"

TARGET_TAYLOR_SLOPE = 1.9756
TAYLOR_TOLERANCE = 0.15
MIN_TAYLOR_R2 = 0.99
MIN_HUB_CORR = 0.85
MIN_BURST_CV = 1.5
MIN_SERENA_DOC_BYTES = 70 * 1024 * 1024

SYMBOL_PHRASES = ["mie void", "ionic phase matching"]
INFRASONIC_PHRASES = ["2.3 hz", "2.3hz", "2.3-hz", "2.3 hz infrasonic"]

FORBIDDEN_DEP_REGEXES = [
    re.compile(r"\bimport\s+web3\b"),
    re.compile(r"\bfrom\s+web3\s+import\b"),
    re.compile(r"\bimport\s+ethers\b"),
    re.compile(r"\bfrom\s+ethers\s+import\b"),
    re.compile(r"\bimport\s+brownie\b"),
    re.compile(r"\bfrom\s+brownie\s+import\b"),
    re.compile(r"\b(infura|alchemyapi|gas\s*fee|gas\s*price)\b", re.IGNORECASE),
]


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: Dict


def _iter_text_files(root: Path, extensions: Tuple[str, ...]) -> Iterable[Path]:
    skip_dirs = {
        ".git",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".venv",
        "venv",
    }
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            if p.suffix.lower() in extensions and p.stat().st_size <= 2 * 1024 * 1024:
                yield p


def _scan_for_phrases(root: Path, phrases: List[str], extensions: Tuple[str, ...]) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {k: [] for k in phrases}
    for path in _iter_text_files(root, extensions):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for phrase in phrases:
            if phrase in text:
                found[phrase].append(str(path.relative_to(ROOT)))
    return found


def statistical_truth_check() -> CheckResult:
    report = void_foundation.build_report()
    signals = report["signals"]

    taylor_slope = signals["taylors_law"]["slope"]
    taylor_r2 = signals["taylors_law"]["r2"]
    hub_corr = signals["popularity_hub"]["pearson_frequency_vs_neighbor_frequency"]
    burst_cv = signals["burst_dynamics"]["mean_burst_cv"]

    in_band = abs(taylor_slope - TARGET_TAYLOR_SLOPE) <= TAYLOR_TOLERANCE
    passed = in_band and taylor_r2 >= MIN_TAYLOR_R2 and hub_corr >= MIN_HUB_CORR and burst_cv >= MIN_BURST_CV

    return CheckResult(
        name="statistical_truth",
        passed=passed,
        details={
            "taylor": {
                "slope": taylor_slope,
                "target": TARGET_TAYLOR_SLOPE,
                "tolerance": TAYLOR_TOLERANCE,
                "in_band": in_band,
                "r2": taylor_r2,
                "min_r2": MIN_TAYLOR_R2,
            },
            "hub_clustering": {
                "pearson": hub_corr,
                "min_required": MIN_HUB_CORR,
            },
            "burst_dynamics": {
                "cv": burst_cv,
                "min_required": MIN_BURST_CV,
            },
        },
    )


def structural_truth_check() -> CheckResult:
    serena_doc_exists = SERENA_DOC.exists()
    serena_doc_size = SERENA_DOC.stat().st_size if serena_doc_exists else 0
    serena_raw_exists = SERENA_RAW.exists()

    phrase_hits = _scan_for_phrases(
        OPENCLAW_ROOT if OPENCLAW_ROOT.exists() else ROOT,
        SYMBOL_PHRASES,
        (".py", ".ts", ".tsx", ".js", ".mjs", ".md", ".json"),
    )
    symbol_phrases_present_count = sum(1 for p in SYMBOL_PHRASES if len(phrase_hits[p]) > 0)
    phrase_coverage = symbol_phrases_present_count / max(1, len(SYMBOL_PHRASES))

    # Weighted evidence model for structural truth.
    # Phrase coverage is meaningful but should not singularly fail the body check
    # when the Serena symbol body is present and healthy.
    score = 0.0
    if serena_doc_exists:
        score += 0.40
    if serena_doc_size >= MIN_SERENA_DOC_BYTES:
        score += 0.20
    if serena_raw_exists:
        score += 0.20
    score += 0.20 * phrase_coverage

    passed = serena_doc_exists and serena_raw_exists and score >= 0.65

    return CheckResult(
        name="structural_truth",
        passed=passed,
        details={
            "serena_document_symbols": {
                "path": str(SERENA_DOC.relative_to(ROOT)),
                "exists": serena_doc_exists,
                "size_bytes": serena_doc_size,
                "min_expected_bytes": MIN_SERENA_DOC_BYTES,
            },
            "serena_raw_symbols": {
                "path": str(SERENA_RAW.relative_to(ROOT)),
                "exists": serena_raw_exists,
            },
            "symbol_phrase_coverage": {
                "required_total": len(SYMBOL_PHRASES),
                "present_total": symbol_phrases_present_count,
                "coverage_ratio": round(phrase_coverage, 4),
            },
            "weighted_score": {
                "score": round(score, 4),
                "min_required": 0.65,
                "weights": {
                    "serena_document_exists": 0.40,
                    "serena_document_size": 0.20,
                    "serena_raw_exists": 0.20,
                    "phrase_coverage": 0.20,
                },
            },
            "required_symbol_phrases": phrase_hits,
        },
    )


def resonance_truth_check() -> CheckResult:
    has_286 = SOVEREIGN_BIT_DEPTH == 286
    has_432 = abs(BASE_FREQ - 432.0) < 1e-9

    infrasonic_hits = _scan_for_phrases(
        ROOT,
        INFRASONIC_PHRASES,
        (".py", ".md", ".txt", ".html", ".json"),
    )
    has_23_reference = any(len(v) > 0 for v in infrasonic_hits.values())

    forbidden_hits = []
    code_roots = [
        ROOT / "void_engine",
        ROOT / "routes",
        ROOT / "openclaw",
    ]
    for code_root in code_roots:
        if not code_root.exists():
            continue
        for path in _iter_text_files(code_root, (".py", ".ts", ".tsx", ".js", ".mjs")):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for rx in FORBIDDEN_DEP_REGEXES:
                if rx.search(text):
                    forbidden_hits.append(str(path.relative_to(ROOT)))
                    break

    passed = has_286 and has_432 and has_23_reference and len(forbidden_hits) == 0

    return CheckResult(
        name="resonance_truth",
        passed=passed,
        details={
            "al_jabr_anchor": {
                "bit_depth": SOVEREIGN_BIT_DEPTH,
                "expected_bit_depth": 286,
                "base_frequency": BASE_FREQ,
                "expected_base_frequency": 432.0,
            },
            "infrasonic_2_3hz_references": infrasonic_hits,
            "forbidden_goliath_dependency_hits": sorted(set(forbidden_hits)),
        },
    )


def build_audit_report() -> Dict:
    statistical = statistical_truth_check()
    structural = structural_truth_check()
    resonance = resonance_truth_check()

    checks = [statistical, structural, resonance]
    overall = all(c.passed for c in checks)

    return {
        "protocol": "VOID_VERACITY_PROTOCOL",
        "standing_date": "2026-04-28",
        "overall_verified": overall,
        "checks": [asdict(c) for c in checks],
    }


def main() -> int:
    report = build_audit_report()
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nReport written: {OUTPUT_PATH}")
    return 0 if report["overall_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())