# Implementation Contract — Board Situar free camera B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** **CLOSED** — smoke **ACCEPT** ([smoke](engineer_smoke_board_situar_free_camera_b1.md)) · [review](implementation_review_board_situar_free_camera_b1.md) PASS WITH NOTES · UI **80**  
**Parents:**
- [smoke situar UX](engineer_smoke_board_situar_ux_b1.md) **ACCEPT** + free-camera blocker
- [Situar UX B1](implementation_contract_board_situar_ux_b1.md) CLOSED (pane/zoom/preview)
- [Board drag pose B1](implementation_contract_board_drag_pose_b1.md) — originally locked tilt `(0,0)` for `pxToMm` honesty; **this Buy supersedes that camera lock only**
- C-113 writer/POST **unchanged**

**Type:** UI camera + situar gesture.  
**Not** full 3D ray-plane CAD unprojection. **Not** multi-copy drag. **Not** envelope resize. **Not** version bump. **Not** LLM.

**Baseline:** package **`0.4.0`** · Python **2668** · UI **70** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_board_situar_free_camera_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **Situar free-camera B1** |
| 2 | Toggle | **Situar ON must not change `tilt`.** Delete / stop using `SITUAR_TILT` / `effectiveTilt = situar ? (0,0) : tilt`. Keep whatever angle the Engineer already had |
| 3 | Orbit while situating | **Re-enable** background drag → camera orbit even when Situar ON (same as Situar OFF). Solid mousedown still starts pose-drag (stopPropagation). Engineer can orbit, then drag a solid, without leaving Situar |
| 4 | Pose drag axes | Default drag still writes **`x_mm` / `y_mm`** via existing `computeDragPosePayload` (screen Δ / zoom → mm). **Document** that under tilt this is an orthographic-style approximation (same foreshortening risk already named) — **not** a CAD unproject. Do **not** invent a second pose schema |
| 5 | Third axis (“hacia atrás” / height) | **`Shift` + drag vertical** adjusts **`z_mm`** (screen Δy → Δz_mm via same `pxToMm`/zoom); horizontal with Shift still adjusts `x_mm` **or** ignore horizontal under Shift (pick one; document). Preview must follow. Without Shift, `z_mm` still untouched as today |
| 6 | Preview / commit | Keep Situar UX live preview + single POST on drop |
| 7 | Writer / HTTP | C-113 only — no bridge change unless payload already supports `z_mm` (it does) |
| 8 | Copy / chrome | Situar toggle label unchanged; optional one-line hint: “fondo: órbita · arrastre: XY · Shift+arrastre: Z” |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Activo Situar y la cámara no salta. Oroito al ángulo que necesito,
arrastro en XY, y con Shift muevo en Z — sin plano forzado.
```

**Not:**

```text
forzar cenital · bloquear órbita en Situar · unproyección CAD perfecta ·
Three.js · Conversation Engine
```

---

## 1. You (Claude)

- `Scene3D.tsx`: remove forced untilt; allow `onBackgroundMouseDown` orbit when situar; Shift→Z in drag payload/preview path (`boardPoseDrag.ts` helpers preferred).
- Tests for Shift→Z math + “situar does not force tilt” if testable; full UI + Python suites green.
- Do **not** reintroduce `SITUAR_TILT` as default. Do **not** bump version.

---

## 2. Intent

```text
Orbit to side view → Situar ON (tilt unchanged)
  → drag solid: XY in declared mm
  → Shift+drag: z_mm changes (“atrás”/alto)
  → drop: one POST → refetch
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| U1 | Helper: normal drag payload leaves `z_mm` prior / null unchanged |
| U2 | Helper: Shift+vertical path changes `z_mm` by `pxToMm(Δy/zoom)` (sign documented) |
| U3 | No code path sets tilt to `{0,0}` when enabling situar (grep/test or Scene3D invariant) |
| U4 | Full `npm test` + pytest green |

---

## 4. Out of scope

True perspective unprojection · multi-copy · envelope · 2D minimap · LLM · version bump

---

## 5. Done when

- [ ] Situar does not reset camera  
- [ ] Orbit works with Situar ON  
- [ ] Shift+drag writes Z; normal drag XY  
- [ ] Suites green; report; `0.4.0`  

---

## 6. Handoff

```text
Claude  → implement + report
Cursor  → review
Engineer → smoke: angle free + hacia atrás via Shift/orbit
```
