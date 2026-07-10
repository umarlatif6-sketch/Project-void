#!/usr/bin/env python3
"""Second batch: state-of-the-art comparison queries for Project VOID domains."""
import subprocess, json, time, re

ANSI = re.compile(r'\x1b\[[0-9;]*m')

QUERIES = {
    "Agent protocols (A2A/MCP class)": "A2A protocol agent",
    "LLM context compression": "prompt compression LLM",
    "Mesh networking (offline comms)": "meshtastic",
    "Decentralized P2P networks": "decentralized peer-to-peer network protocol",
    "Voice biometric identity": "speaker recognition identification",
    "Nail disease detection AI": "nail disease detection deep learning",
    "Materials discovery AI": "machine learning materials discovery",
    "Molecular dynamics engines": "molecular dynamics simulation engine",
    "Acoustic levitation": "acoustic levitation",
    "Sound to structure/matter": "sound vibration matter structure",
    "AI agent frameworks (mainstream)": "AI agent framework autonomous",
    "Frequency healing apps": "frequency generator healing solfeggio",
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
    time.sleep(3)

with open("/home/ubuntu/gh_domain_search_results2.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved batch 2")
