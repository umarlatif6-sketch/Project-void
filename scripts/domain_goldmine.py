#!/usr/bin/env python3
"""Domain Goldmine scanner for high-signal brand domain discovery.

Generates candidate names, scores resale upside, checks likely availability
via RDAP, and outputs ranked buy/hold/watch actions.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests

DEFAULT_TLDS = ["com", "io", "ai", "app", "dev", "xyz"]
DEFAULT_PORTFOLIO_TAGS = ["void", "agent", "mesh", "signal", "vault", "github", "code"]

PREFIX_WORDS = [
    "styrofo",
    "void",
    "gold",
    "prime",
    "alpha",
    "neo",
    "mint",
    "rapid",
    "orbit",
    "pixel",
    "nova",
    "cloud",
    "smart",
    "ultra",
    "vector",
]

CORE_WORDS = [
    "domain",
    "domains",
    "name",
    "names",
    "folio",
    "portfolio",
    "signal",
    "forge",
    "mint",
    "stack",
    "grid",
    "vault",
    "pilot",
    "foundry",
    "scout",
    "lens",
    "loop",
    "stream",
    "path",
    "craft",
]

SUFFIX_WORDS = [
    "hub",
    "lab",
    "labs",
    "works",
    "studio",
    "market",
    "fund",
    "capital",
    "zone",
    "base",
    "deck",
    "pool",
    "flow",
    "sync",
    "pulse",
    "rise",
]

NO_MATCH_TOKENS = [
    "no match",
    "not found",
    "domain not found",
    "object does not exist",
    "status: free",
]


@dataclass
class DomainCandidate:
    fqdn: str
    label: str
    tld: str
    score: int
    resale_grade: str
    action: str
    github_fit: int
    availability: str
    check_signal: str


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _resale_grade(score: int) -> str:
    if score >= 85:
        return "gold"
    if score >= 72:
        return "silver"
    if score >= 60:
        return "bronze"
    return "spec"


def _recommended_action(score: int, availability: str) -> str:
    if availability != "likely_available":
        return "watch"
    if score >= 80:
        return "buy_now"
    if score >= 65:
        return "hold_shortlist"
    return "watch"


def _pronounceability_score(label: str) -> int:
    vowels = set("aeiou")
    has_vowel = any(ch in vowels for ch in label)
    has_consonant = any(ch.isalpha() and ch not in vowels for ch in label)
    if not (has_vowel and has_consonant):
        return 0

    transitions = 0
    prev_is_vowel = label[0] in vowels
    for ch in label[1:]:
        current = ch in vowels
        if current != prev_is_vowel:
            transitions += 1
        prev_is_vowel = current

    if transitions >= 4:
        return 12
    if transitions >= 2:
        return 8
    return 4


def score_domain_label(label: str, portfolio_tags: Iterable[str]) -> tuple[int, int]:
    score = 45
    github_fit = 0

    length = len(label)
    if 6 <= length <= 12:
        score += 20
    elif 13 <= length <= 16:
        score += 10
    elif length <= 5:
        score += 6
    else:
        score -= 8

    if "-" in label:
        score -= 20
    if any(ch.isdigit() for ch in label):
        score -= 10

    score += _pronounceability_score(label)

    premium_terms = {"ai", "lab", "labs", "vault", "market", "fund", "capital", "prime", "mint"}
    for term in premium_terms:
        if term in label:
            score += 3

    for tag in portfolio_tags:
        tag_norm = _normalize_token(tag)
        if tag_norm and tag_norm in label:
            github_fit += 1
            score += 4

    if label.startswith("styrofo"):
        score += 5

    return max(1, min(100, score)), github_fit


def generate_labels(seed_phrases: list[str], max_labels: int) -> list[str]:
    seeds = [_normalize_token(s) for s in seed_phrases if _normalize_token(s)]
    if not seeds:
        seeds = ["styrofo"]

    generated: list[str] = []
    seen = set()

    def add(value: str) -> None:
        value = _normalize_token(value)
        if not value or value in seen:
            return
        seen.add(value)
        generated.append(value)

    for seed in seeds:
        add(seed)
        for core in CORE_WORDS:
            add(f"{seed}{core}")
            add(f"{core}{seed}")
        for suffix in SUFFIX_WORDS:
            add(f"{seed}{suffix}")

    for prefix in PREFIX_WORDS:
        for core in CORE_WORDS:
            add(f"{prefix}{core}")
            for suffix in SUFFIX_WORDS:
                add(f"{prefix}{core}{suffix}")

    return generated[:max_labels]


def check_domain_likely_availability(fqdn: str, timeout: float = 4.0) -> tuple[str, str]:
    url = f"https://rdap.org/domain/{fqdn}"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        return "unknown", f"rdap_error:{exc.__class__.__name__}"

    body = response.text.lower()
    if response.status_code == 404:
        return "likely_available", "rdap_404"
    if response.status_code == 200:
        return "registered", "rdap_registered"
    if response.status_code == 429:
        return "unknown", "rdap_rate_limited"
    if any(token in body for token in NO_MATCH_TOKENS):
        return "likely_available", "rdap_no_match"
    return "unknown", f"rdap_status_{response.status_code}"


def build_domain_candidates(
    seed_phrases: list[str],
    tlds: list[str],
    portfolio_tags: list[str],
    max_labels: int,
    check_limit: int,
) -> list[DomainCandidate]:
    labels = generate_labels(seed_phrases, max_labels=max_labels)
    candidates: list[DomainCandidate] = []
    checks = 0

    for label in labels:
        score, github_fit = score_domain_label(label, portfolio_tags)
        grade = _resale_grade(score)

        for tld in tlds:
            fqdn = f"{label}.{tld}"
            availability = "unchecked"
            signal = "skipped"

            if checks < check_limit:
                availability, signal = check_domain_likely_availability(fqdn)
                checks += 1

            candidates.append(
                DomainCandidate(
                    fqdn=fqdn,
                    label=label,
                    tld=tld,
                    score=score,
                    resale_grade=grade,
                    action=_recommended_action(score, availability),
                    github_fit=github_fit,
                    availability=availability,
                    check_signal=signal,
                )
            )

    candidates.sort(
        key=lambda c: (c.availability == "likely_available", c.score, c.github_fit),
        reverse=True,
    )
    return candidates


def write_outputs(candidates: list[DomainCandidate], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(asdict(candidates[0]).keys()) if candidates else []
    if candidates:
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in candidates:
                writer.writerow(asdict(row))

        with json_path.open("w", encoding="utf-8") as handle:
            json.dump([asdict(c) for c in candidates], handle, indent=2)


def _parse_csv_words(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find likely-available high-value domains")
    parser.add_argument(
        "--seed",
        action="append",
        default=["styrofo", "five little words"],
        help="Seed word or phrase. Repeat flag for multiple seeds.",
    )
    parser.add_argument(
        "--tlds",
        default=",".join(DEFAULT_TLDS),
        help="Comma-separated TLD list without dots (example: com,io,ai)",
    )
    parser.add_argument(
        "--portfolio-tags",
        default=",".join(DEFAULT_PORTFOLIO_TAGS),
        help="Comma-separated tags that align with your GitHub portfolio",
    )
    parser.add_argument("--max-labels", type=int, default=300, help="Max generated labels")
    parser.add_argument("--check-limit", type=int, default=120, help="Max RDAP checks per run")
    parser.add_argument("--top", type=int, default=30, help="Top rows to print")
    parser.add_argument(
        "--csv-out",
        default="exports/domain_goldmine_candidates.csv",
        help="CSV output path",
    )
    parser.add_argument(
        "--json-out",
        default="exports/domain_goldmine_candidates.json",
        help="JSON output path",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    tlds = [t.lower().lstrip(".") for t in _parse_csv_words(args.tlds)]
    tags = _parse_csv_words(args.portfolio_tags)

    candidates = build_domain_candidates(
        seed_phrases=args.seed,
        tlds=tlds,
        portfolio_tags=tags,
        max_labels=args.max_labels,
        check_limit=args.check_limit,
    )

    write_outputs(candidates, Path(args.csv_out), Path(args.json_out))

    top = candidates[: max(1, args.top)]
    print("fqdn,score,grade,action,availability,github_fit")
    for c in top:
        print(
            f"{c.fqdn},{c.score},{c.resale_grade},{c.action},{c.availability},{c.github_fit}"
        )

    likely_count = sum(1 for c in candidates if c.availability == "likely_available")
    print(
        f"\nScanned {len(candidates)} domain records. "
        f"Likely available: {likely_count}. "
        f"CSV: {args.csv_out} JSON: {args.json_out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
