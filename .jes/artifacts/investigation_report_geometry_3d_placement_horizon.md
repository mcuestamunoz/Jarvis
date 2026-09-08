# Investigation Report — Geometry 3D Placement Horizon (First Slice)

**IC:** [investigation_contract_geometry_3d_placement_horizon.md](investigation_contract_geometry_3d_placement_horizon.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Review:** [investigation_review_geometry_3d_placement_horizon.md](investigation_review_geometry_3d_placement_horizon.md) — PASS WITH NOTES  
**Buy:** Engineer ★ **B1−** (`procede` 2026-09-08) → [implementation_contract_geometry_board_click_inspect_b1minus.md](implementation_contract_geometry_board_click_inspect_b1minus.md) READY FOR CLAUDE

---

## 1. Executive recommendation

**B1− — click-inspect only, zero 3D rendering technology, as the immediate next Buy.** Full 3D solids (B1) is honestly reachable from the existing `geometry` DTO with **no new KNOW** for the 5 families that already glyph today (motors, propellers, esc, battery, flight_controller) — confirmed live. But *what renders it* is a genuinely open, non-trivial decision this investigation cannot responsibly prescribe: the visor has zero 3D-capable rendering infrastructure today (pure 2D absolute-positioned DOM + one SVG overlay for edges), Three.js/r3f/meshes are explicitly forbidden for this cycle, and CSS 3D transforms — the only technology-free alternative — cannot honestly draw a disk/cylinder without approximating a curved surface as a many-sided polygon, a rendering-fidelity decision, not a data-honesty one. Click-inspect, by contrast, needs **zero new rendering technology** — it's a selection-state addition to the existing 2D board — and independently delivers real product value (the "click → card" half of the horizon sentence) without waiting on the 3D-technology question at all. Recommend sequencing: **B1− now, B1 next — gated on its own short rendering-technology investigation**, not bundled into the same IC.

---

## 2. Live glyph/3D-fuel matrix (demo, re-verified this session — not rubber-stamped)

Re-ran `project_spatial_nodes` against the live `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` this session (`src/jarvis/workspace/spatial_board.py:56`):

| Key | `geometry` (glyph-ready today) | `mountedOn` | 3D-ready without new KNOW? |
|---|---|---|---|
| `motors` | `{shape: disk, diameter_mm: 27.9}` | `frame_arm` | ✅ — a thin cylinder/flat disk at declared diameter, no invented height |
| `propellers` | `{shape: disk, diameter_mm: 127.0}` | `motors` | ✅ — same |
| `esc` | `{shape: box, 50×21.6×12mm}` | `frame_plate` | ✅ — rectangular prism, all 3 axes real |
| `battery` | `{shape: box, 37×35×75mm}` | `frame` | ✅ — same |
| `flight_controller` | `{shape: box, 44×84×12mm}` | `frame_plate` | ✅ — same |
| `frame` (root) | `None` | `None` | ❌ — see §3 (re-verified: `body_length_mm`/`body_width_mm` exist on the *iFlight* seed row but are a **different property key** than `_geometry_from_spec` reads, and still have no accompanying height on any row) |
| `frame_arm` / `frame_plate` ×4 / `frame_cage` / `frame_standoff` | `None` | `None` | ❌ — thickness/material/label/height-text only, no L×W ever sourced (unchanged since Geometry-for-all B1) |
| `sensors` (Here3) | `None` | `esc` | ❌ — identity frozen, zero dims path exists |

**Notable, freshly-confirmed fact not in the IC's own snapshot table:** `propellers.mountedOn` is now `"motors"` and `sensors.mountedOn` is now `"esc"` on the live demo — both were `None` as recently as the Conn investigation two cycles ago. The Engineer's own Continuity walk has already connected them since. 5 of 14 live nodes have `geometry`; 9 do not, for the reasons already established in this project's own prior, closed investigations (not re-litigated here, only re-verified).

---

## 3. Visor as-is (re-verified, file:line)

- **Projector → API → React, one pipeline, no second SoT.** `ui/spatial-board/vite-plugin-jarvis-projects.ts:97-112`: `projectNodes(statePath)` runs `spawnSync(python, ["-m", "jarvis.workspace.spatial_board", statePath])` **fresh on every request** — the exact same `project_spatial_nodes_from_path` (`spatial_board.py:197-199`) used by every test in this repo. Served at `GET /api/projects/:id/nodes` (`vite-plugin-jarvis-projects.ts:141-142`), fetched by `ui/spatial-board/src/projects.ts:22-24` (`fetchProjectNodes`). A 3D view would consume this **exact same JSON**, no new backend route, no cached mesh store, no second read of `state.json`.
- **`_geometry_from_spec`** (`spatial_board.py:227-276`, re-read in full this session): box requires the full `length_mm`+`width_mm`+`height_mm` triple; disk requires exactly one diameter (`diameter_mm`, else `diameter_in`×25.4). Confirmed **unchanged** since Glyph B1 — still exactly `{box, disk}`, still returns `None` on any partial data, never stitches unrelated dimensions.
- **`SpatialGlyph.tsx`** (full file read): 2D-only — draws a flat `<div>` rectangle or circle, scaled by `constants.ts:33-34`'s `GLYPH = {pxPerMm: 0.5, maxPx: 120}` via `scaled(mm) = min(mm * 0.5, 120)`. **This scale function is capped, not purely linear** — anything over 240mm renders at the same 120px regardless of actual size. This is a real, previously-uninspected technical fact directly relevant to a "3D at declared scale" claim: the *existing* 2D scale already breaks strict proportionality past 240mm (chosen deliberately for 2D card-fit reasons, per the Glyph B1 report), so a 3D view claiming "true declared scale" cannot simply reuse this exact function — it needs its own (likely simpler, uncapped, camera-zoom-driven) scale, a small but real new piece of logic, not a reuse.
- **`SpatialCard.tsx`** (full file read): **every card's `fields` (and `geometry`, when present) render unconditionally, always** — `node.fields.map(...)` (line 44-49) has no collapsed/expanded state. The only interactive handlers on a card are `onMouseDown` for drag (`startDrag`, header grip) and resize (`startResize`, 4 corner handles) — **zero `onClick`, zero selection state, zero "closed" state to open.** This directly answers Governing Question 4: **the card already *is* the always-open inspect surface** — there is no existing "closed" representation for a click to reveal. "Click solid → open card" in a future 3D view is therefore not "revealing hidden info" but a **new cross-view navigation concept** (3D scene → find/scroll-to/highlight the matching 2D card, which already shows everything).
- **`DeclaredMountEdges.tsx`** (full file read, confirmed renamed from `MountEdges.tsx` since the last cycle touched it — same content): a bare, unlabeled `<line>` per edge, `aria-hidden="true"`, `pointer-events: none`. Confirmed presentation-only — still reads only `node.mountedOn`, never card text, never infers from proximity. In a 3D view this remains **exactly a relation indicator**, never a fastener/joint pose — re-affirmed, not re-argued, per Locked Stance 3/5.
- **`useBoardNodes.ts`** (re-confirmed unchanged): the `localStorage` `{x,y,width,height}` overlay is still 100% client-side pixel layout, never sent to the server, never read by any Python code — confirmed still structurally impossible to leak into "pose," consistent with every prior Geometry investigation this session.

---

## 4. Buy options

| Option | Assessment |
|---|---|
| **B0 — Defer** | Defensible on pure "wait for pain" grounds, but harder to justify given the Engineer has already ★-locked a named 3D horizon (`engineer_lock_geometry_3d_placement_horizon.md`) — B0 would mean re-litigating a decision already made, not responding to new evidence against it. Not recommended, but named as still technically available since 5/14 nodes glyphing today is itself already a real, useful 2D deliverable that nothing *requires* extending into 3D immediately. |
| **B1− — Click-inspect only (recommended immediate Buy)** | Add a selection state to the existing 2D board: clicking a card (or, once B1 ships, a solid) highlights/scrolls to it — reusing the card exactly as it renders today (§3's "already the inspect surface" finding). **Zero new rendering technology, zero new DTO fields, zero new dims.** Delivers the "click → card" half of the horizon sentence on its own, independent of the 3D-technology question. Real, small, immediately valuable. |
| **B1 — 3D visor for existing `geometry` DTO (recommended next, not now)** | Honest on the data side (§2: 5 families, zero new KNOW, `_geometry_from_spec` untouched) but **not honest to Buy today on the rendering side** — no 3D infrastructure exists, Three.js/r3f/meshes are explicitly forbidden, and CSS-3D-only rendering of a disk/cylinder requires a genuine rendering-fidelity decision (polygon-approximated curves) this investigation has no evidence to make responsibly. Recommend a **short, dedicated follow-up investigation** scoped exactly to "what renders a box+disk in 3D without Three.js/r3f, at what fidelity, at what cost" before any 3D IC — not bundled into B1− or decided here. |
| **B2 — Frame-part envelope KNOW** | **Rejected, freshly re-verified.** `iflight_xl7_v4_7in`'s `body_length_mm`/`body_width_mm` (202×202mm, seeded in the immediately-prior Geometry-for-all B1 cycle) is real, sourced L×W — but confirmed live this session (§2) that it still has **no accompanying height on any seed row**, and lives under a deliberately distinct property-key name specifically so it does **not** trigger `_geometry_from_spec`'s box path. No new source appeared since G B1 that changes this. B2 stays rejected exactly as the prior investigation concluded — this report does not reopen Geometry-for-all, only re-confirms its finding still holds. |

**Explicitly rejected, no new evidence for any of them:** CAD/STEP import, inferred joints/pose from `mounted_on` edges, a motor cylinder from `stator_height_mm`+`diameter_mm` (re-confirmed still two different physical references, per the Glyph B1 report's own §E, unchanged), `"cabe"` from overlapping 3D solids, and `localStorage` x/y as any kind of spatial truth.

---

## 5. Contingency sketch (B1−, since lean ≠ B0 — not an IC)

```text
InfiniteCanvas: add `selectedId: string | null` state (useState, client-only)
SpatialCard: onClick (grip or body, not the drag handles) -> onSelect(node.id)
             className gains `sb-card--selected` when node.id === selectedId
             (or: a simple scrollIntoView + outline — exact UX is IC's call)

No DTO change. No projector change. No writer/Continuity change (locked
stance 6 — this is visor-only). Tests: a vitest unit for the selection
state transition (click sets/clears), no Python test needed (nothing
server-side changes).
```

**This sketch is illustrative only** — Cursor sizes the exact interaction (persistent highlight vs. momentary scroll, multi-select or single) in a real IC.

---

## 6. Later rungs (named, not bought)

```text
cards + edges (SHIPPED)
  → click-inspect (B1−, THIS report's recommended next Buy)
  → 3D solids at declared scale for {box, disk}-ready families
      (B1, gated on its OWN short rendering-technology investigation —
       no Three.js/r3f/meshes per this IC's own lock; needs a decision
       this report does not make)
  → pose: place solids at a real position/orientation
      (still B0 DEFERRED per the earlier pose-B1+ investigation — no
       reference-frame convention exists anywhere in the system; nothing
       found this cycle changes that)
  → "cabe" / fit vs. that placed situation
      (fit stub QUEUED — DO NOT IMPLEMENT, explicitly not un-queued here)
```

Drag remains layout overlay at every rung above, including a future 3D one — re-affirmed, not re-argued.

---

## 7. Explicit non-goals honored

No code changed — `git status --short -- src/ ui/ tests/` is empty for this cycle. No Three.js/r3f/mesh library referenced as anything other than a named-and-rejected-for-now option. No envelope invented — `_geometry_from_spec` was read, not modified, and every "no glyph" case above was re-verified live against the current seed/schema, not assumed from a prior report's memory. No motor cylinder recommended. No pose/`"cabe"` IC proposed — both explicitly named as later, unbought rungs, with the fit stub confirmed still `QUEUED — DO NOT IMPLEMENT` (read, not touched). No Here3/Pixhawk identity unfreeze — sensors' `mounted_on="esc"` was read as an existing fact, not a reason to add dims. No `parent_key` reinterpreted as a 3D edge — Locked Stance 4 honored, not revisited beyond confirming it's still orthogonal to `mounted_on`.
