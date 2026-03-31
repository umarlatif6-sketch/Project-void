#!/usr/bin/env python3
"""
Auto-update replit.md after every merge.
Uses git diff to find changed files, reads them, and asks OpenAI to summarise
what was added. Appends/updates relevant sections in replit.md without
removing existing content.

Skips silently if the OpenAI API key is unavailable so it never blocks a merge.
"""

import os
import subprocess

SEED_FILE = "replit.md"
PROMPT_SEED_CHARS = 6000
CHANGED_FILE_CHARS = 4000
MAX_CHANGED_FILES = 12


def get_changed_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        return []


def read_file_safe(path: str, max_chars: int = CHANGED_FILE_CHARS) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read(max_chars)
            if len(content) == max_chars:
                content += "\n...[truncated]"
            return content
    except OSError:
        return ""


def read_seed_full() -> str:
    try:
        with open(SEED_FILE, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def is_relevant(path: str) -> bool:
    relevant_dirs = ("void_engine", "routes", "templates", "scripts")
    relevant_exts = (".py", ".html", ".sh", ".js")
    if any(path.startswith(d) for d in relevant_dirs):
        return True
    _, ext = os.path.splitext(path)
    return ext in relevant_exts


def build_prompt(changed_files: list[str], file_contents: dict[str, str], seed_excerpt: str) -> str:
    files_parts = []
    total = 0
    for path, content in file_contents.items():
        part = f"=== {path} ===\n{content}\n"
        if total + len(part) > 8000:
            break
        files_parts.append(part)
        total += len(part)

    return (
        "You are a technical writer maintaining a project seed file called replit.md.\n"
        "Below is an excerpt of the current seed file, followed by files that just merged.\n\n"
        "Your job is to produce a SHORT, CONCISE patch — only new additions or changes.\n"
        "Rules:\n"
        "- Write in the same technical, clear style as the existing seed.\n"
        "- Do NOT rewrite or remove existing content.\n"
        "- Focus on: new routes, new modules, new templates, new external dependencies, new user preferences.\n"
        "- Output only the patch text that should be appended to the relevant sections.\n"
        "  Format each patch as:\n"
        "    SECTION: <section name from seed>\n"
        "    PATCH:\n"
        "    <bullet points to append>\n"
        "- If nothing significant changed (e.g. only minor fixes), output: NO_UPDATE\n"
        "- Limit response to 300 words.\n\n"
        f"--- CURRENT replit.md (excerpt) ---\n{seed_excerpt}\n\n"
        f"--- CHANGED FILES ---\n{''.join(files_parts)}"
    )


def call_openai(prompt: str) -> str:
    api_key = (
        os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    if not api_key:
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def apply_patch(seed_full: str, patch_text: str) -> str:
    if not patch_text or patch_text.strip() == "NO_UPDATE":
        return seed_full

    lines = patch_text.strip().splitlines()
    current_section: str | None = None
    patch_lines: list[str] = []
    section_patches: list[tuple[str, str]] = []

    for line in lines:
        if line.startswith("SECTION:"):
            if current_section is not None and patch_lines:
                section_patches.append((current_section, "\n".join(patch_lines).strip()))
            current_section = line[len("SECTION:"):].strip()
            patch_lines = []
        elif line.startswith("PATCH:"):
            patch_lines = []
        else:
            if current_section is not None:
                patch_lines.append(line)

    if current_section is not None and patch_lines:
        section_patches.append((current_section, "\n".join(patch_lines).strip()))

    if not section_patches:
        return seed_full.rstrip() + f"\n\n{patch_text}\n"

    updated = seed_full
    for section_name, bullets in section_patches:
        if not bullets:
            continue
        idx = updated.find(f"## {section_name}")
        if idx == -1:
            updated = updated.rstrip() + f"\n\n## {section_name}\n{bullets}\n"
        else:
            next_section = updated.find("\n## ", idx + 4)
            if next_section == -1:
                updated = updated.rstrip() + f"\n{bullets}\n"
            else:
                updated = updated[:next_section] + f"\n{bullets}" + updated[next_section:]

    return updated


def main() -> None:
    changed_files = get_changed_files()
    if not changed_files:
        return

    relevant_files = [f for f in changed_files if is_relevant(f)]
    if not relevant_files:
        return

    file_contents: dict[str, str] = {}
    for path in relevant_files[:MAX_CHANGED_FILES]:
        content = read_file_safe(path)
        if content:
            file_contents[path] = content

    seed_full = read_seed_full()
    if not seed_full:
        return

    seed_excerpt = seed_full[:PROMPT_SEED_CHARS]
    if len(seed_full) > PROMPT_SEED_CHARS:
        seed_excerpt += "\n...[truncated for prompt]"

    prompt = build_prompt(relevant_files, file_contents, seed_excerpt)
    patch_text = call_openai(prompt)

    if not patch_text or patch_text.strip() == "NO_UPDATE":
        return

    updated_seed = apply_patch(seed_full, patch_text)

    with open(SEED_FILE, "w", encoding="utf-8") as fh:
        fh.write(updated_seed)


if __name__ == "__main__":
    main()
