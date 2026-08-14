# Investigation Contract — G5 (DSE params vs iterate component dual-truth)

**Project:** Jarvis  
**Date:** 2026-08-14  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code (investigation + repro test; fix only if contract extended)  
**Reviewer:** Cursor  

**Status:** READY FOR ENGINEER → send to Claude  

**Type:** Investigation — state consistency bug (not UX, not catalog).  

**Origin:** CLI session `levantar-4kg-con-atonomia-de-70min` (`1f7e6e8d1a70`) + Engineer/JES review post-F-1.  

**Checkpoint base:** post-F-1 (commit `checkpoint-f1-reducir-payload` when landed).  

**Blocks:** H5/G1 design, Impl C — do **not** build objective-composite layer on unresolved state truth.  

**Workflow:** Investigate → repro test → short report → Engineer decides fix contract. **No commit/push unless Engineer asks.**

---

## 0. Intent

After a **params-only DSE apply** raises `motor_count` and `per_motor_max_thrust_n`, a subsequent **numeric iterate** (e.g. `safety_factor`) silently reverts thrust capacity:

```text
iter_010  dse_apply (estabilidad)   motor_count=10  thrust=67.5 N  → 675 N available
iter_011  iterate (safety_factor)   motor_count=4   thrust=20.0 N  → 80 N available
```

User sees a physics cliff with **no explanation**. This undermines trust in DSE + iterate sequencing.

**Hypothesis (strong):** `current_parameters` (DSE-written) and `design_properties.components["motors"]` (stale ComponentSpec: 4×20 N) diverge; iterate path re-syncs or rebuilds from component truth and **overwrites** DSE params.

Related: Impl B `invalidate_diverged_catalog_refs` may clear `catalog_ref` on thrust divergence — that part may be **correct**; the bug is params reverting to pre-DSE component numbers without narrating why.

---

## 1. Evidence (mandatory read)

| Artifact | Location |
|---|---|
| Final state | `workspace/levantar-4kg-con-atonomia-de-70min-1f7e6e8d1a70/state.json` |
| DSE apply snapshot | `history/iterations/iter_010.json` — `motor_count: 10`, `per_motor_max_thrust_n: 67.5`, `available_total_thrust_n: 675` |
| Iterate snapshot | `history/iterations/iter_011.json` — `motor_count: 4`, `per_motor_max_thrust_n: 20`, `available_total_thrust_n: 80` |
| Components (both) | `motors.properties`: `thrust_n=20`, `motor_count=4`, `catalog_ref=null` |

CLI transcript: Engineer session 2026-08-14 (F-1 validation + H1–H4 smoke).

---

## 2. Investigation questions (must answer in report)

1. **Exact code path** from `IterateAction.run` / `iterate_interactive_session` / `mutation_engine` that produces iter_011 params — where do `motor_count` and `per_motor_max_thrust_n` get set?
2. Does iterate **read** from `ComponentSpec` when recalculating after a partial param mutation?
3. Does DSE params-only apply **fail** to update `components["motors"]` while updating `current_parameters`? (expected today?)
4. Is `invalidate_diverged_catalog_refs` involved in the revert, or only catalog_ref clearing?
5. Are there **other** param pairs with the same hazard (battery_capacity_wh vs component, etc.)?
6. Minimal fix options (report only — do not implement unless Engineer extends contract):
   - A) DSE apply syncs mirrored fields into ComponentSpec when params-only
   - B) Iterate never downgrades params from stale components when params are newer / diverged
   - C) Single writer reconciliation helper post-mutation
   - D) Continuity/narration only (insufficient alone — document why)

---

## 3. IN SCOPE

| # | Work |
|---|---|
| 1 | Trace iter_010 → iter_011 in code (orchestrator, iterate action, writers, mutation_engine) |
| 2 | **Regression repro test** (new file e.g. `tests/test_g5_dse_iterate_dual_truth.py`) |
| 3 | Short report `.jes/artifacts/investigation_report_g5_dse_iterate_dual_truth.md` |

### Required repro test shape

```text
1) Project with motors component (thrust_n=20, motor_count=4 in ComponentSpec)
2) DSE apply (params-only) → motor_count=10, per_motor_max_thrust_n=67.5 persisted
3) Iterate safety_factor (or other numeric param) 
4) ASSERT motor_count and per_motor_max_thrust_n unchanged OR
   ASSERT explicit documented sync + user-visible reason if revert is intentional
```

Test must **fail on current main** demonstrating the bug (red test → investigation success).

---

## 4. OUT OF SCOPE

- H5 / G1 / composite objective implementation
- G3 handoff explore fix
- Catalog Impl C
- Full MIRRORED PARAM refactor
- Fixing in this contract (investigation only unless Engineer adds §Fix)

---

## 5. Deliverables

1. Investigation report with answers to §2 + recommended fix option  
2. Failing repro test (marked xfail or plain fail until fix contract)  
3. Optional: sequence diagram params vs components in report  

**No production fix in this contract.**

---

## 6. Acceptance (Cursor review)

**PASS** if repro test demonstrates the cliff and report identifies the exact write path.  
**FAIL** if inconclusive or fix implemented without approval.

---

## 7. Queue after G5

```text
G5 investigation PASS
        ↓
Engineer: fix contract (small)
        ↓
G3 — explore explicit vs handoff goal
        ↓
G1/G2 — requirements + H5 design
        ↓
UX catálogo → Impl C → BOM
```
