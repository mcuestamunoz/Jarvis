# Implementation Contract — R3a Preempt Refuse Extension (G8/G11 partial)

**Project:** Jarvis  
**Date:** 2026-08-19  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** UX/routing fix — extend ★2 refuse to numeric sub-mode + DSE soft-interrupt mid-wizard.

**Investigation:** [`.jes/artifacts/investigation_r3_preempt_policy.md`](investigation_r3_preempt_policy.md)  
**Checkpoint base:** tag `checkpoint-cli-routing-residuals` (`0690895`)  
**Workflow:** Claude implements **Slices 1→2 in order** + tests + report → Engineer → Cursor review → checkpoint only if Engineer asks.

---

## 0. Why this cut

Investigation §1.1 exposed an asymmetry: `_maybe_refuse_different_target` (★2) gives an honest named refusal for engineering-intent/explore phrases in **component sub-mode** but the **numeric sub-mode** never reaches it — the exact same phrases degrade to `"No reconozco 'X' como valor."` (gate 12d).

This cut fixes the asymmetry and adds `explore_design_space` as a read-only soft-interrupt. It does **not** add any `clear_runtime_session()` — zero data-safety surface.

**Hard rules:**

- No `clear_runtime_session()` added anywhere in this cut.
- No changes to `collected_params` handling.
- No changes to `ParamDefinitionSession.answer()`.
- No changes to `_handle_component_description`'s existing ★2 logic.
- Soft interrupts (project_status, list_materials, list_motors, calculate, simulate) remain unchanged.
- Zero weakened tests.

---

## 1. Slices

### Slice 1 — Port ★2 refuse to numeric sub-mode

**Problem:** When `param_definition_reason != MISSING_COMPONENT_DEFINITION` (numeric sub-mode), intents like `"reducir payload"`, `"explora opciones"`, `"optimiza autonomía"` fall through to `ParamDefinitionSession.answer()` which returns `"No reconozco 'X' como valor."` — no acknowledgment of what the user asked, no guidance.

**Fix:** Before the `ParamDefinitionSession.answer()` call (line ~955), add a gate that detects engineering-intent and explore phrases and returns the same honest refusal component sub-mode already shows:

```
"Estoy definiendo [current block/param]. Escribe 'cancelar' primero si quieres [explore/plan]."
```

**Detection logic:** Reuse the same detectors `_maybe_refuse_different_target` already uses:
- `goal_planner.is_engineering_intention(user_input)` — catches `"reducir payload"`, `"aumentar empuje"`, etc.
- `intent_resolver.resolve_intent(user_input) == "explore_design_space"` — catches `"explora opciones"`, `"optimiza para autonomía"`.
- `acquisition_target.resolve_acquisition_mention(user_input)` — catches `"definir batería"` (different-block declare) while inside a numeric wizard for a different block.

**What the user sees:** The same ★2-style message, adapted to numeric context. The wizard stays open, `collected_params` untouched, the user can continue answering or `cancelar`.

**Files changed:**
- `src/jarvis/core/orchestrator.py` — add a pre-check before `ParamDefinitionSession.answer()` in the DEFINE_MISSING numeric branch.

**Tests:**
- `test_r3a_numeric_submode_engineering_intent_refuses_honestly` — numeric wizard open, send `"reducir payload"` → honest refusal (not `"No reconozco"`)
- `test_r3a_numeric_submode_explore_refuses_honestly` — numeric wizard open, send `"explora opciones"` → honest refusal
- `test_r3a_numeric_submode_different_block_refuses_honestly` — numeric wizard for propulsion, send `"definir batería"` → honest refusal
- `test_r3a_numeric_submode_real_value_still_works` — send `"12.0"` → accepted normally (regression guard)
- `test_r3a_component_submode_refuse_unchanged` — component wizard, send `"reducir payload"` → existing ★2 refusal unchanged (regression)

### Slice 2 — `explore_design_space` as soft-interrupt in both sub-modes

**Problem:** `explore_design_space` is genuinely read-only (pure in-memory, per `DesignExplorer` docstring — never mutates `ProjectState`). It could safely run and return results while the wizard stays open, like `project_status` already does — but it currently hits the ★2 refuse in component sub-mode and the parse-error fallback in numeric sub-mode.

**Fix:** Add `explore_design_space` to the soft-interrupt chain (gates 1-3, 7-8 in investigation §1) — before either sub-mode fork. Same shape as the existing `project_status` soft-interrupt:

1. Detect intent `explore_design_space` via `resolve_intent`.
2. Call `_handle_explore(goal_key, user_input, llm_interface)`.
3. Append a `wizard_reprompt` field (current wizard's pending question) so the CLI can re-show the prompt after DSE results.
4. Return — wizard state untouched.

**Guard:** Only fire if `goal_key` is resolvable (explicit text or active `handoff_context`). If not resolvable, fall through to existing behavior (refuse or LLM analyze, depending on sub-mode).

**Files changed:**
- `src/jarvis/core/orchestrator.py` — add soft-interrupt gate in DEFINE_MISSING branch, before the sub-mode fork.

**Tests:**
- `test_r3a_explore_soft_interrupt_component_submode` — component wizard, send `"explora opciones"` with active handoff_context → DSE results + wizard_reprompt
- `test_r3a_explore_soft_interrupt_numeric_submode` — numeric wizard, send `"optimiza para autonomía"` → DSE results + wizard_reprompt
- `test_r3a_explore_no_goal_falls_through` — no handoff_context, no explicit goal → existing behavior (refuse or analyze)

---

## 2. Scope boundaries

### In scope
- ★2 refuse ported to numeric sub-mode (Slice 1).
- `explore_design_space` as soft-interrupt in both sub-modes (Slice 2).
- Regression tests for existing behavior.

### Out of scope (do not implement — R3b follow-up)
- `clear_runtime_session()` or any preempt-and-redispatch logic.
- `apply_exploration_result` mid-wizard (requires clearing — R3b).
- Bare `iterate` mid-wizard (requires clearing — R3b).
- `dismiss_suggestion` mid-wizard.
- `create_project` mid-wizard.
- Any `ParamDefinitionSession.answer()` changes.
- Any `_handle_component_description` / `_maybe_refuse_different_target` changes.
- G9-A (separate IC).
- G12 retarget paths (separate).

---

## 3. Acceptance criteria

1. `"reducir payload"` in numeric wizard → honest refusal naming the current block, not `"No reconozco"`.
2. `"explora opciones"` in numeric wizard → honest refusal (Slice 1) or DSE results if goal resolvable (Slice 2).
3. `"explora opciones"` in component wizard with active handoff → DSE results + wizard_reprompt (Slice 2).
4. `"12.0"` in numeric wizard → accepted as value (regression).
5. `"reducir payload"` in component wizard → existing ★2 refusal unchanged (regression).
6. All existing tests pass (1856+ baseline).
7. Zero `clear_runtime_session()` calls added.

---

## 4. Decision log

| # | Decision | Rationale |
|---|---|---|
| ★1 | No clearing in this cut | Investigation §3.1: `collected_params` loss is real in numeric sub-mode; Option A sidesteps entirely |
| ★2 | Reuse existing detectors, not new patterns | `is_engineering_intention`, `resolve_intent`, `resolve_acquisition_mention` — same as ★2's own `_maybe_refuse_different_target` |
| ★3 | DSE as soft-interrupt, not preempt | `DesignExplorer.explore` is pure/read-only; wizard state untouched; mirrors `project_status` pattern |
| ★4 | Only fire DSE soft-interrupt when goal resolvable | Avoids LLM fallback mid-wizard; unresolvable falls to refuse or existing analyze path |
| ★5 | R3b (real preempt with partial-apply) is a separate IC | Different risk profile; needs its own investigation of `apply_and_recalculate` mid-wizard side effects |
