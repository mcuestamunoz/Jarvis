# Investigation Review — Geometry 3D Placement Horizon (first slice)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_3d_placement_horizon.md](investigation_contract_geometry_3d_placement_horizon.md)  
**Report:** [investigation_report_geometry_3d_placement_horizon.md](investigation_report_geometry_3d_placement_horizon.md)  
**Lock:** [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)

## Verdict

**PASS WITH NOTES**

Lean **B1−** (2D click-inspect / selection) is Buy-eligible as an immediate visor-only slice. **B1** (3D solids) is correctly **not** this IC: data fuel exists for 5/14 demo nodes, rendering stack does not. **B2** rejected. **B0** remains available. Engineer ★ picks B1− / B0 / re-scope. **No IC until ★.**

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + B0 named | **Pass** |
| Live glyph/3D-fuel matrix | **Pass** — Cursor re-ran projector |
| Motor cylinder still forbidden | **Pass** |
| Frame envelope KNOW (B2) rejected | **Pass** — `body_*` ≠ `length/width/height` |
| Visor pipeline = projection | **Pass** |
| Click vs always-open card | **Pass** — load-bearing for B1− honesty |
| Glyph scale cap | **Pass** — `min(mm×0.5, 120)` |
| `mounted_on` ≠ pose | **Pass** |
| Later rungs named; fit stub still QUEUED | **Pass** |
| No code / no Three.js Buy | **Pass** — `src/` `ui/` `tests/` clean |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| 14 nodes; 5 with `geometry` | **Confirmed** live `project_spatial_nodes_from_path` |
| motors disk 27.9 · propellers disk 127.0 | **Confirmed** |
| esc 50×21.6×12 · battery 37×35×75 · FC 44×84×12 | **Confirmed** |
| `propellers.mountedOn=motors` · `sensors.mountedOn=esc` | **Confirmed** (post-walk) |
| Frame/parts/sensors `geometry=None` | **Confirmed** (9 nodes) |
| `_geometry_from_spec` reads only `length/width/height` + diameter | **Confirmed** `spatial_board.py:257-276` |
| iFlight seed `body_length_mm`/`body_width_mm` 202 | **Confirmed** `library/frames/_datos.json` — demo is Armattan, so live frame still no body keys |
| `SpatialCard` fields always on; no `onClick`/selection | **Confirmed** full file |
| `scaled = min(mm * 0.5, 120)` | **Confirmed** `SpatialGlyph.tsx:11-12` + `constants.ts:32-35` (cap at 240 mm) |
| Nodes API spawn projector per GET | **Confirmed** `vite-plugin-jarvis-projects.ts:97-117`, match `/nodes` at **143+** (report’s 141-142 is the `/api/projects` list — N3) |
| No `src/` `ui/` `tests/` edits | **Confirmed** `git status` |

---

## Notes for ★

### N1 — B1− is selection, not “abrir la card”

On the 2D Board every card already shows all fields. B1− must not claim the horizon sentence “click abre la card” as if info were hidden. Honest product sentence for B1−:

```text
Puedo seleccionar un nodo; la card correspondiente se destaca.
```

That is still useful (focus on 14 cards; scaffolding for a later 3D pick). If Engineer wants **only** the 3D half, pick **B0** and wait for the rendering-tech investigation — do not stretch B1− into fake 3D.

### N2 — Horizon ≠ Buy 3D now

The lock named a **horizon**. Splitting B1− now / B1 after a **separate** rendering investigation is coherent. Do **not** bundle Three.js/CSS-3D into a B1− IC. Next 3D step = new investigation contract, not a surprise IC.

### N3 — Citation nit

`GET /api/projects/:id/nodes` is `vite-plugin-jarvis-projects.ts` ~143, not 141-142. Does not change the pipeline claim.

### N4 — Disk 3D still has no height

Motors/propellers are 3D-ready only as **flat disk** (or zero-thickness). A “thin cylinder” with invented ε height is the same class of stitch Glyph B1 forbade. Lock that in any future B1 3D IC.

### N5 — Demo vs iFlight body

`body_length_mm` lives on the **iFlight seed**, not on live Armattan demo `frame`. Re-bind would be needed to even *see* those text fields; they still would not glyph.

---

## Agreement

| Report lean | Reviewer |
|---|---|
| B1− now | **Agree** if Engineer wants a visor UX slice |
| B1 3D gated on rendering-tech investigation | **Agree** |
| B2 reject | **Agree** |
| B0 still valid | **Agree** — especially if B1− feels like polish without 3D |

---

## Phase

Engineer ★ **B1− CLOSED** (smoke ACCEPT). Next: [investigation_contract_geometry_3d_rendering_tech.md](investigation_contract_geometry_3d_rendering_tech.md) READY FOR CLAUDE. No 3D IC until that ★.
