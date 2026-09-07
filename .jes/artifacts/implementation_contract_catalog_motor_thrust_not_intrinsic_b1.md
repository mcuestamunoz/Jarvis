# Implementation Contract — Motor thrust not intrinsic B1 (OP durability + copy hygiene)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2350**)  
**Review:** [implementation_review_catalog_motor_thrust_not_intrinsic_b1.md](implementation_review_catalog_motor_thrust_not_intrinsic_b1.md)  
**Report:** [implementation_report_catalog_motor_thrust_not_intrinsic_b1.md](implementation_report_catalog_motor_thrust_not_intrinsic_b1.md)  
**Parents:**
- [investigation_contract_catalog_motor_thrust_not_intrinsic.md](investigation_contract_catalog_motor_thrust_not_intrinsic.md)
- [investigation_report_catalog_motor_thrust_not_intrinsic.md](investigation_report_catalog_motor_thrust_not_intrinsic.md)
- [investigation_review_catalog_motor_thrust_not_intrinsic.md](investigation_review_catalog_motor_thrust_not_intrinsic.md) — **PASS WITH NOTES** (N1–N5)
- G5: [implementation_contract_g5_dse_component_sync.md](implementation_contract_g5_dse_component_sync.md) / `sync_motors_component_from_params`
- ESC mass hygiene CLOSED @ suite **2344**

**Type:** Correctness + honesty hygiene for **conditioned motor thrust**.  
**Not** schema optionalization. **Not** vocabulary rename (H3). **Not** pose/glyph. **Not** ESC/FC.

**Baseline:** package **`0.3.8`** · suite **2344**

**Output:** `.jes/artifacts/implementation_report_catalog_motor_thrust_not_intrinsic_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** (H1) | YES — OP durability via G5-shaped `calculated` gate + CLI copy hygiene |
| 2 | `MotorSpec.thrust_n` | **Stays required** — design-space ranking unchanged |
| 3 | `resolve_operating_point` | **Do not** remove or rewrite ladder; call sites may gain sync/`source` fix only |
| 4 | **N1** | Existing exact/fallback property mirror in `set_motor_component` must use **`source="calculated"`** (not `"declared"`), and/or call `sync_motors_component_from_params` after OP params write — **reuse**, don’t invent a second sync module |
| 5 | Regression | Required: exact OP survives `resolve_propulsion_parameters` / apply_to (EMAX + `gemfan_5045_hbn` @ ~16 V → **13.4841**, not 10.042) |
| 6 | Copy | CLI candidate + chosen lines: catalog peak ≠ unconditioned “motor fact” |
| 7 | H2/H3 / pose / ESC / FC | **Out** |
| 8 | Version | **No** bump |

---

## 1. You

- Do **not** make `thrust_n` optional; do **not** rename to `catalog_peak_thrust_n`.
- Do **not** backfill 20 motor OP rows; do **not** invent OP data.
- Do **not** edit ESC / FC / sensors / glyphs / pose.
- Do **not** bump package version.
- Full suite green. Retarget tests; never weaken.
- Write `implementation_report_catalog_motor_thrust_not_intrinsic_b1.md` when done.

---

## 2. Intent

```text
set_motor_component
  resolve_operating_point → params["per_motor_max_thrust_n"] + propulsion_resolution
  for exact/fallback:
    motors.properties["thrust_n"] = OP value, source="calculated"   # N1 (was "declared")
    (optional equivalent: sync_motors_component_from_params(components, params))
        ↓
  resolve_propulsion_parameters  skips declared-only gate → OP value durable
        ↓
  CLI motor assist strings mark catalog peak vs conditioned resolution
```

---

## 3. Locked behavior

### 3.1 Durability (must)

In `src/jarvis/core/component_writers.py` → `set_motor_component`:

- Today, exact/fallback already copies `resolved_op.thrust_n` onto `properties["thrust_n"]` with **`source="declared"`**.
- **Change:** that write must use **`source="calculated"`** (same tag G5 uses), **or** after writing `per_motor_max_thrust_n`, call `sync_motors_component_from_params` so the helper performs the calculated tag (avoid double-conflicting writes — pick **one** clear path; prefer fixing the existing write to `calculated` unless calling the helper is cleaner for DRY).
- `legacy_estimate` / unbound paths: **unchanged** numerically (still bare catalog peak / freeform).
- Do **not** change `resolve_propulsion_parameters` activation rules globally.
- Do **not** change `bind_motor_from_catalog` projecting catalog peak as `declared` (that remains the pre-OP seed on the component until OP mirror runs).

### 3.2 Re-resolve coverage (must check; minimal fix if broken)

Confirm catalog propeller pick still re-calls `set_motor_component` (★5) — **keep**.

If a **one-line** mirror of that re-call on the freeform propeller registration path (~`orchestrator` propellers branch) is required for the regression in §4 to pass in product-shaped flows, you **may** add it. If not needed for green + regression, document as deferred in the report (N2).

### 3.3 CLI copy hygiene (must)

In `src/jarvis/core/motor_catalog_assist.py` (and only there unless a second identical string lives elsewhere):

| Surface | Required honesty |
|---|---|
| Candidate line (`_format_candidate_line`) | Catalog `thrust_n` must not read as a bare motor fact — e.g. include a short marker such as `catálogo` / `pico catálogo` (Spanish CLI voice; keep terse). |
| Chosen line (`format_motor_chosen_line`) | Same: peak is catalog / se refinará con hélice·batería — **or**, if `propulsion_resolution` on the project is already exact/fallback when the line is formatted, show the **resolved** thrust and name condition when cheaply available. Do not invent propeller/voltage if absent. |

Exact wording is implementer choice within honesty; no new i18n framework.

### 3.4 BOM `_MEASURABLE` (should)

If a **localized** honesty improvement in `project_closure.py` is small (e.g. do not treat bare motor `thrust_n` alone as full measurable credit without resolution, **or** add a declarative tail when only legacy peak exists), include it. If it forces a wide BOM redesign, **stop** that part, document deferral in the report, and still ship §3.1–3.3.

### 3.5 Seeds

**No** seed number changes required for B1 (10.042 may remain as catalog peak / fallback shim). Honesty is semantic + durability, not deleting the peak field.

---

## 4. Tests (required)

1. **Regression (new):** catalog-bound `emax_rs2205s_2300` + `gemfan_5045_hbn` + voltage context that yields exact OP **13.4841** → after `set_motor_component` (and a `resolve_propulsion_parameters` + `apply_to` on the resulting components/params), `per_motor_max_thrust_n == pytest.approx(13.4841)` and motors `properties["thrust_n"].source == "calculated"` (or equivalent proof the declared gate no longer reverts to 10.042).
2. **Non-regression:** motor-only / no-prop path still resolves fallback/legacy honestly (10.042 where that is today’s correct fallback).
3. **Triage** literal `10.042` pins in:  
   `tests/test_assisted_acquisition.py`, `tests/test_catalog_bind_v1.py`, `tests/test_dse_motor_op_dual_truth.py`, `tests/test_phase2_lookup_operating_point.py`, `tests/test_propeller_catalog_bind_ux.py` — retarget any assertion that assumed overwrite-to-peak after a conditioned OP should have won.
4. **Copy:** unit or string assert that candidate/chosen formatting includes the honesty marker (or resolved conditioned form).

Run full suite; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | N1: `calculated` (and/or sync call) |
| `src/jarvis/core/motor_catalog_assist.py` | CLI honesty strings |
| `src/jarvis/core/orchestrator.py` | **Only if** N2 freeform re-resolve one-liner needed |
| `src/jarvis/core/project_closure.py` | **Only if** §3.4 stays localized |
| `tests/…` | regression + triage + copy |
| `.jes/artifacts/implementation_report_catalog_motor_thrust_not_intrinsic_b1.md` | write |

**Do not change:** `library/motores/_datos.json` numbers (unless a test-only comment), ESC/FC seeds, `ui/**`, `resolve_operating_point` ladder logic, package version.

---

## 6. Explicit non-goals

H2 optional schema · H3 rename · OP backfill for 20 motors · pose/fit/CAD · glyphs · ESC/FC/Here3 · Phase 2.5 hover rewrite · Continuity redesign · System Optimization · version bump · weakened tests

---

## 7. Done criteria

- [x] Exact/fallback OP thrust on motors component is `source="calculated"` (G5 gate) after `set_motor_component`.
- [x] Regression: conditioned thrust **survives** propulsion resolve/apply (13.4841 path).
- [x] Motor-only fallback/legacy numeric honesty preserved where appropriate.
- [x] CLI candidate/chosen lines no longer present catalog peak as a bare motor fact.
- [x] `10.042` test pins triaged/retargeted; suite green; count reported.
- [x] Implementation report written (include N1 path chosen; N2/N3.4 deferrals if any).
- [x] Cursor review PASS before Engineer close.

---

## 8. Stop conditions

Stop and ask before: making `thrust_n` optional, renaming fields, editing `resolve_operating_point` matching rules, large BOM redesign, pose/glyph work, or version bump.
