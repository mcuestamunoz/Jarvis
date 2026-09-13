# Implementation Contract — Board Situar multi-box UX B1 (`B1-ux-situar`)

**Project:** Jarvis  
**Date:** 2026-09-12  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Should be Claude Code** — this Buy was executed by Cursor (role slip; recorded in review N1). Future Buys: Claude implements.  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** LANDING — **IMPLEMENTED** · [report](implementation_report_board_situar_multibox_ux_b1.md) · [review PASS WITH NOTES](implementation_review_board_situar_multibox_ux_b1.md) · UI **87** · await Engineer smoke  
**Parents:**
- [investigation_contract_board_situar_realism_novice_b0.md](investigation_contract_board_situar_realism_novice_b0.md)  
- [investigation_report…](investigation_report_board_situar_realism_novice_b0.md) · [review PASS WITH NOTES](investigation_review_board_situar_realism_novice_b0.md)  
- Nested-hit ACCEPT — [engineer_note_situar_nested_hit_select_card.md](engineer_note_situar_nested_hit_select_card.md) (scoped one-solid; this Buy covers **N>1** nearby draggables)  
- Board drag → pose B1 / Situar UX / free-camera **CLOSED** — writers & pose math **unchanged**  
- Feature: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)

**Type:** UI-only honesty for Situar when ≥2 box solids can drag.  
**Not** new pose writer. **Not** `isDraggableSolid` / copy-family situar. **Not** silhouette / plate L×W. **Not** novice layout pack. **Not** Three.js. **Not** LLM invent mm. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_board_situar_multibox_ux_b1.md`

**Cola (documented, not this Buy):** [engineer_note_board_situar_work_cola.md](engineer_note_board_situar_work_cola.md)

---

## 0. Engineer Buy (locked) — review N2 **Option A**

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-ux-situar`** — multi-box nested-hit affordance + **minimal** origin-picker honesty |
| 2 | Nested-hit mechanism | **Keep** `pointer-events: none` on non-selected solids + pane background drag → **selected** solid (hotfix #2). Do **not** revert to “click whatever is under cursor” |
| 3 | Affordance | (a) Situar hint copy must state plainly that background drag moves the **card-selected** piece; Alt+drag = orbit. (b) Hit-through solids get a **visible dim** (CSS) so peers look pass-through |
| 4 | Origin picker | Pure helper ranks candidates: **preferred** = subject’s `mountedOn` if that key is a box among solids · plus `frame_plate` if that solid is a box · then **all other** box keys. **Never** drop the fallback “all boxes” list when mounts are empty (15min case). **Never** silent default origin — user still picks + “Fijar origen” |
| 5 | Labels | Preferred options labeled in the `<select>` (e.g. `battery (montado en)` / `frame_plate (placa raíz)`); others keep bare key |
| 6 | Home for filter | This Buy owns `boxOriginCandidates` rewrite. Cola `B1-origin-assist` becomes **thinner or B0** — no second rewrite of the same list without ★ |
| 7 | Pose / HTTP / eligibility | Unchanged: C-113 POST, writer gates, `solidCopies≥2` never arms, disk never origin |
| 8 | Smoke | Multi-box: select A, drag near B → **A** moves; peers look dimmed; picker shows preferred first when `mountedOn` set, else full list |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Con Situar ON y varias cajas, veo qué pieza se mueve (la seleccionada),
las demás se ven passthrough, y el picker de origen prioriza montaje/
placa raíz sin inventar un origen por defecto.
```

---

## 1. You (implementer)

- Prefer a small pure module (e.g. `situarOriginCandidates.ts`) + unit tests; wire from `Scene3D.tsx`.  
- CSS: strengthen `.sb-solid--hit-through` visibility (opacity / face alpha) without changing layout math.  
- Hint string in `Scene3D.tsx` (Spanish, short).  
- Do **not** change `board_pose_bridge` / writers / `isDraggableSolid`.  
- Do **not** mutate `workspace/` demos (wild poses stay; smoke re-declares if needed).  
- Do **not** bump version.

---

## 2. Tests

| ID | Behavior |
|---|---|
| T1 | Ranking: `mountedOn` box preferred first; self excluded |
| T2 | Ranking: empty mounts → all other boxes, stable order; `frame_plate` preferred if boxed |
| T3 | Ranking: non-box / missing mount target never preferred |
| T4 | Existing boardPoseDrag / Scene3D-related UI tests still green |
| T5 | `npm test` in `ui/spatial-board` green |

---

## 3. Out of scope

Silhouette · plate L×W invent · copy-situar · novice pack · 3D mount edges · clusterCenterPx freeze · Conversation Engine · version bump

---

## 4. Done when

- [ ] Hint + dim affordance shipped  
- [ ] Origin ranking helper + Scene3D wire + T1–T3  
- [ ] Suites green; report written; cola note linked from PRIORIDAD  
- [ ] Package still `0.4.1`

---

## 5. Handoff

```text
Implementer → code + report
Cursor      → review
Engineer    → smoke Situar with ≥2 draggable boxes (not wild-pose golden)
```
