# Investigation Report — Board 3D Rendering Technology (box + disk at declared scale)

**IC:** [investigation_contract_geometry_3d_rendering_tech.md](investigation_contract_geometry_3d_rendering_tech.md)
**Investigator:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2429 (unchanged — investigation only, no code/tests touched, no dependency added)
**Review:** [investigation_review_geometry_3d_rendering_tech.md](investigation_review_geometry_3d_rendering_tech.md) — PASS WITH NOTES  
**Buy:** Engineer ★ **B1** (`procede` 2026-09-08) → [implementation_contract_geometry_board_css3d_solids_b1.md](implementation_contract_geometry_board_css3d_solids_b1.md) READY FOR CLAUDE

---

## 1. Executive recommendation

**B1 — CSS 3D / DOM-only solids.** Both shapes the projector already emits can be rendered with **zero new dependencies and zero honesty compromise**: a box is a standard 6-face CSS 3D cuboid (`transform-style: preserve-3d` + `translateZ`, a well-established technique), and a disk is a genuinely flat plane (the same `border-radius: 50%` circle the 2D glyph already draws, given a 3D orientation via `rotateX`) — **not** a squashed cylinder, so there is no "N-gon claimed as a sourced height" problem to solve in the first place, because a flat `<div>` has no depth to invent. Critically, a CSS 3D object **is a real DOM node**, so it can call the exact same `onSelect(id)` from `boardSelection.ts` with the same `onMouseDown` pattern `SpatialCard` already uses — no raycasting adapter, no second selection model. Keep the prior "no Three.js" stance **for now**, not permanently: the one thing WebGL genuinely buys over CSS 3D — a real orbit camera and clean depth-sorting at scale — is not yet needed for 5 solids, and is named below as the explicit reversal criterion.

---

## 2. Visor rendering stack as-is (re-verified, file:line)

- **Dependencies today**: `ui/spatial-board/package.json:13-16` — exactly `react` + `react-dom`. Zero 3D library, zero canvas/WebGL wrapper, zero physics/geometry package. Confirmed unchanged since the parent 3D-horizon investigation.
- **2D world**: `InfiniteCanvas.tsx` renders `.sb-world` (a single `transform: css`-panned/zoomed `<div>`) containing `<DeclaredMountEdges>` (one `<svg>` with `<line>` elements) and one `<SpatialCard>` per node, each an absolutely-positioned `<article>` (`left/top/width/height` from `node.x/y/width/height`, confirmed by direct re-read this session). There is no existing 3D container, no `perspective`, no `transform-style: preserve-3d` anywhere in `spatial-board.css` today — a 3D layer would be a **genuinely new** sibling structure, not an extension of the existing 2D absolute-positioning scheme (mixing 2D absolute layout and 3D transforms on the same elements is not viable — a 3D pane needs its own container).
- **Glyph scale is capped, not linear**: `constants.ts:32-34`'s `GLYPH = {pxPerMm: 0.5, maxPx: 120}`, consumed by `SpatialGlyph.tsx`'s `scaled(mm) = Math.min(mm * 0.5, 120)`. Confirmed (re-derived, not assumed): a 127mm propeller and a 264mm-or-larger object would render at the **same** 120px cap, breaking proportionality above 240mm. This cap exists specifically so a glyph fits inside a small, fixed-size 2D card body — a constraint that **does not exist** for a dedicated 3D pane (nothing forces a 3D scene's camera into a ~96px box). **A 3D view therefore must not reuse this function** — it needs its own, genuinely linear `mm * k` factor (no cap), with the *camera's* zoom (reusing the exact zoom/pan pattern `useCanvasTransform.ts` already implements for the 2D board) providing the "see everything" control instead of clamping individual objects. This answers Governing Question 1: **declared-scale proportionality between a 127mm prop and a 50mm ESC requires dropping the cap, not adjusting it.**
- **Selection pick target**: `boardSelection.ts`'s `nextSelectedId`/`reconcileSelection` (added by the immediately-prior Click-inspect B1− IC, confirmed present and unmodified) — pure, React-free, id-based. `InfiniteCanvas.tsx`'s `onSelect` callback (`setSelectedId((cur) => nextSelectedId(cur, {type: "select", id}))`) is the **single** existing entry point a 3D layer must call — confirmed by re-reading the current file: `SpatialCard` already receives `onSelect` as a prop and fires it from a plain `onMouseDown`, no framework-specific event system involved.
- **CSS 3D primitives, confirmed by their well-established browser-standard behavior (not prototyped — investigation only, no file written)**: `transform-style: preserve-3d` + per-face `translateZ`/`rotateY` is the standard technique for a cuboid (six flat `<div>` faces positioned to their real relative offsets); `border-radius: 50%` produces a mathematically circular element regardless of 2D or 3D context — orienting that same element with `rotateX` places a flat circular plane into a 3D scene without adding any depth. Both are ordinary CSS properties already supported by the browsers this Board already targets (no feature-detection gap beyond what `transform-style: preserve-3d`/`perspective` already require, which is universal in current evergreen browsers).

---

## 3. Fidelity — box vs disk, and what "declared scale" requires

- **Box**: `_geometry_from_spec` (`spatial_board.py:227-276`, re-read in full, unchanged) only ever emits a `box` when the full `length_mm`+`width_mm`+`height_mm` triple exists. A CSS 3D cuboid drawn from those three real numbers, at a single linear mm→unit factor, is **fully honest** — every face is a real, sourced rectangle, nothing is invented, nothing is approximated beyond ordinary anti-aliasing.
- **Disk**: the DTO (same function, `diameter_mm` branch) carries **exactly one number** — there is no height key in the payload at all, for any disk node, ever. This means the honesty guarantee is enforced **before** any rendering technology is even chosen: a 3D consumer has nothing to misuse into a fake height even if it wanted to. The only honest 3D disk is a **zero-thickness flat plane** — which is not a compromise or an approximation of a "real" cylinder, it is the literal, correct shape for "I know the diameter and nothing else." Both a CSS `border-radius:50%` `<div>` and a WebGL `CircleGeometry` primitive are this same shape — a flat plane — with no volume and no invented axial extent. **Do not build a "thin cylinder"** (a `CylinderGeometry`/extruded shape with a near-zero height constant) in either technology — that is a different primitive that implies a side wall and two end-caps where only one exists, exactly the "ε-thickness" trap the IC's own reject list names.
- **Every curved shape rendered by any technology (CSS border-radius, SVG `<circle>`, WebGL `CircleGeometry`) is internally polygon-approximated by the rendering engine** — this is universal and was already true of the *2D* disk glyph shipped in Glyph B1 (an SVG/CSS circle is not "more honest" than a WebGL one at the pixel level). This is **not** the honesty question this investigation is about; the honesty question is exclusively "does the shape carry an invented dimension," and the answer is no for either candidate as long as the disk primitive stays genuinely flat.
- **Declared scale**: requires (1) one linear mm→unit factor with no per-object cap (§2), and (2) a camera/viewport zoom that lets the *user* control how much of the scene is visible, rather than the renderer silently shrinking individual objects to fit. Both CSS 3D and WebGL can provide this; neither requires a new dependency for the *scale* question specifically — this is purely a "drop the `Math.min` cap" decision, independent of which technology draws the shapes.

---

## 4. Candidate comparison

| Candidate | Box honesty | Disk honesty | Click-reuse cost | New dependency | Camera/orbit capability |
|---|---|---|---|---|---|
| **A — CSS 3D / DOM-only** | ✅ full, real 6-face cuboid | ✅ full, genuinely flat plane | **None** — a CSS-3D object is a real DOM node; the exact same `onMouseDown={() => onSelect(node.id)}` pattern `SpatialCard` already uses applies unchanged | **None** | Weak/hand-rolled — no built-in orbit camera; a drag-to-rotate scene needs custom `rotateX`/`rotateY` state (real but well-trodden, no new library required); depth-sorting across many overlapping 3D-transformed elements is a known weaker area of the CSS 3D model at higher object counts (not a concern at today's 5 solids) |
| **B — Canvas/SVG faux-3D** | ✅ possible (hand-projected isometric/perspective math) | ✅ possible, same caveat | **Real new cost** — canvas has no native per-shape DOM events; picking a clicked solid requires hand-rolled hit-testing (hover/click ray vs. your own drawn shape's bounds), a new mechanism `boardSelection.ts` doesn't already give you | **None** | Same hand-rolled burden as A, plus the projection math itself, for **no honesty or cost advantage over A** — dominated by candidate A for this specific need |
| **C — WebGL via Three.js/r3f (or an equivalent)** | ✅ full — `BoxGeometry(l, w, h)` from real dims | ✅ full — `CircleGeometry(radius)` is a standard, genuinely flat, zero-thickness primitive (not a hack) | **Real new cost** — a canvas is one DOM element with no native per-mesh events; reusing `onSelect` requires a raycast-based glue layer (`Raycaster` → intersected mesh → mesh↔`node.id` lookup → call the same `onSelect`) — a real, modest amount of new code, but it stays a thin adapter onto the *same* selection function, not a second model | **Real** — three.js (and r3f/drei if used for camera controls) is a genuine bundle-size and maintenance-surface addition, the exact thing the prior IC's "no Three.js" lock was scoped to forbid *as an implementation choice*, not a permanent ban | Strongest — proper orbit/zoom/pan and correct depth-sorting essentially for free (`OrbitControls`), scales cleanly well past today's 5 solids |
| **D — Defer** | n/a | n/a | n/a (click-inspect already ships on 2D cards) | none | n/a — practically identical outcome to keeping 2D glyphs + click-inspect, the status quo since the immediately-prior IC |

**No candidate requires inventing a disk height, stitching motor dims, or approximating a curved side wall as a claimed sourced dimension** — the DTO itself (§3) makes that impossible regardless of which technology is chosen.

---

## 5. Buy options (including the Three.js/r3f question)

| Option | Assessment |
|---|---|
| **B0 — Defer** | Available and honest, but the Engineer has already ★-locked a named 3D horizon and accepted the click-inspect half of it — B0 here would mean declining evidence-backed candidate A's real, low-cost feasibility rather than responding to a blocker. Not recommended, named per the IC's own requirement that B0 stay available. |
| **B1 — CSS 3D / DOM-only solids (recommended)** | Renders exactly the 5 already-`geometry`-bearing families as honest 3D solids, at a genuinely linear declared-mm scale, reusing `onSelect` with zero new glue code and zero new dependencies. Frame-part/no-`geometry` nodes stay exactly as 2D-only cards — nothing about this candidate pressures inventing their dims. **Keep the "no Three.js" stance this cycle** — not because WebGL is dishonest (§4 shows it isn't), but because candidate A already satisfies the product sentence at lower cost, and the one real WebGL advantage (orbit camera, depth-sorting at scale) isn't yet a proven need at 5 objects. |
| **B1+ — WebGL visor (Three.js/r3f named)** | Not rejected on honesty grounds — genuinely viable, and this report is explicitly permitted to lift the prior forbid if evidence supported it. Evidence instead supports deferring the dependency cost until candidate A's real limitations (depth-sorting past a handful of objects, or an actual product need for free-orbit navigation) show up as real pain, not hypothetical scale. **Reversal criterion, named explicitly**: if the solid count grows well past today's 5, or the Engineer wants true free-orbit camera controls rather than a simple rotate-the-scene interaction, revisit C with that concrete evidence. |
| **B1− — 2D glyphs only (status quo)** | Practically identical to B0 for this cycle's purposes — named for completeness per the IC's own table; superseded by the B1 recommendation above given A's feasibility. |

---

## 6. Contingency sketch (lean ≠ B0 — not an IC)

```text
New sibling structure, NOT an extension of .sb-world's 2D absolute layout:

  <div class="sb-scene3d" style={{ perspective: "...", transformStyle: "preserve-3d" }}>
    {nodes.filter(n => n.geometry).map(n => (
      <Solid3D                       // new component, mirrors SpatialGlyph's
        key={n.id}                   // "draw only when geometry present" rule
        geometry={n.geometry}
        selected={n.id === selectedId}
        onSelect={() => onSelect(n.id)}   // SAME callback InfiniteCanvas already
      />                                   // passes to SpatialCard — no second model
    ))}
  </div>

Solid3D:
  box  -> 6 <div> faces, transform-style:preserve-3d, translateZ from real
          length_mm/width_mm/height_mm * a NEW linear (uncapped) mm->unit factor
  disk -> one <div> with border-radius:50%, sized from diameter_mm * the
          same factor, oriented with rotateX — flat, no depth

Scene camera: reuse the rotate-the-whole-scene pattern (a container-level
rotateX/rotateY driven by drag state), not a full orbit-camera library.

Placement next to today's Board: an additional pane/toggle alongside the
existing 2D card grid — cards remain the inspect surface (locked stance 4);
clicking a solid highlights the SAME 2D card via the SAME selectedId this
session's click-inspect IC already ships, with zero new selection state.

Tests (future IC's job to size exactly): a vitest unit for the new mm-per-unit
scale function (pure, no DOM) mirroring boardSelection.test.ts's style; no
Python test needed (no DTO or projector change).
```

**Illustrative only** — a real IC sizes the exact CSS structure, the rotate-drag interaction, and whether box/disk render inside the same `.sb-scene3d` container or two.

---

## 7. Later rungs (named, not bought)

```text
click-inspect (SHIPPED)
  → 3D solids at declared scale (B1, THIS report's recommendation — CSS 3D,
     no new dependency, reusing onSelect)
      → [reversal criterion: WebGL/Three.js if solid count or orbit-camera
         need genuinely grows past what CSS 3D handles well]
  → pose: place solids at a real position/orientation
      (still B0 DEFERRED — no reference-frame convention exists anywhere in
       the system; nothing in this investigation changes that)
  → "cabe" / fit vs. that placed situation
      (fit stub QUEUED — DO NOT IMPLEMENT, not un-queued here)
```

Drag remains layout overlay at every rung, in 2D or 3D — re-affirmed, not re-argued. `mounted_on` edges remain declared-relation indicators only, never fastener pose, in a future 3D scene exactly as on today's 2D board.

---

## 8. Explicit non-goals honored

No code changed and no dependency added — `git status --short` and `ui/spatial-board/package.json` are both confirmed unmodified this cycle. No Three.js/r3f/CSS-3D/canvas/WebGL file was created — every technique described above is cited as a well-established, standard browser/library capability, not prototyped. No disk axial height invented anywhere in this report — §3 argues the opposite, that the DTO structurally prevents it regardless of rendering choice. No motor cylinder revisited beyond re-citing its already-settled rejection. No plate L×W or frame envelope invention proposed — frame-part/no-`geometry` nodes are explicitly named as staying 2D-only under every candidate. No pose or `"cabe"` bought — both named only in §7, with the fit stub confirmed still `QUEUED — DO NOT IMPLEMENT` (read, not touched). No Here3/Pixhawk identity unfreeze — not referenced anywhere in this report's evidence or recommendation. No Implementation Contract was written — §6 is explicitly labeled a contingency sketch, not IC-ready text.
