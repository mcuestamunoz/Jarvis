# Investigation Contract — Structure B additive enrichment (mass / part fields)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_structure_b_additive_enrichment.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer Buy locked · IC ready  
**Report:** [investigation_report_structure_b_additive_enrichment.md](investigation_report_structure_b_additive_enrichment.md)  
**Review:** [investigation_review_structure_b_additive_enrichment.md](investigation_review_structure_b_additive_enrichment.md)  
**IC:** [implementation_contract_structure_b_thickness_arms_b2.md](implementation_contract_structure_b_thickness_arms_b2.md)  
**Buy (2026-09-05):** B2 YES · N1 **(b) arms-only** · M0 confirmed  
**Engineer mandate:** `procede` on Cursor’s **corrected** reading of the Structure B reflection (2026-09-04): do **not** reopen Structure B ontology; investigate only the **minimum additive** slice on the existing parts graph.

**Correction (locked — do not ignore):**

```text
WRONG question (reflection draft):
  "¿Cuál es el modelo mínimo para representar un frame como assembly?"
  → ALREADY ★ ANSWERED — Parts Graph Fase 1 + G-N1 CLOSED @ suite 2229

RIGHT question (this contract):
  "¿Cuál es el mínimo ADITIVO sobre el grafo Fase 1 (campos por pieza +
   regla de masa) que aporta ingeniería sin poses, mounts_on, clearance,
   CAD/FEA, ni ampliar Structure PASS?"
```

The CLI `└ arm / cage` is **not** a germ awaiting Structure B — it **is** Fase 1 product. This investigation starts **from that model**.

**Type:** Knowledge / claim investigation — additive fields + mass composition policy + claim matrix.  
**Not** an Implementation Contract. **Do not implement.**

**Parents (mandatory — cite; do not re-derive):**
- [engineer_ratification_structure_block_closed.md](engineer_ratification_structure_block_closed.md) — Structure block ★ CLOSED
- [investigation_report_structure_b_parts_graph.md](investigation_report_structure_b_parts_graph.md) + review — ontology locked
- [implementation_contract_structure_b_parts_graph.md](implementation_contract_structure_b_parts_graph.md) — Fase 1 shipped
- [implementation_contract_structure_b_gn1_freetext_root_parts.md](implementation_contract_structure_b_gn1_freetext_root_parts.md) — G-N1 shipped
- Vision §8 Structure B CLOSED — `docs/ENGINEERING_READINESS_VISION.md` (sum-of-parts listed as debt / MEASURE wall)

**Checkpoint:** `v0.3.6` · live tree includes Structure close **2229** + IDLE rebind B2/B3 **2276**

**Do not implement. Do not bump version. Do not weaken tests. Do not reopen Structure PASS meaning. Do not invent CAD/FEA/fit.**

---

## 0. Role split

```text
Engineer ★ → OK corrected path (additive enrichment, not Structure B reopen)
Cursor     → this contract; later IC only after ★ Buy
Claude     → investigation_report_structure_b_additive_enrichment.md
Cursor     → investigation review
Engineer ★ → Buy lock (fields / mass rule / claims)
```

---

## 1. Locked stances (inherit + tighten)

1. **Parts graph Fase 1 stays the ontology.** Keys `frame` + `frame_arm` / `frame_plate` / `frame_cage` / `frame_standoff` + `parent_key` are **not** up for redesign. Do not propose nested JSON under `frame.properties` as a parallel model.
2. **DESCRIPCIÓN ≠ VALIDACIÓN.** Enrichment must not imply strength, fit, clearance, fabricability, or “chasis verificado.”
3. **`Structure PASS *` + footnote stay.** Additive fields must not change `_structure_evidence` / `_derive_subsystem_verdict` unless Buy explicitly recommends a **display-only** honesty tweak (Engineer ★ stop if recommending PASS predicate change).
4. **`arm_count` ↔ `motor_count` claim-closing remains forbidden.**
5. **No poses / relative positions / mounting points / clearances** in this investigation’s Buy (that is a later B.2 spatial slice — name it as out, do not design it here).
6. **No new subsystem** (no chassis engine). Prefer `PropertyValue` on existing part specs + writers.
7. Prefer **not** inventing per-part mm/g values absent from catalog `source_note` / seed — honesty over completeness.
8. Idle rebind B2/B3 is orthogonal — do not reopen as Structure work.

---

## 2. Governing question (single)

> What is the **smallest additive** extension to the existing Structure B parts graph (per-part fields + mass composition rule + claim sentences) that improves engineering *knowledge* of the frame assembly **without** geometry/validation — and should Jarvis Buy it now, later, or not?

---

## 3. Questions the report must answer

### A. Know — what Fase 1 already has (cite file:line)

1. Root fields today (`mass_kg`, `material`, `size_class_inch`, `configuration`, `wheelbase_mm`, `catalog_ref`).
2. Part fields today (`count`, `material`, …) and completeness (`_structure_part_completeness`).
3. How physics / `set_frame_material` / calc read **assembly** mass today (prove sum-of-parts is **not** used).
4. BOM `└` rendering — what attributes are shown vs omitted.

### B. Additive field candidates (per part type)

5. Rank candidate fields for Fase 1.x: `mass_kg` (per part), `length_mm`, `width_mm`, `thickness_mm`, `hardware` as new node type, split top/bottom plate, other.
6. For each: **in / out / later** with one-line reason. Default lean: **mass_kg on parts optional**; dimensions only if seed/catalog can support without invention; **hardware node out** unless proven necessary for mass honesty; top/bottom plate split **out** of minimum.
7. Catalog seed impact: which existing `library/frames` rows could gain real per-part mass/dims vs must stay root-only (Armattan vs TBS honesty).

### C. Mass composition rule (central)

8. Propose exactly one primary policy among:

| Option | Meaning |
|---|---|
| **M0** | Keep assembly-declared only; part masses display-only never drive physics |
| **M1** | Optional part `mass_kg`; physics still uses root `mass_kg` only; Continuity/BOM may show Σ as **informational** when all parts have mass |
| **M2** | When all required part masses present, **replace** root mass with Σ (and mark provenance); else keep root |
| **M3** | Always prefer Σ when any part mass exists (dangerous — justify only if proven safe) |

9. Conflict cases: root says 125 g, Σ says 140 g — what may Jarvis claim? What must it refuse?
10. Interaction with free-text G-N1 / catalog rebind clear-children (B2) — any new orphan/mass hazard?

### D. Claims matrix

11. Allowed vs forbidden sentences after enrichment, extending Structure A ✗ wall, e.g.:

| Sentence | Allowed? |
|---|---|
| “Frame declares 4 carbon arms” | ? |
| “Frame mass is sum of parts (125 g)” | ? |
| “Arms length 108 mm from catalog” | ? |
| “Chassis is structurally adequate” | ✗ (confirm) |
| “Changing arms recalculates system mass” | under which M-option? |

12. Confirm `Structure PASS *` footnote still honest if part masses exist.

### E. Buy

13. Exactly one primary Buy:

| Option | Meaning |
|---|---|
| **B0** | No IC — leave sum-of-parts / dims as debt; Structure stays CLOSED |
| **B1** | Docs/claim lock only (matrix in vision/agenda) — no schema |
| **B2** | Schema + writers: optional per-part `mass_kg` (+ maybe thickness) + BOM display; physics unchanged (**M0/M1**) |
| **B3** | B2 + mass composition policy **M2** wired into calc path — **Engineer ★ stop** if recommended |
| **B4** | Defer to a future “spatial B.2” investigation; this thread B0 |

Default Cursor lean: **B2 + M1** (know more, don’t silently rebind physics) **or B0** if seed cannot support honest part masses. Reject B3 unless evidence is strong.

### F. Explicit non-goals

Re-deriving node types · nested assembly engine · poses/mounts/clearance · CAD/FEA · arm↔motor gate · Structure PASS widen · IDLE rebind reopen · inventing Armattan part masses from “Included” without source (G-N2 stays debt unless Buy needs it).

### G. IC skeleton (only if Buy ∈ {B2, B3})

≤25 lines: files, fields, mass rule, tests, forbidden.

---

## 4. Surfaces to trace (file:line required)

| Surface | Find |
|---|---|
| Schema | `ComponentSpec`, part keys, `parent_key` |
| Completeness | `_frame_completeness`, `_structure_part_completeness` |
| Writers | `set_frame_material`, `upsert_frame_part`, `clear_frame_part_children`, G-N1 extract |
| Physics mass | how `mass_kg` / structure mass enters calculate |
| ERF | `_structure_evidence` — confirm unchanged by parts |
| BOM | `format_bom_lines` `└` attributes |
| Seed | `library/frames/_datos.json` — what part fields exist today |
| Vision debt | §8 “sum-of-parts mass” bullet |

---

## 5. Field reconstruction

Use `tmp_path` only:

1. Armattan bind → list part keys + properties present.  
2. Free-text G-N1 root+parts → same.  
3. Confirm calculate uses root mass, not Σ (read code + optional numeric check).

---

## 6. Done criteria

- Report A–G filled  
- Every factual claim cites `file:line` or named test  
- One Buy + one mass policy (M0–M3)  
- Explicit statement: “Structure B ontology not reopened”  
- No `src/` edits  

---

## 7. After review

Cursor review → Engineer ★ on Buy/M-policy → IC only if Buy ≠ B0/B1/B4.
