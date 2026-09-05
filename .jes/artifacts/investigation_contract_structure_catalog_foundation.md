# Investigation Contract — Structure Catalog Foundation (Frames)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code (or Cursor if same session)  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_structure_catalog_foundation.md`

**Status:** 🟢 Investigation **EXECUTED** · review **PASS WITH NOTES** · Engineer ★ **RATIFICADO** (B0)  
**Report:** [investigation_report_structure_catalog_foundation.md](investigation_report_structure_catalog_foundation.md)  
**Review:** [investigation_review_structure_catalog_foundation.md](investigation_review_structure_catalog_foundation.md)  
**★:** [engineer_ratification_structure_catalog_foundation.md](engineer_ratification_structure_catalog_foundation.md)  
**Implementation Buy:** 🔴 **NOT opened** (IC-2/IC-3 Not Buy; IC-1 not named)  
**Catalog as next Buy:** 🔴 deferred under B0 — IC-1 only if Engineer reopens  
**Prior slice CLOSED:** Structure Foundations claim-copy (suite **2171**)  

**Type:** Product / knowledge investigation. Determine whether **Catalog Foundation — Frames** is the next highest-value leap on Structure, and what minimum honest contract it would need.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** tag **`v0.3.6`** · live tree includes claim hygiene + control parity + Structure Foundations claim-copy (suite **2171**).

**Do not implement. Do not bump version. Do not weaken tests. Do not open CAD, FEA, layout params as Buy, or wire `catalog_bound` into Structure PASS. Do not extend `CatalogRef.family` in this investigation — reachability is a seam to describe, not a fix to ship.**

---

## 0. Role split

```text
Engineer  → approved this Investigation Contract; layout/CAD out; Buy pending report
Cursor    → contract hygiene; investigation review; later IC only after ★ + procede
Claude    → investigation_report_structure_catalog_foundation.md
Engineer  → ★ on model / Buy (or “not yet”) after review
Claude    → implements from IC only — never from this investigation
```

---

## 1. Locked stances (do not contradict)

1. **Claim-copy is CLOSED.** Do not reopen BOM/Continuity class wording unless a catalog model **forces** a seam.
2. **Structure A remains foundation.** LEVEL A class screening stays; catalog must compose with it, not replace it.
3. **`catalog_bound = true` must never mean Structure validated / load-ready / fabricable.** Evidence axes stay separate (`defined` / `calculated` / `simulated` / `validated` / `catalog_bound`).
4. **Curated honest catalog; never invent SKUs.** Same Physical Catalog v1 philosophy (`docs/PHYSICAL_COMPONENT_CATALOG_V1.md`).
5. **Layout params and CAD/FEA are out of Buy recommendations** unless the investigation finds they **block** Catalog Foundation itself (they should not).
6. Frame catalog was historically **deferred** (catalog v1 §6/§10). Reopening requires Engineer Buy after this investigation — not silent scope creep.
7. Prefer extending existing `ComponentLibrary` / `CatalogRef` / bind patterns over a parallel Structure catalog architecture.
8. **Candidate fields ≠ required fields.** The investigator may classify any candidate as **Not yet** without obligation to incorporate it. Manufacturer publishing a number does **not** license Jarvis to close a claim from it (especially `wheelbase` ↛ tip clearance / “cabe”).
9. **Claim-closing chain is mandatory in the report:**

```text
IDENTITY  →  KNOWN PROPERTY  →  CLAIM SUPPORTED
```

Never:

```text
CATALOG SKU  →  ENGINEERING VALIDATION
```

10. **Phased scope is preferred over one “Frame Catalog System” IC.** Report must evaluate at least: schema+seed vs bind+BOM identity vs assist — and may recommend IC-1 / IC-2 / IC-3 with IC-2 possibly enough for Fase 1.

---

## 2. Objective

Answer:

> Is Catalog Foundation for **frames** the next highest-value Structure leap after claim-copy, and if so what is the **minimum honest field/claim model** (identity, properties, provenance, what closes vs what must not)?

The report may conclude **No — catalog is not yet the next Buy** if incremental engineering value is insufficient. That outcome is success, not failure.

---

## 3. Questions the report must answer

1. What **new value** does a frame `catalog_bound` add vs Structure A alone?
2. What are the **minimum fields** a frame SKU needs? (subset of candidates — not the full list by default)
3. What **sources / evidence** can back those fields?
4. What **claims** does binding actually unlock?
5. What **claims** must binding **not** unlock?
6. How does catalog interact with **Structure A** (mass / material / `size_class_inch` / LEVEL A)?
7. How does it affect **BOM / Continuity / ERF** (including `catalog_bound` write-only today)? Describe reachability as a seam; **do not** “fix” it in this investigation.
8. Which **real SKUs** (few) would be enough to validate the model?
9. What is the **minimum catalog scope** (schema vs library seed vs bind vs assist)? Prefer phased IC-1/IC-2/IC-3 if that is cleaner.
10. What stays **out**? → geometry, strength, CAD, FEA, tip-clearance, layout-as-default.
11. **What user/system decision becomes possible, more reliable, or more traceable with a catalog-bound frame that is not possible with Structure A alone?** (If the honest answer is only “show a prettier name,” lean **No / not yet** on Buy.)
12. **What minimum evidence is required for each physical field to become authoritative rather than merely catalog-declared?**

Also classify each candidate field (obligation = classify, not adopt):

| Bucket | Meaning |
|---|---|
| Identity | Who/what product |
| Physical | Measurable property used by Jarvis physics or Structure A |
| Declarative | Optional label / config that does not close claims alone |
| Provenance | How we know (source_url, identity_status, …) |
| Claim-closing | May honestly support a **named** claim (state the claim) |
| Not yet | Explicitly do not introduce |

Candidate list:  
`manufacturer`, `model`, `catalog_ref`, `mass_kg`/`mass_g`, `size_class_inch`, `material`, `configuration`, `arm_count`, `wheelbase`.

For claim-closing fields, the report must show:

```text
IDENTITY
   ↓
KNOWN PROPERTY   (with evidence bar from Q12)
   ↓
CLAIM SUPPORTED  (exact sentence Jarvis may say)
```

Forbidden illusion examples the report must explicitly reject as unlocked:

- “El diseño estructural es correcto.”
- “Los motores caben.”
- “La hélice tiene clearance.”
- “El frame soportará el empuje.”
- “El sistema está listo para ensamblar.”

---

## 4. Code / doc seams to inspect (non-exhaustive)

- `CatalogRef.family` Literal — currently `"motor" | "battery" | "propeller" | "esc"` (**no `frame`**)
- `_structure_evidence` → `catalog_bound = _catalog_ref_set(..., "frame")` (already computed; structurally unreachable for honest bind — **describe only**)
- `_derive_subsystem_verdict` — confirm `catalog_bound` still unused for PASS
- `get_frame_mass_kg` / mass path into calc — what changes if mass comes from bind vs freeform
- `invalidate_diverged_catalog_refs` / motor·battery·prop bind — frankenstein precedent
- `library/` — motors/batteries/props/materials/esc; **no `frames/`**
- `ComponentLibrary` / `EscSpec` as precedent for a late-added family
- `_bom_sku_resolved` / BOM identity
- `docs/PHYSICAL_COMPONENT_CATALOG_V1.md` — frame SKU still listed deferred

---

## 5. Deliverable shape

Report must include:

1. Executive finding (**Yes / No / Not yet** — with engineering-decision proof from Q11).
2. Field authority table (buckets; Not yet allowed freely).
3. Claim unlock / non-unlock matrix + IDENTITY→PROPERTY→CLAIM chains for each closing claim.
4. Q12 evidence bar: catalog-declared vs authoritative per physical field.
5. Interaction with Structure A + honesty rule for `catalog_bound` (no reachability fix).
6. Recommended **phased** scope for later ICs (IC-1 schema+seed / IC-2 bind+BOM / IC-3 assist) — which is enough for Fase 1.
7. Explicit **out** list.
8. Risks / open questions for Engineer ★.
9. **Do not** draft full implementation file lists as authoritative; a thin non-binding outline is OK after ★ section.

---

## 6. Forbidden in this investigation

- Implementing `library/frames/`, extending `CatalogRef`, bind writers, assist UX
- Making Structure PASS require `catalog_bound`
- Recommending CAD/FEA/layout as the immediate next Buy
- Inventing SKUs or fabricated structural ratings
- Treating “manufacturer published X” as automatic claim license
- Weakening or deleting tests
