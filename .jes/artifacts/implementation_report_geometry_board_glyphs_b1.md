# Implementation Report — Board Glyphs (box + disk, representar-complete only) — visualizar B1

**IC:** [implementation_contract_geometry_board_glyphs_b1.md](implementation_contract_geometry_board_glyphs_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · suite 2336

---

## Files changed

- `src/jarvis/workspace/spatial_board.py`:
  - New pure helper `_geometry_from_spec(spec) -> dict | None`. Shape is chosen by which `PropertyValue` keys are actually present, not a hardcoded per-family table (N3): a full `length_mm`+`width_mm`+`height_mm` triple always wins and returns `{"shape": "box", ...}`; otherwise a single diameter path (`diameter_mm`, else `diameter_in * 25.4` for the glyph's mm-equivalent scale only) returns `{"shape": "disk", "diameter_mm": ...}`; anything else (thickness-only, no dims, a diameter alongside an unrelated height like Motor's `stator_height_mm`) returns `None` — no stitching, no invented dimension, ever (N7).
  - `_emit`/`place` extended with an optional `geometry` argument; `place` computes it via `_geometry_from_spec` and passes it through; `place_slot` never passes one (N10 — slots never carry geometry, since it calls `_emit` without the argument, which defaults to `None`).
  - The `geometry` key is added to the node dict **only when not `None`** — omitted entirely otherwise, per N4/the IC's "prefer omit" instruction. `id`/`title`/`declaredName`/`kind`/`fields`/`x`/`y`/`width`/`height` are all unchanged in shape and meaning — `width`/`height` remain exactly the card's pixel-layout defaults (N8), confirmed by a dedicated regression test.
  - Module docstring extended with one paragraph naming the B1 capability and re-stating the `width`/`height` vs `geometry` distinction, so a future reader doesn't have to re-derive it from the code.
- `tests/test_spatial_board_projector.py` — 8 new tests: box from a full triple, disk from `diameter_mm` (with a `stator_height_mm` also present, proving no stitching), disk from `diameter_in` with the mm conversion verified **and** the text field confirmed to still say `"5 in"`, absence when only thickness is declared, absence when no dimension properties exist at all, absence on `kind: "slot"` nodes (in a mixed column where a sibling real component *does* get geometry), box winning over a diameter present on the same spec, and a direct proof that card pixel `width`/`height` are untouched by and unequal to the geometry payload's own mm values.
- `ui/spatial-board/src/types.ts` — new `SpatialGeometry` union type (`box` | `disk`, matching the projector's exact two shapes) and an optional `geometry?: SpatialGeometry` field on `SpatialNode`. No existing field renamed, widened, or removed.
- `ui/spatial-board/src/constants.ts` — new `GLYPH = { pxPerMm: 0.5, maxPx: 120 }` constant (N: "prefer a constant `PX_PER_MM`... simpler than viewport-relative scaling for B1" — locked and documented here as the chosen approach, not viewport-relative). `pxPerMm: 0.5` puts a 200mm edge at 100 CSS px, matching the IC's own worked example; `maxPx: 120` caps any single very large declared dimension from overwhelming a card.
- `ui/spatial-board/src/SpatialGlyph.tsx` (new file) — a small, purely presentational component that draws a `box` (rectangle sized `length_mm × width_mm`, with a `length×width×height mm` caption so the declared `height_mm` is still visibly honored per N1 even though it isn't a 2D draw dimension) or a `disk` (circle sized from `diameter_mm`, with a `Ø … mm` caption, N5's "optional caption" taken). Both shapes use the fixed `GLYPH.pxPerMm` scale from `constants.ts` — the same factor for every glyph on screen, so relative proportions between different components' glyphs stay correct. Purely decorative shape divs are `aria-hidden`; the mm caption text is not, since it's real declared information.
- `ui/spatial-board/src/SpatialCard.tsx` — two-line addition: imports `SpatialGlyph` and renders `{node.geometry ? <SpatialGlyph geometry={node.geometry} /> : null}` inside the existing `sb-card__body`, between the declared-name paragraph and the property `dl`. No change to drag/resize handles, gestures, or any existing rendering path — a glyph is not a separate movable node (N: "No new drag semantics").
- `ui/spatial-board/src/spatial-board.css` — one small, additive block (`.sb-glyph`, `.sb-glyph__box`, `.sb-glyph__disk`, `.sb-glyph__caption`) matching the existing card's dark-theme/muted-caption conventions (`#888` for captions, same as `.sb-card__fields dt`). No existing rule touched.

## Behavior changed

- Any **component/part** node whose declared properties include a full box triple or a usable diameter now carries a `geometry` field in the projector's JSON output, and the Board visually draws a proportionally-scaled outline for it (box or circle) with a small mm caption, above the existing text property list.
- Concretely, with the catalog rows already shipped by prior Geometry ICs: Battery (`lipo_4s_1500mah`, `lipo_4s_5000mah`, `lipo_6s_6000mah`), ESC (`hobbywing_xrotor_40a_6s`), and Flight Controller (`pixhawk_4` only) now get `box` glyphs; Motor (`emax_rs2205s_2300`, `sunnysky_r2205_2500`, via `diameter_mm` only — never combined with `stator_height_mm`) and every Propeller row (`diameter_in`, converted to mm for the glyph only) get `disk` glyphs. Every other identity in every family (unsourced batteries/motors, every other FC model, every frame part, sensors) is byte-identical to before this IC — no glyph, no `geometry` key, unchanged card.
- `kind: "slot"` nodes never carry geometry, confirmed both by the code path (`place_slot` never passes the argument) and by a dedicated regression test placing a real geometry-bearing component in the same lane as slot siblings.
- Card `x`/`y`/`width`/`height` (pixel layout, drag/resize state) are untouched in both meaning and value — confirmed by a dedicated test asserting the pixel `height` is not equal to (and unrelated to) the geometry payload's own `height_mm`.
- No engineering state, catalog seed, or Structure/Control/Sensors claim logic was touched — this is a pure, additive display feature over data every prior Geometry IC already sourced and shipped.

## Tests

Python: executed `python -m pytest -q` → **2344 passed**, 0 failed (baseline 2336 + 8 new). Ran `tests/test_spatial_board_projector.py` alone first (21 passed — 13 pre-existing + 8 new) before the full run. No existing test was weakened.

Frontend: this repo already runs `tsc --noEmit` (`npm run typecheck`) and `vitest run` (`npm test`) as its existing scripts — both executed and both green (`typecheck`: no errors; `test`: 4/4 passed, unchanged — no new JS/TS unit test was added, per the IC's own "do not invent Jest/Vite test infra" instruction, since the projector-side tests already exercise every shape/absence rule and the UI layer is a thin, type-checked renderer of whatever the projector emits). Also ran `npm run build` as an additional smoke — production build succeeds with no errors, confirming the new component and type additions compile cleanly end-to-end.

## Non-goals honored

No pose, `mounted_on`, fit, clearance, or CAD/FEA claim anywhere. No `cylinder` or `bar` renderer built (the vocabulary stays exactly `{box, disk}`, per the investigation's own finding that nothing else has real data behind it). No frame plate/arm/root glyph (thickness-only and wheelbase-only specs correctly return `None` from `_geometry_from_spec`). No dimension invented for any plate/arm/frame/unsourced row. No catalog JSON, `FLIGHT_CONTROLLER_DIMENSIONS` table value, ERF/Control evidence, or Sensors BOM honesty tail touched — confirmed via `git diff --stat` showing zero changes to `library/**`, `aerial.py`, `engineering_readiness.py`, or `project_closure.py`. No second geometric source of truth — `_geometry_from_spec` reads only `spec.properties`, the same `ProjectState`-sourced data `_fields()` already reads; nothing new is stored, cached, or derived outside the existing projection. No version bump.

## Design decisions worth recording (not obvious from the diff alone)

- **`PX_PER_MM` is a fixed constant (`GLYPH.pxPerMm = 0.5`), not viewport/zoom-relative**, per the IC's own explicit preference for B1 simplicity. A 200mm edge renders at 100 CSS px; a `maxPx: 120` cap prevents one oversized declared dimension from dominating a card. This is a presentation choice only, easily revisited in a later Buy without touching the projector or its tests.
- **The box glyph's on-screen rectangle uses `length_mm`×`width_mm` only** (N1 — the 2D footprint), but `height_mm` is not silently dropped: it's included in both the JSON payload (so any future consumer has it) and the glyph's own caption text, satisfying "carried in payload for honesty/tooltip, not as a fake 3D solid."
- **Shape priority when both a box triple and a diameter are present on the same spec: box wins**, and the `geometry` object never contains both a `diameter_mm` and a box triple at once — verified by a dedicated test using a synthetic FC-like spec with both present.
