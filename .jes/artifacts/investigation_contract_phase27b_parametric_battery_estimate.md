# Investigation Contract — Phase 2.7-B Parametric / Estimative Battery Model

**Project:** Jarvis  
**Date:** 2026-09-01  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_phase27b_parametric_battery_estimate.md`

**Status:** READY FOR CLAUDE

**Type:** Architecture investigation — can Jarvis expose an **honest estimative** battery model (parameters in → labeled envelope out) **without** claiming validated flight time, **without** inventing `P_battery`, and **without** replacing `hover_energy_autonomy_min`. **Not** an implementation plan.

**Checkpoint base:** commit **`fc46938`** · tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`**

**Relation to Phase 2.7-A (CLOSED):**

```text
P27-A  ★ RATIFICADO INSUFFICIENT DATA
       Question answered: can we compute *validated* loaded-battery autonomy
       from T1/T2 SKU data?  → NO. PHASE27_LOADED_BATTERY_BOUNDARY frozen.
       hover_energy_autonomy_min stays nameplate Wh / P_motor_input.
       Not a physical lower bound of flight time.

P27-B  THIS CONTRACT
       Different question: what *estimative* model may Jarvis run as
       hypothesis / sensitivity, clearly labeled ESTIMATIVE, so we can
       (1) reason before the drone is built, and (2) see which parameters
       are worth measuring later.
```

P27-A does **not** reopen. P27-B must not smuggle “realistic autonomy” through assumed R/OCV.

---

## Engineer intent (locked framing)

```text
modelo estimativo  ≠  modelo validado
```

Three levels (report maps code to each; does not skip Level 1):

| Level | What | Label |
|---|---|---|
| **L1** | `hover_energy_autonomy_min` = 22.2 Wh / (251.6 W × 4) ≈ 1.32 min | **computed** (motor-input, nameplate) |
| **L2** | OCV / R / SOC / `I_load` **as parameters** → V(t), energy, envelope | **ESTIMATIVE** |
| **L3** | Same model vs instrumented discharge | **validated within tested conditions** — out of scope until T1/T2 |

L2 is the investigation target. L3 is the future comparison target, not this slice.

---

## Physics locks (do not contradict)

**`PHASE26_P_BATTERY_BOUNDARY` — still frozen.**

The battery box takes a **load current (or current envelope) as an input hypothesis**. It must **not** output “hover flight time” by treating `4 × 17 A` as pack current, nor by solving `I = P_motor / V` (P27-A ★4: that identity is `P_battery := P_motor_input`).

Correct L2 split:

```text
                    PHASE 2.6 FROZEN
         P_motor_input → ESC loss → P_battery   ⛔

Battery model (this investigation)
         I_load          ← PARAMETER / sweep / labeled proxy
         OCV(SOC)        ← PARAMETER (sourced OR assumed+labeled)
         R_internal      ← PARAMETER (sourced OR assumed+labeled)
         capacity        ← catalog nameplate unless separate assumed
              ↓
         V_loaded = V_oc − I_load × R     (circuit identity under *that* I)
         SOC(t), energy delivered until cutoff
              ↓
         labeled endurance-at-assumed-load
              ≠ hover_energy_autonomy_min
              ≠ P_battery from the propulsion chain
```

Any **energy delivered until cutoff** produced by L2 is a **model-derived** quantity under the stated assumptions. It must **not** be represented as measured or manufacturer-specified usable battery energy.

`I × V_loaded` under an assumed `I_load` is **terminal power at that hypothesis**, not ESC-bridged `P_battery`. The `V_loaded` identity is only legal when `V_oc`, `R`, and cutoff are the **same electrical scope** (pack vs cell) — see ★★13.

**`I_load` is first-class.** Report must score how L2 may use Combo A’s 17 A/motor without silent identity:

| Use | Honest? |
|---|---|
| Sweep `I_load` as independent parameter | Yes — sensitivity |
| Scenario “I_load = n × motor_hover_current_a” **labeled as motor-current hypothesis, not pack draw** | Yes if provenance string says so |
| Default `I_pack = 68 A` with no label | **No** |
| `I_load = P_motor_input / V_loaded` | **No** (I2 / Phase 2.6) |

---

## Engineer locks (★★)

| Lock | Rule |
|---|---|
| **★★1** | Scope = **estimative battery model + sensitivity**. Not ESC, not `P_battery`, not mission regimes, not replacing L1. |
| **★★2** | Phase 2.6 frozen. No η=1, no `P_battery = P_motor_input`, no I2 solver. |
| **★★3** | L1 field **`hover_energy_autonomy_min` unchanged**. Any L2 number is a **sibling** with `confidence` / `source_type` in `{assumed, catalog_nameplate, sourced_t1, sourced_t2}`. |
| **★★4** | **Assumed ≠ sourced.** Generic LiPo OCV or R **may appear only** as `source_type=assumed` (or sweep). They must **never** be written into `library/baterias/_datos.json` as SKU truth, never unlabeled in CLI as the pack’s R. |
| **★★5** | Forbidden: a single `autonomy = 1.437 min` presented as the vehicle answer. Prefer envelope (optimistic / nominal / pessimistic) **or** a table vs R / vs I. |
| **★★6** | Do **not** call L1 or L2 a demonstrated **physical lower bound** of flight time. |
| **★★7** | Deterministic: `ProjectState` + explicit assumption record → result. No LLM in the model. |
| **★★8** | Prefer existing calc/library helpers over a new “Battery Simulation Engine” subsystem. If a new module is truly required, **STOP** — report it as an architecture ask, do not invent it. |
| **★★9** | Combo A primary. Paper exercises **must** label every assumed number. |
| **★★10** | Investigation only — no production code, no JSON curation, no version bump. |
| **★★11** | P27-A M5 / NO-IC for *validated* loaded autonomy remains. P27-B may recommend an IC **only** for a labeled estimative/sensitivity slice. |
| **★★12** | ERF-2 C-rate check stays independent (★★10 of P27-A). |
| **★★13** | **`R_internal` scope MUST be explicit.** Every `R_internal` value used by L2 must declare whether it represents the **complete pack** resistance or an **individual cell** resistance. The model must **not** silently convert, multiply, or divide resistance between cell and pack scope. Likewise, `V_oc` and `V_cutoff` must declare whether they are **pack-level** or **per-cell** quantities. **No mixed cell/pack quantities** in one circuit equation. |

**Forbidden:**

```text
P_battery = P_motor_input
I_load = P_motor / V_loaded
SKU R_internal = 50 mΩ in catalog
CLI: "autonomía real ≈ X min" from assumed R
Relabel hover_energy_autonomy_min
New architectural subsystem without Engineer ★
Peukert n as default physics
Collapse ESC loss into the battery box
Silent cell↔pack R or V conversion; mixed-scope V = V − I·R
L2 energy-until-cutoff labeled as measured or manufacturer usable Wh
```

---

## Question the report must answer

> What battery model can Jarvis implement as a **physically reasonable estimate**, which parameters does it need, what can come from catalog vs assumed vs later bench, what stays uncertain, and which measurements would actually move the envelope (sensitivity) — **before the drone is assembled** — without fraudulently presenting that estimate as a validated prediction?

---

## Gates

### Gate A — L1 vs L2 surfaces today

Confirm L1 path (file:line) still nameplate / motor-input only. List what would be **new** for L2 (assumption record, sibling fields, CLI label). Confirm no `P_battery`.

### Gate B — Parameter set (minimum honest L2)

Score each: required / optional / later.

| Parameter | Catalog today? | Assumed OK if labeled? |
|---|---|---|
| capacity_Ah / energy_wh | yes (nameplate) | as identity, not “usable” |
| OCV(SOC) | no | yes, labeled + **scope pack \| cell (★★13)** |
| R_internal | no | yes, labeled + sweep + **scope pack \| cell (★★13)** |
| I_load | hover current exists; **not** pack I | sweep + optional labeled proxy |
| cutoff V | no | yes, labeled + **scope pack \| cell (★★13)** |
| T | no | optional; default “neglected” explicit |
| initial SOC | no | yes, labeled (not “100% for whole flight” as sole story) |

Recommend a **minimum** assumption record schema (JSON-serializable, like `hover_energy_resolution`). Schema **must** carry `r_internal_scope` and `voltage_scope` ∈ `{pack, cell}` (★★13). If a future IC ever converts cell→pack, it must be an **explicit recorded step** using catalog `cells` / pack configuration — never implicit ×4 in the solver. Gate D paper numbers must be homogeneous (do not pair `R_pack` with `V_cutoff` per cell in one `V − IR` line).

### Gate C — Model class for L2 (score, do not implement)

| ID | Sketch | Risk |
|---|---|---|
| **E-R** | Fixed R, OCV table or V_oc(SOC) polyline, coulomb count at constant `I_load` until cutoff | Simplest; hides T, Peukert |
| **E-SWEEP** | E-R run over a stated R grid and/or I grid → envelope | Matches Engineer intent |
| **E-M3** | C-rate derating table only (P27-A M3) — no V | Still no T1/T2 table; do not fake one |
| **E-NONE** | L2 not implementable without a new subsystem or without breaking locks | Valid |

Recommend **at most one** implementable class, or E-NONE.

### Gate D — Sensitivity: what is worth measuring?

Paper Combo A (labeled hypotheticals allowed). Example grids (investigator may adjust, must label):

- R: e.g. 10 / 20 / 40 / 80 mΩ **pack** (assumed, **not** SKU) — or a separate cell-scope grid, never mixed in one run
- I_load: e.g. 50 / 68 / 90 A (68 A = 4×17 A **hypothesis**)
- cutoff: e.g. 13.2 vs 14.0 V **pack**, or 3.3 vs 3.5 V/cell **only** in a cell-scope run with cell-scope OCV and R

Report: which axis **moves** estimated endurance by more than ~10% vs which is noise. That ranks M3 high-C campaign vs R measurement vs ESC bench **empirically**, not by slogan.

If the investigator refuses numeric hypotheticals, they must still **qualitatively** rank axes with physics reasoning and say why numbers were withheld.

### Gate E — Integration map (map only)

Same discipline as P27-A Gate F: calc vs library; sibling field names; CLI must show assumptions; DSE must **not** silently score L2 as `autonomy_min` unless Engineer later decides. Default lean: DSE keeps L1 `autonomy_min` until ★.

### Gate F — IC / NO IC

- **NO IC** if L2 cannot be labeled honestly or needs a new engine.
- **Bounded IC** only: assumption record + sweep envelope + sibling fields + CLI ESTIMATIVE line. No catalog R. No L1 change. No P_battery.

M3 data campaign remains **parallel**, not a substitute for this investigation.

---

## Mandatory table

| Capability | Today | L2 possible? | Blocker | First slice |
|---|---|---|---|---|
| L1 motor-input autonomy | YES | — | — | none |
| Labeled parametric OCV+R at assumed I | NO | | | P27-B IC? |
| Sensitivity envelope vs R / I | NO | | | P27-B IC? |
| `I_load` as pack current | NO | not without P26 | ESC | none |
| Validated model (L3) | NO | | T1/T2 | data campaign |
| `P_battery` | NO frozen | — | P26 | none |
| DSE uses L2 | NO | must not by default | ★ | none |

---

## Verdict options

| Verdict | When |
|---|---|
| **PASS** | E-R or E-SWEEP implementable under locks; assumption schema defined; Combo A paper labeled; IC outline bounded |
| **PASS WITH NOTES** | Sweep-only / no single YY min; or I_load only as sweep with no default proxy |
| **INSUFFICIENT DATA** | Even assumed L2 would mislead or requires a new subsystem |
| **FAIL** | Invents SKU R; sets P_battery; relabels L1; implements code; mixes cell/pack R or V; presents L2 energy as measured/manufacturer usable Wh |

---

## Engineer ★ (report surfaces)

| ★ | Question |
|---|---|
| **★1** | Allow L2 estimative model in product (labeled), or keep L1-only until L3 data? |
| **★2** | Default I_load scenario: sweep-only vs optional `n × I_hover` hypothesis? |
| **★3** | May DSE read L2? (lean: **no**) |
| **★4** | Sibling name? (e.g. `battery_endurance_at_assumed_load_min` + envelope fields) |
| **★5** | Keep M3 data campaign parallel? (lean: **yes**) |

---

## Copy-paste prompt for Investigator

```text
You are the Investigator for Jarvis.

Read and execute:
  .jes/artifacts/investigation_contract_phase27b_parametric_battery_estimate.md

Baseline: fc46938 / v0.3.5.
P27-A CLOSED INSUFFICIENT DATA — do not reopen validated loaded autonomy.
PHASE26 frozen — no P_battery, no I = P_motor/V.

Deliver:
  .jes/artifacts/investigation_report_phase27b_parametric_battery_estimate.md

Question: what estimative (not validated) battery model can Jarvis run
as labeled hypothesis + sensitivity, without a new subsystem, without
relabeling hover_energy_autonomy_min, without catalog-invented R.

Non-negotiable: ★★1–★★13 · assumed ≠ sourced · envelope over fake precision
· I_load is a parameter · R/V scope pack|cell explicit · no mixed scopes
· L2 energy-until-cutoff is model-derived, not measured/manufacturer usable Wh
· Combo A labeled paper OK · no production code · fill mandatory table
· INSUFFICIENT DATA is valid.
```

---

**End of contract.**
