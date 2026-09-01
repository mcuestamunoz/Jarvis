# Investigation Review — DSE ↔ `motor_op_power_w` Dual-Truth (Post-P2-2)

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_dse_motor_op_dual_truth.md`](investigation_contract_dse_motor_op_dual_truth.md)  
**Report:** [`.jes/artifacts/investigation_report_dse_motor_op_dual_truth.md`](investigation_report_dse_motor_op_dual_truth.md)  
**Ratification:** [`.jes/artifacts/engineer_ratification_dse_motor_op_dual_truth.md`](engineer_ratification_dse_motor_op_dual_truth.md)  
**Base:** tag `v0.3.3` / `checkpoint-validation-case-regression-gate` · commit `ceb44b4`

## Verdict

**PASS WITH NOTES**

Contract gates met. Root cause traced one level deeper than the contract hypothesis — reframing is **correct and evidenced**. Repro tests fail on baseline with field-walk-matching numbers. Zero `src/` diff. Engineer ★1–★4 ratified in companion artifact.

**Defect-first review:** No open findings that block IC draft. CASE C skip is honestly disclosed and accepted per ★3.

---

## Contract checklist (§4–§6)

| Criterion | Result |
|---|---|
| Q1–Q9 answered with file:line citations | **Pass** — report §4 |
| Repro tests CASE A + B fail on baseline | **Pass** — verified independently |
| CASE C attempted / skip justified | **Pass WITH NOTE** — see Note 1 |
| No production fix / no version bump | **Pass** |
| Fix options analyzed; no unilateral pick | **Pass** — ★ table in report §7 |
| Does not reopen G5 / P2-1 / Validation Case without proof | **Pass** |
| `src/` zero diff | **Pass** |

---

## Independent verification

```text
pytest tests/test_dse_motor_op_dual_truth.py -v
  → 1 passed, 2 failed (expected), 1 skipped

pytest tests/ -q
  → 2030 passed, 2 failed, 1 skipped

git diff --stat src/
  → (empty)

library.py:606-609 — voltage_v is None → voltage_matches True  ✓

Field-walk numbers (fixture):
  explore baseline     8.325  vs  live calc  7.7083
  explore promise #1  12.8077 vs  post-apply 7.7083
```

---

## Review highlights

**Root cause depth.** The investigation correctly identifies that `resolve_operating_point`'s `voltage_v is None` clause treats unknown voltage as universal match, allowing exact OP lock-in before battery voltage exists — then P2-2/IC2's deliberate non-re-call of `set_motor_component` on battery-only bind freezes incoherent OP indefinitely. Explore's `apply_components_delta({})` re-derivation is the **more honest** half — not the buggy half.

**Option A correctly rejected.** Preserving stale `motor_op_*` in explore would extend the honesty bug, not fix it.

**Architectural trade-off named honestly.** ★1 is a product/architecture choice between two prior frozen decisions (resolver priority vs P2-2 stability). Investigator did not overreach by picking unilaterally — appropriate.

**CASE A+B sufficient.** Mechanism and user harm fully demonstrated; margin-cliff (CASE C) is secondary manifestation.

---

## Notes (non-blocking)

### Note 1 — CASE C skip

Battery-only viable candidate did not appear in fixture even after two-round sequence. Acceptable per contract §3 "if reproducible without fragile tuning". ★3 ratified: do not block IC.

### Note 2 — Failing tests in main suite

Post-investigation suite shows **2 intentional failures** until IC fixes land. CI must treat this as **pre-fix gate state** — IC acceptance criterion must flip CASE A+B to PASS and restore full green.

### Note 3 — Option D scope

Ratified ★2 allows symptom-relief slice only with honesty surface — not as arc closure without ★1 resolver change.

---

## Engineer ★ alignment

| ★ | Report question | Ratification |
|---|---|---|
| **★1** | Re-validate on bind vs no exact from unknown voltage | **(2) No exact from unknown voltage** |
| **★2** | Option D parallel cut | **Yes, acotado** |
| **★3** | CASE C follow-up | **A+B sufficient** |
| **★4** | P2-2 test conflict | **Extend with sibling test; do not weaken** |

Full lock: [engineer_ratification_dse_motor_op_dual_truth.md](engineer_ratification_dse_motor_op_dual_truth.md)

---

## Next step

```text
Investigation PASS WITH NOTES
  ↓
Engineer ★ locked
  ↓
Cursor: implementation_contract_motor_op_voltage_coherence.md
  ↓
Engineer approves IC → implement → review → probe → checkpoint (v0.3.4 candidate)
```

---

**End of review.**
