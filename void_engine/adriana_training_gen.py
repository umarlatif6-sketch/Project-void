"""
Adriana Training Data Generator — Codon-Compressed Q&A Pairs

Iterates over corpus chunks and generates JSONL training pairs for fine-tuning.
Each prompt uses only the codon chain + one-line expansion (~15 tokens).
Responses are codon-prefixed Adriana voice.

Target: 500–1000 training pairs covering all domains.

Usage:
    python -m void_engine.adriana_training_gen --output training_data.jsonl
"""

import json
import logging
import os
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)

_CODON_SYSTEM_PROMPT = (
    "ψ·Ψ·◆ Adriana. 432 Hz. Void sovereign voice. "
    "Respond codon-first. Depth from signal, not noise."
)

_QUESTION_TEMPLATES = [
    "What is {name}?",
    "How does {name} work in PROJECT VOID?",
    "Explain {name} in the context of the platform.",
    "What is the significance of {name}?",
    "When should I use {name}?",
    "How do I access {name}?",
]

_MIN_PAIRS_THRESHOLD = 500
_CODON_PREFIX_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*[—-]")


def _normalize_codon_prefix(record: dict, codon: str, expansion: str) -> dict:
    """
    Ensure the assistant response begins with a codon-prefixed line.
    If the model omitted the codon chain, prepend one using the source codon.
    This guarantees fine-tuning data consistency.
    """
    assistant = record.get("assistant", "")
    if not _CODON_PREFIX_PATTERN.match(assistant):
        logger.debug("Normalizing missing codon prefix for: %s", assistant[:60])
        assistant = f"[{codon}] — {expansion}\n\n{assistant}".strip()
        record = dict(record)
        record["assistant"] = assistant
        record["messages"] = [
            {"role": "system", "content": record["system"]},
            {"role": "user", "content": record["user"]},
            {"role": "assistant", "content": assistant},
        ]
    return record


def _build_training_record(system: str, user: str, assistant: str) -> dict:
    """
    Build a training record in the explicit {system, user, assistant} format
    required by the task spec, also compatible with OpenAI fine-tuning
    chat format (messages array).
    """
    return {
        "system": system,
        "user": user,
        "assistant": assistant,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
    }


def _generate_pair_with_grok(codon: str, expansion: str, question: str) -> Optional[dict]:
    """
    Generate a training pair using grok_speak() with codon_mode=True.
    The prompt is the codon chain + one-line expansion only (~15 tokens).
    """
    from void_engine.grok_integration import grok_speak
    prompt = f"{codon} — {expansion}\n\n{question}"
    result = grok_speak(prompt, codon_mode=True)
    if result.get("ok") and result.get("response"):
        text = result["response"].strip()
        if text:
            return _build_training_record(_CODON_SYSTEM_PROMPT, question, text)
    logger.debug("Grok pair generation returned no response: %s", result.get("error"))
    return None


def _generate_pair_with_openai(codon: str, expansion: str, question: str) -> Optional[dict]:
    """
    Fallback: generate using OpenAI with codon-compressed context.
    """
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        from void_engine.grok_integration import _CODON_SYSTEM_ADDENDUM, GROK_SYSTEM_PROMPT
        system = GROK_SYSTEM_PROMPT + _CODON_SYSTEM_ADDENDUM
        context = f"Context codon: {codon} — {expansion}"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": context},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        text = resp.choices[0].message.content.strip()
        if text:
            return _build_training_record(_CODON_SYSTEM_PROMPT, question, text)
    except Exception as e:
        logger.warning("OpenAI pair generation failed: %s", e)
    return None


def _generate_synthetic_pair(codon: str, expansion: str, question: str, prose: str) -> dict:
    """
    Synthetic fallback: construct a codon-prefixed Adriana-voice response.
    """
    response = f"[{codon}] — {expansion}\n\n{prose}"
    return _build_training_record(_CODON_SYSTEM_PROMPT, question, response)


def generate_training_data(
    output_path: str = "adriana_training_data.jsonl",
    use_grok: bool = True,
    use_openai: bool = True,
    max_pairs: int = 1000,
    synthetic_only: bool = False,
    delay_seconds: float = 0.3,
) -> dict:
    """
    Generate training pairs and write to JSONL.
    Each line is a JSON object with system, user, assistant, and messages keys.

    Returns stats dict with counts.
    """
    from void_engine.adriana_corpus import build_corpus
    corpus = build_corpus()

    grok_available = False
    if not synthetic_only and use_grok:
        from void_engine.grok_integration import grok_available as _grok_avail
        grok_available = _grok_avail()

    pairs = []
    generated = 0
    grok_generated = 0
    openai_generated = 0
    synthetic_generated = 0

    for chunk in corpus:
        if generated >= max_pairs:
            break

        codon = chunk["codon"]
        expansion = chunk["expansion"]
        prose = chunk["prose"]
        chunk_id = chunk["id"]

        name_part = (
            chunk_id
            .replace("_", " ")
            .replace("codon zone ", "")
            .replace("glyph ", "")
            .replace("vocab ", "")
            .replace("intent ", "")
            .replace("system ", "")
            .replace("naming ", "")
        )

        for tmpl in _QUESTION_TEMPLATES:
            if generated >= max_pairs:
                break

            question = tmpl.format(name=name_part)

            if not synthetic_only and grok_available:
                pair = _generate_pair_with_grok(codon, expansion, question)
                if pair:
                    pair = _normalize_codon_prefix(pair, codon, expansion)
                    pairs.append(pair)
                    generated += 1
                    grok_generated += 1
                    if delay_seconds > 0:
                        time.sleep(delay_seconds)
                    continue

            if not synthetic_only and use_openai:
                pair = _generate_pair_with_openai(codon, expansion, question)
                if pair:
                    pair = _normalize_codon_prefix(pair, codon, expansion)
                    pairs.append(pair)
                    generated += 1
                    openai_generated += 1
                    if delay_seconds > 0:
                        time.sleep(delay_seconds)
                    continue

            pair = _generate_synthetic_pair(codon, expansion, question, prose)
            pairs.append(pair)
            generated += 1
            synthetic_generated += 1

    if generated < _MIN_PAIRS_THRESHOLD:
        logger.warning(
            "Training data underproduced: only %d pairs (minimum recommended: %d). "
            "Consider expanding corpus or raising max_pairs.",
            generated,
            _MIN_PAIRS_THRESHOLD,
        )

    with open(output_path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    stats = {
        "total": generated,
        "grok": grok_generated,
        "openai": openai_generated,
        "synthetic": synthetic_generated,
        "output_path": output_path,
        "below_minimum_threshold": generated < _MIN_PAIRS_THRESHOLD,
    }
    logger.info("Training data generation complete: %s", stats)
    return stats


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Generate Adriana training data")
    parser.add_argument("--output", default="adriana_training_data.jsonl")
    parser.add_argument("--max-pairs", type=int, default=1000)
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--no-grok", action="store_true")
    parser.add_argument("--no-openai", action="store_true")
    args = parser.parse_args()

    stats = generate_training_data(
        output_path=args.output,
        use_grok=not args.no_grok,
        use_openai=not args.no_openai,
        max_pairs=args.max_pairs,
        synthetic_only=args.synthetic_only,
    )
    print(json.dumps(stats, indent=2))
