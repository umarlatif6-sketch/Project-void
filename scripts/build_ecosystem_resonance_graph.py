#!/usr/bin/env python3
"""
Resonance Graph Builder — Connect Wikipedia into the Ecosystem

Transform imported Wikipedia articles from isolated documents into a resonance web
where every article links back to the 99 Names, frequencies, and core domains.

Like Wikipedia where every link eventually leads to Philosophy, this system makes
every article eventually resonate back to the Name structure and domain roots.

Usage:
  python3 scripts/build_ecosystem_resonance_graph.py \
    --corpus data/ecosystem_feed.sample.jsonl \
    --output data/ecosystem_resonance_graph.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from void_engine.names_286 import NAMES_99, name_frequency, LAMBDA
from void_engine.knowledge_tree_store import init_knowledge_tree_tables, get_knowledge_tree_stats, search_knowledge_tree_nodes


def build_resonance_graph(corpus_path: Path, output_path: Path) -> Dict:
    """
    Build a resonance graph connecting articles via Names, frequencies, and domains.
    
    Graph structure:
    {
        "nodes": [
            {
                "id": "article:chladni_patterns",
                "type": "article",
                "title": "Chladni patterns",
                "name_index": 13,
                "name": "Al-Musawwir",
                "frequency_hz": 450.13,
                "domains": ["physics_wave", "acoustic_frequency"],
                "overall_score": 87.8,
                "glyph": "⊗",
                "codon_hex": "86eff0bf..."
            },
            {
                "id": "name:13",
                "type": "name",
                "name": "Al-Musawwir",
                "meaning": "The Fashioner of Forms",
                "index": 13,
                "frequency_hz": 475.81,
                "glyph": "◈"
            }
        ],
        "edges": [
            {
                "source": "article:chladni_patterns",
                "target": "name:13",
                "type": "reads_as",
                "strength": 0.95
            },
            {
                "source": "article:chladni_patterns",
                "target": "article:mycelium_network",
                "type": "shared_domain",
                "domains": ["acoustic_frequency"],
                "strength": 0.6
            }
        ]
    }
    """
    init_knowledge_tree_tables()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load all imported articles from corpus
    articles = []
    if corpus_path.exists():
        with corpus_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        articles.append(record)
                    except json.JSONDecodeError:
                        pass
    
    # 2. Build nodes
    nodes = []
    article_map = {}  # id → article data
    
    for article in articles:
        article_id = f"article:{article['title'].lower().replace(' ', '_')}"
        article_map[article_id] = article
        
        tree = article.get("tree", {})
        domains = [k for k, v in article.get("domain_scores", {}).items() if v > 0.1]
        
        node = {
            "id": article_id,
            "type": "article",
            "title": article["title"],
            "source": article.get("source", "unknown"),
            "name_index": tree.get("name_index"),
            "name": tree.get("name"),
            "meaning": tree.get("meaning"),
            "frequency_hz": tree.get("frequency_hz"),
            "domains": domains,
            "overall_score": tree.get("overall"),
            "head": tree.get("head"),
            "heart": tree.get("heart"),
            "gut": tree.get("gut"),
            "glyph": tree.get("codon", {}).get("glyph"),
            "codon_hex": tree.get("codon", {}).get("codon_hex"),
            "adriana_signal": tree.get("adriana_signal"),
            "ecosystem_fit": article.get("ecosystem_fit"),
        }
        nodes.append(node)
    
    # Add Name nodes
    name_map = {}  # index → name data
    for idx in range(1, 100):
        if idx <= len(NAMES_99):
            name, meaning = NAMES_99[idx - 1]
            freq = name_frequency(idx)
            name_id = f"name:{idx}"
            name_map[idx] = {
                "id": name_id,
                "type": "name",
                "name": name,
                "meaning": meaning,
                "index": idx,
                "frequency_hz": round(freq, 2),
            }
            nodes.append(name_map[idx])
    
    # 3. Build edges
    edges = []
    article_by_name = defaultdict(list)  # name_index → [articles]
    article_by_domain = defaultdict(list)  # domain → [articles]
    
    # Article → Name edges (reads_as)
    for article in articles:
        article_id = f"article:{article['title'].lower().replace(' ', '_')}"
        tree = article.get("tree", {})
        name_idx = tree.get("name_index")
        
        if name_idx and name_idx in name_map:
            article_by_name[name_idx].append(article_id)
            score = tree.get("overall", 0)
            strength = min(1.0, score / 100.0) if score else 0.5
            edges.append({
                "source": article_id,
                "target": f"name:{name_idx}",
                "type": "reads_as",
                "strength": round(strength, 2),
                "score": score,
            })
        
        # Track by domain
        for domain in tree.get("domains", []) if isinstance(tree.get("domains"), list) else []:
            domains = article.get("domain_scores", {})
            if domain in domains:
                article_by_domain[domain].append((article_id, domains[domain]))
    
    # Article → Article edges (shared_name)
    for name_idx, article_ids in article_by_name.items():
        if len(article_ids) > 1:
            for i, source in enumerate(article_ids):
                for target in article_ids[i + 1:]:
                    edges.append({
                        "source": source,
                        "target": target,
                        "type": "shared_name",
                        "name_index": name_idx,
                        "strength": 0.8,
                    })
    
    # Article → Article edges (shared_domain)
    for domain, articles_with_score in article_by_domain.items():
        article_ids = [a[0] for a in articles_with_score]
        if len(article_ids) > 1:
            for i, source in enumerate(article_ids):
                for target in article_ids[i + 1:]:
                    source_score = next((s for a, s in articles_with_score if a == source), 0.1)
                    target_score = next((s for a, s in articles_with_score if a == target), 0.1)
                    strength = (source_score + target_score) / 2 * 0.8
                    edges.append({
                        "source": source,
                        "target": target,
                        "type": "shared_domain",
                        "domain": domain,
                        "strength": round(min(1.0, strength), 2),
                    })
    
    # 4. Build domain summary nodes and edges
    for domain in article_by_domain.keys():
        domain_id = f"domain:{domain}"
        articles_with_scores = article_by_domain[domain]
        avg_score = sum(s for _, s in articles_with_scores) / len(articles_with_scores)
        
        nodes.append({
            "id": domain_id,
            "type": "domain",
            "domain": domain,
            "article_count": len(articles_with_scores),
            "avg_resonance": round(avg_score, 2),
        })
        
        # Connect articles to their domain node
        for article_id, score in articles_with_scores:
            edges.append({
                "source": article_id,
                "target": domain_id,
                "type": "resonates_with_domain",
                "strength": round(min(1.0, score), 2),
            })
    
    # 5. Build frequency clusters
    freq_clusters = defaultdict(list)
    for node in nodes:
        if node["type"] == "article" and node.get("frequency_hz"):
            # Cluster by 50 Hz bands
            cluster_key = int(node["frequency_hz"] / 50) * 50
            freq_clusters[cluster_key].append(node["id"])
    
    for cluster_freq, article_ids in freq_clusters.items():
        if len(article_ids) > 1:
            for i, source in enumerate(article_ids):
                for target in article_ids[i + 1:]:
                    edges.append({
                        "source": source,
                        "target": target,
                        "type": "nearby_frequency",
                        "frequency_band_hz": cluster_freq,
                        "strength": 0.5,
                    })
    
    # 6. Serialize
    graph = {
        "version": "1.0",
        "buildtime": "2026-04-13",
        "metadata": {
            "total_articles": len(articles),
            "total_names": len(NAMES_99),
            "total_domains": len(article_by_domain),
            "total_edges": len(edges),
        },
        "nodes": nodes,
        "edges": edges,
    }
    
    output_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return {
        "output": str(output_path),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "articles": len(articles),
        "edge_types": list(set(e.get("type") for e in edges)),
    }


def main():
    parser = argparse.ArgumentParser(description="Build resonance graph from imported ecosystem articles.")
    parser.add_argument("--corpus", required=True, help="Path to imported ecosystem JSONL")
    parser.add_argument("--output", required=True, help="Path to output resonance graph JSON")
    args = parser.parse_args()
    
    result = build_resonance_graph(Path(args.corpus), Path(args.output))
    
    print("\nRESSONANCE GRAPH BUILD COMPLETE")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
