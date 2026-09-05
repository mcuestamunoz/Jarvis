# Investigation Report — Structure B additive enrichment (mass / part fields)

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_b_additive_enrichment.md](investigation_contract_structure_b_additive_enrichment.md)
**Checkpoint:** tag `v0.3.6`; live tree includes Structure close (2229) + IDLE rebind B2/B3 (2276)
**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer Buy → IC  
**Review:** [investigation_review_structure_b_additive_enrichment.md](investigation_review_structure_b_additive_enrichment.md)  
**IC:** [implementation_contract_structure_b_thickness_arms_b2.md](implementation_contract_structure_b_thickness_arms_b2.md)  
**Buy:** B2 YES · N1 (b) arms-only · M0

**Structure B ontology is not reopened.** Node types (`frame`/`frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff`), `parent_key`, and the display-only BOM `└` convention are treated as fixed, existing product throughout this report — the question answered is strictly what *additional PropertyValue-shaped fields* belong on the nodes that already exist.

Not an Implementation Contract. No `src/` edits, no schema changes. Every per-part fact this report cites as "sourceable" was re-verified this session by fetching the exact `source_url` already in `library/frames/_datos.json` — none reused from an older, unattributed search summary.

---

## A. Know — what Fase 1 already has

**A1. Root fields today** (`ComponentSpec` for `components["frame"]`): `mass_kg`, `material`, `size_class_inch` (Structure A), `configuration`, `wheelbase_mm` (Structure B Fase 1) — all `PropertyValue`, all optional except mass/material feed `_frame_completeness`. `catalog_ref: CatalogRef | None` for identity (Catalog Foundation).

**A2. Part fields today** (`components["frame_arm"|"frame_plate"|"frame_cage"|"frame_standoff"]`, each `parent_key="frame"`): `count` (int) and `material` (str) only — `domains/aerial.py:386-398` (`_props_from_part_clause`, the single extraction function both the catalog-bind projector and the G-N1 free-text path funnel through). `_structure_part_completeness` (`domains/aerial.py:450-461`) grades a part `"high"` the instant either key is present, `"low"` otherwise — **no other field is recognized or extracted anywhere in the codebase today.**

**A3. Physics mass — confirmed root-only, not sum-of-parts** (traced, not assumed): `set_frame_material` (`component_writers.py:119-130`) writes `current_parameters["structure_mass_override_kg"]` from **only** the root spec's own `mass_kg` property. `upsert_frame_part`/`clear_frame_part_children` (`component_writers.py`, Structure B Fase 1 / IDLE rebind B2) never touch `current_parameters` at all — grepped the whole file, confirmed. `calculation_engine.py:196-207` reads `structure_mass_override_kg` as the single structure-mass input to the physics bundle. **No code path anywhere sums `frame_arm`/`frame_plate`/etc. masses into anything** — there is no part `mass_kg` field to sum in the first place (A2). This matches `ENGINEERING_READINESS_VISION.md` §8's own "sum-of-parts mass" debt bullet: it is debt because the field doesn't exist, not because a summing bug exists.

**A4. BOM `└` rendering — exact attribute list, confirmed by reading the function:** `_frame_part_sublines` (`project_closure.py:767-788`) reads **only** `count` and `material` from a part's properties dict; any other key (were one to exist) is silently **not shown** — the function has no fallback/generic property dump. A part declared with only, say, a hypothetical `thickness_mm` and nothing else would render **no line at all** today (the `if not count_bit and not material_bit: continue` guard at `:785-786`).

---

## B. Additive field candidates

**B1. Ranked, with in/out/later and the evidentiary reason:**

| Candidate | Verdict | Reason |
|---|---|---|
| **`thickness_mm`** (on `frame_arm`, `frame_plate`) | **IN — the one candidate with real, sourced support** | Re-verified this session by fetching all four seed rows' own `source_url`: `tbs_source_one_v5_5in` (racedayquads.com) states *"Arm Thickness: 6mm"* + top/bottom/middle plate thicknesses (2mm/2.5mm/2mm); `tbs_source_one_v5_1_7in_dc` (progressiverc.com) states *"2.5mm bottom plate, 2mm top/middle plate, 6mm arms"*; `armattan_rooster_5in` (armattanquads.com) states *"Main Plate Thickness: 4mm"* + *"Arm Thickness: 4mm"*; `iflight_xl7_v4_7in` (fpv24.com) states *"5mm arms"* + *"2mm upper, upper and lower plate"*. **All four rows, both part types, directly on the cited page** — the strongest evidentiary case of any candidate field in this or the prior Structure B investigation. |
| `mass_kg` (per part) | **OUT for now** | Re-checked all four source pages during this and the prior sourcing pass — **zero** state a per-part mass. Armattan's page names three materials (carbon/titanium/aluminum) but never a gram figure per part. Inventing one would violate the contract's own §7 ("no per-part mm/g values absent from catalog source_note/seed"). |
| `length_mm` (arm length specifically) | **OUT** | Not stated on any of the four pages as a distinct fact from `wheelbase_mm` (motor-to-motor distance), which the root already carries. No source to cite. |
| `hardware` as a new node type | **OUT, unchanged from the prior investigation's own conclusion** | No source data, no consumer, and the contract's own locked stance #1 keeps the node-type set closed to the shipped four. |
| Top/bottom plate split (two nodes instead of one `frame_plate`) | **OUT** | Would be a node-type change (forbidden by locked stance #1) for a distinction (`top` vs `bottom` thickness) that can be represented just as honestly as two properties on the single existing `frame_plate` node if ever needed — no new node required even if this were pursued, and it is not proposed here. |

**B2. Catalog seed impact** — direct answer to the contract's Q7: **all four existing rows** can honestly gain `arm_thickness_mm`/`plate_thickness_mm` (or a single generic `thickness_mm` per part node) sourced from their own already-cited page. This is the opposite of the Armattan-only asymmetry the prior investigation found for per-part *material* (only Armattan's page named materials per part) — thickness is the one fact every current seed row states for both `frame_arm` and `frame_plate`. `frame_cage`/`frame_standoff` thickness is **not** stated on any page (cage/standoff are described by material and, for iFlight, a *height* — a different attribute — not a wall thickness) — so a `thickness_mm` field would apply honestly only to `frame_arm`/`frame_plate` in the current seed, not all four part types uniformly.

---

## C. Mass composition rule

**C1. Recommended policy: M0.** Root `mass_kg` stays the sole physics input; part fields (existing `count`/`material`, and the newly-evidenced `thickness_mm`) remain **display-only forever**, never summed, never a second mass authority.

**Why not M1** (Σ shown as informational when all parts have mass): moot given §B1 — no part has a `mass_kg` field at all today, and none is proposed (no source data). M1 would require the very field this report declines to add. Naming M1 as "the fallback if `mass_kg` per part is ever added later" is enough; adopting it now has nothing to activate it.

**Why not M2/M3** (replace or prefer Σ): explicitly rejected, independent of whether the field ever exists. The exact hazard this session's claim-hygiene and parts-graph work fought to close each time it appeared (`arm_count`↔`motor_count`, `configuration`↔part-graph) recurs identically here: a root mass the user declared or a catalog SKU provided, silently superseded by a number computed from parts the user may have declared at a different time, with no clear tie-break rule the contract asks me to invent. **This is the same class of "two authorities disagree" risk, not a new one** — M0 is the only policy consistent with every prior lock in this phase.

**C2. Conflict case (root says 125 g, a hypothetical Σ says 140 g):** under M0, the conflict cannot arise in product terms because there is no Σ to compute (no part mass field exists) — Jarvis may **never** claim a frame's mass is anything other than the root's own declared/catalog value. If a future thread ever adds part mass (against this report's recommendation, or once real seed data exists), the correct claim would be: *"Frame declara {root mass} kg; piezas declaran {Σ} kg combinados — no se recalcula el total del sistema."* — stating both numbers as **independently declared facts**, never resolving them into one, and never in the same clause that implies one "corrects" the other.

**C3. Interaction with G-N1 / IDLE rebind clear-children (B2):** no new hazard found. `clear_frame_part_children` (component_writers.py) already removes every `parent_key=="frame"` child on a catalog re-pick, and G-N1's free-text root+parts path writes count/material only — since no part carries a mass value, there is no additional mass-orphan scenario beyond the material-orphan one the IDLE-reacquisition investigation already named and left as documented debt.

---

## D. Claims matrix

| Sentence | Allowed? |
|---|---|
| "Frame declares 4 carbon arms" (i.e. `frame_arm.count=4`, `frame_arm.material="fibra de carbono"`, both declared) | ✅ Allowed — pure declaration, existing fields |
| "Frame mass is sum of parts (125 g)" | **✗ Forbidden, unconditionally** (M0, §C1) — no such computation exists or is proposed |
| "Arms length 108 mm from catalog" | ✗ Forbidden as stated — no source states arm *length*; only *thickness* is sourced (§B1). The honest sentence is *"Grosor de brazo declarado: 6mm (fuente: catálogo)"* |
| "Arm thickness declared: 6mm (source: catalog)" | ✅ Allowed, once implemented — pure declared fact, same epistemic status as `material`/`wheelbase_mm` |
| "Chassis is structurally adequate" | ✗ Forbidden — confirmed, unchanged from every prior Structure investigation; no strength model exists or is proposed |
| "6mm arms support the declared thrust" | ✗ Forbidden — a thickness value is not a load calculation; stating a relationship between thickness and thrust is exactly the MEASURE wall |
| "Changing arms recalculates system mass" | **Never true under M0** — and M0 is the only policy this report recommends, so this sentence should never be emitted regardless of which part fields exist |

**D confirms:** `Structure PASS *`'s existing footnote (*"identidad / clase nivel A — sin geometría de chasis"*) remains fully honest whether or not `thickness_mm` is ever added — thickness is exactly the same kind of "declared identity fact" the footnote already covers, not a new claim category. No footnote wording change is proposed or needed.

---

## E. Buy

**B2 — narrow: add `thickness_mm` only, on `frame_arm`/`frame_plate` only, display-only, M0 unchanged.**

Justification, directly from the evidence: this is not the generic "B2: optional per-part mass_kg (+ maybe thickness)" the contract sketched — that broader shape is **not** justified (mass has zero source support, per §B1). What **is** justified is the single field that turned out, on direct re-verification, to have full, per-row, per-part-type source support: `thickness_mm`. This is a genuinely additive knowledge gain (a real manufacturer spec Jarvis currently discards) with the same near-zero risk profile as `wheelbase_mm`/`configuration` before it (declared-only, `PropertyValue.source="declared"` always, no consumer beyond display, `_frame_completeness`/`_structure_evidence`/`Structure PASS` untouched).

Rejected:
- **B0/B4** (no IC / defer entirely) — would leave four already-sourced, zero-risk manufacturer facts (arm and plate thickness on every current seed row) undocumented for no honesty or risk reason; unlike the mass/length candidates, there is no "insufficient evidence" reason to defer this one.
- **B1** (docs-only) — the thickness fact is worth actually representing, not just naming in a claim-hygiene doc; it has the same profile as `wheelbase_mm`, which the prior investigation implemented rather than merely documented.
- **B3** (M2 wired into calc) — rejected per §C1; not triggered by anything found here.
- **The broader B2 as originally framed** (mass_kg + thickness together) — rejected; bundling an evidenced field with an unevidenced one would either force fabricating mass data or ship a half-empty schema slot, neither acceptable.

---

## F. Explicit non-goals confirmed

- Structure B ontology (node/edge types, `parent_key`) — **not reopened**, treated as fixed throughout.
- No nested assembly engine, no poses/mounts/clearance, no CAD/FEA.
- No `arm_count`↔`motor_count` gate (unaffected by this report's recommendation — `thickness_mm` has no relationship to any count).
- No `Structure PASS` widening — confirmed unaffected in §A3/§D.
- No IDLE rebind (B2/B3) reopen — cited only for the orphan-clearing cross-check in §C3, not modified.
- No fabricated per-part mass or length data — the two candidates without source support were explicitly declined, not silently invented.
- `frame_cage`/`frame_standoff` thickness — not proposed; no source states it for those two part types today.

---

## G. IC skeleton (Buy = B2, narrow — not an Implementation Contract)

- **Files (illustrative):** `src/jarvis/knowledge/library.py` (`FrameSpec` gains optional `arm_thickness_mm: float | None`, `plate_thickness_mm: float | None`; loader parses, omits when absent); `library/frames/_datos.json` (all four rows gain the two fields, sourced exactly as quoted in §B1, `source_note` updated to mention them); `src/jarvis/core/catalog_bind.py` (`frame_part_specs_from_catalog`'s `_part` helper gains a `thickness_mm` parameter, passed for `frame_arm`/`frame_plate` only); `src/jarvis/domains/aerial.py` (`_props_from_part_clause` gains a `\d+(?:\.\d+)?\s*mm` thickness pattern for free-text parity, keyword-gated the same way `_extract_wheelbase_mm` already is, to avoid colliding with a bare count); `src/jarvis/core/project_closure.py` (`_frame_part_sublines` reads and renders `thickness_mm` when present, e.g. `└ arm ×4 — fibra de carbono, 6mm`).
- **Behavior change:** two new optional, declared-only properties on two of the four part node types; BOM sub-lines gain a thickness suffix when present; nothing else changes.
- **Tests:** seed loader parses/omits the two new `FrameSpec` fields; `frame_part_specs_from_catalog("armattan_rooster_5in")` projects `thickness_mm` on `frame_arm`/`frame_plate`; a TBS/iFlight row projects the same; free-text extraction of a thickness phrase (e.g. `"brazos 6mm"`) sets `frame_arm.thickness_mm`; BOM sub-line renders the new suffix; a regression proving `_frame_completeness`, `_structure_evidence`, and `Structure` ERF verdict are byte-identical with and without the new fields present (same discipline as every prior Fase 1 addition).
- **Forbidden:** `mass_kg` on any part node; any field on `frame_cage`/`frame_standoff` beyond existing `material`; any new node type; any sum-of-parts computation (M0 stays); any `_structure_part_completeness` change that would make thickness *required* (it must stay purely additive, never blocking "high"); any Structure PASS/`_derive_overall` change.
