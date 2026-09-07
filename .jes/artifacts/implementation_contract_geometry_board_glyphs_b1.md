# Implementation Contract — Board glyphs (box + disk, representar-complete only) — visualizar B1

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS** · CLOSED (suite **2344**)  
**Review:** [implementation_review_geometry_board_glyphs_b1.md](implementation_review_geometry_board_glyphs_b1.md)  
**Report:** [implementation_report_geometry_board_glyphs_b1.md](implementation_report_geometry_board_glyphs_b1.md)  
**Parents:**
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md) — Geometry Progression Lock B1
- [investigation_contract_geometry_board_glyph_vocabulary.md](investigation_contract_geometry_board_glyph_vocabulary.md)
- [investigation_report_geometry_board_glyph_vocabulary.md](investigation_report_geometry_board_glyph_vocabulary.md)
- [investigation_review_geometry_board_glyph_vocabulary.md](investigation_review_geometry_board_glyph_vocabulary.md) — **PASS WITH NOTES**
- Geometry `representar` CLOSED through suite **2336**

**Type:** Board **visualizar** — declarative 2D glyphs from existing dims.  
**Not** pose / assembly / fit / CAD. **Not** new dimension sourcing.

**Baseline:** package **`0.3.8`** · suite **2336**

**Output:** `.jes/artifacts/implementation_report_geometry_board_glyphs_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — glyphs `{box, disk}` only |
| 2 | Ladder | **`visualizar`** — “volumen físico declarado”; ≠ ensamblado / cabe |
| 3 | Shape rule | Driven by **which PropertyValue keys are present**, not a hardcoded family table |
| 4 | Absence | Insufficient dims → **omit** `geometry` (card unchanged) — no dashed/partial glyph |
| 5 | **N1** box 2D | Footprint **`length_mm` × `width_mm`**; `height_mm` carried in payload for honesty/tooltip, not as a fake 3D solid |
| 6 | Disk | Prefer `diameter_mm` if present; else `diameter_in` × **25.4** for glyph mm-scale only; **never** change text `fields` units |
| 7 | Motor | **Disk** via `diameter_mm` only — **do not** stitch to `stator_height_mm`; **do not** resurrect overall axial height |
| 8 | DTO | New optional key **`geometry`** — **never** reuse card `width`/`height` (those stay pixel layout) |
| 9 | Authority | Projector computes; UI **does not** parse `"50 mm"` from `fields` |
| 10 | Slots | `kind: "slot"` → **no** `geometry` |
| 11 | Version | No bump unless Engineer asks after review |

---

## 1. You

- Do **not** add pose / `mounted_on` / fit / clearance / cylinder or bar renderers.
- Do **not** invent dims for plates/arms/frame/unsourced batteries.
- Do **not** change catalog seeds or FC dimension table values.
- Do **not** mutate engineering state from the Board.
- Do **not** bump package version unless asked.
- Full suite green (+ UI typecheck if the repo already runs one in CI/scripts — do not invent a new CI system).
- Write `implementation_report_geometry_board_glyphs_b1.md` when done.

---

## 2. Intent

```text
ComponentSpec.properties (existing mm / in)
        ↓
project_spatial_nodes → optional node["geometry"]
        ↓
SpatialCard draws box or disk inside the card chrome
        ↓
card still has x,y,width,height as pixel layout (unchanged semantics)
```

Product sentence:

> “Sé qué componente es y sé qué volumen físico declarado ocupa.”

---

## 3. Locked behavior

### 3.1 Geometry payload (projector)

In `src/jarvis/workspace/spatial_board.py`, when emitting a **component** or **part** node (not slot), compute optional geometry from `spec.properties`:

**`box`** — only if `length_mm`, `width_mm`, **and** `height_mm` are all present (numeric values):

```json
{
  "shape": "box",
  "length_mm": <float>,
  "width_mm": <float>,
  "height_mm": <float>
}
```

2D draw uses **length × width** as the rectangle aspect (N1). `height_mm` is included so the UI may show a small caption/tooltip (optional) and so the payload remains a true box declaration — not dropped.

**`disk`** — only if **not** a box candidate, and exactly one drawable diameter path exists:

- If `diameter_mm` present → use it.  
- Else if `diameter_in` present → `diameter_mm_equiv = diameter_in * 25.4` for drawing only.

```json
{
  "shape": "disk",
  "diameter_mm": <float>
}
```

(For props sourced in inches, still emit the mm-equivalent number under `diameter_mm` in the geometry object; text fields keep `"5 in"`.)

**Priority if both a full box triple and a diameter somehow appear:** emit **`box`** (complete L×W×H wins). Do not emit both.

**Never emit geometry when:** slot; missing required keys; only thickness; only stator pair without following disk rule; only one of L/W/H.

Omit the `geometry` key entirely when absent (do not send `null` unless existing JSON style already prefers nulls — prefer omit).

Helper name suggestion: `_geometry_from_spec(spec) -> dict | None`. Keep pure and unit-tested.

### 3.2 Node DTO

Extend emitted dict / TS type:

```ts
geometry?: {
  shape: "box" | "disk";
  length_mm?: number;
  width_mm?: number;
  height_mm?: number;
  diameter_mm?: number;
};
```

Do **not** rename or overload `width`/`height` on the node (card pixels).

### 3.3 UI — `ui/spatial-board/`

- Update `types.ts` `SpatialNode` with optional `geometry`.
- In `SpatialCard` (or a tiny child component): if `geometry` present, render a simple SVG/CSS outline:
  - **box:** rectangle with aspect `length_mm : width_mm`
  - **disk:** circle sized from `diameter_mm`
- Scale: fit the glyph into a fixed max box inside the card body (e.g. max ~96–120 CSS px on the longer edge) so a 5" prop and a 44mm FC stay **proportionally** correct relative to each other when both glyphs are visible — same mm→px scale factor for all glyphs on screen (compute from max edge among… **or** fixed `PX_PER_MM` constant chosen so typical parts fit; lock one approach in the report). Prefer a **constant `PX_PER_MM`** (e.g. chosen so a 200 mm edge ≈ 100 px) documented in the implementation report — simpler than viewport-relative scaling for B1.
- Optional (N5): for `disk`, a one-line caption under the glyph: `Ø … mm` (or keep silent if cluttered — either OK; do not invent height).
- Slots / no geometry: unchanged card chrome.
- No new drag semantics; glyph is not a separate movable node.

### 3.4 Honesty

- No CLI/Continuity claim that glyphs verify fit or show “the drone.”
- No assembly copy in UI chrome beyond shape drawing.

---

## 4. Tests (required)

Extend `tests/test_spatial_board_projector.py` (and/or adjacent):

1. **Box:** synthetic / fixture component with L×W×H → node has `geometry.shape == "box"` and the three mm values.  
2. **Disk mm:** motor-like props with `diameter_mm` only → `shape == "disk"`.  
3. **Disk in:** propeller-like `diameter_in: 5` → `diameter_mm == pytest.approx(127.0)`.  
4. **Absence:** thickness-only or empty props → **no** `geometry` key.  
5. **Slot:** slot nodes never carry `geometry`.  
6. **No stitch:** properties with `diameter_mm` + `stator_height_mm` but no L×W×H → still **disk** (not cylinder / not box).  
7. **Card pixels untouched:** emitted `width`/`height` remain the projector’s card pixel defaults (not physical mm).

UI: if there is an existing lightweight front-end test harness, add one smoke; if not, projector tests + manual Board smoke note in report suffice (do not invent Jest/Vite test infra).

Run full Python suite; report count.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | `_geometry_from_spec` + attach on `_emit` for non-slots |
| `tests/test_spatial_board_projector.py` | §4 |
| `ui/spatial-board/src/types.ts` | optional `geometry` |
| `ui/spatial-board/src/SpatialCard.tsx` (+ tiny CSS if needed) | draw box/disk |
| `.jes/artifacts/implementation_report_geometry_board_glyphs_b1.md` | write |

**Do not change:** catalog JSON dims, `aerial.py` FC table values, ERF/Control, sensors BOM tails (unless accidental import — avoid), version.

---

## 6. Explicit non-goals

Pose · `mounted_on` · fit/clearance · cylinder/bar renderers · frame plate/arm glyphs · inventing L×W · UI parsing of `fields` text · second geometric SoT · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · weakened tests

---

## 7. Done criteria

- [x] Nodes with full L×W×H emit `geometry.shape == "box"`.
- [x] Prop/motor diameter paths emit `disk` with mm-equivalent size.
- [x] Incomplete / slots omit `geometry`.
- [x] Card `width`/`height` remain pixel layout keys.
- [x] Board UI draws box/disk when `geometry` present.
- [x] Full suite green; implementation report written (incl. `PX_PER_MM` choice + N1 footprint note).
- [x] Cursor review PASS before Engineer close.

---

## 8. Role split

```text
Engineer ★ → Buy B1 (this contract)
Claude     → implement exactly this IC + report
Cursor     → implementation review
Engineer   → optional Board smoke / next focus
```
