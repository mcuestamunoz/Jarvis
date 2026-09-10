# Engineer smoke — ESC visor rebind B1 (2026-09-09)

**Project:** `autonomía-de-5min` (Board screenshot + live `state.json` + projector)  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_esc_visor_rebind_b1.md) §6 · [review](implementation_review_geometry_esc_visor_rebind_b1.md) PASS WITH NOTES @ suite **2573**

Live census after the screenshot (read-only):

| Fact | Value |
|---|---|
| `catalog_ref` | `esc` / `hobbywing_xrotor_40a_6s` |
| Envelope | box **50.0 × 21.6 × 12.0** mm; `mass_g` **15** |
| Pose | origin `flight_controller`, Δ **5 / 0 / 0** mm (pre-bind pose **survived**) |
| `mounted_on` | `frame_plate` (guide, unchanged) |
| Screening | `Los sobres se solapan… screening, no verificado.` — expected AABB vs FC 44×84×12 at Δx=5 |

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Card `esc` | Hobbywing SKU; L×W×H 50 / 21.6 / 12; pose vs FC still there | **PASS** — screenshot + projector fields |
| 2 | 3D | ESC **box** at declared offset vs FC box | **PASS** — yellow/blue cluster is FC + posed ESC (not a missing solid) |
| 3 | `"cabe"` / sobres | May screen; overlap ≠ VERIFIED | **PASS** — card footer screening copy |
| 4 | Visor X | Unchanged 4+4 disks | **PASS** — green disks still in X (this Buy did not touch stations) |

**Not a fail this Buy:** the visual gap between the X of disks and the FC/ESC cluster. Product **B** (visor stations around wheelbase origin) and product **A** (boxes posed to FC, FC itself unposed in the remainder row) are still two layouts. Unifying them is **3c** (frame/plate origin) or a later origin-unification ★ — not ESC rebind.

Battery / frame / plates / kit still have **no** solid.
