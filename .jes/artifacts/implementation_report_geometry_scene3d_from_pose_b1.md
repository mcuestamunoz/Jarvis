# Implementation Report — Scene3D-from-pose B1 (visor reads `declared_box_pose`)

**IC:** [implementation_contract_geometry_scene3d_from_pose_b1.md](implementation_contract_geometry_scene3d_from_pose_b1.md)
**Implementer:** Claude Code
**Review:** [implementation_review_geometry_scene3d_from_pose_b1.md](implementation_review_geometry_scene3d_from_pose_b1.md) — **PASS WITH NOTES**
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · Python suite 2456 · UI suite 25 passed

---

## Files changed

- `src/jarvis/workspace/spatial_board.py` — **§3.1**: new module-level `_declared_box_pose_dto(spec, components) -> dict | None`, the ONE gate for whether a declared pose is honest to surface at all — requires the origin to still exist in `components` AND `_geometry_from_spec(origin)["shape"] == "box"` (the exact same rule the writer itself already enforces at declare-time, never a second/looser rule). Returns a camelCase dict (`originKey`, and only the axis keys — `xMm`/`yMm`/`zMm` — that are not `None`), never a fallback origin. `_fields`'s previous, looser `if pose and pose.origin_key in components:` gate is replaced by a call to this same helper, so the text fields ("origen pose"/"ejes pose"/"Δx mm"/…) and the machine DTO can never disagree about whether a pose is shown. `place()` now computes this dto and passes it to `_emit(...)` as `declared_box_pose=...`; `_emit`'s signature gained that keyword and sets `node["declaredBoxPose"] = dto` only when not `None` — mirroring the existing `geometry`/`mounted_on` conditional-key pattern exactly, no new pattern invented.
- `ui/spatial-board/src/types.ts` — **§3.2**: `SpatialNode.declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number }` added, documented as the same "honest absence" gate as `mountedOn`.
- `ui/spatial-board/src/scene3dScale.ts` — **§3.3 (extent helper)**: new `solidWrapperPx(geometry, pxPerMm?) -> {width, height}`. Box: `{width: extent.x, height: extent.z}` (CSS width = declared length, CSS height = declared height — the depth/+Y axis lives only in `translateZ`, never in the wrapper's own box, per `Solid3D`'s existing face code). Disk: `{width: extent.x, height: extent.x}` — explicitly never `extent.z` (always 0 for a disk, not its on-screen height).
- `ui/spatial-board/src/scene3dLayout.ts` — **§3.3 (placement algorithm)**: fixed the stale docstring on `layoutSolidsRow` (no longer claims "pose stays B0 DEFERRED"; now says this function itself still doesn't read `declaredBoxPose` and is reused as the base slot-fallback). Added `SolidLayout` type and `layoutSolidsFromPose(items, gapPx, pxPerMm?)`: computes row slots via the unchanged `layoutSolidsRow` first (every item always gets a slot, so a broken/missing pose never makes a solid vanish), then for each item with a `declaredBoxPose` whose `originKey` resolves to another **box-shaped** item in the same list, computes a center-to-center offset; otherwise the item keeps its row slot with `originY = originZ = 0`. Never recurses into the origin's own pose (single-level only, per the locked non-goal). Axis remap and center correction implemented exactly per the IC's locked formula (see "Behavior changed" below for the worked arithmetic).
- `ui/spatial-board/src/Solid3D.tsx` — **§3.4**: added `originY`/`originZ` props (default `0`) to both the box and disk branches; both wrappers' `transform` changed from `translateX(${originX}px)` to `translate3d(${originX}px, ${originY}px, ${originZ}px)`. Face construction inside each solid is untouched — the remap lives entirely in what values `layoutSolidsFromPose` computes, not in how faces are drawn relative to their own wrapper.
- `ui/spatial-board/src/Scene3D.tsx` — **§3.5**: replaced the `layoutSolidsRow(...)` call + `originById: Map<id, originX>` with `layoutSolidsFromPose(solids.map(n => ({id, geometry: n.geometry, declaredBoxPose: n.declaredBoxPose})), GAP_PX)` and a `Map<id, SolidLayout>`; each `<Solid3D>` now receives `originX`/`originY`/`originZ` from that lookup (all defaulting to `0` if absent). `layoutSolidsRow` is no longer called directly at this call site — only internally by `layoutSolidsFromPose`.
- `ui/spatial-board/src/scene3dScale.test.ts` — two new cases under a new `describe("solidWrapperPx", ...)` block (box, disk).
- `ui/spatial-board/src/scene3dLayout.test.ts` — seven new cases under a new `describe("layoutSolidsFromPose", ...)` block: unposed fallback; posed box-origin with all three axes (worked arithmetic below); omitted axes counting as 0; disk origin falling back; missing origin key falling back; empty list; input-order preservation.
- `tests/test_geometry_scene3d_from_pose_b1.py` (**new**) — P1–P6, covering the projector's `declaredBoxPose` DTO gate: single axis, all three axes (DTO + text both), disk origin (both omitted), vanished origin key (both omitted), no pose at all (no key), and omitted axes never appearing as `0`.

## Behavior changed

- `project_spatial_nodes` output now includes a `declaredBoxPose` key on a node whenever `ComponentSpec.declared_box_pose` is set AND its origin still resolves to a box — omitted entirely otherwise (disk origin, vanished origin, or no pose). This is the same gate the existing "origen pose" text field now uses too — previously that text field used a looser `origin_key in components` check that did **not** verify the origin was still a box; that gap is now closed as a side effect of sharing one helper (a disk-origin or now-shapeless-origin pose will no longer show stale "origen pose" text either).
- The CSS 3D visor (`Scene3D`) now positions a posed solid relative to its origin's row slot instead of always laying every solid out in a flat row. Verified arithmetic (fc = box 44×84×12mm, esc = box 50×21.6×12mm, pose `{originKey: "fc", xMm: 5, yMm: 3, zMm: -2}`, `gapPx=24`, `pxPerMm=0.5`):
  - fc's own row slot: `originX = 0` (first in row).
  - esc's fallback row slot (used only if unposed): fc footprint `max(22, 42) = 42`; `42 + 24 = 66`.
  - `originWrap(fc) = {width: 22, height: 6}`, `childWrap(esc) = {width: 25, height: 6}`.
  - `originCenterX = 0 + 22/2 = 11`, `originCenterY = 6/2 = 3`.
  - `originX = 11 + mmToPx(5)=2.5 - 25/2=12.5 = 1`
  - `originY = 3 + mmToPx(-2)=-1 - 6/2=3 = -1` (declared `+Z` → CSS Y)
  - `originZ = mmToPx(3) = 1.5` (declared `+Y` → CSS Z/depth, no half-width correction — the depth axis is already symmetric about 0 in `Solid3D`'s existing face code)
  - This matches the IC's own worked example exactly (`originX = 11 + 2.5 - 12.5 = 1`).
- An unposed solid, a solid whose pose origin resolves to a disk, or a solid whose pose origin key is absent from the current node list all fall back to `{originX: <row slot>, originY: 0, originZ: 0}` — identical to pre-IC behavior for that solid.
- Omitted `xMm`/`yMm`/`zMm` are treated as `0` for display purposes only (`?? 0` in the layout math) — never written back as a schema default; the DTO itself only carries the axis keys that were actually set (verified by P1/P6).
- No pose chain / composition: `layoutSolidsFromPose` never looks at the origin's own `declaredBoxPose` — confirmed by construction (the algorithm only reads `origin.geometry`, never `origin.declaredBoxPose`) and by the "preserves input order" / disk-origin-fallback tests exercising a case where recursion would have mattered if implemented.

## Tests

- `python -m pytest -q` → **2462 passed**, 0 failed (baseline 2456 + 6 new, all in `tests/test_geometry_scene3d_from_pose_b1.py`). Ran the new file plus the two related pre-existing pose test files together first (33 passed), then the full suite.
- `cd ui/spatial-board && npm test -- --run` → **31 passed** across 5 files (baseline 22 + 9 new: 2 `solidWrapperPx` cases in `scene3dScale.test.ts` [now 6 tests total] + 7 `layoutSolidsFromPose` cases in `scene3dLayout.test.ts` [now 10 tests total]). All 5 test files green.
- `npm run typecheck` → clean (`tsc --noEmit`, no errors).
- `npm run build` → clean production build (47 modules, no errors/warnings).
- `git status --short` reviewed: only the files listed above changed under `src/jarvis/` and `ui/spatial-board/src/`; `component_writers.py`, `declared_box_pose_declare_assist.py`, `orchestrator.py`, `library/`, `package.json`, `boardSelection.ts`, and any fit/airframe stub are byte-identical to before this cycle (confirmed via targeted `git diff --stat`). `pyproject.toml` version unchanged at `0.3.8`.

## Non-goals honored

- No pose chain/composition implemented — `layoutSolidsFromPose` is explicitly single-level, per the locked cycle-detection-gap finding from the parent investigation; no cycle guard was added anywhere (still absent, still out of scope).
- No new geometry invented — `solidWrapperPx` and the placement formula only ever read `length_mm`/`width_mm`/`height_mm`/`diameter_mm` already present in the existing `geometry` DTO; no motor cylinder, no plate footprint, no axis convention beyond the already-locked declared frame (`L→+X, W→+Y, H→+Z`).
- No fit/"cabe"/assembly-verified claim added — a posed solid's on-screen position is a rendering of a *declared* number, never a computed collision/clearance check.
- `Solid3D`'s face construction (the six-face cuboid, the single flat disk face) is untouched — only the wrapper's outer `transform` gained two more translate axes.
- No card `x`/`y`/`mountedOn` read by any 3D file — `layoutSolidsFromPose` and `Scene3D` only ever consume `geometry` and `declaredBoxPose` from the node DTOs, confirmed by the function signatures themselves (no such fields are even accepted as input).
- No test weakened; all additions are new files/new `describe` blocks, no existing test's assertions changed.

## Remaining risks / notes for review

- `_fields`'s pose-text gate now silently omits "origen pose" text for a pose whose origin has become a disk or vanished (previously it only omitted for a vanished origin, not a disk-origin case — since the box-check wasn't there before). This is a strictly more honest behavior change than before, but flagged in case any existing manual/demo walkthrough script expected the old (looser) text-only behavior for a disk-origin pose. No live demo project currently has any `declared_box_pose` set (confirmed empty), so this cannot have silently changed anything in `workspace/`.
- `layoutSolidsFromPose`'s disk-origin/missing-origin fallback intentionally reuses each item's **own** row slot from the same `layoutSolidsRow` pass computed over the *full* list — a solid later in the list still gets a slot based on all solids' footprints in list order, exactly matching pre-existing `layoutSolidsRow` semantics for that solid.
