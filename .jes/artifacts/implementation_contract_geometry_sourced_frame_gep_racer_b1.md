# Implementation Contract — #4g Sourced frame GEPRC GEP-Racer B1

**Project:** Jarvis  
**Date:** 2026-09-11  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor / Claude — after Engineer ★ on this text  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** READY FOR ★ — purchase bag locked · Option **A** (new SKU) · 5min rebind away from Rooster  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- Plate L×W Rooster **B0** — Rooster still has **no** plate L×W; this Buy is a **different** frame with cited **Dimensions**  
- iFlight XL7 precedent: `body_length_mm` / `body_width_mm` from “Body dimensions” — **representar / root facts**, not alone a plate box glyph  
- Live 5min frame = `armattan_rooster_5in` — **do not overwrite** that row  

**Type:** Catalog seed + 5min frame rebind — cite GEPRC page → `FrameSpec` Class A keys.  
**Not** inventing per-plate L×W for every plate from overall Dimensions without Engineer gate. **Not** Rooster L×W invent. **Not** version bump.

**Follow-on (part L×W / standoff Ø):** Engineer chose **Option A (CAD)** — [implementation_contract_geometry_gep_racer_part_cad_b1.md](implementation_contract_geometry_gep_racer_part_cad_b1.md). This #4g Buy stays **P1 partial** only.

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | New Class A frame SKU from Engineer purchase citation (GEP-Racer) |
| 2 | Identity | **Option A** — new SKU; leave `armattan_rooster_5in` (and TBS/iFlight rows) untouched |
| 3 | SKU | `geprc_gep_racer_5in` (Agent may tweak; report final) |
| 4 | Root mass / class | `mass_g=78` (±2 in note) · `size_class_inch=5` (page Propeller: 5 inches) |
| 5 | Wheelbase | `wheelbase_mm=208` · `configuration: "quad_x"` (racing X; page does not say “deadcat”) |
| 6 | Body footprint | Page **Dimensions: 175mm×173mm** → `body_length_mm=175`, `body_width_mm=173` (same honesty class as iFlight “Body dimensions”; **not** wheelbase; **not** alone a 3D box without height) |
| 7 | Arms | `arm_thickness_mm=5.0` · material T700 carbon → note / `arm_material` if convention allows |
| 8 | Plates (thickness only unless §0.1 G-plate) | Top 2.0 · Aluminum plate 2.0 · Bottom 2.0 — curated `plates[]` with verbatim labels; **no** L×W on `PlateSeed` (schema has no plate L×W today) |
| 9 | Standoffs | Aluminum column M3\*6\*24mm · Includes **4×** → `standoffs: [{height_mm: 24, count: 4}]` |
| 10 | Mount holes | 30.5 / 25.5 / 20 FC · 16×16 motor · 20 VTX · cam space 14 → **source_note only** (no mount schema) |
| 11 | 5min | **Rebind** `frame` → new SKU; refresh projected wheelbase/mass/body_*/plates/standoffs per existing `bind_frame_from_catalog`. Child `frame_plate*` currently hold **declared** Rooster-era L×W placeholders — see §0.1 plate gate |
| 12 | Out | Overwriting Rooster · inventing plate L×W onto PlateSeed · wheelbase→footprint invent · version bump |

**Product sentence:**

```text
Cito el GEP-Racer que compro (175×173 · wheelbase 208); Jarvis crea ese
SKU Class A y el 5min deja el Rooster en catálogo pero fuera del proyecto.
```

### 0.1 Citation bag — locked (re-fetched geprc.com 2026-09-11 · photo callouts Engineer 2026-09-11)

```text
### geprc_gep_racer_5in
source_url: https://geprc.com/product/gep-racer-frame/
manufacturer: GEPRC
model: GEP-RACER Frame / RACER FPV Frame
Dimensions: 175mm×173mm → body_length_mm=175, body_width_mm=173
  PHOTO: blue callouts 175 / 173 / 208 match the table; 208 = diagonal
  motor-to-motor (wheelbase). 175×173 span the OUTER envelope of the
  assembled airframe (tip/outer motor-mount extent), NOT the narrow
  central stack plate — do NOT treat 175×173 as Main/Top/Bottom plate L×W.
Wheelbase: 208mm
Top / Aluminum / Bottom plate: 2.0mm each (thickness only)
Arm thickness: 5.0mm (thickness only — no arm L×W on page or photo)
Aluminum column: M3*6*24mm · Includes 4× → standoff height 24, count 4
Weight: 78g ± 2g (photo scale shows 78)
Propeller: 5 inches → size_class_inch=5
identity_status: verified
```

**Photo vs invent (locked reading):**

| Callout | Meaning |
|---|---|
| **208 mm** (diagonal) | `wheelbase_mm` — motor center to opposite motor center |
| **175 × 173 mm** | Overall outer envelope → root `body_*` only |
| Plate / arm thicknesses | As table — **no** L×W for those parts in this evidence |

**Still missing for per-part Board boxes (not on page/photo):**

| Part | Have | Need for box |
|---|---|---|
| Central Top/Bottom/Alu plate | thickness 2.0 | **L×W** of that plate (caliper / CAD / another drawing) |
| Arm | thickness 5.0 | **length × width** (or length along arm + width) |
| Standoff | height 24 · count 4 | **cross-section** (Ø or L×W) if you want a post box |
| Shark fin / cam mount / VTX mount | visible in photo | omit unless cited mm |

### 0.1 Plate / arm / standoff honesty — **LOCKED** (Engineer 2026-09-11)

Engineer review (GEPRC page + photo + parts listing) affirms:

| Part | Verified | UNKNOWN (do not invent) |
|---|---|---|
| Frame envelope | 175×173 · wb 208 · mass 78 | — |
| Top / Bottom / Alu plate | thickness **2.0** | **L×W** — never copy 175×173 onto plates |
| Arm ×4 | thickness **5.0** · motor hole 16×16 (note) | **L×W** / freeform outline |
| Standoff ×4 | M3 · height **24** · count 4 | **Ø/sección** — do **not** read “M3×6×24” as Ø6 |

**Board path this Buy:** seed catalog partial kit (**P1**). Critical solids already in other #4* Buys (battery/FC/ESC/prop/GPS). Frame children may exist as thickness/height-only until Engineer **Option A** (cited CAD/STEP) or **Option B** (caliper declared L×W).

**Out of this IC:** new `geometry_level` schema · STL-from-Yeggi as SoT · estimating arm boxes · Ø6 invent.

Corroboration URL (parts): https://geprc.com/product/gep-racer-frame-parts/ (strip UTM if pasted).

**Contrast vs live Rooster:**

| Field | `armattan_rooster_5in` (keep) | GEP-Racer (this Buy · 5min) |
|---|---|---|
| wheelbase | 230 | **208** |
| mass | 125 | **78** |
| body L×W | unset | **175 × 173** |
| arm thick | 4 | **5** |
| main plate thick | 4 | bottom/top **2** (different kit) |

### 0.1 Plate L×W gate (Board boxes)

`PlateSeed` has **no** L×W fields. Root `body_*` does **not** auto-fill `frame_plate` children.

| Option | Meaning |
|---|---|
| **P1 (LOCKED default)** | Seed catalog only (`body_*` + thicknesses + standoffs). On 5min rebind: **clear** stale Rooster declared plate L×W. Leave plate/arm L×W UNKNOWN until A/B. |
| **P2** | **Rejected** for 175×173-as-plate — Engineer + photo. |
| **P3** | Catalog seed only, no 5min plate-child mutation — only if Engineer overrides P1. |

---

## 1. You (implementer)

- Wait for ★ (+ P1/P2/P3 if not defaulting P1).  
- Insert new frame row; Rooster untouched.  
- Rebind 5min frame; apply plate-child policy per gate.  
- Tests: get new SKU wheelbase/body/mass/plates/standoffs; Rooster unchanged; bind projects body_* + wheelbase; no invented plate L×W in `plates[]`.  
- Full suite green. Report.  
- **STOP** if asked to put L×W on `PlateSeed` or invent Rooster footprint.

---

## 2. Intent

```text
Engineer cites GEP-Racer (Dimensions + wheelbase)
        ↓
library/frames new Class A SKU (body_175×173 · wb 208)
        ↓
5min frame rebind (+ plate child policy P1/P2/P3)
        ↓
Board: wheelbase/X stations from 208; plate boxes only if declared
```

---

## 3. Tests (minimum)

| ID | Assert |
|---|---|
| T1 | New SKU → wb 208 · body 175×173 · mass 78 · arm 5 · three 2.0mm plates · standoff 24×4 |
| T2 | Bind projects wheelbase + body_* (+ plates/standoffs per existing bind) |
| T3 | `armattan_rooster_5in` unchanged (still no body L×W) |
| T4 | No `length_mm`/`width_mm` invented inside catalog `plates[]` |
| T5 | 5min frame `catalog_ref.sku` = new SKU; plate policy matches P1/P2/P3 |

---

## 4. Files (expected)

| Path | Action |
|---|---|
| `library/frames/_datos.json` | insert new SKU only |
| 5min `state.json` | frame rebind + plate policy |
| `tests/test_geometry_sourced_frame_gep_racer_b1.py` | write |
| docs / state / report | sync after |
| Rooster row · PlateSeed schema L×W · ui · version | **no** |

---

## 5. Smoke (Engineer)

On `autonomía-de-5min`: frame → GEP-Racer · wheelbase **208** · body **175×173** on card · mass ~78 g — not Rooster 230 / 125 g. Plate boxes only if P2 declared.

---

## 6. Out of scope

Rooster L×W invent · mount-pattern schema · motor T3 · version bump · `#4b` user contribution

---

## 7. Handoff

```text
Engineer → ★ this IC (P1 default, or P2/P3)
Cursor/Claude → implement + report
Cursor → review
Engineer → smoke
```
