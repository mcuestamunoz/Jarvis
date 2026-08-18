# Implementation Report — CLI Polish Bundle (S1–S7 + S8 gated)

**Contract:** [`implementation_contract_cli_polish.md`](implementation_contract_cli_polish.md)
**Audit:** [`investigation_cli_polish_audit.md`](investigation_cli_polish_audit.md)
**Base commit:** `39b85b2` (audit report) on `1b4769f` (Continuity Hardening + G10)
**Status:** Implemented, tests added, full suite green. **Not committed** (per contract §"Do not commit or push unless asked").

---

## Files touched

| File | Slices |
|---|---|
| `src/jarvis/core/project_continuity.py` | S1, S7 |
| `src/jarvis/core/intent_resolver.py` | S2 |
| `src/jarvis/core/motor_catalog_assist.py` | S2 (G16-B) |
| `src/jarvis/core/param_definition_session.py` | S2 (G16-B) |
| `src/jarvis/core/orchestrator.py` | S2, S3, S4, S5 |
| `src/jarvis/core/reasoning_layer.py` | S7 |
| `tests/test_cli_polish.py` | T1–T14 (new) |
| `tests/test_continuity_hardening.py` | updated T6 (status shape change, see below) |
| `tests/test_assisted_acquisition.py` | updated one assertion (G16-B dedupe) |
| `tests/test_reasoning_layer.py`, `tests/test_orchestrator.py` | updated 2 label assertions (S7 relabel) |

No changes to: `domains/materials.py`, library JSON, `IntentResolver` signature, catalog-gap *computation* in `build_startup_context`, retarget-(a), thrust-gate.

---

## Per-slice behavior

### S1 — G9-B catalog-gap ranking
`project_continuity.py` gained `_catalog_gap_covered_by_declared_thrust(project_state, sim_status, req)`: returns `True` only when `sim_status == "pass"` **and** declared `per_motor_max_thrust_n >= thrust_per_motor_needed_n` (both present). The `elif motor_catalog_gap:` branch now requires this helper to be `False` to win `next_useful_step` — otherwise it falls through. The gap stays in `evidence` unconditionally (unchanged). Reads only `project_state.current_parameters` (already passed in) — no `catalog_ref`, no change to catalog-gap computation in `orchestrator.py`.

### S2 — G16-A/B list-motors global + CTA dedupe
- `intent_resolver.py`: new `LIST_MOTORS_PATTERNS` (mirrors `LIST_MATERIALS_PATTERNS`), `"list_motors"` added to `IntentType`, checked in `_resolve_strong_action_intent` immediately after `LIST_MATERIALS_PATTERNS` (before GUIDANCE/ANALYZE/question fallback — so a trailing `?` no longer routes to `analyze`).
- `orchestrator.py`: new `_handle_list_motors()` — filters via `build_motor_catalog_suggestions`/`derive_kv_prop_filters` when an active project has thrust/KV/prop filters, else an unfiltered `default_library.list_motors()` dump. 0 LLM. Soft-interrupt added in the same three places `list_materials` already is: ITERATE_INTERACTIVE interim, DEFINE_MISSING_PARAMETERS, and IDLE dispatch.
- G16-B: `format_motor_catalog_suggestions` gained `include_cta: bool = True` (default preserves every existing caller's output byte-for-byte); `param_definition_session._offer_catalog_help` now calls it with `include_cta=False` since `question` already carries the "Elige un número..." instruction. Checked `iterate_interactive_session.py`'s own caller — its `question` text is different wording (not a literal duplicate), left unchanged per contract ("do not silently strip a CTA from a caller that has no question" / no new duplication introduced elsewhere).

### S3 — G18 aerial vs terrestrial `definir motores`
Orchestrator-side gate only (Engineer lock #2), no `IntentResolver` signature change. In the `intent == "define_params"` bridge: when `reason == "missing_transmission_parameters"` and the active project's `current_parameters["vehicle_type"]` resolves to `"aerial"` via `CreateProjectInteractiveSession._domain_kind` (reused, not duplicated), redirect through new `_redirect_aerial_motors_request(project_state)`:
- if propulsion is still the active pending block → `_continue_block_acquisition()` (existing bridge);
- otherwise → `start_define_missing_params(["motors"], reason=MISSING_COMPONENT_DEFINITION)` (reopens the motors component wizard directly, same shape as any other component-level redefine).
Terrestrial projects (`robot`/`coche`/`rover`) are untouched — the gate only fires on `_domain_kind(...) == "aerial"`.

### S4 — G17 force-motors
New force-motors block in `_handle_component_description`, positioned **before** the existing force-propellers block. Live-tested `infer_component_for_key(..., "motors", ...)` against the audit's own extractor and found the motors rule's `motor_count` regex spuriously matches a bare `"NxP"` propeller size (e.g. `"10x4.5"` → `motor_count=10`, `completeness="medium"`) — so the force-motors gate requires `completeness == "high"` (not the `!= "low"` the audit's prose suggested), which real motor phrases (`"1x/4x 2306 2400KV 50W"`) already satisfy but a bare size does not. This keeps the FN-019/G14 regression guard intact (T10) without touching `_looks_clearly_propeller_shaped`.

### S5 — G12/FN-013 stale pending vs fresh block
New `_fresh_pending_keys_for_block(project_state, block_key)` recomputes the pending component/param keys for a block the same way `_set_pending_next_block` would for a fresh open. In `_try_reprompt_active_block_declaration`, after confirming `block_key == _next_pending_block(...)[0]`, the session's `pending_param_definitions[0]` is now checked against this **freshly recomputed** list (not a static `BLOCK_TO_COMPONENTS` membership check — "motors" is a legitimate member of *both* `"propulsion"` and `"energy"`'s component sets by design, so a static check wouldn't have caught the actual bug). If the session's head item isn't in the fresh list, the brief is rebuilt from the fresh list instead of trusting the stale field. Same-block, still-valid reprompts (the common case) are completely unaffected.

### S7 — G19 Continuity CTA bridge + reasoning labels
- Genuine (non-demoted) catalog-gap branch in `project_continuity.py` now appends to `next_why`: *"Di 'qué motores tenemos' para ver el catálogo, o 'explora opciones' para que Jarvis pruebe configuraciones alternativas."*
- New PASS+demoted-gap branch (`sim_status == "pass" and motor_catalog_gap`, only reached when S1's guard demoted it) with the audit §4.5 copy: `next_step` names the PASS margin and invites iterate/explore/catalog-link; `next_why` states no blocking gaps, quotes the catalog note, and names both escape hatches.
- `reasoning_layer.py`: the two motor suggestion labels relabeled to phrases the resolver now handles — `"Definir empuje por motor real"` → `"Qué motores tenemos en el catálogo"` (resolves to `list_motors`), `"Modelar unidad de potencia"` → `"Explora opciones de motor"` (resolves to `explore_design_space` via existing `EXPLORE_PATTERNS`). No new intent, no picker mechanism.

### S8 — G13 verification (gated)
Reproduced the audit's own probe live against current code (both entry points: direct material-value answer, and the combined "Gap 1" strategy-text path). **Did not reproduce** — `"PVC 400g"` extracts to `"pvc"` and the impact estimate computes correctly (`-12.2%`) in both cases. Confirms the audit's hypothesis: G10 ★2's single shared `MATERIAL_ALIASES` table already fixed this as a side effect. **No code change made** — closed as fixed by G10 ★2, locked with regression test T14.

---

## Tests

`tests/test_cli_polish.py` — T1–T14, all passing:

```
python -m pytest tests/test_cli_polish.py -q
15 passed
```

Regression suite (contract §4, no regressions):

```
python -m pytest tests/test_cli_polish.py tests/test_continuity_hardening.py tests/test_g10_materials_frame.py tests/test_project_continuity.py tests/test_fn019_bare_propeller_size.py -q
63 passed
```

Full suite:

```
python -m pytest -q
1768 passed
```
(baseline 1753 at `1b4769f` + 15 new in `test_cli_polish.py` = 1768; no failures, no skips introduced.)

### Pre-existing tests updated (behavior intentionally changed by this contract, not weakened)
- `tests/test_continuity_hardening.py::test_t6_list_motors_mid_thrust_wizard_is_deterministic` — asserted `status == "interactive"` from the old wizard-local-only list-motors path (Continuity Hardening ★5's partial implementation). G16-A now intercepts the phrase globally before that path is ever reached, same `"ok"`/`"list_motors"` shape as `_handle_list_materials`. Updated assertion; session-state assertions (mode, pending unchanged) kept and still pass.
- `tests/test_assisted_acquisition.py::test_fn009_offer_catalog_help_power_pending_keeps_watts_copy` — asserted the "Elige un número..." CTA appeared in `message` (the exact G16-B duplication bug). Updated to assert it's absent from `message` now that `question` is the sole owner.
- `tests/test_reasoning_layer.py`, `tests/test_orchestrator.py` — two assertions updated from the old suggestion label text (`"Definir empuje por motor real"`) to the new one (`"Qué motores tenemos en el catálogo"`), per S7's intentional relabel.

---

## Residual risks

1. **S4 completeness threshold deviates from contract prose.** The contract said "if completeness != 'low', bind motors"; live-testing showed this would reintroduce a G14-class regression on bare `"NxP"` propeller sizes (motors extractor's `motor_count` regex false-positives on them). Implemented `completeness == "high"` instead — verified against both the composite and singleton acceptance phrases (T9/T9b) and the regression guard (T10). Flagging for Cursor review since it's a deviation from the contract's literal wording, though it satisfies the contract's own stop condition #3 and every acceptance test.
2. **S3's "architecture otherwise complete" branch always reopens `["motors"]` alone**, not the full `["motors","propellers"]` propulsion pair, when propulsion isn't the actively pending block. This matches what the user asked for ("definir motores" specifically) and reuses the existing component-wizard bridge without inventing new logic; flagging in case Engineer wants the full propulsion pair reopened instead in that specific sub-case.
3. **G9-A remains deferred** (unchanged, as locked) — a bound `catalog_ref` still doesn't suppress a catalog-gap note once physical requirements outgrow it. Out of scope for this cut.

---

## Proposed System Map caveat text (not applied — report only)

> **Continuity CTA vs. catalog identity (G9-B, resolved 2026-08-18):** `project_continuity.build_project_continuity` reconciles three previously-independent authorities — physics PASS/margin, declared per-motor thrust, and the catalog matcher's BOM/identity gap — before choosing `next_useful_step`. A catalog gap that has already been physically covered by declared thrust is demoted to an evidence-only BOM note (visible in `next_useful_why`) and never phrased as an imperative "declare thrust" command. G9-A (catalog-gap computation ignoring a bound `catalog_ref`) remains open and separate — do not conflate the two when reading this function.
