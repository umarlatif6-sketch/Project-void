"""VOID Impulse Packet encoder/decoder.

Schema:
  VOID|AGENTID|FREQHEX|VECTORHEX|PAYLOAD_B64_ZLIB|CRC32HEX

Notes:
  - Header is fixed to "VOID".
  - Frequency is encoded as 4 hex chars representing integer Hz.
  - Vector is a 16-hex-character bitmask.
  - Payload is UTF-8 JSON, zlib-compressed, base64-encoded.
  - Checksum is CRC32 over all fields except checksum.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import zlib
from dataclasses import dataclass
from typing import Any


PROTOCOL_HEADER = "VOID"
FIELD_SEPARATOR = "|"
VECTOR_RE = re.compile(r"^[0-9A-Fa-f]{16}$")
AGENT_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
FREQ_RE = re.compile(r"^[0-9A-Fa-f]{4}$")
CRC_RE = re.compile(r"^[0-9A-Fa-f]{8}$")


class PacketError(ValueError):
    """Raised when a packet is malformed or fails integrity checks."""


@dataclass(frozen=True)
class DecodedPacket:
    header: str
    agent_id: str
    frequency_hz: int
    frequency_hex: str
    vector_hex: str
    payload: dict[str, Any]
    checksum_hex: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "header": self.header,
            "agent_id": self.agent_id,
            "frequency_hz": self.frequency_hz,
            "frequency_hex": self.frequency_hex,
            "vector_hex": self.vector_hex,
            "payload": self.payload,
            "checksum_hex": self.checksum_hex,
        }


def _compute_crc32_hex(base_fields: list[str]) -> str:
    base = FIELD_SEPARATOR.join(base_fields).encode("utf-8")
    crc = zlib.crc32(base) & 0xFFFFFFFF
    return f"{crc:08X}"


def _encode_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")


def _decode_payload(payload_field: str) -> dict[str, Any]:
    try:
        compressed = base64.urlsafe_b64decode(payload_field.encode("ascii"))
        raw = zlib.decompress(compressed)
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise PacketError(f"payload decode failed: {exc}") from exc

    if not isinstance(data, dict):
        raise PacketError("payload must decode to a JSON object")
    return data


def encode_void_packet(
    agent_id: str,
    frequency_hz: int,
    vector_hex: str,
    payload: dict[str, Any],
) -> str:
    agent_id = agent_id.upper()
    vector_hex = vector_hex.upper()

    if not AGENT_RE.fullmatch(agent_id):
        raise PacketError("agent_id must be exactly 8 hex chars")
    if not VECTOR_RE.fullmatch(vector_hex):
        raise PacketError("vector_hex must be exactly 16 hex chars")
    if frequency_hz < 0 or frequency_hz > 0xFFFF:
        raise PacketError("frequency_hz must be in range 0..65535")

    frequency_hex = f"{frequency_hz:04X}"
    payload_field = _encode_payload(payload)
    base_fields = [PROTOCOL_HEADER, agent_id, frequency_hex, vector_hex, payload_field]
    checksum_hex = _compute_crc32_hex(base_fields)
    return FIELD_SEPARATOR.join(base_fields + [checksum_hex])


def decode_void_packet(packet: str) -> DecodedPacket:
    parts = packet.strip().split(FIELD_SEPARATOR)
    if len(parts) != 6:
        raise PacketError("packet must contain exactly 6 fields")

    header, agent_id, frequency_hex, vector_hex, payload_field, checksum_hex = parts

    if header != PROTOCOL_HEADER:
        raise PacketError("invalid protocol header")
    if not AGENT_RE.fullmatch(agent_id):
        raise PacketError("invalid agent_id field")
    if not FREQ_RE.fullmatch(frequency_hex):
        raise PacketError("invalid frequency field")
    if not VECTOR_RE.fullmatch(vector_hex):
        raise PacketError("invalid vector field")
    if not CRC_RE.fullmatch(checksum_hex):
        raise PacketError("invalid checksum field")

    expected = _compute_crc32_hex([header, agent_id, frequency_hex, vector_hex, payload_field])
    if checksum_hex.upper() != expected:
        raise PacketError(f"checksum mismatch: expected {expected}, got {checksum_hex.upper()}")

    payload = _decode_payload(payload_field)
    frequency_hz = int(frequency_hex, 16)

    return DecodedPacket(
        header=header,
        agent_id=agent_id.upper(),
        frequency_hz=frequency_hz,
        frequency_hex=frequency_hex.upper(),
        vector_hex=vector_hex.upper(),
        payload=payload,
        checksum_hex=checksum_hex.upper(),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Encode/decode VOID impulse packets")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="Encode a packet")
    enc.add_argument("--agent-id", required=True, help="8-char hex agent id, e.g. AE01F401")
    enc.add_argument("--frequency-hz", type=int, required=True, help="Frequency in Hz")
    enc.add_argument("--vector", required=True, help="16-char hex vector bitmask")
    enc.add_argument(
        "--payload-json",
        required=True,
        help="JSON object string payload, e.g. '{\"status\":\"ok\"}'",
    )

    dec = sub.add_parser("decode", help="Decode a packet")
    dec.add_argument("--packet", required=True, help="Full packet string")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.cmd == "encode":
            payload_obj = json.loads(args.payload_json)
            if not isinstance(payload_obj, dict):
                raise PacketError("payload JSON must be an object")
            packet = encode_void_packet(
                agent_id=args.agent_id,
                frequency_hz=args.frequency_hz,
                vector_hex=args.vector,
                payload=payload_obj,
            )
            print(packet)
            return 0

        decoded = decode_void_packet(args.packet)
        print(json.dumps(decoded.to_dict(), indent=2, sort_keys=True))
        return 0
    except PacketError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
