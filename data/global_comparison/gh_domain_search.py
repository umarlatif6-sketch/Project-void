#!/usr/bin/env python3
"""Search GitHub across Project VOID's domains and save results."""
import subprocess, json, time, sys, re

ANSI = re.compile(r'\x1b\[[0-9;]*m')

QUERIES = {
    "AI-to-AI communication protocol": "agent communication protocol AI",
    "Token-efficient agent language": "symbolic compression LLM",
    "Sovereign mesh network": "mesh network offline communication",
    "Audio steganography": "audio steganography",
    "Frequency biometrics": "acoustic biometric identification",
    "Nail health AI": "fingernail analysis health",
    "AI agent memory persistence": "agent memory persistence context",
    "Molecular dynamics frequency": "molecular dynamics vibration resonance",
    "Chladni cymatics": "chladni pattern",
    "Semantic compression codon": "semantic compression glyph",
}

results = {}
for label, q in QUERIES.items():
    try:
        cmd = f'gh search repos "{q}" --limit 8 --sort stars --json fullName,description,stargazersCount,updatedAt'
        out = subprocess.run(cmd, shell=True, executable="/bin/bash",
            capture_output=True, text=True, timeout=30)
        clean = ANSI.sub('', out.stdout).strip()
        if out.returncode == 0 and clean:
            repos = json.loads(clean)
            results[label] = repos
            print(f"\n=== {label} ({q}) ===")
            for r in repos:
                desc = (r.get("description") or "")[:90]
                print(f"{r['stargazersCount']:>7}* {r['fullName']}: {desc}")
        else:
            results[label] = {"error": out.stderr[:200]}
            print(f"\n=== {label} === ERROR: {out.stderr[:150]}")
    except Exception as e:
        results[label] = {"error": str(e)}
        print(f"\n=== {label} === EXCEPTION: {e}")
    time.sleep(3)  # avoid rate limits

with open("/home/ubuntu/gh_domain_search_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to /home/ubuntu/gh_domain_search_results.json")
