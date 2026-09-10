# Investigation Review — Board drag / resize → Continuity writers

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_board_drag_place_b0.md](investigation_contract_board_drag_place_b0.md)  
**Report:** [investigation_report_board_drag_place_b0.md](investigation_report_board_drag_place_b0.md)  
**Parents:** [concept note](engineer_note_board_drag_place_concept.md) · [feature lock](engineer_lock_continuity_spatial_assembly_feature.md) · writers CLOSED · Scene3D-from-pose CLOSED · U1 visor read-only

## Verdict

**PASS WITH NOTES** · recommended Buy **`B1`** (pose-only, singleton solids, top-down Scene3D, minimal POST → existing writer + save).

Evidence matches the contract: GET-only board, card-px = `localStorage` only, Scene3D drag = camera tilt, no `pxToMm`, live 5min shows orphan FR poses on `prop_adapter` / `frame_standoff` beside `solidCopies: 4`. B2 correctly rejected. B0 is a real fallback (new mutation surface). B1+ resize correctly deferred.

No implementation IC until Engineer ★.

---

## Checklist

| Criterion | Result |
|---|---|
| §A gestures table + `file:line` | **Pass** |
| §B CLI writer → `save_state` path | **Pass** — Cursor spot-check `orchestrator` / `component_writers` / `workspace_manager` |
| §B GET-only + Node↔Python spawn gap named | **Pass** — confirmed `vite-plugin-jarvis-projects.ts` method gate |
| §C card-px / tilt / copies collisions | **Pass** |
| Live orphan pose + copies | **Pass** — Cursor re-read 5min `state.json` + projector (N1) |
| B0 honest (not straw) | **Pass** |
| B1 lean + blast radius + CONNECTIONS | **Pass** |
| B2 rejected on missing mm plane | **Pass** — no `pxToMm`; only `mmToPx` |
| B1+ deferred | **Pass** |
| Report-only (no code / version / workspace) | **Pass** — report claims; Cursor did not re-run full git audit beyond read |
| No IC authored in report | **Pass** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Middleware GET-only | **Confirmed** `vite-plugin-jarvis-projects.ts` — non-GET → `next()` |
| Scene3D background drag → `setTilt` only | **Confirmed** `Scene3D.tsx` |
| `mmToPx` exists; no `pxToMm` | **Confirmed** `scene3dScale.ts` |
| `expandSolidCopies` strips pose when `solidCopies >= 2` | **Confirmed** `scene3dLayout.ts` + test U3 |
| CONNECTIONS absence row drag→writers | **Confirmed** ~L970 |
| 5min `prop_adapter` pose ~(81,81,16) + `solidCopies: 4` | **Confirmed** |
| 5min `frame_standoff` pose ~(30,30,4) + `solidCopies: 4` | **Confirmed** |
| Singletons with pose DTO (battery / FC / ESC) | **Confirmed** — honest B1 drag targets exist |

---

## Notes

### N1 — Orphan pose + copies is live, not hypothetical

Projector still emits `declaredBoxPose` on the card/DTO when `solidCopies: 4` (strip is layout-only). Dragging a station solid would write one shared pose that the 3D copies ignore — dishonest. **Singleton-only** for B1 is mandatory, not optional polish.

Adjacent debt (not required for B1 IC): clear or hide card pose text when copies are active — separate micro-Buy if Engineer cares.

### N2 — U1 flip is the real cost of B1

Product-limits locked the board as non-mutation. B1 is a **narrow** exception (pose POST → `set_component_declared_box_pose` + save only). IC must:

- forbid DEFINE / catalog pick / envelope resize in the same Buy  
- flip or narrow CONNECTIONS L969–970 (new C-xxx or “pose-only CONNECTED; resize still absent”)  
- keep SoT = `state.json` via existing writer — no parallel schema

B0 remains correct if Engineer does not want that surface yet.

### N3 — Axis map for `pxToMm`

Visor layout uses declared Y↔Z swap into CSS (`scene3dLayout.ts`). Top-down mode + inverse must lock which screen axes map to declared `x_mm` / `y_mm` / `z_mm` (likely drag in plate L/W → X/Y, Z unchanged or separate). Do not invent a third frame. Prefer “untilted + documented 2-axis write; Z untouched on drag” unless Engineer ★ asks otherwise.

### N4 — Origin picker

Report’s “existing `originKey` or arm drag only after pick” matches writer honesty. IC must **not** silently default to Main Plate / assembly root.

### N5 — Smoke project

5min has usable singleton targets (`battery`, `flight_controller`, `esc`). Do **not** smoke-drag `prop_adapter` / `frame_standoff` while they have copies.

---

## Buys (after review)

| ★ | Meaning |
|---|---|
| **`B1`** | **Default** — singleton solid drag in top-down Scene3D → POST → `set_component_declared_box_pose` + save; no resize; no multi-copy drag |
| **`B0`** | Defer — keep typing-only; board stays U1 until mutation surface is ★’d as its own decision |
| **`B1+`** | Later — resize → envelope writer (after B1 lands) |
| **`B2`** | **Forbidden** — card-px → pose |

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. Engineer ★ **`B1`** (2026-09-10).  
IC: [implementation_contract_board_drag_pose_b1.md](implementation_contract_board_drag_pose_b1.md).  
Package `0.4.0` · suite **2661**.
