# Implementation Contract — G21 + G22 Catalog Bind UX (pre–Impl C)

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** Acquisition / catalog surface honesty — wire catalog bind into natural CLI paths; align gap vs list authority.

**Evidence (no separate investigation IC — CLI + code audit sufficient):**
- [`.jes/artifacts/cli_findings_post_catalog_bind_v1.md`](cli_findings_post_catalog_bind_v1.md) — **G21**, **G22**
- G9-A CLI probe 2026-08-20 — proyecto `dron-de-prueba-g9-a` (Engineer session transcript)

**Prerequisite:** tag **`checkpoint-g9a`** (`ea3d47d`) — G9-A closed  
**Blocks:** Impl C investigation/IC until this cut is closed + short CLI probe green

**Workflow:** Claude implements **Slices 1→2→3 in order** + tests + report → Engineer → Cursor review → commit/tag if Engineer asks.

---

## 0. Why this cut (together, not separate)

Two findings from the **same CLI session**, same root area (`motor_catalog_assist` + orchestrator acquisition), same gate before Impl C:

| ID | Symptom | Root |
|---|---|---|
| **G21** | `ayúdame a elegir` in motors component wizard re-shows Brief; IDLE after freeform `4x 2306…` shows `estado` instead of picker | FN-005 only on `ASSISTED_MOTOR_PARAMS`; `_try_start_assisted_motor_help` returns `None` when `motor_power_w` set |
| **G22** | `estado` says *"no tengo un motor…"* while `qué motores tenemos` lists 5 SKUs | `build_motor_catalog_suggestions` KV-only fallback when strict search empty; `resolve_motor_catalog_surface` has no fallback |

**Impl C** needs users to reach **`catalog_ref` bind** through normal acquisition — not only via a hidden energy-param wizard. **G22** must not leave two catalog authorities disagreeing before DSE surfaces more catalog rows.

**Hard rules:**

- Reuse **`bind_motor_from_catalog` + `set_motor_component`** — no parallel bind path.
- Do **not** implement battery/propeller catalog pick (out of scope).
- Do **not** start Impl C DSE work in this IC.
- Brief copy must **not** advertise paths that do not work after this cut.
- Zero weakened tests; full suite green.

---

## 1. Design decisions (locked — Option A)

### ★1 G21 — Catalog bind in motors component sub-mode + IDLE re-bind

**Option A (this IC):** Wire `is_help_choose_phrase` in **`MISSING_COMPONENT_DEFINITION`** when `"motors" ∈ expected_keys` to the same catalog list + pick + bind path used by FN-005 (`build_motor_catalog_suggestions` → pick → `bind_motor_from_catalog` → `set_motor_component`).

**Not Option B** (Brief-only honest CTA without bind) — closes the probe gate for G9-A CLI validation and matches Continuity copy that already says *"Di 'ayúdame a elegir'"*.

**IDLE extension:** `_try_start_assisted_motor_help` must **not** return `None` merely because `motor_power_w` is set when `components["motors"]` exists and **`catalog_ref is None`** (freeform declare). In that case, open the same catalog picker (re-bind / upgrade-to-SKU), 0 LLM.

When `catalog_ref` is **already set**, IDLE help-choose may still return `None` (bind done) — G9-A handles honesty post-bind.

### ★2 G22 — Single strict authority (remove KV fallback)

**Delete** the KV-only escape hatch in `build_motor_catalog_suggestions`:

```python
if not matches and kv_hint is not None:
    matches = lib.find_motors_by_kv(kv_hint)
```

Both `list_motors` and `resolve_motor_catalog_surface` already call `find_motors_for_requirements` with the same thrust/kv/prop filters. After G22, **empty strict search → empty list everywhere**.

When prop filter causes empty (e.g. hélice ~10" + ~2400KV motors with 5–6" compatible props), gap message *"no tengo un motor…"* and `list_motors` *"(sin candidatos…)"* are **consistent** — not contradictory.

**Do not** add KV fallback to `resolve_motor_catalog_surface` to match the old list behavior — that would preserve the lie.

### ★3 Pick handling in component wizard

Reuse patterns from `ParamDefinitionSession._apply_catalog_motor_pick` / `_answer_assisted_motor`:

1. Help-choose → populate `session.motor_suggestions`, return numbered list (reuse `format_motor_catalog_suggestions` or `_offer_catalog_help` formatting — same keys).
2. Numeric pick / `match_suggestion_by_input` / `resolve_motor_from_text` while `"motors"` pending and `motor_suggestions` non-empty → bind + save + **advance component wizard** (next key in `expected_keys`, same as `component_description_saved` after motors).

If motors pick completes the motors key only, do **not** clear the whole wizard — continue to propellers/esc as today after freeform declare.

Store `motor_suggestions` on runtime session (existing field) for the pick turn.

### ★4 Brief copy (motors only)

Update `acquisition_brief.build_acquisition_brief` for `key == "motors"` — add third bullet:

```text
  • decir 'ayúdame a elegir' para ver candidatos numerados del catálogo
```

Keep `ayúdame a definir` as repeat-guide. **Do not** add this bullet to battery/frame/propellers in this IC.

---

## 2. Slices

### Slice 1 — G21: component wizard + IDLE catalog bind

**Problem:** Natural propulsion-first flow cannot bind SKU.

**Fix locations (suggested — implementer may extract helpers, not new subsystems):**

| Location | Change |
|---|---|
| `orchestrator._handle_component_description` | Before `infer_components`: if `"motors" in expected_keys` and `is_help_choose_phrase(user_input)` → offer catalog list (set `motor_suggestions`). If `motor_suggestions` and pick resolves → bind via shared pick helper, return `component_description_saved`-style advance. |
| `orchestrator._try_start_assisted_motor_help` | Replace bare `if motor_power_w is not None: return None` with: if `motor_power_w` set **and** motors lacks `catalog_ref` → offer catalog picker (same list/pick/bind). Else if `catalog_ref` set → `return None`. |
| `param_definition_session.py` and/or `orchestrator.py` | Extract minimal shared pick helper if needed (bind + `set_motor_component` + save) — **must** call existing `bind_motor_from_catalog`; do not duplicate Impl B logic. |
| `acquisition_brief.py` | Motors Brief third bullet (§1.4). |

**Out of scope for Slice 1:** Changing freeform `4x 2306…` to auto-bind; changing propellers/ESC acquisition.

**Tests** (new file `tests/test_g21_catalog_bind_ux.py` recommended):

- `test_g21_component_wizard_help_choose_shows_numbered_catalog` — `start_define_missing_params(["motors"], MISSING_COMPONENT_DEFINITION)` → `"ayúdame a elegir"` → response contains numbered candidates + `motor_suggestions` populated; **not** a bare Brief re-show only.
- `test_g21_component_wizard_pick_sets_catalog_ref` — follow pick `"1"` → `components["motors"].catalog_ref.family == "motor"` and SKU matches first suggestion; wizard advances (propellers or next key still pending).
- `test_g21_idle_help_choose_when_power_set_unbound_motor` — project with freeform motors (`catalog_ref None`, `motor_power_w` set) → IDLE `"ayúdame a elegir"` → catalog list, **not** `project_status`/Continuity block.
- `test_g21_idle_help_choose_noop_when_catalog_ref_set` — bound motor → IDLE help-choose → `None` / falls through (no false re-bind); regression guard.

**Regression:** `tests/test_assisted_acquisition.py`, `tests/test_catalog_bind_v1.py`, G9-A tests unchanged.

---

### Slice 2 — G22: align list with gap (remove KV fallback)

**Problem:** `build_motor_catalog_suggestions` softens empty strict search via `find_motors_by_kv`.

**Fix:**

- Remove KV fallback block in `motor_catalog_assist.build_motor_catalog_suggestions` (~246–247).
- Audit **`find_motors_by_kv`** callers — if only used by this fallback, leave function (library API) but ensure no acquisition path reintroduces divergence.
- `_handle_list_motors` already shows *"(sin candidatos para este espacio de diseño)"* when filtered list empty — verify still true.

**Tests:**

- `test_g22_strict_empty_when_prop_excludes_kv_matches` — fixture: thrust ~6.9 N/motor, kv ~2400, `propeller_diameter_in=10.0` → `build_motor_catalog_suggestions` **empty** AND `resolve_motor_catalog_surface` → generic gap (same as pre-G22 gap path for unbound).
- `test_g22_list_motors_and_gap_agree_on_strict_empty` — through `build_motor_catalog_suggestions` vs `resolve_motor_catalog_surface` on same `SimpleNamespace` project state — both empty catalog matches when strict filter empty.

**Regression:** Existing `test_assisted_acquisition` catalog suggestion tests — update **only** if they relied on KV fallback; behavior change is intentional.

---

### Slice 3 — Integration + G9-A CLI probe regressions

**Tests:**

- `test_g21_bound_motor_catalog_gap_cleared` — bind via component-wizard pick → `build_engineering_readiness` → no `GAP-MOTOR-CATALOG-UNRESOLVED` when SKU covers requirements (reuses G9-A Scenario B pattern through **new** entry path).
- G9-A suite + G9-B + full suite green.

**Engineer CLI probe (manual, post-impl — document in report):**

1. Create dron → architecture A → `definir propulsion` → `ayúdame a elegir` → `1` → `estado` → **no** false generic catalog gap (Scenario B).
2. Same project before bind: `estado` gap text and `qué motores tenemos` **both** empty or both non-empty — **not** gap empty + list populated (G22).

---

## 3. Scope boundaries

### In scope

- G21 component motors wizard + IDLE unbound re-bind
- G22 KV fallback removal + test alignment
- Motors Brief copy
- Regression tests above

### Out of scope

- Impl C (catalog-aware DSE)
- Battery/propeller catalog bind UX
- Changing prop mismatch / electrical compatibility
- Fixing control-wizard retarget (`Definir sensors` loop) — separate finding from same session, not G21/G22
- G17 force-motors for bare phrases at IDLE

---

## 4. Acceptance criteria

1. `definir propulsion` → `ayúdame a elegir` → numbered catalog list (not Brief loop).
2. Pick `1` in that wizard → `catalog_ref` on motors + wizard continues.
3. IDLE + freeform motor + `motor_power_w` set + no `catalog_ref` → `ayúdame a elegir` opens picker (not `estado`).
4. IDLE + bound `catalog_ref` → help-choose does not falsely re-open energy wizard.
5. Strict empty design-space → gap and `list_motors` agree (G22).
6. G9-A automated tests still pass; new G21/G22 tests pass.
7. Full suite green.

---

## 5. Decision log

| # | Decision | Rationale |
|---|---|---|
| ★1 | One IC, two slices | Same session, same files, same Impl C gate |
| ★2 | G21 Option A (bind, not CTA-only) | Unblocks catalog_ref in natural flow; matches product copy |
| ★3 | G22 = remove fallback, not add to gap | Single strict authority; gap was already stricter |
| ★4 | Reuse `bind_motor_from_catalog` | Impl B contract; no parallel identity path |
| ★5 | IDLE re-bind when unbound only | Avoid picker noise when SKU already bound |
| ★6 | Motors Brief bullet only | Minimal copy churn |

---

## 6. Review checklist (Cursor — mandatory)

1. Component wizard help-choose runs **before** `infer_components` / Brief re-show.
2. Pick sets `catalog_ref` via `bind_motor_from_catalog`, not freeform declare.
3. IDLE path: `motor_power_w` + no `catalog_ref` → picker; bound → no spurious picker.
4. KV fallback **removed** from `build_motor_catalog_suggestions`.
5. Gap + list empty/non-empty agree on prop-exclusion fixture (G22 test).
6. G9-A tests green; no Impl C code introduced.
7. Full suite green.

---

## 7. Implementation report (Claude deliverable)

`.jes/artifacts/implementation_report_g21_g22_catalog_bind_ux.md` with:

- Files changed per slice
- CLI probe steps 1–2 results (Engineer can paste transcript)
- Test count / suite result
- Deviations (must be empty or flagged)

---

**End of contract.**
