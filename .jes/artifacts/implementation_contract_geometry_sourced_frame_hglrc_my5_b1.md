# Implementation Contract — #4g+ Sourced frame HGLRC MY5 B1

**Project:** Jarvis  
**Date:** 2026-09-13  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** **Cursor** (Engineer “añadelo tú” · catalog-only override)  
**Reviewer:** Cursor self-check + Engineer smoke  

**Status:** IMPLEMENTED (catalog-only) — await Engineer smoke  
**Parents:**
- [engineer_lock_sourced_envelope_to_3d.md](engineer_lock_sourced_envelope_to_3d.md) ★ LOCKED  
- #4g GEP-Racer precedent — [IC](implementation_contract_geometry_sourced_frame_gep_racer_b1.md) · body_* ≠ plate L×W  
- Plate-box B0 hold — [report](implementation_report_geometry_plate_box_b1.md) — **this Buy does not close plate-box**  
- Live frames: leave `geprc_gep_racer_5in` / `armattan_rooster_5in` / TBS / iFlight **byte-stable**  

**Type:** Catalog seed Class A frame from Rotorama product page → optional live rebind (Engineer picks project).  
**Not** copying Dimensions 225×200 onto `frame_plate*`. **Not** inventing arm L×W / standoff H/Ø. **Not** version bump. **Not** plate-box unlock claim.

**Output:** `.jes/artifacts/implementation_report_geometry_sourced_frame_hglrc_my5_b1.md`

**Checkpoint:** package **`0.4.1`** · suite ≥**2763**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | New Class A frame SKU **HGLRC MY5** from citation below |
| 2 | Identity | **Option A** — new SKU; do **not** overwrite GEP / Rooster / other rows |
| 3 | SKU | `hglrc_my5_5in` (Agent may tweak; report final) |
| 4 | Root mass / class | `mass_g=140` · `size_class_inch=5` (page: 5" frame) |
| 5 | Wheelbase | `wheelbase_mm=225` · `configuration: "quad_x"` (freestyle / training X; page never says deadcat) |
| 6 | Body footprint | Page **Dimensions: 225×200 mm** → `body_length_mm=225`, `body_width_mm=200` — **outer envelope only** (same honesty as GEP 175×173 / iFlight body). Note: one axis equals wheelbase callout — still **not** central plate L×W |
| 7 | Arms | `arm_thickness_mm=5.0` — thickness only; no arm L×W on page |
| 8 | Plates | Curated `plates[]` thickness only, labels verbatim from page: Top **2.0** · Middle **3.0** · Bottom **2.0**. **No** L×W on PlateSeed. Order: Top → Middle → Bottom (Key Features). First child key → `frame_plate` under existing bind ordinal rules — disclose in report; Engineer may ★ reorder later if Middle should be Main |
| 9 | Standoffs | Page mentions rear standoffs + SMA/RC holder — **no** height/count/Ø cited → **omit** `standoffs[]` (do not invent 4×H) |
| 10 | Mount holes | 30.5×30.5 stack M3 · VTX 25.5 / 20×20 M2 · motor 16 mm M3 · cam 19–20 mm → **`source_note` only** |
| 11 | Live rebind | ★ picks: `autonomía-de-5min` / `15min` / **none** (catalog-only). If rebind: clear stale plate L×W from prior frame if any (same honesty as #4g — never copy body onto plates) |
| 12 | Out | Plate-box claim · invent plate/arm L×W · invent standoff H · version bump · overwrite other SKUs |

**Product sentence:**

```text
Cito el HGLRC MY5 (wb 225 · body 225×200 · brazos 5 · placas 2/3/2 · 140 g);
Jarvis añade el SKU Class A. 225×200 es envelope, no la caja de la placa main.
```

### 0.1 Citation bag — locked (Engineer paste 2026-09-13 · Rotorama)

```text
### hglrc_my5_5in
source_url: https://www.rotorama.com/product/hglrc-my5
manufacturer: HGLRC
model: MY5
Motor diagonal distance: 225 mm → wheelbase_mm=225
Arm thickness: 5 mm → arm_thickness_mm=5.0
Top plate: 2 mm · Middle plate: 3 mm · Bottom plate: 2 mm
  → plates[] thickness only — NEVER copy Dimensions onto these rows
Stack mounting holes: 30.5×30.5 mm (M3) — source_note only
VTX mounting holes: 25.5×25.5 and 20×20 mm (M2) — source_note only
Motor mounting holes: 16 mm (M3) — source_note only
Camera size: 19–20 mm (Micro) — source_note only
Dimensions: 225×200 mm → body_length_mm=225, body_width_mm=200
  READING LOCK: overall frame envelope (retailer “Dimensions”), NOT the
  narrow central carbon plate that hosts the 30.5 stack. Do NOT treat as
  frame_plate L×W (same lock class as GEP-Racer 175×173).
Weight: 140 g → mass_g=140
size_class_inch: 5 (page: 5" frame / freestyle+training)
identity_status: verified
standoffs: UNKNOWN (mentioned qualitatively; no H/count/Ø) → omit
```

**Rejected without override:**

| Source reading | Why |
|---|---|
| 225×200 as `frame_plate` L×W | Envelope ≠ stack plate; would false-activate assembly root |
| Invent standoff height from “rear standoffs” prose | No mm |
| Estimate plate L×W from 30.5 hole pattern | Hole spacing ≠ plate outline |

**Still missing for Board plate box / plate-box Buy:**

| Part | Have | Need |
|---|---|---|
| Top / Middle / Bottom | thickness | **L×W** (caliper / OEM drawing) |
| Arms | thickness 5 | L×W |
| Standoffs | mention only | H · count · Ø |

---

## 1. You (Claude)

1. Add `library/frames/_datos.json` row per §0.1.  
2. Wire bind/tests mirroring #4g GEP pattern (new SKU present; peers byte-stable).  
3. If ★ live rebind: apply `bind_frame_from_catalog` path; clear stale declared plate L×W that belonged to prior frame identity.  
4. Do **not** write Continuity plate L×W from body_*.  
5. Do **not** bump version / claim plate-box CLOSED.  
6. Report out.

**STOP if** forced to invent plate L×W or standoff mm.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | SKU loads: wb 225 · mass 140 · body 225×200 · arm 5 · three plates 2/3/2 |
| T2 | GEP / Rooster / other frame rows unchanged (byte or field-stable as peers) |
| T3 | Bind projects `body_*` + plate thicknesses; **no** `length_mm`/`width_mm` on plate children from this seed |
| T4 | Full pytest green; package `0.4.1` |

---

## 3. Smoke (Engineer)

1. Catalog / assist shows HGLRC MY5.  
2. If rebound: Board shows updated wheelbase X; plate solids still **no** L×W box / root still off.  
3. Confirm copy nowhere claims plate-box unlocked.

---

## 4. Out of scope

Plate-box §0.1 fill · stack-rule Path F · arm envelopes · standoff invent · version bump

---

## 5. Done when

- [ ] ★ + seed + T1–T4 + report  
- [ ] Engineer smoke ACCEPT  

---

## 6. Handoff

```text
Engineer → ★ this IC (+ optional live rebind target)
Claude   → implement + report
Cursor   → review
Engineer → smoke §3
```
