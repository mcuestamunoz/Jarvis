# Jarvis System Map — Navigation Guide

**Version:** SYS-MAP-002 (split/navigability delta of SYS-MAP-001, reviewed PASS WITH NOTES)
**Date:** 2026-08-10
**Type:** As-is architecture documentation. Zero product behavior changes.

## How to navigate

```
Level 0/1 (whole system, human-legible)
  → JARVIS_SYSTEM_MAP.md

Registries (first-class entities, referenced by ID from everywhere else)
  → CONNECTIONS.md   (Canonical registry: 59 C-xxx — derived detail may repeat IDs; +8 forbidden apart. FN-024, 2026-08-10: C-042 fixed, C-105/C-106 added)
  → AUTHORITY.md      (decision → authority → forbidden, verified against code)
  → FLOWS.md          (FLOW-001…007 — reference user journeys, each step tied to C-xxx)
  → MISMATCHES.md      (doc↔code discrepancies + the FN-021 sticky-state lesson)

Visual companion (diagrams + interactive canvas source)
  → DIAGRAMS.md                      (mermaid + band index; mirrors 57 canonical)
  → jarvis-system-map.canvas.tsx     (filterable graph — 57 / 52 / 4 / 1 / +8)

Design (pre-implementation — handoff continuity)
  → HANDOFF_CONTEXT_DESIGN.md        (transversal contract framing for C-042/C-043/C-025; no code)

Level 2 (subsystem internals — modules, functions, local state)
  → 00_entry/ENTRY_MAP.md
  → 01_runtime/RUNTIME_MAP.md
  → 02_intent/INTENT_MAP.md
  → 03_acquisition/ACQUISITION_MAP.md
  → 04_engineering/ENGINEERING_MAP.md
  → 05_iteration/ITERATION_MAP.md
  → 06_calculation/CALCULATION_MAP.md
  → 07_simulation/SIMULATION_MAP.md
  → 08_continuity/CONTINUITY_MAP.md
  → 09_state/STATE_MAP.md
  → 10_llm/LLM_MAP.md
```

**Reading order for a new engineer:** `JARVIS_SYSTEM_MAP.md` first (get the whole-system shape), optionally `DIAGRAMS.md` for the visual rollup, then `FLOWS.md` (pick the user journey you care about), which will point you at specific `C-xxx` rows in `CONNECTIONS.md`, which will point you at a subsystem map for the module-level detail.

**Reading order for "is X connected to Y?":** go straight to `CONNECTIONS.md` and search for the `From`/`To` pair. If it's not there, check "Suspected missing edges" at the bottom of `CONNECTIONS.md` before assuming it doesn't exist — it may be a known gap already flagged, or it may genuinely be undocumented (fix by adding a row, evidence-first).

## Source-of-truth order (used throughout this tree)

```
1. Code
2. Tests
3. Runtime / CLI evidence
4. Architecture documentation
5. Continuity / JES contracts
```

Where code and prior documentation disagreed, the disagreement is recorded in `MISMATCHES.md` rather than silently resolved in either direction.

## Final taxonomy (after delta)

The provisional tree from the contract was kept with **one addition**: a `00_entry/` subsystem for the CLI/MCP adapter layer and the dual-dispatch entry seam (`orchestrator.handle` vs `orchestrator.handle_user_text`). This was not in the provisional list but is explicitly allowed by the contract ("Add adapters (`00_entry/`) for CLI/MCP if that clarifies Nivel 0") and is needed because the dual-dispatch hotspot (§1.4 of the old single-file map) is a Level-0-relevant fact, not merely a `01_runtime/` internal.

No other taxonomy changes were needed — the provisional 01–10 split matched the real module boundaries closely enough that merging or splitting further would have added navigation cost without new clarity. See the Taxonomy Delta table in the Implementation Report for the full before/after.

| Folder | Scope | Key modules |
|---|---|---|
| `00_entry` | CLI/MCP adapters, dual-dispatch seam | `adapters/cli/main.py`, `adapters/mcp/*.py`, `orchestrator.handle` vs `handle_user_text` |
| `01_runtime` | The turn dispatcher itself: `_handle_user_text_inner`'s checkpoint chain, `ActionRouter` | `core/orchestrator.py`, `core/action_router.py` |
| `02_intent` | Regex-based intent classification | `core/intent_resolver.py` |
| `03_acquisition` | "What's the next gap to declare" — mention resolution, Brief, wizards | `core/acquisition_target.py`, `core/acquisition_brief.py`, `core/param_definition_session.py`, `core/system_definition_session.py`, `core/motor_catalog_assist.py` |
| `04_engineering` | "What design goal is the user naming" + DSE | `core/goal_planner.py`, `core/design_explorer.py` |
| `05_iteration` | Free-text → concrete parameter mutation | `core/iterate_interactive_session.py`, `core/iterate_domain.py`, `core/mutation_engine.py`, `core/semantic_interpreter.py`, `core/interactive_session.py` (new-project wizard, same shape) |
| `06_calculation` | `current_parameters` → physical results | `core/calculation_engine.py`, `core/component_resolver.py`, `tools/*.py` |
| `07_simulation` | Physical results → feasibility verdict | `simulation/simulator.py`, `suggestions/suggestion_engine.py` (`flight_model.py`/`energy_model.py` are empty/unused, see `MISMATCHES.md` M-003) |
| `08_continuity` | Situation/Evidence/Next-step + BOM + phase + reasoning signals | `core/project_continuity.py`, `core/project_closure.py`, `core/phase_layer.py`, `core/reasoning_layer.py` |
| `09_state` | The persisted/runtime source of truth | `core/state_manager.py`, `workspace/workspace_manager.py`, `workspace/render_views.py`, `core/component_inference.py`, `core/component_writers.py`, `core/component_rules.py`, `schemas/*.py` |
| `10_llm` | The LLM boundary | `llm/llm_client.py`, `llm/prompt_builder.py`, `llm/response_parser.py`, `llm/action_policy.py`, `llm/semantic_intent_adapter.py`, `llm/ollama_client.py` |

## Maintenance rule

**Every future FN implementation report must cite the `C-xxx` connection(s) it creates or repairs**, and must update that row's `Status` in `CONNECTIONS.md` (e.g. 🔴 → 🟢) plus the corresponding entry in `MISMATCHES.md` if it closes a documented mismatch. Do not let this tree drift silently — if a change touches routing/authority/state ownership and the map isn't updated in the same cut, the next reader inherits a false picture, which is exactly the failure mode this map exists to prevent.

## Link

Contract: `.jes/artifacts/implementation_contract_sys_map_002.md`. Predecessor: `docs/JARVIS_SYSTEM_MAP.md` (SYS-MAP-001, now a stub redirecting here) and `.jes/artifacts/design_layer_connection_map.md` (superseded, historical A–E/H1–H5 sketch only).
