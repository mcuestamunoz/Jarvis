# Implementation Contract — Geometry assembly Board edges B2 (`mounted_on` visualization)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (this cycle — Engineer ★ queue + start first)  
**Reviewer:** Cursor self-check against this IC + Engineer Board smoke

**Status:** READY FOR IMPLEMENTATION — Engineer ★ Buy (queue natural assembly path; start first)  
**Parents:**
- [investigation_report_geometry_assembly_espacial_b1.md](investigation_report_geometry_assembly_espacial_b1.md) — B2 named follow-on after relation text
- [implementation_contract_geometry_assembly_espacial_b1.md](implementation_contract_geometry_assembly_espacial_b1.md) — CLOSED @ **2364** (relation + `"montado en"` text; edges deferred)
- [implementation_contract_continuity_mounted_on_declare_b1.md](implementation_contract_continuity_mounted_on_declare_b1.md) — CLOSED @ **2380** (IDLE declare)

**Type:** Board **visualization** of already-declared `mounted_on` relations as canvas edges.  
**Not** pose mm. **Not** fit. **Not** auto-layout from mounts. **Not** layout-as-truth.

**Baseline:** package **`0.3.8`** · suite **2380**

**Queue position:** **1 of 3** (assembly espacial visual path)  
**Next queued:** pose B1+ (blocked pending investigation) · fit/compare (blocked pending investigation)

**Output:** `.jes/artifacts/implementation_report_geometry_assembly_board_edges_b2.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B2 Board edges** | YES — first item in natural assembly queue |
| 2 | Authority | Projector exposes machine field; UI draws — UI does **not** parse `"montado en"` text to invent edges |
| 3 | Source | Only `ComponentSpec.mounted_on` already on state |
| 4 | Stale target | Text field may still show key; **no drawable edge** if target node absent |
| 5 | Layout | Card `x`/`y` unchanged by edges; no auto-reposition toward mount target |
| 6 | Honesty | Edges ≠ verified / ensamblado / cabe — presentation only |
| 7 | Pose / fit | **Out** |
| 8 | Version | **No** bump |

---

## 1. You

- Do **not** add pose / orientation / offset fields.
- Do **not** infer mounts from proximity, drag, or BOM.
- Do **not** change `set_component_mounted_on`, Continuity parser, or `parent_key`.
- Do **not** remove the existing `"montado en"` text field (edges **add** visualization).
- Do **not** bump package version.
- Full pytest suite green; run `ui/spatial-board` `npm test` + `npm run typecheck`.
- Write the implementation report when done.

---

## 2. Intent

```text
ComponentSpec.mounted_on (declared)
        ↓
project_spatial_nodes → optional node["mountedOn"] when target is also a projected node
        ↓
Board SVG edges between card anchors (world coords; follow drag overlay)
        ↓
text field "montado en" remains
```

Product sentence:

> “Veo en el Board a qué se declara montado cada componente (línea + texto).”

---

## 3. Locked behavior

### 3.1 Projector (`spatial_board.py`)

When emitting a component/part node:

- If `spec.mounted_on` is truthy **and** that key is among the nodes that will be / have been emitted in this projection (same project graph), set:
  - `node["mountedOn"] = spec.mounted_on` (string key)
- If `mounted_on` is set but target is **not** in the projected node set → **omit** `mountedOn` (no edge DTO). Keep the existing text field `"montado en"` with the stored key (B1 behavior unchanged).
- If `mounted_on` is None → omit both machine field and text field (unchanged).
- Do **not** change `kind`, lane, `x`, `y`, `geometry`, or `parent_key` handling.
- CLI/`main` payload stays `{"nodes": [...]}` — edges are derived client-side from `mountedOn` (no separate top-level edges array required for B2).

### 3.2 UI types + draw

- `SpatialNode` gains optional `mountedOn?: string`.
- New thin layer (e.g. `MountEdges.tsx`) inside `.sb-world`, **under** cards:
  - For each node with `mountedOn`, if a node with `id === mountedOn` exists, draw one straight SVG line between sensible anchors (e.g. source card center → target card center, or mid-bottom → mid-top — pick one and stick to it).
  - Lines use current node rects (including localStorage overlay after drag).
  - No arrowhead claiming direction-as-verified; optional subtle stroke only.
  - **Forbidden** copy on edge: ensamblado, cabe, verificado, fit, correcto.
- Minimap: **optional** omit edges (B2 default: edges only on main canvas — keep minimap simple).

### 3.3 Non-goals (explicit)

No bezier routing engine · no collision avoidance · no edge labels required · no click-to-edit mount · no Continuity changes · no schema field beyond existing `mounted_on` · no version bump

---

## 4. Tests (required)

**Python** — `tests/test_geometry_assembly_board_edges_b2.py` (new):

| # | Case |
|---|---|
| T1 | `mounted_on` set + target present → node has `mountedOn` |
| T2 | `mounted_on` set + target missing → no `mountedOn`; text field still present |
| T3 | no `mounted_on` → no `mountedOn` key |
| T4 | `mountedOn` does not change `x`/`y`/`kind` vs unset twin |
| T5 | Non-regression: `"montado en"` text field still emitted when set |

**UI** — vitest helper (prefer pure function, e.g. `mountEdgeGeometry.ts`):

| # | Case |
|---|---|
| U1 | Two nodes with `mountedOn` → one edge segment with expected endpoints |
| U2 | `mountedOn` to missing id → zero edges |
| U3 | No `mountedOn` → zero edges |

Run: full pytest; `cd ui/spatial-board && npm test && npm run typecheck`.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | emit optional `mountedOn` |
| `ui/spatial-board/src/types.ts` | `mountedOn?: string` |
| `ui/spatial-board/src/mountEdgeGeometry.ts` | pure edge list from nodes |
| `ui/spatial-board/src/MountEdges.tsx` | SVG layer |
| `ui/spatial-board/src/InfiniteCanvas.tsx` | render edges under cards |
| `ui/spatial-board/src/spatial-board.css` | edge stroke |
| `ui/spatial-board/src/mountEdgeGeometry.test.ts` | U1–U3 |
| `tests/test_geometry_assembly_board_edges_b2.py` | T1–T5 |
| `.jes/artifacts/implementation_report_geometry_assembly_board_edges_b2.md` | write |

**Do not change:** `component_writers` · Continuity assist · `action_schema` · glyphs · catalog seeds · package version

---

## 6. Done criteria

- [ ] Drawable edge only when both endpoints projected
- [ ] Text `"montado en"` retained
- [ ] No pose/fit/honesty-theater copy
- [ ] Tests T1–T5 + U1–U3; suites green; counts reported
- [ ] Implementation report written
- [ ] Engineer Board smoke recommended before closing queue item 1

---

## 7. Stop conditions

Stop and ask before: pose fields, fit checks, auto-layout from mounts, parsing field text for edges, or version bump.
