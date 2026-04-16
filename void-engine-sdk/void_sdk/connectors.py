"""
VOID SDK Connectors — pluggable surfaces for present-market systems.

These connectors do not replace the protocol. They expose it through
common integration shapes buyers already understand: webhooks and
warehouse exports.
"""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Optional
from urllib import request
from urllib.error import HTTPError, URLError


class VoidWarehouseExporter:
    """Export VOID events in warehouse-friendly formats."""

    SUPPORTED_FORMATS = {"jsonl", "csv"}

    def export(
        self,
        records: list[dict],
        fmt: str = "jsonl",
        file_path: Optional[str] = None,
    ) -> dict:
        fmt = fmt.lower().strip()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported export format: {fmt}")

        content = self._to_jsonl(records) if fmt == "jsonl" else self._to_csv(records)
        output_path = None
        if file_path:
            output_path = Path(file_path)
            output_path.write_text(content, encoding="utf-8")

        return {
            "ok": True,
            "format": fmt,
            "record_count": len(records),
            "file_path": str(output_path) if output_path else None,
            "content": content,
        }

    def _to_jsonl(self, records: list[dict]) -> str:
        return "\n".join(json.dumps(record, sort_keys=True) for record in records)

    def _to_csv(self, records: list[dict]) -> str:
        if not records:
            return ""
        fieldnames = sorted({key for record in records for key in record.keys()})
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            normalized = {
                key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                for key, value in record.items()
            }
            writer.writerow(normalized)
        return buffer.getvalue()


def build_webhook_payload(
    *,
    entity: str,
    condition: str,
    action: str,
    codon: str,
    meta: dict,
    digest: str,
    formation: float,
    tier: str,
    ts: float,
) -> dict:
    """Return the normalized payload shape for external connector delivery."""
    return {
        "spec_version": "void.webhook.v1",
        "entity": entity,
        "condition": condition,
        "action": action,
        "codon": codon,
        "digest": digest,
        "formation_score": formation,
        "tier": tier,
        "ts": ts,
        "meta": meta,
    }


def post_webhook_payload(
    url: str,
    payload: dict,
    timeout: float = 5.0,
    headers: Optional[dict[str, str]] = None,
) -> dict:
    """POST a VOID payload using only the Python standard library."""
    merged_headers = {
        "Content-Type": "application/json",
        "User-Agent": "void-engine-sdk/1.0.0",
    }
    if headers:
        merged_headers.update(headers)

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, headers=merged_headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "body": response_body,
            }
    except HTTPError as exc:
        return {
            "ok": False,
            "status_code": exc.code,
            "body": exc.read().decode("utf-8", errors="replace"),
        }
    except URLError as exc:
        return {
            "ok": False,
            "status_code": None,
            "body": str(exc.reason),
        }
