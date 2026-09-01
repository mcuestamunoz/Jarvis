# 04 — Engineering

**Purpose.** "What design goal is the user naming" + Design Space Exploration. This subsystem owned the map's three headline broken edges; C-042 (FN-024), C-025/C-044 (FN-025), and C-043 (FN-026) are now all fixed — **0 RED edges remain**.

**Inbound:** C-020 (from Intent), C-040 (from Runtime's FN-022 gate), C-025/C-044 (from Runtime's FN-025 help-goal gate). **Outbound:** C-045/C-046 (DSE run/apply), C-105/C-106 (Handoff Context create/bind, FN-024), C-043 (Handoff Context → Iterate preseed, FN-026).

## Key modules

| Path | Role |
|---|---|
| `core/goal_planner.py` | `GOAL_STRATEGIES`, `detect_goal`, `is_engineering_intention`, `looks_like_numeric_mutate`, `format_goal_plan`, `_prioritize_strategies`, `get_goal_context_for_llm` |
| `core/design_explorer.py` | `DesignExplorer`, `EXPLORATION_GRIDS`, `GOAL_LABELS` — in-memory only, never mutates |
| `schemas/action_schema.py::HandoffContext` | FN-024 (H1) — the operation-scoped, runtime-only bridge between a Goal Plan and its DSE (and, later, Iterate) consumers. Not part of `goal_planner.py`/`design_explorer.py` themselves (it's a schema type, owned by `orchestrator.py`'s create/bind logic), but conceptually belongs to this subsystem. FN-025 added a *second entry point* into the same create path (C-105) — help+goal phrases — without touching `HandoffContext` itself at all. |
| `core/intent_resolver.py::ANALYZE_HELP_PATTERNS`/`ANALYZE_VERB_PATTERNS` | FN-025 — lives in `02_intent`, referenced here because it's what lets `orchestrator.py` distinguish "ayúdame + goal" from a real analyze verb before falling to `_handle_analyze`. |
| `core/handoff_matching.py::match_plan_lever` | FN-026 (H4) — pure helper, resolves a user-referenced `handoff_context.levers` entry to a canonical iterate variable name. Owned here (reads `HandoffContext`), consumed from `01_runtime`/`orchestrator._preseed_variable_from_handoff`; see also `05_iteration`. |

## Important functions (Level 2)

- `goal_planner.detect_goal(user_input) -> goal_key | None` — substring match against `_GOAL_KEYWORDS`, one 4-goal table (`aumentar_payload`, `mejorar_autonomia`, `reducir_masa`, `mejorar_estabilidad`). FN-022 filled keyword gaps for all 4 goals, including mapping thrust/empuje language onto `mejorar_estabilidad` (documented primary-mapping decision, not an ad-hoc thrust branch — see FN-022's report).
- `goal_planner.is_engineering_intention(user_input) -> goal_key | None` — `detect_goal` + `looks_like_numeric_mutate` guard (any digit present ⇒ defer to iterate). This is the function C-040 calls.
- `goal_planner.format_goal_plan(goal_key, sim_context) -> str` — deterministic plan text; reorders strategies via `_prioritize_strategies` when `sim_context` (margin/warnings) is available. **Display order only** — `GOAL_STRATEGIES[goal_key]`'s own (unprioritized) order is what `_handle_engineering_intent` uses to populate `HandoffContext.levers`, since membership doesn't depend on display order.
- `orchestrator._handle_engineering_intent(goal_key) -> dict` — builds the plan + CTA **and (FN-024) creates/replaces `session.handoff_context`** (C-105) with a fresh `dse_capability="active"` context before the CTA is built — this is *why* the CTA's `"... o 'explora opciones' ..."` promise is now true by construction (closes H2/M-002 as a side effect, not a separate text change). **FN-025 reuses this exact function unchanged** as the destination for the help+goal gate — no second plan builder, no second context writer.
- `orchestrator`'s `intent == "analyze"` branch (FN-025, H3) — when the match came from `IntentResolver.ANALYZE_HELP_PATTERNS` specifically (not the verb group), calls `is_engineering_intention`; a detected goal routes here (`_handle_engineering_intent`), no goal routes to `_handle_project_status`. Lives in `01_runtime`/`02_intent` territory more than this subsystem's own files, but is the reason C-025/C-044 are now 🟢.
- `orchestrator._handle_explore(goal_key, user_input, llm_interface) -> dict` — DSE entry. `goal_key is None` → (FN-024) tries to bind from `session.handoff_context` first (C-106); only falls to `_handle_analyze` when no bindable context exists (none, wrong project, or unknown goal) — same honest fallback as before FN-024, now a narrower case than it used to be. **MOP-4 (v0.3.4):** appends one honesty line when live `propulsion_resolution.voltage_validated == false`.
- `DesignExplorer.explore(project_state, goal_key) -> ExplorationResult` — pure, in-memory, applies `EXPLORATION_GRIDS[goal_key]` deltas via `component_writers.apply_components_delta`, ranks viable candidates. **MOP-3 (v0.3.4):** params-only baseline/grid reads live `project_state.current_parameters`; `normalized_state` remains the substrate for catalog/component-delta candidates only.
- `orchestrator._handle_apply_exploration()` — the one DSE-adjacent path that writes `ProjectState`, consuming `session.last_exploration_result` (C-046) — **the precedent FN-024's `HandoffContext` design followed**: runtime-only, capability-scoped, consumed by its own explicit next action.

## Local state touched

- `InteractiveSessionState.last_exploration_result` (write: `_handle_explore`; read+clear-by-consumption: `_handle_apply_exploration`) — unchanged by FN-024.
- `InteractiveSessionState.handoff_context` (FN-024, new) — write: `_handle_engineering_intent` (create/replace, C-105); read: `_handle_explore` (C-106, project_id + `dse_capability` guarded) and, since FN-026, `_preseed_variable_from_handoff` (C-043, project_id + `iterate_capability` guarded); partial-write: `_handle_explore` sets `dse_capability="consumed"` on a successful bind+explore, leaving `goal_key`/`levers`/`iterate_capability` untouched — `_preseed_variable_from_handoff` never writes to the context at all (pure read). Never persisted (`state_manager._PERSISTED_SESSION_FIELDS` excludes it).

## LLM

NO for `goal_planner.py`, `design_explorer.py`, and the `HandoffContext` create/bind logic itself (zero I/O, zero LLM import, verified). YES *indirectly* only when no context can bind: `_handle_explore` falls to `_handle_analyze` when `goal_key is None` and no active same-project context exists, and Intent routes genuine analytical-verb phrases (`"analiza"`/`"evalúa"`/`"revisa"`) to `analyze` — help+goal phrases (FN-025) no longer do, and bare help with no goal now routes to `project_status`, not the LLM.

## Known issues owned by this subsystem

- ~~**C-042** 🔴~~ → **🟢 FIXED (FN-024)** — Goal Plan → DSE now binds via `handoff_context` (C-105/C-106).
- ~~**C-044** 🔴~~ → **🟢 FIXED (FN-025)** — "ayúdame" + named goal → analyze (shared ownership with `02_intent`; same root cause as C-025) now routes to `_handle_engineering_intent` instead.
- ~~**C-043** 🔴~~ → **🟢 FIXED (FN-026)** — Goal Plan lever → Iterate preseed (shared ownership with `05_iteration`), via `handoff_matching.match_plan_lever` + `orchestrator._preseed_variable_from_handoff`.

**No open issues remain in this subsystem.** H1–H4 are all closed (FN-024/FN-025/FN-026, see `MISMATCHES.md`). H5 (C-081) belongs to `08_continuity`, not here.

## Tests

`tests/test_goal_planner.py`, `tests/test_fn022_engineering_intent.py`, `tests/test_fn024_handoff_context_dse.py` (T1–T9, `HandoffContext` create/bind/consume, cross-project invalidation, CTA honesty smoke), `tests/test_fn025_help_goal_intent.py` (T1–T8 + 2 regressions, help+goal → plan, bare help → Continuity, real-analyze-verb precedence), `tests/test_fn026_lever_iterate_preseed.py` (T1–T8, lever → Iterate `variable` preseed, compound-lever token matching, cross-project/DSE-consumed independence), **`tests/test_dse_motor_op_dual_truth.py`** (v0.3.4 explore/apply OP coherence).
