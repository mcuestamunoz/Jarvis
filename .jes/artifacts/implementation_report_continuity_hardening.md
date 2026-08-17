# Implementation Report — Continuity Hardening

**Type:** Product behavior — Acquisition Target Authority (phased, 4 slices).
**Contract:** [implementation_contract_continuity_hardening.md](implementation_contract_continuity_hardening.md)
**Design authority (CLOSED ★1–★7):** [design_continuity_hardening.md](design_continuity_hardening.md)
**Investigation:** [investigation_continuity_hardening.md](investigation_continuity_hardening.md)
**Checkpoint base:** `checkpoint-g3` (`a3b72b8`)
**Commit / tag:** none (per contract — not requested)

All 4 slices implemented in one cut (tests stayed green throughout, per the contract's "prefer all in one cut if tests stay green" instruction).

---

## Files touched

| File | Slice | Change |
|---|---|---|
| `src/jarvis/core/orchestrator.py` | 1, 2, 4 | force-propellers gate (★4), `_maybe_refuse_different_target` + wiring (★2), `_should_preempt_iterate_wizard`/`_iterate_owns_component_input` reorder+extend (★3) |
| `src/jarvis/core/motor_catalog_assist.py` | 3 | `is_list_motors_phrase`, `derive_kv_prop_filters` (extracted), `format_no_thrust_candidate_message` filtered-max param (★6) |
| `src/jarvis/core/param_definition_session.py` | 3 | wire `is_list_motors_phrase` into `_answer_assisted_motor` (★5); pass `kv`/`prop_inch` into the no-candidate message (★6) |
| `tests/test_continuity_hardening.py` (new) | all | T1–T10 + 1 extra regression (T4b) |

`domains/materials.py`, G10's frame keywords/mutation SoT/list-materials intent — **not touched**, per contract §2 hard scope.
`library/*.json`, System Map files — **not touched**.

---

## Per-slice behavior

### Slice 1 — G14 composite force gate (★4)

Added `JarvisOrchestrator._looks_clearly_propeller_shaped(text)`: true when the text contains a real propeller keyword (`hélice`/`helice`/`propeller`/`props`), or when an `NxP`-shaped substring's two numbers fall inside a realistic propeller size band (diameter 1.5–30", pitch 0.5–20") **and** the text has no `kv` marker. The existing FN-019 force-propellers call site now additionally requires `"motors" not in expected_keys or _looks_clearly_propeller_shaped(user_input)` before forcing.

**Behavior change:** `"1x 2306 2400KV 50W"` inside a composite `["motors","propellers"]` wizard no longer force-matches propellers (diameter=1 fails the realistic band, and `"kv"` is present regardless) — falls through to the existing generic-component handling, which (unchanged) shows the **motors** brief, since `motors` is the first-declared member of `system_architecture_catalog.BLOCK_TO_COMPONENTS["propulsion"]` and therefore `expected_keys[0]`. No new "motors-shaped" detector was needed — the existing fallback order already prefers motors once the propeller false-positive is blocked.

Singleton `expected_keys=["propellers"]` and composite-with-a-real-propeller-phrase (`"10x4.5"`, `"hélice 10x4.5"`) are both unaffected — verified live and by T2/T3.

### Slice 2 — G12/G8 refuse policy (★2, refuse not retarget)

Added `JarvisOrchestrator._maybe_refuse_different_target(user_input, expected_keys)`, called at the top of `_handle_component_description` (before the affirmative check). It recognizes two shapes and returns one shared honest-refuse response for both (never mutates session state):

- **G12 shape** — `intent_resolver.resolve_declare_block_request(user_input)` names a block whose components (`system_architecture_catalog.BLOCK_TO_COMPONENTS`) do **not** include the active target. (By construction this can only fire for a genuinely *different* block: the same-block case is already claimed upstream by `_try_reprompt_active_block_declaration`/C-033 before `_handle_component_description` is ever reached.)
- **G8 shape** — `goal_planner.is_engineering_intention(user_input)` resolves a goal, or `resolve_intent(user_input) == "explore_design_space"`.

Response: `"Estoy definiendo <active target>. Escribe 'cancelar' primero si quieres pasar a definir <other>."` (block case) or `"...si quieres explorar otras opciones de diseño."` (engineering/explore case). `cancelar` (C-034) remains the only session-clearing path — no retarget (a) code was written, per ★2's lock.

### Slice 3 — G15 list-motors + filtered-max messaging (★5, ★6)

**★5:** `motor_catalog_assist.is_list_motors_phrase` — 4 narrow patterns (`que motores`, `motores disponibles/tenemos/hay`, `catálogo de motores`, `listar motores`), same shape as G10 ★8's `LIST_MATERIALS_PATTERNS`. Wired into `ParamDefinitionSession._answer_assisted_motor` (only reachable when `pending[0] in ASSISTED_MOTOR_PARAMS`, so it never steals a numeric answer for an unrelated param) — reuses `offer_catalog_help()` unchanged, so the wizard state is untouched and the same deterministic listing "ayúdame a elegir" already produces is shown; the user can still answer with a value afterward.

**★6:** Extracted the kv/prop-diameter derivation that `build_motor_catalog_suggestions` already computed inline into `motor_catalog_assist.derive_kv_prop_filters(project_state)`, reused by both functions. `format_no_thrust_candidate_message` gained optional `kv`/`prop_inch` parameters: when given, `max_available_n` is computed from `lib.find_motors_for_requirements(kv=kv, prop_inch=prop_inch)` (the same filtered universe the empty-candidate search just used) instead of the full unfiltered catalog, and the message explicitly labels it `"máximo compatible con tu KV/hélice cubierto por el catálogo"`. `_offer_catalog_help` now loads the active project once more (cheap, read-only) to pass these filters through. When no filters are available (bare thrust-only search), behavior is byte-identical to before.

Verified live: the exact investigation §3.2 scenario (kv=2400, prop=5") went from an unfiltered `~55 N` quoted next to a filtered `"no tengo un motor ≥ 37.7 N"` to a coherent filtered `~14.0 N` (< 37.7, no contradiction).

### Slice 4 — G11 iterate preempt ownership (★3, reorder + extend, not narrow)

`_should_preempt_iterate_wizard` now consults `_iterate_owns_component_input(session)` **before** the strong-intent check. If the wizard owns the current step **and** the classified intent is `None` or `"iterate"` specifically, it does not preempt. Any other strong intent (`simulate`, `calculate`, `explore_design_space`, `apply_exploration_result`, `create_project`, `define_params`, `dismiss_suggestion`) still preempts even while the wizard owns the step — `_ITERATE_PREEMPT_INTENTS` itself is unchanged, per ★3's rejection of option (c).

`_iterate_owns_component_input` gained a second ownership shape alongside the original `DEFINE`+`step==2`/`motor_suggestions` case: `draft.variable is not None and draft.operation is None` — the strategy-selection step (e.g. right after naming `variable="material"`, before an operation is resolved). This is exactly the step G11-A/B's CLI evidence targeted.

Verified live (reproducing the investigation's exact probes, now fixed):
- `"cambiar a pvc"` at the strategy step → no longer preempts; wizard advances normally, `draft.value == "pvc"`, next question is restrictions.
- bare `"pvc"` at the same step → no longer preempts.
- `"simula"` at the same owned step → **still** preempts and dispatches to `simulate` (`action="simulate"`, `status="ok"`) — proving the fix is narrow, not a blanket suppression.

---

## Tests added/updated

`tests/test_continuity_hardening.py` — 12 tests (T1–T10 required + T4b, a same-block-reprompt regression guard added to prove Slice 2's refuse check doesn't shadow the pre-existing C-033 same-block path).

## Tests executed

```text
pytest tests/test_continuity_hardening.py            12 passed
pytest  (full suite)                                1753 passed
```

1753 = 1741 (pre-existing, all green before this cut) + 12 new. **Zero regressions** — includes FN-011…021, FN-019, `test_propulsion_composite_wizard_flow.py`, `test_iterate_session.py`, `test_g10_materials_frame.py`, and every other existing suite.

---

## Residual risks

- **Slice 1's propeller-shape heuristic is a heuristic.** The realistic size band (1.5–30" diameter, 0.5–20" pitch) and the `"kv"`-absence check are deterministic but tunable; an unusual real propeller phrase outside that band, or a motor phrase that happens to avoid the word "kv" entirely (e.g. a bare wattage with a coincidental NxP-shaped substring), could still misclassify in either direction. No such case was found in testing; flagged for the CLI BOM walk to stress further.
- **Slice 2's refuse message is intentionally terse.** It names the active target and says "cancelar primero" but does not restate what the active wizard still needs — Engineer may want a richer refuse message after the CLI walk; kept minimal per ★2's "one honest line" lock.
- **Slice 2 doesn't cover every conceivable "different target" phrasing** — only `resolve_declare_block_request` (declare-block verbs) and `is_engineering_intention`/`explore_design_space` (G8's specific shape) are checked, matching the contract's explicit scope ("at minimum declare-block mentions + the G8 ... phrases"). A phrase that names a different target some other way (e.g. a bare component keyword with no declare verb) is not covered by this slice and falls through to existing behavior unchanged.
- **Slice 4's ownership extension is state-based, not step-number-based** (`variable set, operation None`), so it should generalize to any variable, not just `material` — this was not exhaustively tested beyond material, since that's the only variable the investigation reproduced the bug for. Recommend a quick CLI spot-check with a non-material variable (e.g. `payload`) during the BOM walk.
- **G15's ★7 exclusion (no thrust gate)** — a user can still type `"15"` for a requirement of `≥37.7` and have it silently accepted, unchanged, exactly as the contract locks.

---

## Proposed System Map caveat text (not applied — report-only, per contract §2)

- `CONNECTIONS.md` **C-052**: *"🟢 CONNECTED. Continuity Hardening (2026-08-15): the strong-intent check is now consulted AFTER an extended ownership predicate (`_iterate_owns_component_input`) — a step-2/strategy-selection answer that also parses as `intent=='iterate'` no longer self-preempts; any other strong intent (simulate/calculate/explore/...) still preempts even while the wizard owns the step. See G11 (closed)."*
- `03_acquisition/ACQUISITION_MAP.md` **"Known issues"**: add — *"G12/G8 (closed, Continuity Hardening 2026-08-15): `_handle_component_description` now refuses (one honest line + 'cancelar' hint) instead of silently re-showing the active wizard's brief when the user names a different valid block or an engineering-intent/explore phrase. No retarget — `cancelar` remains the only clear."*
- `01_runtime/RUNTIME_MAP.md` nested `DEFINE_MISSING_PARAMETERS` pseudocode: add a line for the new `_maybe_refuse_different_target` check (runs inside `_handle_component_description`, before the affirmative/infer branches) — currently still stale from the earlier G10 cut too (list_materials, force-frame), unrelated housekeeping flagged in the investigation, not fixed here.
- A new `C-xxx` candidate for `_maybe_refuse_different_target` itself (mirroring how C-105/C-106 got first-class IDs for the Handoff Context) is proposed but not assigned — Engineer's call whether this bundle warrants new registry entries or stays folded into the existing C-013/C-033/C-040 rows with caveats.

---

## ★1–★7 coverage

| ★ | Status | Where |
|---|---|---|
| ★1 | Done | One contract, 4 slices, all landed in this cut |
| ★2 | Done | Refuse (b) only — `_maybe_refuse_different_target`; no retarget code exists |
| ★3 | Done | Reorder (a) + extend (b); `_ITERATE_PREEMPT_INTENTS` untouched (not (c)) |
| ★4 | Done | `_looks_clearly_propeller_shaped` gate; first-declared (`motors`) wins by falling through to the existing `expected_keys[0]` brief, no new precedence code needed |
| ★5 | Done | `is_list_motors_phrase` wired into `ParamDefinitionSession._answer_assisted_motor` |
| ★6 | Done | `derive_kv_prop_filters` + `format_no_thrust_candidate_message`'s filtered max |
| ★7 | Respected | No thrust under-requirement gate added anywhere |
