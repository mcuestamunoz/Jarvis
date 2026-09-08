# Implementation Review — Board click-inspect B1− (2D selection)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_board_click_inspect_b1minus.md](implementation_contract_geometry_board_click_inspect_b1minus.md)  
**Report:** [implementation_report_geometry_board_click_inspect_b1minus.md](implementation_report_geometry_board_click_inspect_b1minus.md)  
**Buy:** ★ B1− — visor selection only (not “abrir la card”)

## Verdict

**PASS WITH NOTES**

IC locks held. Visor-only. No 3D, no projector, no persistence, no pose/`cabe`. Closable after Engineer Board smoke ACCEPT.

---

## Checklist

| Criterion | Result |
|---|---|
| Honest sentence (highlight, not reveal) | **Pass** — fields still unconditional |
| Single `selectedId`; no toggle-off | **Pass** — U3 + live replace ESC→motors |
| Session only (no localStorage / state) | **Pass** — `useBoardNodes` untouched |
| Clear: empty viewport / Escape / projectId / missing id | **Pass** — wired through `nextSelectedId` / `reconcileSelection` |
| Header select+drag; body select; handles no `onSelect` | **Pass** (handles: code; live click blocked by review sandbox) |
| No auto-pan / z-index raise | **Pass** — outline only |
| Hint append `· click: seleccionar` | **Pass** — live toolbar |
| No Python / DTO / 3D lib | **Pass** — `src/` `tests/` `library/` clean |
| U1–U8 | **Pass** |
| pytest | **Pass** — Cursor **2429** |
| `npm test` / `typecheck` | **Pass** — **15** / clean |
| Version | **None** — `0.3.8` |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest -q` | **2429 passed** |
| `cd ui/spatial-board && npm test` | **15 passed** (8 new + 7 prior) |
| `npm run typecheck` | **clean** |
| `git diff --stat -- src/ tests/ library/` | **empty** |
| Live Board `:5173` | ESC body → `sb-card--selected` + `aria-current=true` on `esc`; motors body → only `motors`; Escape → none; empty `.sb-viewport` click → none. Blue 2px outline visible. Hint includes `click: seleccionar`. 14 cards. |

All `setSelectedId` paths go through `nextSelectedId` or `reconcileSelection`.

---

## Notes

### N1 — Engineer smoke still the close gate

**CLOSED 2026-09-08** — Engineer Board smoke **ACCEPT**: [engineer_smoke_geometry_board_click_inspect_b1minus.md](engineer_smoke_geometry_board_click_inspect_b1minus.md). Recuadro azul solo en la card tocada.

### N2 — `_current` rename

IC named the first arg `current`. It is unused (select/clear ignore prior value). `_current` to satisfy `noUnusedParameters` is cosmetic. Callers unchanged.

### N3 — `nodes` effect during drag

`preview()` replaces the `nodes` array every move, so `reconcileSelection` re-runs. Same id → React bails. Not a behavior bug.

### N4 — Horizon

This Buy is **not** 3D. Next 3D solids = separate rendering-tech investigation.

---

## Phase

Implementation **CLOSED**. Engineer smoke ACCEPT. Next = 3D rendering-tech investigation ([contract](investigation_contract_geometry_3d_rendering_tech.md)). Pose/`cabe` untouched. Package `0.3.8` · suite **2429**.
