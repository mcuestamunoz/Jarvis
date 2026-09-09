# Engineer smoke — Rooster Included plates B2 (2026-09-09)

**Project:** `autonomía-de-10min`  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_rooster_included_plates_b2.md) §6 · [review](implementation_review_geometry_rooster_included_plates_b2.md) PASS WITH NOTES @ suite **2514**

Phrase: IDLE `cambiar frame` → `#1` Armattan Rooster 5". **Not** `actualiza el frame desde catálogo`.

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Re-pick | same SKU `armattan_rooster_5in`; children rebuilt | **PASS** |
| 2 | `estado` BOM `└` | HD Cam plate 1.5 mm **and** Rear VTX plates (Standard and TBS) 2 mm, after the four existing plates | **PASS** |
| 3 | Architecture / kit | 4/4; XT60 + JST-SH unchanged | **PASS** |
| 4 | 3D | no frame box | **PASS** (Board 3D cluster unchanged class) |
| 5 | Sim FAIL | still GAP-SIM-NOT-PASS | **out of Buy** — energy detour (`emax` ×3 + 10 Ah); do not reopen plates |

Board (same session): `frame_plate_6` Rear VTX visible in the crop; minimap **18** cards ⇒ HD Cam (`frame_plate_5`) is on the graph, off-crop. Frame card shows mass / 5" / carbon / 230 mm / quad_x; `max_stack_height_mm` 22 is projected (T4) and may sit below `CARD_MAX_HEIGHT` — resize the frame card if you want the 22 mm line. Not a reopen.

Refresh-only would have missed the two `└` plates. This walk used re-pick. That is ACCEPT.
