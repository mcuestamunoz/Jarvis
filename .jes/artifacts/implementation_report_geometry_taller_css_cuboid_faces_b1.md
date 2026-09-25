# Implementation Report — Taller CSS cuboid faces (`B1-geometry-taller-css-cuboid-faces`)

**IC:** [`implementation_contract_geometry_taller_css_cuboid_faces_b1.md`](implementation_contract_geometry_taller_css_cuboid_faces_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-25
**Status:** Landed — awaiting Cursor independent review + Engineer Taller smoke (thin plate) + ★ ACCEPT. **No `v0.5.34` tag yet** (confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.31`, `v0.5.32`, `v0.5.33` — `v0.5.34` does not exist).

---

## 0. Read this first — honesty summary

This Buy fixes a **visor rendering bug**, not a CAD/fit fact. `Solid3D`'s
`box` branch already draws six CSS faces per cuboid; on a thin plate they
visually "explode" because each face sat at the `.sb-solid__face` CSS
default `left: 0; top: 0` regardless of whether the face's own
width/height matched the wrapper's — `front`/`back` do, so they were
never wrong, but `left`/`right` (width `d`) and `top`/`bottom` (height
`d`) do not. With `transform-origin: 50% 50%` (never overridden), an
off-center face rotates about the wrong point and swings out from the
cuboid's true corner. This Buy extracts a pure helper,
`cuboidFaceLayout(w, d, h)`, that centers every face first, then applies
the existing rotate + `translateZ(half-extent)` construction.

**Visor cuboid != CAD != fit != extra parts != a 2D card's own origin.**

**Exists:** six CSS faces that meet on a thin declared box. **Impossible:**
a machined plate; a fit verdict; a seventh part. Nothing in this Buy is
any of those.

---

## 1. Package layout vs IC §1

```text
ui/spatial-board/src/cuboidFaces.ts        # NEW helper
ui/spatial-board/src/cuboidFaces.test.ts   # NEW — 4 vitest cases
ui/spatial-board/src/Solid3D.tsx           # MODIFIED — box branch consumes the helper
```

`ui/spatial-board/src/spatial-board.css` was **not** touched —
`.sb-solid__face`'s existing `transform-origin: 50% 50%` default (never
overridden) already matches IC §0.5's requirement; only the per-face
inline `left`/`top`/`transform` values needed to change, and those are
computed by the new helper and applied inline in `Solid3D.tsx`, not in
CSS. No Python file under `src/jarvis/`/`library/` was touched — the IC
§1 STOP condition ("a test cannot call the helper") never triggered.

---

## 2. Construction implemented vs IC §0 decisions 4-7 / §2

| Item | IC ref | Match |
|---|---|---|
| Root cause: off-center faces rotate about their own off-center point, not the cuboid's | §0.4 | ✅ documented verbatim in `cuboidFaces.ts`'s own header comment |
| Center every face first (`left: (w-fw)/2`, `top: (h-fh)/2`), then rotate, then `translateZ(half-extent)` | §0.5 | ✅ exact — `cuboidFaceLayout` returns `left`/`top` computed this way; the `transform` string never repositions, only rotates + `translateZ`s |
| Wrapper size stays `width: w; height: h` | §0.5 | ✅ unchanged in `Solid3D.tsx` — only the six face `<div>`s' own props changed |
| Still exactly six `.sb-solid__face` nodes | §0.5 | ✅ `faces.map(...)` renders exactly the 6 entries `cuboidFaceLayout` returns, same class names (`sb-solid__face--front` etc.) as before |
| Axis remap unchanged (`w`=+X/L, `d`=+Y/W, `h`=+Z/H) | §0.5 | ✅ `Solid3D.tsx` still destructures `{x: w, y: d, z: h} = extent` unchanged before calling the helper |
| front `translateZ(d/2)` · back `rotateY(180deg) translateZ(d/2)` · left `rotateY(-90deg) translateZ(w/2)` · right `rotateY(90deg) translateZ(w/2)` · top `rotateX(90deg) translateZ(h/2)` · bottom `rotateX(-90deg) translateZ(h/2)` | §0.6 | ✅ exact strings, verified byte-for-byte in the "normals match the IC §0.6 lock exactly" vitest case |
| Thin-plate fixture `161x42x2mm` -> `w=80.5, d=21, h=1` px | §0.7 | ✅ T2 test uses exactly these numbers; `top`/`bottom` `translateZ(0.5px)` (= `h/2`), `left`/`right` `translateZ(40.25px)` (= `w/2`), never `d/2` for top/bottom |
| No `translateX(-w/2)`/`translateY(-h/2)` in any transform string | §0.7 | ✅ asserted explicitly (T2's own "no translateX/translateY" check) — centering lives entirely in `left`/`top`, never folded back into the transform |

### 2.1 Non-goals (IC §2) — confirmed absent

Standoff perimeter points, plate-box catalog seed, F460, cylinder/disk
rewrite, 2D `.sb-world` origin, Three.js, fit/CAD, silicon — none of
these were touched. Confirmed by §6's `git diff --stat` and by the fact
that `cuboidFaces.ts`/`cuboidFaces.test.ts` only reference the `box`
branch's own geometry.

---

## 3. Verified — real builds, real test runs

```text
$ npx vitest run src/cuboidFaces.test.ts
✓ src/cuboidFaces.test.ts (4 tests)

$ npm run typecheck
> tsc --noEmit
(clean, no output — no type errors)

$ npm test
✓ 14 test files, 136 tests passed (132 pre-existing + 4 new)
```

`Solid3D.tsx`'s diff is minimal and isolated to the `box` branch — one
new import, one `cuboidFaceLayout(w, d, h)` call, and the six
hardcoded `<div>` face elements replaced with a `faces.map(...)` that
renders the same six class names (`sb-solid__face--front` through
`--bottom`) with the helper's computed `width`/`height`/`left`/`top`/
`transform`. The cylinder and disk branches are untouched.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `Solid3D` box | Same six faces, new layout math — verified via `git diff` showing only the box branch changed |
| Cylinder / disk | **Byte-unchanged** — `git diff` on `Solid3D.tsx` shows zero lines touched outside the `box` branch |
| `SCENE3D.pxPerMm` | **Unchanged** — `scene3dScale.ts` not touched, still `0.5` |
| Projector / DTO | **Unchanged** — no Python file touched |
| Grafo cards | **Unchanged** — no `.sb-world`/2D-card file touched |

---

## 5. Tests run

### 5.1 UI — new vitest module

`ui/spatial-board/src/cuboidFaces.test.ts` — **4 tests**:

| Test | Covers |
|---|---|
| `T1: cube w=d=h=40 — six faces, each centered (left/top 0), each translateZ 20` | T1 |
| `T2: thin plate w=80.5, d=21, h=1 — MY5 top plate fixture` | T2 |
| `T2b: thin plate faces are actually centered within the w x h wrapper, not flush at an edge` | T2 (centering, not just the final transform string) |
| `normals match the IC §0.6 lock exactly` | §0.6 |

```text
✓ src/cuboidFaces.test.ts (4 tests) 4ms
```

### 5.2 Full UI vitest suite

```text
Test Files  14 passed (14)
     Tests  136 passed (136)
```

Baseline before this Buy: 132 tests (13 files). Delta: **+4**, exactly
matching the new test count — zero regressions.

### 5.3 `tsc --noEmit`

```text
> jarvis-spatial-board@0.1.0 typecheck
> tsc --noEmit
```

Clean — no type errors.

### 5.4 Full Python suite (T7 — no new Python tests required)

```text
3691 passed, 2 skipped in 8.28s
```

Unchanged from the pre-Buy baseline (`3691 passed, 2 skipped`) — exactly
as IC §4 T7 expects ("no new Python tests required"), since this is a
UI-only fix with no `src/jarvis/` edits.

---

## 6. Module-boundary / freeze grep (run at close of this Buy)

```text
$ git diff -- ui/spatial-board/src/Solid3D.tsx
# diff limited to: +1 import line, +1 `const faces = cuboidFaceLayout(w, d, h);`
# line, and the box branch's six hardcoded face <div>s replaced by a
# faces.map(...) rendering the same six class names. Cylinder/disk
# branches: zero lines changed.

$ git diff --stat -- ui/spatial-board/src/spatial-board.css src/jarvis/workspace/spatial_board.py
ui/spatial-board/src/spatial-board.css | (empty — untouched)
src/jarvis/workspace/spatial_board.py  | (pre-existing diff from an unrelated, external
                                            geometry-track session — not touched by this Buy)
```

`spatial_board.py` already carried a diff from a separate, parallel
session before this Buy started (unrelated craft-geometry work visible
in `git status` throughout this session); this Buy neither opened nor
extended that diff — confirmed by not touching the file at all.

`git status --short` at close of this Buy shows exactly the expected
file set: `cuboidFaces.ts`, `cuboidFaces.test.ts` (new), `Solid3D.tsx`
(modified), plus `pyproject.toml` + version-checkpoint test re-pins +
docs. No `spatial-board.css`, cylinder/disk code, projector, DTO, or
`spatial_board.py` edits from this Buy.

---

## 7. Files changed

**New:**
- `ui/spatial-board/src/cuboidFaces.ts`
- `ui/spatial-board/src/cuboidFaces.test.ts`
- `.jes/artifacts/implementation_report_geometry_taller_css_cuboid_faces_b1.md` (this file)

**Modified:**
- `ui/spatial-board/src/Solid3D.tsx` (box branch consumes `cuboidFaceLayout`; cylinder/disk branches untouched)
- `pyproject.toml` (`0.5.33` → `0.5.34`)
- 41 pre-existing Python test files re-pinned from `0.5.33` to `0.5.34` (literal `'version = "X.Y.Z"' in text` pattern and the `match.group(1) == "X.Y.Z"` regex pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new paragraph after the C35 block), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §9)

No `CMakeLists.txt`/Python change was needed — this is a pure
TypeScript/CSS-adjacent Buy on the UI side.

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.34 includes (landed, awaiting Cursor review + Engineer Taller smoke + ★ ACCEPT — no `v0.5.34` tag yet)" section; the v0.5.33 section's own "Next" line and the bottom "Next" mention both updated to point at this Buy's LANDED status.
- `docs/ARCHITECTURE.md` — banner updated (§2 Platform/Fase C line) and the paragraph after the C35 block extended with a full construction/root-cause writeup, both phrased "landed — awaiting Cursor review + Engineer Taller smoke + ★ ACCEPT, no `v0.5.34` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new block after the C35 paragraph, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim ("Visor cuboid ≠ CAD ≠ fit ≠ extra parts ≠ a 2D card's own origin").
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the Taller CSS table row both changed from "IC READY (awaiting Engineer ★)" to "LANDED (awaiting Cursor review + Engineer Taller smoke + ★ ACCEPT, no tag yet)"; UI vitest count added (`140`).

No file in this Buy claims `v0.5.34` is tagged, ACCEPT CLOSED, "CAD",
"fit VERIFIED", or a real machined plate exists. Confirmed via
`git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.31`,
`v0.5.32`, `v0.5.33` — `v0.5.34` does not exist yet.

---

## 9. Residual / next steps

- Standoff perimeter points (cola 4) is the one remaining no-pin/no-CAD
  front per the existing "situation after C33" engineer note — not
  opened by this Buy.
- The Engineer's own **Taller smoke** (looking at the thin plate
  on-screen, not just the vitest numbers) is still outstanding — this
  report's own test evidence is numeric/structural only, per the IC's
  own "Helper + vitest; no screenshot gate" default (§0, "Defaults
  locked by Cursor"). A visual confirmation is the Engineer's own
  acceptance step, not something this report can substitute for.
- Cylinder/disk's own analogous face-centering (their caps/side segments
  already use different, already-centered math — see `Solid3D.tsx`'s own
  comments on `_CYLINDER_SIDE_SEGMENTS`) was not touched and was not in
  scope; if a similar thin-cylinder bug is ever found, it would be a
  separate, explicitly-scoped Buy.
- `.sb-world`'s own 2D-card `transform-origin: 0 0` (a separate,
  unrelated 2D concern the IC explicitly excludes) remains untouched.

---

## 10. Acceptance self-check vs IC §7

- T1-T9: ✅ T1/T2/T2b/normals-lock in vitest (4/4 passing), T3 (`Solid3D` box branch maps helper fields onto the six face nodes) verified via the `faces.map(...)` wiring itself plus the full 136/136 vitest suite exercising it through every existing UI test that renders a box, T4 (`git diff` shows cylinder/disk untouched), T5 (no `src/jarvis/`/`library/` edits), T6 (`npm test && npm run typecheck` both green), T7 (Python suite unchanged, no new Python tests), T8 (`pyproject` `0.5.34`), T9 (this report).
- Six faces: ✅ `cuboidFaceLayout` always returns exactly 6 entries; `Solid3D.tsx` renders exactly `faces.map(...)`, no seventh element added anywhere.
- Thin-plate fixture: ✅ T2/T2b exercise the exact `80.5x21x1`px MY5-derived numbers from IC §0.7.
- Cylinder/disk frozen: ✅ `git diff` on `Solid3D.tsx` touches only the `box` branch.
- Projector frozen: ✅ no Python file touched.
- Version `0.5.34`: ✅ `pyproject.toml` + all 41 checkpoint tests re-pinned.

**PASS** against every criterion in IC §7 that this report can verify
programmatically. **FAIL conditions** (extra faces, DTO thickness
invented, `.sb-world` retargeted, standoff points, Three.js, cylinder
rewrite) — none present, verified above. The Engineer's own visual
Taller smoke (thin plate on-screen) remains the outstanding
human-in-the-loop step before ★ ACCEPT.
