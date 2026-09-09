# Implementation Report — Motor `height_mm` 31.7 cited B1 (EMAX only, no cylinder)

**IC:** [implementation_contract_geometry_motor_height_cited_b1.md](implementation_contract_geometry_motor_height_cited_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2473

---

## Files changed

- `library/motores/_datos.json` — **§3.2**: added `"height_mm": 31.7` to `emax_rs2205s_2300` only. Rewrote that row's `source_note` clause: it previously said the page's Motor Height 31.7mm was **NOT seeded**; it now says it **is** seeded as `height_mm` (cited "Motor Height", shaft-inclusive per investigation report §C, explicitly **not** comparable to SunnySky's "Body Length"), while keeping the 15mm extended prop shaft figure as still not seeded. No other row touched — `sunnysky_r2205_2500`, `sunnysky_r2305_2500`, and `emax_rs2205_2300` have no `height_mm` key at all; `sunnysky_r2205_2500`'s own note (already correctly stating Body Length 18mm is NOT seeded) was left as-is, since the IC only asked to rewrite the EMAX clause.
- `src/jarvis/knowledge/library.py` — **§3.1**: added `MotorSpec.height_mm: float | None = None`, parsed in `_motor_from_raw` the same way as the other optional mm fields (`float(data["height_mm"]) if data.get("height_mm") is not None else None`). Updated the class's geometry-axis docstring to describe `height_mm` as optional, SKU-scoped, sourced only where a page's own dimension is unambiguous and cited verbatim — explicitly not comparable across manufacturers and explicitly not a glyph/cylinder input. Removed the now-stale sentence claiming "overall axial height/length is deliberately NOT modeled" (replaced by the new, more precise field-level docstring) since that blanket claim is no longer true for this one SKU.
- `src/jarvis/core/catalog_bind.py` — **§3.3**: extended `bind_motor_from_catalog`'s existing dim-projection loop's key tuple from `("stator_diameter_mm", "stator_height_mm", "diameter_mm", "shaft_diameter_mm")` to also include `"height_mm"`, using the exact same `PropertyValue(..., unit="mm", confidence=0.9, source="declared")` construction already used for the other dims — no new code path, no `MotorSuggestion` TypedDict change (the loop reads `motor_spec` looked up from the library, not the suggestion dict).
- `tests/test_geometry_motor_height_cited_b1.py` (**new**) — T1–T7 per the IC's own table.

## Behavior changed

- `default_library.get_motor("emax_rs2205s_2300").height_mm == 31.7`; every other motor's `height_mm` is `None` (verified directly for `sunnysky_r2205_2500`, `sunnysky_r2305_2500` — the live demo's bound SKU — and the sibling `emax_rs2205_2300`).
- `bind_motor_from_catalog` now projects `properties["height_mm"] = PropertyValue(31.7, unit="mm", source="declared")` when binding `emax_rs2205s_2300`; binding any other motor (checked for SunnySky R2205) produces no `height_mm` key at all.
- A motors `ComponentSpec` with `diameter_mm` + `height_mm` (no length/width) still resolves to `{"shape": "disk", "diameter_mm": ...}` via `_geometry_from_spec` — confirmed by T7 as an explicit regression check; `_geometry_from_spec` itself required **no** edit, since it already only builds a box from a full L×W×H triple and never reads `height_mm`/`stator_height_mm` for shape selection. `height_mm` appears as an ordinary text field (`"height_mm"` → `"31.7 mm"`) via the existing, unmodified `_fields` property loop.
- No CSS 3D / `solidCopies` behavior changed — the disk stays a flat, single-face solid; `scene3dScale`'s disk `z` extent is still hardcoded to `0` and was not touched.
- Live demo (`autonomía-de-10min`, bound to `sunnysky_r2305_2500`) is unaffected: that SKU still has no `height_mm`, no `diameter_mm`, and thus no `geometry`/motor solid — confirmed via T3 and by inspection (no `workspace/` file touched, `git status --short -- workspace/` empty).

## Tests

- `python -m pytest -q tests/test_geometry_motor_height_cited_b1.py` → **7 passed** (T1–T7).
- `python -m pytest -q` (full suite) → **2480 passed**, 0 failed (baseline 2473 + 7 new). No pre-existing test (including the motor-catalog/library/electrical-compatibility files that exercise `MotorSpec`) was modified or weakened — confirmed via `git diff --stat` showing an empty diff for all of them.
- `cd ui/spatial-board && npm test -- --run` → **38 passed** across 5 files (unchanged from before this cycle — this IC touched no `ui/` file).
- `npm run typecheck` → clean.
- `git status --short -- ui/` shows only the prior (Motor visor copies B1) cycle's changes, none new from this one — the IC's own "ui/ empty diff" requirement is satisfied for this cycle's own edits.

## Non-goals honored

- `height_mm` seeded on **exactly one** SKU (`emax_rs2205s_2300`) — confirmed by T2/T3/T4 asserting `None` on every other motor, including the sibling `emax_rs2205_2300` and the live demo's `sunnysky_r2305_2500`.
- SunnySky Body Length 18mm still not seeded — `sunnysky_r2205_2500`'s JSON row and `MotorSpec` both remain without any `height_mm`/`body_length_mm` key; its `source_note` already correctly stated this and was left untouched.
- 15mm extended prop shaft still not seeded — no such key added anywhere; the EMAX row's rewritten `source_note` explicitly says this figure "remains NOT seeded."
- No cylinder: `_geometry_from_spec` was not edited at all (confirmed via `git diff` — zero lines changed in that function); T7 is a direct regression proof that `diameter_mm` + `height_mm` together still yield `disk`, never a box or any new shape.
- `Solid3D.tsx`/`scene3dScale.ts` disk faces/`z` untouched — confirmed via `git diff --stat -- ui/`, empty for this cycle.
- Fit stub not un-queued; no version bump (`pyproject.toml` still `0.3.8`).
- No live `workspace/` mutation from tests — the new test file builds its own synthetic `ProjectState`/`ComponentSpec` fixtures (T7) and reads only from `default_library` (T1–T6), never touching `workspace/`.

## Remaining risks / notes for review

- None identified beyond what the IC itself already flagged as future work (the 15mm shaft figure and SunnySky Body Length remain deliberately unseeded, per lock).
