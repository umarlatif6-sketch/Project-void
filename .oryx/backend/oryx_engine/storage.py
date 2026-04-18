"""Persistence helpers for ORYX worlds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonWorldStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, world_id: str) -> Path:
        return self.root / f"{world_id}.json"

    def save(self, world_id: str, payload: dict[str, Any]) -> None:
        self.path_for(world_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, world_id: str) -> dict[str, Any] | None:
        path = self.path_for(world_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_worlds(self) -> list[dict[str, Any]]:
        worlds = []
        for path in sorted(self.root.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            worlds.append(
                {
                    "id": payload["world"]["id"],
                    "name": payload["world"]["name"],
                    "template": payload["world"].get("template"),
                    "tick": payload["world"]["tick"],
                }
            )
        return worlds