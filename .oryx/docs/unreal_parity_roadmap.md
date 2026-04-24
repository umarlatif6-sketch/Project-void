# ORYX Unreal-Parity Roadmap

This roadmap defines how ORYX can move closer to Unreal Engine capabilities over time while preserving the Project VOID doctrine (auditability, role integrity, and repair-state visibility).

It is not a claim of current parity. It is an execution map.

## Positioning

Unreal Engine is a mature, full-spectrum real-time 3D production engine.

ORYX is currently a creator simulation platform with strong collaboration and operations surfaces.

The strategy is to grow ORYX in layers:

1. Runtime and scene foundations
2. Asset and content pipeline
3. Deterministic simulation + multiplayer replication
4. Profiling, tooling, packaging, and platform delivery

## North-Star Outcomes

By the end of this roadmap, ORYX should provide:

- A scene graph and component model suitable for 2D/3D runtime worlds
- A repeatable asset pipeline for import, validation, versioning, and packaging
- Deterministic simulation mode for authoritative replay and server trust
- Multiplayer replication model with predictable conflict handling
- Profiling and diagnostics surfaces comparable to production-grade engines
- Editor and packaging workflows suitable for independent studios

## Phase 0 (Now -> 6 Weeks)

Goal: stabilize the engine core and prepare for real-time runtime growth.

### Deliverables

- Define engine boundary modules:
  - `runtime/` (scene, entities, components)
  - `net/` (replication and state sync)
  - `assets/` (manifests and import pipeline)
  - `perf/` (timing, counters, frame diagnostics)
- Add deterministic tick mode:
  - seeded RNG per world
  - fixed-step simulation option
  - canonical state hash per tick
- Add lightweight metrics endpoint:
  - per-route latency
  - simulation step duration p50/p95
  - socket room counts and update rate

### Acceptance Gates

- Two identical deterministic world runs produce the same state hash sequence
- Metrics endpoint returns stable values under synthetic load
- Existing collaboration/repair-state tests continue to pass

## Phase 1 (6 -> 14 Weeks)

Goal: establish runtime primitives that can host gameplay systems.

### Deliverables

- Scene graph:
  - world -> scene -> entity hierarchy
  - transform component (position/rotation/scale)
  - tags/layers for filtering and culling
- Component system:
  - renderable placeholder component
  - collider component
  - script behavior component
- Runtime update order:
  - pre-physics
  - simulation
  - post-simulation

### Acceptance Gates

- Entities/components can be serialized and restored without drift
- Tick loop remains deterministic when deterministic mode is enabled
- Scene graph operations remain within target latency budgets

## Phase 2 (14 -> 24 Weeks)

Goal: build an asset and content pipeline for creators.

### Deliverables

- Asset manifest format (JSON first):
  - UUID, type, dependencies, version, checksum
- Import pipeline:
  - textures, static meshes, audio stubs
  - validation and fail-closed import errors
- Build artifacts:
  - cooked asset bundle per world
  - reproducible build metadata

### Acceptance Gates

- Asset bundle generation is reproducible for same inputs
- Corrupt or missing dependencies fail cleanly with operator-visible diagnostics
- Creator editor can browse imported assets and attach to entities

## Phase 3 (24 -> 36 Weeks)

Goal: move from simulation sync to gameplay replication semantics.

### Deliverables

- Replication model:
  - authority rules (server authoritative)
  - relevance filtering (who receives what updates)
  - delta compression for world state
- Conflict and correction logic:
  - snapshot + rollback strategy for invalid local predictions
  - explicit repair-state mapping for replication faults
- Session and lobby layer:
  - world instances
  - presence and reconnect behavior

### Acceptance Gates

- Under packet loss simulation, world convergence remains within bounded ticks
- Replication faults are visible in audit log with repair-state tags
- Reconnect path preserves role boundaries and world integrity

## Phase 4 (36 -> 52 Weeks)

Goal: production-grade tooling and platform packaging.

### Deliverables

- Performance tooling:
  - CPU/GPU timing hooks (where available)
  - simulation heatmaps
  - network bandwidth and replication diagnostics
- Editor upgrades:
  - visual scene editing
  - behavior graph v1
  - live playtest mode
- Packaging:
  - one-click world package export
  - runtime package validation
  - deployment presets (local, cloud, private edge)

### Acceptance Gates

- Build, package, and run flow can be executed by non-core engineers
- Operator diagnostics can identify major performance bottlenecks within minutes
- Baseline world template meets defined frame/update and latency targets

## Unreal-Comparison Matrix (Target Direction)

Use this matrix to track "closeness" over time.

| Capability | Unreal Today | ORYX Current | ORYX Target |
|------------|--------------|--------------|-------------|
| Scene graph | Mature | Minimal | Full entity/component scene model |
| Rendering pipeline | AAA | Minimal | Incremental runtime renderer integration |
| Physics | Mature | Logic simulation only | Deterministic physics layer v1 |
| Asset pipeline | Mature | Early/manual | Managed import + bundle cook |
| Multiplayer replication | Mature | Realtime sync primitives | Server-authoritative replication model |
| Editor tooling | Mature | Operational dashboard | Visual world editor + behavior graph |
| Profiling | Mature | Basic logs | Built-in runtime/perf diagnostics |
| Packaging | Mature multi-platform | API-first deployment | Repeatable package/export pipeline |

## Governance Rules While Scaling

- Do not break role/permission boundaries to accelerate tooling.
- Do not hide sync faults; classify and expose them via repair-state.
- Keep deterministic mode available for trust-critical worlds.
- Keep audit trails as first-class engine data.

## Suggested Immediate Backlog (Next 2 Sprints)

1. Add deterministic mode flag + seeded RNG + state hashing.
2. Add `/api/metrics` with simulation and socket counters.
3. Create `assets/manifest` schema and importer stubs.
4. Add replication design spec and failure taxonomy.
5. Add performance budget table for templates.

If these five are complete, ORYX begins moving from simulation platform to engine trajectory.