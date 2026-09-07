# Jarvis

**v0.3.8**

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

**Pizarra** (visor de componentes; huecos de arquitectura declarada se muestran como slots, no es BOM/completeness; el CLI sigue mutando el diseño):

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

## What v0.3.8 includes

- Everything in **v0.3.7** (Structure representation arc + `jarvis board` UI), plus the spatial projector that 0.3.7 gitignored (`src/jarvis/workspace/spatial_board.py`).
- Everything through **v0.3.6** (experimental prop/energy construction + Structure A + fail-routing), plus the closed **Structure representation** arc:
- Claim hygiene + control parity (`PASS *` honesty)
- Structure Foundations / Catalog Foundation IC-1→3 (frame seed + bind + assist)
- Structure honesty `PASS *` · Parts Graph Fase 1 · G-N1 free-text root+parts
- IDLE catalog rebind (frame / motors / propellers / battery)
- Arm `thickness_mm` + curated multi-plate assembly (`plates[]`, ordinal siblings, labels)
- Spatial board visor (`jarvis board`)
- Locks: Prop/Energy experimental = HD-004 wall; System Optimization deferred until demonstrated pain

## On the tree after v0.3.8 (no new tag)

Package version remains **0.3.8**. Live suite **2336**. The working tree also has:

- **B3 honest absence:** declared-architecture holes → `kind: "slot"`. Suite **2310**.
- **Geometry `representar`:** Battery / Motor / ESC catalog envelopes + FC Pixhawk 4 identity-linked box (44×84×12 mm). Suites through **2332**.
- **Sensors BOM honesty:** declarative tails distinguish GNSS vs bare `sensor_type` (suite **2336**) — claim ladder, not geometry.
- Layout overlay still in browser `localStorage` (B1 `spatial_layout.json` = named debt, not PRIORIDAD).
- **PRIORIDAD:** Geometry **visualizar** — Board glyph vocabulary investigation ([lock](.jes/artifacts/engineer_lock_geometry_spatial_representation_progression.md) · [contract](.jes/artifacts/investigation_contract_geometry_board_glyph_vocabulary.md)). Progression: dims → glyphs → pose → assembly → fit (no jump to “cabe”). See `docs/IMPLEMENTATION_TASKS.md`.

## Docs

| Doc | Role |
|-----|------|
| [VISION.md](VISION.md) | Product contract (non-technical) |
| [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md) | v1 usable — when a project is “done” |
| [docs/PROJECT_CONTINUITY.md](docs/PROJECT_CONTINUITY.md) | A' — Situation / Evidence / Next useful step |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system is built |
| [docs/system_map/README.md](docs/system_map/README.md) | System Map — connections & authority |
| [docs/IMPLEMENTATION_TASKS.md](docs/IMPLEMENTATION_TASKS.md) | Roadmap, gaps, software/product debt |  
| [docs/HARDWARE_DEBT.md](docs/HARDWARE_DEBT.md) | Physics debt gated on T1/T2 lab (ESC η, battery C-rate, sag, OP→consumo) |
| [.jes/artifacts/cli_findings_post_catalog_bind_v1.md](.jes/artifacts/cli_findings_post_catalog_bind_v1.md) | Living CLI findings register (G9–G20) |
| [src/jarvis/README.md](src/jarvis/README.md) | Deeper product / flow reference |

## Tags

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
