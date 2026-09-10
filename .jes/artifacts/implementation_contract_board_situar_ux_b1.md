# Implementation Contract — Board Situar UX (viewport + fluid drag) B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · [review](implementation_review_board_situar_ux_b1.md) · UI **70** · smoke **ACCEPT** · next [free-camera IC](implementation_contract_board_situar_free_camera_b1.md)  
**Parents:**
- [smoke board_drag_pose_b1](engineer_smoke_board_drag_pose_b1.md) **ACCEPT**
- [engineer_note_board_situar_ux_followup.md](engineer_note_board_situar_ux_followup.md)
- C-113 CLOSED — `POST /pose` + `set_component_declared_box_pose` unchanged
- Package **`0.4.0`** · suite **2668**

**Type:** UI-only situar ergonomics.  
**Not** new writer. **Not** card-px→pose. **Not** multi-copy drag. **Not** envelope resize. **Not** Three.js. **Not** version bump. **Not** LLM.

**Output:** `.jes/artifacts/implementation_report_board_situar_ux_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **Situar UX B1** — larger pane + deeper zoom + fluid drag preview |
| 2 | Pane size | Default Scene3D height **≥ 420px** (or `min(50vh, …)` with min 420). When **Situar ON**, pane **≥ 56vh** (or equivalent clear expansion). Optional bottom-edge resize handle (persist height in `sessionStorage` only — never ProjectState) |
| 3 | Zoom | Widen Scene3D zoom: allow at least **0.25…4** (document actual). Keep situar `pxToMm` / payload math using live zoom |
| 4 | Fluid drag | While situar-dragging a singleton: **live-move** the solid in the pane (preview). On mouseup: existing `postDragPose` + refetch (discard preview). Mirror card `preview`/`commit` split — SoT still only on commit |
| 5 | Writer / HTTP | **Unchanged** C-113. No mid-drag POST storm |
| 6 | 2D minimap | **Out** of this Buy unless height change is &lt;10 lines — primary ask is Scene3D. Do not rename/repurpose “Mapa” |
| 7 | Axes / eligibility | Same B1 locks: X/Y only; Z untouched; `solidCopies≥2` never arms |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Con Situar ON el mapa 3D es grande, puedo acercarme de verdad, y al
arrastrar la pieza se mueve en vivo como una card; al soltar se guarda
igual que ahora.
```

---

## 1. You (Claude)

- `spatial-board.css` / `Scene3D.tsx` (+ optional small preview state). Prefer extending `computeDragPosePayload` + existing layout helpers over a second math path.
- Tests: zoom bounds if exported; preview helper pure if extracted; full UI suite + Python suite green.
- Do **not** change `board_pose_bridge.py` / writer unless a bug forces it (document).
- Do **not** bump version / mutate `workspace/` demos.

---

## 2. Intent

```text
Situar ON → pane tall
  → wheel zoom past old ×2 cap
  → drag battery: solid follows pointer live
  → drop: POST once → refetch matches preview
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| U1 | Zoom clamp allows values above former max 2 (and below 0.5 if min lowered) |
| U2 | Preview helper (if any) matches commit payload math for same deltas |
| U3 | Existing boardPoseDrag / pxToMm / bridge tests still green |
| U4 | Full `npm test` + full pytest green |

---

## 4. Out of scope

2D minimap redesign · card-px→pose · multi-copy · envelope resize · Three.js · LLM deactivate · version bump

---

## 5. Done when

- [ ] Pane clearly larger (esp. Situar ON)  
- [ ] Deeper zoom usable  
- [ ] Live drag preview + single commit on drop  
- [ ] Suites green; report written; `0.4.0`  

---

## 6. Handoff

```text
Claude  → implement + report
Cursor  → review
Engineer → smoke Situar on 5min
```
