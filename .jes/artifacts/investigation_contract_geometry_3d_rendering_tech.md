# Investigation Contract — Board 3D rendering technology (box + disk at declared scale)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `ACCEPT` of click-inspect B1− + `procede` for this investigation  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_3d_rendering_tech.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **B1** (`procede` 2026-09-08) · IC READY FOR CLAUDE  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — ★ horizon (3D-at-scale is the next named rung)
- [investigation_report_geometry_3d_placement_horizon.md](investigation_report_geometry_3d_placement_horizon.md) — lean **B1− now / B1 3D gated on this investigation**
- [investigation_review_geometry_3d_placement_horizon.md](investigation_review_geometry_3d_placement_horizon.md) — **PASS WITH NOTES** (N2, N4)
- Click-inspect B1− **CLOSED** @ suite **2429** + Engineer smoke **ACCEPT** — [IC](implementation_contract_geometry_board_click_inspect_b1minus.md) · [smoke](engineer_smoke_geometry_board_click_inspect_b1minus.md)
- Glyphs B1 CLOSED @ **2344** — `geometry: {box, disk}` · 2D `SpatialGlyph.tsx`
- Fit stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**
- Pose B1+ — **B0 DEFERRED**

**Type:** Investigation only — **how** to render existing `{box, disk}` as 3D solids at **declared** scale on today’s Board.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** new KNOW / envelopes / motor cylinder / frame L×W. **Not** pose. **Not** `"cabe"`. **Not** CAD/STEP/FEA. **Not** Conversation Engine. **Not** a second geometric SoT.

**Checkpoint base:** package **`0.3.8`** · suite **2429**

**Single objective (locked):**

> Decide the **minimum honest rendering path** for 3D solids of the existing projector `geometry` DTO (`box` = rectangular prism from L×W×H; `disk` = **flat disk at declared diameter, no invented axial height**), at a scale that can honestly claim “declared millimetres,” reusing click-inspect (`selectedId` / `onSelect`) — without treating layout drag as pose.

**Product sentence this must enable (after a later Buy, not this investigation):**

```text
Veo el volumen declarado en 3D a escala; click en el sólido selecciona la card de hoy.
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy before any 3D IC.

**Do not implement. Do not bump version. Do not add Three.js / r3f / CSS-3D / canvas / WebGL in this cycle.** Naming a library as a **candidate** is required; installing one is forbidden until ★ + IC.

---

## 0. Role split

```text
Engineer  → ACCEPT B1−; procede this contract
Cursor    → this contract; review; 3D IC only after ★
Claude    → investigation_report_geometry_3d_rendering_tech.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists

The 3D-horizon investigation already settled **data honesty**:

- 5/14 live demo nodes have full `geometry` (motors, propellers, esc, battery, FC).
- 9 stay cards-only (frame parts / sensors) — B2 envelope KNOW **rejected**.
- Motor cylinder from `diameter_mm` + `stator_height_mm` **still forbidden**.
- Visor pipeline is projector JSON only.
- 2D glyph scale is **capped** (`min(mm × 0.5, 120px)`) — cannot be reused as “true declared scale.”
- Click-inspect now **ships**: one `selectedId`, outline on the 2D card.

What it **explicitly did not decide:** *what draws a box and a disk in 3D*. Prior cycle forbade adding Three.js/r3f **as implementation**. CSS 3D cannot honestly draw a curved disk without a fidelity decision. That decision is **this** investigation.

Do **not** re-litigate glyph fuel, B2, pose, or `"cabe"` except to re-cite the parent (file:line if you re-open a file).

---

## 2. Locked stances (inherited)

1. Board remains a **projection of `ProjectState`**. No mesh store as model of record.  
2. 3D uses the **same** `_geometry_from_spec` `{box, disk}`. Absence = no solid.  
3. Disk 3D = **flat disk / zero axial thickness**. Inventing ε height is the same stitch Glyph B1 forbade (review N4).  
4. Click a solid → **reuse** `boardSelection.ts` / `onSelect(id)`. Do not invent a second selection model. Cards stay the inspect surface (fields already always visible).  
5. `mounted_on` edges remain **declared relation**, not fastener pose.  
6. `localStorage` `{x,y,width,height}` stays **layout**, not pose.  
7. Pose / `"cabe"` / CAD / Here3 unfreeze — **out**.  
8. Fit stub stays QUEUED.

---

## 3. Baseline to inventory (cite live tree)

Re-verify the **visor rendering stack**, not the DTO matrix (parent already did that).

| Surface | Check |
|---|---|
| `ui/spatial-board/package.json` | Deps today = `react` + `react-dom` only. Confirm still no three / r3f / cannon / etc. |
| `InfiniteCanvas.tsx` + `spatial-board.css` | 2D world: absolute DOM cards + SVG edges. How a 3D layer would sit (beside / replace glyphs / second pane) — **recommend, don’t build**. |
| `SpatialGlyph.tsx` + `constants.ts` `GLYPH` | Capped 2D scale; implication for a 3D millimetre camera. |
| `boardSelection.ts` | Pick target for a future solid `onSelect`. |
| CSS 3D (`transform-style`, `perspective`, `rotateX`) | What a box can honestly be vs what a **disk** can honestly be without a mesh. |
| Canvas 2D / SVG extrusion hacks | Same honesty bar: no fake cylinder claimed as sourced height. |

Live demo (do **not** re-run a new KNOW campaign): 5 solids-capable nodes vs 9 cards-only — cite parent report §2 unless the tree changed.

---

## 4. Questions the report must answer

### 1 — What “3D at declared scale” means on this visor

Can a view claim millimetre-true proportions if it does **not** reuse `min(mm × 0.5, 120)`? What scale/camera model is the minimum (e.g. 1 world unit = 1 mm, user zoom)? Prop Ø127 mm vs ESC 50 mm must stay proportional.

### 2 — Box vs disk fidelity

- Box: rectangular prism from real L×W×H — which stacks can draw it honestly (CSS 3D six faces, WebGL box, etc.)?  
- Disk: **no height**. What is an honest drawing (flat circle in a plane, tessellated disk with thickness = 0, etc.) vs a dishonest “thin cylinder”?  
If a candidate approximates a circle as an N-gon, say so; do not call it a sourced cylinder.

### 3 — Technology candidates (this cycle **may** lift the Three.js forbid)

Compare at least:

| Candidate | Must say |
|---|---|
| **A — CSS 3D / DOM only** | Box honesty; disk honesty; camera/orbit cost; keep 2D cards |
| **B — Canvas/SVG faux-3D** | Same |
| **C — WebGL via Three.js or r3f** (or one named equivalent) | New dependency cost; still visor-only; no second SoT |
| **D — Defer 3D** | 2D glyphs + click-inspect already shipped |

Prior cycle’s “no Three.js” was **an implementation lock for that IC**, not a product forever-ban. This report **must** recommend whether to keep it or lift it, with evidence.

### 4 — How it sits next to today’s Board

Keep cards + edges? Glyph inside card vs solids in a 3D pane vs both? Click solid must call the **existing** `onSelect`. Do not require collapsing card fields.

### 5 — Cost vs first Buy

Smallest slice that still matches the product sentence. Frame-part / no-`geometry` nodes stay 2D cards.

### 6 — Later rungs (name only)

Pose → `"cabe"`. Do **not** un-QUEUE the fit stub. Do **not** Buy orbit-as-pose.

---

## 5. Minimum Buy options (must include)

| Option | Intent |
|---|---|
| **B0 — Defer** | No 3D renderer yet; 2D glyphs + click-inspect are enough |
| **B1 — CSS 3D / DOM-only solids** | Only if the report can honestly draw **both** box and disk without invented height and without calling an N-gon a cylinder |
| **B1+ — WebGL visor (named lib)** | Three.js or r3f (or equivalent) as **presentation** of projector `geometry`; lift the prior implementation forbid **only** if this is the lean |
| **B1− — 2D glyphs only** (status quo after click-inspect) | Same practical outcome as B0; name if you distinguish “never 3D on this visor” vs “not this quarter” |

Reject: CAD/STEP as SoT, motor cylinder stitch, ε-thickness disks, plate L×W invention, pose from `mounted_on` or card drag, `"cabe"` from overlapping solids, a second mesh file cache.

---

## 6. Report format (mandatory sections)

1. **Executive recommendation** — one lean (B0 / B1 / B1+ / B1−) + one sentence.  
2. **Visor rendering stack as-is** — deps, DOM+SVG, glyph cap, selection helper (file:line).  
3. **Fidelity** — box vs disk; what “declared scale” requires.  
4. **Candidate comparison** — A/B/C/D; costs; honesty risks.  
5. **Buy options** — including whether to lift Three.js/r3f.  
6. **Contingency sketch** (if lean ≠ B0) — where a 3D layer would mount, how `onSelect` is reused; **not** an IC.  
7. **Later rungs** — pose / cabe named, not bought.  
8. **Explicit non-goals honored.**

---

## 7. Done criteria (investigation)

- [ ] Rendering stack cited; no new deps added  
- [ ] Disk axial height still **not** invented; motor cylinder still forbidden  
- [ ] Glyph cap not rubber-stamped as 3D scale  
- [ ] Clear lean; B0 allowed  
- [ ] Click-inspect reuse named  
- [ ] No code; no 3D IC; no pose/fit IC  

---

## 8. Stop conditions

Stop and ask before: recommending STEP/mesh as SoT, inventing disk height, bundling pose/`cabe`, or writing an Implementation Contract in the report.
