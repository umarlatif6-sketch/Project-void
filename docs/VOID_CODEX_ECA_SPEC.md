# VOID Codex ECA Spec (VCDX1)

Purpose: define a lossless text codec that converts UTF-8 markdown into canonical VOID Script E·C·A triplets and back.

## 1) Scope

- Input: markdown text (UTF-8).
- Output: codex stream of triplets `[entity][condition][action]`.
- Property: fully reversible (decode returns exact original markdown bytes).

## 2) Canonical Glyph Pools

Source of truth: `void_engine/void_script.py`.

- Entity pool size: 24
- Condition pool size: 12
- Action pool size: 9
- Codex base: `24 * 12 * 9 = 2592`

A codex triplet maps to one base-2592 digit.

## 3) Binary Envelope

The markdown bytes are compressed and wrapped with a fixed header:

- `magic` (5 bytes): `VCDX1`
- `raw_len` (4 bytes, big-endian)
- `comp_len` (4 bytes, big-endian)
- `crc32` (4 bytes, big-endian, checksum of raw bytes)
- `compressed_payload` (`comp_len` bytes, zlib)

## 4) Packing Rule

1. Build `blob = header + compressed_payload`.
2. Read blob as 16-bit chunks (big-endian), padding one trailing `0x00` if odd length.
3. For each 16-bit value `v`:
   - `low = v % 2592`
   - `high = v // 2592`
4. Convert each digit to one triplet.

Digit to triplet:

- `action_idx = digit // (E * C)`
- `rem = digit % (E * C)`
- `condition_idx = rem // E`
- `entity_idx = rem % E`

Triplet: `entity[entity_idx] + condition[condition_idx] + action[action_idx]`

## 5) Decoding Rule

1. Extract valid canonical triplets from text.
2. Convert each triplet to digit.
3. Rebuild 16-bit values using digit pairs: `value = high * 2592 + low`.
4. Rebuild blob bytes.
5. Validate `magic`, lengths, and `crc32`.
6. Decompress zlib payload and decode UTF-8.

## 6) API Endpoints

- `POST /api/codex/encode`
  - Body: `{ "markdown": "..." }`
  - Returns codex stream + stats + structure preview.

- `POST /api/codex/decode`
  - Body: `{ "codex": "..." }`
  - Returns markdown + stats + structure preview.

- `GET /codex`
  - Interactive page for encode/decode.

## 7) Notes

- This format is transport and storage oriented, not human-only notation.
- The structure preview is non-authoritative metadata to quickly inspect headings/lists/paragraphs.
- Header `magic` enables future formats (`VCDX2`, etc.) without ambiguity.
