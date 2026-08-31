# 09 — State

**Purpose.** `ProjectState` (disk) + `InteractiveSessionState`/`RuntimeState` (session) — the single source of engineering truth, and the layer everything else reads and writes through.

**Inbound:** C-091 (component writes), C-092 (session writes), C-071 (calc/sim results). **Outbound:** C-093/C-094 (persisted to disk).

## Key modules

| Path | Role |
|---|---|
| `core/state_manager.py` | `StateManager` — `load`, `load_active_project`, `record_action`, `get_runtime_session`/`set_runtime_session`/`clear_runtime_session`, snapshot persistence |
| `workspace/workspace_manager.py` | `WorkspaceManager` — `create_project_workspace`, `save_state`, `save_calculation`/`save_simulation`/`save_iteration_snapshot`, `render_views`, `resolve_state_path` |
| `workspace/render_views.py` | `render_estado_actual`, `render_sistema` — `state.json` → markdown views (uses `project_closure`'s BOM, C-082) |
| `workspace/file_writer.py` | Physical file I/O primitives |
| `core/component_inference.py` | `infer_component[s]`, `infer_component_for_key` (FN-019) — free text → `ComponentSpec`, pure |
| `core/component_writers.py` | `set_frame_material`, `set_control_component`, `set_battery_component`, `set_motor_component`, `set_propeller_component`, `apply_components_delta` — **the only** legal writers of `design_properties.components[key]` |
| `core/component_rules.py` | `ComponentRule`, `ComponentRuleRegistry` — the domain-agnostic matching primitive |
| `domains/aerial.py`, `domains/ground.py` | Data: keyword tables + property extractors per domain |
| `schemas/action_schema.py`, `schemas/state_schema.py` | `ProjectState`, `InteractiveSessionState`, `OrchestratorMode`, `ComponentSpec`, `PropertyValue`, `RuntimeState`, `CatalogRef` |

## `OrchestratorMode` (5 values, no more)

`IDLE`, `CREATE_PROJECT_INTERACTIVE`, `ITERATE_INTERACTIVE`, `DEFINE_MISSING_PARAMETERS`, `SYSTEM_DEFINITION`. Full transition diagram: `JARVIS_SYSTEM_MAP.md` §4 (predecessor doc; reproduced in `01_runtime/RUNTIME_MAP.md`'s checkpoint table). There is **no** `EXPLORING`/`PLANNING` mode — `explore_design_space`, `apply_exploration_result`, `engineering_intent` are all single-turn actions dispatched from IDLE with no dedicated mode.

## `InteractiveSessionState` fields (complete list)

`mode`, `step`, `project_draft`, `iteration_draft`, `memory_context`, `semantic_state`, `pending_entities`, `motor_suggestions`, `pending_param_definitions`, `collected_params`, `param_definition_reason`, `pending_define_missing`, `pending_missing_params`, `pending_missing_reason`, `dismissed_suggestions`, `last_suggested_action`, `last_exploration_result`, `pending_structural_change`, `handoff_context` (FN-024, new).

**`handoff_context: HandoffContext | None`** (FN-024, `schemas/action_schema.py`) — "which engineering goal did we just plan for," the gap `MISMATCHES.md`'s design appendix (H1) discussed, now filled for the DSE consumer (C-042/C-105/C-106). Shaped exactly per the `last_exploration_result` precedent this map already pointed to: runtime-only, capability-scoped (`dse_capability`/`iterate_capability` tracked independently so a successful DSE bind consumes only the DSE side), project-scoped (`project_id` field, checked at every read — the actual "invalidate across a project boundary" mechanism, proven rather than assumed via a clear-on-switch hook). Written only by `orchestrator._handle_engineering_intent` (create/replace); read only by `orchestrator._handle_explore` (bind + partial consume). Not a sticky `last_engineering_goal` string — see `MISMATCHES.md`'s explicit rejection of that shape, question 4.

## The FN-021 invariant (enforced here)

```text
mode == DEFINE_MISSING_PARAMETERS and _next_pending_block(project_state) is None
  ⇒ clear_runtime_session() → IDLE, all pending_* emptied
```
Implemented at `orchestrator._set_pending_next_block`'s gate (calls `StateManager.clear_runtime_session`), not inside `state_manager.py` itself — `StateManager` only provides the mechanism (`clear_runtime_session`), the orchestrator owns *when* to invoke it. See `MISMATCHES.md`'s "sticky-state lesson" section for why this distinction matters for future handoff-context design.

## `parsed_constraints` + requirements (IC 1)

`ProjectState.parsed_constraints` is derived on every load/save from `current_parameters["restrictions"]` and `objective` via `state_schema._parse_constraints`. **Explicit-none:** closed phrases (`"no"`, `"ninguna"`, `"sin restricciones"`, …) satisfy `requirements_declared()` without adding fake numeric keys — `parsed_constraints` stays `{}`. **G26:** mid-session updates to `restrictions` go through `param_definition_session.apply_and_recalculate` (or orchestrator routing into it); save via `ProjectState.model_copy` re-derives `parsed_constraints`. Derived params (`autonomia`, etc.) must not be written directly — `is_derived` gate in param session mirrors `semantic_intent_adapter`.

## Mirrored parameters (invariant, documented in `system_architecture_catalog.py`)

`battery_capacity_wh`, `battery_mass_kg`, `battery_cell_count`, `motor_power_w`, `motor_kv_rating`, `propeller_diameter_in`, `propeller_pitch_in` must **never** be written directly to `current_parameters` — only via their designated `component_writers` function. `motor_count` is the one deliberate exception (settable by both component and numeric wizard). Enforced by convention + `tests/test_d4_param_gatekeeper.py`, not by a runtime guard.

## LLM

NO — zero LLM involvement anywhere in this subsystem.

## Known issues owned by this subsystem

None currently open (FN-021 closed the one open issue this subsystem had).

## Tests

`tests/test_d4_param_gatekeeper.py`, `tests/test_project_closure_v1.py`, `tests/test_project_coherence.py`, `tests/test_fn020_completeness_coherence.py`, component-writer-specific tests (`test_frame_component.py`, `test_battery_component.py`, `test_motor_component.py`, `test_control_component.py`), `tests/test_fn021_session_hygiene.py`, **`tests/test_requirements_closure.py`**, **`tests/test_catalog_bind_v1.py`**.
