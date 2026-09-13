# Implementation Review — Craft montage Path F on plate B1

**Date:** 2026-09-13  
**Reviewer:** Cursor (Engineer Interface) — independent of implementer session  
**Against:** [IC](implementation_contract_geometry_craft_montage_path_f_b1.md) · [report](implementation_report_geometry_craft_montage_path_f_b1.md)

**Verdict:** **PASS WITH NOTES**

---

## Checklist

| Gate | Result |
|---|---|
| Path F only; Path N never proposed | **Pass** — `_STACK_SUBJECTS` fixed; motors/props excluded; writer disk gate still raises (T7) |
| Locked arithmetic `z = H_p/2 + H_c/2`, x=y=0 | **Pass** — T1 + live 10min numbers (e.g. esc z=5.0 on H=2 plate) |
| Estimated plate allowed + disclosure | **Pass** — T2; live 10min reason includes ESTIMATED_TEMPORARY; Cursor drove `cabe` → estimated_dims refusal (gate unweakened) |
| Subjects FC/ESC/battery/sensors box-only | **Pass** |
| Origin: one plate / AMBIGUOUS if 2+ | **Pass** — T3/T4; live both projects: single `frame_plate` boxed |
| Suggest-only IDLE; confirm = retype existing pose bridge | **Pass** — T6/T7; no new writer |
| No workspace mutation / no version bump | **Pass** — report + `0.4.1`; suite **2813** (Cursor re-ran) |
| Project-agnostic (no MY5/10min literals) | **Pass** — T8 |
| Non-goals (layout-pack, Product B, mounts auto-write) | **Pass** |
| Report + T1–T9 coverage | **Pass** |
| Live reproducibility narrative | **Pass WITH N1** — 10min proposes 4; 5min all already posed (expected) but **format copy wrong** (below) |

---

## Independent checks (Cursor)

1. `pytest tests/test_geometry_craft_montage_path_f_b1.py` → **17 passed**.  
2. Full suite → **2813 passed, 1 skipped**.  
3. Live `propose_path_f_stack` on `state.json`:  
   - **10-min:** 4 proposals, estimated disclosure, phrases ready.  
   - **5min:** plate boxed; all four subjects already posed → **zero** proposals (correct skip policy).  
4. Orchestrator: pose on estimated plate then `cabe el esc` → estimated_temporary refusal (unchanged screening).  
5. Module has no project-id / MY5 string branches.

---

## Notes

| ID | Severity | Note |
|---|---|---|
| **N1** | **Should fix before / during smoke** | When plate **exists** but every stack subject is already posed, `propose_path_f_stack` returns `[]`, and `format_path_f_stack([])` prints **“no hay una placa con caja declarada”** — **false** on 5min. Report correctly says “nothing to propose”; the **user-facing string lies**. Prefer a distinct empty message: *“placa OK; nada que proponer (sujetos ya tienen pose o sin caja)”* when origin resolves but proposal list is empty. Small follow-up; does not invalidate 10min Path F. |
| **N2** | Smoke hygiene | 5min: clear a pose first (`quita la pose del esc`) **or** smoke Path F on **10min** first (clean). Report already warned. |
| **N3** | Optional | Lock #5 “Top/main label” preference among multiple boxed plates not implemented — any 2+ boxed → AMBIGUOUS. **Stricter/safer** than guessing Top; OK. |
| **N4** | Cosmetic | Disclaimer “no VERIFICADO” (caps) reads as refusal in context — OK; not a Product B claim. |

---

## Verdict

**PASS WITH NOTES** — mechanism matches IC; suite green; 10min ready for Engineer smoke.  

**Before calling smoke ACCEPT on 5min:** either apply N1 copy fix, or smoke with eyes open that empty checklist currently mis-says “no plate.”

**Next:** Engineer smoke §3 (prefer **10min** first → retype one phrase → Board). Then layout-pack XY / plate caliper / silhouette remain gated.
