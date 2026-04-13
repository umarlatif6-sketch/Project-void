#!/usr/bin/env python3
"""
Monitor the Wikipedia → Ecosystem encoding pipeline in real-time.
Tracks progress, checkpoints, and convergence metrics.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import time

def read_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return json.load(f)
    except:
        return {}

def read_output(path: Path, last_n: int = 10) -> list:
    if not path.exists():
        return []
    try:
        with path.open() as f:
            lines = [json.loads(line) for line in f if line.strip()]
            return lines[-last_n:] if last_n > 0 else lines
    except:
        return []

def monitor_ecosystem_encoding():
    print("\n" + "="*80)
    print("WIKIPEDIA → ECOSYSTEM ENCODING PIPELINE MONITOR")
    print("="*80)
    print(f"Start time: {datetime.now().isoformat()}")
    
    checkpoint_path = Path("/workspaces/Project-void/data/wikipedia_ecosystem_full.jsonl.eco.checkpoint.json")
    output_path = Path("/workspaces/Project-void/data/wikipedia_ecosystem_full.jsonl")
    
    while True:
        checkpoint = read_checkpoint(checkpoint_path)
        articles = read_output(output_path, -1)  # Read all
        
        if checkpoint:
            processed = checkpoint.get("processed", 0)
            accepted = checkpoint.get("accepted", 0)
            rejected = checkpoint.get("rejected", 0)
            acceptance_rate = checkpoint.get("acceptance_rate", 0)
            status = checkpoint.get("status", "unknown")
            
            print(f"\n📊 PROGRESS ({status}):")
            print(f"   Processed: {processed:,} articles")
            print(f"   Accepted: {accepted:,} ({acceptance_rate:.1f}%)")
            print(f"   Rejected: {rejected:,}")
            print(f"   Last article: {checkpoint.get('last_title', '?')}")
            
            if status == "complete":
                print(f"\n✓ PIPELINE COMPLETE")
                break
        else:
            print(f"   Waiting for pipeline to start...")
        
        if len(articles) > 0:
            # Sample convergence from last few articles
            names_sample = {}
            for article in articles[-20:]:
                tree = article.get("tree", {})
                name = tree.get("name")
                if name:
                    names_sample[name] = names_sample.get(name, 0) + 1
            
            if names_sample:
                print(f"\n🔗 RECENT CONVERGENCE (last 20 articles):")
                for name, count in sorted(names_sample.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"   {name}: {count} articles")
        
        print(f"\n⏱️  Next check: {datetime.now().isoformat()}")
        print("   (Ctrl+C to stop monitoring)")
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    try:
        monitor_ecosystem_encoding()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
