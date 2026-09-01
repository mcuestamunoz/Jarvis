# Investigation Review — Phase 2.7-B Parametric / Estimative Battery Model

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_phase27b_parametric_battery_estimate.md`](investigation_contract_phase27b_parametric_battery_estimate.md)  
**Report:** [`.jes/artifacts/investigation_report_phase27b_parametric_battery_estimate.md`](investigation_report_phase27b_parametric_battery_estimate.md)  
**Base:** tag `v0.3.5` / `checkpoint-phase25-hover-energy` · commit `fc46938`

## Verdict

**PASS WITH NOTES**

Investigation quality **ACCEPT**. Question was the estimative one (not P27-A validated/sourced). E-SWEEP is implementable under locks without a new subsystem. Gate D paper numbers reproduce. ★★13 pack-scope is homogeneous in the exercise. No FAIL criterion (no catalog R, no `P_battery`, no L1 relabel, no mixed-scope `V − IR`, no production code).

**Engineer physics pass (2026-09-01):** arithmetic of L1, base point, R=40 mΩ infeasible, and optimistic 1.51875 min **confirmed**. Corrections below (sweep vs L1 wording; OCV linear as hypothesis; IR leverage scoped to this model/grid) are **in this review**, not a rejection of the investigation.

**Principle (locked for IC):** the calculations are correct **inside the stated hypothetical model**. That does **not** show the model is representative of the real Combo A LiPo.

**Ready for Engineer ★1–★5.** IC draft **after** ★1 allows L2 in product. Do not implement before ★.

---

## Contract checklist

| Criterion | Result |
|---|---|
| Baseline @ `fc46938` | **Pass** — report: `src/` empty vs tag; Cursor: no L2 symbols in `src/jarvis` (`r_internal` / `v_oc` / endurance model) |
| Gates A–F answered | **Pass** |
| Mandatory table populated | **Pass** |
| ★★2 / ★★11 P26 + P27-A validated path unreopened | **Pass** |
| ★★3 L1 unchanged | **Pass** |
| ★★4 assumed ≠ sourced | **Pass** — Gate D Voc bookends labeled generic chemistry |
| ★★5 envelope, not a single YY min | **Pass** — E-R inner formula, E-SWEEP user-facing |
| ★★6 no physical lower-bound claim | **Pass** — envelope vs L1 is the demonstration |
| ★★8 no new subsystem | **Pass** — `tools/electricity.py`; empty `simulation/*.py` ruled out with both readings |
| ★★10 no production code | **Pass** |
| ★★13 pack vs cell | **Pass** — pack throughout; schema requires `r_internal_scope` / `voltage_scope`; mismatch → refuse |
| Combo A labeled paper | **Pass** — grids from contract; one added Voc polyline, labeled |
| INSUFFICIENT DATA allowed | N/A — not the outcome; PASS WITH NOTES matches sweep-only / no scalar UX |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| L1 formula 22.2 / (251.559×4)×60 = 1.3237 | **Confirmed** (same as P27-A) |
| Gate D base R=20 mΩ, I=68 A, Vcut=14.0 V → SOC=0.675, 0.4301 min | **Confirmed** — `SOC = (Vcut + IR − Voc_empty) / ΔVoc`; IR=1.36 V |
| R=40 mΩ same I/Vcut → infeasible | **Confirmed** — V_loaded(SOC=1)=16.4−2.72=13.68 V **< 14.0 V** |
| Envelope high end ≈1.52 min | **Confirmed** — optimistic corner R=10 mΩ, I=50 A, Vcut=13.2 V → **1.51875 min** (not in the abbreviated table; consistent with “full 24-point grid”) |
| `calculate_autonomy_min` lives in `tools/electricity.py` | **Confirmed** — `:25-38`; `calculation_engine.py` imports it |
| `simulation/energy_model.py` / `flight_model.py` empty | **Confirmed** — 0 bytes, v0.1 scaffold; Glob often skips empty files |
| No `P_battery` / L2 fields in code | **Confirmed** — grep |

---

## Review highlights

**Right question, right verdict.** P27-A closed *validated* loaded autonomy. This report answers *labeled estimate + which axis is worth measuring*. E-SWEEP wrapping E-R matches ★★5.

**Gate D is load-bearing.** At the labeled hypothesis I=68 A, Vcut=14.0 V pack, R from 20→40 mΩ pack is not a 10% tweak: V_loaded at SOC=100% is already **below cutoff** (13.68 V < 14.0 V) → **model infeasibility**, not a shorter time. **Within this L2 model and this hypothetical grid**, pack `R_internal` has high leverage on predicted cutoff-limited endurance. That is **not** an objective claim that IR measurement outranks M3 in general (M3 asks a different question: nameplate vs high-C capacity). Keep the M3 campaign parallel (★5).

**L1 is not a flight-time floor.** The sweep spans approximately **0–1.52 min**, with **most feasible grid points below L1 (1.3237 min)** and the **optimistic corner above L1** (1.51875 min at R=10 mΩ pack, I=50 A, Vcut=13.2 V pack). A point above L1 does **not** make L1 a physical lower bound; it is why ★★6 forbids that language.

**OCV line is a paper assumption.** Voc_full=16.4 V / Voc_empty=13.2 V pack with linear interpolation is a **mathematical hypothesis** for the exercise (generic 4S rest bookends), **not** a sourced characterization of `lipo_4s_1500mah`. The report Gate D provenance already states this; IC must keep it in every assumption record.

**Placement.** Extending `tools/electricity.py` is the live sibling. Do not revive 0-byte `energy_model.py`.

---

## Notes (non-blocking)

### Note 1 — Quantity is time-at-assumed-I, not manufacturer usable Wh

Gate D uses `endurance_min = (capacity_Ah × (1 − SOC_cutoff)) / I_load × 60`. That is **nominal-capacity coulomb-counting** at constant I until V_loaded hits cutoff — model-derived time, as required. Catalog `capacity_Ah` is the **nameplate** used by the model, not demonstrated available Ah at 50/68/90 A. It is **not** ∫V·I dt. IC must name it endurance/time, never “usable Wh” / catalog energy / actual battery endurance.

### Note 2 — Cell→pack ×4 is in the *assumption*, not the solver

Voc 16.4 / 13.2 V pack = 4× 4.1 / 3.3 V/cell, then the circuit is pack-only. Honest if provenance says so. IC: `estimate_loaded_endurance` takes **already-scoped** volts and ohms; **refuse** if `r_internal_scope != voltage_scope`; **no** silent `× cells` inside the formula.

### Note 3 — Opt-in, not every `build()`

Report: L2 only when the caller supplies an assumption record. Required. Auto-running a sweep on every calc would invent a default grid (Gate F forbids baking the grid into product).

### Note 4 — Sweep vs L1 (do not say “mostly below” without the corner)

Feasible points exist **below** L1; **infeasible** points are 0 min (not a time); the **optimistic corner is above L1** (1.51875 min). IC probe: at least one infeasible and one sustainable point; do not freeze 1.52 (or 0.43) as a product number.

### Note 5 — `I_load` “no cell/pack ambiguity”

True for 4S1P (same current in every cell). If a future pack is nP, current *split* becomes a scope issue. Out of Combo A / this IC; document as non-goal.

### Note 6 — Linear OCV(SOC) is not the SKU

`SOC = (V_oc − 13.2) / 3.2` is a **relation of the paper model**, not a property of `lipo_4s_1500mah`. Allowed in P27-B only as `source_type=assumed`. IC assumption records must repeat that the 16.4→13.2 V linear polyline is a mathematical hypothesis, not a characterization of the pack.

---

## Engineer ★ — Cursor lean (not decided)

| ★ | Lean | Rationale |
|---|---|---|
| **★1** | **Allow L2** in product, labeled ESTIMATIVE, sweep-only | Gate D has decision value; P27-A validated path stays closed |
| **★2** | **Sweep-only primary**; `n × I_hover` only as a **labeled** sweep point | No silent 68 A default |
| **★3** | **DSE must not read L2** | Frozen `_score_candidate`; which envelope point is a product question |
| **★4** | **`battery_endurance_envelope`** (list) + **`battery_endurance_assumption`** (JSON) | No scalar `_min` field |
| **★5** | **Keep M3 campaign parallel** | Different question (high-C Ah). **Within this L2 model and grid**, pack R has high leverage on cutoff-limited endurance — not a global “IR > M3” ranking |

---

## Recommended IC scope (post-★1 yes)

Bounded — **estimative endurance sweep**, not “realistic autonomy”:

1. `tools/electricity.py`: pure `estimate_loaded_endurance(...)` + scope-mismatch **refusal** (★★13); OCV polyline inputs labeled assumed  
2. Sweep wrapper: caller-supplied grid; **no** hardcoded default R/I/V  
3. `CalculationBundle`: envelope list + assumption JSON; **opt-in only**; outcomes include **infeasible** (not negative minutes)  
4. CLI block visually separate from L1; every R/V labeled assumed + pack\|cell; no “usable Wh”  
5. Probe: envelope shape (sustainable + infeasible); never one golden minute  

**Non-goals:** catalog JSON · `P_battery` · DSE · L1 · silent cell↔pack · usable-Wh wording · version bump  

---

## Next

```text
Engineer ★1–★5
      ↓
IF ★1 yes → implementation_contract_phase27b_parametric_battery_estimate.md
IF ★1 no  → L1-only until L3 data; this report still documents the paper envelope
```

No `src/` until IC approval.
