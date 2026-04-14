#!/usr/bin/env python3
"""Generate and rotate Packet Ed25519 keys for Project VOID.

Usage:
  python3 scripts/packet_key_manager.py generate --key-id k1
  python3 scripts/packet_key_manager.py rotate --key-id k2 --existing-keyset '{"k1":"<pubhex>"}'
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Dict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@dataclass
class KeyBundle:
    key_id: str
    private_hex: str
    public_hex: str


def generate_key_bundle(key_id: str) -> KeyBundle:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return KeyBundle(
        key_id=key_id,
        private_hex=private_key.private_bytes_raw().hex(),
        public_hex=public_key.public_bytes_raw().hex(),
    )


def parse_existing_keyset(raw: str) -> Dict[str, str]:
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise ValueError("--existing-keyset must be valid JSON object") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--existing-keyset must be a JSON object")
    out: Dict[str, str] = {}
    for k, v in parsed.items():
        key_id = str(k or "").strip()
        pub = str(v or "").strip()
        if key_id and pub:
            out[key_id] = pub
    return out


def print_env_block(bundle: KeyBundle, keyset: Dict[str, str]) -> None:
    print("# Packet security env block")
    print("VOID_PACKET_SECURITY_ENFORCE=true")
    print(f"VOID_PACKET_SIGNING_KEY_ID={bundle.key_id}")
    print(f"VOID_PACKET_SIGNING_PRIVATE_KEY={bundle.private_hex}")
    print(f"VOID_PACKET_VERIFY_KEYS_JSON={json.dumps(keyset, separators=(',', ':'))}")
    print("VOID_PACKET_REQUIRE_SECTOR_POLICY=true")
    print("VOID_PACKET_MAX_AGE_SECONDS=86400")


def cmd_generate(args: argparse.Namespace) -> int:
    bundle = generate_key_bundle(args.key_id)
    keyset = {bundle.key_id: bundle.public_hex}

    print("Generated new Ed25519 packet signing key")
    print_env_block(bundle, keyset)
    return 0


def cmd_rotate(args: argparse.Namespace) -> int:
    existing = parse_existing_keyset(args.existing_keyset)
    bundle = generate_key_bundle(args.key_id)

    existing[bundle.key_id] = bundle.public_hex

    print("Generated rotated Ed25519 packet signing key")
    print("Old keys retained in verify keyset for compatibility.")
    print_env_block(bundle, existing)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Packet key generation and rotation helper")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate initial key pair and keyset")
    gen.add_argument("--key-id", default="k1", help="Key id for signing key")
    gen.set_defaults(func=cmd_generate)

    rot = sub.add_parser("rotate", help="Rotate signing key and merge into existing keyset")
    rot.add_argument("--key-id", required=True, help="New key id for rotated signing key")
    rot.add_argument(
        "--existing-keyset",
        required=True,
        help="Current VOID_PACKET_VERIFY_KEYS_JSON object",
    )
    rot.set_defaults(func=cmd_rotate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
