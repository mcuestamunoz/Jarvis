# Implementation Report — FN-026 (H4)

## Summary

Once a Goal Plan has an active `HandoffContext` (created by `_handle_engineering_intent`, C-105), naming one of that plan's levers — e.g. `"incrementa safety_factor"` after `"ayúdame a mejorar la estabilidad"` — now preseeds the Iterate wizard's `variable` slot before the wizard even opens. The wizard confirms the objective ("sí") and jumps straight to step 2, never asking "¿Qué quieres modificar?" for a lever the user already named. **C-043 closed (🔴→🟢). H1–H4 are now all implemented — the registry is 58🟢/0🔴/1🟡; only C-081 (H5, design-only) remains non-green.**

## Option chosen (A or B) + membership helper location

**Option A** (bind where Iterate starts / seeds from user text), as the contract preferred. A new pure helper, `handoff_matching.match_plan_lever(user_input, handoff_context) -> str | None`, lives in a small new module `core/handoff_matching.py` — not inside `goal_planner.py` (which is presently a clean, dependency-free pure catalog module; importing `iterate_domain`/`parameter_requirements` into it would be a new cross-module coupling this codebase's layering doesn't have elsewhere, the same reasoning FN-025 used to reject its own Option B), and not inside the LLM adapter (`semantic_intent_adapter.py`, which is a distinct, LLM-facing mechanism with its own confidence/grounding rules — conflating the two would blur "the user named a plan lever" with "the LLM proposed a variable").

`match_plan_lever` is called from a new orchestrator method, `_preseed_variable_from_handoff(action_request, user_input)`, invoked once — right before `self.handle(local_action_request)` — inside `_handle_user_text_inner`'s existing `intent in {"create_project","iterate","calculate","simulate"}` dispatch block, scoped to `intent == "iterate"` only.

## Behavior changed

- **New:** `core/handoff_matching.py::match_plan_lever(user_input, handoff_context) -> str | None`. For each lever in `handoff_context.levers`, tries (1) the full lever string, then (2) each of its `/`-separated tokens (stripped). A candidate counts only if it is both referenced (substring, normalized) in the user's text AND passes `iterate_domain._is_valid_variable` — the same closed-domain gate step 1 of the wizard already enforces. A match is resolved to its canonical name via the exact same chain `iterate_interactive_session._apply_answer` uses at step 1: `normalize_alias(candidate)` → `_VARIABLE_NORMALIZATION.get(...)  or  _fuzzy_normalize_variable(...)`. No parallel vocabulary.
- **New:** `orchestrator._preseed_variable_from_handoff(action_request, user_input) -> dict`. No-ops (returns the request unchanged) unless: `parameters.variable` is not already set (never overrides an existing resolver-set variable, e.g. `"componentes"`/`"material"` from the existing `resolve_action_request` keyword paths), an active `handoff_context` exists with `iterate_capability == "active"`, a project is loaded, `handoff.project_id` matches that project, and `match_plan_lever` finds a hit. Never reads or writes `dse_capability`. Never wipes or otherwise mutates the context — this is a pure read.
- **`orchestrator.py`'s `intent in {"create_project","iterate","calculate","simulate"}` dispatch:** for `intent == "iterate"` only, the resolved `local_action_request` is passed through `_preseed_variable_from_handoff` before `self.handle(...)`. `create_project`/`calculate`/`simulate` are untouched.
- Compound levers (e.g. `"per_motor_max_thrust_n / motors"` for `aumentar_payload`, `"total_power_w / motors"` for `mejorar_autonomia`) preseed only from their settable sibling token — `motors` is a valid alias of `motor_count`, so it preseeds; `total_power_w` is a derived/computed quantity with no `PARAMETER_REQUIREMENTS` entry, so `_is_valid_variable` rejects it and the wizard falls back to asking, exactly as if the user had typed `total_power_w` at step 1 manually.

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/handoff_matching.py` (new) | `match_plan_lever` pure helper. |
| `src/jarvis/core/orchestrator.py` | Import + `_preseed_variable_from_handoff` + one-line hook in the `iterate` dispatch. |
| `tests/test_fn026_lever_iterate_preseed.py` (new) | 12 tests (T1–T8 + 4 regressions). |
| `tests/test_fn025_help_goal_intent.py` | `test_iterate_lever_preseed_still_not_implemented` renamed to `test_iterate_lever_preseed_now_implemented` and inverted — it pinned the pre-FN-026 broken fallback; now locks in the fixed outcome (same precedent as FN-021→FN-022's test update). |
| `docs/system_map/CONNECTIONS.md`, `AUTHORITY.md`, `FLOWS.md`, `MISMATCHES.md`, `DIAGRAMS.md`, `jarvis-system-map.canvas.tsx`, `JARVIS_SYSTEM_MAP.md`, `01_runtime/RUNTIME_MAP.md`, `04_engineering/ENGINEERING_MAP.md`, `05_iteration/ITERATION_MAP.md` | System Map updated per §7 of the contract. |
| `docs/IMPLEMENTATION_TASKS.md` | FN-026 marked complete; FN-024/025 entries' forward-references to H4 updated. |

## Connections (C-043)

- **C-043**: 🔴 → 🟢 (Goal Plan lever → Iterate wizard preseed)
- Canonical registry: **59 unique `C-xxx`, unchanged count** — no new connection ID was needed; the fix reuses C-105 (`HandoffContext` creation) exactly as it already existed, adding only a new *reader*.
- Rollup moved **57🟢/1🔴/1🟡 → 58🟢/0🔴/1🟡**. `DIAGRAMS.md` and `jarvis-system-map.canvas.tsx` re-verified to mirror the 59-ID set and new rollup exactly (zero symmetric difference, checked programmatically). **H1–H4 all closed — 0 RED remains in the entire registry.**
- **C-081** — status unchanged (🟡, H5), explicitly not touched. It is now the sole non-green edge in the registry.

## Tests run

```
pytest tests/test_fn026_lever_iterate_preseed.py tests/test_fn025_help_goal_intent.py -v   → 22 passed
pytest tests/test_assisted_acquisition.py tests/test_fn011_propulsion_declare_routing.py \
       tests/test_fn013_active_block_declare_routing.py tests/test_fn014_acquisition_target_idle.py \
       tests/test_fn015_pending_help.py tests/test_fn016_navigation_parse_safety.py \
       tests/test_fn020_completeness_coherence.py tests/test_fn021_session_hygiene.py \
       tests/test_fn022_engineering_intent.py tests/test_fn023_next_step_help.py \
       tests/test_fn024_handoff_context_dse.py tests/test_fn025_help_goal_intent.py \
       tests/test_fn026_lever_iterate_preseed.py \
       tests/test_goal_planner.py tests/test_iterate_session.py tests/test_orchestrator.py \
       tests/test_llm_integration.py tests/test_llm_response_parser.py -q                  → 350 passed
pytest -q (full suite)                                                                      → 1591 passed (1579 baseline + 12 new)
```
0 failures anywhere. Product files touched: exactly `src/jarvis/core/handoff_matching.py` (new) and `src/jarvis/core/orchestrator.py`.

## Blast-radius table

| Path | Expected effect | Evidence |
|---|---|---|
| Plan → named lever → confirm → iterate | `variable` preseeded, step 1 skipped | `test_plan_lever_confirm_preseeds_variable` |
| No active context / bare iterate phrase | Unchanged — wizard still asks | `test_no_context_still_asks` |
| Valid iterate variable, but ∉ current plan's levers | No preseed, honest fallback | `test_valid_variable_outside_plan_levers_not_preseeded` |
| Stale cross-project `handoff_context` | No preseed (project_id guard) | `test_cross_project_stale_context_not_preseeded` |
| After DSE capability consumed | Preseed still works — `dse_capability`/`iterate_capability` are independent | `test_preseed_works_after_dse_consumed` |
| FN-025 help+goal path → named lever | Preseed works identically | `test_help_plus_goal_then_lever_preseed` |
| Compound lever, settable sibling token (`motors`) | Preseeds | `test_compound_lever_valid_sibling_token_preseeds` |
| Compound lever, derived/non-settable token (`total_power_w`) | No preseed, honest fallback | `test_compound_lever_derived_token_not_preseeded` |
| FN-022/024/025 regressions | Unaffected | `test_fn022_bare_intention_unaffected`, `test_fn024_explore_bind_unaffected`, `test_fn025_help_plus_goal_unaffected` |
| Existing keyword-based iterate preseed (`"definir componentes"`) | Unaffected — `_preseed_variable_from_handoff` never overrides an already-set `variable` | `test_iterate_without_active_context_unaffected` |

## Explicitly deferred

- H5 (C-081 — Continuity margin thread): untouched, still design-only.
- Create→BOM, Conversation Engine, Step D, dual-dispatch refactor: not touched.
- Optional polish from the contract ("mark the matched lever consumed/reconciled after a successful mutation apply") — not implemented. Not required to close C-043; adding it now would be scope beyond the contract's minimum, and the Decision Log's per-lever reconciliation semantics deserve their own review rather than a rushed add-on here.
- No opportunistic hygiene cleanup performed.

## Risks

- `match_plan_lever`'s substring-containment matching is intentionally narrow — it matches the literal lever token (e.g. `safety_factor`) or its slash-split pieces, not a full synonym/NLP expansion (e.g. a Spanish phrase like `"factor de seguridad"` typed without the underscore form does not match `"safety_factor"` as a substring). This is the contract's own stated scope ("reuse existing iterate alias / `_is_valid_variable` / `normalize_alias` machinery... do not invent a parallel vocabulary") — flagged for awareness, not considered a defect; a synonym-aware version would be a separate, larger design decision.
- Compound-lever resolution mirrors an existing quirk in `_apply_answer`: an alias-only canonical (e.g. `"motors"`, an alias of `motor_count` but not a `concept_alias`) resolves through `_fuzzy_normalize_variable`'s fallback-to-raw-input path and ends up stored as the literal string `"motors"`, not the canonical `"motor_count"`. This is pre-existing, unchanged behavior (verified: an unmodified wizard run typing `"motors"` at step 1 produces the identical result) — `match_plan_lever` deliberately reuses the same chain so its output is always bit-identical to what typing that token manually at step 1 would produce.
- System Map footprint for this cut spans 10 files (similar scale to FN-024/FN-025) — all cross-checked programmatically for ID/count/rollup consistency (`CONNECTIONS.md` ↔ `DIAGRAMS.md` ↔ `jarvis-system-map.canvas.tsx`, zero symmetric difference), but a manual skim by Cursor is still worthwhile.
