# Implementation Contract — #4e Sourced prop Gemfan Hurricane MCK 51466-3 V2 B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ on this text  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** LANDING — IMPLEMENTED · review **PASS WITH NOTES** · await Engineer smoke  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- Propeller envelope B0+B1 / cited seeds B2 — bag keys already on `PropellerSpec`  
- Live 5min propellers = `gf_5045x3` — **do not overwrite**

**Type:** Catalog seed + 5min propeller rebind — cite HobbyDrone page → Class A disk + hub bag.  
**Not** inventing pitch from model digits “51466”. **Not** hub cylinder. **Not** motor/ESC/FC. **Not** version bump.

**Baseline:** package **`0.4.1`** · suite **≥2708** · UI **83**

**Output:** `.jes/artifacts/implementation_report_geometry_sourced_prop_gemfan_51466_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | New Class A propeller SKU from Engineer purchase citation |
| 2 | Identity | **Option A** — new SKU; leave `gf_5045x3` (and other Gemfan rows) untouched |
| 3 | SKU | `gemfan_hurricane_mck_51466_3_v2` (Agent may tweak; report final) |
| 4 | Diameter | Page **Prop Diameter: 131.8mm** → store `diameter_in = 131.8 / 25.4` (**≈5.189**) **or** dual-disclose: primary disk from mm via existing `diameter_in` path. Do **not** invent `5.0` from category “5 inch” alone when 131.8 is quoted. Report chosen float. |
| 5 | Pitch | Page **Pitch: 3.6inch** → `pitch_in=3.6` — **not** 4.66 from the model code |
| 6 | Hub bag | `hub_thickness_mm=6.8` (Center Thickness). `shaft_bore_mm=5` (Center Hole M5). **No** `hub_diameter_mm` unless page states outer hub OD (M5 is bore, not hub OD) |
| 7 | Other | `blade_count=3` · `material="PC"` · `mass_g=4.2` · color Midnight Gray → note only |
| 8 | Adaptive motor | “2207-2306 and up” → `source_note` only (no invented `compatible_kv_band` unless Engineer ★ a numeric band) |
| 9 | 5min | Rebind `propellers` → new SKU |
| 10 | Out | Overwriting `gf_5045x3` · pitch-from-SKU invent · hub cylinder · version bump |

**Product sentence:**

```text
Cito las Gemfan Hurricane MCK 51466-3 V2 que compro; Jarvis crea ese SKU
(Ø131.8mm · pitch 3.6 · hub 6.8 · M5) y el 5min deja gf_5045x3.
```

### 0.1 Citation bag — locked (re-fetched HobbyDrone 2026-09-10)

```text
### gemfan_hurricane_mck_51466_3_v2
source_url: https://www.hobbydrone.cz/hurricane-mck-51466-3-v2-pc-durable-midnight-gray-2ccw-2cw-/
manufacturer: Gemfan
model: Hurricane MCK 51466-3 V2 PC Durable (Midnight Gray)
Prop Diameter: 131.8mm → diameter_in = 131.8/25.4
Pitch: 3.6inch → pitch_in=3.6
Weight: 4.2g → mass_g=4.2
Center Thickness: 6.8mm → hub_thickness_mm=6.8
Center Hole Dia: M5 → shaft_bore_mm=5
blade_count: 3 (page “Number of blades: 3” / model -3)
material: PC
identity_status: verified
package: 2CW+2CCW — note only (quantity not a catalog physics field)
```

**Contrast vs live `gf_5045x3`:**

| Field | `gf_5045x3` (keep) | This Buy |
|---|---|---|
| size code | 5×4.5×3 | Hurricane **51466-3 V2** |
| Ø | 5.0 in | **131.8 mm (~5.189 in)** |
| pitch | 4.5 | **3.6** |
| mass / hub thick | 4.5 / 9.5 | **4.2 / 6.8** |

---

## 1. You (implementer)

- Wait for ★.  
- Insert new propeller row; `gf_5045x3` byte-stable.  
- Rebind 5min propellers.  
- Update any mass-census test that lists cited props with mass_g (add new SKU — not a weaken).  
- Tests: diameter/pitch/hub/mass/blades; gf unchanged; projector disk from diameter_in (≈131.8 mm).  
- Full suite green. Report.  
- **STOP** if asked to set pitch_in=4.66 from the model digits or overwrite gf_5045x3.

---

## 2. Intent

```text
Engineer cites Gemfan Hurricane MCK 51466-3 V2
        ↓
library/helices new Class A SKU
        ↓
5min propellers rebind
        ↓
Board disk Ø131.8mm (+ card hub/mass/pitch)
```

---

## 3. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | `get_propeller(new_sku)` → pitch 3.6 · mass 4.2 · blades 3 · hub_thickness 6.8 · shaft_bore 5 · diameter_in≈5.189 |
| T2 | Bind projects bag fields |
| T3 | Projector disk `diameter_mm` ≈ **131.8** |
| T4 | `gf_5045x3` unchanged |
| T5 | Pitch is **3.6**, never 4.66 |

---

## 4. Files (expected)

| Path | Action |
|---|---|
| `library/helices/_datos.json` | insert new SKU only |
| 5min `state.json` | propellers rebind |
| `tests/test_geometry_sourced_prop_gemfan_51466_b1.py` (+ census tweak if needed) | write |
| docs / state / report | sync after |
| `gf_5045x3` · ui · version | **no** |

---

## 5. Smoke (Engineer)

On `autonomía-de-5min`: propellers → Gemfan Hurricane MCK · disk ~**131.8 mm** · pitch **3.6** — not gf_5045x3 Ø127 / 4.5.

---

## 6. Out of scope

Motor thrust gate · ESC SpeedyBee · FC/GPS · Rooster · version bump

---

## 7. Handoff

```text
Engineer → ★ this IC
Cursor/Claude → implement + report
Cursor → review
Engineer → smoke
```
