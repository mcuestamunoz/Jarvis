# Investigation Review — G5 (DSE params vs iterate dual-truth)

**Date:** 2026-08-14  
**Reviewer:** Cursor (JES)  
**Contract:** `.jes/artifacts/investigation_contract_g5_dse_iterate_dual_truth.md`  
**Report:** `.jes/artifacts/investigation_report_g5_dse_iterate_dual_truth.md`  
**Base:** `checkpoint-f1-reducir-payload`

## Verdict

**PASS**

Bug confirmed, reproduced, root cause isolated to line-level precision. Zero `src/` changes (investigation-only, as scoped). Hypothesis in the contract was correct; report adds a second call site and a latent torque instance of the same class.

## Checklist

| Gate | Result |
|---|---|
| Repro matches CLI cliff (675→80 / elevate→revert) | **Pass** |
| Exact write path identified | **Pass** — `iterate.py:197-200` |
| Q1–Q6 answered | **Pass** |
| `invalidate_diverged_catalog_refs` ruled out | **Pass** (Q4 + control test) |
| DSE apply itself not the revert site | **Pass** (control test) |
| Failing repro test (`xfail(strict=True)`) | **Pass** — reviewer re-run: 1 xfailed, 2 passed |
| Full suite green | **Pass** — 1683 passed, 1 xfailed |
| No production fix in this cut | **Pass** |
| Fix recommendation concrete | **Pass** — Option A (+ C packaging) |

## Code review highlights

**Root cause is solid.** After params-only DSE elevates `current_parameters`, `design_properties.components["motors"]` stays at 4×20. Every physical iterate turn then calls:

```text
resolve_propulsion_parameters(components) → PhysicalOverride.apply_to(params)
```

unconditionally — even when mutating `safety_factor`. Stale component wins; DSE elevation is clobbered.

**FN-004 structural-confirm blindness** is a sharp finding: the gate compares old vs new *before* the revert at line 200, so it never sees the motor_count change. Ordering bug, not a missing feature.

**Second call site** (`param_definition_session.py:765-768`) correctly identified — same hazard on DEFINE_MISSING recalculation. Option A (sync components on DSE apply) fixes both without touching either caller.

**Scope discipline** — clean. No H5/G1/G3/Impl C drift.

## Notes (non-blocking)

1. Option A recommendation accepted as primary direction for the fix contract.  
2. Latent `per_actuator_torque_nm` hazard should be named in fix test coverage even if no DSE grid exercises it today.  
3. Property `source` tagging after DSE sync (`declared` vs DSE-derived) is a presentation decision — fix may use a provisional tag and defer Continuity/BOM copy.

## Queue

```text
G5 investigation PASS
        ↓
Fix contract Option A (shared sync helper on DSE params-only apply)
        ↓
G3 handoff explore
        ↓
G1/G2 + H5 design
```
