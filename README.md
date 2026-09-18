# Jarvis

**v0.4.2**

Deterministic engineering engine for designing physical systems with AI-assisted natural language.

Jarvis is **aerial-first** (drones and related vehicles): you describe goals and components in Spanish; calculation and simulation stay rule-based and auditable. The model may interpret — it does not invent the physics.

Read the one-page contract: [VISION.md](VISION.md).

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

## What v0.4.2 includes (tag)

Mission craft software checkpoint (**Fase M CLOSED** — [M7 closeout](.jes/artifacts/engineer_note_fase_m_closeout_m7.md)):

- Continuity mission intent + wizard vigilancia nudge + SYSTEM_DEFINITION **B** routing
- Mission `mass_g` → AUW; Continuity ladder mount + autonomía objetivo; `power_w` declare + Phoenix catalog W
- `library/cameras` Phoenix 2 + `library/vtx` Zeus 800 — fluid catalog help-choose / rebind / mass mirror (RF mW ≠ DC W)
- BOM `[sku]` display for cameras / FC / sensors; craft-montage user guide sync
- Live suite **3165** · UI **105**
- Next: **Fase C** (control / enlace) — await Engineer ★; first product-contract Buy may be **`0.5.0`**

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

**Fase C** — firmware FC · MAVLink/GCS · bind ELRS · PID · mission planner · app piloto — await Engineer ★.

Parked (bags/lab): plate-box · Path N · HD-* · more camera/radio SKUs.

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
