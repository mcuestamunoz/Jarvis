# Engineer smoke — Pose multi-hop composition B1 (2026-09-09)

**Project:** `autonomía-de-5min` (Board + 3D screenshot)  
**Status:** **ACCEPT**  
**Authority:** Engineer screenshot after multi-hop PASS (reload Board)  
**Parents:** [IC](implementation_contract_geometry_pose_multihop_b1.md) §6 · [review](implementation_review_geometry_pose_multihop_b1.md) **PASS**

| Step | Expected | Result |
|---|---|---|
| 1 | ESC on the FC stack on the plate (not floating on an empty FC row slot) | **PASS** — central racimo: FC + ESC + battery share the plate origin with the X |
| 2 | Motors/props X unchanged around plate | **PASS** — four green disks in X |
| 3 | Screening overlap footers OK | **PASS** — ESC `5/0/0` vs FC still shows AABB screening (not VERIFIED); expected |

Live card facts (screenshot): ESC pose `Δx:5` vs `flight_controller`; battery `Δz:13` vs plate; screening footers on FC/ESC/battery — honest, not a reopen.

**Not this smoke:** sensors/kit boxes · `frame_plate_2` L×W · sourced dims · invent mm.
