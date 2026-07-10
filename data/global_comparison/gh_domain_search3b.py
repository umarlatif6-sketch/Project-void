#!/usr/bin/env python3
"""Batch 3b: retry zero-result domains with simpler queries."""
import subprocess, json, time, re

ANSI = re.compile(r'\x1b\[[0-9;]*m')

QUERIES = {
    "Nail image analysis AI": "nail disease",
    "Nail detection": "nail detection",
    "Palmistry AI": "palmistry",
    "Traditional medicine AI (TCM)": "TCM diagnosis",
    "Ayurveda AI": "ayurveda",
    "HRV biometrics": "heart rate variability",
    "432Hz / solfeggio tools": "solfeggio",
    "432Hz tools": "432hz",
    "AI memory persistence": "LLM long-term memory",
    "Vibration health sensing": "vibration analysis fault detection",
}

results = {}
for label, q in QUERIES.items():
    try:
        cmd = f'gh search repos "{q}" --limit 8 --sort stars --json fullName,description,stargazersCount'
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
            results[label] = []
            print(f"\n=== {label} === NO RESULTS: {out.stderr[:120]}")
    except Exception as e:
        results[label] = {"error": str(e)}
        print(f"\n=== {label} === EXCEPTION: {e}")
    time.sleep(3)

with open("/home/ubuntu/gh_domain_search_results3b.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved batch 3b")
