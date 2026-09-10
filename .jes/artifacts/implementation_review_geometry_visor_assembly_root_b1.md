# Implementation Review — Visor assembly root (Main Plate at world origin) B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_visor_assembly_root_b1.md](implementation_contract_geometry_visor_assembly_root_b1.md)  
**Report:** [implementation_report_geometry_visor_assembly_root_b1.md](implementation_report_geometry_visor_assembly_root_b1.md)  
**Buy:** Engineer ★ **B1-assembly-root**

## Verdict

**PASS WITH NOTES**

Root detection, world-0 plate, pose-vs-root, and U10–U13 match the Buy. UI **47** green (Cursor re-ran layout suite). Version **0.3.8**. No Python DTO / writer change in this cycle’s intent. Live Board smoke is Engineer’s (§6).

---

## Checklist

| Criterion | Result |
|---|---|
| #1–#3 Root = `frame_plate` + box → world 0 centered | **Pass** — U10 |
| #2 No silent `frame_plate_2` / disk-as-root | **Pass** — U13 |
| #4 Stations still around (0,0); share plate origin | **Pass** — U10 |
| #5 Pose `originKey=frame_plate` from world-0 center | **Pass** — U11 |
| #6 Pose vs non-root still row-slot (no ESC→FC chain) | **Pass** — code path `originIsActiveRoot` only for root id |
| #7 Root + `offsetMm` skipped from row cursor when root active | **Pass** — U10 |
| #8 No-root path byte-identical to pre-Buy | **Note N1** — N1 tidy always on (see below) |
| #9 No Python offset / pose / envelope writer | **Pass** — this Buy’s files are `ui/` + report only |
| #10 No version bump | **Pass** — `0.3.8` |
| U10–U13 | **Pass** — 26/26 in `scene3dLayout.test.ts` |
| `layoutSolidsRow` / `clusterCenterPx` / `expandSolidCopies` API | **Pass** — unchanged exports; filter is inside `layoutSolidsFromPose` |
| Multi-hop / invent L×W / 230-as-box | **Pass** — out of scope, not done |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Root place = `-wrap/2` at (0,0,0) | **Confirmed** — same centering as zero `offsetMm` |
| `originIsActiveRoot` → `originCenterX/Y = 0` | **Confirmed** |
| Non-root origin still `slotX + wrap/2` | **Confirmed** |
| `ASSEMBLY_ROOT_ID === "frame_plate"` only | **Confirmed** |
| Report suite 2583 / UI 47 | **UI confirmed** (Cursor). Full pytest not re-run this review; report claim accepted for `ui/`-only delta |

---

## Notes

### N1 — N1 tidy applies even without an active root (lock #8 tension)

IC **#7** says items with `offsetMm` do not advance the row cursor (unqualified). IC **#8** and table §3.2 **without root** say: stations still advance cursor — byte-identical to pre-Buy. Claude implemented always-on skip of `offsetMm` from the row (and U12 asserts FC at cursor 0 with no plate). Report documents this as deliberate.

**Verdict:** accept for this Buy — better visor hygiene; product path with Main Plate box is correct. Not a reopen. If Engineer wants literal #8, a one-line gate `&& root` on the `offsetMm` filter would restore pre-Buy no-root packing; not required for smoke.

### N2 — Docstring overclaim

Comment claims “No root … exactly today’s row-based path” while N1 always-on changes no-root packing. Harmless; same as N1.

### N3 — ESC vs FC

Still single-level vs FC row slot (§6 ACCEPT). Not a fail.

---

## Engineer smoke (next)

Reload Board / 3D on `autonomía-de-5min`:

1. Main Plate at center; 4+4 X around it  
2. FC / battery stack on plate  
3. X-vs-racimo gap gone or much smaller  
4. ESC vs FC may look slightly off — ACCEPT  

Record [engineer_smoke_geometry_visor_assembly_root_b1.md](engineer_smoke_geometry_visor_assembly_root_b1.md) after walk.
