# Investigation Report — Plate L×W / Rooster envelope (sourced, GetFPV vs Armattan)

**IC:** [investigation_contract_geometry_plate_lw_sourced_b1.md](investigation_contract_geometry_plate_lw_sourced_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-09
**Checkpoint base:** package `0.3.8` · suite 2497

**Do not implement — this is a read-only report. No `src/`/library edit made.**

---

## Executive summary

Neither Armattan's own manufacturer page nor GetFPV's retailer listing states a footprint (L×W) for the Rooster's Main Plate or for the whole airframe — both pages state **thickness only** (Main Plate 4mm, Arms 4mm) plus a real but unrelated height figure (Armattan's own page: "Max Stack Height: 22mm", not seeded in the current catalog row at all). GetFPV's kit list is indeed richer than the current seed (two more named plates: a "1.5mm HD" plate and "2mm Rear VTX plates"), but every one of them is **thickness-only card text**, never a footprint — confirming the parent lock's own framing exactly. `_geometry_from_spec` reads only `length_mm`/`width_mm`/`height_mm` (box) or `diameter_mm`/`diameter_in` (disk); it does not and today cannot read `wheelbase_mm`, `body_length_mm`/`body_width_mm`, or any `plates[].thickness_mm` — confirmed by direct inspection, so no frame anywhere in the catalog (including `iflight_xl7_v4_7in`, which already has a real cited `body_length_mm`/`body_width_mm: 202/202` from a different manufacturer's page) currently produces a 3D box. **Recommendation: B0 — leave the frame-box gap open for Rooster.** No cited page supplies a usable L×W for this SKU, and stitching `wheelbase_mm` or any plate thickness into an invented footprint is exactly the fabrication this investigation was written to rule out. A narrow, non-geometric B1 (capturing GetFPV's two extra named plates as additional curated `plates[]` thickness-only entries — text, no box) is available as an optional side Buy if the Engineer wants it, but it does not unlock a 3D solid either.

---

## A. What 3D would need

| Candidate physical referent | Keys `_geometry_from_spec` would need | Cited on any page checked? |
|---|---|---|
| Main Plate as its own box (a named, single carbon plate) | `length_mm` + `width_mm` + `height_mm` (thickness) | **Thickness only** (4mm, both pages) — no L×W for the Main Plate or any other named plate on either page |
| Whole-airframe axis-aligned bounding box | `body_length_mm` + `body_width_mm` + some height (e.g. "Max Stack Height") | **No footprint at all** on either page for Rooster. A real height number exists (Armattan: "Max Stack Height: 22mm") but has no L×W to pair with |
| Wheelbase-derived footprint (`wheelbase_mm` reused as L/W) | N/A — this is not a real footprint, just motor-to-motor spacing | Explicitly **rejected**: `wheelbase_mm` (230mm) is a diagonal motor-to-motor distance, not a plate or body dimension; using it as L or W would fabricate a shape the pages never describe |
| Compressed-X named silhouette (a polygon, not a rectangle) | Would require a non-box glyph type that doesn't exist in this system (`_geometry_from_spec` only emits `box`/`disk`) | Not applicable — out of scope regardless of sourcing, since no such glyph type is locked/authorized |

**None of the four candidate referents has a complete, cited box triple for the Rooster.** The one frame in the catalog that *does* have a cited footprint (`iflight_xl7_v4_7in`, `body_length_mm`/`body_width_mm: 202/202` from `fpv24.com`'s "Technical Data" section) still produces **no box today**, because (a) `_geometry_from_spec` reads `length_mm`/`width_mm`, not `body_length_mm`/`body_width_mm` — a deliberate, already-documented naming split (per `FrameSpec`'s own docstring: "never a full box glyph input alone") — and (b) that row has no accompanying height figure either. This confirms Locked Stance #3 by direct code inspection, not assumption.

---

## B. Armattan live quotes (re-fetched 2026-09-09, `https://armattanquads.com/products/rooster-1`)

Verbatim, from the page's own "Specification" table:

> "Frame Weight — approx 125 grams"
> "Motor to Motor — 230mm @ 5in, 253mm @ 6in"
> "Frame Shape — Compressed X"
> "Main Plate Thickness — 4mm"
> "Arm Thickness — 4mm"
> "Center Stack Mount — 30.5mm"
> "FPV Camera Mount — 28.5mm (Swift v2, Arrow v3, etc)"
> "Max Stack Height — 22mm"

**Footprint: NO.** The page states no plate dimension beyond thickness, no body/overall dimensions, no bounding box, no footprint measurement of any kind. "Max Stack Height: 22mm" is a real, citable number **not currently in the catalog row** — it is a Z-axis (stack) figure, not paired with any L×W, so it cannot complete a box on its own.

---

## C. GetFPV quotes

**Live fetch of `https://www.getfpv.com/armattan-rooster-5-fpv-frame.html` returned HTTP 403** — a Cloudflare bot-challenge page ("Just a moment..."), confirmed independently via both the `WebFetch` tool and a direct `curl` with a standard browser user-agent. This is a genuine access block, not missing/thin content (per Locked Stance #6: reporting this, not inventing the HTML).

To answer the governing question (footprint vs. thickness vs. kit extras) without inventing text, I retrieved an **archived snapshot of the same GetFPV listing via web.archive.org (captured 2023-10-29)** — explicitly **not** a live 2026 fetch of the current page; flagged here as a distinct evidence class from both `live_fetch` and `engineer_provided`. Verbatim from that archived page's own "Specification" and "Includes" sections:

> "Frame Weight — approx 125 grams"
> "Motor to Motor — 230mm @ 5in, 253mm @ 6in"
> "Frame Shape — Compressed X" ... "Main Plate Thickness — 4mm" "Arm Thickness — 4mm"
> "Hardware — Stainless Steel Bolts" "Titanium Cage" "Aluminum Standoffs"
> "Motor Mount Pattern — 22xx"
> "Center Stack Mount — 30.5mm" "FPV Camera Mount — 28.5mm (Sw[ift v2]...)"
> Includes: "1x 2mm Top (LiPo) plate", "1x 1.5mm HD Ca[mera/Cage] ...plate" [string truncated by page markup at fetch time], "1x 1.5mm Small front (top) plate", "1x 1.5mm Small rear (top) plate", "**1x 2mm Rear VTX plates (Standard and TBS)**", "1x 4mm Main plate", "4x 4mm Arms - 5 inch or 6 inch", plus bolt/nut/nylon-standoff hardware counts.

This confirms the parent lock's own framing exactly: this GetFPV listing is effectively a **republication of Armattan's own spec sheet**, word-for-word identical on every field both pages share. Its "richer than Armattan" quality is real but is entirely in the **Includes kit list**, not in any new dimension type:

**Footprint: NO** — the archived page states no plate/body L×W or bounding box anywhere, same as Armattan's own page.

**Kit extras, classified:**

| Item | Thickness stated | Currently in catalog `plates[]`? | Box-eligible? |
|---|---|---|---|
| Top (LiPo) plate, 2mm | Yes | Yes (already seeded) | No — thickness only |
| Small front (top) plate, 1.5mm | Yes | Yes (already seeded) | No |
| Small rear (top) plate, 1.5mm | Yes | Yes (already seeded) | No |
| Main plate, 4mm | Yes | Yes (already seeded) | No |
| **"HD Ca[mera/Cage]..." plate, 1.5mm** | Yes (thickness only; exact label truncated by page markup) | **No — not in current seed** | No — thickness only |
| **Rear VTX plates (Standard and TBS), 2mm** | Yes | **No — not in current seed** | No — thickness only |
| Titanium camera-cage braces, standoffs, bolts/nuts | N/A (hardware, no plate-style thickness) | Partially (`cage_material`/`standoff_material` scalars) | No — never a footprint source, out of scope regardless |

Every "extra" item is **card-only** (a thickness/material fact, same class as the four plates already seeded) — none is box-eligible, because none states a length or width for that plate.

---

## D. Honest Buys (ranked)

1. **B0 — leave the frame-box gap open for `armattan_rooster_5in`.** No page checked (Armattan's own current live page, or GetFPV's archived-but-content-identical listing) states any footprint number for this SKU. Fabricating one from `wheelbase_mm` (a different physical fact — motor-to-motor spacing, not a plate/body dimension) would repeat exactly the mistake this investigation was written to prevent. This is the **recommended default lean**.
2. **Optional, narrow B1 (text-only, does not unlock geometry)**: extend the existing curated `plates[]` list on `armattan_rooster_5in` with the two additional named plates GetFPV's fuller kit copy states ("HD [Camera/Cage] plate" ~1.5mm — exact label needs a clean, non-truncated re-read before seeding; "Rear VTX plates (Standard and TBS)" 2mm) plus Armattan's own cited "Max Stack Height: 22mm" as a new scalar (a real, height-only fact with no matching L×W — same "representar text only" class as the existing plate thicknesses). This would make the card's Included-kit listing as complete as GetFPV's own copy, but produces **zero** change to `_geometry_from_spec`'s output — still no box, since none of these are footprint numbers.
3. **Engineer-declared L×W (`source: "declared"`, not `"verified"`/cited)** — the one path that *could* produce a box this cycle, but only if the Engineer supplies an actual measured or CAD-sourced number (e.g. "I measured/modeled the Main Plate at N×M mm") rather than Claude inferring or estimating one. This is explicitly **not** something this investigation (or any future IC) can decide unilaterally — Locked Stance #1 forbids inventing mm even under a plausible-sounding derivation, and the "declared" provenance tag exists precisely to keep such a number honestly distinguished from a cited manufacturer fact.
4. **Defer indefinitely** — wait for Armattan (or any retailer) to publish an actual dimensioned drawing or footprint spec for the Rooster. None exists today on any page checked.

**Default lean: B0.** Item 2 is worth doing only if the Engineer specifically wants the card's Included-kit text to match GetFPV's fuller copy — it is a pure text-completeness Buy, unrelated to unlocking a 3D box, and should not be conflated with "progress toward a frame solid."

---

## E. Explicitly not this investigation

A GetFPV pass over all 17 propeller/helix SKUs · adding a new "Dinoblades" or any other new frame/part SKU · a motor cylinder · STEP import · `"cabe"`/fit verification · an in-product HTML scraper or automated crawler of GetFPV · treating the wayback-machine snapshot as a live 2026 fetch (it is explicitly flagged as an archived, access-of-last-resort source, not equivalent evidence to `live_fetch`) · seeding `wheelbase_mm` as a footprint value · any `src/`/library edit (none made — this is a report only) · version bump (none made, `pyproject.toml` unchanged).
