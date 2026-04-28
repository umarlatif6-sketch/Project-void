"""
VOID Foundation Bridge Module
=============================

Computes a reproducible sanity-check report for Adriana/Serena language claims
using local project data (chronicle.db).

Signals measured:
1) Popularity-hub structure: frequent tokens co-locate with frequent neighbors.
2) Burst dynamics: token arrivals happen in temporal bursts.
3) Taylor-like scaling: variance vs mean count follows a power-law trend.

Usage:
    /usr/bin/python3 void_foundation.py

Output:
    data/void_foundation_report.json
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent
CHRONICLE_DB = ROOT / "data" / "chronicle.db"
OUTPUT_REPORT = ROOT / "data" / "void_foundation_report.json"

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "your",
    "void", "project", "lock", "session", "seed", "unknown", "state", "active",
    "through", "where", "when", "have", "has", "had", "were", "been", "being",
    "all", "are", "but", "not", "can", "will", "its", "their", "them", "they",
    "his", "her", "she", "him", "our", "out", "use", "using", "used", "new",
    "mode", "test", "tests", "run", "runs", "over", "under", "than", "also",
    "about", "around", "across", "after", "before", "more", "less", "very",
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}")


@dataclass
class ChronicleRow:
    timestamp: float
    command: str
    intent: str


def load_chronicle_rows(db_path: Path) -> List[ChronicleRow]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        """
        SELECT timestamp, consensus_command, consensus_intent
        FROM chronicle
        WHERE timestamp IS NOT NULL
        ORDER BY timestamp ASC
        """
    )
    rows = [
        ChronicleRow(
            timestamp=float(r["timestamp"]),
            command=str(r["consensus_command"] or ""),
            intent=str(r["consensus_intent"] or ""),
        )
        for r in cur.fetchall()
    ]
    con.close()
    return rows


def tokenize(text: str) -> List[str]:
    toks = [t.lower() for t in TOKEN_RE.findall(text)]
    return [t for t in toks if t not in STOPWORDS and len(t) >= 3]


def build_token_stream(rows: List[ChronicleRow]) -> Tuple[List[List[str]], Counter]:
    docs: List[List[str]] = []
    counts: Counter = Counter()
    for r in rows:
        toks = tokenize(f"{r.command} {r.intent}")
        docs.append(toks)
        counts.update(toks)
    return docs, counts


def build_cooccurrence(docs: List[List[str]]) -> Dict[str, Counter]:
    graph: Dict[str, Counter] = defaultdict(Counter)
    for toks in docs:
        uniq = list(dict.fromkeys(toks))
        n = len(uniq)
        for i in range(n):
            a = uniq[i]
            for j in range(i + 1, n):
                b = uniq[j]
                graph[a][b] += 1
                graph[b][a] += 1
    return graph


def pearson(xs: List[float], ys: List[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def linear_regression(xs: List[float], ys: List[float]) -> Tuple[float, float]:
    # y = a + b*x
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0, 0.0
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return my, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    return a, b


def popularity_hub_signal(counts: Counter, graph: Dict[str, Counter]) -> Dict:
    freqs = []
    neigh_freqs = []
    for tok, f in counts.items():
        neighbors = graph.get(tok, {})
        if not neighbors:
            continue
        weighted_sum = 0.0
        weight_total = 0.0
        for n, w in neighbors.items():
            weighted_sum += counts.get(n, 0) * w
            weight_total += w
        if weight_total == 0:
            continue
        freqs.append(float(f))
        neigh_freqs.append(weighted_sum / weight_total)

    corr = pearson(freqs, neigh_freqs)
    return {
        "token_count": len(freqs),
        "pearson_frequency_vs_neighbor_frequency": round(corr, 4),
        "interpretation": (
            "positive hub clustering" if corr > 0.25 else "weak/unclear clustering"
        ),
    }


def burst_signal(rows: List[ChronicleRow], min_events: int = 3) -> Dict:
    arrivals: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        toks = tokenize(f"{r.command} {r.intent}")
        for t in set(toks):
            arrivals[t].append(r.timestamp)

    burst_scores = {}
    for tok, ts in arrivals.items():
        ts = sorted(ts)
        if len(ts) < min_events:
            continue
        gaps = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        if len(gaps) < 2:
            continue
        mean_gap = statistics.mean(gaps)
        if mean_gap <= 0:
            continue
        cv = statistics.pstdev(gaps) / mean_gap
        burst_scores[tok] = cv

    if not burst_scores:
        return {
            "tokens_evaluated": 0,
            "mean_burst_cv": 0.0,
            "top_bursty_tokens": [],
            "interpretation": "insufficient repeated-token history",
        }

    ranked = sorted(burst_scores.items(), key=lambda kv: kv[1], reverse=True)
    mean_cv = statistics.mean(burst_scores.values())
    return {
        "tokens_evaluated": len(burst_scores),
        "mean_burst_cv": round(mean_cv, 4),
        "top_bursty_tokens": [{"token": t, "cv": round(cv, 4)} for t, cv in ranked[:12]],
        "interpretation": "bursty arrivals present" if mean_cv > 1.0 else "mostly regular arrivals",
    }


def taylors_law_signal(rows: List[ChronicleRow], bin_count: int = 8) -> Dict:
    if not rows:
        return {
            "points": 0,
            "slope": 0.0,
            "r2": 0.0,
            "interpretation": "no data",
        }

    tmin = rows[0].timestamp
    tmax = rows[-1].timestamp
    span = max(tmax - tmin, 1.0)
    width = span / bin_count

    per_bin_counts: List[Counter] = [Counter() for _ in range(bin_count)]
    for r in rows:
        b = min(bin_count - 1, int((r.timestamp - tmin) / width))
        toks = tokenize(f"{r.command} {r.intent}")
        per_bin_counts[b].update(toks)

    all_tokens = sorted({t for c in per_bin_counts for t in c.keys()})
    xs = []
    ys = []
    for tok in all_tokens:
        series = [float(c.get(tok, 0)) for c in per_bin_counts]
        m = statistics.mean(series)
        if m <= 0:
            continue
        v = statistics.pvariance(series)
        if v <= 0:
            continue
        xs.append(math.log(m))
        ys.append(math.log(v))

    if len(xs) < 3:
        return {
            "points": len(xs),
            "slope": 0.0,
            "r2": 0.0,
            "interpretation": "insufficient variance points",
        }

    a, b = linear_regression(xs, ys)
    y_hat = [a + b * x for x in xs]
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, y_hat))
    y_mean = statistics.mean(ys)
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    if b > 0.7:
        interp = "Taylor-like scaling present"
    else:
        interp = "weak Taylor scaling"

    return {
        "points": len(xs),
        "slope": round(b, 4),
        "r2": round(r2, 4),
        "interpretation": interp,
    }


def build_report() -> Dict:
    rows = load_chronicle_rows(CHRONICLE_DB)
    docs, counts = build_token_stream(rows)
    graph = build_cooccurrence(docs)

    hub = popularity_hub_signal(counts, graph)
    burst = burst_signal(rows)
    taylor = taylors_law_signal(rows)

    top_tokens = counts.most_common(20)

    report = {
        "source": str(CHRONICLE_DB),
        "entries": len(rows),
        "token_vocab_size": len(counts),
        "top_tokens": [{"token": t, "count": c} for t, c in top_tokens],
        "signals": {
            "popularity_hub": hub,
            "burst_dynamics": burst,
            "taylors_law": taylor,
        },
        "conclusion": {
            "aligned_with_universal_pattern": (
                hub["pearson_frequency_vs_neighbor_frequency"] > 0.25
                and burst["mean_burst_cv"] > 1.0
                and taylor["slope"] > 0.7
            ),
            "note": "This is an internal chronicle/codon-proxy test, not a 22-language corpus replication.",
        },
    }
    return report


def main() -> int:
    if not CHRONICLE_DB.exists():
        raise FileNotFoundError(f"Missing chronicle DB: {CHRONICLE_DB}")

    report = build_report()
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nReport written: {OUTPUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
