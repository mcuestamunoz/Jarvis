# Implementation Contract — #4f Sourced battery Tattu 2300mAh 4S 75C XT60 B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ on this text  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** LANDING — IMPLEMENTED · review **PASS WITH NOTES** · await Engineer smoke  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- Battery #4 GenS Ace LANDING — **keep row**; Engineer: 3S Deans pack **likely not craft-compatible** → 5min moves to this 4S XT60  
- Existing `lipo_4s_*` rows — **do not overwrite**

**Type:** Catalog seed + 5min battery rebind.  
**Not** deleting/mutating GenS Ace. **Not** inventing XT60 box. **Not** version bump.

**Baseline:** package **`0.4.1`** · suite **≥2713** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_sourced_battery_tattu_2300_4s_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | New Class A 4S battery SKU from Engineer purchase citation |
| 2 | Identity | **Option A** — new SKU; GenS Ace + all `lipo_4s_*` untouched |
| 3 | SKU | `tattu_2300mah_4s_75c_xt60` (Agent may tweak; report final) |
| 4 | Envelope | **105 × 35 × 29 mm** (L×W×H) · tolerances ±5/±2/±2 in `source_note` |
| 5 | Mass | **270 g** (±20 in note) |
| 6 | Electrical | 2300 mAh · 4S · 14.8 V · 75C · `energy_wh = 2300×14.8/1000 = 34.04` · `max_continuous_current_a = 2.3×75 = 172.5` derived_from_c_rating |
| 7 | Connectors | XT60 main · JST-XHR-5P balance → note only (no connector schema) |
| 8 | 5min | **Rebind** battery from `gens_ace_2200mah_3s_35c_gtech` → this SKU (pose/mount preserve; clear stale fit attest if needed). GenS Ace remains in catalog for other projects |
| 9 | Authority | Engineer purchase-ground-truth (craft stack compatibility vs 3S Deans) |
| 10 | Out | Overwriting GenS Ace / CNHL/Spektrum · XT60 invent · version bump |

**Product sentence:**

```text
Cito la Tattu 2300 4S 75C XT60 que sí encaja en el craft; Jarvis crea ese
SKU Class A (105×35×29) y el 5min deja la GenS Ace 3S en catálogo pero
fuera del proyecto.
```

### 0.1 Citation bag — locked (re-fetched RCDrone 2026-09-10; UTM stripped)

```text
### tattu_2300mah_4s_75c_xt60
source_url: https://rcdrone.top/es/products/src-taa23004s75x6-tattu-2300mah-4s-75c-lipo-battery-pack-with-xt60-plug
  (Engineer paste had ?utm_source=chatgpt.com — strip for SoT)
Brand: Tattu
Capacity: 2300mAh
Voltage: 14.8V · 4S / 4S1P
Discharge: 75C
Main plug: XT60 · Balance: JST-XHR-5P
Size (L x W x H): 105 × 35 × 29 mm
tolerances: L ±5 · W ±2 · H ±2 · mass ±20 → source_note
Net weight: 270 g
identity_status: verified
SKU hint on path: SRC-TAA23004S75X6 (optional part_number if schema allows)
availability: page showed Agotado/sold-out on re-fetch — disclose in note; do not invent replacement
```

**Contrast:**

| Field | GenS Ace (catalog keep) | Tattu (this Buy · 5min) |
|---|---|---|
| S / V | 3S / 11.1 | **4S / 14.8** |
| mAh / C | 2200 / 35 | **2300 / 75** |
| plug | Deans / G-tech | **XT60** |
| L×W×H | 74.7×33.5×25.4 | **105×35×29** |
| mass | 143 g | **270 g** |
| Wh | 24.42 | **34.04** |

---

## 1. You (implementer)

- Wait for ★.  
- Insert new battery row (pattern = GenS Ace / CNHL seeds).  
- Rebind 5min → Tattu; refresh `battery_capacity_wh` / `battery_mass_kg` / `battery_cell_count` via existing `set_battery_component`.  
- Leave GenS Ace row byte-stable.  
- Tests: get new SKU dims+electrical; GenS Ace unchanged; projector box; 5min params coherent (34.04 Wh · 0.27 kg · 4 cells).  
- Full suite green. Report.

---

## 2. Intent

```text
Engineer cites Tattu 2300 4S XT60 (craft-compatible)
        ↓
library/baterias new Class A SKU
        ↓
5min rebind away from GenS Ace 3S
        ↓
Board box 105×35×29
```

---

## 3. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | New SKU → 105/35/29 · mass 270 · C 75 · cells 4 · energy ≈34.04 |
| T2 | Bind projects L×W×H + mass |
| T3 | Projector box |
| T4 | `gens_ace_2200mah_3s_35c_gtech` unchanged |
| T5 | Other `lipo_4s_*` unchanged |

---

## 4. Files (expected)

| Path | Action |
|---|---|
| `library/baterias/_datos.json` | insert only |
| 5min `state.json` | battery rebind + params |
| `tests/test_geometry_sourced_battery_tattu_2300_4s_b1.py` | write |
| docs / state / report | sync after |
| GenS Ace delete · ui · version | **no** |

---

## 5. Smoke (Engineer)

On `autonomía-de-5min`: battery → Tattu **105×35×29** · ~270 g · 4S / 34 Wh — not GenS Ace 74.7×33.5×25.4 / 3S.

---

## 6. Out of scope

Motor T3 · prop #4e (separate ★) · Rooster · XT60 box invent · version bump

---

## 7. Handoff

```text
Engineer → ★ this IC
Cursor/Claude → implement + report
Cursor → review
Engineer → smoke
```
