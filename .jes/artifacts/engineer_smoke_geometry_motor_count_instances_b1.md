# Engineer smoke — Motor visor copies B1 (2026-09-09)

**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_motor_count_instances_b1.md) · [review](implementation_review_geometry_motor_count_instances_b1.md) PASS WITH NOTES @ suite **2473**

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Card `motors` | one node; `motor_count` **3**; SKU SunnySky | **PASS** |
| 2 | 3D pane | **no** motor solid (`geometry` / `solidCopies` absent) | **PASS** |
| 3 | Prop disk | still **one** (not tripled) | **PASS** |
| 4 | Frame card | `wheelbase_mm` **230 mm** unused by this layout | **PASS** |

Empty 3D motors is the locked ACCEPT, not a bug. Visible copies need a later envelope ★.

Projector read-only via `project_spatial_nodes_from_path` after Claude’s report. Demo `state.json` not mutated this Buy.
