# Implementation Report — R3a Preempt Refuse Extension

**Contract:** [`implementation_contract_r3a_preempt_refuse.md`](implementation_contract_r3a_preempt_refuse.md)
**Investigation:** [`investigation_r3_preempt_policy.md`](investigation_r3_preempt_policy.md)
**Checkpoint base:** `checkpoint-cli-routing-residuals` (`0690895`)
**Status:** Implemented, both slices, tests added, full suite green. **Not committed** (per contract §"checkpoint only if Engineer asks").

---

## Note on how this session started

A substantial portion of this implementation (roughly the shape now on disk) was already present when this turn began — `orchestrator.py` was modified with both slices' gates, and `tests/test_r3a_preempt_refuse.py` already existed with 9 tests, one of which (`test_r3a_numeric_submode_different_block_refuses_honestly`) was **failing**. I treated the on-disk state as the current baseline (per the session's own convention for externally-changed files), verified it line by line against the contract, found and fixed three real issues, added tests locking each fix, and re-verified the whole thing end to end. This report describes the **final, corrected** state — not a diff against an intermediate draft.

---

## Slices completed

- [x] Slice 1 — ★2 refuse ported to numeric sub-mode
- [x] Slice 2 — `explore_design_space` as soft-interrupt in both sub-modes

---

## Files changed

| File | What |
|---|---|
| `src/jarvis/core/orchestrator.py` | `_maybe_refuse_numeric_submode` (Slice 1), inline `explore_design_space` soft-interrupt gate (Slice 2), `_get_define_missing_reprompt` helper (used by Slice 2's `wizard_reprompt`), `_NUMERIC_REASON_LABELS` dict. |
| `tests/test_r3a_preempt_refuse.py` | New — 11 tests (contract's 8 named tests + 3 I added for the fixes below). |

No `ParamDefinitionSession.answer()` changes, no `_handle_component_description`/`_maybe_refuse_different_target` changes, no `clear_runtime_session()` calls added anywhere (verified via `git diff | grep clear_runtime_session` — zero matches).

---

## Three issues found and fixed during verification

### 1. Wrong check order in `_maybe_refuse_numeric_submode` — real bug, caused a test failure

The on-disk version checked engineering-intent/explore **before** declare-different-block. I ran the full suite and `test_r3a_numeric_submode_different_block_refuses_honestly` failed: `"definir batería"` produced the *explore* refusal ("...si quieres explorar otras opciones de diseño") instead of the *different-block* refusal ("...si quieres pasar a definir la energía").

Root cause: `goal_planner.is_engineering_intention("definir batería")` returns `"mejorar_autonomia"` (not `None`) — `detect_goal`'s keyword table for that goal has real overlap with "batería"/energy vocabulary. I verified this **is not a novel collision** — it's the exact reason `_maybe_refuse_different_target` (★2, component sub-mode, `orchestrator.py:2067-2094`) checks `resolve_declare_block_request` **first** and `is_engineering_intention`/`explore` **second**. The on-disk numeric-sub-mode port had the two checks in the opposite order, which is what surfaced the collision.

**Fixed:** swapped the order in `_maybe_refuse_numeric_submode` to match ★2 exactly (declare-block first). Re-verified: `"definir batería"` now correctly returns "Estoy definiendo los parámetros de propulsión. Escribe 'cancelar' primero si quieres pasar a definir la energía." — no `"No reconozco"`, no misleading "explorar" wording.

The pre-existing test's own docstring had rationalized the bug as *"same precedence `_maybe_refuse_different_target` already uses"* — which is the opposite of what that method's actual code does. I corrected the test's docstring and strengthened its assertions (`"energía" in msg`, `"explorar" not in msg.lower()`) so a future regression on this exact collision would be caught, not silently accepted again.

### 2. Missing `_NUMERIC_REASON_LABELS` entry for `missing_transmission_parameters`

`parameter_requirements.py` defines exactly four numeric-sub-mode reasons (`MISSING_FORCE_REASONS`, minus `MISSING_COMPONENT_DEFINITION`): propulsion, energy, propeller, **transmission**. `_NUMERIC_REASON_LABELS` only had the first three — a terrestrial project's transmission wizard (torque/wheel/gear) would have shown the raw reason string leaking into the refusal: *"Estoy definiendo missing_transmission_parameters. Escribe 'cancelar'..."*.

**Fixed:** added `"missing_transmission_parameters": "los parámetros de transmisión"`. Locked with `test_r3a_numeric_submode_transmission_reason_has_real_label`.

### 3. `_get_define_missing_reprompt`'s component-sub-mode branch hand-rolled generic text

The on-disk version built `f"¿Cómo son {label}? Descríbelos."` from `_ACQUISITION_TARGET_LABELS` directly, instead of reusing `_component_prompt_for_first_missing`/`_COMPONENT_PROMPTS` — the established Brief-consistent prompt machinery FN-017/018 built specifically so *every* path that asks about a pending component key uses the same text, never a hand-rolled generic string. This is the same discipline `IterateInteractiveSession.get_current_prompt`'s own docstring states outright: *"Reuses the existing `_question_for_session` machinery — the orchestrator must NOT reconstruct this logic independently."*

**Fixed:** component-sub-mode branch now calls `self._component_prompt_for_first_missing(keys)` directly. Locked with `test_r3a_explore_soft_interrupt_reprompt_uses_component_prompts`, which asserts `wizard_reprompt == _COMPONENT_PROMPTS["motors"]` exactly.

---

## Behavior changed

- **Slice 1:** engineering-intent (`"reducir payload"`), explore (`"explora opciones"`), and different-block-declare (`"definir batería"`, `"declarar estructura"`) phrases in numeric sub-mode now return the same honest, named refusal component sub-mode already gave via ★2 — instead of degrading to `"No reconozco 'X' como valor."` (investigation §1, gate 12d).
- **Slice 2:** `explore_design_space` fires as a soft-interrupt in **both** sub-modes when the goal is resolvable (an explicit goal phrase in the text, or an active-project `handoff_context` with `dse_capability == "active"`) — returns real DSE results plus a `wizard_reprompt` field, wizard state completely untouched. When not resolvable, falls through to Slice 1's refuse (numeric) or ★2's existing refuse (component) — never silently calls the LLM from this gate.
- **No existing behavior changed.** Component sub-mode's `_maybe_refuse_different_target` is untouched. All five existing soft-interrupts (project_status, list_materials, list_motors, calculate, simulate) are unchanged, unaffected by gate ordering (Slice 2's new gate sits between navigation-back and the component/numeric fork, after all of them).

---

## `_handle_explore` state-safety verification (unchanged conclusion from the earlier pass, re-verified)

Traced `_handle_explore` (`orchestrator.py:2694-2872`) end to end:

1. Reads `current_session` via `self.state_manager.get_runtime_session()`.
2. The only session field it can ever write back is `last_exploration_result`, plus optionally `handoff_context` (DSE-capability consumption or goal replacement) — both via a Pydantic `model_copy(update=session_updates)`, which preserves every field not explicitly listed.
3. `mode`, `pending_param_definitions`, `collected_params`, `param_definition_reason`, `pending_missing_params`, `pending_missing_reason` never appear in `session_updates` — they survive a call to `_handle_explore` byte-for-byte, confirming this really is the read-only soft-interrupt the contract's ★3 decision calls it.

`wizard_reprompt` is computed from the `current_session` snapshot captured *before* `_handle_explore` runs, at the Slice 2 gate — so it reflects the correct pending question regardless of any field `_handle_explore` might touch (and per point 3, it touches none of the fields `_get_define_missing_reprompt` reads anyway).

---

## Tests

`tests/test_r3a_preempt_refuse.py` — 11 tests, all passing:

```
python -m pytest tests/test_r3a_preempt_refuse.py -q
11 passed
```

| Test | Verifies |
|---|---|
| `test_r3a_numeric_submode_engineering_intent_refuses_honestly` | `"reducir payload"` → honest refusal, not `"No reconozco"` |
| `test_r3a_numeric_submode_explore_refuses_honestly` | `"explora opciones"` (no goal) → honest refusal |
| `test_r3a_numeric_submode_different_block_refuses_honestly` | `"definir batería"` → **correct** different-block refusal (fix #1) |
| `test_r3a_numeric_submode_pure_block_declare_refuses_honestly` | `"declarar estructura"` → block-declare branch, no engineering-intent overlap |
| `test_r3a_numeric_submode_transmission_reason_has_real_label` | terrestrial reason → real label, not the raw reason string (fix #2) |
| `test_r3a_numeric_submode_real_value_still_works` | `"12.0"` → accepted normally (regression) |
| `test_r3a_component_submode_refuse_unchanged` | `"reducir payload"` in component wizard → existing ★2 refusal unchanged (regression) |
| `test_r3a_explore_soft_interrupt_component_submode` | `"explora opciones"` + active handoff → DSE results + `wizard_reprompt`, mode unchanged |
| `test_r3a_explore_soft_interrupt_numeric_submode` | `"optimiza para autonomía"` + active handoff → DSE results + `wizard_reprompt`, mode unchanged |
| `test_r3a_explore_soft_interrupt_reprompt_uses_component_prompts` | `wizard_reprompt` reuses `_COMPONENT_PROMPTS` exactly (fix #3) |
| `test_r3a_explore_no_goal_falls_through` | `"explora opciones"` with no handoff → falls through to Slice 1 refuse, never calls the LLM |

Full suite:

```
python -m pytest -q
1867 passed
```
(baseline 1856 + 11 new tests = 1867. No failures, no skips, zero weakened assertions — one pre-existing test's docstring and assertions were *strengthened*, not weakened, once the bug it had rationalized was actually fixed.)

---

## Acceptance criteria checklist

1. ✅ `"reducir payload"` in numeric wizard → honest refusal naming the current block, not `"No reconozco"`.
2. ✅ `"explora opciones"` in numeric wizard → honest refusal (no goal resolvable here) or DSE results (goal resolvable, per Slice 2 test).
3. ✅ `"explora opciones"` in component wizard with active handoff → DSE results + `wizard_reprompt`.
4. ✅ `"12.0"` in numeric wizard → accepted as value (regression).
5. ✅ `"reducir payload"` in component wizard → existing ★2 refusal unchanged (regression).
6. ✅ All existing tests pass (1867 ≥ 1856 baseline).
7. ✅ Zero `clear_runtime_session()` calls added.

---

## Risks / follow-ups

- **R3b** (real preempt with partial-apply for `apply_exploration_result`/bare `iterate`/`dismiss_suggestion`/`create_project` mid-wizard) remains a separate, deliberately out-of-scope follow-up per the investigation's own recommendation (Option B) — this cut does not touch `clear_runtime_session()` at all, by design.
- The `is_engineering_intention`/keyword-overlap issue (fix #1) is a **pre-existing** characteristic of `goal_planner.detect_goal`'s keyword table, not something introduced or fully resolved here — it's exactly why check-order matters, and why I matched ★2's proven order rather than trying to fix the keyword table itself (out of scope, and risks its own regressions elsewhere `is_engineering_intention` is used).
