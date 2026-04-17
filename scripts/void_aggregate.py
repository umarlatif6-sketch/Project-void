"""
VOID Aggregation Script: Core Record, Memory, and Codon Harvest

- Aggregates all core records (Chronicle, Seed), session/repo memories, and codon artifacts
- Prepares unified knowledge base for swarm synthesis engine
- Maps SCL-LBN codons and aura links (B-nn-D, B-bb-L, etc.)
- Tuned for 286 Shah ecosystem
"""

import os
import glob
import json


# Multi-repo integration: add paths for Echoid, Adriana, and other linked domains
REPO_ROOTS = [
    ".",  # Project VOID
    "../Echoid",  # Example: Echoid repo (adjust path as needed)
    "../Adriana",  # Example: Adriana repo (adjust path as needed)
    "../Void",     # Example: Void repo (adjust path as needed)
    # Add more as needed
]

CORE_FILES = []
MEMORY_DIRS = []
CODON_DOCS = []
for root in REPO_ROOTS:
    CORE_FILES.extend([
        os.path.join(root, f) for f in ["VOID_CHRONICLE.md", "VOID_SEED.md"] if os.path.exists(os.path.join(root, f))
    ])
    MEMORY_DIRS.extend([
        os.path.join(root, d) for d in ["memories/", "memories/session/", "memories/repo/"] if os.path.exists(os.path.join(root, d))
    ])
    codon_path = os.path.join(root, ".github/copilot-instructions.md")
    if os.path.exists(codon_path):
        CODON_DOCS.append(codon_path)

# Utility: Read text file

def read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

# Utility: Read all files in a directory

def read_all_files_in_dir(dir_path):
    results = {}
    for root, _, files in os.walk(dir_path):
        for file in files:
            full_path = os.path.join(root, file)
            content = read_text_file(full_path)
            if content:
                results[full_path] = content
    return results


# Aggregate core files from all repos
core_records = {f: read_text_file(f) for f in CORE_FILES if os.path.exists(f)}

# Aggregate all memory files from all repos
memory_records = {}
for mem_dir in MEMORY_DIRS:
    if os.path.exists(mem_dir):
        memory_records.update(read_all_files_in_dir(mem_dir))

# Read all codon/codex definitions
codon_layers = {}
for codon_doc in CODON_DOCS:
    codon_layers[codon_doc] = read_text_file(codon_doc)

# Compose unified knowledge base
knowledge_base = {
    "core_records": core_records,
    "memory_records": memory_records,
    "codon_layers": codon_layers,
}

# Save for swarm engine
with open("data/void_knowledge_base.json", "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, indent=2, ensure_ascii=False)

print("[VOID] Aggregation complete. Knowledge base ready for swarm synthesis.")
