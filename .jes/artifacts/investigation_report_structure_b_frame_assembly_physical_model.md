# Investigation Report — Structure B Frame Assembly Physical Model

**Project:** Jarvis
**Date:** 2026-09-05
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_b_frame_assembly_physical_model.md](investigation_contract_structure_b_frame_assembly_physical_model.md)
**Checkpoint:** `v0.3.6`; live suite **2286**
**Status:** CLOSED — Engineer Buy locked → IC READY  
**Review:** [investigation_review_structure_b_frame_assembly_physical_model.md](investigation_review_structure_b_frame_assembly_physical_model.md)  
**IC:** [implementation_contract_structure_b_frame_assembly_physical_model.md](implementation_contract_structure_b_frame_assembly_physical_model.md)

**Not an Implementation Contract. No `src/` edits made.** This report answers the governing questions with live-code and live-source evidence and names one recommended Buy; it does not implement anything.

**Fase 1 graph is baseline, not greenfield.** Node types `frame`/`frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff`, the `parent_key` edge convention, the `└` BOM display convention, and the arms-only `thickness_mm` field are all treated as fixed, shipped product throughout this report (closed @ suite 2229 and 2286 respectively) — the question answered is strictly whether/how the *next* honest fact (plate thickness, and by extension "what does a frame assembly generally look like") fits the existing model, or requires it to change shape first.

---

## Executive summary

**Plate thickness is not a valid next IC on its own. Plate role typing is a prerequisite**, proven directly from the same four seed rows already in the repository — re-fetched live this session, not reused from an older summary. Every row that states any plate thickness at all states **two or three different values for different named plates on the same frame** (§B7 below has the exact quotes). A single scalar `frame_plate.thickness_mm` cannot hold more than one number; forcing one in would silently discard a real, sourced, distinct fact the manufacturer states — the exact same "one node, one value, can't hold two distinct materials" problem the parts-graph investigation already solved for `material` by splitting `frame` into `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff` instead of keeping one `frame.material` scalar. This report recommends solving the recurrence the same way: split multi-plate frames across more than one plate node, rather than widen `frame_plate` with a thickness field it cannot honestly represent.

**Recommended Buy: B2** — schema IC introducing plate multiplicity (not a fixed cross-manufacturer role taxonomy — see §B7 for why that's rejected) as a **mechanical extension of the existing node-per-part-type pattern**, still M0, still no MEASURE, no new subsystem. Full justification in §E.

---

## A. Know — baseline map

### A1. What a frame assembly can already represent today

- **Root** (`components["frame"]`, `ComponentSpec`, `action_schema.py:143-171`): `mass_kg`, `material`, `size_class_inch` (Structure A), `configuration`, `wheelbase_mm` (Structure B Fase 1) — all `PropertyValue` (`action_schema.py:123-127`, a flat `{value, unit, confidence, source}` scalar). `catalog_ref: CatalogRef | None` for identity. `ComponentSpec.parent_key: str | None = None` (`action_schema.py:164-171`) is the sole nesting primitive — a child declares itself a child by pointing its own dict key's spec at the parent's key; there is no reverse list on the parent.
- **Part children** (`components["frame_arm"|"frame_plate"|"frame_cage"|"frame_standoff"]`, each `parent_key="frame"`): `count` (int), `material` (str), and — **arm only**, added this week (suite 2286) — `thickness_mm` (float, unit `"mm"`). `FRAME_ARM_KEY`/`FRAME_PLATE_KEY`/`FRAME_CAGE_KEY`/`FRAME_STANDOFF_KEY` (`domains/aerial.py:341-344`) are the exact four locked dict keys; there is no fifth key and no mechanism today for two frames of the same type to coexist (e.g. two plates) — one dict key per type, full stop.
- **Catalog seed** (`library/frames/_datos.json` + `FrameSpec`, `library.py:148-183`): flat scalar fields per part type — `arm_count`, `arm_material`, `arm_thickness_mm`, `plate_count`, `plate_material`, `cage_material`, `standoff_count`, `standoff_material`. One value per field, no list, no per-instance nesting anywhere in `FrameSpec`.
- **BOM**: `_frame_part_sublines` (`project_closure.py:767-796`) iterates the fixed `_FRAME_PART_ORDER` tuple (`project_closure.py:758-764`, derived from `_FRAME_PART_LABELS`'s four keys) and renders at most **one line per part type** — `└ arm ×4 — fibra de carbono, 4mm`. There is no way today to render two distinct `plate` lines even if two distinct plate facts existed, because there is only one `frame_plate` dict key to read from.
- **Completeness**: `_structure_part_completeness` (`domains/aerial.py:465-476`) — `"high"` the instant `count` or `material` is present on a part child; independent of `_frame_completeness` (root-only), never feeds `Structure PASS`.
- **Free-text**: `_PART_TYPE_MAP` (`domains/aerial.py:346-361`) maps aliases (`brazo`/`placa`/`jaula`/`standoff`/…) to exactly the same four locked keys; `_props_from_part_clause` (`domains/aerial.py:389-415`) extracts `count`/`material`/(arm-only)`thickness_mm` per matched clause.

### A2. What it cannot represent

- **More than one physically distinct plate, arm-set, or cage per frame** — the dict-key model is one node per *type*, not per *instance* or per *named role*. A frame whose manufacturer states a bottom plate and a top plate at different thicknesses has no second slot to put the second number in.
- **Any field beyond `count`/`material`/(arm)`thickness_mm`** — no dimensions (length/width/height), no per-part mass, no hardware (screws/nuts), no part-level `catalog_ref` (per-part catalog rows don't exist), no free-text `role`/`label` string on any part.
- **A distinction between "the one plate this frame has" and "one of several plates this frame has"** — today's `frame_plate` node is silently ambiguous between those two cases; nothing in the schema flags which one applies.

### A3. How catalog projection and free-text create/skip children

- **Catalog** (`catalog_bind.py:297-355`, `frame_part_specs_from_catalog`): the inner `_part` helper (`catalog_bind.py:321-…`) creates a child **iff** `count`, `material`, or (arm only) `thickness_mm` is non-`None` on the `FrameSpec`; otherwise the key is simply absent from the returned dict — never a stub. Exactly one call per locked key (`catalog_bind.py:352-355`), so exactly zero or one node per type, deterministically.
- **Free-text** (`aerial.py:416-…`, `extract_all_frame_part_properties`): one entry per matched alias-key in a comma/`y`/`and`-split clause list; **longest alias wins per key** — meaning if a single free-text message named two plates by different words that both map to `FRAME_PLATE_KEY` (e.g. "placa superior 2mm, placa inferior 2.5mm"), only the **last-processed matching clause survives** in the returned dict (`by_key` is a plain dict keyed by the locked type key, so a second clause for the same key overwrites, it does not merge or accumulate two entries) — confirmed by reading `aerial.py:416-…`'s `by_key: dict[str, tuple[int, dict[str, PropertyValue]]]` structure, keyed by the four-key enum, not by an open key space. **This is a live, already-present asymmetry**: catalog seed data cannot express two plates at all (flat scalar fields), and free-text can *name* two plate clauses but the extractor silently keeps only one. Neither path is "broken" against its own current contract (no test claims two-plate free-text is supported) — but it is direct evidence the *current* model was never asked to hold two instances of the same type, not evidence that it *can*.

---

## B. Target model (minimum generalizable)

### B4. Proposed smallest coherent model

**Do not add a `thickness_mm` field to `frame_plate` as shipped.** Instead, generalize the *existing* "one node per declared physical thing" pattern from "one node per **part type**" to "one node per **distinctly-thicknessed/named plate instance**," using the same mechanism already proven for material (splitting `frame` into typed children) — recursively applied one level deeper, only for the one part type (`plate`) that the evidence (§B7) shows actually needs it. `frame_arm`/`frame_cage`/`frame_standoff` show **zero** sourced evidence of needing a second instance (every seed row states exactly one arm thickness value, one cage material, one standoff material) — so this generalization is **not** proposed for those three types; it is scoped exactly to where the evidence points.

Concretely: keep `frame_plate` as the default/single-plate key (fully backward compatible — every existing test and seed usage of `frame_plate` for `material`/`count` is untouched). When a source or a free-text message states **more than one** distinctly-valued plate, use additional sibling keys under the same `parent_key="frame"` (e.g. an ordinal suffix — `frame_plate_2`, `frame_plate_3` — not a semantic role name; see §B7 for why a semantic name is rejected). Each such node carries the same property shape any part node already has (`material`, `count` if meaningful, `thickness_mm`) **plus one new optional property, `label`** — a short **verbatim-from-source** string (e.g. `"bottom plate"`, `"placa superior"`) for display attribution only, never matched against a closed vocabulary, never cross-checked against `configuration` or against any other plate's label.

This requires:
- **No new node *type*** (still `component_type="structure_part"`, still `parent_key="frame"`) — only a small, bounded widening of which *dict keys* are recognized as frame-part children (a mechanical change to `_FRAME_PART_ORDER`/`_FRAME_PART_LABELS`/`_PART_TYPE_MAP`'s consumers, not a new subsystem).
- **One genuinely new schema shape**: `FrameSpec` needs to hold *more than one* plate's worth of seed data per row, which its current flat-scalar fields (`plate_count`, `plate_material`) cannot. The smallest change is an optional `plates: list[PlateSeed] | None = None` (a small frozen record — `label`, `thickness_mm`, `material` — mirroring `PropellerSpec`/`MotorSpec`'s existing flat-record style) rather than yet more flat `plate_2_material`/`plate_3_material` scalar fields (unbounded, uglier, and still forces choosing a fixed slot count). This is the one item in this report that is a genuinely new *shape* in `library.py` (every existing catalog dataclass there is flat scalars only) — flagged explicitly as the biggest single schema-impact decision in this Buy, not hidden inside "mechanical."
- **No change** to `ComponentSpec`, `PropertyValue`, `ProjectState`, `DesignProperties`, `BLOCK_TO_COMPONENTS`, `_frame_completeness`, `_structure_part_completeness`'s own high/low rule (still: `count` or `material` present ⇒ `"high"`; a `label`/`thickness_mm`-only plate node stays `"low"`, exactly mirroring the arm-thickness-only precedent already shipped and tested at suite 2286).

### B5. In / out / later, per part type

| Part type | Verdict | Reason |
|---|---|---|
| **Plate — multiplicity + `label` + `thickness_mm`** | **IN (this Buy)** | Only type with direct, repeated, multi-value source evidence (§B7) that a single scalar cannot honestly hold. |
| Arm — `thickness_mm` | **Already shipped** (suite 2286) — no change proposed | Every seed row states exactly one arm thickness value; no multiplicity evidence found on any of the four re-fetched pages. |
| Cage — any new field | **OUT** | Only `cage_material` is ever stated (Armattan: "titanium cage"); no thickness/dimension/count fact found on any of the four source pages, this session or the prior enrichment investigation. |
| Standoff — any new field | **OUT** | Same as cage — only material (Armattan: "aluminum standoffs") is ever stated. |
| Hardware (screws, etc.) | **OUT, unchanged** | No source data on any of the four pages; contract's own locked stance and the parts-graph investigation's §2 already closed this as no-proven-need. |
| Per-instance position nodes (`arm_front_left`, etc.) | **OUT, unchanged** | Rejected in the parts-graph investigation (borders MEASURE via implied layout); this report's plate-multiplicity proposal is explicitly **not** this — it is instance-by-*declared-fact*, not instance-by-*position* (see §B7's rejection of a role taxonomy for the same reasoning applied the other direction). |

### B6. Shared physical property set

| Property | Common schema? | Notes |
|---|---|---|
| `material` | Yes — already shared across all four types | No change. |
| `count` | Yes — already shared (arm/plate/standoff; cage has none by design, matches "cage is described once, not counted" in every source) | No change. |
| `thickness_mm` | Yes, but **only meaningful where source data exists** — today arm (shipped), proposed plate (this report) | Not proposed for cage/standoff — would be fabricated (no source states it). |
| `label` (free string, verbatim from source) | **New, plate-only in this Buy** | Purely an attribution string, never matched/validated/cross-referenced — see §B7 for why it must stay free-text, not closed-vocabulary. |
| `mass_kg` (per part) | **Stays out** | Zero source support on any of the four pages, reconfirmed this session (see §C8). |
| length/width/dims | **Stays out** | Not stated as a distinct fact from `wheelbase_mm` (root) on any page; would border MEASURE (a length claim invites a fit/clearance inference this investigation is explicitly told not to open). |

### B7. Plate thickness vs. plate role typing — the Engineer's decision hinge

**Direct evidence, re-fetched live this session from each seed row's own `source_url`** (not reused from the prior enrichment investigation's summary):

| SKU | Source quote (verbatim) | Distinct values on one page |
|---|---|---|
| `tbs_source_one_v5_5in` (racedayquads.com) | "Top Plate: 2mm" / "Bottom Plate: 2.5mm" / "Middle Plate: 2mm" | **2 distinct values** (2mm top+middle, 2.5mm bottom) across 3 named plates |
| `tbs_source_one_v5_1_7in_dc` (progressiverc.com) | "2.5mm bottom plate, 2mm top/middle plate, 6mm arms" | **2 distinct plate values** (2.5mm bottom, 2mm top/middle) |
| `iflight_xl7_v4_7in` (fpv24.com) | "2mm upper, upper and lower plate" / "1,5mm vertical side plates" | **2 distinct values** (2mm upper/lower, 1.5mm vertical side) |
| `armattan_rooster_5in` (armattanquads.com) | "Main Plate Thickness: 4mm" / "2mm Top (LiPo) plate" / "1.5mm Small front (top) plate" / "1.5mm Small rear (top) plate" | **3 distinct values** across 4 named plates (4mm main, 2mm LiPo, 1.5mm front/rear) |

**All four rows — 100% of the current seed — state at least two different plate-thickness values on the same page.** There is no seed row where a single `frame_plate.thickness_mm` scalar would be honest; every single one would require silently picking one value and discarding at least one other sourced, real fact.

**Explicit answer: plate role typing (or, more precisely, plate *multiplicity*) is a prerequisite. Plate thickness as a bare field on the existing single `frame_plate` key is not a valid next IC** — it fails the same honesty bar that already forced the material split. This directly disproves Buy option B3 ("extend props only… without role split — only if you prove roles are unnecessary"): the evidence proves the opposite.

**One additional, load-bearing finding that changes the shape of the "role typing" answer from what the contract's B2 option sketches:** the four manufacturers use **no shared vocabulary** for plate roles — TBS says "top/middle/bottom," iFlight says "upper/lower" + "vertical side," Armattan says "main" + "top (LiPo)" + "small front (top)" + "small rear (top)." There is no stated fact anywhere that TBS's "bottom plate" is the same *kind* of plate as Armattan's "main plate" (both happen to be the thickest/primary structural plate, but no source says so explicitly — that would be an inferred equivalence, not a declared one). **Building a fixed, closed cross-manufacturer role enum (e.g. locked keys `frame_plate_top`/`frame_plate_bottom`/`frame_plate_main`) would require Jarvis to invent that equivalence** — the same class of forbidden inference as `arm_count`↔`motor_count`, just recurring at the ontology level instead of the value level. **Recommendation: reject a semantic role taxonomy. Use ordinal sibling keys (`frame_plate`, `frame_plate_2`, `frame_plate_3`, …) plus a free-text `label` property that quotes the source's own words verbatim**, never interpreted, never compared across nodes or across SKUs. This is the "minimum generalizable" answer: it works for any manufacturer's own naming without Jarvis ever deciding what a name *means*.

---

## C. Mass & provenance

### C8. M0 reconfirmed for any proposed part `mass_kg`

No part `mass_kg` is proposed by this report (§B6). Re-checked all four source pages live this session for a per-plate or per-arm mass figure: **none state one** — Armattan names three materials (carbon/titanium/aluminum) and four plate thicknesses but never a gram figure per part; the two TBS pages and the iFlight page likewise give thickness/material only, never mass, for any individual part. `set_frame_material` (`component_writers.py`, the frame-root writer) and `calculation_engine.py`'s `structure_mass_override_kg` read path remain the sole mass authority, confirmed unchanged and untouched by this investigation (no `src/` edit made). **M0 stands, unconditionally, because the precondition for even considering M1 (per-part mass existing at all) still does not exist in any source.**

### C9. Claims allowed vs. forbidden if part masses were ever declared-only (hypothetical, not proposed)

Restated from the parent additive-enrichment investigation (§C2), unchanged by this report: root mass and any hypothetical Σ-of-parts must always be presented as **two independently declared facts**, never resolved into one, and Jarvis must never claim recalculating a part changes system mass. This report adds no new claim here because it proposes no mass field — cited only so a future reader doesn't need to re-derive it.

---

## D. Claims / PASS *

### D10. Claim matrix — composed assembly declared vs. forbidden

| Sentence | Allowed? | Why |
|---|---|---|
| "Frame declara 2 placas: placa 1 — bottom plate, 2.5mm; placa 2 — top/middle plate, 2mm (fuente: catálogo)" | ✅ Allowed | Both values sourced verbatim, both attributed, neither claims equivalence to any other manufacturer's naming. |
| "Placa principal: 4mm (fuente: catálogo)" (Armattan, quoting its own "Main Plate") | ✅ Allowed | `label` quotes the source's own designation; no invented "main" judgment for a frame whose source doesn't use that word. |
| "La placa inferior de TBS es la placa principal de Armattan" | ✗ Forbidden | Invents a cross-manufacturer semantic equivalence no source states — exactly what §B7 rejects. |
| "El chasis tiene 2 placas estructurales redundantes" | ✗ Forbidden | "Redundant"/"structural" implies a load-bearing engineering judgment; Jarvis states thickness and count, never structural role or adequacy. |
| "Grosor total del chasis: 6.5mm" (sum of two plate thicknesses) | ✗ Forbidden | Summing two independent, non-stacked thickness values is a fabricated derived quantity — no source states plates are stacked/adjacent; this is a MEASURE-adjacent inference. |
| "Placa 2mm — compatible con el stack FC declarado" | ✗ Forbidden | Invents a fit/clearance relationship between an unrelated component (FC stack height) and this frame's plate — exactly the class of claim the arms-only B2 IC already forbade for wheelbase/stack. |

### D11. Structure PASS * footnote — recommendation: unchanged

Current footnote (`adapters/cli/main.py:147`): `"* Structure: identidad / clase nivel A — sin geometría de chasis"`. **This report's own default lean, per the contract's own instruction, is to leave it unchanged** unless an *implemented* model justifies otherwise — no model has been implemented by this investigation. Substantively: plate multiplicity/labels are exactly the same epistemic category the footnote already covers ("identity" facts, not geometry/fit) — a second declared plate is no more a geometry claim than the first one was. **No footnote change is proposed.** If Engineer wants to preemptively broaden the footnote's wording to explicitly cover "composed assembly" language ahead of an IC, that is a documentation-only B1-shaped decision independent of this report's schema recommendation — named here as optional, not recommended as necessary.

---

## E. Buy

### Recommended: **B2 — schema IC: plate multiplicity (ordinal siblings + free-text `label`), still M0, still no MEASURE, no role taxonomy**

**Justification:**
- Directly evidenced (§B7): 4/4 seed rows need it to state plate thickness honestly at all; 0/4 need it for arm/cage/standoff.
- Smallest schema footprint that actually solves the problem: reuses `ComponentSpec`/`parent_key`/`upsert_frame_part`/`_structure_part_completeness`/BOM machinery verbatim (all four already generic over dict keys and property dicts) — the only genuinely new pieces are (a) a bounded list-of-flat-records field on `FrameSpec` for seed multiplicity, and (b) widening `_FRAME_PART_ORDER`-style consumers from a fixed 4-tuple to "4 fixed keys + N ordinal plate siblings." Neither is a new subsystem, a new node *type*, or a change to any existing PASS/completeness/architecture-progress predicate.
- Explicitly **rejects** inventing a cross-manufacturer role taxonomy (the literal reading of the contract's own B2 phrasing, "plate role typing") because the evidence shows that would require an inference no source supports — this is a deliberate, evidenced deviation from the contract's suggested shape, not an oversight.

**Rejected:**
- **B0** (no IC, doc only) — would leave the same already-sourced, zero-risk facts (2-3 plate thicknesses per row, on every one of the four rows) undocumented for no honesty reason, the same objection the prior enrichment investigation raised against deferring arm thickness.
- **B1** (docs/claim lock only) — the plate-multiplicity fact is representable at near-zero risk (same profile as `wheelbase_mm`/arm `thickness_mm` before it); documenting it without representing it undersells real, sourced knowledge Jarvis could honestly hold.
- **B3** (extend `frame_plate` in place, no split) — **directly disproven** by §B7's evidence; every row needs at least 2 values, one scalar cannot hold them.
- **B4** (typing now, mass/hardware later) — this report already recommends *no* mass/hardware in the same breath (§B5/§C8 find zero source support for either), so B4's phased split collapses into B2 with an empty "later" bucket; naming it separately would imply mass/hardware are coming next, which nothing in this investigation supports.

---

## F. Non-goals confirmed

- **MEASURE / CAD / FEA / fit / clearance / mounts** — not opened. `label` is a verbatim-quoted identity string, never a position, dimension, or fit claim. No two plates are ever claimed to be "stacked" or spatially related (§D10's forbidden-sum example exists precisely to close this off).
- **Σ→physics** — no part `mass_kg` proposed (§C8); M0 unconditionally reconfirmed.
- **`arm_count`↔`motor_count` gate** — untouched; this report's proposal has zero relationship to motor count.
- **ESC/Control catalog, System-level Optimization** — untouched, out of scope, not referenced by any proposed change.
- **Implementation** — no `src/` file was edited to produce this report; all line citations are read-only.
- **A closed cross-manufacturer role vocabulary** — explicitly rejected in §B7, not merely deferred; naming it here so a future reader doesn't mistake "ordinal + label" for a stepping-stone toward a role enum.

---

## G. IC skeleton (Buy = B2 — not an Implementation Contract, ≤25 lines)

- **Files:** `src/jarvis/knowledge/library.py` — new frozen `PlateSeed` record (`label: str | None`, `thickness_mm: float | None`, `material: str | None`); `FrameSpec.plates: list[PlateSeed] | None = None` (additive, existing `plate_count`/`plate_material` scalars untouched, kept as the single-plate fallback). `library/frames/_datos.json` — populate `plates` for all four rows from the quotes in §B7 (`source_note` updated per row). `src/jarvis/core/catalog_bind.py` — `frame_part_specs_from_catalog` emits `frame_plate` (first/only plate, backward compatible) plus `frame_plate_2`, `frame_plate_3`, … for `spec.plates[1:]`, each with `label`/`thickness_mm`/`material` as available. `src/jarvis/domains/aerial.py` — free-text stays single-plate only in this IC (no ordinal free-text parsing — out of scope, named as its own future debt) unless Engineer explicitly asks for it. `src/jarvis/core/project_closure.py` — `_frame_part_sublines` iterates `frame_plate*` keys present in `components` (not just the fixed 4-tuple) so every declared plate sibling renders its own `└` line with its `label` when set.
- **Behavior change:** catalog-bound multi-plate frames (all four current seed rows) show 2-3 plate BOM lines instead of one (or, for TBS/iFlight, one where they previously showed zero — same "arm-thickness-only regression target" pattern as suite 2286). Free-text unaffected. Completeness/PASS/architecture-progress: regression-tested unchanged.
- **Tests:** seed loader parses/omits `plates`; catalog projection emits N plate siblings per row matching §B7's quoted values; BOM renders each with `label`; the mandatory twin (`_frame_completeness`/`_structure_evidence`/ERF verdict byte-identical with vs without plate siblings, mirroring the arm-thickness B2 T6 pattern).
- **Forbidden:** any closed role-name enum; any per-plate `mass_kg`; any sum of plate thicknesses; any free-text ordinal parsing (deferred, name as debt only); any `_structure_part_completeness`/PASS/`BLOCK_TO_COMPONENTS` change; version bump.
