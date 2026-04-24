# ORYX Creator Engine

ORYX is a separate game and world-building company concept incubated alongside Project VOID. It is structured as a standalone creator engine with optional Project VOID integration rather than a hard dependency.

## What Exists Now
- Modular Python backend for world simulation
- Creator API for spawning worlds from templates
- Agent, quest, faction, and resource simulation primitives
- JSON persistence for saved creator worlds
- Compatibility route for a simple AI-agent arena
- Documentation for company separation and integration boundaries

## Product Direction
ORYX is aimed at being a lower-cost creator platform where studios, communities, or solo builders can launch their own worlds without depending on a heavyweight proprietary engine stack.

## Layout
- backend/: Flask API and ORYX engine package
- backend/data/: saved world states
- docs/company_blueprint.md: separate company and platform model
- docs/creator_platform.md: creator-engine roadmap and API model
- docs/repair_doctrine.md: creator-side repair law for broken workflows, permissions, and world integrity
- docs/unreal_parity_roadmap.md: phased roadmap to approach fuller game-engine capability over time
- frontend/: reserved for the creator dashboard and world editor

## Quick Start
1. Install backend dependencies from backend/requirements.txt.
2. Run the Flask API from backend/app.py.
3. Create worlds through /api/worlds and step them through /api/worlds/<world_id>/step.

Project VOID can remain an optional upstream intelligence and lore source, but ORYX should be able to operate on its own.

When ORYX workflows break, the expectation is not silent reset or blind overwrite. The platform should preserve state, classify the fracture, and repair under audit.