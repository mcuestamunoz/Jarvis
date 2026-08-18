# Jarvis

**v0.2.0**

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

## What v0.2 includes

- Guided / direct `create_project`
- Component definition in natural language (motors, frame, battery, propellers, …)
- Deterministic `calculate` and `simulate` with history + Markdown views
- Controlled `iterate` and design-space explore / apply (DSE)
- Engineering intent → Goal Plan → Handoff Context (Plan → DSE / Iterate, FN-024…026)
- Living System Map (`docs/system_map/`) — 59 connections, 0 RED
- CLI and MCP adapters
- Curated material & motor library (small; Physical Catalog v1 is the next engineering leap)

## Docs

| Doc | Role |
|-----|------|
| [VISION.md](VISION.md) | Product contract (non-technical) |
| [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md) | v1 usable — when a project is “done” |
| [docs/PROJECT_CONTINUITY.md](docs/PROJECT_CONTINUITY.md) | A' — Situation / Evidence / Next useful step |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system is built |
| [docs/system_map/README.md](docs/system_map/README.md) | System Map — connections & authority |
| [docs/IMPLEMENTATION_TASKS.md](docs/IMPLEMENTATION_TASKS.md) | Roadmap, gaps, technical debt |
| [.jes/artifacts/cli_findings_post_catalog_bind_v1.md](.jes/artifacts/cli_findings_post_catalog_bind_v1.md) | Living CLI findings register (G9–G20) |
| [src/jarvis/README.md](src/jarvis/README.md) | Deeper product / flow reference |

## Tags

`v0.2.0` — H1–H4 handoffs closed; System Map at 0 RED. Still not a production CAD/FEM tool; physical catalogs remain thin.  
`checkpoint-continuity-polish` — Continuity Hardening + G10 materials/frame + CLI polish S1–S7 (G9-B, G16, G18, G17 partial, G12, G19); commit `15aa503`.  
`checkpoint-fn026-h4` — architectural checkpoint for the handoff stack.  
`v0.1.0-prototype` — first functional cut.
