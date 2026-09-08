# Implementation Review — Catalog-bound Refresh B1

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_catalog_bound_refresh_b1.md](implementation_contract_catalog_bound_refresh_b1.md)  
**Report:** [implementation_report_catalog_bound_refresh_b1.md](implementation_report_catalog_bound_refresh_b1.md)  
**Buy:** ★ B1 — refresh-from-`catalog_ref`, **all five** bind families

## Verdict

**FAIL**

ESC / battery / propeller / frame refresh paths match the IC and the reported demo case. The **motor** family does **not**: dispatch passes `catalog_ref.sku` (a `str`) into `bind_motor_from_catalog`, which requires a `MotorSuggestion` dict. Cursor reproduced `AttributeError: 'str' object has no attribute 'get'`. Continuity phrase `actualiza motores` is therefore unsafe (orchestrator only catches `ValueError`).

Do **not** CLOSE. Do **not** Engineer-smoke motors until hotfix. ESC demo smoke may still proceed after hotfix lands (or Engineer may smoke ESC-only knowing motor is broken — prefer fix first).

---

## Checklist

| Criterion | Result |
|---|---|
| Writer via existing `bind_*` + `base=` | **Fail** — motor signature mismatch |
| Continuity IDLE phrases (5 families) | **Partial** — parse OK; motor write crashes |
| `mounted_on` preserved on ESC | **Pass** (T1 + independent probe) |
| Honest copy / no forbidden tokens | **Pass** (T5) |
| No Board-load / picker / seeds / version | **Pass** (`0.3.8`; no `library/` / Board) |
| Tests T1–T6 | **Pass as written** — gap: no writer test for motor |
| Full suite | **Pass** — Cursor **2403** |
| Frame children untouched | **Pass** — single-key write (report correct) |
| Report written | **Pass** |

---

## Independent verification

| Check | Result |
|---|---|
| ESC refresh 26→15 + `mounted_on` | **Pass** (tests + report dry-run claim) |
| `refresh(..., "motors")` with live SKU | **Fail** — `AttributeError` |
| battery / propeller / frame refresh | **Pass** (live SKU probe) |
| `pytest tests/test_catalog_bound_refresh_b1.py` | **18 passed** |
| `pytest -q` | **2403 passed** |
| Diff scope | `component_writers` · `catalog_refresh_assist` · `orchestrator` · tests · report — no seeds/Board/version |

---

## Blocking note — N1 Motor adapter (required hotfix)

`bind_motor_from_catalog(suggestion: MotorSuggestion, *, base=...)` is the only binder that does **not** take `sku: str`. Existing callers always pass a suggestion from assist/DSE.

**Minimum fix (no new binder, no IC reopen):** in `refresh_component_from_catalog`, for `family == "motor"`:

1. `lib.get_motor(sku)`  
2. `motor_spec_to_suggestion(...)`  
3. `bind_motor_from_catalog(suggestion, base=spec)`

Add **T1-motor** (stale `weight_g` or dim → seed; `mounted_on` preserved if set). Optionally catch non-`ValueError` only if something else surfaces — prefer fixing the call shape.

---

## Non-blocking notes

### N2 — Demo project still stale

Expected until Engineer Continuity smoke: `actualiza el esc desde catálogo` on `autonomía-de-10min-…`.

### N3 — T6 smoke used mount **clear**, not declare SET

Still exercises the mounted_on IDLE bridge; acceptable.

### N4 — Float equality in `diff_refreshed_properties`

As report flags; fine for this cycle.

---

## Phase

Implementation **not closable**. Claude: motor-adapter hotfix + T1-motor → Cursor re-review → Engineer ESC smoke → then CLOSE Fase 1 refresh B1.
