# Implementation Contract — CLI catalog-assist T1 (misfit re-offer)

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** RATIFIED ★1–★5 (2026-09-01). **You are Claude Code.** Implement this file only. Cursor reviews; Cursor does not implement.

**Type:** Catalog-assist wiring + Continuity copy + watts CTA predicate split. **Not** new search. **Not** G22 filter relax. **Not** a recommender. **Not** ERF §11.

**Evidence:**
- [investigation_report_cli_catalog_assist_misfit_propose.md](investigation_report_cli_catalog_assist_misfit_propose.md)
- [investigation_review_cli_catalog_assist_misfit_propose.md](investigation_review_cli_catalog_assist_misfit_propose.md) — **PASS WITH NOTES**
- [engineer_ratification_cli_catalog_assist_t1.md](engineer_ratification_cli_catalog_assist_t1.md) — ★1–★5 locked

**Checkpoint base:** tag **`v0.3.5`** / `fc46938` plus current tree (Block Closure / CLI feasibility already shipped). Do not revert those.

**Walk fixture (do not mutate `workspace/`):**  
`inspección-autonomía-mínima-5-minutos` / `eb61a0ed6fe2` — bound `sunnysky_r2305_2500` + `gf_5045x3` + `lipo_6s_10000mah`, sim fail, `bound_sku_underspec`. Reproduce in **tmp tests**, not by editing that folder.

---

## 0. You (Claude)

- Edit only files listed in §5.
- Reuse `resolve_motor_catalog_surface` + `build_motor_catalog_suggestions`. **No** second motor-ranking function. **No** drop-KV / drop-prop second pass.
- Do not change `_derive_overall`, `ASSEMBLY_READY`, `derive_prop_energy_block_closure`, N1 discharge copy, catalog JSON, G24-B `_score_candidate`, `find_motors_for_requirements` predicate.
- Do not invent `motor_power_w`, minutes, or SKUs.
- Do not bump `pyproject.toml`.
- Full suite green. Zero weakened tests — especially `test_g21_idle_help_choose_noop_when_catalog_ref_set`.

---

## 1. Intent

After architecture 4/4, a catalog-bound motor that **no longer covers** current thrust must not make `ayúdame a elegir` reprint `estado`.

It must open the **existing** numbered G22 list (T1 filters: current thrust + inherited KV + prop inch). Picking a number re-binds via the existing COMPONENT catalog pick path.

`estado` / Continuity after sim **fail** must name those candidates (or the help-choose CTA) instead of only “la simulación no es PASS”.

Copy must **not** say the offer guarantees sim PASS or bloque CERRADO. On the walk fixture the T1 candidate (`sunnysky_r2205_2500`) still cannot lift ~30 N.

When the bound SKU **does** cover requirements, help-choose keeps today’s fall-through (propeller → battery → Continuity). G21 false motor re-bind stays forbidden.

---

## 2. Locked behavior

### 2.1 Underspec predicate (single authority)

Add a thin helper (prefer `engineering_readiness.py` next to `resolve_motor_catalog_surface`):

```text
bound_motor_sku_is_underspec(project_state) -> bool
```

True iff `resolve_motor_catalog_surface(...)` returns `gap_evidence_fact` starting with `bound_sku_underspec:`.

Use `derive_physical_requirements` already used by that surface. Do not reimplement `_motor_covers_requirements`.

`EngineeringReadinessResult.motor_catalog_gap_fact` already exists — Continuity should prefer `readiness.motor_catalog_gap_fact` when `readiness` is passed (no second resolve required on the `estado` path).

### 2.2 IDLE `ayúdame a elegir` — `orchestrator._try_start_assisted_motor_help`

Today (`:1482-1483`): `catalog_bound_motor_covers_power_w` → `return None`.

Replace that dead-end with:

| Bound motor | Underspec | Behavior |
|---|---|---|
| no | — | unchanged (existing propulsion/energy assist) |
| yes | **False** | `return None` (fall through to propeller/battery) — **G21** |
| yes | **True** | Open COMPONENT motor catalog: session `DEFINE_MISSING_PARAMETERS`, `pending_missing_reason=MISSING_COMPONENT_DEFINITION`, `pending_missing_params=["motors"]`, return `_offer_component_motor_catalog` (same as G21 freeform re-bind `:1506-1514`) |

Do **not** open the `motor_power_w` numeric wizard on this branch.

### 2.3 COMPONENT gate — `_handle_component_description`

`motors_want_help` today: `"motors" in expected_keys and _wants_catalog_help(motors)`.

`_wants_catalog_help` stays stub-or-unbound (Prop-3 ★4). **Additionally** OR in `bound_motor_sku_is_underspec(gate_project_state)` so a composite wizard can re-show the motor list when the bound SKU drifted.

Pick-matching via `session.motor_suggestions` already exists (`:2939`). Leave it.

Do **not** apply underspec to propeller or battery `_wants_catalog_help`.

### 2.4 Continuity — specialize sim-fail when underspec (★2)

In `project_continuity.py`, the rank-2 branch (`:179-182`, sim warning/fail) currently always wins and hides catalog next-step.

**Do not** delete rank 2. **Inside** that branch (or immediately before its generic copy), when underspec is live (`readiness.motor_catalog_gap_fact` starts with `bound_sku_underspec:` **or**, if `readiness` is omitted, `motor_catalog_gap` contains the existing Spanish “ya no cubre el hueco de diseño”):

**`next_useful_step` locked sense (Spanish, you may interpolate numbers/names):**

If `motor_catalog_matches` is non-empty:

```text
El motor vinculado ya no cubre el empuje (≥ {N} N/motor). Candidatos: {names}. Di 'ayúdame a elegir' para la lista numerada. Elegir no garantiza sim PASS.
```

`names` = up to 5 `name` fields from `motor_catalog_matches` (already G22-filtered). `{N}` = `thrust_per_motor_needed_n` if present.

If matches empty (honest G22 empty):

```text
El motor vinculado ya no cubre el empuje requerido. No hay otro motor en el catálogo con KV/hélice actuales. Di 'ayúdame a elegir' — la lista puede estar vacía.
```

**`next_useful_why`:** reuse `motor_catalog_gap` (already names the bound SKU). Do not invent a PASS claim.

Blocking (`status_type == "blocking"`) stays first. Other sim-fail cases (underspec **false**) keep today’s “Corrige la causa… / La última simulación no es PASS.”

### 2.5 GAP title — `engineering_readiness._motor_catalog_gaps`

Keep `gap_type="GAP-MOTOR-CATALOG-UNRESOLVED"`. Vary **title** only:

| `gap_evidence_fact` prefix | Title (locked) |
|---|---|
| `bound_sku_underspec:` | `Bound motor SKU no longer covers thrust` |
| `bound_sku_missing:` | `Bound motor SKU missing from catalog` |
| else (`catalog_matches.empty` / default) | `Motor SKU unresolved` (today) |

Do not rename the type ID. Update gap tests that assert title if any; evidence `fact` assertions stay.

### 2.6 Watts CTA — predicate split (★3)

**Do not change** `catalog_bound_motor_covers_power_w` (identity: `catalog_ref.family == "motor"`). Architecture-progress and “don’t open W wizard just because SKU is bound” stay.

Add (prefer `project_closure.py` beside that helper):

```text
catalog_bound_motor_lacks_nameplate_watts(design_properties) -> bool
```

True only when identity-bound **and** `default_library.get_motor(sku).max_watts is None` (missing SKU → False, do not crash).

`ReasoningLayer._catalog_bound_motor_lacks_watts` and the locked CLI-feasibility labels/insights that say **“este motor de catálogo no declara vatios”** must call **this** helper, not `catalog_bound_motor_covers_power_w`.

Keep `tests/test_energy_params.py::test_reasoning_missing_energy_catalog_bound_motor_no_watts_label` green (`emax_rs2205s_2300` has no `max_watts`).

**New test:** `design_properties` motors `catalog_ref` = `sunnysky_r2305_2500` (has ~220 W) + `missing_energy_parameters` → labels/insights must **not** contain `no declara vatios`. Unbound path still asks to declare W.

If the remaining missing energy param is battery only, the existing unbound-style `Declarar battery_capacity_wh…` path is fine.

Orchestrator energy proactive (`catalog_bound_motor_covers_power_w` stripping `motor_power_w`) **unchanged**.

---

## 3. Tests (mandatory)

| File | What |
|---|---|
| `tests/test_g21_g22_catalog_bind_ux.py` | **Keep** `test_g21_idle_help_choose_noop_when_catalog_ref_set` byte-intent: bound motor that **still covers** must not reopen **motors**. Add **new**: architecture-complete-ish project, bind `sunnysky_r2305_2500` + `gf_5045x3` + heavy battery (`lipo_6s_10000mah` or equivalent mass so underspec fires), IDLE `"ayúdame a elegir"` → message is a numbered catalog list (or honest empty G22 sentence), **not** a bare `estado` reprint; session pending motors **or** `motor_suggestions` non-empty. Do not touch the Engineer’s `workspace/` tree. |
| `tests/test_project_continuity.py` | Sim fail + `readiness.motor_catalog_gap_fact="bound_sku_underspec:…"` + matches containing `sunnysky_r2205_2500` → `next_useful_step` contains `ayúdame a elegir` and the candidate name; does **not** only say generic “no es PASS”. Sim fail **without** underspec unchanged. |
| `tests/test_engineering_readiness_gaps.py` | Underspec gap **title** is the new underspec title; type ID unchanged. Missing-from-library title. Empty-search title unchanged. |
| `tests/test_energy_params.py` | Existing emax no-W CTA. New r2305 must not say `no declara vatios`. |
| `tests/test_cli_catalog_assist_t1.py` **new** | Orchestrator unit: underspec help-choose; covering bound SKU still falls through (propeller or status). Optional: Continuity + title in one module. |
| `scripts/cli_probe_cli_catalog_assist_t1.py` | Optional probe, tmp workspace, `_RefuseLLM`. Not a substitute for unit tests. |

Do not weaken G22 empty-search tests. Do not add a filter-relax test that would become T1+2.

---

## 4. Non-goals

```text
T1+2 named G22 second pass (drop KV / drop prop)
Tier 3 joint motor+prop+battery search
G24-B _score_candidate
H5 ESC catalog / Catalog Foundation SKUs
Option B ERF / _derive_overall / ASSEMBLY_READY
derive_prop_energy_block_closure / N1 discharge copy
battery bound_sku_underspec / filtering build_battery_catalog_suggestions
Structure / frame mass iterate
Conversation Engine / new chat verb
library JSON expansion / “type sunnysky_r2205_2500” as the product fix
Changing catalog_bound_motor_covers_power_w semantics
```

---

## 5. Files

| File | Role |
|---|---|
| `src/jarvis/core/engineering_readiness.py` | `bound_motor_sku_is_underspec`; GAP titles |
| `src/jarvis/core/orchestrator.py` | IDLE underspec → `_offer_component_motor_catalog`; COMPONENT `motors_want_help` OR underspec |
| `src/jarvis/core/project_continuity.py` | Rank-2 underspec copy ★2 |
| `src/jarvis/core/project_closure.py` | `catalog_bound_motor_lacks_nameplate_watts` (or equivalent) |
| `src/jarvis/core/reasoning_layer.py` | CTA/insight uses nameplate-watts helper |
| `tests/test_g21_g22_catalog_bind_ux.py` | Underspec IDLE case; G21 noop intact |
| `tests/test_project_continuity.py` | Underspec next_step |
| `tests/test_engineering_readiness_gaps.py` | Titles |
| `tests/test_energy_params.py` | r2305 vs emax watts copy |
| `tests/test_cli_catalog_assist_t1.py` | New |
| `scripts/cli_probe_cli_catalog_assist_t1.py` | Optional |
| `docs/IMPLEMENTATION_TASKS.md` | In progress / done when you finish |
| `.jes/state/engineering_state.json` | Sync |

You may add a 2–4 line helper import in `project_closure.py` **or** keep the watts helper there and underspec in `engineering_readiness.py`. Do not put ranking in `orchestrator.py`.

---

## 6. Acceptance (reviewer)

- Underspec + IDLE `ayúdame a elegir` → numbered G22 list (or honest empty), not `estado` reprint.
- Bound motor that still covers → G21: no motor picker.
- Continuity sim-fail + underspec → step names candidates / help-choose; no PASS/CERRADO claim.
- GAP type ID unchanged; underspec title changed.
- emax no-W CTA unchanged; r2305 must not say “no declara vatios”.
- `catalog_bound_motor_covers_power_w` still identity-only.
- Block Closure rollup / `_derive_overall` / G22 search function unmodified.
- Suite green.

---

## 7. After you finish

Write `implementation_report_cli_catalog_assist_t1.md` (files, tests run, behavior, risks). Cursor reviews against **this** IC.
