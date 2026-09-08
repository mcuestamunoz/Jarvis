# Investigation Review — Geometry pose box-anchored origin (existing solids)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_pose_box_anchor.md](investigation_contract_geometry_pose_box_anchor.md)  
**Report:** [investigation_report_geometry_pose_box_anchor.md](investigation_report_geometry_pose_box_anchor.md)  
**Parents:** origin/axes plate/front-arm B0 (path closed, vision not) · CSS 3D `{box, disk}` CLOSED

## Verdict

**PASS WITH NOTES**

This is **not** a rubber-stamp of the previous B0. The report splits the candidate honestly:

- **Origin point — solved.** Geometric center of a declared box is a function of sourced L×W×H. Not plate-center invention.  
- **Axes — still blocked**, for a **new** reason: live-demo L/W/H are **verbatim print order** / battery **unlabeled**, not manufacturer edge assignment.  
- **Numeric pose Buy — B0.** A point with no verified axis cannot carry a translation.

No READY pose IC. Fit stub stays **QUEUED**. Plate/front-arm B0 **unchanged**.

Engineer ★ still required. Locking this finding is **progress on the path**, not idle-the-horizon.

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + solution-path paragraph | **Pass** — B0 with separable point vs axes |
| Relation to plate/arm B0 | **Pass** — not re-litigated |
| Live box/disk census | **Pass** — Cursor re-ran projector |
| A–E answered | **Pass** |
| B1 local prism rejected with seed evidence | **Pass** — C8/C10 |
| Disks excluded as origin | **Pass** |
| No field sketch under B0 | **Pass** |
| Fit QUEUED; no code / no IC | **Pass** |
| Manufacturer re-fetch | **Pass** — quotes from committed seeds |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Live 14 nodes: 3 box, 2 disk, 9 none | **Confirmed** — `project_spatial_nodes_from_path` on `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` |
| FC 44×84×12 · ESC 50×21.6×12 · battery 37×35×75 | **Confirmed** |
| `mountedOn`: FC/ESC→`frame_plate`, battery→`frame`, motors→`frame_arm`, props→`motors` | **Confirmed** |
| Pixhawk `source_note` “Verbatim print order” | **Confirmed** — `aerial.py:555-558` |
| ESC “verbatim print order mapped to length/width/height” | **Confirmed** — `library/esc/_datos.json` `hobbywing_xrotor_40a_6s` |
| Demo battery “unlabeled axes” + verbatim print order | **Confirmed** — `library/baterias/_datos.json` `lipo_4s_1500mah` |
| DTO `types.ts:24` has no forward/up annotation | **Confirmed** |
| Fit stub QUEUED | **Confirmed** |

---

## Agreement with report core

1. **Box center ≠ plate center** — correct; this is the finding Engineer asked investigations to produce.  
2. **Print-order L/W/H ≠ local physical axes** — correct and load-bearing for rejecting B1.  
3. **`height_mm` ≠ gravity up** — agree; battery note is the sharp example.  
4. **Point without axes cannot express translation** — agree; do not ship an inert `origin_key`.  
5. **CSS 3D `length→x, width→y, height→z` stays visor chrome** — agree; this report does not upgrade it.

---

## Notes

### N1 — Catalog already has one *labeled*-axis battery (not the demo)

`lipo_4s_5000mah` (Spektrum) `source_note`: *“Page states labeled Length / Width / Height … mapped directly, not verbatim print order.”* That is reversal **#1** for **that SKU’s part labels**, not airframe heading, and **not** bound on the live demo (`lipo_4s_1500mah`). Do not rebind to Spektrum to fake a pose Buy. Name it so a later cycle does not re-discover that labeled triples exist in the library.

### N2 — Do not close the vision

B0 here means: **no millimetre translation schema this Buy**. The path remains: point (solved) → verified axes (next evidence) → numbers → visor move → `"cabe"`. Same discipline as “investigations find solutions.”

### N3 — Risk Buy is still a named door

Report reversal #3: Engineer may ★ “center + **explicitly arbitrary** print-order axes, labeled as such.” That would be a **conscious** first place-slice, not silent promotion of transcription into physics. This review does **not** recommend it; it must not be forgotten.

---

## Recommended Engineer moves

| Choice | Effect |
|---|---|
| ★ **Lock finding** (recommended) | Record: box-center honest; unlabeled live SKUs cannot supply axes; pose numbers stay deferred; **horizon open** |
| ★ Diagram / labeled-edge search for **one live** box SKU | Class-A-adjacent fetch for **axis meaning**, not new L×W — separate investigation |
| ★ Risk Buy (print-order axes, labeled honest) | Explicit ★ + READY IC later — not the deferred pose stub |
| ★ Spektrum-style labeled SKU as probe | Product/bind choice, not this IC |
| ★ Skip to fit / invent +X / plate center | **Forbidden** |

---

## Phase

Investigation **reviewable**. Engineer ★ **B1 declared box-local frame** (`procede` paso 1). IC: [implementation_contract_geometry_pose_declared_box_frame_b1.md](implementation_contract_geometry_pose_declared_box_frame_b1.md). Package `0.3.8` · suite **2429**.
