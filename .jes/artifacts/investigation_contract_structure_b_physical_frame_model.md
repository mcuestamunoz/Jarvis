# Investigation Contract — Structure B Physical Frame Model

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_structure_b_physical_frame_model.md`

**Status:** EXECUTED · Cursor review **PASS WITH NOTES** · Engineer ★ **rejected scalar Fase 1** → **B parts graph**  
**Report:** [investigation_report_structure_b_physical_frame_model.md](investigation_report_structure_b_physical_frame_model.md)  
**Review:** [investigation_review_structure_b_physical_frame_model.md](investigation_review_structure_b_physical_frame_model.md)  
**Follow-on:** [investigation_contract_structure_b_parts_graph.md](investigation_contract_structure_b_parts_graph.md)  
**★ package:** [engineer_ratification_structure_b_parts_graph.md](engineer_ratification_structure_b_parts_graph.md)  

**Parents (mandatory reading — do not re-derive from scratch):**
- [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md) — **PASS WITH NOTES** (Cursor)  
- [investigation_review_structure_a_pass_meaning.md](investigation_review_structure_a_pass_meaning.md)  
- Catalog Foundation IC-1→IC-3 CLOSED  

**Type:** **Model investigation** — define the minimum physical representation of `frame` as an assembly of structural components and declared properties (KNOW + CLAIM).  
**Not** “should we open Structure B?” — Engineer already said **yes** for representation.  
**Not** an Implementation Contract. **Do not implement.**

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE (fit inference, clearance validation, strength, FEA, CAD, meshes, fabricate).**

---

## 0. Role split

```text
Engineer  → ★ Physical Frame Model in KNOW+CLAIM; MEASURE out
Cursor    → this contract; review report; later IC only after ★ on model
Claude    → investigation_report_structure_b_physical_frame_model.md
Engineer  → ★ on model + whether honesty IC ships first
```

---

## 1. Locked stances

1. **Consume** Structure A PASS ✓/✗ table (prior report §3). Do not reopen MEASURE exclusions as optional Buys.
2. **DESCRIPCIÓN ≠ VALIDACIÓN.** More frame fields must not widen `Structure PASS` to “chassis verified.”
3. **Asymmetry to fix:** motor/prop/battery have identity + properties; frame after Catalog Foundation is still mostly `{mass, material, size_class}`.
4. **Target metaphor:** drone → structure → frame → {arms, plates, hardware, …} — system physical map, not CAD.
5. Prefer extending existing `ComponentSpec` / catalog / writer patterns over a parallel “chassis engine.”
6. Catalog Foundation stays CLOSED as a phase; seed enrichment may be *discussed* as later IC scope, not done here.

---

## 2. Objective

Answer:

> What is the **minimum correct physical model** for a frame (and its structural parts) so Jarvis can KNOW and CLAIM declared mechanical facts comparable to motor/prop/battery — **without** MEASURE/CAD — and how does that model compose with Structure A LEVEL A and Catalog Foundation identity?

---

## 3. Questions the report must answer

### A. Boundaries

1. Reaffirm KNOW / CLAIM / MEASURE split with concrete examples for frame fields.  
2. Which fields are **SÍ** (represent) vs **NO** (validate) — Engineer draft list to refine:

```text
SÍ: brazos, arm_count (with motor_count policy), configuración, placas,
    standoffs, material, masa, size_class, wheelbase (declared),
    dimensiones declaradas, mounting pattern declarado, componentes
    estructurales, identidad/SKU, provenance

NO: inferir geometría ausente, asumir que cabe, validar resistencia,
    FEA, CAD, meshes, fabricar
```

### B. Ontology

3. Is a **brazo** a separate `PhysicalComponent` / `ComponentSpec`, or a nested part record under frame?  
4. Is `frame` an **assembly** whose mass is (a) declared on the assembly, (b) sum of parts, (c) either with explicit provenance rules?  
5. What is universal vs type-dependent (quad-X vs hex vs deadcat…)?  
6. What does **“tipo” / configuration** mean as a field — vocabulary, closed enum, free string?  
7. Manufacturer vs user-declared vs Jarvis-inferred — and when is each `known` / `declared` / `estimated` / `unknown`?  
8. How does this interact with **Catalog Foundation** (`FrameSpec` today: mass_g, size_class, material, identity) — extend seed schema vs assembly-only in project state?

### C. Authority & hazards

9. **`arm_count` vs `motor_count`** — resolve the hazard named in prior investigations (reconcile / alias / forbid claim-closing).  
10. Declared **wheelbase / mounts** as KNOW+CLAIM only: what exact sentences may Jarvis say, and which are forbidden?  
11. Does richer description require changing **`Structure PASS`** evidence bits? Default lean from prior report: **No** — PASS meaning stays; optional `PASS *` honesty IC parallel.

### D. Minimum slice & Buy

12. Propose **Fase 1 model** (smallest useful assembly): required entities + fields + provenance rules.  
13. Explicit **out** for Fase 1 and for all of Structure B MEASURE.  
14. Buy recommendation: (a) model ★ only / doc, (b) thin honesty IC first then model IC, (c) single IC implementing Fase 1 model, (d) defer model — with rationale.  
15. Open questions for Engineer ★.

---

## 4. Seams to inspect

- Prior PASS-meaning report §2–§5 (mandatory)  
- `FrameSpec` / `library/frames/_datos.json` / `bind_frame_from_catalog`  
- `set_frame_material` / `_frame_completeness` / LEVEL A  
- `ComponentSpec` nesting patterns elsewhere (if any)  
- Control parity `PASS *` render path (honesty precedent)  
- BOM: single `frame` line vs future multi-line structural BOM  

---

## 5. Deliverable shape

1. Executive finding (Fase 1 model sketch + Buy lean).  
2. KNOW/CLAIM/MEASURE matrix for candidate fields.  
3. Ontology decision table (assembly vs parts; mass rules; arm_count policy).  
4. Allowed vs forbidden claim sentences for declared geometry.  
5. Composition with Structure A PASS (no silent widen).  
6. Catalog seed implications (read-only discussion).  
7. Out list.  
8. ★ questions.  
9. Thin non-binding IC outline only if Buy lean is (b) or (c).

---

## 6. Forbidden

- Implementing Structure B in `src/`  
- MEASURE / CAD / FEA / fit solvers  
- Widening Structure PASS to require geometry  
- Inventing manufacturer dimensions not in sources  
- Reopening Catalog Foundation as “broken”  

---

## 7. Engineer gate

**Do not write the report until Engineer `procede` on this contract.**  
If no → edit this contract in place.
