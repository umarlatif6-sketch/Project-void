# ORYX Creator Platform

ORYX is evolving toward a creator platform where users can define and operate their own games and worlds.

The platform now also carries an explicit repair doctrine: preserve world integrity, role boundaries, and audit continuity while repairing broken creator workflows.

## Current Backend Primitives
- World templates
- Persistent world state
- SQLite creator accounts and token sessions
- World ownership controls per creator account
- Agents with behaviors and inventories
- Quests and faction influence
- Tick-based simulation and treasury growth
- Browser editor shell for creator workflows
- Realtime world rooms and websocket tick streaming
- Role-based collaboration: owner, editor, viewer
- Per-collaborator feature permission overrides
- Expiring invite tokens with share URLs
- Audit log for collaboration and world mutation events
- World summary snapshot for operational dashboard views
- Paged audit browsing for higher-volume worlds

## First Creator Loop
1. Pick a world template.
2. Name the world and company.
3. Launch the world through the API.
4. Add agents or inject quests.
5. Step the world and inspect the resulting economy and state transitions.

## API Surface
- GET /api/templates
- GET /api/worlds
- POST /api/worlds
- GET /api/worlds/<world_id>
- GET /api/worlds/<world_id>/summary
- POST /api/worlds/<world_id>/step
- POST /api/worlds/<world_id>/agents
- POST /api/worlds/<world_id>/quests
- GET /api/worlds/<world_id>/collaborators
- POST /api/worlds/<world_id>/collaborators
- POST /api/worlds/<world_id>/collaborators/remove
- GET /api/worlds/<world_id>/permissions
- POST /api/worlds/<world_id>/permissions
- GET /api/worlds/<world_id>/invites
- POST /api/worlds/<world_id>/invites
- POST /api/worlds/<world_id>/invites/revoke
- POST /api/invites/accept
- GET /api/worlds/<world_id>/audit

## Permission Model
- owner: full control, can manage collaborators
- editor: can mutate world state (step, agents, quests, stream control)
- viewer: spectator mode only (view world, join room, receive realtime state)

Delegated admin controls are permission-driven:
- can_manage_collaborators
- can_manage_invites
- can_manage_permissions

## Invite Flow
- Owner creates an editor or viewer invite token for a world.
- Each invite has an expiry window and a share URL in the form /editor?invite=<token>.
- Logged-in user accepts the token through POST /api/invites/accept.
- Owner can revoke unused tokens or remove existing collaborators later.
- The editor can copy the generated share URL directly after invite creation or selection.

## Feature Override Model
- Base role grants the default capability set.
- Owner can override collaborator capabilities per world for:
- can_view_world
- can_step_world
- can_manage_agents
- can_manage_quests
- can_manage_stream
- can_manage_collaborators
- can_manage_invites
- can_manage_permissions

This allows owners to delegate parts of collaboration administration without granting full ownership.

## Audit Model
- Collaboration changes, invite lifecycle events, stream actions, and world mutations are recorded in the world audit log.
- Audit entries now carry a persisted `repair_state` so recoverable and quarantined events can be filtered without re-deriving state from action names at read time.
- Consumers can query recent entries through GET /api/worlds/<world_id>/audit.
- Audit queries can be filtered by exact action, actor email, and repair_state through query params.
- Audit queries support limit and offset for paging through longer histories.

## Operator Dashboard
- The editor exposes a world dashboard panel backed by GET /api/worlds/<world_id>/summary.
- Summary responses include world metadata, entity counts, current stream status, caller role, caller permissions, and the most recent audit slice.
- The audit panel supports page size and offset controls so operators can move through larger logs without dumping the entire history at once.

## Repair Doctrine
- See `docs/repair_doctrine.md` for the creator-side translation of the Al-Jabr repair law.
- Operators should classify broken workflows as recoverable, quarantined, superseded, or false joins before changing them.
- Repairs must preserve auditability, role boundaries, and world-state continuity.

## Realtime Socket Events
- Client -> Server: join_world {world_id, token}
- Client -> Server: leave_world {world_id}
- Client -> Server: tick_once {world_id, token, steps}
- Client -> Server: start_stream {world_id, token, interval_ms, steps}
- Client -> Server: stop_stream {world_id, token}
- Server -> Client: joined_world, left_world, stream_status, stream_error, world_state

## Next Technical Moves
- Add Postgres storage and migrations for production
- Add visual editor frontend
- Add combat, traversal, and dialogue systems
- Add packaging so creators can publish worlds as products

## Unreal-Parity Direction
- See `docs/unreal_parity_roadmap.md` for the phased plan to move ORYX closer to full engine capabilities over time.
- Use that roadmap as the execution contract for runtime, asset pipeline, replication, profiling, and packaging evolution.