# Investigation Review — Structure A (masa + compatibilidad de clase)

**Date:** 2026-09-03  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_a.md](investigation_contract_structure_a.md)  
**Report:** [investigation_report_structure_a.md](investigation_report_structure_a.md)  
**Physics lock (Engineer, 2026-09-03):** class screening LEVEL A, not geometric fit  
**Seed notes (not proof):** [engineer_notes_structure_a.md](engineer_notes_structure_a.md)  
**Base:** tag `v0.3.5` / `checkpoint-phase25-hover-energy` · commit `fc46938` (live tree + DSE apply honesto, as the report discloses)

## Verdict

**PASS WITH NOTES**

Seams are sufficient for shape **B**. The report does **not** pick A, does **not** recommend HIGH, and does **not** edit `_derive_overall`. No extra Engineer ★ is required on the ASSEMBLY_READY gate.

The Engineer physics evaluation is absorbed here before the IC:

```text
D = physical propeller diameter
size_class_inch = declared architectural class (not diagonal, not clearance)
D <= class → CLASS COMPATIBILITY PASS — LEVEL A / CLASS-BASED
D > class  → CLASS COMPATIBILITY GAP — Structure INCOMPLETE
             (class convention exceeded; physical impossibility NOT demonstrated)
```

Report seams (masa leak, dual `_block_progress_status`, MEDIUM already rolls up) stay. Report **language** that treats `D <= class` as FIT PASS / “does not fit” / misfit **does not**.

**Ready for Implementation Contract.** Engineer `ratifico` on that IC → Claude implements. Do not implement from this review or from the old draft.

---

## Contract checklist

| Criterion | Result |
|---|---|
| §1 locked product model (unidirectional \(D\), class required when \(D\) known, LEVEL A) | **Pass** — report does not reopen OP vs \(D^4\); invasion check is file:line |
| §3.1 masa paths | **Pass** — walk leak is session extractor, not only `apply_material_definition` |
| §3.2 completeness / 4/4 / ERF dual | **Pass** — architecture progress ignores `_frame_completeness`; helper is mandatory |
| §3.3 invasion / `GAP-PROP-MOTOR-MISMATCH` | **Pass** — motor↔prop HIGH; CalculationEngine never reads frame class |
| §3.4 gap + Gate §1 | **Pass** — MEDIUM + structure incomplete already → `NOT_ASSEMBLY_READY`; no HIGH |
| §3.5 extractors / mm | **Pass with Note 5** — grams vs inches not fully regex-probed; IC still forbids mm→class |
| §4 shape B/A/C/D | **Pass** — **B** for seam cohesion, matching Engineer physics default |
| §6 draft keep/change/drop vs CLASS COMPATIBILITY | **Pass with Notes 1–3** — report §6 “keep FIT PASS verbatim” is **superseded** |
| Frozen / no `src/` | **Pass** |
| C1–C5 style (no CAD, no class→thrust, no invent density) | **Pass** |

---

## Independent verification (spot-check)

| Claim | Cursor check |
|---|---|
| `_extract_material_from_text` at `:295` and `:412` | **Confirmed** — `iterate_interactive_session.py:295,412`; helper `:1266-1273` returns canonical name only |
| `apply_material_definition` writes material string only | **Confirmed** — `mutation_engine.py:158-172` |
| DEFINE dispatch hits material before `component_patch` | **Confirmed** — `mutation_engine.py:66-70` |
| `_run_declarative_iteration` never calls `_apply_mutation_to_parameters` | **Confirmed** — `actions/iterate.py:296-313` applies design_properties; writers only for catalog-bound motor/battery |
| Dual `_block_progress_status` is stub-vs-present only | **Confirmed** — `orchestrator.py` (component branch) and `engineering_readiness.py:410-422`; `component_presence_tier` treats `medium` as present (`project_closure.py:223-238`) |
| `_derive_overall` HIGH fast-path + any non-PASS subsystem | **Confirmed** — `engineering_readiness.py:1122-1134` |
| Blocking gap → subsystem not PASS | **Confirmed** — `_derive_subsystem_verdict` `:1082-1119`; MEDIUM with `blocks=["structure"]` → structure `INCOMPLETE` |
| `GAP-ARCH-BLOCK-INCOMPLETE` when architecture not complete | **Confirmed** — `:526-564` / `:551-552` |
| `GAP-PROP-MOTOR-MISMATCH` is catalog pairing, HIGH | **Confirmed** — `:856-877`, `blocks=["propulsion","catalog"]` |
| CalculationEngine thrust order: bound thrust then \(D^4\) | **Confirmed** — `calculation_engine.py:238-291`; no frame field |
| `set_propeller_component` bridges `diameter_in` → param | **Confirmed** — `component_writers.py:446-465` |
| `COMPONENT_PROMPTS["frame"]` is mass+material only | **Confirmed** — `acquisition_target.py:117` |
| `tests/test_fase2_uxc.py` | **Confirmed absent** — drop from IC |
| PVC library density | **Not re-run** — accept report read of `1380.0`; IC must not invent density and must not expect a “PVC has no physics” honesty string |

---

## Physics lock vs report (the evaluation the Engineer asked for)

The contract architecture is physically valid for Structure A. **B is the correct first IC.** Nothing in the seams justifies A, C, or D.

What the IC must **not** copy from the report:

| Report text | Engineer lock |
|---|---|
| §6 “Keep verbatim” FIT PASS / misfit table | **Drop the words.** Keep the **states**. \(D \le\) class = CLASS COMPATIBILITY PASS. \(D >\) class = CLASS COMPATIBILITY GAP. |
| Suggested `Gap.title` `"Propeller does not fit frame size class"` | **Forbidden.** That is “cabe” in English. Use class-exceeded / class-missing titles. |
| Helper returning `fit` / `misfit` | Rename: `not_required` / `missing` / `class_compatible` / `class_incompatible` |
| `GAP-FRAME-PROP-SIZE` `blocks=["structure","catalog"]` | **Change:** `blocks=["structure"]` only. Catalog pairing is a different question (`GAP-PROP-MOTOR-MISMATCH`). Class screening must not make the catalog subsystem look broken. |
| Adding the new type to `_INCOMPATIBLE_CLASS_GAP_TYPES` | **Forbidden.** That ERF verdict means demonstrated conflict (ESC, discharge, motor↔prop). Class screening is LEVEL A incomplete, not INCOMPATIBLE. |

What the report got right and the IC keeps:

- Declared grams → `0.2 kg` is legitimate; do not invent PVC density/volume.
- `size_class_inch` never enters thrust / power / RPM / \(C_T\) / autonomy.
- Conservatism: unknown class or class exceeded → Structure incomplete, not silent PASS.
- No `+0.25"`. No mm→class.
- Dedicated gap types are for **honest copy**, not because the rollup needs HIGH.
- Continuity carries the long Spanish sentences; `Gap.title` stays short.

---

## Notes (non-blocking — IC must absorb)

### Note 1 — CLASS COMPATIBILITY, not FIT PASS

Report §2.2 / §6 “keep verbatim” was written against an earlier draft. Engineer physics (2026-09-03) supersedes it. CLI may say “compatible de clase (nivel A)”. Never `STRUCTURAL FIT: VERIFIED`, never “la hélice cabe”, never “misfit geométrico demostrado”.

### Note 2 — Gap titles must not say “fit”

Convention of short English `Gap.title` is correct. The example title in report §5 is not. Locked titles are in the IC.

### Note 3 — Do not block `catalog`

A 7" prop on a declared 5" class is a **structure** class-convention gap. Motor↔prop catalog pairing can still be valid. `blocks=["structure"]`.

### Note 4 — One `prop_diameter_in` predicate

Contract §3.2 asked for one predicate covering param, component property, and bound SKU. Report §4 named the param key and noted the engine already uses it; it did not name the helper. IC locks:

```text
components["propellers"].properties["diameter_in"]
  else current_parameters["propeller_diameter_in"]
  else bound propeller catalog_ref → library.get_propeller(sku).diameter_in
```

Do not parse a class out of millimetres. Do not copy class from \(D\).

### Note 5 — Grams vs `5"`

`extract_frame_properties` grams regex is `\b(\d+)\s*g\b` (`aerial.py:222`). `5"` and `5 in` should not match grams. IC still requires a regression that `"pvc 200g"` does not invent `size_class_inch`, and `"frame 5 pulgadas"` does not invent mass.

### Note 6 — PVC density

Honesty-message test is **not** “PVC lacks density”. Material-only `"pvc"` may follow today’s density-ratio path if reached; the walk bug is **discarded grams**, not missing library data. Do not invent mass when grams are absent.

### Note 7 — Files the draft omitted

Keep report §7 file list: `iterate_interactive_session.py`, `actions/iterate.py`, `project_closure.py`, `project_continuity.py`, both `_block_progress_status` copies, `acquisition_target.py` `COMPONENT_PROMPTS` (conditional pulgadas when \(D\) known). `mutation_engine.py` is not the primary leak.

---

## Shape / Gate

| Question | Answer |
|---|---|
| B vs A? | **B.** Physics does not split. Seams share writer + both progress copies. |
| HIGH / `_derive_overall`? | **No.** Structure incomplete already yields `NOT_ASSEMBLY_READY`. |
| Extra Engineer ★? | **No.** Report picked B and closed the gate. |

---

## Next

Cursor writes [implementation_contract_structure_a.md](implementation_contract_structure_a.md) from this review + the physics lock. That file is the work order **after** Engineer `ratifico`. Claude does not implement from the investigation report.
