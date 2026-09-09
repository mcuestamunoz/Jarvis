# Implementation Contract — Propeller cited seeds B2 (`dal_7040` Cyclone + `apc_10x6_ep`)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED — REVIEWED PASS WITH NOTES @ **2497** — Engineer smoke  
**Parents:**
- Engineer ★ `procede` after B0+B1 smoke ACCEPT — next helix listings (not plate L×W)
- [engineer_validation_propeller_catalog_2026-09-09.md](engineer_validation_propeller_catalog_2026-09-09.md) §5 — `dal_7040` **LOCKED**; `apc_10x6_ep` candidate
- Propeller B0+B1 **CLOSED** @ **2489** — bag + bind already exist
- Fit / plate L×W / `"cabe"` / STEP — **out**

**Type:** Catalog **seed only** (schema/bind already ship). Representar text. Disk still from `diameter_in`.  
**Not** T-Motor 🟢. **Not** 8×4.5MR. **Not** overwrite `apc_10x4_5`.

**Baseline:** package **`0.3.8`** · suite **2489**

**Output:** `.jes/artifacts/implementation_report_geometry_propeller_cited_seeds_b2.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B2** — two cited helix rows |
| 2 | `dal_7040` | **=** DALProp Cyclone 7040 · GetFPV |
| 3 | `apc_10x6_ep` | **New SKU** · GetFPV 10×6EP CW gray · **not** `apc_10x4_5` |
| 4 | 3D | Disk scale only (7″ ≈ 177.8 mm, 10″ = 254 mm). No hub solid |
| 5 | Schema | **No** new PropellerSpec keys. POPO / rotation → `source_note` |
| 6 | Version | **No** bump |

**Product sentence:**

```text
Cyclone 7040 y APC 10×6EP citan buje y gramos en card.
El disco 3D crece con Ø. No es la 10×4.5.
```

---

## 1. You (Claude)

- Re-fetch **both** URLs live. If a page contradicts the expected bag, **STOP**.
- Do **not** write Cyclone numbers onto any other DAL. Do **not** merge EP into `apc_10x4_5`.
- Do **not** seed 6040 / HBN / HQ / T-Motor / `apc_8x4_5`.
- Do **not** add schema keys, STEP, cylinder, plate L×W, `"cabe"`, version bump.
- Update B0+B1 T9 (mass census) to the new cited set — required, not a weaken.
- `ui/` empty. Full pytest green. Report when done.

---

## 2. Intent

```text
library/helices/_datos.json
  dal_7040      ← Cyclone bag (B0 already dropped fake 9 g)
  apc_10x6_ep   ← new row
        ↓
bind_propeller_from_catalog (unchanged loop)
        ↓
card text; disk from diameter_in
```

---

## 3. Locked behavior

### 3.1 Re-fetch

| SKU | Primary URL |
|---|---|
| `dal_7040` | `https://www.getfpv.com/dalprop-cyclone-7040-7-2-blade-propeller.html` |
| `apc_10x6_ep` | `https://www.getfpv.com/propellers/x-class-propellers/apc-10x6ep-2-blade-propeller-cw-gray.html` |

### 3.2 `dal_7040` (existing key)

Keep `diameter_in` 7, `pitch_in` 4, `compatible_kv_band`. Seed **if the page states them**:

```text
manufacturer: DALProp   # or the page’s brand string
model: Cyclone 7040     # quote
identity_status: verified
source_url: (the GetFPV URL above)
mass_g: 5.7
blade_count: 2
material: Pure PC       # or verbatim
hub_diameter_mm: 5
hub_thickness_mm: 7
```

`source_note`: quote Ø×paso, palas, PC, hub 5/7, 5.7 g; **POPO yes**; CW/CCW pack. No `shaft_bore_mm` unless the page names a bore distinct from hub Ø.

### 3.3 `apc_10x6_ep` (**new** key)

Do **not** edit `apc_10x4_5`.

```text
diameter_in: 10
pitch_in: 6
manufacturer: APC
model: 10x6EP            # quote (electric pusher)
identity_status: verified
source_url: (GetFPV 10x6EP URL)
blade_count: 2
material: Nylon Long Fiber Composite   # or verbatim
mass_g: 20.1             # Specifications Weight 20.1 g; if the page only says 20, seed 20 and quote; if 20 vs 20.1 conflict without a clear primary, STOP
hub_diameter_mm: 20.3
hub_thickness_mm: 9.9
shaft_bore_mm: 6.35      # page Hub ID / Shaft Diameter — distinct from hub Ø
```

`source_note`: quote bag; this listing is **CW**; **POPO no**; not the catalog’s `apc_10x4_5`.

Optional `tags`: `["apc", "10inch", "ep", "2-blade"]` — not a seed source for dims.

### 3.4 Bind / 3D

No `catalog_bind.py` change unless a field fails to project (it should not). `_geometry_from_spec` **untouched**.

Regression: `diameter_in=10` → disk `diameter_mm == 254`; `diameter_in=7` → `177.8`.

### 3.5 Tests to update

`tests/test_geometry_propeller_envelope_b0_b1.py` **T9**: `mass_g is not None` names **exactly** `{gf_5045x3, dal_7040, apc_10x6_ep}` (order free).

---

## 4. Tests (new file)

`tests/test_geometry_propeller_cited_seeds_b2.py`:

| ID | Behavior |
|---|---|
| T1 | `get_propeller("dal_7040")`: mass 5.7, blades 2, hub 5 / 7, `source_url` GetFPV Cyclone, `source_note` non-empty |
| T2 | bind `dal_7040` projects those; no `source_note` property |
| T3 | `get_propeller("apc_10x6_ep")`: 10×6, mass ~20.1 or 20 as seeded, hub Ø 20.3, H 9.9, `shaft_bore_mm` 6.35, blades 2 |
| T4 | bind `apc_10x6_ep` projects bag; `apc_10x4_5` still pitch 4.5, **no** mass |
| T5 | `project_spatial_nodes` synthetic 10″ + hub → disk **254**; hub text |
| T6 | `project_spatial_nodes` synthetic 7″ → disk **177.8** |
| T7 | `gf_5045x3` bag **unchanged** (mass 4.5, hub 5 / 9.5) |
| T8 | `list_propellers()` includes `apc_10x6_ep`; still 18 rows (17+1) |

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `library/helices/_datos.json` | `dal_7040` bag; new `apc_10x6_ep` |
| `tests/test_geometry_propeller_cited_seeds_b2.py` | T1–T8 |
| `tests/test_geometry_propeller_envelope_b0_b1.py` | T9 census |
| `src/` bind/library | **empty** unless loader bug |
| `ui/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_propeller_cited_seeds_b2.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live demo may stay HBN (5″). Optional: bind `dal_7040` → Ø ~178 mm disk + Cyclone card fields; bind `apc_10x6_ep` → Ø 254 mm + EP card. `apc_10x4_5` unbound/unchanged.

Record `engineer_smoke_geometry_propeller_cited_seeds_b2.md`.

---

## 7. Done when

- [ ] T1–T8 + updated T9 green; full pytest green
- [ ] `apc_10x4_5` not given 10×6 / 20 g
- [ ] No schema / 3D / plate / version bump
- [ ] Report written

---

## Explicitly not this IC

Plate L×W · T-Motor masses · `apc_8x4_5` MR · `tmotor_22x6_6` · hub extrusion · STEP · `"cabe"`
