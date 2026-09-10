# Investigation Contract — Board drag / resize → Continuity writers

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_board_drag_place_b0.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · [review](investigation_review_board_drag_place_b0.md) · await Engineer ★ **B1** or **B0**  
**Report:** [investigation_report_board_drag_place_b0.md](investigation_report_board_drag_place_b0.md)  
**Parents:**
- Engineer ★ post-`v0.4.0` — “piezas sueltas + arrastrar y ampliar → guardar” ([concept note](engineer_note_board_drag_place_concept.md))
- Feature lock: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)
- Writers CLOSED: `set_component_declared_box_pose` · `set_component_declared_box_envelope`
- Visor CLOSED: Scene3D-from-pose · multi-hop · assembly root · `solidCopies`
- Board product limits: visor = **read-only mutation surface** (U1) — layout = `localStorage` overlay
- CONNECTIONS: “Board drag/resize → pose/envelope writers — NOT IMPLEMENTED”
- **Out of this investigation:** B4 `standoff_count` · #4 sourced dims · Fit VERIFIED · HD-* · CAD mate solver

**Type:** Minimum honest **input-surface** investigation.  
**Not** an IC. **Do not implement. Do not bump version. Do not invent millimetres. Do not flip fit to VERIFIED.**

**Checkpoint:** package **`0.4.0`** · suite **2652** · tag `v0.4.0` / `checkpoint-continuity-spatial-assembly`

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

---

## 0. Role split

```text
Engineer  → drag/resize as situar input (same writers as declara…)
Cursor    → this contract; review; IC only after ★ on Buy shape
Claude    → investigation_report_board_drag_place_b0.md
```

---

## 1. Why this exists

Continuity spatial assembly @ `v0.4.0` already lets the Engineer **type** envelopes and poses. Typing Δmm is hard; inventing numbers via LLM is forbidden.

Product insight (Engineer):

> Pieces start loose on the Board; **drag** = pose; **resize** = envelope; Jarvis **persists** via the **same** Continuity writers — ProjectState remains SoT.

Wrong next step:

```text
· Treat 2D card localStorage {x,y,w,h} as millimetre pose
· Persist only in browser and call it “posed”
· LLM invent drop coordinates
· CAD mate / auto-fit VERIFIED / Conversation Engine
· N BOM clones so each copy can be dragged independently
· Reopen Board B1 layout-on-disk as if it were this Buy
```

Right question:

> On the **live tree**, what gestures exist today (2D cards vs Scene3D), what do they write (if anything), and what is the **minimum honest first Buy** — including **B0 leave the gap** — that turns a calibrated mm gesture into a call of the **existing** pose/envelope writers without a second SoT?

---

## 2. Locked stances

1. **Same writers.** Any Buy commits through `component_writers.set_component_declared_box_pose` and/or `set_component_declared_box_envelope` (caller saves `state.json`). No parallel pose schema.  
2. **Not localStorage SoT.** Card overlay pixels are presentation debt; they must not become engineering truth.  
3. **Scene3D camera ≠ solid drag.** Today Scene3D mousedown/move tilts the camera — do not conflate with moving a solid.  
4. **API honesty.** Live board plugin is **GET-only**. A mutation path (if Buy ≠ B0) must be named explicitly (minimal POST → writers + save, or CLI-only bridge) — not smuggled as “refresh.”  
5. **Origin still box.** Pose origin rules of the writer hold; drag cannot invent a disk origin or a mute plate as origin.  
6. **Multiplicity.** One BOM key → N `solidCopies`; drag moves the **subject**; copies follow projector rules. Do not recommend N sibling specs.  
7. **Grammar stays.** `declara…` remains valid; UI is another input, not a replacement.  
8. **U1 tension.** Product-limits locked the board as non-mutation. This investigation may recommend a **narrow** exception — it must say so and sketch the CONNECTIONS note (C-xxx or amend absence). It must **not** open general DEFINE/catalog-from-card.  
9. **No version bump. No Three.js rewrite** as the Buy. Prefer existing CSS Scene3D + `scene3dLayout` mm math.  
10. Reuse Continuity refuse / writer `ValueError` messages. **No** Conversation Engine.

---

## 3. Baseline to inventory (cite live tree · `file:line`)

| Surface | Check |
|---|---|
| `ui/spatial-board/vite-plugin-jarvis-projects.ts` | Confirm GET-only `/api/projects` + `/nodes`; no POST |
| `useBoardNodes.ts` / `useNodeGestures.ts` | Card drag/resize → `localStorage` overlay only |
| `Scene3D.tsx` | What “drag” does today (camera vs solids) |
| `scene3dLayout.ts` | mm↔px, composed centers, stations — reusable for drop math? |
| `component_writers.set_component_declared_box_pose` / `_envelope` | Gates, allowlists, “caller must save” |
| Orchestrator Continuity declare handlers | How CLI persists after writer (save path to mirror) |
| `docs/system_map/CONNECTIONS.md` absence rows | Quote board→writers NOT IMPLEMENTED |
| Concept note + feature lock §Next | Confirm product intent without expanding scope |
| Live demo (read-only `workspace/`) | Optional: one posed solid + one unposed — gesture would need which origin? |

Do **not** mutate `workspace/`. Read-only.

---

## 4. Report sections (required)

### A. Gestures as-is
Table: surface × gesture × units × persistence × engineering effect (none / localStorage / ProjectState).

### B. Writer + save path as-is
How CLI `declara…` reaches disk today. What a board commit would have to call. Gaps (HTTP, auth, project id → `state.json`).

### C. Honesty collisions
Where card-px drag would lie if wired naively. Where Scene3D tilt would lie if mistaken for pose. Station copies vs subject drag.

### D. Buy ladder (evaluate all; pick one lean)

| Lean | Meaning |
|---|---|
| **B0 — Defer** | Keep typing-only; board stays U1 visor; document why (e.g. write-path architecture not ready) |
| **B1 — Pose-only** | Drag solid in **mm frame** (Scene3D or calibrated top-down) → `set_component_declared_box_pose` + save; resize **out** |
| **B1+ — Pose + envelope** | B1 plus resize handles → `set_component_declared_box_envelope` for allowlisted keys |
| **B2 — Card-px → pose** | Map 2D overlay to Δmm — **default reject** unless you prove a calibrated mm plane already exists on the 2D map |

State blast radius (files / new route / tests / CONNECTIONS). Name **out**: snap grid, undo stack, multi-select, CAD mates, VERIFIED fit.

### E. Contingency sketch (if lean ≠ B0)
Name-only: gesture surface · Δmm computation vs which origin · write endpoint shape · poll/reload after save · copy-select behavior. **Not** an IC.

### F. Explicit non-goals
One short list.

---

## 5. Done when

- [ ] All §4 sections present with live `file:line` cites  
- [ ] One executive lean + one sentence  
- [ ] B0 evaluated honestly (allowed)  
- [ ] No code, no version bump, no IC authored in this report  
- [ ] Engineer can ★ Buy / Defer without guessing the write path

---

## 6. After ★

| ★ | Next |
|---|---|
| B0 | Close investigation; PRIORIDAD → cola item or idle |
| B1 / B1+ | Cursor authors thin IC; Claude implements; smoke on 5min |
| Reject / re-scope | New contract |
