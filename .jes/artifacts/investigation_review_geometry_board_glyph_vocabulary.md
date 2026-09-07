# Investigation Review — Minimum Board Glyph Vocabulary (Geometry · visualizar B1)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_board_glyph_vocabulary.md](investigation_contract_geometry_board_glyph_vocabulary.md)  
**Report:** [investigation_report_geometry_board_glyph_vocabulary.md](investigation_report_geometry_board_glyph_vocabulary.md)  
**Parents:** Geometry Progression Lock B1 · `representar` @ **2336**

## Verdict

**PASS WITH NOTES**

Governing question answered. Vocabulary correctly **narrowed** to `{box, disk}` with **zero** live cylinder/bar matches. Motor cylinder stitch rejected honestly. Board DTO `width`/`height` = card pixels — collision finding confirmed. Absence → **no glyph** is the right B1 default. Default lean **Buy B1** (projector-computed `geometry`, UI dumb draw) is Buy-ready.

Engineer ★ still required before IC / code. No `src/`/`ui/` this investigation.

---

## Checklist

| Criterion | Result |
|---|---|
| A–H present | **Pass** |
| Dim inventory glyph-ready / partial / blocked | **Pass** |
| Closed vocabulary + family map | **Pass** — `{box, disk}` only |
| Motor special case (no cylinder stitch) | **Pass** |
| Absence policy + default lean | **Pass** — no glyph |
| Honesty / ladder (≠ assembly / fit) | **Pass** |
| Default Buy lean | **Pass** — **B1** |
| No code | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Battery box-ready 3/10 | **Confirmed** |
| ESC box 1/1 | **Confirmed** |
| Motor `diameter_mm` 2/22; no overall height | **Confirmed** |
| Propeller `diameter_in` 17/17 | **Confirmed** |
| Projector DTO `width`/`height` = card px | **Confirmed** — `spatial_board.py` + `types.ts` |
| Frame thickness-only / no L×W | **Confirmed** (prior Structure knowledge + report) |
| FC dims only `pixhawk_4` | **Confirmed** |

---

## Agreement with report core

1. **`{box, disk}` only for B1** — correct narrowing vs contract starter table.  
2. **Motor → `disk` via `diameter_mm`**, not cylinder from bell Ø + stator height — correct.  
3. **No glyph when incomplete** — correct; aligns with Progression Lock honesty.  
4. **Shape from present keys, not family hardcode** — sound for B1.  
5. **`in`→mm for glyph scale only; text fields keep `"5 in"`** — correct.  
6. **New DTO key(s), never reuse card `width`/`height`** — load-bearing finding.

---

## Notes (must land in IC if Engineer ★ B1)

### N1 — 2D `box` face

B1 draws a **2D** outline. For identities with L×W×H, IC must lock which pair sizes the rectangle (default lean: **length × width** as top-down footprint; `height_mm` remains in the geometry payload for tooltip / future, not invented). Do not imply the flat rectangle is a full 3D solid.

### N2 — Locked B1 identity set

| Shape | Who |
|---|---|
| `box` | Battery rows with full L×W×H (3 today) · ESC `hobbywing_xrotor_40a_6s` · FC `pixhawk_4` |
| `disk` | All propellers with `diameter_in` · motors with `diameter_mm` (2 today) |

No frame/arm/plate · no cylinder renderer · no sensors.

### N3 — Projector owns readiness; UI does not parse `fields`

Emit optional additive structure (e.g. `geometry: { shape, … }` with mm-normalized sizes). React draws or skips. Never re-parse `"50 mm"` strings.

### N4 — Progression Lock still holds

Glyph proximity on canvas ≠ fit. Card drag layout ≠ assembly pose.

### N5 — Optional copy affordance (non-blocking)

Motor/prop disk tooltip “diameter shown; height not represented” may land in IC as optional one-liner, not a schema Buy.

---

## Buy recorded — Engineer ★ B1 (2026-09-07)

| Option | Outcome |
|---|---|
| B0 vocabulary-only | Not bought |
| **B1 box+disk glyphs** | **★ Bought** → [IC](implementation_contract_geometry_board_glyphs_b1.md) |
| B2+ pose/assembly/fit | Frozen |

---

## What Engineer decides next

~~1. ★ Buy B1 → Cursor writes IC → Claude implements~~ **Done — IC open**  
Claude implements IC → Cursor review → optional Board smoke.
