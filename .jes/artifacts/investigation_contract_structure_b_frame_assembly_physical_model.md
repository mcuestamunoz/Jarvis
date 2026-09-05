# Investigation Contract — Structure B Frame Assembly Physical Model

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_structure_b_frame_assembly_physical_model.md`

**Status:** CLOSED — Engineer Buy locked → IC READY  
**Review:** [investigation_review_structure_b_frame_assembly_physical_model.md](investigation_review_structure_b_frame_assembly_physical_model.md)  
**IC:** [implementation_contract_structure_b_frame_assembly_physical_model.md](implementation_contract_structure_b_frame_assembly_physical_model.md)  
**Engineer focus (2026-09-05):** KNOW Structure — **not** “add the next attribute.” Docs sync + thickness smoke **PASS** done first.

**Type:** Ontology / schema / claim investigation for a **minimum generalizable physical assembly model** of a drone frame.  
**Not** an Implementation Contract. **Do not implement.**

**Parents (mandatory — start here; do not pretend the graph does not exist):**
- Structure block CLOSED @ suite **2229** — Parts Graph Fase 1 + G-N1 are **product**
- Additive arms `thickness_mm` B2 CLOSED @ suite **2286** — [implementation_review_structure_b_thickness_arms_b2.md](implementation_review_structure_b_thickness_arms_b2.md)
- [investigation_report_structure_b_parts_graph.md](investigation_report_structure_b_parts_graph.md) — ontology baseline
- [investigation_report_structure_b_additive_enrichment.md](investigation_report_structure_b_additive_enrichment.md) — M0; plate thickness deferred as N1(b)
- Smoke: [engineer_cli_smoke_thickness_arms_b2.md](engineer_cli_smoke_thickness_arms_b2.md) — **PASS**

**Checkpoint:** `v0.3.6` · live suite **2286**

**Do not implement. Do not bump version. Do not weaken tests. Do not open MEASURE/CAD/FEA/fit/clearance/mounts. Do not widen Structure PASS into structural validation. Do not invent Conversation Engine.**

---

## 0. Role split

```text
Engineer → named KNOW Structure focus; wants assembly model, not attribute drip
Cursor   → this contract; review report; IC only after Engineer Buy
Claude   → investigation_report_structure_b_frame_assembly_physical_model.md
```

---

## 1. Why this investigation (and what it is not)

**Wrong next step (forbidden as default Buy):**

```text
arm thickness → plate thickness → another field → another field …
```

That is horizontal growth without a coherent assembly model.

**Right question:**

> What is the **minimum generalizable model** so a catalog/free-text frame is a **composed physical assembly** Jarvis can KNOW — keeping **M0** (root mass sole physics authority), **without** geometry, fit, mounts, clearance, CAD, FEA, or structural-adequacy claims?

**Baseline that already exists (do not re-derive as if greenfield):**

```text
components["frame"] + parent_key children:
  frame_arm | frame_plate | frame_cage | frame_standoff
  fields today: count, material, (arm only) thickness_mm
  BOM └ display-only
  Structure PASS * = identity / class LEVEL A — no chassis geometry
```

This investigation may conclude any of:

- `parent_key` + shared physical property bag is **enough** (schema extension only); or  
- plates need **typed roles** (main/top/bottom) before any plate thickness; or  
- a common `structure_part` physical schema is required; or  
- hardware node / mass-per-part stays **out** until sources exist; or  
- **plate thickness is premature** as the next IC.

**The investigation decides.** Do not assume plate thickness is next.

---

## 2. Locked stances

1. **M0:** root `mass_kg` / `structure_mass_override_kg` remains the only mass that drives physics. Part masses, if ever modeled, are not Σ→physics in this Buy space unless Engineer later overrides M0 (default: **do not** recommend M2/M3).
2. **DESCRIPCIÓN ≠ VALIDACIÓN.** Assembly KNOW must not imply strength, fit, or “chasis funciona.”
3. **`Structure PASS *` may evolve wording only if justified** (e.g. toward “assembly físico declarado — sin validación geométrica/estructural”) — recommend in claim matrix; **do not** change ERF predicates in this investigation.
4. **`arm_count` ↔ `motor_count` claim-closing remains forbidden.**
5. Prefer extending existing `ComponentSpec` / writers / BOM over a new chassis subsystem.
6. No fabricated g/mm from density×volume or from “Included” lists without explicit source policy (G-N2 stays debt unless Buy needs counts).
7. IDLE rebind B2/B3 and thickness arms B2 stay closed — cite only as constraints.

---

## 3. Governing questions (answer all)

### A. Know — baseline map (file:line)

1. What can a frame assembly already represent today (root + four part keys + thickness arm)?
2. What can it **not** represent (multi-plate thicknesses, part mass, hardware, dimensions, roles)?
3. How do catalog projection and free-text currently create/skip children?

### B. Target model (minimum generalizable)

4. Propose the **smallest** assembly model (nodes, roles, shared properties) that is coherent for catalog + free-text frames **in general**, not only Armattan.
5. For each of: arms, plates (incl. main/top/bottom question), cage, standoffs, hardware — **in / out / later** with reason.
6. Shared physical property set (candidates: `material`, `thickness_mm`, `count`, `mass_kg`, length/width/dims) — which are **common schema**, which stay type-specific, which stay out?
7. Explicitly answer: **Is plate thickness a valid next IC, or is plate role typing a prerequisite?** (Engineer’s decision hinge.)

### C. Mass & provenance

8. Reconfirm M0 for any proposed part `mass_kg`.
9. If part masses are in the model as declared-only, what claims are allowed vs forbidden when root ≠ Σ?

### D. Claims / PASS *

10. Claim matrix for “composed assembly declared” vs forbidden structural/geometry claims.
11. Should the Structure PASS * footnote change after a future model IC — and to what exact Spanish string — **only if** the model actually justifies it? Default lean: keep current footnote until an implemented model warrants the change.

### E. Buy

Exactly one primary:

| Option | Meaning |
|---|---|
| **B0** | No IC now — model doc only; stay on Fase 1 + arm thickness |
| **B1** | Docs/claim lock only (matrix + footnote candidate) — no schema |
| **B2** | Schema IC: shared part physical props + **plate role typing** (or justify why single `frame_plate` remains) — still M0, still no MEASURE |
| **B3** | Schema IC: extend props only (e.g. plate thickness under explicit main-plate rule) **without** role split — only if you prove roles are unnecessary |
| **B4** | Split: typing/schema now; mass-per-part / hardware later |

Justify. Prefer the smallest Buy that stops attribute-drip without premature plate thickness.

### F. Non-goals

MEASURE · CAD/FEA · mounts/clearance · Σ→physics · arm↔motor gate · ESC/Control catalog · System-level Optimization · implementing anything.

### G. IC skeleton (if Buy ≠ B0/B1)

≤25 lines: files, schema, projection rules, tests, forbidden.

---

## 4. Surfaces to inspect

`action_schema.ComponentSpec` · `catalog_bind.frame_part_specs_from_catalog` · `upsert_frame_part` · `_structure_part_completeness` · `_frame_part_sublines` · `library/frames/_datos.json` + `FrameSpec` · seed source pages for **multi-plate** reality (TBS / Armattan) · `_structure_evidence` / PASS * CLI footnote · Vision §8 debt list.

---

## 5. Done criteria

- Report A–G filled with `file:line` evidence  
- Explicit answer to **plate thickness vs plate roles**  
- One Buy option  
- Statement: “Fase 1 graph is baseline, not greenfield”  
- No `src/` edits  

---

## 6. After review

Cursor investigation review → Engineer Buy → Implementation Contract only if Buy ∈ {B2,B3,B4}.  
Then re-evaluate System optimization vs Prop/Energy vs further KNOW.
