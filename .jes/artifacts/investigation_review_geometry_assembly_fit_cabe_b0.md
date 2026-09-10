# Investigation Review — `"cabe"` / fit vs spatial situation (mapping rung 5)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_assembly_fit_cabe_b0.md](investigation_contract_geometry_assembly_fit_cabe_b0.md)  
**Report:** [investigation_report_geometry_assembly_fit_cabe_b0.md](investigation_report_geometry_assembly_fit_cabe_b0.md)  
**Parents:** [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) §5 · pose CLOSED @ **2456** · Scene3D-from-pose CLOSED @ **2462** · plate L×W **B0** · kit D CLOSED

## Verdict

**PASS WITH NOTES** · recommended Buy **`B1-min`**.

Live tree has **one** posed box–box pair (`esc` → `flight_controller` on `autonomía-de-10min`), both real boxes, pose **incomplete** (`x_mm=5` only). That is not Plate L×W (no page): one already-shipped Continuity turn can complete the axes. Shipping AABB in the **declared mm frame**, fail-closed on any missing axis, never `"cabe"` / VERIFIED / `ASSEMBLY_READY`, is the honest first compare.

`B0` is valid if Engineer wants to wait for a complete live pose before any math. `B1-copy` is the refuse-only cut. **B-naive** (card-lane / visor px / missing-axis-as-0) is **forbidden**.

No IC until Engineer ★.

---

## Checklist

| Criterion | Result |
|---|---|
| Live identities table | **Pass** — Cursor re-read both `state.json` + `project_spatial_nodes` |
| Complete posed box–box count = 0 | **Pass** |
| Partial pair count = 1 (`esc`/`flight_controller`) | **Pass** |
| `autonomía-de-5min` zero poses | **Pass** |
| Rooster still no box | **Pass** |
| Fail-closed missing axis | **Pass** — visor `?? 0` must **not** leak into engineering (N1) |
| Never card-lane / `localStorage` | **Pass** |
| Never reuse `scene3dLayout.ts` (Y↔Z + px) | **Pass** — confirmed in source |
| Frame class ≠ this Buy | **Pass** |
| Kit SKUs no geometry | **Pass** |
| Stub IC not treated as READY | **Pass** |
| Single recommended Buy | **Pass** — Claude **B1-min**; Cursor **keeps** it (N3) |
| Report-only (no `src/` this investigation) | **Pass** — report file; prior-cycle diffs unrelated |

---

## Independent checks

| Claim | Cursor |
|---|---|
| 10min `esc.declared_box_pose` | **Confirmed** `{origin_key: flight_controller, x_mm: 5.0, y_mm/z_mm: None}` |
| Board DTO | **Confirmed** `{"originKey":"flight_controller","xMm":5.0}` — no `yMm`/`zMm` keys |
| ESC box 50×21.6×12, FC box 44×84×12 | **Confirmed** via projector |
| `esc.mounted_on=frame_plate` ≠ pose origin FC | **Confirmed** (N2) |
| 5min: no pose; ESC no envelope; FC box only | **Confirmed** |
| `layoutSolidsFromPose` `yMm ?? 0` / `zMm ?? 0` + Y↔Z | **Confirmed** `scene3dLayout.ts` |
| `_declared_box_pose_dto` origin must be box | **Confirmed** |
| `GAP-FRAME-PROP-SIZE` never “cabe” | **Confirmed** `engineering_readiness._frame_class_gaps` / `project_closure` |

---

## Notes

### N1 — Visor already treats missing axes as 0. Engineering must not.

Display (`scene3dLayout.ts`) fills omitted `xMm`/`yMm`/`zMm` with **0** and swaps Y↔Z for CSS. B1-min AABB **must** live in Python on raw `declared_box_pose` mm, require **all three** axes, and **must not** call or port that layout function. First live walk on 10min will say **pose incompleta**, not a screening fact. That is ACCEPT, not a bug. Smoke after IC: declare `y` and `z`, then screening copy.

### N2 — Mount is not the compare

`esc` is mounted on `frame_plate` (no box). Pose origin is `flight_controller`. IC copy must not say the ESC “cabe en el FC” as assembly, nor that it fits on the plate. The fact is: **declared pose child vs origin envelope**, screening only.

### N3 — Why not B0 despite §A “zero complete pairs”

Contract §A flags zero **complete** pairs as B0 evidence. Cursor agrees the evidence exists and still defaults **B1-min**: the pair and both boxes already exist; the missing axes are user-declarable with shipped grammar; fail-closed is the mechanism (same pattern as adapter skip / kit catalog on an empty hole). B0 = wait until someone happens to type y/z before any compare exists. Engineer may still ★ **B0**.

### N4 — Center-to-center in declared LWH axes

Claude’s proposed model (child box centered at `(x,y,z)` vs origin at origin center, half-extents from L/W/H, **no** Y↔Z) matches visor **intent** (center-to-center) without stealing visor **pixels**. IC must lock axes to `POSE_AXES_HONESTY_LABEL` (`L→+X, W→+Y, H→+Z`). Single-level; no pose chains.

### N5 — 5min is the wrong smoke project for AABB

`autonomía-de-5min` ESC has **no** box. Use `autonomía-de-10min` (or give ESC a box first).

---

## Buys (after review)

| ★ | Meaning |
|---|---|
| **`B1-min`** | **Default** — named `esc`/`flight_controller` AABB in declared mm; fail-closed incomplete pose; screening copy; PASS/`ASSEMBLY_READY` unchanged |
| **`B1-copy`** | CLI/Continuity refuse or honest absence only — no AABB this Buy |
| **`B0`** | Park. No IC. Wait for a complete live pose (or never) |
| **B-naive** | **Forbidden** — card overlap, visor px, missing-axis-as-0, `"cabe"`/`VERIFIED`, Rooster L×W invention, cylinder |

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. Engineer ★ **B1-min** (2026-09-09). IC: [implementation_contract_geometry_assembly_fit_cabe_b1.md](implementation_contract_geometry_assembly_fit_cabe_b1.md). Package `0.3.8` · suite **2532**.
