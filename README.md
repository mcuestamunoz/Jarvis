# Jarvis

**v0.4.1**

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

## What v0.4.1 includes (tag)

- Everything in **v0.4.0** (Continuity spatial assembly), plus Board **Situar**:
  - **C-113** — Scene3D drag → `board_pose_bridge` → same `set_component_declared_box_pose` writer as CLI `declara…`
  - Free camera while situating (no forced cenital); screen-plane drag follows the cursor; Shift = profundidad (Y)
  - Situar UX: larger pane, zoom range, live preview
  - Standoff count gate B4-min (`count==4` → corners; else omit)
- Live suite **2669** · UI **80**
- Locks unchanged: Prop/Energy = HD-004 wall; System Optimization deferred until pain; screening AABB ≠ fit VERIFIED

## What's landed since (same `0.4.1`, no version bump)

The **craft montage** arc (2026-09-13→15) — Jarvis can walk a project from empty to an honestly-montado Board without inventing a millimetre:

- **Checklist family** (suggest-only, never silent writes): `montajes estándar` · `apilar en placa` (Path F centered stack) · `layout pack` (named curated kit packs) · `parece un dron` (racimo / silueta estimada B\* / silueta B) · `relaciones`/`fit` (per-relation screening/attest checklist)
- **Estimated-temporary dims**, disclosed and gated out of `cabe`/`declaro verificado`: main plate (`declara frame_plate estimada … mm`) and, for a hybrid ESC with cited L×W but no cited height, `declara el esc estimado … mm`
- **Arm radial Visor** — `frame_arm` copies place along the origin→motor ray using the arm's own declared length (not a fixed midpoint), with yaw
- **Disk axial Visor** — a motor/propeller with both a diameter and a cited axial fact (`height_mm`/`hub_thickness_mm`) now renders as a real cylinder, never a flat disk pretending to have no depth
- **`library/fc/` + `library/sensors/`** — flight-controller and GPS/sensor physical envelopes moved out of a hard-coded dict in `aerial.py` into `ComponentLibrary` (`FcSpec`/`SensorSpec`), matching every other catalog family
- **SYSTEM_DEFINITION block gate** — custom blocks only accept if every expanded component key has a `ComponentRule`; otherwise refuse honestly (no stuck BOM)
- **Mission payload identity** — `cameras` + `radio_module` identity rules unlock SYSTEM_DEFINITION **B** for `cámara` / `comunicación` (model → medium; no invented mm/g/W; no catalog physics yet). Still gated: `payload` / `brazo` / wheels / gearbox
- **Disk-station reach** — `relaciones` screens **motors↔frame_arm** as station reach (arm L vs quad-X radius); `declaro verificado el motor` when reach-ok. Propellers↔motors still n/a disk. AABB `cabe` unchanged (boxes only)
- **User guide**: [`docs/USER_GUIDE_CRAFT_MONTAGE.md`](docs/USER_GUIDE_CRAFT_MONTAGE.md) — empty project → montaje + arquitectura B + cámara/radio + alcance motor
- Live suite **2968** · UI **105**
- Parked on bags/lab (not software queue): plate-box measure · Path N · HD-* · `library/cameras` physics

## Next (software-closable — no caliper / no banco)

- Continuity next-step vs mission intent (“vigilancia” vs “Aumentar carga útil”)
- Wizard vigilancia nudge (after mission identity)
- `propellers`↔`motors` evidence class (own B0/B1)
- Hygiene: `bind_esc_from_catalog` stale-key leak · `cambiar`/`actualiza` FC/GPS
- Optional identity rules: `payload_bay` / `arm` / … (same pattern as cameras)

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

`v0.4.1` (current tip, untagged patch work) — craft montage + mission-payload + disk-station reach + user guide; suite **2968** · UI **105**.  
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
