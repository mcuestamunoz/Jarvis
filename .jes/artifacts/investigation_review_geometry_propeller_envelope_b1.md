# Investigation Review — Propeller cited envelope + Engineer catalog pass

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_propeller_envelope_b1.md](investigation_contract_geometry_propeller_envelope_b1.md)  
**Claude report:** [investigation_report_geometry_propeller_envelope_b1.md](investigation_report_geometry_propeller_envelope_b1.md)  
**Engineer pass:** [engineer_validation_propeller_catalog_2026-09-09.md](engineer_validation_propeller_catalog_2026-09-09.md)

## Verdict

**PASS WITH NOTES**

Two layers, do not collapse:

1. **Live demo SKU** (`gemfan_5045_hbn`) — Claude **B0** is correct. Ø×paso already KNOW. Mass/hub/blades stay **UNKNOWN**. Oscar Liang is not a Gemfan datasheet.
2. **Catalog campaign** (Engineer) — honesty is correct (UNKNOWN ≠ guess; identity before fill; several current `mass_g` are not KNOW). The **40-field schema + L4 STEP as Spatial SoT** is **not** the next Implementation Contract. That is catalog-v2 / visor-CAD, and it collides with locked “STEP never SoT in core.”

Engineer ★ required on **Buy shape** before any IC / `src/`.

---

## Agreement

| Claim | Cursor |
|---|---|
| Do not invent; missing → omit / UNKNOWN | **Agree** — same as motor envelope |
| Do not limit forever to `mass_g` | **Agree** as product direction; B1 bag is still **small** |
| Identity/variant before rewriting grams | **Agree** — APC 8×4.5 MRP vs ST; Gemfan 5030 2 vs 3; `dal_7040` = Cyclone? |
| `gemfan_5045_hbn` extras UNKNOWN | **Agree** — Claude + Engineer |
| `tmotor_22x6_7` do not enrich | **Agree** — identity Buy, not a silent 6.7→6.6 |
| Current T-Motor/APC/DAL/Gemfan masses can be **wrong KNOW** | **Agree** — e.g. `tmotor_15x5` 55 vs cited ~21 |
| Geometry / mounting / operating are different bags | **Agree as labels** — not as one schema dump |
| Board already shows any projected property | **Agree** |

---

## Reject / defer (architecture — do not sneak into B1)

| Proposal | Lock |
|---|---|
| Nested identity/geometry/mounting/operating/environment object in one IC | **Defer** — `PropellerSpec` stays a flat optional-field dataclass like Motor/Battery |
| Duplicate `diameter_mm` as catalog SoT | **Out** — `diameter_in` is required; projector already `× 25.4` for the disk |
| Operating RPM / thrust_limit / temps → calculation_engine or hover W | **Out** — HD-004 / Prop-Energy. May exist later as **declared text** only |
| L2 hub solid / L3 drawing / L4 STEP replacing CSS disk | **Out this Buy.** Parent: STEP visor-only, never core SoT. Later ★ |
| Full refresh of 17 rows in one PR | **Out** — Engineer already: identity first, don’t touch all masses yet |
| ChatGPT-utm retailer pages as primary without IC re-fetch | **IC must re-fetch** manufacturer/listing and quote |

---

## Notes (must land in any IC)

### N1 — Two products

**A.** Honest gap on live HBN (B0).  
**B.** Stop publishing unsourced `mass_g` as if it were a datasheet (B0 catalog hygiene).  
**C.** Cited envelope bag + bind (B1 representar).  
**D.** T-Motor STEP visor (later).  

Do not implement C+D to “fix” A.

### N2 — Unsourced `mass_g` is already a KNOW lie

Bind projects `mass_g` whenever the JSON has it. Cards/BOM can show **7 g / 9 g / 55 g / 190 g** with `source=declared` and **no** `source_url`. Engineer’s pass says several of those numbers do not match current pages. Lean B0: **null** `mass_g` (or drop the key) on rows without a locked identity + cited page — so the card shows absence, not a costume gram. Confirm no calc path treats propeller `mass_g` as hover physics (bind docstring: mass not wired into calc).

### N3 — Minimum B1 bag (if ★ after B0)

Optional, sourced-only, independently omitable — motor-envelope shape:

```text
blade_count: int | None
material: str | None
hub_diameter_mm: float | None
hub_thickness_mm: float | None
mass_tolerance_g: float | None
shaft_bore_mm: float | None
source_note: str | None
```

`mass_g` / `part_number` / `source_url` / `identity_status` already exist. `bind_propeller_from_catalog` grows the same dim loop as motors. 3D **stays disk from `diameter_in`**. No hub extrusion.

POPO / thread / adapter lists / environment / recommended_motor: **later**, per SKU when a page states them — not the first bag.

### N4 — 🟢 list is not an auto-seed

`gf_5045x3` is the strongest (PN + ABS + 4.5 g). `gemfan_6040` / `dal_7040` need Engineer one-liner: **this SKU means that exact listing**. T-Motor 🟢 masses also need primary-page re-fetch in the IC (RobotShop vs shop.tmotor.com). Do not rewrite `gemfan_6040` 7→5.2 until variant is locked.

### N5 — SKU splits are identity, not geometry

`apc_8x4_5_mrp` vs `_mrp_st`; `tmotor_22x6_6` vs archive `22x6_7`. Separate small Buy. Do not hide variants under one key.

### N6 — Claude row count

Claude said 18; file has **17** keys. Non-blocking.

---

## Default lean (for Engineer ★)

```text
B0  Catalog honesty
    — gemfan_5045_hbn identity_status → partially_verified (Oscar Liang ≠ ficha)
    — hq_5045_bn stays partially_verified; do not invent BN variant
    — null unsourced mass_g on rows without locked page
    — name tmotor_22x6_7 as identity debt (no enrich, no silent rename)
    — optional PropellerSpec.source_note (parity with Motor)

B1  Cited envelope bag (N3) on identity-locked SKUs only
    — first seed: gf_5045x3 (+ others only after Engineer locks the listing)
    — representar text; disk unchanged

B2  SKU splits (APC / T-Motor 22×6.6) when Engineer names them

B3  T-Motor 2D/STEP visor-only — later ★, never core SoT
```

**Not the default:** implement Engineer’s full nested schema + L4 CAD this cycle.

---

## Phase

Investigation **REVIEWED**. No IC until Engineer ★ **B0** / **B0+B1** / re-scope. Fit QUEUED. Package `0.3.8` · suite **2480**.
