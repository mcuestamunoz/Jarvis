# Implementation Report — FN-025 (H3)

## Summary

`"ayúdame a mejorar la estabilidad"` (and any help-verb phrase naming a real engineering goal) now routes to the same deterministic Goal Plan path FN-022 already uses — 0 LLM — entering/refreshing the existing `HandoffContext` via the existing C-105 creation path. C-025 and C-044 both fixed (🔴→🟢, same root cause, one fix). H3 closed. FN-023's next-step-help precedence, FN-022's bare-intention gate, and FN-024's DSE bind are all unaffected — verified, not assumed. **C-043 (H4) is now the only remaining RED edge in the entire 59-connection registry.**

## Option chosen (A or B) + why

**Option A** (orchestrator-side gate), as the contract preferred. The fix lives entirely in `orchestrator.py`'s `intent == "analyze"` branch, reusing a small data-only split in `intent_resolver.py` (`ANALYZE_PATTERNS` → `ANALYZE_VERB_PATTERNS` + `ANALYZE_HELP_PATTERNS`, same union, zero change to `resolve_intent`'s own classification for any existing phrase). Option B (teaching `resolve_intent` itself to reach into `goal_planner` before returning `"analyze"`) was rejected: it would blur intent *classification* (a pure regex concern) with goal *detection* (a different, already-separate authority), and would have required `intent_resolver.py` to import `goal_planner.py` — a new cross-module coupling this codebase's layering doesn't currently have anywhere else. Keeping the split as plain pattern data in `intent_resolver.py`, and the goal-aware decision entirely in `orchestrator.py` (which already imports both modules), is the smaller, clearer change — consistent with how C-040 (FN-022) already does exactly this same shape of check.

## Behavior changed

- `intent_resolver.py`: `ANALYZE_PATTERNS` is now `ANALYZE_VERB_PATTERNS + ANALYZE_HELP_PATTERNS` — two new named tuples, same concatenated content as before, so every existing `_matches_any(normalized, self.ANALYZE_PATTERNS)` call (i.e. `resolve_intent` itself) is byte-for-byte unaffected.
- `orchestrator.py`'s `intent == "analyze"` branch: before dispatching to `_handle_analyze`, checks whether the match came from `ANALYZE_HELP_PATTERNS` specifically and *not* `ANALYZE_VERB_PATTERNS` (a real analytical verb always wins, even combined with a help word — `"ayúdame, analiza el margen"` stays analyze). If so:
  - `goal_planner.is_engineering_intention(user_input)` (same authority as C-040) finds a goal → routes to `_handle_engineering_intent(goal_key)` — the exact same function FN-022/024 use, creating/replacing `handoff_context` via C-105.
  - No goal detected (bare `"ayúdame"`) → routes to `_handle_project_status()` instead of `_handle_analyze` — Continuity answers "what's next" instead of the LLM inventing a target.
  - Neither condition → unchanged, falls to `_handle_analyze` exactly as before.
- FN-023's `GUIDANCE_PATTERNS` (checked earlier in `_resolve_strong_action_intent`, before ANALYZE) are completely untouched — `"ayúdame con el siguiente paso"` resolves to `"project_status"` *before* `resolve_intent` even returns, so this new branch never sees it. Verified, not assumed (`test_fn023_next_step_help_still_project_status`).

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/intent_resolver.py` | `ANALYZE_PATTERNS` split into `ANALYZE_VERB_PATTERNS`/`ANALYZE_HELP_PATTERNS` (data only, same union). |
| `src/jarvis/core/orchestrator.py` | New logic inside the existing `intent == "analyze"` branch. |
| `tests/test_fn025_help_goal_intent.py` (new) | 10 tests (T1–T8 + 2 regression checks). |
| `docs/system_map/CONNECTIONS.md`, `AUTHORITY.md`, `FLOWS.md`, `MISMATCHES.md`, `DIAGRAMS.md`, `jarvis-system-map.canvas.tsx`, `JARVIS_SYSTEM_MAP.md`, `01_runtime/RUNTIME_MAP.md`, `02_intent/INTENT_MAP.md`, `04_engineering/ENGINEERING_MAP.md` | System Map updated per §7 of the contract. |
| `docs/IMPLEMENTATION_TASKS.md` | FN-025 marked complete. |

## Connections (C-025, C-044)

- **C-025**: 🔴 → 🟢 ("ayúdame" + named goal → Intent → analyze, now redirected before reaching `_handle_analyze`)
- **C-044**: 🔴 → 🟢 (same finding, Engineering-side listing) — cross-referenced, counted once
- Canonical registry: **59 unique `C-xxx`, unchanged count** — no new connections were needed; both fixes reuse C-040 (`is_engineering_intention` → `_handle_engineering_intent`) and C-105 (context create) exactly as they already existed.
- Rollup moved **55🟢/3🔴/1🟡 → 57🟢/1🔴/1🟡**. `DIAGRAMS.md` and `jarvis-system-map.canvas.tsx` re-verified to mirror the 59-ID set and new rollup exactly (zero symmetric difference, checked programmatically).
- **C-043** — status unchanged (🔴), explicitly not touched. It is now the sole remaining RED edge in the registry.

## Tests run

```
pytest tests/test_fn025_help_goal_intent.py -v                → 10 passed
pytest tests/test_assisted_acquisition.py tests/test_fn011_propulsion_declare_routing.py \
       tests/test_fn013_active_block_declare_routing.py tests/test_fn014_acquisition_target_idle.py \
       tests/test_fn015_pending_help.py tests/test_fn016_navigation_parse_safety.py \
       tests/test_fn020_completeness_coherence.py tests/test_fn021_session_hygiene.py \
       tests/test_fn022_engineering_intent.py tests/test_fn023_next_step_help.py \
       tests/test_fn024_handoff_context_dse.py tests/test_fn025_help_goal_intent.py \
       tests/test_goal_planner.py tests/test_iterate_session.py tests/test_orchestrator.py \
       tests/test_llm_integration.py tests/test_llm_response_parser.py -q  → 338 passed
pytest -q (full suite)                                          → 1579 passed (1569 baseline + 10 new)
```
0 failures anywhere. `git status --short -- src/` confirmed to contain exactly `intent_resolver.py` and `orchestrator.py` — no other product file touched.

## Blast-radius table

| Path | Expected effect | Evidence |
|---|---|---|
| help + goal (`"ayudame a mejorar la estabilidad"`) | → `engineering_intent` + C-105 context create | `test_help_plus_goal_routes_to_engineering_intent`, `test_help_plus_goal_creates_handoff_context`, `test_help_plus_different_goal_generic` (second goal, generic over `goal_key`) |
| FN-023 next-step help (`"ayudame con el siguiente paso"`) | → `project_status` unchanged | `test_fn023_next_step_help_still_project_status` — never reaches the new branch at all (GUIDANCE wins first in `resolve_intent`, by construction) |
| bare `"ayudame"` (no goal) | → Continuity, not LLM goal invention | `test_bare_ayudame_routes_to_project_status_not_llm` |
| FN-022 bare iterate intention (`"aumentar el empuje"`, no help verb) | unchanged | `test_fn022_bare_intention_unchanged` — this phrase never enters the `intent == "analyze"` branch at all (resolves to `"iterate"`) |
| FN-024 `"explora opciones"` bind | unchanged | `test_fn024_explore_bind_after_help_goal_plan` — after a help+goal plan, bare explore still binds via C-106 and consumes DSE capability only |
| explicit analyze without engineering intention (`"analiza el margen de seguridad"`) | still analyze | `test_real_analyze_verb_still_reaches_analyze` |
| help word + real analyze verb combined (`"ayúdame, analiza el margen..."`) | still analyze (verb wins) | `test_analyze_verb_with_help_word_still_analyze` |
| H4 / iterate preseed | untouched | `test_iterate_lever_preseed_still_not_implemented` — a named lever after a help+goal plan still hits the existing (unfixed) honest fallback `"¿Qué quieres modificar?"`, `missing_slots == ["variable"]` |

## Explicitly deferred

- H4 (C-043 — lever → iterate preseed): completely untouched; `HandoffContext.levers`/`iterate_capability` remain populated-but-unread, exactly as FN-024 left them.
- H5 (C-081 — Continuity margin thread): untouched, still design-only.
- Create→BOM, Conversation Engine, Step D, dual-dispatch refactor: not touched.
- No opportunistic hygiene cleanup performed.

## Risks

- The `is_help_verb` check re-derives which `ANALYZE_PATTERNS` sub-group matched by re-running `_normalize_text`/`_matches_any` inside the orchestrator, rather than having `resolve_intent` return that information directly. This is a small, deliberate duplication of a cheap regex pass (mirrors the existing pattern at `_try_reprompt_active_block_declaration` and others, which already do their own independent pattern checks rather than threading extra return values through `resolve_intent`'s public `IntentType` signature) — flagged for awareness, not considered a defect.
- A phrase matching both `ANALYZE_HELP_PATTERNS` and `ANALYZE_VERB_PATTERNS` always keeps analyze routing (verb wins) — this is a conservative default the contract didn't explicitly specify, chosen because it never swallows a genuine analytical request; worth a quick Engineer sanity check if a real-world phrase surfaces that expected the opposite.
- System Map footprint for this cut spans 10 files (similar scale to FN-024) — all cross-checked programmatically for ID/count/rollup consistency, but a manual skim by Cursor is still worthwhile.
