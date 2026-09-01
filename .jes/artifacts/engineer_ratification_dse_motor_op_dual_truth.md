# Engineer Ratification — DSE ↔ Motor OP Voltage Coherence

**Date:** 2026-08-31  
**Authority:** Engineer (via JES / Cursor review ratification post field-walk + investigation)  
**Investigation:** [report](investigation_report_dse_motor_op_dual_truth.md) · [review PASS WITH NOTES](investigation_review_dse_motor_op_dual_truth.md)  
**Contract:** [investigation_contract_dse_motor_op_dual_truth.md](investigation_contract_dse_motor_op_dual_truth.md)  
**Baseline:** tag **`v0.3.3`** / **`checkpoint-validation-case-regression-gate`** · commit `ceb44b4`  
**Origin:** CLI field walk `autonomía-15-min` (`7efc98205ee6`) @ v0.3.3

---

## Ratification status

**LOCKED** — pending Implementation Contract draft + Engineer approval of IC scope before any `src/` change.

---

## ★ Decisions (locked)

### ★1 — Conceptual direction: **(2) No `exact_operating_point` lock-in from unknown voltage**

**Ratified:** Do **not** select an `exact_operating_point` row when `voltage_v is None` at resolution time. Require a real, bound-battery voltage (catalog nominal or derived cell count) before a curated exact row can qualify.

**Rationale (Engineer/JES):**

- Closes the stale-OP bug **at source** (motor/prop bind before battery no longer freezes a voltage-unvalidated exact match).
- Preserves P2-2/IC2 intent for the **compatible** case: once OP is resolved with a **known** voltage, a later compatible battery bind must not needlessly downgrade (existing regression test remains valid for that scenario).
- Aligns with deterministic engineering truth: exact OP is a voltage-specific claim, not a voltage-agnostic guess.

**Explicitly NOT ratified:** Direction (1) — blanket re-validation on every battery bind without distinguishing “never validated” vs “already validated at compatible voltage”. May be revisited only as a **narrow** complement inside the IC if (2) alone leaves an edge case — not as the primary fix.

**Frozen surfaces unlocked for IC (only):**

- `resolve_operating_point` matching priority (`library.py` — `voltage_v is None` clause)
- Resolver / acquisition sequencing docs as needed to narrate “exact OP after battery voltage known”

**Still frozen without new ★:**

- H5, G24-B, battery/ESC data curation
- FN-R1–R5 routing UX (separate arc if ever scheduled)

---

### ★2 — Parallel safe cut (Option D, acotado): **YES — ship as optional first slice**

**Ratified:** A bounded **explore/apply coherence** slice using `effective_motor_power_w()` on **both** paths is approved **in parallel** with ★1, with these locks:

| Allowed | Forbidden |
|---|---|
| Explore baseline + apply use the **same** power authority as live `calcular`/`simular` | Making both paths **consistently wrong** by blindly copying stale `motor_op_power_w` without ★1 |
| `estado`/explore message honesty when OP was resolved under unknown voltage (read-only flag/warning) | Changing resolver matching rules under the Option D slice alone |
| Reduces user-visible cliff (e.g. 12.8 min promised → 7.7 delivered) | Claiming Option D fixes physics without ★1 |

**Ordering:** Option D may land **before** ★1 resolver change if IC is split into two slices; Option D alone is **not** sufficient for arc closure.

---

### ★3 — CASE C fixture: **Accept A+B as sufficient evidence**

**Ratified:** Do **not** block IC on reproducing the battery-candidate viable→fail margin cliff (CASE C skip). CASE A + B conclusively demonstrate the mechanism with field-walk-matching numbers.

Optional: add CASE C post-fix only if a natural fixture emerges from ★1 implementation — not a gate for IC draft.

---

### ★4 — P2-2 regression contract: **Extend, do not weaken**

**Ratified:** `test_battery_pick_does_not_regress_already_resolved_propulsion_op` (P2-2) **remains** for the voltage-**compatible** battery-bind scenario.

The IC **must** add a sibling test:

- Motor + prop bound **with known voltage** → exact OP locked → compatible battery bind → OP unchanged (**existing**).
- Motor + prop bound **before** voltage known → **no** exact lock (★1) → battery bound → honest resolution at real voltage (**new**).

Do **not** silently delete or xfail the P2-2 test without replacing its scenario coverage.

---

## Recommended IC structure (for Cursor draft — not implemented here)

```text
Arc: Motor OP Voltage Coherence @ v0.3.3 baseline

Slice 1 (optional, ★2): DSE explore/apply effective_motor_power_w coherence + honesty surface
Slice 2 (required, ★1): Resolver — no exact match from voltage_v=None; acquisition/estado narrative

Gate:
  - tests/test_dse_motor_op_dual_truth.py CASE A+B flip to PASS
  - P2-2 sibling test added (★4)
  - Full suite green (no intentional failing repro tests post-fix)
  - Probe: cli_probe_dse_motor_op_dual_truth.py (mirror field walk)
  - src/ diff scoped to resolver + DSE coherence only
```

**Working title:** `implementation_contract_motor_op_voltage_coherence.md`

---

## Explicit deferrals (unchanged)

| Item | Status |
|---|---|
| H5 ESC catalog | Frozen |
| G24-B `_score_candidate` rewrite | Frozen |
| Battery/ESC data curation | Engineer/research — not this IC |
| FN-R1–R5 acquisition routing | Separate investigation if scheduled |
| Version bump | After IC review + checkpoint — target **v0.3.4** candidate |

---

## Next step (workflow)

```text
Engineer ★ locked (this document)
  ↓
Cursor: implementation_contract_motor_op_voltage_coherence.md
  ↓
Engineer approves IC scope
  ↓
Claude implements → review → probe → checkpoint v0.3.4
```

**Do not implement until IC is explicitly approved.**

---

**End of ratification.**
