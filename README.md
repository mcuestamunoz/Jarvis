# Jarvis

**v0.1 prototype**

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

## What v0.1 includes

- Guided / direct `create_project`
- Component definition in natural language (motors, frame, battery, propellers, …)
- Deterministic `calculate` and `simulate` with history + Markdown views
- Controlled `iterate` and design-space explore / apply (DSE)
- CLI and MCP adapters
- Curated material & motor library (small; matching by KV — see debt **D8**)

## Docs

| Doc | Role |
|-----|------|
| [VISION.md](VISION.md) | Product contract (non-technical) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system is built |
| [docs/IMPLEMENTATION_TASKS.md](docs/IMPLEMENTATION_TASKS.md) | Roadmap, gaps, technical debt |
| [src/jarvis/README.md](src/jarvis/README.md) | Deeper product / flow reference |

## Tag

`v0.1.0-prototype` — first functional cut. Not a production CAD/FEM tool.
