# Implementation Contract — Board click-inspect B1− (2D selection)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2429**) + Engineer Board smoke **ACCEPT**  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — ★ horizon (3D later; this Buy is the click-inspect half only)
- [investigation_contract_geometry_3d_placement_horizon.md](investigation_contract_geometry_3d_placement_horizon.md)
- [investigation_report_geometry_3d_placement_horizon.md](investigation_report_geometry_3d_placement_horizon.md) — lean **B1−**
- [investigation_review_geometry_3d_placement_horizon.md](investigation_review_geometry_3d_placement_horizon.md) — **PASS WITH NOTES** (N1: selection ≠ “abrir la card”)
- Glyphs B1 CLOSED @ **2344** · Board edges B2 CLOSED @ **2385** · Conn B1 CLOSED @ **2429**
- Fit stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**
- Pose B1+ — **B0 DEFERRED**

**Type:** Board **visor UX only** — client selection/highlight of an already-open card.  
**Not** 3D. **Not** CSS 3D / Three.js / r3f / meshes. **Not** new KNOW / `geometry` / envelopes. **Not** pose / `"cabe"`. **Not** Continuity / writers / projector.

**Baseline:** package **`0.3.8`** · suite **2429**

**Output:** `.jes/artifacts/implementation_report_geometry_board_click_inspect_b1minus.md`

---

## 0. Engineer Buy (locked)

Engineer `procede` 2026-09-08 after investigation review PASS WITH NOTES.

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1−** | YES — 2D click-inspect / selection only |
| 2 | Honest product sentence | **“Puedo seleccionar un nodo; la card correspondiente se destaca.”** — **not** “click abre la card” (fields already always visible) |
| 3 | Surface | Existing 2D cards. **No 3D visor in this IC** |
| 4 | Selection model | **Single** `selectedId: string \| null`. Clicking another card replaces. Clicking the already-selected card **keeps** it (no toggle-off) |
| 5 | Persist | **Session only.** Do **not** write `selectedId` to `localStorage`, URL, or `ProjectState` |
| 6 | Clear | Click empty viewport (not card / handle / toolbar / minimap / select) **or** Escape **or** project switch **or** selected id no longer in `nodes` |
| 7 | Click vs drag | Header grip: select on mousedown, then existing drag. Body: select (no new drag). Resize handles: **do not** change selection |
| 8 | Scroll/camera | **No** `scrollIntoView` / auto-pan to the selected card |
| 9 | Layout overlay | `{x,y,width,height}` `localStorage` **unchanged** — still layout, not pose |
| 10 | 3D / pose / cabe / B2 envelope | **Out.** Next 3D = separate rendering-tech investigation, not a surprise in this report |
| 11 | Version | **No** bump |

---

## 1. You

- Do **not** add Three.js, r3f, CSS 3D, canvas/WebGL, meshes, or a second Board view.
- Do **not** change `_geometry_from_spec`, `geometry` DTO, glyph scale (`min(mm × 0.5, 120)` stays), or invent disk height / motor cylinder.
- Do **not** change Python projector, writers, Continuity, catalog, or `mounted_on`.
- Do **not** treat selection as pose or as `"cabe"`.
- Do **not** persist selection.
- Do **not** bump package version.
- Full pytest suite green (expect **unchanged** count **2429** unless you add no Python tests — add **none**).
- `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.

---

## 2. Intent

```text
click card (header or body)
        ↓
selectedId = node.id   (client useState only)
        ↓
that SpatialCard gets sb-card--selected  (visible outline)
        ↓
fields / glyph / "montado en" unchanged — already always shown
```

Product sentence:

> “Puedo seleccionar un nodo; la card correspondiente se destaca.”

Scaffolding: a later 3D pick must be able to call the same `select(id)` without a second selection model. **Do not implement 3D here.**

---

## 3. Locked behavior

### 3.1 Pure helper (test authority)

New `ui/spatial-board/src/boardSelection.ts` — **no React**. Export:

```ts
export type BoardSelectionAction =
  | { type: "select"; id: string }
  | { type: "clear" };

export function nextSelectedId(
  current: string | null,
  action: BoardSelectionAction,
): string | null;

export function reconcileSelection(
  selectedId: string | null,
  nodeIds: Iterable<string>,
): string | null;
```

Rules:

- `select` → return `action.id` (replace; same id stays selected).
- `clear` → `null`.
- `reconcileSelection` → if `selectedId` is null, null; if `selectedId` is **not** in `nodeIds`, null; else unchanged.

`InfiniteCanvas` **must** route all selection transitions through these two functions (no parallel ad-hoc string sets).

### 3.2 Canvas wiring

`InfiniteCanvas`:

- `useState<string | null>(null)` for `selectedId`.
- Pass `selected={node.id === selectedId}` and `onSelect={(id) => setSelectedId((cur) => nextSelectedId(cur, { type: "select", id }))}` into each `SpatialCard`.
- On successful `onPanStart` (empty viewport — existing `shouldIgnorePan` is false): also `setSelectedId((cur) => nextSelectedId(cur, { type: "clear" }))`. Pan behavior otherwise **unchanged**.
- `keydown` Escape (when focus is not in toolbar `<select>`): clear.
- When `projectId` changes: clear.
- After `nodes` update: `setSelectedId((cur) => reconcileSelection(cur, nodes.map(n => n.id)))`.

Do **not** raise z-index of the selected card (outline only). Edges SVG unchanged (`pointer-events: none`).

### 3.3 Card

`SpatialCard`:

- New props: `selected: boolean`, `onSelect: (id: string) => void`.
- `<article>` gets `sb-card--selected` when `selected`; `aria-current="true"` when selected, omit/false otherwise. Keep `data-node-id`.
- Header `onMouseDown`: call `onSelect(node.id)` then existing `startDrag`.
- Body (`sb-card__body`, including name + glyph + fields): `onMouseDown` → `onSelect(node.id)` only. **Do not** start drag from the body (today’s behavior).
- Resize handles: existing `startResize` only — **do not** call `onSelect`.

### 3.4 Chrome

- CSS: `.sb-card--selected` — clearly visible 2px (or equivalent) highlight outline/border distinct from default `#3a3a3a`. No layout shift (use `outline` or keep `border-width` constant).
- Toolbar hint: add selection to the existing Spanish hint, e.g. keep zoom/pan/mover/tamaño and append `· click: seleccionar`. Do not replace the whole string with 3D copy.

### 3.5 Non-goals (explicit)

3D solids · CSS 3D · Three.js/r3f · glyph scale change · `scrollIntoView` · multi-select · persist selection · pose · `"cabe"` · projector/Python · Continuity · catalog · version bump · collapsing/expanding card fields · click-to-edit `mounted_on`

---

## 4. Tests (required)

**Python:** none. Do not add `tests/test_*click*`. Suite count stays **2429**.

**UI** — `ui/spatial-board/src/boardSelection.test.ts`:

| # | Case |
|---|---|
| U1 | `null` + select `"esc"` → `"esc"` |
| U2 | `"esc"` + select `"motors"` → `"motors"` |
| U3 | `"esc"` + select `"esc"` → `"esc"` (no toggle-off) |
| U4 | `"esc"` + clear → `null` |
| U5 | `null` + clear → `null` |
| U6 | `reconcileSelection("esc", ["esc", "motors"])` → `"esc"` |
| U7 | `reconcileSelection("esc", ["motors"])` → `null` |
| U8 | `reconcileSelection(null, ["esc"])` → `null` |

Run: full pytest (report count); `cd ui/spatial-board && npm test && npm run typecheck`.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `ui/spatial-board/src/boardSelection.ts` | **new** — `nextSelectedId` + `reconcileSelection` |
| `ui/spatial-board/src/boardSelection.test.ts` | **new** — U1–U8 |
| `ui/spatial-board/src/InfiniteCanvas.tsx` | state, clear, pass props, Escape, project/nodes reconcile, hint |
| `ui/spatial-board/src/SpatialCard.tsx` | `selected` / `onSelect`; header+body select; handles unchanged |
| `ui/spatial-board/src/spatial-board.css` | `.sb-card--selected` |
| `.jes/artifacts/implementation_report_geometry_board_click_inspect_b1minus.md` | write |

**Do not change:** `src/` · `tests/` · `library/` · projector · glyphs · edges geometry · `useBoardNodes` persistence keys · package version

---

## 6. Done criteria

- [ ] Single persistent highlight; honest sentence (not “abre la card”)
- [ ] Empty viewport click + Escape + project switch + missing id all clear
- [ ] Header select+drag still works; body selects; handles do not select
- [ ] Selection not in `localStorage` / state.json
- [ ] U1–U8 green; pytest still **2429**; `npm test` + `typecheck` green
- [ ] Implementation report written
- [ ] Engineer Board smoke recommended (click ESC / motors / fondo / Escape) before close

---

## 7. Stop conditions

Stop and ask before: any 3D/WebGL/CSS-3D, projector/DTO change, persisting selection, multi-select, auto-camera, collapsing fields, pose/`cabe`, or version bump.
