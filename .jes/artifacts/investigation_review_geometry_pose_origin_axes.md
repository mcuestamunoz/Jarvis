# Investigation Review — Geometry pose origin & axes (body frame)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_pose_origin_axes.md](investigation_contract_geometry_pose_origin_axes.md)  
**Report:** [investigation_report_geometry_pose_origin_axes.md](investigation_report_geometry_pose_origin_axes.md)  
**Parents:** pose revisit **CLOSED Keep B0** · 3D horizon rungs 1–2 **CLOSED** · Geometry-for-all envelope matrix

## Verdict

**PASS WITH NOTES**

Default lean **B0 — defer convention entirely (not even name-only)** is correct. A component key is an honest *which*, not a millimetre origin. `+Z up` is free and insufficient. A horizontal axis cannot be named because **arms are not individuated** (unlike plates). Completing Class A still yields **zero** placement facts. **No READY IC.** Fit stub stays **QUEUED**. Arm individuation is a **reversal to watch**, not a Buy.

Engineer ★ still required to **lock B0** (or override).

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + one paragraph | **Pass** — B0, not B1 name-only |
| Vision map rungs 1–2 vs 3 | **Pass** |
| 14 demo keys Class A vs B | **Pass with N1** — keys covered; plates collapsed to one row |
| Class A next labels (`sourced-search ★` / freeze / …) | **Pass with N2** — column omitted; substance in “missing for a solid”; filled below |
| Sourced-search not run in this report | **Pass** |
| A–E answered; no pose/name sketch | **Pass** — D7 correctly rejects scaffolding theater |
| Completing Class A ≠ assembled 3D | **Pass** — required sentence present |
| Fit QUEUED; no code / no IC | **Pass** |
| Arm individuation named, not recommended | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `FRAME_ARM_KEY = "frame_arm"` only; plates get ordinals | **Confirmed** — `aerial.py:341-356`; N7 lock “ordinal plate siblings **only**” |
| Live demo: `frame_plate` + `_2` `_3` `_4`; one `frame_arm` | **Confirmed** — `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` |
| Live `frame_arm` properties | **thickness_mm + material only** — **no `count`** on this bind (see N3) |
| `motors.mounted_on = frame_arm`; FC/ESC → `frame_plate`; battery → `frame`; sensors → `esc` | **Confirmed** |
| `ComponentSpec` still `parent_key` + `mounted_on` | **Confirmed** — `action_schema.py:171,184` |
| Fit stub | **Confirmed** — `QUEUED — DO NOT IMPLEMENT` |
| No `src/` / `ui/` / `tests/` from this investigation | **Consistent** with investigator claim |

---

## Agreement with report core

1. **Key ≠ millimetre origin** — load-bearing; reaffirms 2026-09-07 A2 with the Class A hole made explicit (`frame_plate` has no surface).  
2. **Name-only B1 is theater** — agree. `+Z up` alone cannot express “ESC on that plate.”  
3. **Horizontal axis blocked on arm individuation** — agree; this is new, specific, and correctly **not** a Structure Buy.  
4. **Class A ⊥ Class B** — agree; sourced L×W later still does not place.  
5. **Reject mixing** as standing rule — agree; do not ★ envelope search *in order to* fake an assembled 3D.

---

## Notes

### N1 — 14 keys, 11 table rows

IC asked one row per key. Four plates share one row. Same Class A/B facts. Not a FAIL.

### N2 — Class A next (reviewer fill)

IC required this column. Report left it implicit. Cursor mapping (no new fetch):

| Key | Class A next |
|---|---|
| motors, propellers, esc, battery, FC | `none` |
| `frame` | `shape-mismatch` (`wheelbase` / optional body footprint ≠ box) |
| `frame_arm` | `thickness-by-design` |
| `frame_plate` / `_2` `_3` `_4` | `sourced-search ★` (Armattan page already empty in Geometry-for-all — search may fail again) |
| `frame_cage` | `sourced-search ★` |
| `frame_standoff` | `sourced-search ★` (height on other SKUs; this bind has none; still no diameter) |
| sensors | `freeze` |

Required sentence (substance was in §7, not quoted): **a later sourced-search ★ is how Class A grows; this investigation did not run it.**

### N3 — `count` is not the wall

Report says `frame_arm` “carries a `count` property.” On the **live demo** it does not (`test_frame_catalog_bind_ux` even asserts count absent on some binds). The wall is **one addressable key** vs plate ordinals. Count is optional multiplicity on that type node — same honesty class as `motor_count`, not four `frame_arm_2` siblings.

### N4 — “7 of 8” frame parts

Non-root frame parts on this demo are **seven** (arm, four plates, cage, standoff). Nit only.

### N5 — Do not ★ arm individuation from this review

Naming it as reversal is correct. Building `frame_arm_2`… would be a **Structure** model Buy (addressability of instances), not a Geometry pose IC, and not today’s PRIORIDAD. Same class of decision as “one motor card vs four copies.”

---

## Recommended Engineer moves

| Choice | Effect |
|---|---|
| ★ **B0 defer convention** (recommended) | Origin/axes stay unnamed; pose stub stays DEFERRED; Geometry **idle** on rung 3 |
| ★ Class A sourced-search (optional, parallel) | Later investigation/agent fetch per N2 candidates — **not** pose |
| ★ Arm individuation | **Not** opened here — would need its own Structure investigation ★ |
| ★ Override (written risk / invented +X) | Explicit new ★; do not ship name-only `+Z` as a convention Buy |
| ★ Skip to fit | **Forbidden** |

---

## Phase

Investigation **reviewable**. Engineer did **not** ★ idle-B0. Next = [box-anchor origin](investigation_contract_geometry_pose_box_anchor.md). Plate/front-arm B0 **stands** as a closed *path*, not as vision-closed. Package `0.3.8` · suite **2429**.
