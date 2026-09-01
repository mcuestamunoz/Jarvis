# Investigation Review — Phase 2.7 Battery Voltage / Sag / SOC Model

**Date:** 2026-09-01  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_phase27_battery_voltage_sag.md`](investigation_contract_phase27_battery_voltage_sag.md)  
**Report:** [`.jes/artifacts/investigation_report_phase27_battery_voltage_sag.md`](investigation_report_phase27_battery_voltage_sag.md)  
**Base:** tag `v0.3.5` / `checkpoint-phase25-hover-energy` · commit `fc46938`

## Verdict

**INSUFFICIENT DATA** (contract §7 — valid success · **NO IC**)

Investigation quality **ACCEPT**. Gates A–H answered. Mandatory §3 table fully populated. ★★1–★★12 respected. No FAIL criterion triggered (no invented OCV/R, no `P_battery`, no relabel of `hover_energy_autonomy_min`, ★★3 audit present, no production code).

**Ready for Engineer ★** on questions ★1–★10. Do **not** draft an Implementation Contract unless ★ reverses the M5 / I4 / NO IC recommendation.

---

## Contract checklist (§4 / §7)

| Criterion | Result |
|---|---|
| Baseline @ `fc46938` | **Pass** — `git diff --stat fc46938 HEAD -- src/ library/ tests/ scripts/` empty (HEAD is 3 JES-metadata commits ahead) |
| Gates A–H answered | **Pass** |
| Mandatory §3 table — no empty cells | **Pass** |
| ★★3 `battery_capacity_wh` end-to-end audit | **Pass** — nameplate `V_nom × Ah` |
| ★★7 `I_load` scored I1–I4 | **Pass** — I4 recommended; I2 correctly flagged as hidden identity |
| ★★2 / ★★6 Phase 2.6 + hover field intact | **Pass** |
| Combo A numeric trace | **Pass** — 22.2 Wh / 251.559 W × 4 → **1.3237 min** re-derived independently |
| M1–M5 scored; INSUFFICIENT DATA allowed | **Pass** — M5 |
| No production code / no JSON curation / no version bump | **Pass** |
| Does not reopen Phase 2.5 / 2.6 | **Pass** |

---

## Independent verification (spot-check)

| Claim | Cursor check |
|---|---|
| `calculate_autonomy_min` = `(Wh / P) × 60` | **Confirmed** — `tools/electricity.py:25-38` |
| Bind projects `energy_wh` as-is | **Confirmed** — `catalog_bind.py:100-102` (`spec.energy_wh` → `battery_capacity_wh`); `component_writers.py:170-171` direct assign |
| Combo A nameplate `14.8 V × 1.5 Ah = 22.2 Wh` | **Confirmed** — float identity (`22.200000000000003` vs `22.2`) |
| Combo A autonomy arithmetic | **Confirmed** — `(22.2 / (251.559 × 4)) × 60` rounds to **1.3237** |
| Hover pack-equivalent C-rate | **Confirmed** — `17.0107 × 4 = 68.0428 A` → **45.36 C** vs 150 A limit |
| No `P_battery` field | **Confirmed** — grep `src/jarvis` + `schemas/` empty |
| `BatterySpec` has no R/OCV fields | **Confirmed** — `library.py:93-121`; `operating_points` defaults empty; **zero** `operating_points` keys in `library/baterias/_datos.json` |
| `_battery_from_raw` does not transform energy | **Confirmed** — `library.py:349-392` copies `energy_wh` as `float` |
| ERF-2 uses bench `motor_op_current_a` | **Confirmed** — `electrical_compatibility.py:129-140, 321, 278-288` |
| Design-doc `internal_resistance` wishlist | **Confirmed** — `PHYSICAL_PROPULSION_ENGINE_PHASE2.md:153-165` |
| Catalog `source_url` (Baltic Drones) | **Re-fetched** — 1500 mAh / 14.8 V / 100C / 183 g / XT60 only. **Zero** IR, OCV, or discharge-curve numbers. Gate D **T4** stands. |

**Catalog-wide strengthening (not in report, non-blocking):** every SKU in `library/baterias/_datos.json` has `energy_wh = nominal_voltage × capacity_Ah` exactly. Nameplate semantics are catalog-wide, not Combo-A-only.

---

## Review highlights

**I2 finding is the load-bearing architectural result.** Solving `I_load = P_motor_input / V_loaded` makes `I × V_loaded = P_motor_input` by construction — i.e. `P_battery := P_motor_input` inside the circuit, which is the frozen Phase 2.6 identity. The contract listed I2 as a candidate “demand” solve; the report correctly **rejects it on inspection**, not merely as a data gap. Future contracts must not revive I2 with `P_motor_input` in the numerator.

**Independence principle held.** Phase 2.7 documents what the battery layer cannot honestly claim **while pack draw remains unknown**, without filling the ESC hole. Composition is deferred to a later arc, as the contract required.

**M3 is the nearest future slice, still data-blocked.** Hover at ~45 C is outside the “derating is a rounding error” regime, so a sourced C-rate table would matter. Gate D found none. See Note 2 for a qualification on I_load independence.

---

## Notes (non-blocking)

### Note 1 — Gate C.2 per-SKU table omitted

Contract Gate C asked which rows have `max_continuous_current_a`, `c_rating`, `operating_points`, `source_url`. The report deep-audits `lipo_4s_1500mah` only. Cursor fill (does not change verdict):

| SKU | `energy_wh` = V×Ah | `max_continuous_current_a` | `c_rating` | `source_url` | `operating_points` |
|---|---|---|---|---|---|
| `lipo_2s_850mah` | yes | **absent** | 75 | no | empty |
| `lipo_3s_1300mah` | yes | **absent** | 100 | no | empty |
| `lipo_3s_2200mah` | yes | **absent** | 50 | no | empty |
| `lipo_4s_1500mah` | yes | 150 (derived) | 100 | yes | empty |
| `lipo_4s_5000mah` | yes | 500 (derived) | 100 | yes | empty |
| `lipo_4s_10000mah` | yes | 100 | 10 | no | empty |
| `lipo_6s_6000mah` | yes | 600 (derived) | 100 | yes | empty |
| `lipo_6s_10000mah` | yes | 100 | 10 | no | empty |
| `lipo_6s_22000mah` | yes | 220 | 10 | no | empty |
| `lipo_12s_16000mah` | yes | 160 | 10 | no | empty |

Legacy rows without `max_continuous_current_a` already map to ERF-2 `"unverifiable"` (`electrical_compatibility.py:286-287`). No energy-model equivalent exists — consistent with M5.

### Note 2 — M3 is not fully independent of ★★7

The report states M3 “does NOT need `I_load` at all” because it can reuse hover or bench current. Pack C-rate is `I_pack / capacity`. If `I_pack` is unknown, the C-rate argument is a **proxy**:

- hover `68 A` → I1-class assumption (motor current as pack current)
- bench `160 A` → different regime (ERF-2), conservative vs hover, still not pack draw

M3 remains **rejected on Gate D** (no numeric derating table). If a table is ever sourced, the IC must still name which current defines C-rate — it does not automatically escape ★★7.

### Note 3 — Combo A′ not re-run

Gate G lists Combo A′; ★★9 marks it optional. Report inherits Phase 2.6’s live proof that ESC bind does not change hover numbers. Acceptable. Battery model does not consume ESC η.

### Note 4 — `BatterySpec` field list slightly incomplete

Report cites `library.py:93-118` and says `source_note` is JSON-only. The dataclass also has `pack_configuration`, `max_continuous_current_source`, and **`source_note` (line 121)**. None are R/OCV. No schema gap missed.

### Note 5 — Generic hobby OCV charts not enumerated as T3-reject

Public 4.20–3.0 V/cell LiPo charts exist. Contract ★★4 already forbids T3 heuristics for implementation. Report’s T4/T3-unusable outcome is correct; an explicit “ubiquitous hobby chart = T3, rejected” row would have been cleaner, not outcome-changing.

### Note 6 — `_battery_from_raw` cited via schema, not the loader

Contract Gate C named `_battery_from_raw`. Cursor confirmed `library.py:349-392` copies `energy_wh` with no cutoff/load transform — same ★★3 conclusion.

---

## Engineer ★ — Cursor lean (for ratification, not decided)

| ★ | Lean | Rationale |
|---|---|---|
| **★1** | **NO** — cannot honestly compute loaded-battery autonomy today | M1–M4 all fail preconditions |
| **★2** | **Ratify nameplate** `battery_capacity_wh = V_nom × Ah` | Catalog-wide, not Combo-A-only |
| **★3** | **Ratify M5** | Only class whose precondition is met |
| **★4** | **Ratify I4**; **lock: I2 with `P_motor_input` is forbidden** | Hidden `P_battery = P_motor_input` |
| **★5** | **Keep `hover_energy_autonomy_min` unchanged** | Already ★★6 |
| **★6** | **Do not add a sibling field now**; reserve `hover_loaded_battery_autonomy_min` | No model to name |
| **★7** | **No partial M3 IC today** | No table; Note 2 if ever sourced |
| **★8** | **Do not retarget ERF-2 to hover current** | Separate margin check (★★10) |
| **★9** | **Engineer call** among: (a) accept interim motor-input lower bound, (b) battery data campaign targeting an M3 derating table, (c) parallel ESC bench (P26-D/E). None is forced by this investigation. | Two independent data paths remain open |
| **★10** | **Accept UNVERIFIABLE as success** | Already ★★4/★★8 |

---

## Recommended next step (post-★)

```text
Engineer ★ (★1–★10)
      ↓
IF ★ confirms INSUFFICIENT DATA → freeze PHASE27_LOADED_BATTERY_BOUNDARY
                                 (NO IC; hover_energy_autonomy_min remains interim)
IF ★ wants a bounded slice anyway → only then draft IC (not recommended by review)
      ↓
Parallel, not blocking:
  - ESC bench campaign (reopens P26-D/P26-E)
  - Battery electrical data campaign (OCV/R and/or C-rate derating table)
      ↓
Future: compose P26 + P27 at pack terminal — only after both layers have T1/T2 data
```

**Explicit non-actions until ★:** no `implementation_contract_phase27_*.md`, no catalog JSON edit, no sibling autonomy field, no version bump, no commit unless Engineer asks.

---

## FAIL criteria (none triggered)

| Forbidden | Status |
|---|---|
| Invented OCV / R / Peukert | **Not present** |
| `P_battery` invented or `η = 1` identity | **Rejected** (I1/I2) |
| Relabel `hover_energy_autonomy_min` as “real autonomy” | **Not present** |
| Skip ★★3 audit | **Present and verified** |
| Recommend sag model that assumes `P_battery` | **Not present** |
| Production code | **Not present** |
