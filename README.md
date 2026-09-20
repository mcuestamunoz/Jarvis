# Jarvis

**v0.5.3** — Fase C platform surface through radio (C4+C5 one block; no `v0.5.2` tag)

Deterministic engineering engine for designing physical systems with AI-assisted natural language.

Jarvis is **aerial-first** (drones and related vehicles): you describe goals and components in Spanish; calculation and simulation stay rule-based and auditable. The model may interpret — it does not invent the physics.

Read the one-page contract: [VISION.md](VISION.md).

**Fase C (platform scaffold) in plain language:** what “scaffold” means and what each new package is for — [ARCHITECTURE.md §1a](docs/ARCHITECTURE.md).

## Quick start

```bash
git clone https://github.com/mcuestamunoz/Jarvis.git
cd Jarvis
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,mcp]"
```

**CLI chat** (optional: local [Ollama](https://ollama.com) for `analyze` / free-form interpret):

```bash
python -m jarvis.main --chat
# or
jarvis --chat
```

**Pizarra** (visor 3D + Continuity spatial assembly; huecos de arquitectura = slots, no BOM; mutación = CLI / Continuity / Situar drag):

```bash
jarvis board
```

**Tests:**

```bash
pytest
```

**MCP server** (Cursor / MCP clients):

```bash
python -m jarvis.adapters.mcp.server
```

Workspace projects live under `workspace/` (override with `JARVIS_WORKSPACE_ROOT`).  
Ollama defaults: `JARVIS_OLLAMA_BASE_URL`, `JARVIS_OLLAMA_MODEL` (see `src/jarvis/config.py`).

## What v0.5.3 includes

Fase C · **C4 + C5** as **one ACCEPT block** (Engineer 2026-09-20) — package/tag **`v0.5.3`**. Intermediate tag **`v0.5.2` was never cut** (see [docs truth-sync](.jes/artifacts/engineer_note_docs_truth_sync_fase_c_2026_09_20.md)).

### C4 — autonomy command surface (`B1-fase-c-autonomy-surface`)

- **Same Engineer scaffold discipline: "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** No C++ tree, no CMake created.
- Opens `src/jarvis/flight_software/autonomy/` — `AutonomyVerb` (`TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/`RETURN_HOME`/`LAND`/`PATROL`), `propose_command()`, `submit_command()`
- Every `submit_command` call goes through `SafetyGate.evaluate(...)` first — with `RejectAllSafetyGate`, `HOLD`/`LAND` always `outcome=reject` / `execution="not_attempted"`
- Even a test-local fake `allow` gate cannot make `execution` become `"executed"` — resolves to `"not_implemented"`
- No `flight_software/autonomy/executor.py`; C3 IMU rung unchanged; registry still empty
- **Command surface != flyable autonomy**

### C5 — radio dual-role stub (`B1-fase-c-radio-dual-role`)

- `src/jarvis/capabilities/radio.py` — `RadioStubFrame` → `SimulatedRadioIngress` → `RadioDualRoleResult` (`Intent` and/or `AuthoritySignal`)
- `RadioIntentAdapter.parse(...)` still raises `NotImplementedError` (live path refuse)
- Optional `SafetyRequest.authority_signal_id` — RejectAll unchanged; authority never implies allow
- **Dual-role stub != live ELRS** — no CRSF/ELRS decode, no serial I/O, no radio→autonomy auto-submit
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- Tagged **`v0.5.3`** on Engineer ACCEPT (suite **3236**)

## What v0.5.1 includes

Fase C · **C3** (`B1-fase-c-first-fc-rung`) — **first `flight_control` rung, sensing-only**:

- **Engineer amendment (on top of the C3 IC): "Python scaffold / sim only — production flight_control runtime is C++ (future IC)."** Everything here is a Python platform scaffold, not the production flight controller; the real `flight_control` runtime/firmware will be C++ in later Buys with its own IC. No C++ tree, no CMake created in this Buy.
- Opens `src/jarvis/flight_software/flight_control/` and `src/jarvis/vehicle_profiles/` on disk for the first time — **exactly one rung**: HAL + simulated IMU sample acquisition (`ImuHal`, `SimulatedImuHal`, `ImuSample`)
- No filtering, no state estimation, no attitude/rate/position controller, no mixer, no ESC/PWM, no autonomy verbs — none of it exists in this package yet
- `SimulatedImuHal` is deterministic (same `seed` → same sample sequence) and never touches real hardware, a bus, or a network socket
- One pytest smoke `VehicleProfile` (`smoke_quad_hal_imu`) + `run_hal_imu_smoke()` in `vehicle_profiles/` — not bound to any craft workspace/BOM/catalog SKU
- **Naming split (honesty-critical):** craft catalog `flight_controller` (a BOM part) and `flight_software.flight_control` (this control spine) are different systems of record — never conflated
- `default_safety_gate()` unchanged — still always `RejectAllSafetyGate`; no `AllowAllSafetyGate` anywhere in `src/`
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/`
- **First rung stub @ 0.5.1 != controlled flight.** Estimation/control/mixer/ESC/autonomy remain future ICs (C4+)
- Tagged **`v0.5.1`** on Engineer ACCEPT (see `.jes/artifacts/implementation_review_fase_c_first_fc_rung_b1.md`)

## What v0.5.0 includes

Fase C · **C1** scaffold (`B1-fase-c-capability-registry-scaffold`) — **schemas only, no runtime**:

- `src/jarvis/capabilities/` — typed `CapabilityRecord` / `ProviderRecord` / `SkillRecord` (Pydantic) + a `CapabilityRegistry` with a query-only API (list / get-by-id / "who offers capability X?")
- `CapabilityRegistry.load_default()` is **always empty** — 0 capabilities, 0 providers, 0 skills. No path in the product marks flight/actuation as `available`; the `availability` enum only offers `stub` / `not_implemented` in C1
- **No execution path**: no method or field named `execute` / `dispatch` / `command_esc`; nothing here turns a record into a motor/ESC/autonomy command
- Does **not** touch Continuity, orchestrator IDLE, Board, or `library/` — craft SoT stays the `v0.4.3` surface
- **Scaffold @ 0.5.0 != Flight Software shipped.** At C1, `flight_software/` did not exist yet; C3 @ `v0.5.1` opens the first Python scaffold rung (production FC runtime remains C++ / future IC)
- Git tag **`v0.5.0`** / `checkpoint-fase-c-capability-registry` (Engineer ACCEPT 2026-09-20)

## What v0.4.3 includes (tag)

Last pre–Fase C checkpoint ([closeout note](.jes/artifacts/engineer_note_v0_4_3_pre_fase_c_close.md)):

- Everything in **v0.4.2** (Fase M mission craft), plus:
  - **D1** docs/` truth-sync @ code · obsolete labeled
  - **U1** Board **Taller 3D** default · Grafo tab · inspector + mount chain to plate · piece chips
  - IDLE first-acquire catalog scoped to `vtx`/`cameras` (FN-009 / terrestrial wizard preserved)
- Live suite **3166** · UI **132**
- Next: **Fase C** @ **`0.5.0`** on first Engineer ★ Buy

## What v0.4.2 included

Mission craft software checkpoint (**Fase M CLOSED** — [M7 closeout](.jes/artifacts/engineer_note_fase_m_closeout_m7.md)):

- Continuity mission intent + wizard vigilancia nudge + SYSTEM_DEFINITION **B** routing
- Mission `mass_g` → AUW; Continuity ladder mount + autonomía objetivo; `power_w` declare + Phoenix catalog W
- `library/cameras` Phoenix 2 + `library/vtx` Zeus 800 — fluid catalog help-choose / rebind / mass mirror (RF mW ≠ DC W)
- BOM `[sku]` display for cameras / FC / sensors; craft-montage user guide sync
- Live suite **3165** · UI **105**

## What v0.4.1 included

- Everything in **v0.4.0** (Continuity spatial assembly), plus Board **Situar**:
  - **C-113** — Scene3D drag → `board_pose_bridge` → same `set_component_declared_box_pose` writer as CLI `declara…`
  - Free camera while situating (no forced cenital); screen-plane drag follows the cursor; Shift = profundidad (Y)
  - Situar UX: larger pane, zoom range, live preview
  - Standoff count gate B4-min (`count==4` → corners; else omit)
- Live suite **2669** · UI **80**
- Locks unchanged: Prop/Energy = HD-004 wall; System Optimization deferred until pain; screening AABB ≠ fit VERIFIED

## What's landed between v0.4.1 and v0.4.2 (now tagged)

The **craft montage** + **mission craft** arc — empty project → montaje honesto + identidad/masa/montaje/potencia/VTX sin inventar física:

- Checklist family, estimated-temporary dims, arm/disk Visor, FC/sensors library envelopes
- Mission payload identity → cameras/radio → Continuity ladder → catalog seeds
- See `docs/IMPLEMENTATION_TASKS.md` and [USER_GUIDE_CRAFT_MONTAGE.md](docs/USER_GUIDE_CRAFT_MONTAGE.md)

## Next

**Fase C platform surface through radio CLOSED @ `v0.5.3`** (C4+C5 one block). Next Buy when Engineer prioritizes (further FC rungs / real Safety policy / native stacks). Filtering, state estimation, attitude/rate/position control, mixer, ESC/PWM, MAVLink/GCS, real ELRS decode, PID, mission planner, and app piloto remain later Buys.

Parked (bags/lab): plate-box · Path N · HD-* · more camera/radio SKUs · Board inspector polish.

See `docs/IMPLEMENTATION_TASKS.md`.

## Docs

| Doc | Role |
|-----|------|
| [VISION.md](VISION.md) | Product contract (non-technical) |
| [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md) | v1 usable — when a project is “done” |
| [docs/PROJECT_CONTINUITY.md](docs/PROJECT_CONTINUITY.md) | A' — Situation / Evidence / Next useful step |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system is built |
| [docs/system_map/README.md](docs/system_map/README.md) | System Map — connections & authority |
| [docs/USER_GUIDE_CRAFT_MONTAGE.md](docs/USER_GUIDE_CRAFT_MONTAGE.md) | Command-level walk: empty project → montaje honesto en Board |
| [docs/IMPLEMENTATION_TASKS.md](docs/IMPLEMENTATION_TASKS.md) | Roadmap, gaps, software/product debt |  
| [docs/HARDWARE_DEBT.md](docs/HARDWARE_DEBT.md) | Physics debt gated on T1/T2 lab (ESC η, battery C-rate, sag, OP→consumo) |
| [.jes/artifacts/cli_findings_post_catalog_bind_v1.md](.jes/artifacts/cli_findings_post_catalog_bind_v1.md) | Living CLI findings register (G9–G20) |
| [src/jarvis/README.md](src/jarvis/README.md) | Deeper product / flow reference |

## Tags

`v0.5.3` / `checkpoint-fase-c-autonomy-radio` — Fase C C4+C5 one block: autonomy command surface + radio dual-role stub; suite **3236** · UI **132**. (**No `v0.5.2` tag** — see truth-sync note.)  
`v0.5.1` / `checkpoint-fase-c-first-fc-rung` — Fase C C3: first `flight_control` rung (HAL + simulated IMU), `flight_software/`+`vehicle_profiles/` opened; Python scaffold, production FC runtime is C++ (future IC); suite **3206** · UI **132**.  
`v0.5.0` / `checkpoint-fase-c-capability-registry` — Fase C open: empty Capability Registry scaffold; suite **3181** · UI **132**.  
`v0.4.3` / `checkpoint-board-taller-3d` — pre–Fase C CLOSED: docs truth-sync + Board Taller 3D; suite **3166** · UI **132**.  
`v0.4.2` / `checkpoint-fase-m-mission-craft` — Fase M CLOSED: mission mass + Continuity ladder + cameras/VTX seeds + B routing; suite **3165** · UI **105**.  
`v0.4.1` / `checkpoint-board-situar` — Board Situar drag→pose (C-113) + free camera + standoff count gate; suite **2669** · UI **80**.  
`v0.4.0` / `checkpoint-continuity-spatial-assembly` — Continuity spatial assembly (*situar el mapa*); suite **2652**.  
`v0.3.8` / `checkpoint-spatial-board-projector` — ship `spatial_board.py` (was gitignored); `/workspace/` ignore.  
`v0.3.7` / `checkpoint-structure-representation-closed` — Structure representation arc closed (catalog→parts→rebind→plates); suite **2294**.  
`v0.3.6` / `checkpoint-experimental-prop-energy-closed` — experimental prop/energy/Structure A/fail-routing construction closed; knowledge-parity phase starts.  
`v0.3.5` / `checkpoint-phase25-hover-energy` — Phase 2.5 honest hover-regime autonomy.  
`v0.3.4` / `checkpoint-motor-op-voltage-coherence` — motor OP voltage gate + DSE live params.  
`v0.3.3` / `checkpoint-validation-case-regression-gate` — Validation Case probe/docs.  
`v0.3.2` / `checkpoint-deferred-queue-cd` — Deferred Queue C+D.  
`v0.3.1` / `checkpoint-next-engineering-block` — G24-A + P2-2 OP bridge.  
`v0.3.0` / `checkpoint-propeller-catalog-bind` — propeller help-choose → exact OP.  
`v0.2.0` — H1–H4 handoffs closed; System Map at 0 RED.  
`v0.1.0-prototype` — first functional cut.
