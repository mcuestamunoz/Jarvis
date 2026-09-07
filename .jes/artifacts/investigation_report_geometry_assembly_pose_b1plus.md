# Investigation Report — Geometry Assembly Pose B1+ (numeric pose / reference frame)

**IC:** [investigation_contract_geometry_assembly_pose_b1plus.md](investigation_contract_geometry_assembly_pose_b1plus.md)
**Investigator:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · suite 2385 (unchanged — investigation only, no code/tests touched)

---

## 1. Executive recommendation

**B0 — Defer.** Nothing that changed between the assembly-espacial B1 report and today removes the blocker that report identified. `mounted_on` and Board edges solved *addressability* (which existing component key does another component point at) — they did not, and could not, solve *reference-frame convention* (what a number like "10mm" would mean: from where, along which axis, in which direction). That second problem is still completely unsolved anywhere in Jarvis's data model, for every family, with no exception: no catalog seed for any Motor/Battery/ESC/FC/Frame/Propeller SKU publishes a mounting-hole pattern, a footprint anchor point, or a body-axis convention (confirmed by a fresh, full-field grep across every seed file — zero hits beyond one unrelated prose sentence). Even the single richest, most recently-sourced geometric case in the system — Pixhawk 4's own official dimensions table — was explicitly checked for a mounting-hole pattern during the earlier FC Geometry investigation and found to have none ("No mounting hole pattern stated on either page — not claimed," `aerial.py:558-560`). A numeric offset with no defined axis convention is not a smaller, safer version of pose — it is precise-looking noise, and inventing a convention ourselves (e.g. "assume plate center, +X = forward") is exactly the "paper over" move Locked Stance 5 forbids. This investigation **reaffirms**, and narrows the scope of, the prior rejection — it does not supersede it.

---

## 2. Evidence table

| Surface | Finding | Cite |
|---|---|---|
| `ComponentSpec` schema | Exactly two relational fields exist: `parent_key` (BOM topology, always literal `"frame"`) and `mounted_on` (declared relation, `str \| None`). Zero position/orientation/offset fields. | `src/jarvis/schemas/action_schema.py:171,184` |
| `state_schema.py` | Zero pose/orientation/offset/position identifiers anywhere in `ProjectState`/`DesignProperties`/`StructureProperties`. | grep, zero hits |
| All catalog seeds (Motor/Battery/ESC/FC/Frame/Propeller, ~25 files) | Full field-key inventory across every seeded SKU contains only identity, mass, electrical ratings, and the already-known glyph geometry fields (`length_mm`/`width_mm`/`height_mm`, `diameter_mm`/`diameter_in`, `stator_diameter_mm`, `shaft_diameter_mm`, `arm_thickness_mm`, `plate_material`, `wheelbase_mm`). No `mount`, `hole`, `offset`, `cg`/center-of-gravity, `face`, `origin`, `centroid`, or `bolt_pattern` key exists anywhere. | `python3` field-key union script, full output quoted below |
| ESC seed's one grep hit for "origin" | Prose only — "[mass_g]'s origin is undocumented/unknown," about provenance of a number, not a spatial origin. | `library/esc/_datos.json:21` |
| Frame plate labels (`library/frames/_datos.json`) | Plates carry `label` (e.g. `"Main Plate"`, `"Top"`, `"Bottom"`) + `thickness_mm` + optional `material` only — **no length/width, no footprint, no defined "center" or corner**. A label makes a plate *nameable*, not *geometrically anchorable*. | `library/frames/_datos.json:11-66` |
| Frame root | `mass_kg`, `material`, `size_class_inch`, `wheelbase_mm` only. `wheelbase_mm` is a single scalar distance (diagonal motor-to-motor span) — it establishes a rough scale, never an axis convention, a zero point, or a "front"/"up" direction. | `library/frames/_datos.json` (frame root keys); prior Motor/Frame Geometry investigations |
| Pixhawk 4 (richest single case) | Official PX4 docs + Holybro product page both quoted for L×W×H; both explicitly checked for a mounting-hole pattern during the prior FC Geometry investigation and found to state none. | `src/jarvis/domains/aerial.py:546-561` |
| Board projector / edges (B2) | `place()` reads `spec.mounted_on` and checks presence only; `mountEdgeSegments` computes a line from `node.x/y/width/height` (card pixel rects). Zero pose math, zero mm-to-px conversion beyond the pre-existing glyph `PX_PER_MM` constant (unrelated — used for `geometry`, never for edges). Confirmed by reading both files in full this session (also independently re-verified during the B2 review). | `src/jarvis/workspace/spatial_board.py` (`place`, `_emit`), `ui/spatial-board/src/mountEdgeGeometry.ts` |
| `mounted_on_declare_assist.py` | Confirmed relation-only — grep for `pose\|orientation\|offset\|_mm\b\|position` returns zero hits. The parser resolves a target *key*, never a number. | `src/jarvis/core/mounted_on_declare_assist.py` |
| Prior assembly-espacial B1 report, §D | *"Rejected for B1, with reasons: Position (mm): no catalog source anywhere documents a mount offset for any SKU... and no reference frame is defined anywhere in the system... Orientation: same absence of source."* | `investigation_report_geometry_assembly_espacial_b1.md` §D |

**Full field-key union across every catalog seed (verbatim script output):**
```
['arm_material', 'arm_thickness_mm', 'burst_current_a', 'c_rating', 'cage_material',
 'capacity_mah', 'cells', 'cells_max', 'cells_min', 'channels', 'chemistry',
 'compatible_kv_band', 'compatible_prop_inch', 'configuration', 'continuous_current_a',
 'continuous_current_source', 'density_kg_m3', 'design_space', 'diameter_in',
 'diameter_mm', 'energy_wh', 'esc_topology', 'height_mm', 'identity_status',
 'is_generic', 'kv_rating', 'length_mm', 'manufacturer', 'mass_g', 'material',
 'max_continuous_current_a', 'max_continuous_current_source', 'max_current_a',
 'max_watts', 'model', 'nominal_voltage', 'operating_points', 'pack_configuration',
 'part_number', 'pitch_in', 'plate_material', 'plates', 'shaft_diameter_mm',
 'size_class_inch', 'source_note', 'source_url', 'standoff_material',
 'stator_diameter_mm', 'stator_height_mm', 'tags', 'thrust_n', 'voltage_max',
 'voltage_min', 'weight_g', 'wheelbase_mm', 'width_mm']
```
Nothing in this list names a mount pattern, hole spacing, offset, face, or axis.

---

## 3. Answers A–E

### A. Reference frame

**A1 — What named origins could be honest today?** *Keys*, not *points*. Any existing component key (`frame`, `frame_plate`, `frame_plate_1`, `frame_arm`, …) is honestly nameable as "the thing a measurement is relative to," exactly the way `mounted_on` already names a component as "the thing something is mounted on" — this requires zero new data, since these keys already exist and are already addressable. What is **not** honestly nameable is a *geometric point on* that key — "plate centroid," "arm root," "frame center" — because none of these have a defined shape/footprint/anchor in the data model. A plate's `label` tells you *which* plate; it tells you nothing about *where on the plate* "center" is, because no plate has a stored length/width. This is the same distinction the Board glyph investigation already drew for shape (envelope ≠ CAD) — here it recurs for pose (a name ≠ a coordinate origin).

**A2 — Is "user-declared origin string + numbers" enough, or must the origin be an existing component key?** If pose were ever built, the origin **must** be an existing component key, never a free string. A free-text origin ("measured from the front-left mounting hole") is exactly the "precise-looking, not honest" trap: the number would carry implied precision (mm, to one decimal) while its meaning depends entirely on an unvalidated, unstructured sentence nobody re-checks. A component-key origin is at least *structurally* honest (it names a real, existing thing) even though it still doesn't solve the deeper axis-convention problem (see A3/§4).

**A3 — If origin target ≠ `mounted_on` target, is that allowed/required/forbidden?** Should be **allowed but not required** if pose is ever built — a component could plausibly be mounted on one part (`mounted_on="frame_plate"`) while a user wants to describe its position relative to another reference (`pose_origin="frame"`, i.e. "10mm from the frame's own center, which happens to sit on this plate"). Forcing them to be identical would be a false constraint; forcing them to differ would be equally arbitrary. This is a minor schema question, not a blocker — the blocker is upstream of it (§4).

### B. Pose bag minimum

**B4 — Smallest field set?** Not applicable while B0 stands, but for the record: even the smallest imaginable bag (`x_mm: float, y_mm: float`, translation-only, no yaw) already presupposes a 2-axis convention (what does `+x` point toward?). There is no version of this question with a smaller honest answer than "none, until an axis convention exists."

**B5 — Units?** Millimeters is the only unit already used throughout Geometry (dims, glyphs) and would be the obvious choice if this were ever built — not itself a blocker.

**B6 — Must every mount have a pose, or is it optional?** If ever built, must be optional, mirroring `mounted_on`'s own optionality — a huge fraction of declared mounts (per the seed/catalog evidence above) would have no numeric backing at all, and forcing a value would immediately produce invented numbers.

### C. Honesty / provenance

**C7 — Allowed `source` values?** If ever built: `declared` (user-typed, honest about being unverified) and `unknown`/absent (no claim at all). **`catalog` should not be an allowed source today** — confirmed above, no seed anywhere publishes a mount offset a `catalog` tag could honestly cite. Adding the vocabulary value without any seed ever using it would be dead code inviting future misuse (someone eventually "filling it in" from a rough visual estimate, mislabeled as `catalog`).

**C8 — Forbidden copy?** Identical list to `mounted_on`'s own: "ensamblado," "cabe," "verificado," and additionally **"posición real"** (per this IC's own explicit list) — a declared pose is a claim about what the user typed, never a claim about physical reality.

### D. Board / Continuity (moot under B0, answered for completeness)

**D9 — Board display, text vs. glyph move?** If ever built: **text-only first**, exactly the IC's own default lean and exactly the precedent `mounted_on`'s own B1 set (declare → text field → *then*, separately reviewed, → edges). Moving glyph positions from a declared-but-unverified number would be a strictly worse honesty regression than anything shipped so far — it would make the Board's rendered layout *look* like it reflects the declared pose precisely, which is the opposite of B2's own edges lock ("layout unchanged by mount relation").

**D10 — Continuity declare-of-pose in scope for a first Buy?** No, for the same reason relation-declare was sequenced *after* the schema+Board slice for `mounted_on` (three separate, reviewed cycles) — parsing a number out of free text ("pon el FC a 10mm de...") is a strictly harder and riskier problem than parsing a component-name relation, and should not be bundled into whatever the smallest pose Buy would be.

### E. Buy options

| Option | Recommended? |
|---|---|
| **B0 — Defer** | **Yes — default lean.** No schema change, pose stays a stub, revisit only if new evidence (below) arrives. |
| B1 — Optional declared translation | No — no axis convention exists to make even a "just declared" number meaningfully comparable across two components' independently-typed offsets. |
| B1+ — Translation + yaw | No — same blocker, worse (adds an angle with no reference heading defined anywhere either). |
| Reject numeric pose (permanently) | Not recommended as stated — "permanently" overclaims; the honest position is "blocked on evidence," not "impossible in principle." Recommend keeping the door open, gated on new evidence, rather than a permanent reject. |

**What would change this lean:**
1. A manufacturer page that *does* publish a mounting-hole pattern or footprint-anchor for a specific SKU (this is common in the FPV world for **flight-controller/ESC "stack" standards**, e.g. 30.5×30.5mm or 20×20mm bolt patterns — genuinely different from "where does this sit in the whole airframe" pose, and worth a *separate*, narrower future investigation scoped to "self-geometry hole pattern," not conflated with this IC's relative-assembly-pose question).
2. Jarvis explicitly deciding to define its *own* self-consistent per-project axis convention (e.g., "arm-relative polar coordinates from a declared frame center, heading undefined") — a real, nameable design decision, but one big enough that it is itself a fresh, dedicated investigation (a body-frame convention is CAD-adjacent scaffolding), not a rider on this report.
3. The Engineer explicitly accepting the risk of a "declared-only, no axis convention, plain free-text description alongside a bare distance" model (see the contingency sketch below) — a legitimate product decision this report is not positioned to make, only to flag as a possibility with named risk.

---

## 4. Risks if we Buy wrong

- **Buying B1 without an axis convention** produces numbers that *look* precise (mm, decimal) but are individually meaningless and mutually incomparable — two declared offsets on the same project could not be checked against each other for consistency, and any future "compare/verify" or fit work would inherit ambiguous inputs it could never safely act on. This is the single biggest risk, and it is exactly the trap Locked Stance 5 names.
- **Buying B1 and quietly defaulting an origin ("assume plate center")** — explicitly forbidden by this IC, and it would also silently violate the project's own established honesty precedent (BOM/Board tails exist specifically to flag exactly this kind of unstated assumption elsewhere in the system).
- **Deferring forever without naming reversal criteria** (the failure mode of a bad B0) would leave the Engineer unable to tell "still blocked" from "nobody re-checked" a year from now — addressed above by naming the three concrete conditions that would change the lean.

---

## 5. Supersede or reaffirm?

**Reaffirm**, not supersede. The prior assembly-espacial B1 report's rejection of numeric pose rested on two independent facts: (1) no catalog source documents any mount offset, and (2) no reference frame is defined anywhere in the system. Fact (1) is unchanged — reconfirmed by a fresh, full-seed grep this cycle (§2). Fact (2) is not only unchanged but now demonstrably *deeper* than "no offsets exist" — even the one part of the system that gained real geometric richness since B1 (glyph envelope dims) never established an axis/anchor convention, and the one part of the system that gained real relational richness since B1 (`mounted_on` + Board edges) solved a *different* problem (which key, not which coordinate). Nothing in the intervening work touches the actual blocker.

---

## 6. Field sketch (contingency only — not recommended, not an IC)

Per §6's format requirement, and purely as a reference in case the Engineer chooses to accept the risk named in E/§4 rather than follow this report's B0 recommendation — **this is not a recommendation**:

```text
ComponentSpec.pose: {
  origin_key: str          # an existing component key (§A2) — never free text
  distance_mm: float        # a single declared scalar — no implied axis
  description: str          # required, human-readable, e.g. "≈10mm forward of plate edge"
  source: "declared"        # only allowed value — no "catalog" until real seed evidence exists
} | None
```

Deliberately **not** `x_mm/y_mm/z_mm` or yaw — a single scalar + mandatory prose description is the only shape that doesn't silently imply an axis convention nobody has defined. Even this reduced shape should not ship without the Engineer explicitly naming the risk it accepts (uncomparable declared numbers across components) in the ★ Buy itself.

---

## 7. Non-goals honored

No code changed — `git status --short -- src/ tests/` is empty for this cycle. No fit/clearance/intersection opened. No Board layout ever treated as pose SoT. No mount-hole pattern invented for any SKU. `mounted_on` semantics and Board edges B2 behavior were read, not modified. No Continuity pose parser designed or implemented. No CAD/FEA/Conversation Engine/version bump. Pose B1+ stub file (`implementation_contract_geometry_assembly_pose_b1plus.md`) was read and confirmed still an inert, correctly-gated placeholder — not touched.
