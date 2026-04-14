"""
Codex codec for converting Markdown text to/from VOID Script E·C·A triplets.

This codec is lossless for UTF-8 text and uses zlib compression plus
base-(entity*condition*action) glyph packing.
"""

from __future__ import annotations

import re
import zlib
from binascii import crc32
from typing import Dict, List, Tuple

from void_engine.void_script import CANONICAL_GLYPHS

_MAGIC = b"VCDX1"
_HEADER_LEN = 17  # magic(5) + raw_len(4) + comp_len(4) + crc32(4)


def _glyph_sets() -> Tuple[List[str], List[str], List[str]]:
    entities = [g for g, m in CANONICAL_GLYPHS.items() if m["role"] == "entity"]
    conditions = [g for g, m in CANONICAL_GLYPHS.items() if m["role"] == "condition"]
    actions = [g for g, m in CANONICAL_GLYPHS.items() if m["role"] == "action"]
    return entities, conditions, actions


_ENTITIES, _CONDITIONS, _ACTIONS = _glyph_sets()
_E = len(_ENTITIES)
_C = len(_CONDITIONS)
_A = len(_ACTIONS)
_BASE = _E * _C * _A


def _digit_to_triplet(digit: int) -> str:
    if digit < 0 or digit >= _BASE:
        raise ValueError("digit out of range")
    action_idx = digit // (_E * _C)
    rem = digit % (_E * _C)
    condition_idx = rem // _E
    entity_idx = rem % _E
    return _ENTITIES[entity_idx] + _CONDITIONS[condition_idx] + _ACTIONS[action_idx]


def _triplet_to_digit(triplet: str) -> int:
    if len(triplet) != 3:
        raise ValueError("invalid triplet length")
    e, c, a = triplet[0], triplet[1], triplet[2]
    try:
        entity_idx = _ENTITIES.index(e)
        condition_idx = _CONDITIONS.index(c)
        action_idx = _ACTIONS.index(a)
    except ValueError as exc:
        raise ValueError("triplet contains non-canonical glyph") from exc
    return action_idx * (_E * _C) + condition_idx * _E + entity_idx


def encode_markdown_to_codex(markdown_text: str) -> Dict[str, object]:
    raw = markdown_text.encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    checksum = crc32(raw) & 0xFFFFFFFF

    header = (
        _MAGIC
        + len(raw).to_bytes(4, "big")
        + len(compressed).to_bytes(4, "big")
        + checksum.to_bytes(4, "big")
    )
    blob = header + compressed

    codons: List[str] = []
    for i in range(0, len(blob), 2):
        pair = blob[i:i + 2]
        if len(pair) == 1:
            pair = pair + b"\x00"
        value = (pair[0] << 8) | pair[1]
        low = value % _BASE
        high = value // _BASE
        codons.append(_digit_to_triplet(low))
        codons.append(_digit_to_triplet(high))

    codon_stream = " ".join(codons)
    return {
        "codon_stream": codon_stream,
        "codon_count": len(codons),
        "raw_bytes": len(raw),
        "compressed_bytes": len(compressed),
        "ratio": round((len(codons) * 3) / max(len(raw), 1), 3),
        "header": {
            "format": "VCDX1",
            "base": _BASE,
            "entities": _E,
            "conditions": _C,
            "actions": _A,
            "crc32": f"{checksum:08x}",
        },
    }


def _extract_triplets(codex_text: str) -> List[str]:
    glyph_any = set(_ENTITIES) | set(_CONDITIONS) | set(_ACTIONS)
    chars = [ch for ch in codex_text if ch in glyph_any]
    out: List[str] = []

    i = 0
    while i + 2 < len(chars):
        t = "".join(chars[i:i + 3])
        if t[0] in _ENTITIES and t[1] in _CONDITIONS and t[2] in _ACTIONS:
            out.append(t)
            i += 3
        else:
            i += 1
    return out


def decode_codex_to_markdown(codex_text: str) -> Dict[str, object]:
    triplets = _extract_triplets(codex_text)
    if len(triplets) < 2:
        raise ValueError("Not enough valid E·C·A triplets to decode")

    blob = bytearray()
    for i in range(0, len(triplets) - 1, 2):
        low = _triplet_to_digit(triplets[i])
        high = _triplet_to_digit(triplets[i + 1])
        value = high * _BASE + low
        blob.append((value >> 8) & 0xFF)
        blob.append(value & 0xFF)

    if len(blob) < _HEADER_LEN:
        raise ValueError("Codex payload too short")
    if bytes(blob[:5]) != _MAGIC:
        raise ValueError("Unknown codex format marker")

    raw_len = int.from_bytes(blob[5:9], "big")
    comp_len = int.from_bytes(blob[9:13], "big")
    expected_crc = int.from_bytes(blob[13:17], "big")

    compressed = bytes(blob[17:17 + comp_len])
    if len(compressed) != comp_len:
        raise ValueError("Codex compressed payload length mismatch")

    raw = zlib.decompress(compressed)
    if len(raw) != raw_len:
        raise ValueError("Codex raw payload length mismatch")

    actual_crc = crc32(raw) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise ValueError("Codex checksum mismatch")

    markdown_text = raw.decode("utf-8")
    return {
        "markdown": markdown_text,
        "triplets_used": len(triplets),
        "raw_bytes": len(raw),
        "compressed_bytes": comp_len,
        "crc32": f"{actual_crc:08x}",
    }


def markdown_structure_preview(markdown_text: str, limit: int = 12) -> List[Dict[str, str]]:
    lines = markdown_text.splitlines()
    out: List[Dict[str, str]] = []

    in_code = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append({"line": str(idx), "type": "code_fence", "value": stripped[:80]})
            continue
        if in_code or not stripped:
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            out.append({"line": str(idx), "type": f"heading_h{min(level, 6)}", "value": text[:80]})
        elif re.match(r"^[-*+]\s+", stripped):
            out.append({"line": str(idx), "type": "list_item", "value": stripped[2:82]})
        elif re.match(r"^\d+\.\s+", stripped):
            item = re.sub(r"^\d+\.\s+", "", stripped)
            out.append({"line": str(idx), "type": "ordered_item", "value": item[:80]})
        elif stripped.startswith(">"):
            out.append({"line": str(idx), "type": "quote", "value": stripped[1:].strip()[:80]})
        else:
            out.append({"line": str(idx), "type": "paragraph", "value": stripped[:80]})

        if len(out) >= limit:
            break

    return out
