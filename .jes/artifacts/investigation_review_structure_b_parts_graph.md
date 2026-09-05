# Investigation Review — Structure B Parts Graph Ontology

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_b_parts_graph.md](investigation_contract_structure_b_parts_graph.md)  
**Report:** [investigation_report_structure_b_parts_graph.md](investigation_report_structure_b_parts_graph.md)  
**★ mandate:** [engineer_ratification_structure_b_parts_graph.md](engineer_ratification_structure_b_parts_graph.md)  
**Parents:** scalar Fase 1 rejected; Structure A PASS ✓/✗ wall

## Verdict

**PASS WITH NOTES**

Claude delivered a coherent minimum graph that respects KNOW≠MEASURE, avoids a
new assembly subsystem, and names the first nesting precedent honestly
(`ComponentSpec.parent_key`). Armattan multi-material evidence is real in the
seed `source_note`. Buy (b) honesty → graph model remains sound.

Ready for Engineer ★ on node set / BOM display / seed bundling — **not** for
silent implementation.

---

## Checklist

| Criterion | Result |
|---|---|
| Graph shape (nodes/edges) | **Pass** — part-type + count; single `has_part` via `parent_key` |
| State placement | **Pass** — siblings + `parent_key`; nested-in-properties / new assembly field rejected with reasons |
| Mass / arm↔motor / configuration | **Pass** — assembly mass only; no cross-checks; config on root |
| Allowed/forbidden claims | **Pass** — extends prior ✗ wall |
| Structure PASS unchanged | **Pass** — `_structure_evidence` + `BLOCK_TO_COMPONENTS["structure"]=["frame"]` |
| Catalog bind / wheelbase | **Pass** — root-only bind; wheelbase on root; seed discussable |
| Buy lean | **Pass** — (b) honesty then graph |
| No code | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `ComponentSpec` has no nesting / no `parent_key` today | **Confirmed** — `action_schema.py:143-163` |
| `PropertyValue` scalar-only | **Confirmed** — `{value, unit, confidence, source}` |
| `DesignProperties.components: dict[str, ComponentSpec]` | **Confirmed** — `state_schema.py:126` |
| `BLOCK_TO_COMPONENTS["structure"] == ["frame"]` | **Confirmed** — `system_architecture_catalog.py:162` |
| `_structure_evidence` reads only frame + calc + sim | **Confirmed** — `engineering_readiness.py:1043-1050` |
| Armattan `source_note` cites CF plate/arms + Ti cage + Al standoffs | **Confirmed** — `library/frames/_datos.json` `armattan_rooster_5in` |
| Seed `material` still single `"fibra de carbono"` | **Confirmed** — incomplete vs source_note (report’s point stands) |
| BOM classifies **extra** keys not in architecture | **Confirmed** — `build_component_bom` lines 618–622 — see **N1** |

---

## Notes

### N1 — Child keys would become peer BOM lines today (IC must filter)

Report §3 says children are display-only and “never enter
`build_component_bom`’s `expected_keys`/gap logic.” That is only half true:

- They will **not** appear in `missing` (not in `BLOCK_TO_COMPONENTS`) — good.
- They **will** be classified in the “extra components” loop and land in
  `defined` / `declarative` / `incomplete` as **peer** top-level BOM entries
  if they carry e.g. `material` (in `_MEASURABLE`).

Any model IC **must** explicitly exclude `parent_key is not None` from
top-level BOM buckets and render them only as sub-lines under the parent.
Otherwise the CLI shows both a peer `frame_arm` line **and** a sub-line — or
worse, a peer line alone that looks like a second architecture component.

### N2 — Dict key naming not locked

Exec summary uses `components["frame_arm"]`; node table says type `arm`.
IC must lock one convention (`frame_arm` / `frame_plate` / … vs bare `arm`)
plus how extractors choose `suggested_key`, so orchestrator does not treat
parts as free-floating acquisition targets.

### N3 — Seed enrichment vs Engineer’s prior ★

Engineer already ★’d **wheelbase in the model IC path**. Report Q3 is really
about **per-part materials** on `FrameSpec` (Armattan Ti/Al). Lean to bundle
with graph IC is coherent; still needs ★. Do not invent mm/material values
beyond cited sources.

### N4 — First nesting precedent

`parent_key` is correctly named as the first intra-project parent/child
reference. Acceptable under locked stance #7 **if** Engineer ★ accepts that
precedent. Not a new subsystem; still a real schema contract change.

### N5 — Honesty sequencing

Report Q4: Engineer already said honesty first. Reconfirm only if the graph
shape changed that preference (Cursor sees no reason it should).

---

## Next

Engineer ★:

1. Fase 1 nodes = `arm` / `plate` / `cage` / `standoff` (+ hardware out)?  
2. BOM sub-line shape OK?  
3. Bundle seed (`wheelbase_mm` + Armattan per-part materials) into model IC?  
4. Confirm honesty IC still ships first?

Then: honesty IC draft → graph model IC (after ★). No `src/` until IC + `procede`.
