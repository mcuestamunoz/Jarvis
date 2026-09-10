# Engineer smoke — Declared battery + Main Plate envelope B1 (2026-09-09)

**Project:** `autonomía-de-5min` (Board screenshot + live `state.json` + projector)  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_declared_battery_plate_envelope_b1.md) §6 · [review](implementation_review_geometry_declared_battery_plate_envelope_b1.md) PASS WITH NOTES @ suite **2583**

Live census after the screenshot (read-only):

| Fact | Value |
|---|---|
| Battery | SKU `lipo_3s_2200mah`; Wh **24.42** / mass **180** / cells **3** unchanged |
| Battery box | **80 × 34 × 22** mm, `source=declared` |
| Main Plate | L×W **100 × 100**; `height_mm` **4**; `thickness_mm` **4** still |
| Frame | `wheelbase_mm` still **230** — **not** copied into plate L/W |
| 3D | battery box + plate box + FC/ESC cluster + 4+4 visor X |

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | `declara la batería 80 x 34 x 22 mm` | box; identity/energy untouched | **PASS** |
| 2 | `declara la placa principal 100 x 100 mm` | L×W 100; alto 4 from thickness; wheelbase 230 untouched | **PASS** — plate ≠ 230 |
| 3 | 3D | new boxes; X disks unchanged | **PASS** |
| 4 | Forbidden tell | plate size = 230 only if typed | **PASS** — plate is 100 |

Optional pose `respecto a frame_plate` not required to ACCEPT. ESC screening overlap vs FC is prior Buy, not this smoke.
