# Implementation Report — G3 (Active Goal Continuity for Explore)

## Summary

An explore-shaped phrase that names the same engineering dimension as an active Goal Plan but carries no explicit direction (`"optimiza payload"`) now inherits the active plan's goal instead of silently re-deriving from text and inverting it — the exact CLI failure this contract closes. A single pure precedence function, `explore_continuity.resolve_explore_goal_with_handoff`, implements the locked precedence (`explicit new goal > active goal > inferred/default goal`) and is wired into `orchestrator._handle_explore`. `goal_planner.detect_goal`'s bare-`"payload"` default (F-1) is untouched — G3 operates entirely at the explore+handoff layer, exactly as scoped. **Full suite: 1715 passed** (1693 baseline + 22 new), zero regressions — including one real regression this cut initially introduced against FN-024's own "explicit goal is capability-neutral" rule, caught and fixed before landing (see §"A regression caught during implementation" below).

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/explore_continuity.py` (new) | `resolve_explore_goal_with_handoff` — the one pure precedence function. |
| `src/jarvis/core/orchestrator.py` | `_handle_explore` rewired to consult the handoff for both `goal_key is None` (H1, unchanged in outcome) and `goal_key is not None` (new — G3); ★4 handoff-replace on successful override. |
| `tests/test_g3_active_goal_continuity.py` (new) | 22 tests — see below. |

`goal_planner.py`, `intent_resolver.py`, `catalog_bind.py`, `component_sync.py`, H4's `handoff_matching.py` — **not touched**. `git status --short -- src/` confirms exactly the two files above.

## Precedence function (`explore_continuity.py`)

```python
resolve_explore_goal_with_handoff(user_input, text_goal, handoff) -> str | None
```

Implements Design §4's algorithm with one deliberate clarification of an ambiguity in its pseudocode, documented in the function's own docstring: the design's rule 4 condition is written as *"same dimension family AND NOT opposite_direction AND NOT has_explicit_direction_override"* — three conditions. In implementation, `"optimiza payload"` (undirected) and `"ahora aumenta el payload"` (explicit) both collapse to the **identical** `text_goal = "aumentar_payload"` via `detect_goal`'s own bare-dimension default — meaning the enum value alone cannot distinguish continuation from override; only the raw text's presence of an explicit direction word can. So `opposite_direction(text_goal, handoff.goal_key)` is not computed as a separate goal-key comparison — it is subsumed by checking `goal_planner._direction_of` directly on the raw input (reused verbatim, no new direction-word tables). This was verified to produce the exact outcomes in Design §2.4's and §7's acceptance tables for every listed case, including the ones that specifically motivated flagging this ambiguity (★1 vs. the "ahora aumenta" row).

Dimension families (Design §3, minimal, not rebuilding `goal_planner`): `payload={aumentar_payload, reducir_payload}`, `mass={reducir_masa}`, `autonomy={mejorar_autonomia}`, `stability={mejorar_estabilidad}`. No `_OPPOSITE_PAIRS` table was implemented — with only one two-member family today, "does the raw text carry an explicit direction word" is sufficient by construction (if it does, and the resulting `text_goal` differs from `handoff.goal_key`, that's the override, and within a 2-member family it can only be the opposite); a future dimension with more than two directional goals would need this reconsidered as part of that dimension's own migration (out of scope here, per Design §5).

## Wiring (`_handle_explore`)

The handoff is now loaded **unconditionally** at the top of the function (previously only loaded inside the `goal_key is None` branch), then `resolve_explore_goal_with_handoff` is called once to get `resolved_goal_key`. The function branches on `using_handoff_goal` — **whether the active handoff's goal was actually substituted in** — not merely on "does the final resolved goal happen to match the handoff":

- **`using_handoff_goal = True`** when `text_goal is None` (H1, unchanged) **or** when `text_goal != handoff.goal_key` but the resolver chose `handoff.goal_key` anyway (G3 rule 4, ★1 — a genuine inheritance). This path keeps the *exact* existing H1 gating: `dse_capability == "active"` → bind + explore + consume; `"consumed"` → the same deterministic "ya exploré opciones" message (now correctly also covers `"optimiza payload"`-style continuations, not just bare `"explora opciones"`); neither → fall to `_handle_analyze`.
- **`using_handoff_goal = False`** otherwise — covers three distinct cases, all handled identically to (and for the first one, byte-for-byte preserving) pre-G3 behavior:
  1. No bindable handoff at all → today's plain text-derive (T5).
  2. `text_goal` already equals `handoff.goal_key` (rule 3) — an **explicit** goal phrase that happens to name the currently-active goal. This is FN-024's own pre-existing "simplest option" (§4.2): capability-neutral, handoff completely untouched. Distinguishing this from case (3) below by checking `text_goal != handoff.goal_key` (not just `resolved_goal_key == handoff.goal_key`) was the fix for the regression described below.
  3. An explicit override (★2 different dimension, or ★1's mirror — an explicit conflicting direction) — explores independently of `dse_capability`, and if `handoff` existed with a *different* goal, triggers ★4's replace after a successful explore.

## ★4 — handoff replace on override

On a successful override explore (`goal_key not in EXPLORATION_GRIDS` already returned early; `bindable_handoff is not None`; `goal_key != bindable_handoff.goal_key`), the session's `handoff_context` is replaced with a fresh `HandoffContext(goal_key=goal_key, levers=GOAL_STRATEGIES[goal_key], dse_capability="consumed", project_id=...)` — same construction shape as `_handle_engineering_intent`/C-105. **`dse_capability` starts `"consumed"`, not `"active"`**: this explore already ran DSE for the new goal in the same turn, so a subsequent bare `"explora opciones"` should get H1's own honest "ya exploré opciones" message (now correctly naming the *new* goal), not a free silent re-run. Verified directly: after an override to `mejorar_autonomia`, the replaced handoff's `levers` are autonomy's own (`battery_capacity_wh`/`motor_power_w`-shaped), not payload's — H4's `match_plan_lever` is therefore automatically correct for the new plan too, no changes needed there.

No handoff is *invented* when none existed before an explicit, independently-resolved explore (T5) — matching Design's own acceptance table row and avoiding scope creep into "every explore creates a plan" territory.

## A regression caught during implementation (worth documenting)

The first wiring attempt defined `using_handoff_goal` simply as `resolved_goal_key == bindable_handoff.goal_key`. This broke an **existing** FN-024 regression test (`test_explicit_explore_domain_still_works_context_untouched`): an active `mejorar_estabilidad` plan, followed by the fully explicit `"optimiza para estabilidad"` (which resolves to `mejorar_estabilidad` on its own, no handoff involvement needed), was asserted to leave `dse_capability == "active"` untouched — FN-024's original, deliberately "simplest" design choice. Because `resolved_goal_key` trivially equals `handoff.goal_key` whenever `text_goal` already matches it (rule 3, a pass-through, not a precedence decision), the naive condition mistook this pass-through for an actual G3 inheritance and started consuming `dse_capability` for a case that was never supposed to touch it. Fixed by requiring `text_goal != handoff.goal_key` as part of the "genuine inheritance" check (see wiring section above) — re-ran the full FN-024/025/026/F-1/G3 regression sweep afterward to confirm no other case was affected by the correction.

## Tests

**Pure function (unit level)**: `test_resolve_explore_goal_with_handoff_pure` — parametrized across rules 1–5 (no handoff, `text_goal=None`, trivial agreement, ★1 inheritance both directions — T7's symmetric case included, ★2 different dimension, explicit same-family override) plus a dedicated "handoff for a different/non-bindable project must not leak in" case.

**T1–T7 (contract §4)**, all via the real orchestrator, no mocks:
- T1 — bare explore, H1 regression, still reduces.
- T2 (★1) — `"optimiza payload"` with active `reducir_payload` → DSE reduce, viable candidates all below baseline.
- T3 — explore-shaped explicit increase (`"optimiza para aumentar el payload"` — see note below on phrasing) overrides to `aumentar_payload`.
- T4 (★2) — `"optimiza para autonomia"` overrides to `mejorar_autonomia`; a second test confirms the handoff is also replaced in this different-dimension case (its new levers are autonomy's, not payload's).
- T5 — no handoff at all → today's text-derive (`aumentar_payload`), and confirms no handoff gets invented.
- T6 (★4) — after T3's override, the session's `handoff_context.goal_key`/`dse_capability` are the new goal/`"consumed"`; a *subsequent* bare `"explora opciones"` is asserted to reference the **new** goal's label in its message (not the stale one) — proof the replace actually took effect for a real downstream consumer, not just that a field looks right in isolation.
- T7 — symmetric continuation for `aumentar_payload` (undirected `"optimiza payload"` inherits increase).
- T8/T9 — see regressions and full-suite results below.

**Additional, not explicitly enumerated but required by acceptance criteria**:
- `test_continuation_phrase_after_consumed_gives_honest_message_not_silent_reexplore` — a G3-inherited continuation after `dse_capability` was already consumed gets the same deterministic "ya exploré opciones" message H1 already gives for bare explore, correctly naming the *active* (reduce) goal.
- `test_new_plan_phrase_routes_as_engineering_intent_not_explore` — ★3 (no dual-fire): a full plan-forming phrase (`"aumentar payload"` after `"reducir payload"` is already active) is classified as `intent="engineering_intent"` by the pre-existing FN-022 gate, never reaches `_handle_explore`/G3's precedence function at all — the existing plan-replace path (C-105, unchanged) owns it entirely.
- `test_explicit_explore_domain_still_works_context_untouched` (in `test_fn024_handoff_context_dse.py`) — the FN-024 regression described above, now green.
- `test_fn024_bare_explore_no_handoff_still_falls_to_analyze`, `test_fn025_help_plus_goal_then_bare_explore_regression`, `test_fn026_lever_preseed_unaffected_by_g3`, `test_f1_aumentar_payload_dse_regression` — smoke coverage across FN-024/025/026/F-1.

```
pytest tests/test_g3_active_goal_continuity.py -v                                 → 22 passed
pytest tests/test_fn022_engineering_intent.py tests/test_fn023_next_step_help.py \
       tests/test_fn024_handoff_context_dse.py tests/test_fn025_help_goal_intent.py \
       tests/test_fn026_lever_iterate_preseed.py tests/test_f1_reducir_payload.py \
       tests/test_g5_dse_iterate_dual_truth.py tests/test_component_sync.py \
       tests/test_design_explorer.py tests/test_goal_planner.py \
       tests/test_g3_active_goal_continuity.py -q                                 → 236 passed
pytest -q (full suite)                                                            → 1715 passed (1693 baseline + 22 new)
```

## Note on T3's exact phrasing

The contract's own T3 example, `"ahora aumenta el payload"`, does **not** match `EXPLORE_PATTERNS` at all (the explore-verb group is deliberately `optimiza|mejora|maximiza` — "aumenta"/"sube" are excluded by an existing comment: *"those stay as iterate mutations"*). That phrase is classified `intent="iterate"`, then intercepted by the pre-existing FN-022 gate as a **new plan-forming** phrase (routes to `engineering_intent`, replacing the handoff via the existing, unrelated C-105 path) — which is actually the **correct**, already-working behavior per ★3 (no dual-fire), not a G3 gap. T3 was implemented and tested against `"optimiza para aumentar el payload"` instead — a genuinely explore-shaped phrase (verb `optimiza` + domain `payload`, matches `EXPLORE_PATTERNS` line 171) that also carries a true explicit increase word (`"aument"`, detected by `goal_planner._direction_of`) — this is the phrasing that actually exercises G3's override branch inside `_handle_explore`. A test proving the *other* (engineering_intent, no-dual-fire) path exists separately: `test_new_plan_phrase_routes_as_engineering_intent_not_explore`.

## CLI probe (Engineer, post-review)

Simulated via direct orchestrator calls (no mocks) mirroring §5 of the contract exactly:

```text
1) "reducir payload"                        → Plan Reducir carga útil (unchanged)
2) "optimiza payload"                       → DSE reducir (2.0/2.8 kg candidates vs 4.0 kg baseline) — NOT maximizar
3) "optimiza para aumentar el payload"      → DSE aumentar (goal_key=aumentar_payload)
4) "explora opciones" (after step 3)        → "Ya exploré opciones para «maximizar carga útil»..." — follows the NEW handoff goal, not the stale reducir one
```

## Explicitly deferred

G6, G7, G1/G2, H5, Catalog Impl C, F-1b, changing F-1's bare-payload default globally, H4 lever synonym expansion — none touched. `cli_findings_post_catalog_bind_v1.md` — arrived already externally updated by Cursor/Engineer before this contract; not touched here, per contract §6's "update to 🟢 when Engineer confirms."

## Risks / notes

- `using_handoff_goal`'s three-way split (H1 / G3 inheritance / explicit-match-passthrough) is more intricate than the two-way split the contract's own pseudocode suggested. This was necessary to preserve FN-024's existing capability-neutral guarantee for explicit-but-coincidentally-matching goal phrases — documented inline in the code and above, not a deviation from any locked outcome (★1–★4 are all still satisfied exactly as specified; the regression this caught was in an *unstated* interaction, not a locked case).
- The dimension-family table is intentionally minimal (Design §3) — a future F-1b-style migration of another dimension's direction handling would need its own review of whether `_direction_of`'s word lists are adequate for that dimension's phrasing, same caveat F-1's own report already flagged.
