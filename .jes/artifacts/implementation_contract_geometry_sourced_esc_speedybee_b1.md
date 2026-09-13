# Implementation Contract — #4c Sourced ESC SpeedyBee BLS 60A 4-in-1 B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ on this text  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — purchase bag locked · Option **A** (new SKU)  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- ESC envelope / Hobbywing Class A already seeded — **do not overwrite**  
- Battery #4 LANDING @ **2703** · FC+GPS [IC](implementation_contract_geometry_sourced_fc_gps_b1.md) parallel  

**Type:** Catalog seed + 5min ESC rebind — cite SpeedyBee page → `EscSpec` L×W×H + electrical identity.  
**Not** overwriting `hobbywing_xrotor_40a_6s`. **Not** mount-pattern schema. **Not** FC/GPS. **Not** version bump.

**Baseline:** package **`0.4.1`** · suite **2703** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_sourced_esc_speedybee_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | New Class A ESC SKU from Engineer purchase citation |
| 2 | Identity | **Option A** — insert new row; leave Hobbywing untouched |
| 3 | SKU | `speedybee_bls_60a_30x30_4in1` (Agent may tweak naming; report final) |
| 4 | Topology | `esc_topology: "4in1"` · `channels: 4` · `continuous_current_a: **60**` (per channel from “60A * 4”) · `burst_current_a: 80` |
| 5 | Envelope | L×W×H **45.6 × 44 × 8** mm · mass_g **23.5** |
| 6 | Mount | 30.5×30.5 · 4mm holes → `source_note` only (no new schema) |
| 7 | Authority | Engineer purchase-ground-truth |
| 8 | 5min | Rebind `esc` from Hobbywing → new SKU (pose/mount preserved if bind supports base merge; else document) |
| 9 | Out | Hobbywing rewrite · mount_pattern field · stack-height invent · version bump |

**Product sentence:**

```text
Cito el SpeedyBee BLS 60A 4-in-1 que compro; Jarvis crea ese SKU Class A
(45.6×44×8) y el Board del 5min deja el Hobbywing individual.
```

### 0.1 Citation bag — locked (re-fetched SpeedyBee 2026-09-10)

```text
### speedybee_bls_60a_30x30_4in1
source_url: https://www.speedybee.com/speedybee-bls-60a-30x30-4-in-1-esc/
Product Name: SpeedyBee BLS 60A 30x30 4-in-1 ESC
SKU page: SB-BLS-60A
Firmware: BLHeli_S J-H-40 (note only)
Continuous Current: 60A * 4  → continuous_current_a=60, channels=4
Burst Current: 80A (10 sec) → burst_current_a=80
Power Input: 3-6S LiPo → cells_min=3, cells_max=6
  voltage_min/max: derive consistently with other ESC rows (3S–6S LiPo convention) or omit if loader allows — match Hobbywing style if present
Dimension: 45.6(L) * 44(W) *8mm(H) → 45.6 / 44 / 8
Weight: 23.5g
Mounting: 30.5 x 30.5mm (4mm hole) — note only
Current sensor: Scale=400 Offset=0 — note only
identity_status: verified
```

**Contrast vs live catalog / 5min:**

| Field | `hobbywing_xrotor_40a_6s` (keep) | SpeedyBee (this Buy) |
|---|---|---|
| topology | individual · ch 1 | **4in1 · ch 4** |
| continuous A | 40 | **60** (per ch) |
| L×W×H | 50×21.6×12 | **45.6×44×8** |
| mass | 15 g | **23.5 g** |

**Availability note (disclose in `source_note`, not a STOP unless Engineer says stop):** SpeedyBee page shows **Discontinued** on re-fetch 2026-09-10. Engineer still cites as purchase identity — seed as cited; do not invent a replacement SKU.

---

## 1. You (implementer)

- Wait for ★.  
- Insert new ESC row; Hobbywing byte-stable.  
- Rebind 5min ESC.  
- Tests: get new SKU dims+60A+4ch; Hobbywing unchanged; projector box; electrical fields coherent with EscSpec loader.  
- Full suite green. Report.  
- **STOP** if asked to overwrite Hobbywing or invent mount_pattern schema.

---

## 2. Intent

```text
Engineer cites SpeedyBee BLS 60A 4-in-1
        ↓
library/esc new Class A SKU
        ↓
5min esc rebind
        ↓
Board box 45.6×44×8
```

---

## 3. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | `get_esc(new_sku)` → 45.6/44/8 · mass 23.5 · continuous 60 · channels 4 · topology 4in1 |
| T2 | Bind projects L×W×H (+ mass per existing ESC bind) |
| T3 | Projector box for bound spec |
| T4 | `hobbywing_xrotor_40a_6s` unchanged |
| T5 | Rooster / battery GenS Ace untouched |

---

## 4. Files (expected)

| Path | Action |
|---|---|
| `library/esc/_datos.json` | insert new SKU only |
| 5min `state.json` | ESC rebind |
| `tests/test_geometry_sourced_esc_speedybee_b1.py` | write |
| docs / engineering_state / report | sync after |
| Hobbywing row · ui · version · mount schema | **no** |

---

## 5. Smoke (Engineer)

On `autonomía-de-5min`: ESC card/solid **45.6×44×8** · SpeedyBee identity · not Hobbywing 50×21.6×12. FC/GPS/battery path unchanged by this Buy.

---

## 6. Out of scope

FC+GPS IC · battery · Rooster · `#4b` user contribution · version bump

---

## 7. Handoff

```text
Engineer → ★ this IC
Cursor/Claude → implement + report
Cursor → review
Engineer → smoke
```
