# Cursor review — Phase 2.7-B Implementation Contract (pre-implementer)

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES Engineer Interface)  
**Subject:** External contract+architecture review of IC v0.1, contrasted with repo  
**Authority:** last word on whether that review is correct before Claude Code  
**IC after this review:** [implementation_contract_phase27b_parametric_battery_estimate.md](implementation_contract_phase27b_parametric_battery_estimate.md) **v0.2**

---

## Verdict on the external review

**Architecture sections (1.1–1.4, 11–13): ACCEPT.**  
L1/L2 split, `tools/electricity.py`, DSE isolation, opt-in, CLI split, non-regression tests, and “do not relabel Gate D paper numbers as SKU truth” are correct against this tree.

**“BLOCKED until 4 contractual points”: PARTIALLY ACCEPT.**  
Two of the four are real domain holes that would let a passing test suite still emit nonsense. Two are overstated. Three “minor” notes are valid precision issues. One note invents a `ToolResult` API this repo does not have.

Investigation stays **closed**. No new physics. No P_battery. No catalog R.

---

## Finding-by-finding (repo-checked)

### F1 — `SOC_cutoff < 0` — **VALID, must lock**

Algebra of the locked model:

```text
SOC = (V_cutoff − V_oc_empty + I·R) / (V_oc_full − V_oc_empty)
SOC < 0  ⇔  V_loaded(SOC=0) > V_cutoff
```

Then `capacity × (1−SOC) / I` exceeds nameplate coulomb time `capacity / I`. That contradicts the already-ratified model (nameplate Ah coulomb-count, SOC is a fraction of that Ah). The paper grid never hits this (Vcut ≥ Voc_empty), but the IC accepts arbitrary caller numbers.

**Lock (model completeness, not new physics):** if cutoff is never reached inside SOC ∈ [0,1], endurance is nameplate `capacity_ah / I_load × 60`, `soc_at_cutoff = 0`, `stopping_condition = nameplate_exhausted`. Not a fourth physics theory.

### F2 — `SOC_cutoff == 1` — **VALID as underspecification, not a blocker of F1 weight**

Investigation Gate D already wrote `SOC ≥ 1 → infeasible`. Equality is measure-zero and unused by the paper cases.

**Lock:** evaluate in voltage space. `V_loaded(SOC=1) < V_cutoff` → `infeasible`. `V_loaded(SOC=1) == V_cutoff` → `sustainable`, `endurance_min = 0`, `stopping_condition = voltage_cutoff`. Zero minutes is a time; `None` is reserved for cannot-start.

### F3 — `R < 0` — **VALID, must lock**

IC already refuses `I <= 0`, `C <= 0`, non-finite, scope mismatch. Negative R makes `V_loaded > V_oc`. **Refuse** (`invalid_input`). **`R == 0` allowed** (ideal pack).

### F4 — `capacity_ah` provenance — **OVERSTATED as implementer blocker**

Solver stays a pure numeric function. Investigation Gate B already had `capacity_source: catalog_nameplate` on the **assumption record**, and IC v0.1 already fixed assumption JSON `source_type: "assumed"`.

**Lock (passthrough, no inference):** every envelope row and the assumption record **write** `source_type = "assumed"` (L2 is definitionally assumed). If the caller point includes `capacity_source`, copy it. If not, omit — do **not** invent `catalog_nameplate`. Solver does not grow new provenance parameters.

### F5 / §6 — origin of envelope `source_type` — **VALID, fold into F4**

Do not `point.get("source_type", "assumed")` as a read-side default. **Write** `"assumed"`.

### §7 — JSON string assumption — **ACCEPT, no change**

Same persistence pattern as `hover_energy_resolution: str | None` in `CalculationBundle`. Compatibility, not domain need.

### §8 — “byte-identical” — **VALID precision**

Adding `battery_endurance_* = None` changes `model_dump()` keys. Require **L1 semantic invariance** (`hover_energy_autonomy_min`, `autonomy_min` unchanged; new fields `None` without sweep). Not pickle/bytes identity.

### §9 — “dict or equivalent” — **VALID precision**

Sweep type is `list[dict[str, Any]]`. No new point class in this IC.

### §10 — `ToolResult` refusal — **CONCEPT VALID, API WRONG**

This repo’s `ToolResult` is `{tool_name, inputs, outputs}` only (`schemas/tool_schema.py`). There is **no** `success` / `error` / `result`. Refusal elsewhere uses `outputs={"reason": ...}` (e.g. `missing_energy_parameters`). v0.2 defines refuse vs infeasible **inside `outputs.outcome`**.

`infeasible` is a **successful model evaluation**, not a refusal.

### CLI / tests / paper R numbers — **ACCEPT** (reviewer §§11–13)

---

## What v0.2 does **not** do

- Reopen P27-A, P26, L1, DSE, catalog, `energy_model.py`
- Invent P_battery or SKU R/OCV
- Add a third user-facing autonomy scalar
- Change ★1–★5
