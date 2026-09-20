# Implementation Contract — Board 3D-first workshop + mount-chain inspector (`B1-board-3d-first-inspector`)

**Project:** Jarvis  
**Date:** 2026-09-18  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke on `dron-de-vigilancia-doméstico` / `10-min-autonomía`

**Status:** **ACCEPT CLOSED** (Engineer smoke 2026-09-20 — polish deferred)  
**Parents:**
- Engineer UX brief 2026-09-18 (screenshots Board split / Situar / Attack-board reference for “detail on demand only”)  
- Continuity spatial assembly + C-113 Situar — [lock](engineer_lock_continuity_spatial_assembly_feature.md)  
- Craft montage honesty — [lock](engineer_lock_craft_montage_honest_reproducible.md)  
- M7 / package **`0.4.2`** — Fase M CLOSED; this Buy is **UI workshop** before Fase C product  
- Selection model — `ui/spatial-board/src/boardSelection.ts` (session-only `selectedId`)  
- Projector — `src/jarvis/workspace/spatial_board.py` (`mountedOn`, `declaredBoxPose`, geometry)

**Type:** **UI / presentation Buy** (primary deliverable under `ui/spatial-board/`).  
**Goal:** Make the Board a **3D workshop** that helps work the engineering core — not a dense card wall with a 3D annex.  
**Not** new Continuity writers · not catalog bind from cards · not inventing mounts/poses · not Fase C firmware · not version bump · not Attack-board templates/tasks clone.

**Outputs (required):**
1. UI changes per locks below (`ui/spatial-board/`)  
2. Targeted UI/unit tests for selection → ancestor chain + view-mode tab + overlap picker  
3. `.jes/artifacts/implementation_report_board_3d_first_inspector_b1.md`  
4. Short USER_GUIDE note (or subsection) in `docs/USER_GUIDE_CRAFT_MONTAGE.md` — how to use Taller 3D / Grafo / inspector / picker (Spanish phrases for UI chrome OK)

**Checkpoint:** package **`0.4.2`** (no bump) · suite / UI tests green at ★

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-board-3d-first-inspector`** — 3D-first Board + inspector + overlap picker |
| 2 | Default view | **Taller 3D** = full-bleed (or near full-bleed) `Scene3D` as primary workspace |
| 3 | Cards graph | Keep current InfiniteCanvas **as secondary tab “Grafo”** — available, not default, must not steal vertical half by default |
| 4 | Inspector | On 3D selection → **right-side panel** with selected card in **summary** mode; expand “Ver todo” for full fields |
| 5 | Cascade | Walk **ancestors via `mountedOn`** from selection **up to assembly root (Main Plate / `frame_plate`)**; show that chain in the inspector (selection + ancestors). **Not** “everything nearby in 3D” |
| 6 | 3D dimming | Solids **on the chain** = full opacity; **all other** solids = dimmed/ghost. Clear selection → restore full opacity |
| 7 | Overlap picker | Generalize Situar **piece-strip / chip picker** to **always available** when a click hits an ambiguous stack (or user opens picker) — same pattern as Situar bottom chips, not only when Situar ON |
| 8 | Situar ON | **Yes:** 3D nearly full; inspector **collapses to chips** (piece strip + essential Situar chrome: origin picker, hints). No fat inspector column fighting Situar |
| 9 | Pin / compare | **Out of this Buy** — keep **single** `selectedId`. Named debt: optional pin later. Coherence: selection stays session highlight, not a second SoT |
| 10 | Mutation | **Unchanged:** pose = C-113 only; card drag in Grafo still ≠ pose; no optimistic SoT; refetch after pose commit |
| 11 | Projector | Prefer **reuse** existing node DTOs (`mountedOn`, fields, geometry). Backend change **only if** a pure helper is needed to compute ancestor chain consistently — prefer UI walk of `mountedOn` first |
| 12 | Version | **No** bump |
| 13 | Docs sync Buy | Orthogonal — may land before/after; this IC does not depend on `B1-docs-folder-truth-sync` |

**Product sentence:**

```text
El Board por defecto es un taller 3D: seleccionas en el craft,
ves un inspector ligero con la cadena de montaje hasta la placa,
y un picker cuando las piezas se solapan. El grafo de cards
sigue existiendo en una pestaña, sin saturar el trabajo.
```

**Engineer answers locked in:**

1. Grafo = pestaña (no molesta).  
2. Cascada = **ancestros hasta la placa**.  
3. Pin = **no en este Buy** (elección Cursor por coherencia).  
4. Situar ON = 3D dominante; inspector → chips.

---

## 1. Current as-is (evidence — do not regress)

| Fact | Where |
|---|---|
| Vertical split: InfiniteCanvas cards + Scene3D below | `InfiniteCanvas.tsx`, `spatial-board.css` |
| Cards always full `fields` dump | `SpatialCard` — no collapse |
| Shared `selectedId` cards↔3D | `boardSelection.ts` |
| Situar piece chips + origin picker | `Scene3D.tsx` (`.sb-scene3d__piece-strip`) |
| Pose write C-113 | `board_pose_bridge` / `POST …/pose` |
| `mountedOn` on nodes when declared + target projected | `spatial_board.py` |

---

## 2. Target UX (normative)

### 2.1 View modes (tabs)

| Tab id | Label (ES) | Content |
|---|---|---|
| `taller` | **Taller 3D** | Default. Scene3D primary; inspector dock; overlap picker; Situar |
| `grafo` | **Grafo** | Current InfiniteCanvas + cards + mount edges + minimap; optional compact 3D or hide 3D — **must not** be the first paint after open |

Persist last tab in **session** (or `localStorage` key scoped by project, presentation-only). Default on first visit = `taller`.

### 2.2 Inspector (Taller only · Situar OFF)

**When:** `selectedId` set and Situar OFF.

**Layout:** right dock (~280–360px, responsive; collapsible).

**Content (top → bottom):**

1. **Selected** — summary card: `title` / `kind` · `declaredName` · SKU if present · at most ~3–5 priority fields (prefer: montado en, masa/g if present, envelope/pose one-liner). Button **Ver todo** → full fields `<dl>` (current density).  
2. **Cadena hasta la placa** — ordered list of ancestors:  
   `selected → mountedOn → … → frame_plate` (or assembly-root plate id used by visor).  
   Each ancestor = summary row/card; click row → `onSelect(thatId)` (updates 3D highlight + chain).  
3. If no `mountedOn` chain: show selected only + honest empty state (“Sin cadena de montaje declarada hasta la placa”).

**Do not** dump every BOM card.

### 2.3 Ancestor walk (algorithm lock)

```text
chain = [selectedId]
cur = selectedId
seen = {selectedId}
while true:
  node = nodes[cur]
  parent = node.mountedOn   # DTO field; relation-only
  if parent is None: break
  if parent in seen: break  # cycle guard
  if parent not in projected nodes: break  # honest stop
  chain.append(parent)
  seen.add(parent)
  cur = parent
  if is_assembly_root_plate(parent): break
```

`is_assembly_root_plate`: reuse existing Main Plate / `frame_plate` assembly-root notion from Scene3D / layout (same id the visor treats as world root). Document the helper in report.

**Out:** do **not** walk `declaredBoxPose.originKey` as primary parent (pose frame ≠ mount graph). Optional note in report if they diverge on a smoke project.

### 2.4 3D dimming

- Chain ids (selection + ancestors) → full opacity / normal materials.  
- Other solids → dimmed (CSS opacity or material flag — keep simple; no new physics).  
- Multi-copy stations: dim/highlight by `selectId` / solid group rules already used for selection — do not invent per-copy SoT.  
- Clear selection → no dimming.

### 2.5 Overlap / stack picker

**Problem:** stacked boxes (FC/ESC/battery…) hard to click.

**Solution:** picker UI **same family** as Situar piece-strip chips:

- Always reachable in Taller (Situar ON or OFF).  
- Trigger A: click that hits multiple overlapping pickables → open picker listing candidates (ids + short labels), user chooses → `onSelect`.  
- Trigger B: explicit control “Piezas” / strip always visible with draggable/selectable solids (may reuse current chip strip; refine hit-test if needed).  
- Situar ON: strip remains the primary selection affordance; inspector dock hidden/collapsed per lock #8.

Hit-test perfection is best-effort: if exact multi-hit is hard in CSS-3D, **Trigger B (always-on strip) is sufficient for PASS**; multi-hit is PASS WITH NOTES if strip works.

### 2.6 Situar ON chrome

| Element | Behavior |
|---|---|
| Scene3D | Near full viewport height/width |
| Inspector dock | **Collapsed** — no right column of cards |
| Piece chips | Visible (selection) |
| Origin picker / hints / attest | Unchanged honesty rules |
| C-113 pose | Unchanged |

### 2.7 Grafo tab

Preserve today’s card density/behavior enough that existing craft-montage walks still work for users who open Grafo. No requirement to redesign SpatialCard in Grafo this Buy (optional: collapse later). Mount edges stay.

---

## 3. Non-goals / forbidden

| Forbidden | Why |
|---|---|
| Pin / dual selection / compare | Deferred; single `selectedId` |
| Writing pose from Grafo card drag | Still presentation overlay |
| Inferring mount chain from 3D proximity | Dishonest |
| Inventing `mounted_on` / envelopes in UI | SoT = Continuity |
| Catalog / DEFINE from inspector | U1 stance unless separate Buy |
| Attack-board templates / task cards | Wrong product |
| Version bump / Fase C features | Out |
| Removing Grafo entirely | Engineer: keep as tab |

---

## 4. Files likely touched (guidance · not exhaustive)

| Area | Paths |
|---|---|
| Shell / tabs | `InfiniteCanvas.tsx`, `main.tsx`, CSS |
| 3D | `Scene3D.tsx`, `Solid3D.tsx`, `spatial-board.css` |
| Inspector (new) | e.g. `InspectorDock.tsx` / `MountAncestorChain.tsx` / `SummaryCard.tsx` |
| Selection | `boardSelection.ts` (extend only if needed) |
| Tests | `ui/spatial-board` vitest / existing UI suite |
| Guide | `docs/USER_GUIDE_CRAFT_MONTAGE.md` short subsection |

Prefer small extracted components over bloating `Scene3D.tsx` further.

---

## 5. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Default view on fresh load = Taller 3D (not Grafo half-split as primary) |
| T2 | Tab switch Taller ↔ Grafo works; Grafo still shows cards |
| T3 | Select solid A with `mountedOn` chain to `frame_plate` → inspector lists ancestors in order ending at plate |
| T4 | Cycle / missing parent → chain stops honestly (no throw) |
| T5 | Dimming: non-chain solids marked dimmed when selection set; cleared when selection cleared |
| T6 | Summary vs Ver todo: default summary does not render full fields list |
| T7 | Situar ON → inspector dock not visible as column; chips/origin still usable |
| T8 | Overlap affordance: piece strip (or picker) can select a stacked id without relying on perfect 3D hit |
| T9 | Pose commit path still calls existing C-113 POST (no new writer) — smoke or unit mock |
| T10 | UI test suite green; no required Python suite growth unless a tiny pure helper is added under `workspace/` |

---

## 6. Smoke (Engineer)

On a project with plate + stacked mounts (e.g. vigilancia or 10min):

1. Open Board → lands in **Taller 3D** (cards not dominating).  
2. Click / chip-select FC (or battery) → inspector shows summary + ancestors to plate; others dimmed.  
3. **Ver todo** expands fields.  
4. Switch **Grafo** → old cards visible.  
5. **Situar ON** → 3D dominant; dock collapsed; move a singleton; pose still commits.  
6. Use strip/picker to select an occluded stack piece.

**ACCEPT when:** workshop feel is real; cascade honest; Situar unbroken; Grafo still reachable.

---

## 7. Named debt (explicit)

| Debt | Notes |
|---|---|
| Pin / compare two parts | After this Buy if Engineer still wants it |
| Multi-hit ray picker perfection | Strip may be enough |
| Collapse SpatialCard inside Grafo | Optional polish |
| Children-of-selection cascade | Not this Buy (ancestors only) |
| Inspector edits (declare mount/pose) | Separate Buy; Continuity remains CLI-primary |

---

## 8. Report shape

`.jes/artifacts/implementation_report_board_3d_first_inspector_b1.md`:

- Screens / behavior summary  
- Ancestor helper definition (`is_assembly_root_plate`)  
- What was reused vs new components  
- Situar interaction proof  
- Tests run + counts  
- Residual notes (hit-test, CSS dimming limits)

---

## 9. Acceptance

**PASS when:** locks §0 + T1–T10 + smoke path plausible.  
**PASS WITH NOTES OK for:** imperfect multi-hit if strip works; minor CSS polish.  
**FAIL if:** default still card-primary; cascade uses proximity; Situar pose broken; Grafo removed; pin shipped against lock; SoT mutated from UI outside C-113.

---

## 10. Handoff

```text
Engineer → ★ this IC
Claude   → implement ui/spatial-board + tests + report + guide blurb
Cursor   → independent review vs IC
Engineer → smoke §6 / ACCEPT
```

**Ordering vs other cola:** can run **before** Fase C and **in parallel or after** `B1-docs-folder-truth-sync` (no dependency either way).

---

## 11. PRIORIDAD blurb (paste on ★)

```text
COLA UI: B1-board-3d-first-inspector READY — Taller 3D default, Grafo tab,
inspector + ancestors→placa, dim others, overlap chips; Situar ON = chips;
no pin; no bump; C-113 intact.
```
