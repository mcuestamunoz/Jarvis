# Investigation Report — Scene3D-from-Pose B1 (Visor Reads `declared_box_pose`)

**IC:** [investigation_contract_geometry_scene3d_from_pose_b1.md](investigation_contract_geometry_scene3d_from_pose_b1.md)
**Investigator:** Claude Code
**Review:** [investigation_review_geometry_scene3d_from_pose_b1.md](investigation_review_geometry_scene3d_from_pose_b1.md) — **PASS WITH NOTES** · Engineer ★ **B1** · [IC READY](implementation_contract_geometry_scene3d_from_pose_b1.md)
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2456 · commit `8930c0b` (unchanged — investigation only, no code/tests touched, nothing persisted)

---

## 1. Executive recommendation

**B1 — additive DTO + CSS placement, explicitly NOT B1+ (no chain composition), for a concrete and freshly-discovered reason: origin-chain cycle detection does not exist anywhere in the system today, and no live evidence justifies building it yet.** The visor genuinely has no machine-readable pose today — only human text inside `fields` — so a new, additive projector key (mirroring `mountedOn`'s own precedent exactly) is the correct fix, not parsing presentation strings. But composing placement through a chain of origins (an origin that is itself posed relative to a third box) requires cycle-safe graph walking that nothing in the schema or writer currently guarantees — I proved this live: the writer accepts a 2-node mutual-origin cycle (`a`'s origin `b`, then `b`'s origin `a`) without complaint. Since the entire live demo currently has **zero** declared poses set anywhere, there is no evidence a first Buy needs chain composition at all — scope B1 to single-level placement (a node may be placed relative to an origin's own already-existing position, but an origin that is itself posed is out of scope for composing further) and defer chains to a later, separately-evidenced cycle.

---

## 2. As-is visor vs as-is pose

- **The projector DTO has no pose key of any kind.** Re-read `_emit` in full (`spatial_board.py:117-144`): its only optional keyword parameters are `geometry` and `mounted_on`; there is no third parameter, and `place()` (the function that calls `_emit`) never computes or passes one. Pose exists **only** as human-readable text inside `fields` — `_fields` (confirmed present, unchanged since the writer IC) appends `"origen pose"`/`"ejes pose"`/`"Δx mm"` etc. as plain `{label, value}` strings, indistinguishable at the type level from any other property text.
- **`SpatialNode` (`types.ts:27-40`) has no pose field.** Only `geometry?: SpatialGeometry` and `mountedOn?: string` exist beyond the base rect/kind/fields shape — confirmed by reading the full type definition this session.
- **`scene3dLayout.ts`'s own module docstring is stale**, confirmed by direct comparison against the current state of the project: line 9 reads *"a 3D 'where does this sit relative to the others' fact does not exist anywhere in the system yet (pose stays B0 DEFERRED)"* — this was true when Board CSS 3D solids B1 shipped, but pose has since been Bought, written, and Continuity-declared (closed at suite 2456). The comment is not functionally wrong (the function genuinely still doesn't read pose), but it misdescribes *why* — pose is not absent from the system, only absent from this one function's inputs. Worth a one-line fix in any future IC touching this file, named here so it isn't lost.
- **The card already shows what the visor doesn't yet read** — confirmed the writer/Continuity/Board-text chain (closed at suite 2438/2456) works end-to-end; the sole gap this investigation is about is that `Scene3D`/`Solid3D` never consume it.

---

## 3. Live census (re-verified fresh — not carried over from memory)

Re-ran `_geometry_from_spec` against the **current** `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` this session:

| Key | `geometry` | `mounted_on` | `declared_box_pose` |
|---|---|---|---|
| `esc` (`hobbywing_xrotor_40a_6s`) | `box` 50×21.6×12mm | `frame_plate` | `None` |
| `battery` (`lipo_4s_1500mah`) | `box` 37×35×75mm | `frame` | `None` |
| `flight_controller` (`Pixhawk 4`) | `box` 44×84×12mm | `frame_plate` | `None` |
| `propellers` (`gemfan_5045_hbn`) | `disk` Ø127mm | `motors` | `None` |
| `motors` (`sunnysky_r2305_2500`) | **`None`** | `frame_arm` | `None` |
| 9 remaining keys | `None` | mostly `None`, `sensors→frame` | `None` |

**This census has genuinely drifted since the CSS 3D investigation and must not be assumed stale-but-stable**: the project's `motors` component is now bound to a **different** SKU (`sunnysky_r2305_2500`, not `emax_rs2205s_2300`) that has **no `diameter_mm` in its seed row at all** (confirmed: `library/motores/_datos.json`'s `sunnysky_r2305_2500` entry has only `thrust_n`/`kv_rating`/`weight_g`/`max_watts`/`compatible_prop_inch`/`design_space` — no geometry field whatsoever). The live count is therefore **3 boxes, 1 disk, 10 none** today — not the "3 box + 2 disk" figure this IC's own baseline table (and every prior Geometry report this session) assumed. This is itself a small, concrete illustration of Question D's concern: `motors` is mounted (`mounted_on=frame_arm`) but has zero geometry, so it cannot be a solid at all, independent of and prior to any pose question. **Zero non-null `declared_box_pose` exists anywhere** — confirmed directly, matching this IC's own hint that the prior cycle's Engineer smoke set then cleared a pose and did not leave one live.

---

## 4. Answers A–F

### A — How does pose reach the visor?

**A1/A2 — DTO vs parsing `fields` text.** **DTO**, not text-parsing — confirmed as the only honest option by the same reasoning `mountedOn`'s own B2 IC already established for the identical choice (machine key vs. reading `"montado en"` text). Sketch (name-only, not an IC): an additive, optional `declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number }` on `SpatialNode`/the projector's node dict — mirroring `mountedOn`'s own **omit-when-invalid** rule (§A2 continued below), never a required field, never inferred.

**A2 (continued) — omission rule.** Same honest-absence discipline `mountedOn`'s own DTO key already uses: emit `declaredBoxPose` only when (a) `ComponentSpec.declared_box_pose` is set, **and** (b) the origin key is still present among the projected nodes with a `box` geometry. This is not a new rule to invent — `_fields`'s own existing pose-text logic (`spatial_board.py`, added by the Continuity Declared Box-Local Pose B1 writer IC) already implements exactly this check for the text fields; the DTO key would reuse the identical condition, just also carrying the numbers as numbers instead of only as formatted strings.

**A3 — Projector stays the only writer of this DTO.** Confirmed by construction: the DTO would be Python-computed, server-side, from the same `ComponentSpec.declared_box_pose` field the writer already validates — the visor would never infer, guess, or compute a pose from `mounted_on` or card `x`/`y`, matching Locked Stances 2/5/6 exactly.

### B — Origin solid and composition

**B4 — Where does the origin's own center sit?** The origin box, when unposed itself (the common case — writer forbids self-origin, and today literally every box-capable node is unposed), stays exactly where the existing presentation row already puts it — its own `originX` from `layoutSolidsRow`, unchanged. A placed child's translation is computed **relative to that row position**, not relative to some new, separately-defined "scene zero."

**B5 — Compose through chains? Recommended: no, not in this Buy.** The schema's own docstring says origin = "the geometric center of `origin_key`'s declared box" — it does not say "unposed," and in principle nothing prevents an origin from itself carrying a pose relative to a third box. But I tested this live and found **no cycle protection exists anywhere**: `set_component_declared_box_pose(state, "a", DeclaredBoxPose(origin_key="b", ...))` followed by `set_component_declared_box_pose(..., "b", DeclaredBoxPose(origin_key="a", ...))` succeeds at the writer layer with no error — a genuine 2-node mutual-origin cycle is representable in `ProjectState` today. A visor that recursively "walks the chain to compute world position" would need its own defensive cycle guard that nothing else in the system provides, for a capability **zero live components currently use** (§3 — every pose is `None`). Building chain-walking + cycle detection now, against no live evidence of need, is exactly the kind of premature complexity this investigation line has consistently rejected elsewhere (inventing envelopes, axes, hole patterns). **Recommendation: B1 scopes to single-level placement only** — a node's origin is treated as sitting at its row position regardless of whether that origin itself happens to carry a `declared_box_pose` (i.e., don't recurse). This is honestly labelable ("this node is placed relative to its origin's *current on-screen* position, one level only") and defers chain composition to a later cycle that would also need to design the cycle guard this investigation found missing.

**B6 — Missing/non-box origin.** Confirmed the projector's existing text-field logic already omits the pose text when the origin has vanished or is no longer a box; the DTO key would use the identical guard (§A2). The visor never falls back to a guessed origin — a node with an unresolvable pose simply stays in the unposed remainder (§D).

### C — CSS 3D axes vs. declared L→+X — the load-bearing finding of this investigation

**C7/C8 — The cuboid's own face geometry already commits to a specific, non-obvious axis remap, found by tracing the actual code, not assumed:**

`Solid3D.tsx:22,30` destructures `solidExtentPx`'s output as `{x: w, y: d, z: h} = extent` for a box — i.e., **CSS width = declared length (+X)**, **the depth used for `translateZ` = declared width (+Y)**, and **CSS height = declared height (+Z)**. The six faces (`Solid3D.tsx:40-45`) confirm this is deliberate and consistent: front/back faces span `width×height` and sit at `±translateZ(d/2)` (so the L×H face is the one facing the viewer, with W receding into the screen); top/bottom faces span `width×d` and use `rotateX(±90deg)` at `±translateY(h/2)`.

This means **CSS's own three transform axes do not line up one-to-one with the declared L/W/H → X/Y/Z labels**:

| Declared axis (schema) | What it measures | CSS transform axis actually used |
|---|---|---|
| `x_mm` (L, "+X") | length | `translateX` — **aligned**, no remap |
| `y_mm` (W, "+Y") | width | `translateZ` — **CSS's depth axis**, not CSS-Y |
| `z_mm` (H, "+Z") | height | `translateY` — **CSS's vertical axis**, not CSS-Z |

A naive `transform: translate3d(x_mm*k, y_mm*k, z_mm*k)` would put a declared-width offset where CSS expects vertical movement, and a declared-height offset where CSS expects depth — silently placing a component in the wrong on-screen relationship to the box whose own faces were drawn with the opposite convention. **The one honest remap table is `translate3d(x_mm, z_mm, y_mm)`** (note the swap) — the same convention the cuboid's own faces already use, not a new invention. This is a concrete, precise, previously-undocumented fact this investigation surfaced by reading the transform code line by line, not something a future IC should have to rediscover.

**C9 — `pxPerMm` stays linear/uncapped.** Confirmed — `solidExtentPx` (`scene3dScale.ts`, re-read, unchanged) is the same function every current solid already uses; a placement translation would reuse it for the offset values too, never `GLYPH`'s capped 2D scale.

**C10 — Disk translation.** A disk's own local frame is rotationally symmetric (`diameter_mm` is the same value on both `x`/`y` of its extent, `z` is always `0`) — there is no "wrong remap" risk for the disk's **own shape**, since any horizontal rotation of a circle looks identical. But a disk's **position** relative to an origin should use the identical `(x, z, y)` remap for consistency with how boxes are placed — otherwise a disk and a box posed at the same declared `(5, 0, 0)` would visually move in different screen directions relative to the same origin, which would be a real, confusing inconsistency even though neither number was dishonest on its own.

**CSS top-left vs. geometric center — a second concrete gap found by reading the code, not assumed.** `.sb-solid` (the outer wrapper `div`) is `position: absolute` with **no** `top`/`left` offset of its own — its drawn box spans from `(0,0)` to `(w,h)` relative to its positioned ancestor, i.e., **the wrapper's top-left corner**, not its center, is what `translateX(originX)` actually moves. Every face inside is positioned with `±half-extent` offsets *from that same (0,0) corner*, meaning the cuboid's true geometric center is drawn at local `(w/2, h/2, 0)`, not at `(0,0,0)`. **Any future placement code that applies a "center-to-center" declared offset directly as a CSS `translate` would be off by exactly half the box's own width/height** unless it also corrects for this — a real, non-obvious implementation detail, named here precisely so a future IC doesn't silently ship an off-by-half-extent placement bug.

### D — Who stays in the row?

**D11 — Default lean: remainder row, confirmed by evidence, not asserted.** Given §3's finding that **zero** live components have a pose set today, the honest behavior for the current demo (and for any project until someone actually Continuity-declares a pose) is that **all** solid-capable nodes stay in `layoutSolidsRow` exactly as today — nothing regresses, nothing silently jumps to a shared origin (the CSS 3D review's own N1 concern). A node only leaves the row once it has a resolvable `declaredBoxPose` DTO key.

**D12 — Unposed origin with a posed child.** The origin stays in the row (it has no pose of its own), and the child is placed relative to the origin's *row position*, per §B4 — this is internally consistent with D11's own rule (an object is either "in the row" or "placed relative to something," and an unposed origin is squarely in the former case even while serving as a reference point for something else).

**D13 — Geometry present, origin vanished.** Stays in the row (falls back to the unposed rule) — confirmed as the correct behavior by §A2/§B6's own omission logic; never a guessed origin, never a crash.

### E — What this Buy must not become

Confirmed, all by direct re-reading rather than assumption: `mountedOn` edges remain 2D-only (`DeclaredMountEdges.tsx`/`mountEdgeGeometry.ts` untouched, still read only `node.mountedOn` and card pixel rects — no 3D edge proposed). No `motor_count` instancing — `motors` has exactly one node regardless of its `motor_count=4` property, confirmed live in §3 (and today it has no geometry at all, making the question moot for this project). Click-inspect: a placed solid would still call the identical `onSelect(id)` prop already passed to every `Solid3D` — no second selection model, confirmed by re-reading `InfiniteCanvas.tsx`'s existing prop-threading. Three.js: not evidenced as necessary — §C shows the *entire* remapping problem is expressible as a corrected CSS `translate3d`, a pure arithmetic fix to already-working CSS, not a rendering-capability gap.

### F — Buy options

| Option | Recommended? |
|---|---|
| **B0 — Defer** | No — the DTO/axis/composition questions are all honestly answerable (§A-D), not blocked on missing KNOW the way earlier pose cycles were. |
| **B1 — DTO + CSS place, single-level only (recommended)** | Yes — additive `declaredBoxPose` DTO key, corrected `(x, z, y)` translate remap, center-correction for the top-left-anchor gap, unposed remainder stays a row, no chain composition. |
| B1− — DTO only | Not recommended as the sole Buy — pose text has existed on the card for a full cycle already with no visor consumer; shipping the DTO with nothing reading it yet would repeat that same gap one layer down for no new reason. |
| **B1+ — Compose + place** | **Not recommended this cycle** — §B5's cycle-detection gap is real and currently unguarded anywhere in the system; zero live evidence (§3: no pose set at all) justifies building chain-walking now. |
| B2 — Three.js | Not recommended — §C proves CSS `transform` already expresses the correct remap; no capability gap found. |

**What would change this lean:** a real project with a genuine multi-level pose chain (an origin that is itself meaningfully posed relative to a further box) would justify revisiting B1+ — and that future cycle should design the cycle guard this investigation found missing, not assume the writer already provides one.

---

## 5. Risks

- **Treating a corrected local-prism placement as airframe assembly.** A solid leaving the row and sitting at a declared millimetre offset from another solid's own declared center is real, honest progress — it is still not "the Rooster," still not four motors, still not `"cabe."` The product sentence for this Buy is explicit about this and should stay so in any resulting copy.
- **Treating the unposed remainder row as "these parts are unassembled."** The row is, and remains, a presentation convenience for parts nobody has declared a relative position for yet — not a claim that they're floating in space or missing from the design. No copy anywhere should imply otherwise.
- **The CSS top-left-vs-center gap (§C) is the single most likely silent bug** a future implementer could ship without reading this report closely — a naive placement using the wrong anchor point would still "work" visually (something moves) while being off by a consistent, wrong amount, which is worse than an obvious failure because it looks plausible.
- **The axis swap (§C) is the second most likely silent bug** — a translation using unswapped `x/y/z → translateX/Y/Z` would also "work" in the sense of moving something, while systematically misrepresenting which declared axis corresponds to which on-screen direction, for every box, every time.
- **Composition cycles (§B5), if ever built without a guard, are a real crash risk** (unbounded recursion), not just a display glitch — flagged precisely so a future B1+ cycle treats it as a hard requirement, not an edge case to discover in production.

---

## 6. Later rungs (named, not bought)

```text
rung 1 — Scene3D reads declared_box_pose, single-level placement   THIS report's recommended Buy (B1)
rung 2 — project wheelbase_mm / instance N motors                  NOT this report — mapping-path ★, later
rung 3 — seed motor axial height (e.g. 31.7mm) / cylinder           NOT this report — needs new sourced KNOW, later
rung 4 — plate L×W search or invention                              NOT this report — Class A gap, later, no invention ever
rung 5 — "cabe" vs the assembled situation                          fit stub QUEUED — DO NOT IMPLEMENT, not touched
```

Origin-chain composition (B1+) is named as a **future sub-decision within rung 1's own scope**, not one of the five mapping-path rungs — gated on real evidence of a multi-level pose chain existing, per §F.

---

## 7. Non-goals honored

No code changed — `git status --short -- src/ ui/ tests/` is empty for this cycle. No projector DTO, no `Scene3D`/`Solid3D`/`scene3dLayout`/`scene3dScale` file modified — every finding above came from reading the current files, not editing them. No `state.json` touched — the writer dry-run proving the cycle gap (§B5) ran against a synthetic in-memory `ProjectState`, never the demo project; `git status --short -- workspace/` is empty. No wheelbase, plate L×W, or motor axial height sourced or invented — rungs 2-4 are named only (§6). No fit/`"cabe"` opened, fit stub not touched. No Three.js/r3f added or recommended — §F concludes CSS already suffices. No `motor_count` instancing — confirmed the live `motors` node is a single `ComponentSpec` regardless of its count property, and currently has no geometry at all besides. No Continuity grammar change — no visor-only hole was found that would force one; the existing writer/Continuity/text-field chain is confirmed sufficient as the source of truth this Buy would read from. No version bump. No Implementation Contract written — §F's field-name sketch is explicitly a name-only note, not IC-ready text; Cursor writes any IC after ★.
