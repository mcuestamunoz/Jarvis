# Implementation Review — Frame arm envelope + visor X copies B1

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_frame_arm_visor_x_b1.md](implementation_contract_geometry_frame_arm_visor_x_b1.md)  
**Report:** [implementation_report_geometry_frame_arm_visor_x_b1.md](implementation_report_geometry_frame_arm_visor_x_b1.md)  
**Buy:** Engineer ★ **B1-arm-visor-X**

## Verdict

**PASS WITH NOTES**

Locks hold. Declared L×W×H on `frame_arm`; copies only at true quad-X + N=4; same station math as motors; one BOM key; no invent from 230. Closable after Engineer smoke §5.

---

## Checklist

| Criterion | Result |
|---|---|
| Writer allowlist `frame_arm` | **Pass** — `_ENVELOPE_ALLOWED_LITERAL_KEYS` |
| Parser noun `brazo`/`brazos`/`arm`/`arms` + exact key | **Pass** — P2; reuses `resolve_declared_part_noun` |
| SET needs three mm; no thickness→H fallback | **Pass** — `_NO_THICKNESS_FALLBACK_KEYS`; P6 pair → INCOMPLETE |
| `_solid_copies` frame_arm: own geometry + motors count==4 + `_quad_x_wheelbase_mm` | **Pass** — P3/P4 |
| N≠4 or missing quad_x/W → **no** `solidCopies` (single box, not row of 3) | **Pass** — documented prefer; P4 |
| Offsets = `_quad_x_station_points` only; same as motors | **Pass** — P3 + Cursor independent assert |
| Pose strip on copies | **Pass** — UI `expandSolidCopies` strips for any `solidCopies≥2` (U3/U9 pattern); no second formula |
| One `frame_arm` node | **Pass** — P3 |
| No library arm L/W invent | **Pass** — P5; version still `0.3.8` |
| Battery/plate/kit regressions | **Pass** — P6 + Cursor related suite |
| Non-goals (loose / Conversation Engine / 4 BOM keys / version) | **Pass** |
| P1–P6 | **Pass** — Cursor 7/7 |
| Full pytest | **Pass** — Cursor **2622** (matches report) |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Offsets byte-identical to motors @ W=230 | **Confirmed** |
| N=4 + `quad_x` but **no** `wheelbase_mm` → no copies | **Confirmed** (extra to P4 params) |
| `ui/` / version untouched this Buy | **Confirmed** — strip already generic |
| Pose Continuity subject does **not** add `frame_arm` this Buy | **Confirmed** — lock #5 = strip on expand, not a pose-subject Buy |

---

## Notes

### N1 — P4 coverage

IC P4 covers N=3 and missing `configuration`. Missing `wheelbase_mm` alone is not a pytest param; Cursor verified omit. Optional one-liner later — not a reopen.

### N2 — Stricter than motors/propellers on N≠4

Arm never emits a packed row. Honest for this part. Matches IC prefer clause.

### N3 — Live Board smoke still open

Parse/write/project chain verified (report + tests). Engineer must still: declare arm mm → reload Board → 4 boxes on X · one card. Record [engineer_smoke_geometry_frame_arm_visor_x_b1.md](engineer_smoke_geometry_frame_arm_visor_x_b1.md).

---

## Phase

Implementation **CLOSED** for review. **Smoke pending** Engineer §5. Package `0.3.8` · suite **2622**.
