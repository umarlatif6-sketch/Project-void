#!/usr/bin/env python3
"""Third batch: biometric frequency analysis / nail reading / traditional medicine AI."""
import subprocess, json, time, re

ANSI = re.compile(r'\x1b\[[0-9;]*m')

QUERIES = {
    "Nail image analysis / onychology AI": "nail segmentation classification",
    "Nail health detection": "fingernail detection",
    "Palmistry / hand reading AI": "palmistry palm reading",
    "Traditional medicine AI (TCM)": "traditional chinese medicine diagnosis AI",
    "Unani / Ayurveda AI": "ayurveda diagnosis machine learning",
    "Biofield / bioresonance": "bioresonance biofield",
    "Heart rate variability biometrics": "HRV analysis biometric",
    "Cymatics software": "cymatics",
    "Solfeggio / 432Hz tools": "432hz solfeggio",
    "Iridology AI": "iridology",
    "Vibration-based health sensing": "vibration health monitoring machine learning",
    "AI session continuity / memory bootstrap": "LLM session memory persistence bootstrap",
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
            results[label] = []
            print(f"\n=== {label} === NO RESULTS or ERROR: {out.stderr[:120]}")
    except Exception as e:
        results[label] = {"error": str(e)}
        print(f"\n=== {label} === EXCEPTION: {e}")
    time.sleep(3)

with open("/home/ubuntu/gh_domain_search_results3.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved batch 3")
