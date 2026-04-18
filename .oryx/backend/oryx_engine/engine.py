"""Core simulation engine for ORYX creator worlds."""

from __future__ import annotations

import random
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from .storage import JsonWorldStore
from .templates import WORLD_TEMPLATES


class OryxEngine:
    def __init__(self, storage_root: Path) -> None:
        self.store = JsonWorldStore(storage_root)

    def templates(self) -> dict[str, dict[str, Any]]:
        return deepcopy(WORLD_TEMPLATES)

    def list_worlds(self) -> list[dict[str, Any]]:
        return self.store.list_worlds()

    def create_world(
        self,
        *,
        name: str,
        template_key: str,
        company_name: str,
        integration_mode: str = "optional",
    ) -> dict[str, Any]:
        template = self.templates().get(template_key)
        if template is None:
            raise ValueError(f"Unknown template: {template_key}")

        world_id = uuid.uuid4().hex[:12]
        payload = {
            "company": {
                "name": company_name,
                "product": name,
                "linked_to_project_void": integration_mode != "none",
                "integration_mode": integration_mode,
            },
            "world": {
                "id": world_id,
                "name": name,
                "template": template_key,
                "theme": template["theme"],
                "grid_size": template["grid_size"],
                "tick": 0,
                "treasury": 0,
                "creator_tools": {
                    "quests": True,
                    "factions": True,
                    "agents": True,
                    "economy": True,
                },
            },
            "agents": self._spawn_agents(template["grid_size"]),
            "resources": self._spawn_points(template["resource_count"], template["grid_size"]),
            "enemies": self._spawn_enemies(template["enemy_count"], template["grid_size"]),
            "quests": [
                {"id": uuid.uuid4().hex[:8], "text": item, "status": "open"}
                for item in template["quest_pool"]
            ],
            "factions": [{"name": faction, "influence": 50} for faction in template["factions"]],
            "log": [f"World {name} initialized from template {template_key}."],
        }
        self.store.save(world_id, payload)
        return payload

    def load_world(self, world_id: str) -> dict[str, Any]:
        payload = self.store.load(world_id)
        if payload is None:
            raise KeyError(world_id)
        return payload

    def add_agent(self, world_id: str, *, agent_name: str, behavior: str) -> dict[str, Any]:
        payload = self.load_world(world_id)
        grid = payload["world"]["grid_size"]
        payload["agents"].append(
            {
                "id": uuid.uuid4().hex[:8],
                "name": agent_name,
                "behavior": behavior,
                "x": random.randint(0, grid - 1),
                "y": random.randint(0, grid - 1),
                "energy": 100,
                "inventory": [],
                "score": 0,
            }
        )
        payload["log"].append(f"Agent {agent_name} joined with {behavior} behavior.")
        self.store.save(world_id, payload)
        return payload

    def inject_quest(self, world_id: str, *, quest_text: str) -> dict[str, Any]:
        payload = self.load_world(world_id)
        payload["quests"].append({"id": uuid.uuid4().hex[:8], "text": quest_text, "status": "open"})
        payload["log"].append(f"Creator injected quest: {quest_text}")
        self.store.save(world_id, payload)
        return payload

    def step_world(self, world_id: str, *, steps: int = 1) -> dict[str, Any]:
        payload = self.load_world(world_id)
        for _ in range(max(1, steps)):
            self._step(payload)
        self.store.save(world_id, payload)
        return payload

    def _step(self, payload: dict[str, Any]) -> None:
        grid = payload["world"]["grid_size"]
        resources = {(item["x"], item["y"]): item for item in payload["resources"]}
        for agent in payload["agents"]:
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            agent["x"] = min(max(agent["x"] + dx, 0), grid - 1)
            agent["y"] = min(max(agent["y"] + dy, 0), grid - 1)
            agent["energy"] = max(agent["energy"] - 1, 0)
            resource = resources.pop((agent["x"], agent["y"]), None)
            if resource:
                agent["score"] += resource["value"]
                agent["inventory"].append(resource["kind"])
                payload["world"]["treasury"] += resource["value"]

        payload["resources"] = list(resources.values())
        while len(payload["resources"]) < max(4, grid // 2):
            payload["resources"].append(self._resource_point(grid))

        for enemy in payload["enemies"]:
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0), (0, 0)])
            enemy["x"] = min(max(enemy["x"] + dx, 0), grid - 1)
            enemy["y"] = min(max(enemy["y"] + dy, 0), grid - 1)

        if payload["quests"] and random.random() < 0.35:
            quest = random.choice(payload["quests"])
            if quest["status"] == "open":
                quest["status"] = "in_progress"

        if payload["factions"] and random.random() < 0.5:
            faction = random.choice(payload["factions"])
            faction["influence"] = min(100, max(0, faction["influence"] + random.randint(-3, 4)))

        payload["world"]["tick"] += 1
        payload["log"].append(
            f"Tick {payload['world']['tick']}: treasury={payload['world']['treasury']} resources={len(payload['resources'])}"
        )
        payload["log"] = payload["log"][-25:]

    def _spawn_agents(self, grid_size: int) -> list[dict[str, Any]]:
        archetypes = [
            ("Pathfinder", "explore"),
            ("Sentinel", "guard"),
            ("Broker", "trade"),
            ("Seeker", "quest"),
        ]
        return [
            {
                "id": uuid.uuid4().hex[:8],
                "name": name,
                "behavior": behavior,
                "x": random.randint(0, grid_size - 1),
                "y": random.randint(0, grid_size - 1),
                "energy": 100,
                "inventory": [],
                "score": 0,
            }
            for name, behavior in archetypes
        ]

    def _spawn_enemies(self, count: int, grid_size: int) -> list[dict[str, Any]]:
        return [
            {
                "id": uuid.uuid4().hex[:8],
                "name": f"Rival-{index + 1}",
                "threat": random.choice(["low", "medium", "high"]),
                "x": random.randint(0, grid_size - 1),
                "y": random.randint(0, grid_size - 1),
            }
            for index in range(count)
        ]

    def _spawn_points(self, count: int, grid_size: int) -> list[dict[str, Any]]:
        return [self._resource_point(grid_size) for _ in range(count)]

    def _resource_point(self, grid_size: int) -> dict[str, Any]:
        return {
            "id": uuid.uuid4().hex[:8],
            "kind": random.choice(["relic", "intel", "fuel", "artifact"]),
            "value": random.randint(5, 20),
            "x": random.randint(0, grid_size - 1),
            "y": random.randint(0, grid_size - 1),
        }