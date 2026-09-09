# Implementation Report — Rooster Included plates B2 (HD Cam + Rear VTX text)

**IC:** [implementation_contract_geometry_rooster_included_plates_b2.md](implementation_contract_geometry_rooster_included_plates_b2.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2508

---

## Re-fetch confirmation (live, 2026-09-09)

Re-fetched `https://armattanquads.com/products/rooster-1` live before editing anything. The page's own **Carbon Fiber** Included list states, verbatim: `"1x 1.5mm HD Cam plate"` and `"1x 2mm Rear VTX plates (Standard and TBS)"` — exact match to the IC's expected quotes. Its **Specification** table states `"Max Stack Height" — "22mm"` — exact match. **No plate or airframe L×W/body-dimension string appears anywhere on the page** (confirmed by reading both the full Specification table and the full Included section) — the STOP condition in §1 was not triggered; proceeded with the seed exactly as locked.

## Files changed

- `library/frames/_datos.json` — `armattan_rooster_5in` only (confirmed via `git diff`, no other SKU line touched). Appended two `plates[]` entries after the existing four, **same order locked in §3.1**, no `material` on either new row (matching the existing Top/front/rear pattern): `{"label": "HD Cam plate", "thickness_mm": 1.5}`, `{"label": "Rear VTX plates (Standard and TBS)", "thickness_mm": 2}` — one Included line, one `PlateSeed`, never split. Added root-level `"max_stack_height_mm": 22`. Extended `source_note` with the new quotes, explicitly re-stating "still no L×W" and naming what remains unseeded (nylon standoffs, bolt/nut counts, LiPo strap, camera foam, 28.5mm camera mount, 30.5mm stack mount).
- `src/jarvis/knowledge/library.py` — added `FrameSpec.max_stack_height_mm: float | None = None`, parsed in `_frame_from_raw` exactly like `body_length_mm`/`body_width_mm` (`float(data["max_stack_height_mm"]) if data.get(...) is not None else None`). Docstring states explicitly this is a distinct physical fact from `height_mm`/`body_*`/standoff `height_mm` — never aliased/merged with any of them.
- `src/jarvis/core/catalog_bind.py` — `bind_frame_from_catalog` projects `properties["max_stack_height_mm"] = PropertyValue(value=22, unit="mm", confidence=0.9, source="declared")` when `spec.max_stack_height_mm is not None` — same conditional pattern as `body_length_mm`/`body_width_mm` immediately above it, root-only, never enters `_frame_completeness` (untouched, confirmed via `git diff` — empty). No plate-projection code changed: `frame_part_specs_from_catalog`'s existing `for index, plate in enumerate(spec.plates)` loop already walks every curated entry generically, so the two new rows automatically become `frame_plate_5`/`frame_plate_6` with zero code change (`FRAME_PLATE_MAX_SIBLINGS = 8` guard, 6 ≤ 8, untouched).
- `tests/test_geometry_rooster_included_plates_b2.py` (**new**) — T1–T6 per the IC's own table.
- `tests/test_frame_parts_graph_v1.py` — see "Existing-test updates" below.
- `tests/test_idle_frame_rebind_b2.py` — see "Existing-test updates" below.

## Behavior changed

- `default_library.get_frame("armattan_rooster_5in").plates` now has 6 entries; the first four are byte-identical to before (confirmed T1); `max_stack_height_mm == 22.0` (confirmed T2), every other frame SKU (`tbs_source_one_v5_5in`, `tbs_source_one_v5_1_7in_dc`, `iflight_xl7_v4_7in`) still `None` (confirmed T2).
- `frame_part_specs_from_catalog("armattan_rooster_5in")` now yields 9 part children total (was 7): `frame_arm`, `frame_plate`..`frame_plate_6`, `frame_cage`, `frame_standoff` — `frame_plate_5` labeled "HD Cam plate" (1.5mm), `frame_plate_6` labeled "Rear VTX plates (Standard and TBS)" (2mm), both `parent_key="frame"` (confirmed T3).
- `bind_frame_from_catalog("armattan_rooster_5in")`'s root `properties` now includes `max_stack_height_mm` (22, unit `"mm"`) and still has **no** `height_mm`/`length_mm`/`width_mm`/`body_length_mm`/`body_width_mm` key (confirmed T4).
- `_geometry_from_spec` on the bound Rooster root, and on a synthetic spec carrying **only** `max_stack_height_mm`, both still return `None` — `_geometry_from_spec` itself was not edited (confirmed via `git diff`, zero lines changed); it only ever reads `length_mm`/`width_mm`/`height_mm`/`diameter_mm`/`diameter_in`, none of which `max_stack_height_mm` is or feeds (confirmed T5/T6).
- Live demo path (per the IC's own intent section, confirmed by reading `refresh_component_from_catalog`'s docstring and code): a plain "actualiza frame desde catálogo" **refresh** reaches `bind_frame_from_catalog(sku, base=spec)` and would therefore pick up the new `max_stack_height_mm` root property, but — by the refresh writer's own explicit contract ("this writer only touches `components[component_key]` — a frame refresh never reaches into sibling `frame_plate`/... entries") — does **not** create `frame_plate_5`/`frame_plate_6`. Those only appear via a full catalog **re-pick** (`frame_part_specs_from_catalog` + `upsert_frame_part`, the existing IDLE frame-rebind path) — confirmed by inspection, matching the IC's own smoke instructions exactly (re-pick, not refresh-only).

## Existing-test updates (as required by §4 — reported, not silently weakened)

- `tests/test_frame_parts_graph_v1.py::test_frame_part_specs_from_catalog_armattan_has_arm_four_plates_cage_standoff` **renamed** to `test_frame_part_specs_from_catalog_armattan_has_arm_six_plates_cage_standoff` (the old name would lie about the count) — assertion set extended from 7 to 9 keys (added `frame_plate_5`/`frame_plate_6`), plus new assertions on their `label`/`thickness_mm` values; every pre-existing assertion (arm/plate 1-4/cage/standoff material+thickness, `parent_key`/`component_type` on every part) is unchanged.
- `tests/test_idle_frame_rebind_b2.py::test_rebind_to_tbs_clears_stale_armattan_children` — the "before rebind" sorted `frame_*` key-list assertion extended from 7 to 9 entries (`frame_plate_5`/`frame_plate_6` inserted in their correct alphabetical position before `frame_standoff`); docstring updated from "4 curated plate siblings" to "6 curated plate siblings, per Rooster Included plates B2." The test's actual subject (rebind to TBS clears every stale Armattan child) is unaffected — the assertion **after** rebind (TBS's own 3-plate list) was not touched.
- `tests/test_geometry_for_all_b1.py` — **not touched**, confirmed still green as-is (T5 no-body-footprint, T5b standoff-no-height, T7's own stop-at-`frame_plate_4` assertion all still pass unmodified, since that file tests different frame rows / different assertions than plate count on Armattan specifically).
- N3 (TBS equal-thickness siblings, `test_plate_multiplicity_never_merges_equal_thickness_siblings`) — untouched, still green (operates on `tbs_source_one_v5_5in`, unaffected by this Buy).

## Tests

- `python -m pytest -q tests/test_geometry_rooster_included_plates_b2.py tests/test_frame_parts_graph_v1.py tests/test_idle_frame_rebind_b2.py tests/test_geometry_for_all_b1.py` → **68 passed** (6 new + all pre-existing frame-parts/rebind/geometry-for-all tests, including the one renamed test).
- `python -m pytest -q` (full suite) → **2514 passed**, 0 failed (baseline 2508 + 6 new).
- `git diff --stat -- ui/ src/jarvis/core/engineering_readiness.py` confirms `engineering_readiness.py` has **zero** changes; `ui/` shows only unrelated prior-cycle diffs — this IC touched neither.
- `git diff library/frames/_datos.json` confirms only the `armattan_rooster_5in` row changed — no other SKU (TBS/iFlight) touched.
- No version bump (`pyproject.toml` still `0.3.8`).

## Non-goals honored

- No L×W/box: `_geometry_from_spec` has zero diff; T5/T6 are direct regression proofs that neither the bound Rooster root nor a synthetic `max_stack_height_mm`-only spec ever produces a `geometry` key.
- `max_stack_height_mm` never aliased to `height_mm`/`body_*`/standoff `height_mm` — confirmed by construction (it is its own field, its own `PropertyValue` key, read by nothing else) and by T4's explicit assertion that none of those other keys appear.
- The existing four `plates[]` entries were not reordered — confirmed T1 (`plates[0..3]` byte-identical to before).
- "Rear VTX plates (Standard and TBS)" was seeded as **one** `PlateSeed`, not split into two — confirmed T3 (`frame_plate_6` alone carries that full label).
- No nylon standoffs, bolt counts, LiPo strap, camera foam, 28.5mm camera mount, or 30.5mm stack mount seeded anywhere — confirmed by reading the final JSON row; only two new plate entries and one new scalar were added.
- `_frame_completeness`, Structure PASS, `BLOCK_TO_COMPONENTS`, `KIT_TO_COMPONENTS` all untouched — confirmed via `git diff`, empty for `engineering_readiness.py` and for the `BLOCK_TO_COMPONENTS`/`KIT_TO_COMPONENTS` dict bodies in `system_architecture_catalog.py` (that file's only diff present is from the prior, already-closed kit-template cycle).
- No other frame SKU edited; no version bump; no kit key added; no `vtx`/camera/`prop_adapter` component key introduced anywhere.

## Remaining risks / notes for review

- None identified beyond what the IC itself already flagged as future work (nylon/bolts/camera-mount/stack-mount figures remain deliberately unseeded, per lock).
