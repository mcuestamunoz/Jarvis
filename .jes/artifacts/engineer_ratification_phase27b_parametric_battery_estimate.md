# Engineer Ratification — Phase 2.7-B Parametric / Estimative Battery Model

**Date:** 2026-09-01  
**Authority:** Engineer (“ratifico” ★1–★5 as tabled)  
**Investigation:** [report PASS WITH NOTES](investigation_report_phase27b_parametric_battery_estimate.md) · [review PASS WITH NOTES](investigation_review_phase27b_parametric_battery_estimate.md)  
**Contract (investigation):** [investigation_contract_phase27b_parametric_battery_estimate.md](investigation_contract_phase27b_parametric_battery_estimate.md)  
**Baseline:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** · commit `fc46938`

---

## Ratification status

**LOCKED.** L2 estimative sweep **allowed in product**, labeled ESTIMATIVE.  
P27-A validated loaded autonomy remains **NO IC**. `PHASE26_P_BATTERY_BOUNDARY` and `PHASE27_LOADED_BATTERY_BOUNDARY` stay frozen for unlabeled / “realistic” / sourced-SKU claims.

**Principle:** Gate D arithmetic is correct **inside the hypothetical model**. That does **not** show the model represents the real Combo A LiPo.

---

## ★ Decisions (locked)

| ★ | Decision |
|---|---|
| **★1** | **Yes** — L2 in product, labeled ESTIMATIVE, sweep-only. Not “autonomía real”. |
| **★2** | **Sweep-only primary.** `n × motor_hover_current_a` only as a **labeled** sweep point. No silent 68 A default. |
| **★3** | **DSE must not read L2.** |
| **★4** | Names: **`battery_endurance_envelope`** (list) + **`battery_endurance_assumption`** (JSON). No scalar `_min` field. |
| **★5** | **M3 data campaign stays parallel.** IR leverage is **only** within this L2 model and grid — not a global IR > M3 ranking. |

---

## Additional locks (from Engineer physics pass)

- Linear OCV 16.4→13.2 V pack is a **paper hypothesis**, not SKU characterization. Must appear in every assumption record when that polyline is used. **Not** a default inside `electricity.py`.
- Endurance is **nominal-capacity coulomb-counting time** at assumed I, not usable Wh, not actual battery endurance.
- Sweep vs L1: range ~0–1.52 min in the paper grid; feasible points may lie below **or** above L1 (optimistic corner 1.51875 min). L1 is **not** a physical lower bound.
- Infeasible load → **infeasible** outcome, not negative minutes.
- ★★13: pack vs cell explicit; no silent conversion; no mixed-scope `V − IR`.

---

## Next

[`implementation_contract_phase27b_parametric_battery_estimate.md`](implementation_contract_phase27b_parametric_battery_estimate.md) — implement only after Engineer accepts that IC (or says implement).
