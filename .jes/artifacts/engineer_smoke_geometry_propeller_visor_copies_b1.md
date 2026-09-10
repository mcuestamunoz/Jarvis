# Engineer smoke — Propeller visor copies B1 (2026-09-09)

**Project:** `autonomía-de-5min` (Board screenshot, Engineer 2026-09-09)  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_propeller_visor_copies_b1.md) §6 · [review](implementation_review_geometry_propeller_visor_copies_b1.md) PASS WITH NOTES @ suite **2550**

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Card `propellers` | still **one** card; Ø127 | **PASS** — `gf_5045x3`, Ø 127 mm |
| 2 | 3D pane 5min | **4** propeller disks | **PASS** — four yellow disks. Presentation row (pose stripped), **not** an X of 230. Other solids (FC / plates) stay in the same pane |
| 3 | Card `motors` | still one card; **no** motor solid | **PASS** — `emax_rs2205_2300`, `motor_count` 4, no motor Ø / no motor solid |
| 4 | Frame card | still no box | **PASS** — Rooster identity / mass / 5 in; no L×W prism |
| 5 | 10min visor | **3** disks | **PASS** — projector census this review (`solidCopies=3`). Not in this screenshot |

Click-any-copy → one hélices card was not walked on the Board. `expandSolidCopies` `selectId` + U5 cover it.

Motors remaining invisible is the locked ACCEPT, not a bug. Four disks in the pane are **not** millimetre stations and **not** a quadrotor in space.

Do **not** seed `emax_rs2205_2300` Ø. Do **not** treat this smoke as ★ stations / disk-origin.
