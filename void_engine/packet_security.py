"""Packet security bootstrap and environment validation helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PacketSecurityConfig:
    enforce: bool
    signing_key_id: str
    signing_private_key: str
    verify_keys: Dict[str, str]
    require_sector_policy: bool
    max_age_seconds: int


def _parse_bool(raw: str, default: bool = False) -> bool:
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _parse_verify_keys(raw: str) -> Dict[str, str]:
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise ValueError("VOID_PACKET_VERIFY_KEYS_JSON must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("VOID_PACKET_VERIFY_KEYS_JSON must be an object of key_id -> public_key")

    clean: Dict[str, str] = {}
    for key_id, key_value in parsed.items():
        kid = str(key_id or "").strip()
        kval = str(key_value or "").strip()
        if not kid or not kval:
            continue
        clean[kid] = kval
    return clean


def read_packet_security_config() -> PacketSecurityConfig:
    enforce = _parse_bool(os.getenv("VOID_PACKET_SECURITY_ENFORCE", "false"), default=False)
    signing_key_id = (os.getenv("VOID_PACKET_SIGNING_KEY_ID") or "default").strip()
    signing_private_key = (os.getenv("VOID_PACKET_SIGNING_PRIVATE_KEY") or "").strip()
    verify_keys = _parse_verify_keys(os.getenv("VOID_PACKET_VERIFY_KEYS_JSON") or "")
    require_sector_policy = _parse_bool(os.getenv("VOID_PACKET_REQUIRE_SECTOR_POLICY", "false"), default=False)

    raw_max_age = (os.getenv("VOID_PACKET_MAX_AGE_SECONDS") or "86400").strip()
    try:
        max_age_seconds = int(raw_max_age)
    except ValueError as exc:
        raise ValueError("VOID_PACKET_MAX_AGE_SECONDS must be an integer") from exc

    if max_age_seconds <= 0:
        raise ValueError("VOID_PACKET_MAX_AGE_SECONDS must be > 0")

    return PacketSecurityConfig(
        enforce=enforce,
        signing_key_id=signing_key_id,
        signing_private_key=signing_private_key,
        verify_keys=verify_keys,
        require_sector_policy=require_sector_policy,
        max_age_seconds=max_age_seconds,
    )


def validate_packet_security_config(config: PacketSecurityConfig) -> List[str]:
    errors: List[str] = []
    if not config.enforce:
        return errors

    if not config.signing_private_key:
        errors.append("VOID_PACKET_SIGNING_PRIVATE_KEY is required when VOID_PACKET_SECURITY_ENFORCE=true")
    if not config.verify_keys:
        errors.append("VOID_PACKET_VERIFY_KEYS_JSON must provide at least one key when VOID_PACKET_SECURITY_ENFORCE=true")
    if not config.signing_key_id:
        errors.append("VOID_PACKET_SIGNING_KEY_ID is required when VOID_PACKET_SECURITY_ENFORCE=true")
    if config.signing_key_id and config.signing_key_id not in config.verify_keys:
        errors.append("VOID_PACKET_SIGNING_KEY_ID must exist in VOID_PACKET_VERIFY_KEYS_JSON")

    return errors
