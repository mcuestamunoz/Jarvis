# Implementation Contract — Board Situar experience B1 (`B1-situar-experience`)

**Project:** Jarvis  
**Date:** 2026-09-12  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement)  
**Reviewer:** Cursor against this IC · Engineer smoke

**Status:** LANDING — **IMPLEMENTED** · [report](implementation_report_board_situar_experience_b1.md) · [review PASS WITH NOTES](implementation_review_board_situar_experience_b1.md) · UI **99** · await Engineer smoke S1–S5  
**Parents:**
- Engineer field (2026-09-12): “la experiencia es malísima en el 3D” after multi-box UX + ranking/drop fix  
- [investigation realism/novice B0](investigation_report_board_situar_realism_novice_b0.md) · [review](investigation_review_board_situar_realism_novice_b0.md)  
- Multi-box UX B1 + fix LANDING — [IC](implementation_contract_board_situar_multibox_ux_b1.md) · [report §Fix](implementation_report_board_situar_multibox_ux_b1.md) · [review fix](implementation_review_board_situar_multibox_ux_b1_fix.md)  
- Nested-hit ACCEPT — [engineer_note_situar_nested_hit_select_card.md](engineer_note_situar_nested_hit_select_card.md) — **refine, do not discard** the ESC-inside-box need  
- Feature: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)  
- Cola: [engineer_note_board_situar_work_cola.md](engineer_note_board_situar_work_cola.md)

**Type:** UI-only Situar **ergonomics**. Three experience locks.  
**Not** silhouette / plate L×W invent. **Not** copy-family situar / N BOM. **Not** Three.js. **Not** new pose writer / POST shape / pose math. **Not** Conversation Engine. **Not** LLM invent mm. **Not** version bump. **Not** `workspace/` mutation.

**Output:** `.jes/artifacts/implementation_report_board_situar_experience_b1.md`

**Checkpoint:** package **`0.4.1`** · UI **91** · suite ~**2747**

---

## 0. Why this Buy

Multi-box honesty (hint, dim, ranking tiers, preview-hold) is **necessary** and still insufficient. Live Engineer experience:

```text
Situar ON → 3D pane eats the card row → cannot pick the piece
Click another box under the cursor → ignored (always-on hit-through)
Drop → world still feels unstable / hostile
Racimo ≠ drone (OUT — silhouette / data, not this Buy)
```

Product sentence after this Buy:

```text
Con Situar ON sigo viendo y eligiendo piezas (2D usable o lista en el
pane), puedo clickar otra caja 3D para seleccionarla cuando no estoy
arrastrando, y el racimo no se recentra a cada drop.
```

---

## 1. Engineer Buy (locked) — three experience locks

| # | Lock | Decision |
|---|---|---|
| **E1** | **2D stays usable with Situar ON** | Situar must **not** make the card canvas unusable. Pick **one** approach (implementer chooses smallest that passes smoke): **(A)** cap Situar pane height so `.sb-viewport` keeps a **minimum usable height** (document the px/vh — e.g. 2D ≥ ~280px or ≥40% of board column), **and/or** **(B)** add a compact **piece strip** inside `.sb-scene3d` (buttons for each **situar-draggable** box id) that calls the same `onSelect` as cards. Prefer A+B if A alone still leaves cards under the pane on typical laptop heights. |
| **E2** | **Click solid → select that solid (idle)** | Refine nested-hit: `pointer-events: none` on non-selected solids **only while a situar solid-drag is active** (or preview pending / posting — same window as today’s cluster freeze), **not** whenever `selectedId` is set. Idle + Situar ON: click another **draggable** box solid → `onSelect(that id)` (and may arm drag per existing Solid3D handler). **Keep** pane-background drag → move **selected** when peers are hit-through **during** an active drag (ESC-inside-outer still works via card/strip select + pane drag). Alt+drag orbit unchanged. Disks / `solidCopies≥2` remain non-draggable. |
| **E3** | **Stable cluster while Situar ON** | While `situar === true`, **do not** recompute the world camera-center from `clusterCenterPx` on every pose settle. Freeze cluster to the value at Situar-ON (or first settled layout after ON). Recompute when Situar turns **OFF**, or when the user hits an explicit control if you add one (optional “Recentrar 3D” button — nice-to-have, not required). Preview-hold from the multi-box fix **stays**. |
| 4 | Writers / eligibility | Unchanged: C-113 POST, `isDraggableSolid`, origin picker ranking (siblings / already-origin) untouched unless a compile touch is forced |
| 5 | Hint copy | Update situar hint to match E2 (click caja = elegir; arrastre mueve seleccionada; Alt = órbita) |
| 6 | Version | **No** bump |
| 7 | Out | Silhouette · plate L×W · motors/prop situar · novice pack · Three.js · invent mm |

---

## 2. Nested-hit honesty (do not regress ESC)

The ACCEPT nested-hit smoke (**card ESC → drag anywhere in pane**) must still pass:

1. Select `esc` (card **or** strip **or** idle click if visible).  
2. Situar ON.  
3. Drag on pane background → **esc** moves.  
4. Outer overlapping box must **not** steal the drag **while the drag is active**.

E2’s “idle click selects peer” is the only intentional change to hit-through scope. If a conflict appears, prefer: strip/card select + during-drag hit-through over “never select from 3D.”

---

## 3. You (Claude)

- `spatial-board.css` / `Scene3D.tsx` / possibly thin strip component.  
- Pure helpers + unit tests where logic extracts cleanly (e.g. `pointerEventsNone` predicate, cluster freeze gate).  
- Do **not** change `board_pose_bridge` / writers / `situarOriginCandidates` ranking tiers unless forced — ranking fix stays.  
- Do **not** mutate `workspace/`. Do **not** bump version.  
- Report: what height/strip choice you took for E1; smoke steps.

---

## 4. Tests

| ID | Behavior |
|---|---|
| T1 | Predicate/helper: hit-through **false** when situar+selected but **not** dragging/posting/preview |
| T2 | Predicate/helper: hit-through **true** when situar+selected+drag/preview/posting |
| T3 | Cluster freeze gate: while situar ON, settled center does not follow a layout bbox change (unit or documented integration) |
| T4 | Existing situarOriginCandidates + boardPoseDrag suites still green |
| T5 | `npm test` + `npm run typecheck` in `ui/spatial-board` green |

---

## 5. Smoke (Engineer)

| # | Check |
|---|---|
| S1 | Situar ON → can still select a box **without** fighting the 3D pane (2D visible and/or strip) |
| S2 | Idle: click box B in 3D → B selected (yellow); then drag → B moves |
| S3 | Nested ESC path still works (select esc → pane drag moves esc) |
| S4 | Drop a piece: **no** whole-racimo recenter; piece stays where dropped (preview-hold intact) |
| S5 | Situar OFF → cluster may recompute / feel normal again |

**ACCEPT** if S1–S4 hold on 5min or 15min with ≥2 draggable boxes.

---

## 6. Done when

- [ ] E1–E3 shipped  
- [ ] T1–T5 green; report written  
- [ ] Package still `0.4.1`  
- [ ] Engineer smoke ACCEPT  

---

## 7. Handoff

```text
Engineer  → ★ this IC (or amend E1 A/B)
Cursor    → IC only (this file); review after Claude
Claude    → implement + report
Engineer  → smoke S1–S5
```
