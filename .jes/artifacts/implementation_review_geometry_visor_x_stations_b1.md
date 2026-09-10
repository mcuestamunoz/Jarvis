# Implementation Review — Visor X stations from cited wheelbase B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_visor_x_stations_b1.md](implementation_contract_geometry_visor_x_stations_b1.md)  
**Report:** [implementation_report_geometry_visor_x_stations_b1.md](implementation_report_geometry_visor_x_stations_b1.md)  
**Buy:** Engineer ★ **situar** / **B1-visor-x**

## Verdict

**PASS WITH NOTES**

Gate and formula hold. N=3 stays a row. Missing wheelbase does not invent 230. Math in Python. Visor remaps declared mm like pose. Writer untouched. Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| `_solid_copy_offsets_mm` only motors/propellers | **Pass** |
| Emit iff `solidCopies==4` + `quad_x` + `W>0` | **Pass** |
| Formula `a=W/(2√2)`; opposite 0–2 = W | **Pass** — P1 `dist≈230` |
| Same points on hélices | **Pass** — P1/P6 |
| Independent geometry (mute motors, props station) | **Pass** — P6 |
| N=3 / no W / no config / hex / no count | **Pass** — P2–P5, P7 |
| No `current_parameters` for N | **Pass** |
| Offsets not `DeclaredBoxPose`; copies strip pose | **Pass** — U9 |
| Axis remap +X→X, +Y→Z, +Z→Y, Z=0 | **Pass** — `layoutSolidsFromPose` offset branch |
| Domain math not recomputed in TS | **Pass** |
| Writer / library / workspace / version | **Pass** |
| P1–P7 | **Pass** — Cursor 7/7 |
| UI U6–U9 (IC U1–U3) + prior copy tests | **Pass** — 43 UI; typecheck clean |
| Full pytest **2562** | **Pass** — Cursor re-ran |
| Live 5min: props 4, **no** offsets (no frame W) | **Pass** |
| Live 10min: props 3, **no** offsets | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| `a = 230/(2√2) ≈ 81.317`; FR/FL/RL/RR | **Confirmed** |
| Mute SKU still no `diameter_mm` | **Confirmed** |
| `_solid_copies` reused, not a second N | **Confirmed** `place()` passes `solid_copies` in |
| `set_component_declared_box_pose` this Buy | **Confirmed** empty |

---

## Notes

### N1 — Row cursor still counts stationed copies

IC: stationed copies get **no row slot**. Placement bypasses the slot; `layoutSolidsRow` still walks every copy, so unposed boxes (FC, battery) can shift because 8 disk footprints still advance the cursor. Millimetre X is correct. Not a reopen. Later tidy: omit `offsetMm` items from the row walk.

### N2 — Live Board still a row until smoke

5min needs `actualiza la frame` **and** `cambiar motor` → RaceSpec. 10min must **stay** a row of 3.

### N3 — UI ids U6–U9

IC U1–U3. Pre-existing expand tests already used U1–U5. Coverage is the lock.

---

## Phase

Implementation **CLOSED**. Engineer smoke **ACCEPT** ([smoke](engineer_smoke_geometry_visor_x_stations_b1.md)): 5min after `actualiza la frame` + RaceSpec rebind → 4+4 stations, opposite ≈230 mm. 10min N=3 stays a row. Package `0.3.8` · suite **2562**.
