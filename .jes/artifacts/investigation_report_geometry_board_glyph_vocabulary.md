# Investigation Report — Minimum Board Glyph Vocabulary (Geometry · visualizar B1)

**Project:** Jarvis
**Date:** 2026-09-07
**Investigator:** Claude Code
**Contract:** [investigation_contract_geometry_board_glyph_vocabulary.md](investigation_contract_geometry_board_glyph_vocabulary.md)
**Parents:** Geometry Progression Lock B1 · `representar` CLOSED (Battery 2316 · Motor 2323 · ESC 2327 · FC 2332) · live suite 2336
**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Review:** [investigation_review_geometry_board_glyph_vocabulary.md](investigation_review_geometry_board_glyph_vocabulary.md)  
**IC:** [implementation_contract_geometry_board_glyphs_b1.md](implementation_contract_geometry_board_glyphs_b1.md)

**Not an Implementation Contract. No `src/`/`ui/` edits made.** All family/dimension claims below are re-read from the live seed data and code this session, not assumed from the prior investigations' summaries.

---

## A. Executive answer

Re-scanning every family's actual sourced dims (not the candidate table's assumptions) produces a **smaller** vocabulary than the contract's own starting point suggests: **`box` and `disk` are the only two shapes any real, sourced identity can honestly draw today — `cylinder` and `bar`/`rectangle` are currently unreachable, zero live matches.** Battery (3/10 rows), ESC (1/1 row), and Flight Controller (`pixhawk_4` only) each have a full L×W×H triple → `box`. Propeller (17/17 rows, `diameter_in` is a required field) and Motor (2/22 rows, `diameter_mm` only) both reduce to a single diameter with no honest height → `disk`. **Motor cannot get a 3D cylinder in B1 without either resurrecting the overall-axial-height field Motor B1 explicitly rejected, or stitching together two different physical references (the outer bell's `diameter_mm` with the stator core's `stator_height_mm`) — both are dishonest, and this report recommends neither.** Frame's arm/plate (thickness + label only, no L×W ever sourced) and the frame root itself (`wheelbase_mm` is a span, not an oriented box edge) stay glyph-blocked — a single scalar cannot define a 2D area, full stop. A real, previously-uninspected finding: the Board DTO's existing `width`/`height` keys already mean the **card's on-screen pixel size** (draggable/resizable) — a glyph feature must use different key names for physical mm dims, or it will silently collide with unrelated layout state. Recommended shape: the **Python projector** computes shape+dims from whichever `PropertyValue` keys are actually present (not a hardcoded family table) and emits an additive, optional `geometry` object per node; the React side is a dumb renderer that draws it or draws nothing — never re-derives readiness from the already-formatted text `fields`. **Default absence policy: no glyph at all when dims are insufficient — the card stays exactly as it renders today, never a "partial" shape.** **Recommend Buy B1**, scoped to exactly `{box, disk}` for exactly the identities named above.

---

## B. As-is inventory (glyph-ready / partial / blocked)

| Surface | Finding | Citation |
|---|---|---|
| Board data path | `ProjectState` → `project_spatial_nodes` (pure Python projection) → JSON over `/api/projects/:id/nodes` (Vite plugin, spawns the projector fresh per request) → React `SpatialNode[]` → `SpatialCard.tsx`. No second geometric store anywhere in this path — confirmed unchanged since the B3 investigation. | `spatial_board.py:36`, prior Board investigations |
| Node DTO shape today | `{id, title, declaredName, kind, fields, x, y, width, height}` — **`width`/`height` are the card's on-canvas pixel rectangle** (drag/resize state, Q1-Q11 viewport work), not any physical dimension. `fields` is `[{label, value}]` — pre-formatted **display strings** (`"50 mm"`, `"5 in"`), produced by `_format_property`, which discards the original numeric value and unit as separate machine-readable fields once formatted. | `spatial_board.py:60-103` (`place`/`_emit`), `spatial_board.py:181-202` (`_fields`/`_format_property`), `types.ts:9-22` (`SpatialRect`/`SpatialNode`) |
| Naming collision (new finding) | A glyph feature that reused `width`/`height` for physical mm size would silently corrupt the existing drag/resize layout state — these keys are already load-bearing for an unrelated concern. Any geometry hint needs its own key(s), never `width`/`height`. | direct comparison of `spatial_board.py:96-99` against `types.ts:9-14` |
| Battery | 3 of 10 rows (`lipo_4s_1500mah`, `lipo_4s_5000mah`, `lipo_6s_6000mah`) carry a full `length_mm`+`width_mm`+`height_mm` triple. The other 7 have none. | `library/baterias/_datos.json` (re-read this session) |
| ESC | 1 of 1 row (`hobbywing_xrotor_40a_6s`) carries the full triple. | `library/esc/_datos.json` |
| Flight Controller | Only `pixhawk_4` has any dims at all — `FLIGHT_CONTROLLER_DIMENSIONS["pixhawk_4"]` = `44.0/84.0/12.0`. Every other `FLIGHT_CONTROLLER_MAP` identity (`pixhawk_4_mini`, `pixhawk_6*`, `ardupilot`, `betaflight`, `naze32`, `matek`) has zero geometry — confirmed by reading the table (one entry). | `aerial.py` (`FLIGHT_CONTROLLER_DIMENSIONS`, added by the FC B1 IC) |
| Propeller | **All 17 rows** have `diameter_in` (a required, non-optional `PropellerSpec` field) — the only family with 100% coverage. `pitch_in` is also required but pitch is not a drawable envelope dimension (it's a helical-twist spec, not a size); irrelevant to a disk glyph. | `library/helices/_datos.json`, `library.py` `PropellerSpec` |
| Motor | Only 2 of 22 rows (`emax_rs2205s_2300`, `sunnysky_r2205_2500`) have any dims: `stator_diameter_mm`+`stator_height_mm` (22/5, both rows, sourced) and `diameter_mm` (overall bell, 27.9/27.4, both rows, sourced). **No row has an overall axial height** — Motor B1 explicitly rejected it (EMAX's shaft-inclusive "Motor Height" 31.7mm vs SunnySky's body-only "Body Length" 18mm disagreed by nearly 2× for the same stator class). | `library/motores/_datos.json`, Motor B1 investigation §C (re-confirmed, not re-litigated) |
| Frame arm/plate(s) | `arm_thickness_mm` + `plates[].thickness_mm`/`label` — **thickness only, no length or width ever sourced for any seeded row**, confirmed by re-reading `FrameSpec`/`PlateSeed` (`library.py`) and all four frame rows. A single scalar (thickness) cannot define a 2D area — there is no honest shape to draw, not even a degenerate one. | `library.py` (`FrameSpec`, `PlateSeed`), `library/frames/_datos.json` |
| Frame root | Only `wheelbase_mm` (a motor-to-motor span) exists — not an oriented length/width pair, and mapping it onto a box edge would require an unstated assumption about which axis and configuration (quad-X vs deadcat differ). No frame row has any L×W×H envelope. | `library.py` `FrameSpec` |
| Sensors | Free-text only (`gps_model`/`sensor_type`), zero geometry ever proposed for this family, orthogonal per the Sensors BOM honesty investigation. | `aerial.py` `extract_sensor_properties` |
| B3 slot cards | `kind: "slot"` nodes carry exactly `fields: [{"label": "estado", "value": "no declarado"}]` — no geometry-shaped data at all. A glyph feature must not synthesize a placeholder shape for a slot; absence stays absence. | `spatial_board.py` (slot emission, B3 IC) |

---

## C. Minimum glyph vocabulary

**Closed set for B1: `box`, `disk`. Nothing else ships.**

| Shape | Driven by (dims present on the spec) | Identities that qualify today |
|---|---|---|
| `box` | `length_mm` **and** `width_mm` **and** `height_mm`, all present | Battery ×3, ESC ×1, FC (`pixhawk_4` only) |
| `disk` | a single diameter (`diameter_mm` **or** `diameter_in`), **no** height/length present alongside it | Propeller ×17 (all), Motor ×2 (`emax_rs2205s_2300`, `sunnysky_r2205_2500`) |
| *(named, not shipped)* `cylinder` | would need diameter + a *same-object* height | **zero** current matches — see §E |
| *(named, not shipped)* `bar`/`rectangle` (arm/plate) | would need thickness + length (+ width) | **zero** current matches — thickness alone exists, length never sourced |

**Design rule recommended:** shape selection should be **driven by which dimension keys are actually present on the `ComponentSpec`**, not a hardcoded per-family lookup. This is why Motor and Propeller — two unrelated families — both resolve to the *same* `disk` shape: both happen to have exactly "one diameter, no height" today. It also means a hypothetical future cylindrical-cell battery row (`diameter_mm`+`height_mm`, no L/W) would correctly fall out as a future `cylinder` candidate without any code path needing to know "batteries are boxes" as a fixed rule — the rule is about the *data shape*, not the *product category*.

**Units — mm vs in, both drawn to the same physical scale, never silently relabeled:** Propeller's `diameter_in` and every mm family must render at the *same physical scale* on one canvas (a 5-inch prop and a 44mm FC board must look proportionally correct next to each other) — this requires converting `diameter_in × 25.4` to an mm-equivalent **purely for the glyph's pixel size**, at render/projection time. This is a lossless unit conversion (a physical constant), not an invention of a new fact, and it must **never** change what the card's own text field says (`"5 in"` stays `"5 in"` in `fields`) — the conversion exists only inside whatever new geometry-hint structure feeds the drawing, never overwriting the declared unit shown to the reader.

---

## D. Absence / partial-dim policy — default lean

**Default: no glyph at all when dims are insufficient for one of the two closed shapes above.** The card renders exactly as it does today (identity + text `fields`, nothing more) — no dashed placeholder, no "partial envelope" outline, no interpolated/assumed dimension.

**Why not a "partial glyph" (the contract's named alternative):** a partial/incomplete outline risks being read as *some* real geometric fact ("this is roughly how big it is") when the actual truth is "Jarvis knows nothing about this identity's shape." The Board already has an established, understood visual language for "we know this slot exists but not its content" — B3's dashed `kind: "slot"` card — and that pattern exists for missing *components*, not missing *dimensions* on an otherwise-present component. Inventing a second, different "incomplete" visual (a half-drawn box) for a present-but-under-dimensioned component would add a new honesty vocabulary the reader has to learn, for marginal benefit over simply not drawing anything. **No glyph is the smaller, safer, more consistent-with-precedent default.**

**Named alternative (not recommended for B1):** a visibly dashed/greyed shape using only the dims present (e.g., a disk-only hint on a box-shaped part with just one dimension known) — would need its own honesty-matrix entry ("dashed shape ≠ verified shape") and its own visual design pass; deferred, not ruled out forever.

---

## E. Motor cylinder special case

Motor is the one family with genuinely mixed evidence, and it is where a rushed implementation would most easily reintroduce the exact problem Motor B1 closed. Laid out explicitly:

- `diameter_mm` (27.9/27.4mm) — the **outer bell/rotor** diameter, sourced, on both rows.
- `stator_diameter_mm`+`stator_height_mm` (22/5mm) — the **stator core**, a different, smaller, internal physical reference, also sourced, on both rows.
- No overall axial height for the assembled motor — deliberately absent per Motor B1's finding that EMAX's and SunnySky's own "height"-shaped figures for the *same* stator class disagree by nearly 2× (shaft-inclusive vs body-only), with no way to tell which convention a bare mm figure follows.

**Two ways this could go wrong, both rejected here:**
1. **Resurrect the rejected field** by inventing/estimating an overall height to pair with `diameter_mm` — directly contradicts Motor B1's own locked exclusion and this contract's "do not invent missing dimensions."
2. **Stitch `diameter_mm` (outer bell) to `stator_height_mm` (stator core)** to make a cylinder — technically two real, sourced numbers, but they describe **two different physical objects nested inside one product**; the resulting cylinder would correspond to nothing real (neither the stator's true size nor the motor's true size). This is a subtler form of inventing geometry — the ingredients are real, the composite is not.

**Recommended: `disk` using `diameter_mm` only** — an honest "how wide is this motor, viewed from above" footprint fact, with no height claim implied at all (a disk has no height dimension by construction, so there is nothing to get wrong here). The stator-core pair (`stator_diameter_mm`/`stator_height_mm`) is a real, drawable cylinder **of the stator alone**, but is **not recommended as the motor's primary glyph** in B1 — it would visually read as "this is the motor's size," which it is not (it is roughly the size of the internal lamination stack, dramatically smaller than the assembled product). Naming it here as a possible, clearly-labeled *secondary* detail for a much later iteration, not a B1 deliverable.

---

## F. Honesty / ladder matrix

| Implication | True if B1 ships as scoped? | Over-claim risk | Desired wording |
|---|---|---|---|
| "The Board shows the drone" | No — it shows individual declared components' own envelopes, each independently, with no spatial relationship between them (per the Progression Lock's own frontier: "tiene geometría ≠ está ensamblado") | High if ever implied | Keep Board copy scoped to "declared component shapes," never "the drone" or "the design." |
| "Glyph = CAD" | No — a glyph is one closed 2D shape (`box` outline or `disk` circle) sized from declared scalars; no mesh, no tolerance, no manufacturing data, no fasteners | Medium if marketed loosely | "Forma declarada aproximada," never "modelo CAD." |
| "Card layout = assembly" | No — unchanged from every prior Board investigation; card position on canvas is presentation-only, drag/resize state, never engineering position | Low, already an established, tested locked stance (B3, viewport work) | No change needed; re-affirmed, not re-litigated. |
| "Visualizar verifies fit" | No — no two glyphs are ever compared, measured against each other, or checked for overlap/interference; each glyph is drawn independently of every other node on the canvas | **High — this is the exact next-rung boundary the Progression Lock draws** ("ASSEMBLY ESPACIAL" is later, explicitly not this Buy) | Never emit or imply a fit/clearance/interference statement from glyph proximity on the canvas. |
| "This motor's glyph shows its true size" | Partially — the `disk` only claims *width* (bell diameter); it makes no claim about the motor's actual depth/height, and the reader must not infer one from the flat circle | Medium — a bare circle glyph for a 3D object could be over-read as "this is the whole shape" | If a UI affordance is needed, a plain tooltip/label distinguishing "diameter shown, height not represented" is a copy-only mitigation available at implementation time; not decided here. |
| "No glyph = no component" | No — many present, honestly-declared components (most motors, all unsourced batteries, every non-`pixhawk_4` FC, every frame part) will show text-only, exactly as today; absence of a glyph must never be confused with absence of the component itself | Medium, purely a UI-legibility question, not a truth-claim risk | Text-only cards remain fully legitimate, unchanged visual treatment from today — no regression implied by "no glyph." |

---

## G. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| B0 | Docs/vocabulary lock only, no code | If Engineer wants to ★ the `{box, disk}` vocabulary and the "no glyph on absence" default before any implementation — reasonable given how much this report narrows the contract's own starting assumptions |
| **B1** | **Glyphs for exactly the ready identities in §B/§C** (`box`: Battery×3, ESC×1, FC `pixhawk_4`; `disk`: Propeller×17, Motor×2), driven by a projector-computed `geometry` DTO hint, no UI-side dimension inference, no partial/dashed shapes | **Recommended — see below** |
| B2+ | Pose / `mounted_on` / assembly / fit | Explicitly out of scope — next rung per the Progression Lock, not this investigation's Buy space |
| Defer | — | Not applicable — real, sourced identities exist today for both shapes in the recommended closed vocabulary; nothing blocks a scoped B1 |

### Default lean: **B1, scoped to exactly `{box, disk}` for exactly the identities named in §C**

Smallest coherent shape: two shape renderers (a rectangle and a circle, sized proportionally by mm-equivalent scale, per §C's unit-conversion rule), computed server-side in the existing Python projector from dims already sourced and shipped across four prior IC's, exposed as one new, optional, additive DTO key that leaves every current field (`fields`, `width`, `height`, `kind`) untouched. No pose, no `mounted_on`, no fit, no new dimension sourcing, no cylinder/bar renderer built for a vocabulary slot nothing currently occupies.

**Suggested first IC title (for Cursor, not decided here):** *"Board glyphs — box + disk for representar-complete identities only, projector-computed, no UI inference."*

---

## H. Non-goals for the first `visualizar` IC

Pose / orientation · `mounted_on` / assembly relations · intersection/overlap detection · clearance/fit claims · STEP/STL import · FEA/manufacturability claims · a `cylinder` or `bar` renderer (named in the vocabulary, not shipped — zero current matches) · resurrecting Motor's rejected overall axial height · combining `diameter_mm` with `stator_height_mm` into a composite motor cylinder · Frame arm/plate/root glyphs (no L×W ever sourced) · Sensors geometry · a "partial/dashed" glyph visual language (named as a later alternative, not this Buy) · reusing `width`/`height` DTO keys for physical dims (naming collision, §B) · UI-side dimension parsing from the existing text `fields` · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · inventing any dimension not already sourced by a prior, closed Geometry IC · weakening tests.
