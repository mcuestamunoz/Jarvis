# Implementation Review — Propeller Catalog Bind UX

**Date:** 2026-08-21  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_propeller_catalog_bind_ux.md`](implementation_contract_propeller_catalog_bind_ux.md)  
**Report:** [`.jes/artifacts/implementation_report_propeller_catalog_bind_ux.md`](implementation_report_propeller_catalog_bind_ux.md)  
**Base:** tag `checkpoint-phase2-p2-1` · commit `e82b8a1`

## Verdict

**PASS WITH NOTES**

Prop-1…Prop-7 match the IC. ★4 starvation fix is real and correctly implemented. ★5 re-call of `set_motor_component` is correct. Definitive product CLI (`fallback → exact` without patches) is proven by the probe (6/6), re-run green in this review. Prop-5 IDLE wiring does not steal the motor-first / both-bound cases under the locked predicates.

**Defect-first review:** No open findings that block checkpoint.

## Engineer gates (explicit)

| Gate | Result |
|---|---|
| Definitive CLI: `emax_rs2205s_2300` → fallback 10.042 → `ayúdame a elegir` → `hq_5045_bn` → exact 9.7086 (no `bind_propeller` patch) | **Pass** — probe steps 1–5; re-run `6/6 PASS` |
| Prop-5 IDLE does not hijack normal IDLE | **Pass** — see matrix below |
| ★4 both blocks gated on `_wants_catalog_help` | **Pass** |
| G21 motor help-choose unbroken | **Pass** — probe step 6 + suite |

### Prop-5 IDLE matrix (code + tests)

| Motor | Hélice | Expected | Evidence |
|---|---|---|---|
| stub | stub | motor / existing | Propeller help returns `None` while motors stub (`_is_stub_or_absent`); motor assist keeps priority |
| catalog | stub | hélice | Motor assist `None` (catalog_ref set) → propeller assist opens; probe + wizard tests |
| catalog | freeform | hélice | `_wants_catalog_help` true without catalog_ref; `test_propeller_idle_help_choose_when_freeform_unbound` |
| catalog | catalog | nada | Both assists `None`; no picker noise; `test_propeller_idle_help_choose_noop_when_catalog_ref_set` |
| freeform | stub | motor | Motor assist opens upgrade/energy path before propeller; propeller never claims first |
| none | none | motor / existing | Unchanged FN-005 / energy / propulsion missing routes |

## Checklist

| Gate | Result |
|---|---|
| Prop-1 `propeller_suggestions` | **Pass** |
| Prop-2 `propeller_catalog_assist.py` (import, not duplicate) | **Pass** — `motor_catalog_assist.py` untouched |
| Prop-3 priority-gated dispatch | **Pass** |
| Prop-4/★5 OP re-resolve after pick | **Pass** — 9.7086 N, no battery |
| Prop-5 IDLE fallback | **Pass** |
| Prop-6 acquisition brief | **Pass** (diff present) |
| Prop-7 tests + probe | **Pass** — 8 new + probe 6/6; targeted 31 green |
| No OP resolver / writers / library physics change | **Pass** |
| G21 test rewrite disclosed, not weakened | **Pass** — see Notes |

## Code review highlights

**★4 predicates match the IC.** `_is_stub_or_absent` / `_wants_catalog_help` at module level; dispatch uses live components, not bare membership. Motors-first when both want help is preserved (`test_motors_help_choose_wins_when_both_incomplete`).

**★5 is minimal.** `_apply_component_propeller_catalog_pick` binds propeller, then re-calls `set_motor_component` only when motors has motor `catalog_ref`. No new refresh helper; `component_writers.py` untouched.

**Suggestions honesty.** Empty list when no bound motor + honest formatter path — no full-catalog dump (G22 spirit).

**G21 regression test update is legitimate.** Old assertion forbade *any* `component_description_prompt` after motor bind; Prop-5 makes propeller picker correct for that fixture. New asserts guard the real bug (never reopen `["motors"]`) and require any picker to be `["propellers"]`. Stricter on the intended regression, not weaker. Accepted.

## Notes (non-blocking)

1. **No single parameterized IDLE-matrix test** covering all six rows in one table — coverage is piecewise + code structure. Optional follow-up; not required to checkpoint.

2. **Predicate helpers live only in `orchestrator.py`** (report §7.2) — acceptable for this cut; future share with `still_missing` is cleanup, not debt that blocks.

3. Untracked deliverables at review time (IC/report/investigation/tests/probe) — include in the commit when Engineer asks; exclude `workspace/` and the old g21 probe unless wanted.

## Next step

Engineer: short CLI walk (optional — probe already is the definitive path) → **commit + checkpoint** (e.g. `checkpoint-propeller-catalog-bind`) → **consider version bump** (`0.2.0` → `0.3.0`) now that P2-1 + Propeller UX is a closed user-visible block.  
G24–G27 / battery UX / ESC remain deferred.
