# Implementation Report — FN-024 (H1+H2)

## Summary

`"explora opciones"` after a Goal Plan now runs DSE for that plan's `goal_key` — 0 LLM — via a small, capability-scoped, project-scoped, runtime-only `HandoffContext`. C-042 fixed (🔴→🟢). H2 (CTA honesty) closed as a *consequence* of H1, not a separate text change: the CTA's `'explora opciones'` promise is now true by construction, since a fresh active context is always created immediately before the CTA is built. H3, H4, H5, and Create→BOM are untouched, as required.

## Design citation

- `docs/system_map/HANDOFF_CONTEXT_DESIGN.md` — Decision log: **§5 CLOSED, Hybrid Operation-Scoped Context** (2026-08-10).
- Lifecycle implemented: create-on-plan / replace-on-new-plan / bind-and-consume-DSE-capability-only-on-successful-explore / project-scoped via a `project_id` guard proven at the one read site, not an enumerated "clear on switch" list.
- Storage: runtime-only (`InteractiveSessionState.handoff_context`), excluded from `state_manager._PERSISTED_SESSION_FIELDS` — same tier as `last_exploration_result` (C-046), the precedent both this design doc and the predecessor map pointed to.
- Explicit rejection of a naive `last_engineering_goal: str` honored: `HandoffContext` is a typed model with `goal_key`/`levers`/`origin`/`dse_capability`/`iterate_capability`/`project_id`, not a bare string.

## Behavior changed

- `_handle_engineering_intent(goal_key)`: now also creates/replaces `session.handoff_context` (fresh, `dse_capability="active"`, `levers` from `GOAL_STRATEGIES[goal_key]`, current `project_state.project_id`) immediately before building the CTA. Plan text and CTA copy themselves are byte-identical to FN-022 — no text change was needed.
- `_handle_explore(goal_key, ...)`: when `goal_key is None` (bare "explora opciones"), now checks `session.handoff_context` before falling to `_handle_analyze`. Three outcomes:
  1. Context matches current project and `dse_capability == "active"` → bind `goal_key` from context, run DSE, then consume DSE capability only (`goal_key`/`levers`/`iterate_capability` untouched).
  2. Context matches current project but `dse_capability == "consumed"` → deterministic 0-LLM message ("Ya exploré opciones para «X»...") instead of a silent re-bind or an LLM call.
  3. No context, wrong project, or unrecognized goal → unchanged pre-FN-024 fallback to `_handle_analyze`.
- Explicit-goal explores (`"optimiza para estabilidad"`) are entirely unaffected — the new logic only runs inside the `goal_key is None` branch; the "simplest" option from the contract's §4.2 was chosen: context is never consumed or overwritten by an explicit-goal explore, even if it happens to match the context's `goal_key`.

## Files changed

| File | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | New `HandoffContext` model; new `InteractiveSessionState.handoff_context` field. |
| `src/jarvis/core/orchestrator.py` | `_handle_engineering_intent` creates/replaces context (C-105); `_handle_explore` binds/consumes (C-106); new imports (`GOAL_STRATEGIES`, `HandoffContext`). |
| `src/jarvis/core/state_manager.py` | Comment only — documents `handoff_context`'s intentional exclusion from `_PERSISTED_SESSION_FIELDS` (no code change; it was already excluded by construction, being an allowlist). |
| `tests/test_fn024_handoff_context_dse.py` (new) | 11 tests (T1–T9 + 2 regression checks). |
| `docs/system_map/CONNECTIONS.md`, `DIAGRAMS.md`, `jarvis-system-map.canvas.tsx`, `FLOWS.md`, `MISMATCHES.md`, `JARVIS_SYSTEM_MAP.md`, `04_engineering/ENGINEERING_MAP.md`, `09_state/STATE_MAP.md`, `README.md` | System Map updated per §5/§8 of the contract (see "Connections" below). |
| `docs/IMPLEMENTATION_TASKS.md` | FN-024 marked complete. |

## Connections

- **C-042**: 🔴 → 🟢 (Plan → DSE binding now works)
- **C-105** (new): `_handle_engineering_intent` success → create/replace `handoff_context`
- **C-106** (new): active `handoff_context` → `_handle_explore` goal bind
- Canonical registry: **57 → 59** unique `C-xxx` (55🟢/3🔴/1🟡). `DIAGRAMS.md` and `jarvis-system-map.canvas.tsx` re-verified to mirror the new 59-ID set and 55/3/1 rollup exactly (zero symmetric difference, checked programmatically).
- **C-043, C-025/C-044, C-081** — status unchanged (🔴/🟡), explicitly not touched.

## Tests run

```
pytest tests/test_fn024_handoff_context_dse.py -v          → 11 passed
pytest tests/test_fn020_completeness_coherence.py tests/test_fn021_session_hygiene.py \
       tests/test_fn022_engineering_intent.py tests/test_fn023_next_step_help.py \
       tests/test_fn024_handoff_context_dse.py tests/test_goal_planner.py \
       tests/test_iterate_session.py tests/test_orchestrator.py -q  → 212 passed
pytest -q (full suite)                                       → 1569 passed (1558 baseline + 11 new)
```
0 failures anywhere. `git status --short -- src/` confirmed to contain exactly `orchestrator.py`, `state_manager.py` (comment-only), `action_schema.py` — no other product file touched.

## Blast-radius table (proof, not assertion)

Verified via `grep -rn "handoff_context" src/jarvis --include="*.py"` — the **only** two functions in the entire `src/` tree that reference the field are `_handle_engineering_intent` (write) and `_handle_explore` (read/partial-write). Every other row below is "keep" **by construction** (there is no code path there that could touch it), not by having remembered to add a no-op.

| Path | Context effect | Evidence (test or code pointer) |
|---|---|---|
| `_handle_engineering_intent` (new plan) | create/replace | `test_plan_creates_active_handoff_context`, `test_new_engineering_intent_replaces_context` |
| bare `"explora opciones"` (context active) | bind + consume DSE capability only | `test_bare_explore_binds_context_and_consumes_dse_capability_only` — asserts `dse_capability=="consumed"` **and** `goal_key`/`levers`/`iterate_capability` still present |
| bare `"explora opciones"` (capability already consumed) | keep (deterministic message, no re-bind) | `test_second_bare_explore_after_consumed_does_not_rebind` |
| explicit `"optimiza para …"` | keep (untouched — "simplest" option, contract §4.2) | `test_explicit_explore_domain_still_works_context_untouched` |
| `project_status` / Continuity | keep | `test_project_status_does_not_clear_handoff_context` |
| `apply_exploration` (`_handle_apply_exploration`) | keep (default, per Decision log) | Grep-proof: `_handle_apply_exploration` contains zero references to `handoff_context` — structurally cannot touch it |
| project switch/load (different `project_id`) | invalidate (inert, not physically cleared — proven via guard) | `test_handoff_context_inert_across_project_boundary` — a context bound to project A, injected into an orchestrator on project B, correctly falls through to `_handle_analyze` exactly as if no context existed |
| Never persisted / never restored from snapshot | invalidate across process restart | `test_handoff_context_never_persisted` — asserts `"handoff_context" not in _PERSISTED_SESSION_FIELDS` |
| Iterate path (untouched, no H4 yet) | keep | Grep-proof: `iterate_interactive_session.py`, `mutation_engine.py`, `semantic_interpreter.py` contain zero references to `handoff_context` — structurally cannot touch it. `HandoffContext.levers`/`iterate_capability` exist and are populated (`test_plan_creates_active_handoff_context` asserts `hc.levers` non-empty) but nothing reads them yet — exactly the "ready for H4, not implemented by H4" contract requirement. |

## Explicitly deferred

- H3 (C-025/C-044 — "ayúdame" + named goal → analyze): no intent-precedence change made.
- H4 (C-043 — lever → iterate preseed): `HandoffContext.levers`/`iterate_capability` are populated and left untouched by every FN-024 code path, ready for a future consumer, but no consumer was implemented.
- H5 (C-081 — Continuity margin thread): untouched, still design-only per `MISMATCHES.md`.
- Create→BOM, Conversation Engine, Step D, dual-dispatch refactor: not touched.
- No opportunistic hygiene cleanup performed (SYS-MAP-003's `HYG-xxx` catalog is unaffected).

## Risks

- `HandoffContext.levers` currently stores the *unprioritized* `GOAL_STRATEGIES[goal_key]` order (membership-only use for now) rather than the `_prioritize_strategies`-reordered display order shown in the plan text. Harmless for H1 (order-independent), but a future H4 implementation should decide whether lever *order* matters for anything (e.g. picking the "first" lever when a user names none) — flagged, not resolved here.
- The "already explored" deterministic message (§4.3) is new user-facing copy, not present in any prior FN's test coverage; low risk (fully covered by `test_second_bare_explore_after_consumed_does_not_rebind`), but worth a quick manual CLI smoke by the Engineer if desired.
- System Map now carries FN-024's changes across 8 files (`CONNECTIONS.md`, `DIAGRAMS.md`, canvas, `FLOWS.md`, `MISMATCHES.md`, `JARVIS_SYSTEM_MAP.md`, 2 subsystem maps) — larger doc footprint than a typical FN; all cross-checked programmatically for ID/count consistency, but a manual skim by Cursor is still worthwhile given the volume.
