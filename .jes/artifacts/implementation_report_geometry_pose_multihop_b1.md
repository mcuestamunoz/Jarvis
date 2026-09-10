# Implementation Report — Pose multi-hop composition B1

**IC:** [implementation_contract_geometry_pose_multihop_b1.md](implementation_contract_geometry_pose_multihop_b1.md)  
**Implementer:** Claude Code  
**Note (process):** This cycle’s `ui/` edit was landed in the Cursor session by mistake — role lock is **Claude implements / Cursor reviews**. Code matches the IC and smoke **ACCEPT**; authorship below is corrected. Next Buys (#2–#4): Cursor writes IC only; Claude implements; Cursor reviews.  
**Date:** 2026-09-09  
**Baseline:** package `0.3.8` · suite **2583** (unchanged — `ui/`-only). UI: 47 → **52** (+5: U20–U24; U8 flipped)

---

## Files changed

| File | Change |
|---|---|
| `ui/spatial-board/src/scene3dLayout.ts` | `layoutSolidsFromPose` resolves origin centers via `resolveComposedCenter` (walk `declaredBoxPose` chain; cycle → row-slot center; active `frame_plate` box → world 0). Child placement = composed origin center + Δmm − wrap/2. `offsetMm` still absolute, checked before pose. |
| `ui/spatial-board/src/scene3dLayout.test.ts` | U8 flipped to assert composition; new describe with U20–U24. |

`src/`, `library/`, `workspace/`, `pyproject.toml` — **not** part of this Buy’s delta (version still `0.3.8`).

---

## Behavior changed

- ESC posed vs FC, FC posed vs Main Plate → ESC sits on the **posed** FC center (including FC’s Δz), not on FC’s empty row slot.
- Longer chains and cycles: cycle revisit uses row-slot (or root world 0); solids never vanish.
- Single-hop with unposed origin unchanged (U21).
- Stations / assembly root / N1 tidy unchanged.

---

## Tests added / executed

- **U20** plate root + FC `zMm:8` + ESC `xMm:5` → ESC at composed FC + 5 mm X and +8 mm on CSS Y  
- **U21** single-hop arithmetic byte-compatible with pre-Buy  
- **U22** A↔B cycle: no throw; finite layouts  
- **U23** disk origin → row-slot fallback  
- **U24** `offsetMm` ignores a fake pose and stays at absolute station  

`npm test` → **52 passed**. `npm run typecheck` → clean. `python -m pytest -q` → **2583 passed**.

---

## Non-goals honored

No sensors/kit · no `frame_plate_2` Buy · no sourced dims · no Python pose/envelope writer · no version bump · no composing X stations into pose chains.

---

## Remaining risks

- Live smoke: reload 5min Board — ESC should sit on the FC/plate stack.  
- Screening overlap footers may remain (AABB screening ≠ VERIFIED).  
- Work order steps #2–#4 not started.
