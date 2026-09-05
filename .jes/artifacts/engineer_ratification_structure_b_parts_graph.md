# Engineer Ratification — Structure B ★ decisions (post scalar report)

**Date:** 2026-09-04  
**Authority:** Engineer  

**Parents:**
- [investigation_report_structure_b_physical_frame_model.md](investigation_report_structure_b_physical_frame_model.md) — Cursor **PASS WITH NOTES**
- [investigation_review_structure_b_physical_frame_model.md](investigation_review_structure_b_physical_frame_model.md)

---

## Locked ★

| # | Decision |
|---|---|
| **Ontology** | **B — parts graph** (not A scalars, not C plate-count middle). Frame is a non-linear assembly; arms/plates/hardware are structural parts, not more flat properties on one box. |
| **Sequencing** | **Honesty IC first** (`Structure PASS *`), then model IC(s). Separate ICs. |
| **`configuration` vocab** | Starting closed set OK: `quad_x` / `quad_plus` / `hex` / `deadcat` / `tricopter` (match-from-text; never infer from `motor_count`). |
| **Wheelbase seed** | Enrich `library/frames/_datos.json` **inside** the model IC path (not deferred forever). Exact placement (assembly node vs FrameSpec field) is for the graph investigation. |

## Supersedes

Prior report’s Fase 1 lean (**three scalars on one `ComponentSpec`**, “arm is not a separate component”) is **rejected as the target model**. That report remains valid evidence that **today’s codebase has no nesting precedent** — which is exactly why a **new ontology investigation** is required before any model IC.

## Still open (not blocking the next investigation contract)

- Structure `PASS *` footnote exact string + blanket vs conditional (honesty IC).  
- Plates/standoffs/hardware: which are Fase-1 graph nodes vs later.  
- Mass rule under a graph (assembly-declared only vs optional sum with provenance).  

## MEASURE wall (unchanged)

No fit, clearance, strength, FEA, CAD, meshes, fabricate. Graph = KNOW+CLAIM structure map only. Do **not** widen `Structure PASS` to “chassis verified.”

## Next

1. **ICs drafted** (report leans locked into contracts):
   - [implementation_contract_structure_honesty_pass_star.md](implementation_contract_structure_honesty_pass_star.md)
   - [implementation_contract_structure_b_parts_graph.md](implementation_contract_structure_b_parts_graph.md)
2. Engineer `procede` on **honesty IC** first.  
3. Graph IC only after honesty REVIEWED PASS.  
4. MEASURE wall unchanged.

## Locked into ICs from report / prior ★

| Item | Lock |
|---|---|
| Sequencing | Honesty → graph |
| Footnote | Blanket `* Structure: identidad / clase nivel A — sin geometría de chasis` |
| Nodes | `frame_arm` / `frame_plate` / `frame_cage` / `frame_standoff` |
| BOM | `└` sub-lines; N1 filter peers |
| Seed | wheelbase + Armattan part materials when sourced |
| Config vocab | `quad_x` / `quad_plus` / `hex` / `deadcat` / `tricopter` |
