# Implementation Review — Motor visor copies from the project’s `motor_count` B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_motor_count_instances_b1.md](implementation_contract_geometry_motor_count_instances_b1.md)  
**Report:** [implementation_report_geometry_motor_count_instances_b1.md](implementation_report_geometry_motor_count_instances_b1.md)  
**Buy:** Engineer ★ **B1** — visor copies, N from the motors spec, not a default of 4

## Verdict

**PASS WITH NOTES**

IC locks held. Count SoT is the motors spec’s `motor_count`. Quad-X and `current_parameters` are not read. No default 4. One card still. Copies expand in the visor row with unique `layoutId` and shared `selectId`. Pose stripped on copies. Live demo still has **zero** motor solids (no Ø). Fit QUEUED. Closable. Engineer smoke **ACCEPT**.

---

## Checklist

| Criterion | Result |
|---|---|
| `_solid_copies` only `suggested_key=="motors"` | **Pass** |
| Geometry gate + `2..16` integer | **Pass** — Cursor also checked 0/17 omit, 2/16 emit |
| Never default 4 / never `quad_x` / never `current_parameters` | **Pass** — source + P5 |
| DTO omit when None | **Pass** — same pattern as `geometry` |
| One `id=="motors"` node | **Pass** — P1 |
| Propellers never `solidCopies` | **Pass** — P1 |
| `expandSolidCopies` `motors#i` / strip pose | **Pass** — U1/U3 |
| Scene3D expand-before-layout; `key=layoutId` `id=selectId` | **Pass** |
| `Solid3D.tsx` untouched | **Pass** — `git diff` empty |
| Row layout, not wheelbase X | **Pass** — `layoutSolidsFromPose` unchanged |
| P1–P7 + U1–U4 | **Pass** |
| Suite **2473** + UI **38** + typecheck | **Pass** — Cursor re-ran |
| Version `0.3.8` | **Pass** |
| Fit stub QUEUED | **Pass** |
| Live census: 1 motors card, no geometry, no `solidCopies` | **Pass** |
| No catalog Ø seed | **Pass** — `library/` diff empty |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `_solid_copies` reads only `suggested_key`, `_geometry_from_spec`, `properties.motor_count` | **Confirmed** `spatial_board.py:337-361` |
| Literal 4 never substituted | **Confirmed** — bounds 2 and 16 only |
| P1–P7 | **Confirmed** 7 passed |
| U1 originX strictly increasing | **Confirmed** |
| Scene3D maps `layoutId` into `layoutSolidsFromPose` / `clusterCenterPx` | **Confirmed** `Scene3D.tsx:76-91` |
| Live motors: `motor_count` 3, no `geometry`, no `solidCopies` | **Confirmed** `project_spatial_nodes_from_path` |
| Live propellers: one disk, no `solidCopies` | **Confirmed** |
| Live frame: `wheelbase_mm` 230 unused by this Buy | **Confirmed** |
| `git diff` empty: writers, orchestrator, pose assist, Solid3D, boardSelection, package.json, pyproject, library | **Confirmed** |
| Full pytest **2473** | **Confirmed** this review |

---

## Notes

### N1 — No named test for 0 / 17

§3.1 requires omit. Code does. Cursor probed 0 and 17 → no key; 16 → 16. Add those two if `_solid_copies` is edited later. Not a reopen.

### N2 — Visor trusts `solidCopies`

`expandSolidCopies` expands any node with `N >= 2` and does not re-check `id==="motors"` or cap at 16. Honest: projector is the gate. A hand-forged DTO could draw 99 disks. Acceptable this Buy.

### N3 — Copies path is fixture-only on the live demo

SunnySky still has no Ø. N-copies rendering is proven on synthetic disks (P1/U1). §6 called that live emptiness **ACCEPT**.

---

## Phase

Implementation **CLOSED**. Engineer smoke ACCEPT ([smoke](engineer_smoke_geometry_motor_count_instances_b1.md)). Mapping rungs 3–5 later ★. Fit still QUEUED. Package `0.3.8` · suite **2473**.
