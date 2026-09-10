# Implementation Contract — Board drag → Continuity pose B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · [review](implementation_review_board_drag_pose_b1.md) · suite **2668** · smoke **ACCEPT** ([smoke](engineer_smoke_board_drag_pose_b1.md)) · UX follow-up [IC](implementation_contract_board_situar_ux_b1.md)  
**Parents:**
- [investigation_review_board_drag_place_b0.md](investigation_review_board_drag_place_b0.md) — **PASS WITH NOTES** · lean **B1**
- [investigation_report_board_drag_place_b0.md](investigation_report_board_drag_place_b0.md)
- [concept note](engineer_note_board_drag_place_concept.md)
- Feature lock: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)
- Writer CLOSED: `set_component_declared_box_pose` (`component_writers.py`)
- Visor CLOSED: Scene3D-from-pose · multi-hop · `solidCopies` / stations
- Standoff count gate B4-min **CLOSED** @ **2661** (review PASS) — orthogonal
- U1 product-limits: board was read-only — **this Buy is the narrow mutation exception**

**Type:** First honest **Board → ProjectState** input for pose only.  
**Not** envelope resize (B1+). **Not** card-px → pose (B2 forbidden). **Not** drag of `solidCopies ≥ 2` nodes. **Not** DEFINE / catalog / Continuity grammar changes. **Not** Conversation Engine. **Not** Fit VERIFIED.

**Baseline:** package **`0.4.0`** · suite **2661** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_board_drag_pose_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1 — pose-only drag** (singleton solids) |
| 2 | Surface | **Scene3D only** — new **top-down / untilted** mode (tilt locked to `rotateX=0`, `rotateY=0` while situating). Do **not** wire 2D card drag |
| 3 | Eligible solids | Node has geometry **and** `solidCopies` absent or `< 2`. If `solidCopies ≥ 2` → **no drag arm** (click-select only). Never invent per-copy pose |
| 4 | Origin | Drag **armed** only when `declaredBoxPose.originKey` already exists **or** Engineer picks an origin from a small UI list of **box** keys (same gate as writer). **Forbidden:** silent default to Main Plate / assembly root / `mounted_on` |
| 5 | Axes written | Drag updates **`x_mm` and `y_mm`** in declared box axes (L→+X, W→+Y). **`z_mm` unchanged** if already set; if no prior pose, write `z_mm=None` (or keep prior `None`). Do **not** invent Z from screen. Document screen→declared map in report (top-down: screen Δx → declared X; screen Δy → declared Y after the same Y↔Z CSS convention used by `layoutSolidsFromPose` — pick one honest mapping and test it) |
| 6 | Math | Add `pxToMm` inverse of existing `mmToPx` (`scene3dScale.ts`). Valid only in untilted mode. Round-trip tests required |
| 7 | Commit | On drop: build `DeclaredBoxPose(origin_key=…, x_mm=…, y_mm=…, z_mm=…)` → **only** `set_component_declared_box_pose` → persist `state.json` (same SoT as CLI). Writer `ValueError` → HTTP 4xx + honest message; no silent invent |
| 8 | HTTP | New **POST** on Vite plugin (today GET-only). Suggested: `POST /api/projects/:id/pose` body `{ component_key, origin_key, x_mm, y_mm, z_mm }` (nulls allowed for axes). Bridge: small Python entry (spawnSync) that `ProjectState.model_validate_json` → writer → `write_json`/`save_state` equivalent → optionally reprint nodes JSON. **No** full orchestrator / LLM |
| 9 | Reload | After 2xx, re-`fetchProjectNodes` and refresh Scene3D (existing GET). Do not treat `localStorage` as success |
| 10 | CONNECTIONS | Narrow absence rows: add **C-113** (or next free id) Board pose POST → `set_component_declared_box_pose` + save — 🟢. Keep “resize / DEFINE / catalog-from-board” **NOT IMPLEMENTED**. Update map note in report |
| 11 | Grammar | `declara…` **unchanged** — both paths remain valid |
| 12 | `ui/` polish | Minimal: situar toggle + drag cursor on eligible solids. No Three.js rewrite, no themes |
| 13 | Version | **No** bump |

**Product sentence:**

```text
En modo situar (vista cenital), arrastro una pieza única (sin copias X)
respecto a una caja origen ya elegida; al soltar, Jarvis guarda los Δmm
con el mismo writer que declara… — no es layout de cards ni fit VERIFIED.
```

**Not:**

```text
arrastrar cards 2D · drag de motor/standoff con solidCopies · resize L×W×H ·
origen inventado · localStorage como pose · Conversation Engine
```

---

## 1. You (Claude)

- Implement POST bridge + `pxToMm` + top-down situar mode + singleton drag → writer → save → refresh.
- Prefer one small Python module under `src/jarvis/` (e.g. board pose bridge) callable as `-m` from the Vite plugin — **not** a new architectural subsystem beyond that thin I/O shell.
- Tests: Python bridge (happy path + writer reject + missing project); TS `pxToMm` round-trip; optional UI unit if cheap.
- Update `docs/system_map/CONNECTIONS.md` (+ canvas/map one-liner if you already touch docs in this Buy — otherwise report lists the exact CONNECTIONS edit and Cursor can sync living docs in review).
- Do **not** implement resize/envelope. Do **not** drag multi-copy nodes. Do **not** bump version. Do **not** mutate Engineer `workspace/` demos except via the new path under test fixtures.
- **STOP** if you need per-copy pose, card-px calibration, or a second pose schema.

---

## 2. Intent

```text
Scene3D situar ON (tilt 0,0)
  → drag singleton battery (origin already frame_plate_2)
  → drop at +10 mm X, −5 mm Y (Z kept)
  → POST → set_component_declared_box_pose → state.json
  → GET nodes → solid moves; card shows new Δ
prop_adapter with solidCopies:4 → drag never arms
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| P1 | Bridge: valid pose write persists `declared_box_pose` on disk (tmp project) |
| P2 | Bridge: writer reject (disk origin / self-origin / missing key) → non-zero / 4xx, no partial save |
| P3 | `pxToMm(mmToPx(x))` round-trip within float tolerance |
| P4 | Eligibility: node with `solidCopies ≥ 2` is not draggable (unit or pure helper) |
| P5 | Axis lock: drag path does not invent `z_mm` when prior was `None` (or documents keep-prior — assert chosen lock) |
| P6 | Existing Continuity pose CLI tests still green; full pytest green |

---

## 4. Out of scope

Envelope resize (B1+) · card-px→pose · multi-copy drag · origin auto-default · snap grid · undo stack · DEFINE/catalog-from-board · Fit VERIFIED · standoff count reopen · sourced #4 · Conversation Engine · version bump

---

## 5. Done when

- [ ] Situar drag → same writer → `state.json`  
- [ ] Singleton-only; multi-copy never arms  
- [ ] POST named; GET-only era ended for this one route  
- [ ] CONNECTIONS updated (C-113 or documented)  
- [ ] §3 + full suite green; package `0.4.0`  
- [ ] Report written  

---

## 6. Handoff

```text
Claude  → implement + report
Cursor  → review vs this IC (+ CONNECTIONS/docs if deferred)
Engineer → smoke: situar battery/FC/ESC on 5min; do NOT drag adapter/standoff copies
```
