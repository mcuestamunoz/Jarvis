# Implementation Contract — Phase 2.7-B Parametric / Estimative Battery Endurance Sweep

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR IMPLEMENTER — **v0.2** (contract clarification 2026-09-01). Engineer ★1–★5 unchanged.

**Type:** Deterministic **labeled estimative** battery endurance (E-SWEEP wrapping E-R). **Not** validated flight time. **Not** `P_battery`. **Not** catalog R/OCV. **Not** DSE. **Not** L1 change.

**Investigation:** [report](investigation_report_phase27b_parametric_battery_estimate.md) · [review](investigation_review_phase27b_parametric_battery_estimate.md)  
**★:** [engineer_ratification_phase27b_parametric_battery_estimate.md](engineer_ratification_phase27b_parametric_battery_estimate.md)  
**Pre-implementer IC review:** [implementation_contract_review_phase27b_parametric_battery_estimate.md](implementation_contract_review_phase27b_parametric_battery_estimate.md)

**Checkpoint base:** commit **`fc46938`** · tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`**

### v0.2 changelog (vs v0.1 READY text)

Does **not** reopen investigation or ★1–★5. Completes input/output semantics so the formula cannot emit super-nameplate time or accept negative R:

1. Endpoint evaluation in voltage space; `SOC_cutoff < 0` → nameplate coulomb time (`stopping_condition=nameplate_exhausted`).
2. `V_loaded(SOC=1) < V_cutoff` → `infeasible`; equality → `sustainable` / `0` min.
3. `r_internal_ohm < 0` → refuse; `R == 0` allowed.
4. Envelope `source_type` is **written** `"assumed"`; optional `capacity_source` passthrough; solver stays numeric.
5. Sweep type is `list[dict[str, Any]]` (no “or equivalent”).
6. Refuse vs infeasible defined on real `ToolResult` (`outputs.outcome`), not a fictional `success`/`error` API.
7. L1 acceptance is **semantic** (values + new fields `None`), not `model_dump()` byte identity.

---

## 0. Engineer ★ (locked)

| ★ | IC obligation |
|---|---|
| **★1** | Ship L2 as ESTIMATIVE sweep only |
| **★2** | No default `I_load`; labeled `n×I_hover` only if caller puts it in the sweep |
| **★3** | Zero `design_explorer.py` / `_score_candidate` reads of L2 fields |
| **★4** | `battery_endurance_envelope` + `battery_endurance_assumption` only |
| **★5** | Do not mention M3 as superseded; do not bake “measure IR first” into UX copy as a global ranking |

**Principle:** numbers are correct **inside the caller’s model**. Never present as SKU truth or flight time.

---

## 1. Intent

Add a **pure formula** + **caller-supplied sweep** that, given assumed pack-or-cell scoped OCV bookends, R, I, cutoff, and **nameplate** `capacity_ah`, reports:

- `sustainable` → `endurance_min` (coulomb-count time at constant I until **either** V_loaded hits cutoff **or** nameplate SOC is exhausted)
- `infeasible` → load cannot stay at/above cutoff even at SOC=100% (`endurance_min=None`, not negative time, not `0.0` pretending to be a duration)
- `refused` → invalid / mixed-scope inputs (`endurance_min=None`)

Opt-in only: if the caller does not pass a sweep, `hover_energy_autonomy_min` and `autonomy_min` are **unchanged** vs the same `build()` without L2; new bundle fields are `None`. Do **not** require `CalculationBundle.model_dump()` byte identity (new keys with `None` are allowed).

---

## 2. Physics (locked)

Evaluate in **voltage space** (same electrical scope). Do not implement as an unclamped `else: C×(1−SOC)/I` after only `SOC >= 1`.

```text
V_oc(SOC) = V_oc_empty + SOC × (V_oc_full − V_oc_empty)   # linear — ASSUMED
V_loaded(SOC) = V_oc(SOC) − I_load × R                      # R >= 0; same electrical scope

V_full_loaded  = V_loaded(1) = V_oc_full  − I_load × R
V_empty_loaded = V_loaded(0) = V_oc_empty − I_load × R

if V_full_loaded < V_cutoff:
    outcome = infeasible
    endurance_min = None
    soc_at_cutoff = (V_cutoff − V_oc_empty + I_load×R) / (V_oc_full − V_oc_empty)  # diagnostic, may be > 1
    stopping_condition = None

elif V_empty_loaded > V_cutoff:
    # Cutoff never reached inside nameplate SOC ∈ [0, 1]. Coulomb budget ends first.
    outcome = sustainable
    soc_at_cutoff = 0.0
    endurance_min = capacity_ah / I_load × 60
    stopping_condition = "nameplate_exhausted"

else:
    # Includes V_full_loaded == V_cutoff → SOC = 1, endurance_min = 0.
    SOC_cutoff = (V_cutoff − V_oc_empty + I_load×R) / (V_oc_full − V_oc_empty)
    outcome = sustainable
    soc_at_cutoff = SOC_cutoff
    endurance_min = capacity_ah × (1 − SOC_cutoff) / I_load × 60
    stopping_condition = "voltage_cutoff"
```

- `capacity_ah` is a **number the caller supplies**. Product meaning is nameplate Ah (not usable Ah at this C-rate). The solver does **not** interpret provenance.
- **Not** ∫ V·I dt. Do not output or label **usable Wh**.
- **Not** P_battery. **Not** I2 (`I = P_motor / V`).
- ★★13: `r_internal_scope` and `voltage_scope` ∈ `{pack, cell}` **required**. If they differ → **refuse**, no `× cells`.
- Formula takes **already-scoped** volts and ohms. Cell→pack conversion, if any, is **outside** this function (caller / assumption record).

---

## 3. API

### 3.1 `tools/electricity.py`

```text
estimate_loaded_endurance(
    *,
    v_oc_full_v, v_oc_empty_v,
    r_internal_ohm, i_load_a, v_cutoff_v, capacity_ah,
    r_internal_scope: "pack" | "cell",
    voltage_scope: "pack" | "cell",
) -> ToolResult
```

`ToolResult` in this repo is **only** `{tool_name, inputs, outputs}` (`schemas/tool_schema.py`). There is no `success` / `error` / `result` field. Put status in `outputs`.

**Refuse** — `outputs.outcome = "refused"`, `endurance_min` absent or `None`, no endurance number to present as a result:

| `outputs.reason` | When |
|---|---|
| `scope_mismatch` | scopes missing, not in `{pack, cell}`, or disagree |
| `invalid_input` | `i_load_a <= 0` or `capacity_ah <= 0` or `v_oc_full_v <= v_oc_empty_v` or `r_internal_ohm < 0` or any input non-finite |

`r_internal_ohm == 0` is **valid** (ideal pack).

Copy all finite inputs (including scopes) into `ToolResult.inputs`.

**Sustainable:** `outcome="sustainable"`, `endurance_min` (round 4 decimals, same as `calculate_autonomy_min`), `soc_at_cutoff`, `stopping_condition` ∈ `{voltage_cutoff, nameplate_exhausted}`.

**Infeasible:** `outcome="infeasible"`, `endurance_min=None`, `soc_at_cutoff` may be `> 1` (diagnostic), `stopping_condition=None`. This is a **successful evaluation**, not a refuse.

**No default Voc 16.4/13.2, no default R, no default I** in this module.

### 3.2 Sweep wrapper (same file)

```text
estimate_loaded_endurance_sweep(points: list[dict[str, Any]]) -> list[ToolResult]
```

Each point is a `dict` whose keys match the keyword arguments of `estimate_loaded_endurance` (plus optional passthrough keys listed in §3.3). **No** new dataclass/TypedDict in this IC. **No built-in grid.** Empty list → empty list.

A refused or infeasible point does **not** abort the rest of the sweep. One `ToolResult` per input point, same order.

### 3.3 `CalculationEngine.build` (opt-in)

Read optional `parameters["battery_endurance_sweep"]`:

- missing / null / `[]` → `battery_endurance_envelope=None`, `battery_endurance_assumption=None`
- JSON string or `list[dict[str, Any]]` → run sweep; set envelope to a list of **plain dicts**, one per point, in order.

**Each envelope row must contain:**

- all numeric/scope inputs used
- `outcome` (`sustainable` | `infeasible` | `refused`)
- `endurance_min` (`float | None`)
- `soc_at_cutoff` (`float | None` — `None` on refuse)
- `stopping_condition` (`voltage_cutoff` | `nameplate_exhausted` | `None`)
- `r_internal_scope`, `voltage_scope`
- `source_type`: always the string `"assumed"` (**write** it; do not read a default off the point dict)

**Optional passthrough** (copy if present on the point; **omit** if absent — do not invent):

- `i_load_label`
- `capacity_source` (e.g. caller may send `catalog_nameplate` or `assumed`)
- `capacity_source_ref`

Do **not** auto-fill I from `motor_hover_current_a` unless that value is already in the caller’s point dict.

`battery_endurance_assumption`: JSON string, `sort_keys=True`, at least:

```json
{
  "model_class": "E-SWEEP",
  "source_type": "assumed",
  "label": "ESTIMATIVE — not validated, not flight time, not manufacturer usable energy",
  "ocv_note": "linear V_oc(SOC) is a mathematical hypothesis, not a SKU characterization",
  "n_points": <int>
}
```

JSON-string persistence matches `hover_energy_resolution`. It is a bundle/CLI convenience, not a second domain model.

### 3.4 Schema

`CalculationBundle` (`schemas/tool_schema.py`):

```text
battery_endurance_envelope: list[dict] | None = None
battery_endurance_assumption: str | None = None
```

No `battery_endurance_min`. No `P_battery`.

---

## 4. Presentation

### 4.1 Orchestrator

Mirror hover-energy: if bundle has a non-None envelope, put a `battery_endurance` object on CLI ctx (envelope + parsed assumption). **Do not** fold into `hover_energy` or `autonomy_min`.

### 4.2 CLI (`adapters/cli/main.py`)

Only if ctx has endurance data. Block **after** “Energía hover (evidencia)”, **never** on the same line.

Example shape (wording may match tone of existing CLI; **required phrases** below):

```text
Autonomía estimada (ESTIMATIVO — no validado, no es tiempo de vuelo):
  R=20 mΩ pack (asumido) · I=68 A (hipótesis) · Vcut=14.0 V pack → 0.43 min
  R=40 mΩ pack (asumido) · I=68 A · Vcut=14.0 V pack → INVIABLE
```

For `stopping_condition=nameplate_exhausted`, the row must still be clearly ESTIMATIVE; do **not** call it flight time or usable Wh. A short “corte no alcanzado (capacidad nominal)” (or equivalent) is allowed.

**Required in the heading or first line:** `ESTIMATIVO` and that it is **not** validated flight time.  
**Forbidden:** `autonomía real`, `usable Wh`, `P_battery`, calling L1 a lower bound.

Refused points: skip or show as invalid input — **not** as `INVIABLE` (infeasible is a model result; refuse is bad input).

### 4.3 DSE / ERF-2 / catalog

No edits to `design_explorer.py`, `electrical_compatibility.py`, `library/baterias/_datos.json`.

---

## 5. Tests + probe

### 5.1 `tests/test_phase27b_loaded_endurance.py`

| Case | Expect |
|---|---|
| Scope mismatch pack R vs cell V | `outcome=refused`, `reason=scope_mismatch`, no endurance_min |
| `r_internal_ohm = -0.02` | `outcome=refused`, `reason=invalid_input` |
| Voc 16.4/13.2, R=0.020 Ω, I=68, Vcut=14, C=1.5, **pack/pack** | sustainable, soc≈0.675, endurance≈0.4301, `stopping_condition=voltage_cutoff` |
| Same, R=0.040 Ω | infeasible, endurance_min is None |
| Optimistic R=0.010, I=50, Vcut=13.2 | sustainable ≈1.51875, `voltage_cutoff` |
| Voc 16.4/13.2, R=0.020, I=68, **Vcut=10.0**, C=1.5, pack/pack | sustainable, soc_at_cutoff=0, endurance≈1.3235 (`1.5/68*60`), `nameplate_exhausted` (must **not** be `> 1.3235`) |
| Knife-edge: construct `v_cutoff_v = v_oc_full_v − I×R` | sustainable, endurance_min=0.0, soc_at_cutoff=1, `voltage_cutoff` |
| `build()` **without** sweep key | envelope None; assumption None; `hover_energy_autonomy_min` and `autonomy_min` **equal** to a control `build()` of the same params (semantic L1; new keys may exist as `None`) |
| `build()` with 2-point sweep | envelope len=2; assumption JSON has `ESTIMATIVE` / `assumed`; each row `source_type=="assumed"` |
| Import grep: `design_explorer.py` does not reference `battery_endurance_` | static or test |

Paper numbers are **regression of the formula**, not product defaults.

### 5.2 `scripts/cli_probe_phase27b_battery_endurance.py`

1. Combo A bind (same pattern as Phase 2.5 probe) → `build()` **no** sweep → L1 ≈1.3237, envelope None.  
2. Same params **plus** caller sweep: (20 mΩ, 68 A, 14 V) and (40 mΩ, 68 A, 14 V), pack, labeled Voc hypothesis → one sustainable, one infeasible.  
3. Rendered CLI (or ctx string) contains `ESTIMATIVO` and `INVIABLE` (or `infeasible`) and does **not** contain `autonomía real`.  
4. No `p_battery` / `P_battery` on bundle dump.

---

## 6. Non-goals

```text
P_battery / ESC η
Silent I_pack = n × I_hover
Catalog R or OCV
Relabel hover_energy_autonomy_min
DSE scoring of envelope
Peukert / thermal / ∫V·I energy
Hardcoded default grid or default Voc in electricity.py
New simulation subsystem / revive energy_model.py
Version bump
New ToolResult schema fields (success/error)
New envelope scalar battery_endurance_min
```

---

## 7. Acceptance

- Suite green including new tests  
- Probe 4/4  
- `git diff` for this IC: `electricity.py`, `tool_schema.py`, `calculation_engine.py`, orchestrator ctx + CLI render, tests, probe — **not** library JSON, **not** DSE  
- L1 Combo A still ≈1.32 min without sweep (semantic; new bundle keys `None`)  

---

## 8. Copy-paste prompt for implementer

```text
Implement:
  .jes/artifacts/implementation_contract_phase27b_parametric_battery_estimate.md

Read v0.2 changelog and §2 voltage-space evaluation. Baseline fc46938 / v0.3.5.
★1–★5 locked. P26 / P27-A validated path frozen.
No P_battery, no catalog R, no L1 change, no DSE.
Opt-in sweep only. ★★13 refuse on scope mismatch.
Refuse R < 0 (invalid_input). R == 0 allowed.
SOC/cutoff: V_full_loaded < Vcut → infeasible; V_empty_loaded > Vcut → nameplate_exhausted (cap at C/I, never super-nameplate time); else voltage_cutoff (incl. endurance 0 at knife edge).
ToolResult is {tool_name, inputs, outputs} only — put outcome in outputs (refused | infeasible | sustainable). Sweep does not abort on one refused point.
source_type always written "assumed" on envelope rows. Optional capacity_source passthrough only if caller sent it.
No default Voc/R/I in electricity.py.
L1 semantic unchanged without sweep (not model_dump byte-identity).
ESTIMATIVE CLI. Tests including R<0, nameplate_exhausted, knife-edge 0 min.
scripts/cli_probe_phase27b_battery_endurance.py.
```
