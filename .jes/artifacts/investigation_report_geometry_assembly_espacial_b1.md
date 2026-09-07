# Investigation Report — Geometry Assembly Espacial B1 (minimum pose / `mounted_on`)

**IC:** [investigation_contract_geometry_assembly_espacial_b1.md](investigation_contract_geometry_assembly_espacial_b1.md)
**Investigator:** Claude Code
**Date:** 2026-09-07
**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ Buy B1 → IC READY  
**Review:** [investigation_review_geometry_assembly_espacial_b1.md](investigation_review_geometry_assembly_espacial_b1.md)  
**IC:** [implementation_contract_geometry_assembly_espacial_b1.md](implementation_contract_geometry_assembly_espacial_b1.md)  
**Baseline:** package `0.3.8` · suite 2350 (unchanged — investigation only, no code/tests touched)

---

## A. Executive answer

**Zero assembly-spatial state exists anywhere in the schema today.** A full grep of `action_schema.py` and `state_schema.py` finds exactly one relational field on the entire `ProjectState` graph — `ComponentSpec.parent_key: str | None` — and it is not a spatial relation: it is a BOM/topology "belongs-to" tag, hardcoded in every one of its 3 production write sites to the literal value `"frame"`, used only to group/remove/lane-place frame sub-parts (`frame_arm`/`frame_plate[_N]`/`frame_cage`/`frame_standoff`). It has no position, orientation, or offset semantics, and cannot honestly be repurposed for motor→arm or ESC→plate mounting without breaking the several call sites that assume "has a `parent_key`" means "is a frame sub-part" (BOM peer-exclusion, `clear_frame_part_children`'s blanket removal, Board lane grouping).

The Board's `x`/`y` are a deterministic lane/row-stacking layout computed fresh from `system_blocks` order (`spatial_board.py`), overlaid client-side by a per-project `localStorage` map after any drag (`useBoardNodes.ts`) — confirmed non-authoritative: no Python code reads it, `ProjectState` has no layout field at all. This is exactly the trap the IC names, and it is already structurally impossible for it to leak into engineering truth today.

No catalog seed (Motor/Battery/ESC/FC/Propeller/Frame, ~25 files) contains any mount/hole/offset field — there is no primary source to condition a numeric pose on, and no reference frame (frame CAD origin? arm centerline? plate corner?) is defined anywhere in the system to make such a number meaningful even if a user typed one.

**Recommendation: B1, relation-only.** Add one new optional field, `mounted_on: str | None`, to `ComponentSpec` — a plain reference to another component's key (including addressable ordinal frame-part keys like `frame_plate_1`), always `source="declared"`, never inferred from Board proximity, BOM co-membership, or cardinality-of-one defaults. This makes the locked product sentence ("sé... a qué se declara montado") true with the smallest possible schema change, touches nothing pose/fit-shaped, and leaves `parent_key`, glyphs, and Board layout completely untouched and orthogonal.

---

## B. As-is inventory

### Schema (`action_schema.py`, `state_schema.py`)

- `ComponentSpec.parent_key: str | None = None` (`action_schema.py:171`) is the **only** relational field anywhere in `ProjectState`, `DesignProperties`, `StructureProperties`, or `ComponentSpec` — confirmed by grep across both schema files for `mounted_on|pose|orientation|attachment|mount`.
- `StructureProperties` (`state_schema.py:107-121`) carries `material`/`density`/`volume`/`structural_fraction`/`notes` — mass/material engineering only, nothing spatial.
- Zero `pose`, `mounted_on`, `orientation`, `attachment_point`, `mount_pattern`, `mount_hole` identifiers exist in any production `.py` file. The only "orientation" string hits (`intent_resolver.py:66,210`, `orchestrator.py:992`) are CLI navigation-help comments — unrelated to physical orientation.
- `CatalogRef.family: Literal["motor","battery","propeller","esc","frame"]` (`action_schema.py:139`) — note `flight_controller` has no catalog family at all (consistent with the prior FC Geometry investigation's finding of an identity-linked dims table instead of a catalog).

### Structure parts graph (`parent_key`)

Set in exactly 3 production locations, **always to the literal string `"frame"`**, never to any other component key:
- `component_writers.py:211` (`set_frame_part_component`, the single writer for `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff` children) — docstring: *"`parent_key="frame"` always — Fase 1 has exactly one assembly root."*
- `catalog_bind.py:409` (frame-part catalog bind, same invariant).
- `clear_frame_part_children` (`component_writers.py:218-229`) removes **every** component with `parent_key == "frame"` on a catalog re-pick — a blanket filter that assumes the value is always `"frame"`.

Consumers all assume this same invariant:
- `project_closure.py:622,635`: any spec with a non-`None` `parent_key` is excluded from top-level BOM peer listing (displayed only as a sub-line under its parent via `_frame_part_sublines`).
- `project_closure.py:840`: frame-part sublines are built by filtering `parent_key != "frame"` out.
- `spatial_board.py:60-67,90,180`: `parent_key` groups a card into its root's Board lane (`children[parent].append(key)`) and marks it `kind: "part"` instead of `"component"`.

`parent_key` therefore encodes exactly one fact — *"I am a BOM sub-part of the frame"* — never *"I am physically fastened to X at some position/orientation."*

### Board layout (`spatial_board.py` + `ui/spatial-board`)

- `project_spatial_nodes` computes every card's `x`/`y` **deterministically** from lane index and a running per-lane vertical offset: `x = ORIGIN_X + col*(CARD_WIDTH+LANE_GAP)`, `y = next_y[col]` incremented by each card's height + `ROW_GAP` (`spatial_board.py:106-123`). This is a flow-chart layout algorithm — it has no relationship to physical space, and a frame's children are simply stacked directly beneath their root in the same lane (`spatial_board.py:134-135,142-143`).
- `ui/spatial-board/src/useBoardNodes.ts:23-33`: after any drag/resize `commit()`, the frontend persists `{x,y,width,height}` for every node into `localStorage`, keyed per `projectId`, and re-applies that overlay on top of the server-computed layout on next load (`applyOverlay`, line 31-33). This is **entirely client-side** — confirmed no Python code reads or writes this key; `ProjectState` has no `x`/`y`/layout field to receive it even if something tried. The overlay is real, but it is fully quarantined from engineering state today, exactly as the Progression Lock requires ("Board remains a projection... No second geometric model of record").

### Glyphs (Board glyphs B1, closed @ 2344)

`_geometry_from_spec` derives `{shape: "box"|"disk", ...}` purely from one component's own declared `length_mm`/`width_mm`/`height_mm` or `diameter_mm`/`diameter_in` — confirmed unmodified, no relation to any other component, no shared coordinate system. An assembly relation needs nothing from this layer: there is no common origin for a child glyph to be placed "on" a parent glyph even if one wanted to draw it that way.

### Continuity / CLI

Zero "montado"/"ensamblado"/mount-adjacent language anywhere in production strings — confirmed by grep across `src/`. The only related text in the tree is the glyph B1 module docstring's own explicit disclaimer: *"...nunca ensamblado ni 'cabe.'"* (`spatial_board.py:18`).

### Prior locks (binding, confirmed still in force)

- `engineer_lock_geometry_spatial_representation_progression.md`: locks the exact ladder `KNOW → representar → visualizar → ASSEMBLY ESPACIAL (pose + mounted_on) → comparar/verificar → CAD/MEASURE/FEA`, and names B1 (visualizar)'s explicit non-goals as *"spatial position, orientation/pose, `mounted_on`/assembly relations, intersection detection, clearance/fit..."* — confirming assembly espacial is the correct next rung, not yet opened.
- `implementation_contract_geometry_board_glyphs_b1.md:185` / `implementation_report_geometry_board_glyphs_b1.md:40`: *"No pose, `mounted_on`, fit, clearance, or CAD/FEA claim anywhere."* — glyph B1 shipped with zero assembly surface, confirming today's baseline is truly a clean zero, not a partial/undocumented one.

### Families available (`BLOCK_TO_COMPONENTS`, `system_architecture_catalog.py:146-170`)

`motors`, `propellers`, `esc`, `battery`, `frame` (+ addressable ordinal children `frame_plate`/`frame_plate_1`..`frame_plate_7`, `frame_arm`, `frame_cage`, `frame_standoff` — via `aerial.py`'s `frame_plate_key`/`is_frame_plate_key`, `FRAME_PLATE_MAX_SIBLINGS=8`), `flight_controller`, `sensors`, `wheels`, `gearbox`, `cameras`, `lidar`, `radio_module`, `payload_bay`, `arm` (robotic manipulation — an unrelated name collision with `frame_arm`, worth flagging for whoever writes copy later so "arm" in a mount relation is never ambiguous between the two).

No catalog seed anywhere (`library/**/_datos.json`, ~25 files across motors/batteries/esc/frames/propellers) contains a mount/hole/offset/pattern field — confirmed by grep. There is no primary source today to condition a numeric mount fact on for any SKU.

---

## C. Reuse vs diverge from `parent_key`

**Diverge.** `parent_key` cannot be reused as-is, for two independent reasons:

1. **Structural risk.** Every consumer of `parent_key` treats its mere presence (or its literal `"frame"` value) as "this is a frame BOM sub-part," not "this has *a* parent." Naming a motor's arm via `parent_key="frame_arm"` would silently: vanish the motor from top-level BOM listing (`project_closure.py`'s peer-exclusion is keyed on `parent_key is not None`, not on the value), reroute it into `_frame_part_sublines`-style display instead of its own BOM line, misplace it in Board's frame lane instead of the propulsion lane, and make it a casualty of `clear_frame_part_children`'s blanket removal on the next frame catalog re-pick (which removes *any* `parent_key`-bearing component today, not just literal `"frame"` ones, since it filters by exactly that value — a generalized `parent_key` would need every one of these call sites re-audited and re-scoped, not just one new writer added).
2. **Semantic mismatch.** Even a widened `parent_key` would still only answer "which BOM group do I belong to for display/removal purposes" — a fact with no honesty requirement (grouping is structural, not a claim about the physical world). A mount relation is a *different kind of fact* — a claim about physical reality that needs a `source` (declared vs inferred) and can be wrong. Collapsing both into one field means one field would need two different honesty disciplines depending on which root it points at, which is worse than two small, separately-honest fields.

`parent_key` and a new `mounted_on` are **not mutually exclusive** and would legitimately coexist: a `frame_plate_1` child (`parent_key="frame"`, a BOM-topology fact) could simultaneously be the *target* of a `flight_controller`'s `mounted_on="frame_plate_1"` (a spatial-relation fact) — two orthogonal relations about the same physical object, not a hierarchy to unify.

---

## D. Minimum field bag + source rules

### Recommended field

```text
ComponentSpec.mounted_on: str | None = None
```

- A plain string naming another key in `design_properties.components` — including ordinal frame-part keys (`frame_plate_1`, `frame_arm`, etc.), which already exist and are already addressable today.
- **No numeric position** (mm offset in any frame). **No orientation** (enum or otherwise). **No "face"/"side"** field.
- **Rejected for B1, with reasons:**
  - *Position (mm)*: no catalog source anywhere documents a mount offset for any SKU (confirmed, §B), and no reference frame is defined anywhere in the system (frame CAD origin? arm root? plate corner?) — a user-typed number would look precise while being uncomparable/untraceable across projects, which is a worse honesty failure than not having the number at all.
  - *Orientation*: same absence of source; an enum (`"top"|"bottom"|"front"`...) would need to be relative to *something* already spatially defined, which doesn't exist.
  - *"Face"/"side"*: same reasoning — would silently imply a shape/frame model this axis has deliberately not built (glyphs are envelope-only, no faces).

### Source rules (locked recommendation)

- `mounted_on` should always carry `source="declared"` — reusing the exact vocabulary already on `PropertyValue.source` (`Literal["declared","inferred","calculated"]`) for consistency, even though `mounted_on` itself is a plain field on `ComponentSpec`, not a `PropertyValue` — an Implementation Contract should decide whether it needs its own provenance wrapper or can stay a bare `str | None` given it has exactly one legitimate source.
- **Never inferred** from: Board drag proximity (two cards being visually close on screen says nothing about physical reality — and per §B, Board position isn't even sent to the server to infer from), BOM co-membership (two `defined` components in the same project are not thereby "mounted"), or cardinality-of-one convenience (a project with exactly one frame plate declared must not auto-assume "the FC must be on it" — that is still an invented fact the user never stated).
- **Validation floor**: the target key named by `mounted_on` should exist in `design_properties.components` at write time. A dangling reference (naming a component that was never declared) is an honest-absence case, not a silent no-op or an invented placeholder — mirroring the B3 slot precedent's own discipline ("never invent for what wasn't declared"). The exact enforcement point (writer-time reject vs. render-time honest-absence badge) is an Implementation Contract decision.

### Which families can honestly participate in B1

Any two already-addressable component keys can express a `mounted_on` relation the moment the field exists — no new KNOW is required for the field itself to work. Concretely, with today's shipped catalog: `flight_controller → frame_plate[_N]`, `esc → frame_plate[_N]`, `motors → frame_arm`, `battery → frame` (no dedicated "tray" part type exists yet, so a battery can only name the frame root, not a specific sub-part, until Structure adds one). **Nothing is architecturally blocked** — the honesty gate is entirely about *who declared it and is it echoed back as `declared`, never invented*, not a per-family allowlist. This is a materially different (smaller, cheaper) gate than the IC's own governing question 5 anticipated needing.

---

## E. Honesty / ladder matrix

| Phrase / signal | Status today | Allowed in B1 | Forbidden in B1 |
|---|---|---|---|
| "Sé qué es" (identity) | ✅ shipped | — | — |
| "Sé qué volumen declarado ocupa" (glyph) | ✅ shipped @2344 | — | — |
| "Declarado montado en X" | ❌ does not exist | ✅ — `mounted_on` names a component key, `source=declared` | Inferring it from proximity/co-membership |
| "Pose declarada" (position/orientation) | ❌ does not exist | ❌ — no source, no reference frame | Any numeric offset/orientation field |
| "Board position = pose" | Already false (layout is pixel/lane, client-overlay only) | Must stay false | Ever reading `x`/`y`/localStorage as physical truth |
| "Ensamblado" / "assembled" | Not claimed anywhere | Still not claimed | Any copy implying B1 verifies assembly |
| "Cabe" (fits) | Not claimed anywhere | Still not claimed | Any clearance/intersection check |
| "Glyph proves mount" | N/A (glyphs have no relation to each other) | N/A | Drawing a child glyph "on" a parent glyph as if geometrically verified |
| "Structure `parent_key` = mount" | False today, and would stay false | `parent_key` and `mounted_on` may coexist, kept semantically distinct | Reusing/overloading `parent_key`'s value for spatial meaning |

Ladder rung: the recommended Buy stays squarely at **assembly espacial** (a declared relation) — it does not advance to **comparar/verificar** (which would require checking a declared relation against something, e.g. "is this plate big enough for this FC's footprint" — a fit-adjacent question this report does not open).

---

## F. Buy options + default lean

- **B0 — Doc-only / defer.** Write down the ladder position, take no schema action. Valid if the Engineer wants to sequence this behind other work; leaves the product sentence unmet.
- **B1 — Relation-only (recommended default lean).** Add `ComponentSpec.mounted_on: str | None`, `source="declared"` always, validated for target-existence, no numeric pose. Board may show it as a plain text field (e.g. an extra `fields` entry: `"montado en: frame_plate_1"`) with **zero new geometry math** — this is a trivial rendering addition reusing the existing `_fields()`/text-field mechanism, not a new capability, so it can ship in the same IC as the schema field without expanding scope. Smallest change that makes the locked product sentence true.
- **B1+ — Relation + minimal pose bag.** Adds position and/or orientation. **Not recommended for this cycle** — no primary source exists for any SKU (§D), no reference frame is defined anywhere in the system, and inventing either would violate the IC's own lock ("do not invent mount patterns or mm offsets without a cited source or an explicit 'declared by user / unknown' honesty path") in spirit even under a "user declared it" banner, since the user would be declaring a number relative to an undefined origin — precise-looking, not honest.
- **B2 — Board visualization of relations (edges/labels).** Drawing an actual line/label between a card and its `mounted_on` target on the canvas, rather than a text field. A natural, small follow-on — genuinely optional for the product sentence (which only requires "sé... a qué se declara montado," satisfied by plain text) and slightly more Board/UI work (edge routing across the existing lane layout) than B1's text-field option. Recommend sequencing as B1's own display choice (text field, ship now) vs. a follow-on B2 (edges, later) rather than bundling both into one Buy.
- **Defer — full pose / multi-body.** No KNOW backs it today; stays explicitly out of scope per the Progression Lock's own "later ★" framing.

**Default lean: B1**, with the text-field Board display included (it is not a separate cost), and B1+/B2 explicitly deferred to a later ★.

---

## G. Non-goals for the first assembly IC

- No fit / clearance / intersection / "cabe" check of any kind.
- No numeric position or orientation field — B1 is relation-only.
- No reuse or overloading of `ComponentSpec.parent_key` — a new, separate, orthogonal field.
- No inference of `mounted_on` from Board drag position, `localStorage` overlay, or BOM co-membership.
- No treating a project's Board layout (`x`/`y`, pixel overlay) as physical truth — confirmed already structurally impossible today; must stay that way.
- No auto-layout of Board cards driven by declared relations ("pretty assembly" from physics).
- No new glyph shape or change to `_geometry_from_spec` — assembly and envelope stay independent.
- No mount-pattern/hole/offset data invented for any catalog seed; none exists today and none should be fabricated to make B1 "richer."
- No reopening of ESC mass, motor thrust H2/H3, Here3/Pixhawk variant work, or HD-004 — confirmed untouched, out of scope.
- No CAD / MEASURE / FEA / System Optimization / Conversation Engine.
- No version bump; no test changes (none were made — this is an investigation-only deliverable, `git status --short -- src/ tests/` is empty for this cycle).
