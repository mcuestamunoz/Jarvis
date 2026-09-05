# Investigation Report — Structure B Parts Graph Ontology

**Project:** Jarvis
**Date:** 2026-09-04
**Investigator:** Claude Code
**Contract:** [investigation_contract_structure_b_parts_graph.md](investigation_contract_structure_b_parts_graph.md)
**Parents consumed:** [investigation_report_structure_b_physical_frame_model.md](investigation_report_structure_b_physical_frame_model.md) (scalar Fase 1 rejected); [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md) (✓/✗ wall)
**Checkpoint:** tag `v0.3.6`; live tree unchanged since prior investigation (suite 2197)
**Status:** OPEN — for Engineer ★ on graph shape

Not an Implementation Contract. No `src/` edits, no schema changes. This report proposes a schema shape and names it as the first nesting precedent in the codebase — it does not write the code.

---

## 1. Executive finding

**A real parts graph is achievable with the smallest possible schema change:
one new optional field, `parent_key: str | None = None`, on `ComponentSpec`.**
No nested-record structure, no new subsystem, no change to
`design_properties.components: dict[str, ComponentSpec]`'s shape
(`state_schema.py:126`) — the dict already accepts arbitrary string keys
(confirmed, no key-format constraint anywhere). Sibling entries like
`components["frame_arm"]` become **children** of `components["frame"]`
purely by setting `parent_key="frame"` on the child spec. This is additive
and backward-compatible: every existing saved project, every existing
`ComponentSpec` in every test, has `parent_key` default to `None` and is
completely unaffected.

**Concrete evidence the graph is not academic:** Catalog Foundation IC-1's
own sourcing pass already found a real product that a flat scalar
`frame.material` field **cannot honestly represent** — the manufacturer's
own page for `armattan_rooster_5in` (already in the seed,
`library/frames/_datos.json`) states *"carbon fiber main plate/arms with
titanium cage and aluminum standoffs"* — three different materials on one
product. My own prior report's rejected scalar model would have forced a
single, lossy `material="fibra de carbono"` value, silently discarding the
titanium/aluminum hardware. This is the strongest evidence available that
Engineer's rejection of the scalar model was correct, using data already in
the repository, not hypothetical future products.

**Fase 1 graph:** `frame` (root, unchanged from today) with optional
**part-type** children — `arm`, `plate`, `cage`, `standoff` — each **one
node per type with a `count` property** (mirroring the `motor_count`
precedent, not one node per physical instance). No `mounts_on`/spatial edge
type. No wiring into `BLOCK_TO_COMPONENTS`/architecture-progress/completeness
— sub-parts are optional, informational, invisible to `Structure PASS` by
construction (§8). Catalog bind creates only the root in Fase 1 (today's
seed schema has no per-part fields to project honestly); seed enrichment for
wheelbase and per-part material is named as a real, evidence-backed later
slice (§7).

**Buy: (b) — honesty IC first (unchanged from prior report), graph model IC
second**, matching Engineer's own stated lean. The graph is feasible without
a new subsystem, so (d) retreat-to-scalars is not triggered.

---

## 2. Node/edge catalog

| Node type | Fase 1? | Fields | Notes |
|---|---|---|---|
| `frame` (root) | Yes — unchanged | `mass_kg`, `material`, `size_class_inch`, `catalog_ref` (all existing) | Today's component, untouched. Its own `material` may now honestly mean "primary/declared material" rather than "the only material" once children exist — a wording nuance, not a schema change. |
| `arm` | Yes | `count` (int), `material` (optional, overrides/supplements frame's), `catalog_ref` (none in Fase 1 — no per-part catalog rows exist yet) | Mirrors `motor_count`: one node, a count, not N instances. |
| `plate` | Yes | `count` (int, default 1 or 2 for top/bottom), `material` | |
| `cage` | Yes (justified directly by the Armattan example) | `material` | Present on some real products (motor guards/prop cages); absent on most — always optional. |
| `standoff` | Yes | `count`, `material` | |
| `hardware` (screws, etc.) | **No — out of Fase 1** | — | No proven need; no source data seeds it; matches prior report's "no proven immediate need" discipline. |
| Per-instance part nodes (e.g. `arm_front_left`) | **No — out of Fase 1** | — | Would require a spatial/positional concept (front/left/etc.), which borders the MEASURE wall (position implies layout). Named as a possible Fase 2 only if a concrete future need appears (e.g. per-arm mount identity) — not proven now. |

**Edge type: exactly one — `has_part`, encoded as the child's
`parent_key` pointing at the parent's dict key.** Directed (child → parent),
no reverse traversal needed for Fase 1 (a parent doesn't need to enumerate
children for anything PASS-relevant; a display helper can scan
`components.items()` for matching `parent_key` when needed — see §3).
**No `mounts_on` edge type** — that would encode a spatial/functional
relationship ("this part mounts on that one") which starts to imply the
geometric correctness Structure A's LEVEL A screening is deliberately
narrower than. `has_part` only ever claims "this is declared as part of the
assembly," never "this is correctly attached/positioned."

**Cardinality departure from `motor_count`, justified:** motor's precedent
is one scalar (`motor_count`) on one node (`motors`). This report's Fase 1
uses one **node per part type**, each with its own scalar count — a
generalization, not a departure, of the same "count, don't enumerate
instances" principle, applied across multiple part *types* instead of one.
The reason a single frame-level scalar (my prior report's rejected model)
doesn't suffice is that a frame's parts can have *different materials from
each other* (Armattan) — a fact a flat `frame.properties` dict, being one
scalar per key, cannot hold for "material" twice. Separate nodes solve this
without inventing a new property-value shape.

---

## 3. State-placement decision table

| Option | Verdict | Why |
|---|---|---|
| Nested records inside `components["frame"].properties` | **Rejected** | `PropertyValue` (`action_schema.py:123-127`) is `{value, unit, confidence, source}` — a scalar. Holding a list of child part records here requires changing `PropertyValue` itself, which is read by every domain (motors, battery, propellers, ESC, sensors, FC) — the blast radius is the whole schema, not just frame. Far larger than "smallest schema change." |
| **Sibling keys in `design_properties.components` + new `ComponentSpec.parent_key: str \| None = None`** | **Recommended** | `components` is already `dict[str, ComponentSpec]` with no key-format constraint (confirmed, `state_schema.py:126`). Adding a key is zero-schema-change; adding `parent_key` to `ComponentSpec` is one optional field, additive, defaults `None` for every existing/serialized project — no migration needed. Composes with the existing dict/writer/BOM machinery per locked stance #7, rather than replacing it. |
| New assembly field on `ProjectState`/`DesignProperties` (e.g. `frame_assembly: FrameAssembly`) | **Rejected — flagged as new-subsystem risk, per contract's own instruction** | Would need its own read/write helpers, its own BOM-equivalent traversal, and would duplicate machinery `components`/`build_component_bom` already provide. `DesignProperties.structure: StructureProperties` (`state_schema.py:107-121`, the legacy material/density/volume record `mutation_engine.py`'s material-swap heuristic already reads) is the closest existing precedent for "a second structure-shaped field" — and it is itself flat, not a graph, and already a known duplication the codebase has lived with rather than a pattern to repeat. |
| Any other existing pattern in the tree | **None found** | Searched for nesting/hierarchy anywhere in `action_schema.py`/`state_schema.py` — `catalog_ref` is the only "reference" concept in the schema today, and it points *outward* to a library SKU, not to a sibling in-project component. No precedent for intra-project parent/child references exists to reuse; `parent_key` would be the first. |

**BOM/CLI display:** `frame` keeps its single existing BOM line, unchanged.
A new, purely additive display helper (not wired into `expected_keys`/
completeness) can render declared children as sub-lines, e.g.:

```text
✓ frame: armattan_rooster_5in [armattan_rooster_5in] qty=1 (high)
   └ arm ×4 — fibra de carbono
   └ cage — titanio
   └ standoff ×4 — aluminio
```

This is display-only, reading `parent_key`, never entering
`build_component_bom`'s `expected_keys`/gap logic — the same "informational,
not gating" posture Structure Foundations' claim-copy work already used for
the BOM suffix.

---

## 4. KNOW / CLAIM / MEASURE matrix (graph fields)

| Field | Node | KNOW | CLAIM | MEASURE (excluded) |
|---|---|---|---|---|
| `parent_key` | any child | Yes — a declared "this belongs to that assembly" fact | "Parte declarada de {parent}" | That the part is correctly attached, positioned, or load-bearing relative to the parent |
| `count` | `arm`/`plate`/`standoff` | Yes, declared | "Brazos declarados: 4" | Consistency with `motor_count` (§5) or with any physical count |
| `material` (per-part) | any node | Yes, declared, same alias-table pattern as frame's existing material | "Material declarado del brazo: fibra de carbono" | Structural adequacy of that material for that part's role |
| `configuration` | `frame` root only | Yes, closed vocabulary (unchanged from prior report) | "Configuración declarada: quad-X" | Whether the declared arm/plate graph actually matches that configuration's real topology (Jarvis does not cross-check configuration against the part graph in Fase 1 — see §5) |
| `wheelbase_mm` | `frame` root (assembly-level span, not a per-part field — see §7) | Yes, declared or catalog-sourced | "Wheelbase declarado: N mm" | Clearance, mount fit, frame rigidity |

---

## 5. Mass, `arm_count`↔`motor_count`, and `configuration` policy under the graph

**Mass:** stays **assembly-declared only**, unchanged from the prior
report's lean — re-decided here under the graph and still correct. A
sum-of-parts rule would require every child part to carry its own `mass_kg`
and would silently produce a *second*, potentially-diverging total-mass
number next to the one `calculations.total_mass_kg` already uses
(`_frame_completeness`/calc only ever read the frame root's own `mass_kg`,
never a sum) — introducing exactly the "two authorities disagree" hazard
this whole phase's claim-hygiene work has been closing, not opening. Fase 1
explicitly **forbids** sum-of-parts; child `mass_g`/`mass_kg` fields are not
even included in the Fase 1 node table (§2) for this reason — if a future
slice wants per-part mass, it needs its own explicit reconciliation rule
first, named as a separate future decision, not assumed here.

**`arm_count` ↔ `motor_count`:** the graph does **not** smuggle this
cross-check through an edge type. There is no edge from `arm` to `motors`,
no `mounts_on`, no shared count validation. `arm.count` and
`current_parameters["motor_count"]` remain two independent declared facts
that Jarvis never compares — the same forbidding this report's parent
already locked, restated here because a graph makes it *easier* to
accidentally imply a relationship (an edge is a natural place to hide a
check) — worth being explicit that none exists.

**`configuration`:** stays on the `frame` root only (not a graph node
itself — it is a label describing the assembly's overall topology, not a
physical part). Unchanged from the prior report: closed vocabulary, matched
from declared text, never inferred from `motor_count` or from the declared
part graph. Jarvis does not check that a declared `configuration=quad_x`
is consistent with `arm.count=4` — both are independently declared,
independently displayed, never cross-validated (same discipline as
`arm_count`↔`motor_count`).

---

## 6. Allowed vs. forbidden claim sentences (extends prior report §4)

**Allowed:**

```text
"Frame compuesto de: brazos ×4 (fibra de carbono), placa (fibra de
 carbono), jaula (titanio), standoffs ×4 (aluminio) — fuente: catálogo,
 Armattan Rooster."
"Parte declarada: brazo ×4, material fibra de carbono (declarado, no
 verificado contra motor_count)."
"Jaula declarada: titanio (fuente: catálogo)."
```

**Forbidden (extends the prior list, now for graph-specific phrasing):**

```text
"Los 4 brazos sostienen los 4 motores."           # invents a mounts_on/motor-count relation
"La jaula protege el hardware de impactos."        # functional/protective claim (strength-adjacent)
"Los brazos están correctamente dimensionados para la configuración quad-X."  # cross-checks
 configuration against the part graph, which Jarvis does not do
"El ensamblaje estructural es coherente."           # implies a verified topology, none exists
"Standoffs de aluminio — compatibles con el stack declarado."  # invents a mounting-compatibility claim
```

---

## 7. Catalog bind + wheelbase seed implications

**Bind creates the root only, in Fase 1.** `FrameSpec` (`library.py`,
Catalog Foundation IC-1) has no per-part fields today (`mass_g`,
`size_class_inch`, optional `material`/`manufacturer`/`model`/provenance —
all assembly-level). `bind_frame_from_catalog` therefore has nothing honest
to project onto `arm`/`plate`/`cage`/`standoff` children yet — creating
them from a flat SKU row today would be fabrication (the contract's own
explicit prohibition). **No child stubs are created by bind in Fase 1.**

**Wheelbase placement:** stays an **assembly-root** property
(`frame.wheelbase_mm`), not a per-part field — wheelbase is a span between
opposite arms/motors, a property of the whole assembly's geometry, not of
any one part. This resolves contract Q12/locked-stance-#6 cleanly: it lives
on the same node the prior report already proposed it for, and this
investigation does not change that placement.

**Seed enrichment (named, not implemented):** a future model IC could add
optional `arm_material`/`plate_material`/`cage_material`/`standoff_material`
and `wheelbase_mm` fields to `FrameSpec`, sourced the same way IC-1 already
sourced `material`/`mass_g` (manufacturer/retailer page + `source_note`).
The Armattan row is the concrete existing case that would benefit — its
current single `material: "fibra de carbono"` field is honest but
incomplete relative to what its own source page states. This is scoped as
future work, not attempted here (Catalog Foundation stays closed as a
phase, per locked stance #8's own framing — "discussable here as schema
impact only").

---

## 8. Composition with Structure PASS — confirmed unchanged

Re-verified against live code with the graph in mind: `_structure_evidence`
(`engineering_readiness.py:1043-1050`) reads `classify_component("frame")`,
`calc.total_mass_kg`, `bool(sim)`, `sim_status`. None of these read
`components.items()` broadly or `parent_key` at all — they operate on the
single `frame` key exactly as today. `_frame_completeness`
(`domains/aerial.py:262-281`) checks only `mass_kg`/`material` on whatever
spec is passed to it — a graph child's own completeness (if ever computed)
would be a **separate, independent** call, never merged into the frame
root's own completeness. `BLOCK_TO_COMPONENTS["structure"] = ["frame"]`
(`system_architecture_catalog.py:163`) stays `["frame"]` only — Fase 1 does
**not** add `arm`/`plate`/etc. to this list, so architecture
progress/`expected_keys`/BOM completeness gating are **byte-identical**
whether or not any child part is ever declared. `Structure PASS`'s meaning
(prior report's locked ✓/✗ table) is unchanged by this graph, by
construction — no exception was needed (the display-only BOM sub-lines in
§3 are the one place the graph is visible at all, and they do not feed any
verdict).

---

## 9. Risk / migration notes

- **Schema change size: small.** One new optional field
  (`ComponentSpec.parent_key: str | None = None`). No change to
  `PropertyValue`, `DesignProperties`, `ProjectState`, or any existing
  required field.
- **Migration: none.** Every existing saved project JSON deserializes
  unchanged (Pydantic fills the new field's default). No existing test
  fixture needs updating for the schema addition alone.
- **Test surface for the eventual model IC (not this investigation):**
  moderate — new extraction rules for part-type text (mirroring
  `extract_frame_properties`'s regex style), a new BOM display helper and
  its tests, a regression suite proving `_frame_completeness`/
  `_structure_evidence`/`_derive_subsystem_verdict`/architecture-progress
  are byte-identical with and without declared children (the same kind of
  regression test this phase has written for every prior claim-copy/model
  slice).
- **Blast radius stays inside `domains/aerial.py` (new extractors),
  `project_closure.py` (new optional display helper), and
  `catalog_bind.py`/`library.py` only if seed enrichment is pursued later.**
  No `engineering_readiness.py`, no `project_continuity.py` change is
  implied by the graph itself.

---

## 10. Open questions for Engineer ★

1. **Node set confirmation:** `arm`/`plate`/`cage`/`standoff` as the Fase 1
   part-type set — does Engineer want to trim or extend this before an IC?
   (`hardware` and per-instance nodes are explicitly excluded per §2; this
   report does not treat that exclusion as provisional without cause.)
2. **BOM sub-line format** (§3) — is the proposed `└ arm ×4 — material`
   shape acceptable, or does Engineer want a different display convention?
   Not locked here.
3. **Seed enrichment sequencing** (§7): should the model IC include the
   `FrameSpec` per-part fields for the Armattan row (the one product that
   already proves the need), or ship the graph schema first and enrich the
   seed in a still-later IC? Both are coherent; this report leans toward
   including it in the same model IC since the evidence and sourcing
   pattern already exist, but does not decide it.
4. **Sequencing vs. the honesty IC:** unchanged question from the prior
   report — confirm (b) ordering (honesty IC, then this graph model IC) is
   still Engineer's preference now that the model itself has changed shape.

---

## 11. Thin non-binding IC outline (Buy (b) — graph model IC, after the honesty IC)

- **Files (illustrative):** `src/jarvis/schemas/action_schema.py`
  (`ComponentSpec.parent_key: str | None = None` — one field);
  `src/jarvis/domains/aerial.py` (new extractors for `arm`/`plate`/`cage`/
  `standoff` part-type text, mirroring `extract_frame_properties`'s
  regex/alias style; `configuration`/`wheelbase_mm` extractors from the
  prior model report, unchanged scope); `src/jarvis/core/project_closure.py`
  (new, purely additive BOM display helper reading `parent_key` — not
  touching `build_component_bom`'s `expected_keys`/bucket logic).
- **Behavior change:** users can declare frame sub-parts as sibling
  components with `parent_key="frame"`; BOM optionally shows them as
  display-only sub-lines. `Structure PASS`, `_frame_completeness`,
  architecture progress, `ASSEMBLY_READY`: **unchanged, regression-tested**.
- **Tests:** extraction unit tests per part type (declared text → correct
  node+properties, unrecognized → absent, never fabricated); BOM display
  helper tests (children rendered under the correct parent, orphaned
  `parent_key` — pointing at a nonexistent key — handled honestly, not
  crashing); the mandatory regression suite from §9.
- **Forbidden:** everything in §6's forbidden list; any `mounts_on`/spatial
  edge type; any `hardware`/per-instance node; any sum-of-parts mass rule;
  any `arm_count`/`configuration`↔`motor_count` cross-check; any
  `_derive_subsystem_verdict`/`_derive_overall`/`BLOCK_TO_COMPONENTS`
  change; seed JSON edits unless Engineer ★ explicitly bundles §7's seed
  enrichment into this same IC (open question #3).
