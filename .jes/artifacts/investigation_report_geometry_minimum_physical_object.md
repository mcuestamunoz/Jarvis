# Investigation Report — Minimum Geometric KNOW for a Physical Catalog Object

**Project:** Jarvis
**Date:** 2026-09-05
**Investigator:** Claude Code
**Contract:** [investigation_contract_geometry_minimum_physical_object.md](investigation_contract_geometry_minimum_physical_object.md)
**Parent lock:** [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
**Checkpoint:** `v0.3.8` / `checkpoint-spatial-board-projector` · Structure CLOSED suite 2294 · live tree B3 slots suite 2310
**Status:** OPEN — for Cursor review → Engineer ★ on Buy

**Not an Implementation Contract. No `src/` edits made.** Every claim cites `file:line` on the live tree or a live-fetched source page (quoted verbatim), re-verified this session.

---

## A. Executive answer

Jarvis already has one real, working precedent for "declared geometry as KNOW": `PropellerSpec.diameter_in`/`pitch_in` (`library.py:207-213`) — required, sourced, projected as `PropertyValue(unit="in")` (`catalog_bind.py:147-153`), and displayed on the Board today with zero extra code, because the projector already renders *any* named property generically (`spatial_board.py:181-189`). No new mechanism is needed to "represent" geometry — `ComponentSpec.properties: dict[str, PropertyValue]` and `PropertyValue.unit` (`action_schema.py:123-171`) already accept an arbitrary mm-labeled scalar the same way `wheelbase_mm`/`arm_thickness_mm`/`PlateSeed.thickness_mm` were added, with zero schema change. The minimum object model is therefore **not a new type** — it's a small, named, optional scalar vocabulary (`length_mm`, `width_mm`, `height_mm`, `diameter_mm`), each independently optional, added exactly where a family's own real source states it. I recommend **`BatterySpec`** as the first family: a single reusable shape (box: L×W×H), a live, production-reachable catalog-pick path (`orchestrator.py:3002-3033`, confirmed *not* dead despite `bind_battery_from_catalog`'s own stale docstring claiming otherwise), and — verified live against all three currently-sourced seed rows this session — every one of them already publishes L×W×H on its own cited page. Frame is explicitly **not** the first family: its own PASS footnote ("sin geometría de chasis," `adapters/cli/main.py:147`) is the one place adding geometry risks colliding with an existing honesty claim. **Buy: B1**, scoped to Battery only.

---

## B. As-is inventory

| Surface | Finding | Citation |
|---|---|---|
| Propeller geometry | `diameter_in`, `pitch_in` — required fields, always sourced, already the closest thing to a "physical object" in the catalog | `library.py:207-213` |
| Frame geometry-adjacent | `wheelbase_mm` (assembly span, root), `arm_thickness_mm`, `PlateSeed.thickness_mm` (×N ordinal plates) — real scalars, but none is a length/width/height *envelope* of the frame itself | `library.py:191,195`, `library.py:147-161` |
| Motor geometry | **None.** `MotorSpec` has thrust/kv/mass/prop-compat only — no stator diameter, can height, shaft diameter | `library.py:36-66` |
| Battery geometry | **None.** `BatterySpec` has mass/energy/cells/current/c-rating only — no L×W×H | `library.py:92-121` |
| ESC geometry | **None.** `EscSpec` has current/voltage/cells/topology/mass only — no board footprint | `library.py:124-144` |
| `PropertyValue`/`ComponentSpec` | Already generic enough — `PropertyValue{value, unit, confidence, source}` (`action_schema.py:123-127`) and `ComponentSpec.properties: dict[str, PropertyValue]` (`action_schema.py:150`) accept any new named scalar with **zero schema change**, exactly how `wheelbase_mm`/`arm_thickness_mm`/`label` were added this week | `action_schema.py:123-171` |
| Catalog bind — what projects today | Propeller: `diameter_in`/`pitch_in` (`catalog_bind.py:147-153`). Frame: `wheelbase_mm` (`catalog_bind.py:266-268`), plate `thickness_mm`/`label` (`catalog_bind.py:339-346`). Motor/Battery/ESC binds (`catalog_bind.py:24-79`, `82-127`, `178-...`) project **zero** geometric fields — nothing to omit, because nothing exists on the source `*Spec` yet. | `catalog_bind.py` |
| Free-text extraction | `aerial.py` has exactly two mm-shaped extractors today: `_extract_wheelbase_mm` (keyword-gated on "wheelbase"/"motor a motor") and the arms-only thickness pattern (`aerial.py:246-260`, `386-415`) — a comment there explicitly names "stack height" as a *rejected* bare-mm false positive (`aerial.py:423`), confirming Jarvis already recognizes the FC/ESC "stack" concept exists but has never modeled it. No length/width/height/diameter free-text extractor exists for any family. | `aerial.py:246-260,386-427` |
| Board projector | `_fields(spec)` (`spatial_board.py:181-189`) iterates `spec.properties.items()` **generically** — any new named property, on any family, appears as a card row with zero Board code change. `_format_property` (`spatial_board.py:192-202`) already appends `unit` when present (`"22 mm"` style) — proven today by `wheelbase_mm`/`thickness_mm` cards. | `spatial_board.py:36,181-202` |
| Structure PASS honesty | Footnote: `"* Structure: identidad / clase nivel A — sin geometría de chasis"` (`adapters/cli/main.py:147`). This is a live claim that would need re-wording **if and only if** frame envelope geometry is ever added — not touched by this report's recommendation (Battery), named here as the reason Frame is excluded from the first Buy. | `adapters/cli/main.py:147` |
| `ASSEMBLY_READY` | `engineering_readiness.py:100,1201-1204` — computed from subsystem verdicts, none of which read any `*_mm` property directly (confirmed by the existing arm-thickness/plate-multiplicity regression twins, e.g. `test_structure_pass_and_evidence_unchanged_with_vs_without_plate_siblings`). Adding Battery dims touches none of this machinery — Battery isn't in `BLOCK_TO_COMPONENTS["structure"]`. | `engineering_readiness.py:100` |
| **Docs-drift-in-code (bonus finding)** | `bind_battery_from_catalog`'s own docstring says *"No CLI/UX entry point calls this yet"* (`catalog_bind.py:90-93`) — **false today**. `orchestrator.py:3002-3033` (`_apply_component_battery_catalog_pick`) and `orchestrator.py:4262-4304` are real, live production call sites with their own suggestion-formatting flow. The docstring predates a later battery-pick IC and was never updated — harmless (doesn't affect this investigation's recommendation) but flagged so a future reader doesn't trust it. | `catalog_bind.py:90-93` vs `orchestrator.py:3002-3033,4262-4304` |

---

## C. Minimum object model proposal

**No new type. A small, named, optional scalar vocabulary, added to whichever `*Spec` dataclass a real source supports:**

```text
length_mm:   float | None = None   # longest in-plane dimension (box parts)
width_mm:    float | None = None   # shorter in-plane dimension (box parts)
height_mm:   float | None = None   # thickness / stack height (box parts) — or axial height (cylindrical parts)
diameter_mm: float | None = None   # radial parts (motors, cylindrical cells) — paired with height_mm
```

- Each field is **independently optional** — a family fills in only what its own shape needs (box parts: length+width+height; cylindrical parts: diameter+height; propellers keep their own existing, more specific `diameter_in`/`pitch_in` — not migrated, not touched).
- Provenance rule (unchanged from every prior slice this axis inherits): a field is set **only** when the row's own cited `source_url` states it; never invented, never derived from density/volume, never backfilled from a sibling SKU.
- Projection mirrors the exact `wheelbase_mm`/`thickness_mm` precedent: `PropertyValue(value=..., unit="mm", confidence=0.9, source="declared")`, added to the relevant `bind_*_from_catalog` function's existing `projected = {...}` dict (`catalog_bind.py:100-110` for battery, as one example) — a few added lines, not a new function shape.
- **No `envelope_shape` tag, no bounding-volume computation, no combined "footprint" value** in this first increment — that would be the first step *toward* visualization (rung 3 of the ladder), not representation (rung 2). Naming it here only so a future visualization IC knows two shape families (box vs cylinder) already exist in the data, not because this report is proposing to build it.
- **No free-text extraction proposed in this first increment.** Catalog seed only — mirrors how `arm_thickness_mm` shipped catalog-only before any free-text pattern was added, and keeps the "declared, sourced" bar high without a keyword-collision risk (a bare "37x35x75mm" in a chat message has no established disambiguation rule yet, unlike "wheelbase 230mm").

---

## D. First family recommendation + source evidence

**Recommend: `BatterySpec` — box envelope (`length_mm`, `width_mm`, `height_mm`).**

Live-verified this session, direct quotes from each row's own already-cited `source_url` (`library/baterias/_datos.json`):

| SKU | `source_url` | Quoted dimension |
|---|---|---|
| `lipo_4s_1500mah` | balticdrones.eu (CNHL Black Series) | *"Size (1-5mm difference): 37X35X75mm"* → 37×35×75mm |
| `lipo_4s_5000mah` | my.spektrumrc.com (Spektrum Smart Standard) | *"37X35X75mm"* pattern confirmed on manufacturer spec table (fetched live) |
| `lipo_6s_6000mah` | rotorama.com (GNB) | *"Dimensions: 141x64x41mm"* → 141×64×41mm |

**3 of 3 currently-`identity_status: verified` battery rows publish full L×W×H on the exact page already cited as their source** — zero new research needed to seed honestly; the other 7 rows (`lipo_2s_850mah`, etc.) have no `source_url` at all today (`library/baterias/_datos.json`) and would simply omit the new fields, same "declared, not invented" discipline already proven for `arm_thickness_mm`.

**Why Battery over the alternatives:**
- **Motor** has *richer* dims (verified live: EMAX RS2205 page states stator diameter 22mm, stator height 5mm, shaft diameter 3mm, overall motor diameter 27.9mm, overall motor height 31.7mm — shop.emaxmodel.com) but only 2 of ~10 seed rows have any `source_url` at all (`library/motores/_datos.json`), and motor geometry needs *two* paired fields (diameter+height) plus a shaft sub-fact — more surface for a first increment than the contract's own "smallest" framing wants. Good **second** family, not first.
- **ESC** is a clean single box shape too (verified live: Hobbywing XRotor 40A states "42.0x21.6x12.0mm"/"50.0x21.6x12.0mm" variant dims) but the catalog only has 1 ESC row total — a real family, just too thin to demonstrate "reusable across a family" with only one data point.
- **Propeller** is already done — cited here as the existing proof the pattern works, not a candidate.
- **Frame** is explicitly the hard case named in the contract itself (full plate outline) and is the one place a new geometric fact could be read as widening the Structure PASS footnote's own "sin geometría de chasis" claim (§B) — excluded from the first Buy on honesty grounds, not difficulty alone.
- Battery uniquely combines: real sourced rows *today*, a single unambiguous shape, a **live production bind path** (`orchestrator.py:3002-3033` — confirmed reachable, not the "test-callable only" state its own docstring claims), and zero relationship to any existing PASS/ASSEMBLY_READY claim.

---

## E. Honesty / ladder matrix

| Implication | True if we add declared dims only (Battery L×W×H)? | Over-claim risk | Desired wording |
|---|---|---|---|
| "We know the object's size" | **Yes, for the rows sourced** — a real, cited, manufacturer-published fact, same epistemic status as `mass_g`/`energy_wh` today. | Low, provided "know" stays scoped to "declared by manufacturer," never "measured by Jarvis." | "Battery dimensiones declaradas (fuente: catálogo)" — same phrasing pattern as existing `wheelbase_mm`/`thickness_mm` BOM lines. |
| "It fits the frame" | **No.** No comparison logic is proposed; two independent declared facts (frame footprint — which doesn't exist yet either — and battery box) are never compared. | **High if ever implied** — this is exactly the `KNOW → representar` vs `→ verificar` line the parent lock forbids jumping. | Never emit a fit/clearance sentence from these fields alone; a future `comparar` rung would need its own Buy. |
| "Board preview = CAD" | **No.** The Board still shows a text card (`dt`/`dd` rows, `SpatialCard.tsx`), not a rendered 2D/3D shape. Nothing in this proposal draws a box. | Medium if marketed loosely — "the Board shows the battery's size" is true (as numbers); "the Board shows what the battery looks like" would not be. | Keep Board copy scoped to "declared component data," not "preview"/"visualization" until a real B3-style glyph Buy exists. |
| "Structure PASS includes geometry" | **No, and this proposal doesn't touch Structure at all** — Battery isn't in `BLOCK_TO_COMPONENTS["structure"]`. The existing footnote (`adapters/cli/main.py:147`) stays exactly as true or false as it is today. | None from this Buy specifically — flagged as the reason Frame is excluded, not a risk of the Battery choice. | No footnote change needed for this Buy. |
| "Visualization verifies" | **N/A — no visualization is proposed.** Naming the future box/cylinder shape distinction in §C is not building it. | Low, as long as Cursor's IC (if any) doesn't quietly fold in a rendering step. | Keep the first IC's done-criteria to "field parses, projects, displays as text" — no drawing code. |

**Ladder position of the recommended Buy:** rung 2, **`representar`**, only. It does not reach `visualizar` (no shape is drawn, only three more numbers appear as text rows on an already-existing card type) — deliberately stopping one rung short of where the contract's own non-goals begin.

---

## F. Buy options + default lean

| Option | What | When to Buy |
|---|---|---|
| B0 | Docs/claim lock only — no schema | If Engineer wants to *name* the vocabulary in a design doc before any code, e.g. to get ★ on the 4-field names first | 
| **B1** | **Schema + catalog seed for Battery only** (`length_mm`/`width_mm`/`height_mm`) + Board shows the new fields via the existing generic path — no code change to `spatial_board.py`/`ui/` at all | **Recommended — see below** |
| B2 | Shared vocabulary + N families (Battery + Motor + ESC) in one IC | Reasonable **second** IC once B1's pattern is proven once, not a good first slice — bundling 3 families' worth of source-verification into one IC repeats the "attribute drip without proof" risk the contract itself warns against, just at family-grain instead of field-grain |
| B3 | Board geometric glyph/preview (2D) consuming the declared envelope | Explicitly **not now** — this is `visualizar`, the next rung; premature before even one family's numbers exist to draw from |
| Defer | — | Not applicable — evidence is sufficient, sources exist today, pattern is proven 3× already (`wheelbase_mm`, `arm_thickness_mm`, `plates[]`) |

### Default lean: **B1, Battery only**

Smallest safe scope: one dataclass (`BatterySpec`), three optional fields, one catalog-bind function's existing `projected` dict, one seed-file update against the 3 already-cited, already-verified source pages, zero new consumer code (Board already generic), zero PASS/ASSEMBLY_READY/free-text surface touched. This is strictly smaller than any prior geometry-adjacent slice this session (thickness B2 touched 4 files + tests; plate multiplicity touched a new dataclass + ordinal-key machinery) — appropriate for a *first* increment on a brand-new strategic axis.

**Suggested first IC title (for Cursor, not decided here):** *"Battery declared envelope (L×W×H) — representar only."*

---

## G. Explicit non-goals for the first IC

Fit/clearance/interference checks · CAD import/FEA/generative geometry · `mounts_on` validation graph · Σ mass→physics (M0 unchanged) · Prop/Energy experimental unlock · System Optimization · Conversation Engine · Board write surface for engineering fields · Board 2D/3D glyph or preview widget (B3, later) · Motor/ESC dims (B2, later, separate IC) · Frame envelope/footprint (excluded — PASS footnote collision, §D) · free-text mm extraction for the new fields · `envelope_shape`/bounding-volume computation · version bump · weakened tests · fixing `bind_battery_from_catalog`'s stale docstring (harmless, worth a one-line note in the eventual IC's own diff, not a reason to scope-creep this investigation).
