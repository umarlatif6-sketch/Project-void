"""Starter world templates for ORYX creators."""

WORLD_TEMPLATES = {
    "sunsteel_frontier": {
        "name": "Sunsteel Frontier",
        "theme": "Mythic action frontier with traversal, relic hunts, and faction pressure.",
        "grid_size": 18,
        "resource_count": 20,
        "enemy_count": 8,
        "quest_pool": [
            "Recover a sun shard from the canyon vault.",
            "Escort a caravan through a hostile pass.",
            "Stabilize a fractured beacon before nightfall.",
        ],
        "factions": ["Caravan Houses", "Dust Monks", "Frontier Wardens"],
    },
    "veilrunner_city": {
        "name": "Veilrunner City",
        "theme": "Dense stealth-action city with rooftops, patrol routes, and social infiltration.",
        "grid_size": 16,
        "resource_count": 16,
        "enemy_count": 10,
        "quest_pool": [
            "Extract an archivist from the upper district.",
            "Swap the ledger before the patrol rotation resets.",
            "Map the hidden lifts beneath the market ring.",
        ],
        "factions": ["Guild Houses", "Mirror Office", "Street Choir"],
    },
    "starfold_reaches": {
        "name": "Starfold Reaches",
        "theme": "Space-opera frontier with sector claims, relic salvage, and fleet skirmishes.",
        "grid_size": 22,
        "resource_count": 24,
        "enemy_count": 12,
        "quest_pool": [
            "Chart a jump lane through an ion storm.",
            "Secure a relic engine before rival crews arrive.",
            "Broker a ceasefire between two sector captains.",
        ],
        "factions": ["Free Captains", "Helios Directorate", "Drift Syndicate"],
    },
}