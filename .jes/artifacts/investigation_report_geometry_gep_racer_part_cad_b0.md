# Investigation Report — GEP-Racer part envelopes from CAD (B0 — gap holds)

Status: **CLOSED B0 — no authentic CAD found, no code changed**
Parent: `implementation_contract_geometry_gep_racer_part_cad_b1.md` (§0 Phase 0)
Baseline: package `0.4.1` (unchanged) · suite `2723` (unchanged) · UI `83` (unchanged)

## Task

Per the IC's own §0/§1 Phase 0 instructions: search for authentic
OEM/licensed/manufacturer-linked CAD (STEP/STL/DXF) for the GEP-Racer
frame's plates, arms, and standoff, to fill the three UNKNOWN dimensions
(plate L×W, arm L×W, standoff outer Ø/section) the Engineer flagged on
2026-09-11. Phase 0 needs no ★ to search, only to seed from a found
file. This report covers Phase 0 only — no CAD was found, so Phase 1
(measure + declare) never started.

## What was checked

1. **`https://geprc.com/downloads/racer/`** (re-fetched) — confirmed
   empty for CAD purposes. Contains only: a drone manual ("in
   development"), the TAKER F722 SE/E55A SE FC manual (PDF), and three
   CLI `.txt` config files (TBS/ELRS/SBUS receiver types). No STEP/STL/
   DXF. The page's own FAQ states verbatim: "There is nothing for the
   time being, you can submit FAQs to us." — matches the Engineer's own
   2026-09-11 pre-check exactly.
2. **`https://geprc.com/product/gep-racer-frame-parts/`** (re-fetched) —
   the parts product page lists the part names (Top Plate, Bottom Plate,
   Arm Plate, Silver/Red Aluminum Part, Fin, Antenna Mount, Camera Mount,
   Battery Anti-slip Pad, Aluminum Pillar) but offers zero technical
   downloads beyond product photography — no CAD link of any kind.
3. **Web search** ("GEPRC GEP-Racer frame STEP STL CAD download") —
   surfaced CAD models on GrabCAD, Printables, Cults3D, and MakerWorld,
   but every hit that names a specific GEPRC frame is for the **Mark 4**
   or **Mark 5** family (e.g. "GEPRC Mark 4 Frame by Riley Entropy",
   GrabCAD's "GEPRC Mark 4 Frame (5, 6, 7, 8, 9 and 10-inch)") — a
   **different product line**, not the GEP-Racer. No search result named
   "GEP-Racer" specifically.
4. **`https://grabcad.com/library/tag/geprc`** — attempted directly;
   returned HTTP 403 (GrabCAD blocks unauthenticated fetches). Not
   pursued further via an authenticated path, because the search results
   above already established that GrabCAD's GEPRC-tagged content is
   Mark 4/Mark 5 (wrong product) and, independently of that, every named
   uploader on these community sites (e.g. "Riley Entropy") is an
   individual hobbyist, not GEPRC or a licensed distributor — this fails
   lock #3's authenticity bar ("Only files Engineer accepts as OEM /
   licensed / manufacturer-linked. Community camera-mount STLs ≠ frame
   plates") on provenance grounds alone, independent of the 403.
5. **Engineer asked directly** (via `AskUserQuestion`, per the IC's own
   step "Ask Engineer if they hold a private OEM pack"): does the
   Engineer hold a private OEM/licensed CAD pack not on GEPRC's public
   site? **Answer: No — close this as B0.**

## Outcome

No authentic OEM/licensed/manufacturer-linked CAD exists for the
GEP-Racer's plates, arms, or standoff, as of this 2026-09-11 diligent
search. Per the IC's own §0 lock #7 ("If §0.1 bag stays empty after
search → close A as B0 gap → Engineer opens Option B (caliper) — no
invent"), **Option A (CAD) is closed as a B0 gap**. No dimension was
estimated, guessed, or back-derived from the #4g P1 catalog seed's own
175×173mm body/wheelbase-208mm/standoff-thread facts (the Engineer's own
explicit honesty lock this IC's Parents section names: "do not copy
175×173 onto plates · do not read M3×6×24 as Ø6").

## Files changed

**None.** This was a read-only Phase 0 search. No `library/`, no
`workspace/`, no test file, no schema change. Confirmed via `git status
--short` showing zero diff from this cycle's own work.

## Non-goals honored

- No Yeggi/Printables/GrabCAD community model used as source-of-truth.
- No dimension estimated from wheelbase or from the #4g P1 seed's own
  body/wheelbase numbers.
- No `M3×6×24` thread-length figure misread as a Ø6 outer diameter.
- No `PlateSeed.length_mm`/`width_mm` schema field added.
- No version bump.
- `armattan_rooster_5in` and the #4g P1 seed (a separate, orthogonal IC)
  untouched.

## Next step (handoff, per the IC's own §7)

Option A (CAD) is closed. The Engineer's own next move, per this IC's
own fallback, is to open an **Option B (caliper)** IC — a physical
measurement of a real GEP-Racer unit's plates/arms/standoff, if/when one
is in hand — rather than waiting on CAD that does not exist. `#4g P1`
(the partial catalog seed: body 175×173, wheelbase 208, thicknesses,
H24) remains a separate, already-in-flight IC and is unaffected by this
closure — it can land on its own with the plate/arm L×W and standoff Ø
fields simply left absent, exactly as they are today.
