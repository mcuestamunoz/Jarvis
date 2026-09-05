# Investigation Contract — Structure B Parts Graph Ontology

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_structure_b_parts_graph.md`

**Status:** EXECUTED · Cursor review **PASS WITH NOTES** — awaiting Engineer ★  
**Report:** [investigation_report_structure_b_parts_graph.md](investigation_report_structure_b_parts_graph.md)  
**Review:** [investigation_review_structure_b_parts_graph.md](investigation_review_structure_b_parts_graph.md)  
**★ mandate:** [engineer_ratification_structure_b_parts_graph.md](engineer_ratification_structure_b_parts_graph.md)  

**Parents (mandatory — do not re-derive):**
- [investigation_report_structure_b_physical_frame_model.md](investigation_report_structure_b_physical_frame_model.md) — **PASS WITH NOTES**; Fase 1 **scalars rejected** by Engineer ★ (choose **B**)
- [investigation_review_structure_b_physical_frame_model.md](investigation_review_structure_b_physical_frame_model.md) — N1 named this fork
- [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md) — PASS ✓/✗ wall; honesty IC still valid parallel
- Catalog Foundation IC-1→IC-3 CLOSED  

**Type:** **Ontology / architecture investigation** — define the minimum **parts graph** for frame-as-assembly (KNOW + CLAIM only).  
**Not** an Implementation Contract. **Do not implement.**

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE (fit, clearance, strength, FEA, CAD, meshes, fabricate). Do not widen Structure PASS.**

---

## 0. Role split

```text
Engineer  → ★ B = parts graph; honesty first; config vocab OK; wheelbase in model path
Cursor    → this contract; review report; honesty IC may ship in parallel; model IC only after ★ on graph
Claude    → investigation_report_structure_b_parts_graph.md
```

---

## 1. Locked stances

1. **Target is a parts graph**, not three more scalars on a single flat frame `ComponentSpec`. Prior scalar Fase 1 is **not** the accepted model.
2. **DESCRIPCIÓN ≠ VALIDACIÓN.** Graph nodes/edges must not imply motors fit, clearance, strength, or fabricability.
3. **Structure PASS evidence bits stay unchanged** by the graph. Honesty (`PASS *`) remains a separate IC.
4. **`configuration` closed vocab** accepted starting set; never infer from `motor_count`.
5. **`arm_count` ↔ `motor_count`:** forbid claim-closing cross-check (prior hazard). Graph must not smuggle that check via edge types.
6. **Wheelbase** must be representable and **seed-enrichable** in the eventual model IC path (Engineer ★). Investigation decides *where* it lives (assembly property vs part vs catalog field) without inventing mm values not in sources.
7. Prefer composing with existing `ComponentSpec` / project `components` / writers / BOM over inventing a parallel “chassis engine” — but if nesting is required, **name the smallest schema change** honestly (this may be the first nesting precedent in the repo).
8. Catalog Foundation phase stays CLOSED; seed extension for wheelbase is **in scope for later model IC**, discussable here as schema impact only.

---

## 2. Objective

Answer:

> What is the **minimum correct parts-graph model** for a drone frame assembly (nodes, edges, identity, mass, configuration, wheelbase, catalog) so Jarvis can KNOW and CLAIM declared structural composition **without** MEASURE/CAD — and what is the smallest implementable Fase 1 slice of that graph?

Engineer reason to respect: structural parts are **not linear** (not a flat property list); topology matters for the mental/system map even when validation is out.

---

## 3. Questions the report must answer

### A. Graph shape

1. **Node types** for Fase 1 — required vs optional: `frame` (assembly root?), `arm`, `plate` (top/bottom?), `standoff`, `hardware`, other? Which stay **out** of Fase 1?
2. **Edge types** — `has_part`, `mounts_on`, count/multiplicity only, or typed relations? Directed? Can edges carry declared properties?
3. **Cardinality** — how are N identical arms represented: N nodes vs one `arm` node + `count`? (Compare motor `motor_count` precedent; justify if departing.)
4. **Where does the graph live in state?** Options to evaluate against live code:
   - nested records under `components["frame"].properties` (breaks flat scalar precedent — say so);
   - sibling keys in `design_properties.components` (`frame_arm`, …) with explicit parent refs;
   - a new assembly field on project state (new subsystem risk — flag if proposing);
   - other existing pattern found in tree.
5. **BOM / CLI display** — one assembly line vs multi-line structural BOM; what may each line claim?

### B. Fields on nodes (KNOW/CLAIM)

6. Place **`configuration`**, **`wheelbase_mm`**, **`mass_kg`**, **`material`**, **`size_class_inch`**, catalog identity — on which node(s)?
7. **Mass rule:** assembly-declared only / optional sum-of-parts with provenance / forbidden sum in Fase 1? Default lean from prior report was assembly-declared; re-decide under a graph.
8. **Provenance:** reuse `PropertyValue.source` (`declared`|`inferred`|`calculated`) — confirm; no new vocab unless proven necessary.
9. Allowed vs forbidden **claim sentences** for graph edges and part counts (extend prior §4 list; map to Structure A ✗ bullets).

### C. Catalog & PASS

10. How does **Catalog Foundation** `FrameSpec` / bind project onto an assembly root? Does bind create only the root, or also default child stubs? (No silent physics.)
11. Confirm **zero impact** on `_frame_completeness`, `_structure_evidence`, `_derive_subsystem_verdict` for Fase 1 — or name any *display-only* exception without changing PASS meaning.
12. **Wheelbase seed:** additive optional field on `FrameSpec` vs only on assembly after bind — recommendation for the model IC that will include seed enrichment.

### D. Minimum slice & Buy

13. **Fase 1 graph** — smallest useful node/edge set + fields. Explicit **out**.
14. **Implementation risk rank:** schema change size, migration of existing projects, test surface.
15. Buy: (a) ★ model doc only, (b) honesty IC first then graph model IC (Engineer already leans this), (c) multi-IC graph rollout (name slices), (d) retreat to scalars — only if graph proves infeasible without new subsystem; justify.
16. Open ★ questions (footnote honesty; which nodes in Fase 1; mass rule).

---

## 4. Seams to inspect

- `ComponentSpec` / `action_schema.py` — flat `properties` dict  
- `design_properties.components` dict usage (sibling components pattern)  
- `set_frame_material` / writers / `classify_component` / `_frame_completeness`  
- BOM render paths (`project_closure`, Continuity)  
- `FrameSpec` + `library/frames/_datos.json` + `bind_frame_from_catalog`  
- Motor `motor_count` precedent (scalar multiplicity)  
- Prior Structure B report §3–§7 (scalar rejection context)  
- Control / Structure honesty render path (parallel, do not implement)

---

## 5. Deliverable shape

1. Executive finding (Fase 1 graph sketch + where it lives in state + Buy).  
2. Node/edge catalog for Fase 1 vs out.  
3. State-placement decision table (with “new subsystem?” flag).  
4. KNOW/CLAIM/MEASURE matrix for graph fields.  
5. Mass + arm_count/motor_count + configuration policies.  
6. Allowed/forbidden claim sentences.  
7. Catalog bind + wheelbase seed implications.  
8. Composition with Structure PASS (no widen).  
9. Risk / migration notes.  
10. ★ questions.  
11. Thin non-binding IC outline only if Buy is (b) or (c).

---

## 6. Forbidden

- Implementing graph or honesty in `src/` under this contract  
- MEASURE / CAD / FEA / fit solvers  
- Widening Structure PASS / completeness to require graph nodes  
- Inferring `configuration` / part counts from `motor_count`  
- Inventing manufacturer dimensions not in cited sources  
- Reopening Catalog Foundation as “broken”  
- Smuggling a full CAD assembly model “because graph”

---

## 7. Engineer gate

**Do not write the report until Engineer `procede` on this contract.**  
If no → edit this contract in place.
