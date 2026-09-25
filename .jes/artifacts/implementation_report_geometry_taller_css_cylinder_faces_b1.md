# Implementation Report — Taller CSS cylinder faces (`B1-geometry-taller-css-cylinder-faces`)

**IC:** [`implementation_contract_geometry_taller_css_cylinder_faces_b1.md`](implementation_contract_geometry_taller_css_cylinder_faces_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-25
**Status:** Landed — awaiting Cursor independent review + Engineer Taller smoke (short hub / tall post) + ★ ACCEPT. **No `v0.5.35` tag yet** (confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.32`, `v0.5.33`, `v0.5.34` — `v0.5.35` does not exist). Note: `v0.5.34` (Taller CSS cuboid's own tag) exists **locally** but has not been pushed to origin, per the Engineer's own note at handoff.

---

## 0. Read this first — honesty summary

This Buy fixes the same **class of visor rendering bug** the cuboid Buy
(`v0.5.34`) just shipped, applied to `Solid3D`'s `cylinder` branch. The
cylinder already draws 2 disk-caps + 16 flat side slats; on a short axial
height (a prop hub) or a tall one (a standoff-shaped post) the **caps**
explode because each `D×D` cap sat at the `.sb-solid__disk-face` CSS
default `left: 0; top: 0` — correct only when the wrapper's own height
`H` equals `D`. With `transform-origin: 50% 50%` (never overridden), an
off-center cap rotates about the wrong point and swings off axis. This
Buy extracts a pure helper, `cylinderSolidLayout(diameterPx, heightPx)`,
that centers every cap first, then applies the existing rotate +
`translateZ(H/2)` construction — the same locked pattern the cuboid Buy
already used for its own faces.

**Visor cylinder != CAD != fit != extra parts != round metal != a standoff hole pattern.**

**Exists:** 2 CSS caps + 16 CSS slats that meet on a declared Ø×H.
**Impossible:** a turned standoff; a prop hub from the mill; a fit
verdict; a 17th face. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
ui/spatial-board/src/cylinderFaces.ts        # NEW helper
ui/spatial-board/src/cylinderFaces.test.ts   # NEW — 6 vitest cases
ui/spatial-board/src/Solid3D.tsx             # MODIFIED — cylinder branch consumes the helper
```

`ui/spatial-board/src/cuboidFaces.ts` was **not** touched — confirmed
`git diff --stat` empty. `ui/spatial-board/src/spatial-board.css` was
also not touched — `.sb-solid__disk-face`'s existing
`transform-origin: 50% 50%` default (never overridden) already matches
IC §0.5's requirement; only the per-cap inline `left`/`top`/`transform`
values needed to change, computed by the new helper and applied inline
in `Solid3D.tsx`. No Python file under `src/jarvis/`/`library/` was
touched — the IC §1 STOP condition never triggered.

---

## 2. Construction implemented vs IC §0 decisions 4-7 / §2

| Item | IC ref | Match |
|---|---|---|
| Root cause: off-center caps rotate about their own off-center point, not the cylinder's mid-height | §0.4 | ✅ documented verbatim in `cylinderFaces.ts`'s own header comment |
| Wrapper stays `width: D; height: H` | §0.5 | ✅ unchanged in `Solid3D.tsx` — only the cap/slat `<div>`s' own props changed |
| Caps centered (`left: (D-D)/2 = 0`, `top: (H-D)/2` — negative when `H < D`) | §0.5 | ✅ exact — `cylinderSolidLayout` computes `capTop = (heightPx - diameterPx) / 2` |
| Caps: rotate then `translateZ(H/2)` — top `rotateX(90deg) translateZ(H/2)`, bottom `rotateX(-90deg) translateZ(H/2)` | §0.5/§0.6 | ✅ exact strings, verified byte-for-byte in the "normals match the IC §0.5 lock exactly" vitest case |
| No `translateY`/`translateX` in any cap or slat transform | §0.5 | ✅ asserted explicitly in T2 and the normals-lock test — centering lives entirely in `left`/`top`, never folded back into the transform |
| Slats: N=16 frozen, `chord = 2·(D/2)·sin(π/16)`, `left: (D-chord)/2`, `top: 0`, `transform: rotateY(i·22.5deg) translateZ(D/2)` | §0.5 | ✅ exact — same formula the pre-existing code already used, relocated unchanged into the helper |
| Axis: arguments are `diameterPx, heightPx`, no cuboid `w/d/h` remap inside the helper | §0.6 | ✅ `cylinderSolidLayout(diameterPx: number, heightPx: number)` — no shared types/names with `cuboidFaces.ts` |
| Thin-cylinder fixture Ø130.72×6.8mm -> px `D=65.36, H=3.4`, cap `top=-30.98`, `translateZ(1.7)` | §0.7 | ✅ T2 test uses exactly these numbers |
| Tall-post fixture Ø6×30mm -> px `D=3, H=15`, cap `top=6`, `translateZ(7.5)` | §0.7 | ✅ T2b test uses exactly these numbers |
| Cube-like `D=H=40` -> cap `top=0`, `translateZ(20)` | §0.7 | ✅ T1 test |

### 2.1 Non-goals (IC §2) — confirmed absent

Standoff perimeter points, plate-box catalog seed, F460, cuboid recut,
disk rewrite, 2D `.sb-world` origin, Three.js, fit/CAD, silicon, D2 docs
— none of these were touched. Confirmed by §6's `git diff --stat` and by
the fact that `cylinderFaces.ts`/`cylinderFaces.test.ts` only reference
the `cylinder` branch's own geometry.

---

## 3. Verified — real builds, real test runs

```text
$ npx vitest run src/cylinderFaces.test.ts
✓ src/cylinderFaces.test.ts (6 tests)

$ npm run typecheck
> tsc --noEmit
(clean, no output — no type errors)

$ npm test
✓ 15 test files, 142 tests passed (136 pre-existing + 6 new)
```

`Solid3D.tsx`'s diff is minimal and isolated to the `cylinder` branch and
its own module-level doc comment — one new import, one
`cylinderSolidLayout(diameterPx, heightPx)` call replacing the old inline
`radiusPx`/`angleStep`/`segmentWidth` math, and the two hardcoded cap
`<div>`s plus the 16-slat `Array.from(...)` map replaced with
`caps.map(...)`/`slats.map(...)` rendering the same class names
(`sb-solid__disk-face` for caps, `sb-solid__face` for slats). The
now-unused module-level `_CYLINDER_SIDE_SEGMENTS` constant (its own math
moved into the helper) was removed along with its explanatory comment,
which was relocated (expanded) into `cylinderFaces.ts`'s own header. The
`box` and `disk` branches are untouched.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `Solid3D` cylinder | Same 2 caps + 16 slats, new layout math — verified via `git diff` showing only the cylinder branch (+ the module doc comment) changed |
| `Solid3D` box / `cuboidFaces.ts` | **Byte-unchanged** — `git diff --stat` on `cuboidFaces.ts` empty; `Solid3D.tsx`'s `box` branch untouched |
| Disk | **Byte-unchanged** — `Solid3D.tsx`'s `disk` branch untouched |
| `SCENE3D.pxPerMm` | **Unchanged** — `scene3dScale.ts` not touched, still `0.5` |
| Projector / DTO | **Unchanged** — no Python file touched |
| Grafo cards | **Unchanged** — no `.sb-world`/2D-card file touched |
| Standoff layout copies | **Unchanged** — no XY-point file touched; this is visor faces only |

---

## 5. Tests run

### 5.1 UI — new vitest module

`ui/spatial-board/src/cylinderFaces.test.ts` — **6 tests**:

| Test | Covers |
|---|---|
| `T1: cube-like D=H=40 — two caps (left=0, top=0, translateZ 20), 16 slats with the correct chord/left` | T1 |
| `T2: thin hub D=65.36, H=3.4 — Gemfan 51466-class prop-hub fixture` | T2 |
| `T2b: tall post D=3, H=15 — standoff-visor-sized fixture` | T2b |
| `T2c: cap top follows (H-D)/2 exactly, including the negative case` | T2c |
| `normals match the IC §0.5 lock exactly, and no cap/slat transform ever uses translateX/translateY` | T2 (no-translateX/Y check) + normals lock |
| `always exactly 2 caps and 16 slats (N frozen), regardless of D/H` | freeze/N=16 lock |

```text
✓ src/cylinderFaces.test.ts (6 tests) 3ms
```

### 5.2 Full UI vitest suite

```text
Test Files  15 passed (15)
     Tests  142 passed (142)
```

Baseline before this Buy: 136 tests (14 files, after the cuboid Buy).
Delta: **+6**, exactly matching the new test count — zero regressions.

### 5.3 `tsc --noEmit`

```text
> jarvis-spatial-board@0.1.0 typecheck
> tsc --noEmit
```

Clean — no type errors. Removing the now-unused
`_CYLINDER_SIDE_SEGMENTS` module constant did not leave any dangling
reference.

### 5.4 Full Python suite (T7 — no new Python tests required)

```text
3691 passed, 2 skipped in 7.87s
```

Unchanged from the pre-Buy baseline (`3691 passed, 2 skipped`) — exactly
as IC §4 T7 expects, since this is a UI-only fix with no `src/jarvis/`
edits.

---

## 6. Module-boundary / freeze grep (run at close of this Buy)

```text
$ git diff -- ui/spatial-board/src/Solid3D.tsx
# diff limited to: +1 import line, the module doc comment's cylinder
# sentence reworded to name the new helper instead of the removed
# private constant, the removed _CYLINDER_SIDE_SEGMENTS const + its
# comment, and the cylinder branch's cap/slat rendering replaced by
# caps.map(...)/slats.map(...). box and disk branches: zero lines
# changed.

$ git diff --stat -- ui/spatial-board/src/cuboidFaces.ts ui/spatial-board/src/spatial-board.css \
    src/jarvis/workspace/spatial_board.py
ui/spatial-board/src/cuboidFaces.ts    | (empty — untouched)
ui/spatial-board/src/spatial-board.css | (empty — untouched)
src/jarvis/workspace/spatial_board.py  | (pre-existing diff from an unrelated, external
                                            geometry-track session — not touched by this Buy,
                                            same pre-existing diff noted in the cuboid Buy's
                                            own report)
```

`git status --short` at close of this Buy shows exactly the expected
file set: `cylinderFaces.ts`, `cylinderFaces.test.ts` (new),
`Solid3D.tsx` (modified), plus `pyproject.toml` + version-checkpoint test
re-pins + docs. No `cuboidFaces.ts`, `spatial-board.css`, disk branch,
projector, DTO, or `spatial_board.py` edits from this Buy.

---

## 7. Files changed

**New:**
- `ui/spatial-board/src/cylinderFaces.ts`
- `ui/spatial-board/src/cylinderFaces.test.ts`
- `.jes/artifacts/implementation_report_geometry_taller_css_cylinder_faces_b1.md` (this file)

**Modified:**
- `ui/spatial-board/src/Solid3D.tsx` (cylinder branch consumes `cylinderSolidLayout`; box/disk branches untouched; removed now-unused `_CYLINDER_SIDE_SEGMENTS` constant)
- `pyproject.toml` (`0.5.34` → `0.5.35`)
- 41 pre-existing Python test files re-pinned from `0.5.34` to `0.5.35` (literal `'version = "X.Y.Z"' in text` pattern and the `match.group(1) == "X.Y.Z"` regex pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new paragraph after the cuboid block), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §9)

No `CMakeLists.txt`/Python change was needed — this is a pure
TypeScript/CSS-adjacent Buy on the UI side, same axis as the cuboid Buy.

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.35 includes (landed, awaiting Cursor review + Engineer Taller smoke + ★ ACCEPT — no `v0.5.35` tag yet)" section; the v0.5.34 section's own "Next" line and both bottom "Next" mentions updated to point at this Buy's LANDED status.
- `docs/ARCHITECTURE.md` — banner updated (§2 Platform/Fase C line) and a new paragraph inserted after the cuboid block, both phrased "landed — awaiting Cursor review + Engineer Taller smoke + ★ ACCEPT, no `v0.5.35` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new block after the cuboid paragraph, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim ("Visor cylinder ≠ CAD ≠ fit ≠ extra parts ≠ round metal ≠ a standoff hole pattern").
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the cylinder table row both changed from "IC READY (awaiting Engineer ★)" to "LANDED (awaiting Cursor review + Engineer Taller smoke + ★ ACCEPT, no tag yet)"; UI vitest count updated `136` → `142`.

No file in this Buy claims `v0.5.35` is tagged, ACCEPT CLOSED, "CAD",
"round stock", "fit VERIFIED", or a real turned part exists. Confirmed
via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.32`,
`v0.5.33`, `v0.5.34` — `v0.5.35` does not exist yet. Docs also note that
`v0.5.34` itself is a **local** tag not yet pushed to origin, per the
Engineer's own handoff note — this Buy did not push anything either (no
commit/tag/push is performed by the implementer, per standing session
rule).

---

## 9. Residual / next steps

- D2 docs truth-sync (`B1-docs-truth-sync-after-c35`) remains explicitly
  retargeted/blocked behind this Buy's own tag per its own IC §8 STOP —
  not opened here.
- Standoff perimeter points is the one remaining no-pin/no-CAD front per
  the existing "situation after C33" engineer note — not opened by this
  Buy.
- The Engineer's own **Taller smoke** (looking at a short hub and a tall
  post on-screen, not just the vitest numbers) is still outstanding —
  this report's own test evidence is numeric/structural only, per the
  IC's own "Helper + vitest; no screenshot gate" default.
- The disk branch's own single-face, no-axial-extent construction was
  not touched and remains out of scope — it has no analogous cap-pivot
  bug since it never has a second face or a nonzero axial wrapper
  height.

---

## 10. Acceptance self-check vs IC §7

- T1-T9: ✅ T1/T2/T2b/T2c/normals-lock/N-frozen in vitest (6/6 passing), T3 (`Solid3D` cylinder branch maps helper fields onto the 2 cap nodes and 16 slat nodes) verified via the `caps.map(...)`/`slats.map(...)` wiring itself plus the full 142/142 vitest suite exercising it through every existing UI test that renders a cylinder, T4 (`git diff --stat` shows `cuboidFaces.ts` and the disk branch untouched), T5 (no `src/jarvis/`/`library/` edits), T6 (`npm test && npm run typecheck` both green), T7 (Python suite unchanged, no new Python tests), T8 (`pyproject` `0.5.35`), T9 (this report).
- 2 caps + 16 slats: ✅ `cylinderSolidLayout` always returns exactly 2 caps and 16 slats; `Solid3D.tsx` renders exactly `caps.map(...)`/`slats.map(...)`, no extra element added anywhere.
- Thin-hub fixture: ✅ T2/T2b exercise both the short-hub (`65.36×3.4`) and tall-post (`3×15`) fixtures from IC §0.7.
- Box + disk frozen: ✅ `git diff` on `Solid3D.tsx` touches only the `cylinder` branch (plus the module doc comment); `cuboidFaces.ts` diff empty.
- Projector frozen: ✅ no Python file touched.
- No `translateY(±H/2)` kept on centered caps: ✅ explicitly asserted absent in T2 and the normals-lock test.
- Version `0.5.35`: ✅ `pyproject.toml` + all 41 checkpoint tests re-pinned.

**PASS** against every criterion in IC §7 that this report can verify
programmatically. **FAIL conditions** (extra faces, DTO Ø/H invented,
`.sb-world` retargeted, standoff points moved, Three.js, cuboid recut,
`translateY(±H/2)` kept on centered caps) — none present, verified
above. The Engineer's own visual Taller smoke (short hub / tall post
on-screen) remains the outstanding human-in-the-loop step before ★
ACCEPT.
