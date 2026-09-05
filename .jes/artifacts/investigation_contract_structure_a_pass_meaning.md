# Investigation Contract — Structure A PASS meaning (frontier → Structure B)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output:** `.jes/artifacts/investigation_report_structure_a_pass_meaning.md`

**Status:** EXECUTED · Cursor review **PASS WITH NOTES** · meaning table ready for ★  
**Report:** [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md)  
**Review:** [investigation_review_structure_a_pass_meaning.md](investigation_review_structure_a_pass_meaning.md)  
**Follow-on:** Structure B Physical Frame Model contract — [investigation_contract_structure_b_physical_frame_model.md](investigation_contract_structure_b_physical_frame_model.md)  
**★ mandate:** [engineer_ratification_structure_a_pass_meaning.md](engineer_ratification_structure_a_pass_meaning.md)  

**Type:** Product / knowledge investigation. Register exactly what **`Structure PASS`** means under Structure A, and whether any **minimum mechanical leap** toward Structure B is justified — **without** implementing Structure B.  
**Not** an Implementation Contract. **Do not implement.**

**Prior block CLOSED:** Catalog Foundation IC-1→IC-3 (suite **2197**) + Engineer manual CLI walk 2026-09-04.

**Checkpoint base:** tag **`v0.3.6`** · live tree includes claim hygiene, control parity, Structure Foundations claim-copy, Catalog Foundation.

**Do not implement. Do not bump version. Do not weaken tests. Do not open CAD, FEA, layout params, wheelbase, mounting patterns, clearance physics, or chassis BOM decomposition as Buys in this investigation’s recommendations unless Engineer later ★’s them — the report may name them only as out / later.**

---

## 0. Role split

```text
Engineer  → closed Catalog Foundation; ordered this frontier investigation (no Structure B code)
Cursor    → this contract; later review of report; IC only if Engineer ★ Buy after ★ on meaning
Claude    → investigation_report_structure_a_pass_meaning.md only
Engineer  → ★ on Structure A PASS meaning; then decide Structure B / defer / other
```

Cursor generates this contract. Cursor does **not** open/execute the investigation until Engineer `procede`.

---

## 1. Locked stances (do not contradict)

1. **Catalog Foundation is CLOSED.** Do not reopen frame schema/bind/assist as the default fix.
2. **Frame implementation is not the defect.** Structure A’s conceptual narrowness is.
3. **Do not “fix” Structure PASS by widening it** in code during this investigation.
4. **Structure B (wheelbase, mounts, clearance, layout, arms/plates, CAD, FEA) is not pre-authorized.** Investigation may conclude **defer Structure B** entirely.
5. Preserve the walk signal: `ASSEMBLY READY` can coexist with weak propulsion evidence and Control declaration-only — software-complete ≠ engineering-demonstrated.
6. Prefer composing with existing LEVEL A (`frame_class_compatibility_state` / GAP-FRAME-*) over inventing parallel structure truth.

---

## 2. Objective

Answer:

> What should **`Structure PASS`** mean exactly in Jarvis under Structure A, and what is the **minimum honest next leap** (if any) from `frame = SKU + mass + class` toward a useful mechanical representation **without** turning Jarvis into a CAD prematurely?

Engineer framing to respect:

```text
STRUCTURE A — TODAY
  Frame: identity, mass, material, size_class_inch
    → compare to propeller diameter
    → LEVEL A PASS

         ↓ WALL ↓

STRUCTURE B — NOT OPEN
  configuration, arm_count, wheelbase, dimensions,
  mounting, motor positions, FC/battery mounting,
  clearances, physical subcomponents → geometry → layout → CAD/FEA
```

> The frame is no longer the hole. The hole is the **physical meaning of “frame.”**

---

## 3. Questions the report must answer

1. **What does `Structure PASS` mean today in code?** Trace `_structure_evidence`, `_derive_subsystem_verdict`, LEVEL A gaps, completeness — cite paths. Separate **evidence bits** from **userdict**.
2. **What may a user reasonably (mis)read** from CLI `Structure PASS` / `ASSEMBLY READY` after a catalog frame pick? Use the Engineer walk as primary evidence.
3. **Propose a locked meaning table** for Engineer ★:

```text
Structure A PASS means:   (✓ bullets)
Structure A PASS does NOT mean:   (✗ bullets)
```

Must cover at least: identity, mass, material, size class, class↔prop; and exclude motors-fit, clearance, wheelbase, mounts, battery/FC fit, strength, fabricability, CAD.

4. **Is any claim-copy / UX honesty gap** still open *inside* Structure A (without Structure B)? e.g. should Continuity/estado footnote Structure PASS the way Control has `PASS *`? Recommend Yes/No/Lean — **no code**.
5. **What would be the minimum Structure B slice** that adds real mechanical meaning without CAD? Rank 0–2 candidates by value vs illusion risk; may recommend **zero** (defer).
6. **What must stay out** even if Structure B opens later?
7. **How does this interact with ASSEMBLY READY** and the weak-OP / Control-declaration signals from the walk — keep frontiers distinct.
8. **Buy recommendation:** (a) ★ meaning-only / doc+claim-copy later, (b) thin Structure A honesty IC, (c) Structure B investigation/IC, (d) defer all — pick one lean with rationale.

---

## 4. Code / doc seams to inspect (non-exhaustive)

- `engineering_readiness.py` — `_structure_evidence`, `_derive_subsystem_verdict`, `_frame_class_gaps`
- `project_closure.py` — `frame_class_compatibility_state`, claim-copy BOM frame tails
- `project_continuity.py` — situation when Structure gaps present / absent
- Catalog Foundation artifacts (IC-1/2/3 reviews) — closed scope
- Engineer CLI walk transcript (2026-09-04) — ASSEMBLY READY + Structure PASS + weak prop evidence

---

## 5. Deliverable shape

1. Executive finding (what PASS means; Structure B now? Y/N/lean).  
2. Code-backed “today” matrix.  
3. Locked ✓ / ✗ meaning table for Engineer ★.  
4. Optional honesty gap inside A (claim-copy footnote?) — lean only.  
5. Minimum B candidates or explicit defer.  
6. Out list.  
7. Open questions for Engineer ★.  
8. No authoritative IC file lists; thin non-binding outline only if Buy lean ≠ defer.

---

## 6. Forbidden in this investigation

- Implementing Structure B fields, layout, CAD, FEA  
- Widening `_derive_subsystem_verdict` / Structure PASS criteria in code  
- Reopening Catalog Foundation ICs  
- Inventing structural ratings or fit claims  
- Weakening or deleting tests  

---

## 7. Engineer gate

**Do not write the investigation report until Engineer `procede` on this contract.**  
If no → edit this contract in place.
