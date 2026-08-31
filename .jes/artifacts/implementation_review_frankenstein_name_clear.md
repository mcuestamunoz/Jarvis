# Implementation Review — Frankenstein `.name` Clear (IC D)

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_frankenstein_name_clear.md`](implementation_contract_frankenstein_name_clear.md)  
**Report:** [`.jes/artifacts/implementation_report_frankenstein_name_clear.md`](implementation_report_frankenstein_name_clear.md)  
**Base:** tag `v0.3.1` / `checkpoint-next-engineering-block` · commit `30c9aec`

## Verdict

**PASS WITH NOTES**

All G24D-1…G24D-5 contract gates met. Micro-IC scope discipline verified: **`catalog_bind.py` is the only `src/` file this IC touches.** G5 invalidate **conditions** and battery branch byte-identical; only the motor divergence `model_copy` payload gains `.name`. Investigation §6.1 trust gap closed at source — BOM/`estado` motor identity line no longer displays the stale SKU string.

**Defect-first review:** No open findings that block combined checkpoint with IC C.

---

## Contract checklist (§6)

| Criterion | Result |
|---|---|
| §6.1 repro: post-divergence `.name` honest; motor line no stale SKU | **Pass** — live probe + `test_frankenstein_entry_after_g5_divergence_is_not_resolved` |
| G5 semantics preserved (`catalog_ref` cleared; `sku_resolved=False`) | **Pass** — probe steps 2, 5; BOM assertions unchanged |
| Frankenstein BOM test updated with disclosed assertion change | **Pass** — §3 disclosure accepted |
| Probe 5/5; full suite green | **Pass** — **5/5**, **2028/2028** |
| IC D `src/` touch set only `catalog_bind.py` | **Pass** — `design_explorer.py` / `orchestrator.py` are IC C only |
| G5 invalidate conditions unchanged | **Pass** — divergence `if` block identical |
| Readiness / BOM `[sku]` rules not weakened | **Pass** — `format_bom_lines` / `_bom_sku_resolved` untouched |
| Not undifferentiated mega-IC with IC C | **Pass** — independently reviewable diffs |

---

## Independent verification

```text
pytest tests/test_impl_d_sku_bom.py              → 12 passed (3 new G24D tests)
pytest tests/ (full)                             → 2028 passed
cli_probe_frankenstein_name_clear.py             → 5/5 PASS
cli_probe_g24_viable_selection_honest_cta.py     → 6/6 PASS (IC C regression)
cli_probe_g24_apply_by_index.py                  → 6/6 PASS (G24-A regression)

git diff HEAD -- src/jarvis/core/catalog_bind.py
  → _DIVERGED_MOTOR_NAME constant + motor model_copy adds "name" key only

Live §6.1 repro (probe):
  catalog_ref: None
  name:        motor (parámetros divergentes)
  BOM line:    ✓ motors: motor (parámetros divergentes) qty=6 (high)
```

---

## Code review highlights

**G24D-1 — minimal source fix.** `_DIVERGED_MOTOR_NAME = "motor (parámetros divergentes)"` set in the same `model_copy` that clears `catalog_ref`. Correct placement: only the motor divergence path where G5 already decided to invalidate. Battery branch still `model_copy(update={"catalog_ref": None})` only — verified by `test_battery_divergence_does_not_rename_motor` with `is` identity on motor spec.

**Label choice (§2.4).** Non-SKU-shaped (spaces, parens, accent); `default_library.has_motor()` false. Does not imply resolved binding — satisfies trust contract without touching BOM heuristics.

**Negative tests lock scope.** `test_motor_name_unchanged_when_catalog_ref_preserved` asserts pure no-op (`updated_components is components`) when thrust matches. Prevents accidental rename on unrelated paths.

---

## Disclosed changes — accepted

1. **`test_frankenstein_entry_after_g5_divergence_is_not_resolved`** — contract-pre-authorized assertion flip from stale-SKU encoding to honest-label encoding. Docstring updated. Additional `_SKU not in motor_line` assertion strengthens the fix beyond bracket-only checks.

2. **`test_bound_motor_aplica_la_mejor_clears_catalog_ref`** (IC C file, not IC D touch table) — necessary side-effect fix when both ICs land in same tree. Disclosure in IC D report accepted; does not expand IC D `src/` scope.

3. **Probe step 4 scope narrowing** — Continuity `"Catálogo: candidatos …"` line may legitimately re-suggest the same SKU as a fresh pick (contract §5 non-goal). Probe correctly checks only the motor's own identity line in BOM and `estado` "Componentes / gaps". No source change required — probe assertion correction only.

---

## Notes (non-blocking)

### Note 1 — Combined tree, separate reviews

Working tree carries IC C + IC D together (**2028 tests** = 2013 baseline + 12 IC C + 3 IC D). Each IC's `src/` delta is disjoint and independently PASS. Ready for single Engineer checkpoint per ★6.

### Note 2 — Continuity catalog suggestions unchanged

Post-divergence, `estado` may still list the old SKU under Continuity evidence as a **new** catalog candidate for the expanded design space. That is correct product behavior, distinct from the stale-identity bug IC D fixes. Remains separate debt if UX polish is ever wanted.

### Note 3 — Section header comment stale in test file

`test_impl_d_sku_bom.py` section comment `# 3. Frankenstein: catalog_ref cleared, .name retained` predates IC D — behavior is now "`.name` cleared to honest label". Cosmetic only; test docstring is accurate.

---

## Deferred Queue arc — closure

```text
IC C (G24 Viable Selection + Honest CTA)  — PASS WITH NOTES ✓
IC D (Frankenstein .name Clear)             — PASS WITH NOTES ✓
        ↓
Engineer: single checkpoint + 0.3.x (★6)
```

No tag, no version bump in this review.

---

**End of review.**
