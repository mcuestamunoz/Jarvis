# Engineer Ratification — Phase 2.7 Battery Voltage / Sag / SOC

**Date:** 2026-09-01  
**Authority:** Engineer (delegated close — “proceda como tú veas”)  
**Investigation:** [report INSUFFICIENT DATA](investigation_report_phase27_battery_voltage_sag.md) · [review ACCEPT](investigation_review_phase27_battery_voltage_sag.md)  
**Contract:** [investigation_contract_phase27_battery_voltage_sag.md](investigation_contract_phase27_battery_voltage_sag.md)  
**Baseline:** tag **`v0.3.5`** / **`checkpoint-phase25-hover-energy`** · commit `fc46938`

---

## Ratification status

**LOCKED** — physics verdict **INSUFFICIENT DATA**. **NO Implementation Contract.**  
Boundary frozen: **`PHASE27_LOADED_BATTERY_BOUNDARY`**.

`hover_energy_autonomy_min` remains the honest motor-input figure (Combo A ≈ 1.32 min): catalog nameplate Wh ÷ hover motor input power. **Not** a validated flight-time prediction, and **not** claimed as a physical lower bound of real flight time.

---

## ★ Decisions (locked)

### ★1 — Loaded-battery autonomy today: **NO**

Jarvis cannot honestly compute sag / `V_loaded` / usable-Wh-under-load autonomy. M1–M4 fail data preconditions.

### ★2 — `battery_capacity_wh` semantics: **nameplate `V_nom × Ah`**

Catalog-wide identity, not Combo-A-only. No cutoff, no load derating, no measured vs computed distinction. Status-quo Wh division is **not** “autonomía real”.

### ★3 — Model class: **M5 UNVERIFIABLE**

Only class whose precondition is met. M3 remains the nearest *future* slice, blocked on a sourced C-rate table (see ★9).

### ★4 — `I_load` policy: **I4 UNVERIFIABLE**

**Additional lock:** **I2 with `P_motor_input` in the numerator is forbidden.**  
`I = P_motor / V_loaded` asserts `P_battery := P_motor_input` and reopens `PHASE26_P_BATTERY_BOUNDARY`.

I1 (silent `I_pack = I_motor`) remains forbidden without a labeled, sourced assumption. I3 is a one-sided bound only, not a model.

### ★5 — `hover_energy_autonomy_min`: **unchanged**

Do not rename, replace, or present as flight time.

### ★6 — Sibling field: **do not add now**

Name reserved if a future sourced model exists: `hover_loaded_battery_autonomy_min`. No field in `CalculationBundle` until T1/T2 data + IC.

### ★7 — Partial M3 IC today: **NO**

No numeric derating table. If a table is later sourced, a **new** investigation/IC must still name which current defines C-rate (hover motor current is an I1-class proxy — review Note 2).

### ★8 — ERF-2 hover current: **NO**

`_battery_discharge` stays a bench-max C-rate **limit check**, independent of the energy chain.

### ★9 — Next after INSUFFICIENT DATA: **battery high-C data campaign (primary)**

**Primary (this close):** acquire T1/T2 C-rate vs usable-capacity data for `lipo_4s_1500mah` (Combo A hover ≈ 45 C). Contract: [data_acquisition_contract_phase27_m3_crate_derating.md](data_acquisition_contract_phase27_m3_crate_derating.md).

**Parallel, not blocking:** ESC-isolated bench for `hobbywing_xrotor_40a_6s` (reopens P26-D/P26-E). Smaller expected autonomy delta (~4% paper η) vs unknown high-C derating.

**Not next:** H5 ESC catalog expansion, G24-B, Catalog Foundation bulk, mission regimes, Block Closure (product queue — parked).

### ★10 — UNVERIFIABLE as success: **YES**

Phase 2.7 investigation is closed. Knowing Jarvis **cannot** claim loaded-battery autonomy is the delivered limitation.

---

## Frozen boundary (`PHASE27_LOADED_BATTERY_BOUNDARY`)

```text
catalog energy_wh  →  battery_capacity_wh     ✅ nameplate only (★★3)
battery_capacity_wh → hover_energy_autonomy_min  ✅ motor-input Wh/W (Phase 2.5)
                  → V_oc(SOC)                 ⛔ UNVERIFIABLE
                  → R_internal                ⛔ UNVERIFIABLE
                  → I_load without P_battery  ⛔ I4 (I2 forbidden)
                  → V_loaded / usable Wh      ⛔ NO IMPLEMENTAR until T1/T2
                  → sibling loaded autonomy   ⛔ NO IMPLEMENTAR until T1/T2 + IC
```

**Forbidden without new investigation + sourced T1/T2:**

```text
Invented OCV / R / Peukert
P_battery = P_motor_input                         (Phase 2.6)
I = P_motor_input / V_loaded                      (I2)
autonomy relabeled "real" from nameplate Wh
Collapse battery sag into ESC loss
```

---

## Explicit non-actions

- No `implementation_contract_phase27_*.md`
- No `src/` / catalog JSON edits for sag, OCV, R, or derating
- No version bump
- No commit unless Engineer asks separately

---

## Sequencing (locked)

```text
P25  Hover motor energy           ✅ CLOSED @ v0.3.5
P26  ESC / P_battery              ⚠️ CLOSED UNVERIFIABLE · PHASE26 frozen
P27  Battery sag / SOC / R        ⚠️ CLOSED UNVERIFIABLE · PHASE27 frozen  ← this ★
     Data: high-C derating (M3)   ← PRIMARY, external
     Data: ESC-isolated bench     ← PARALLEL, external
Future: IC only after T1/T2
Future: compose P26 + P27
Future: mission regimes
```
