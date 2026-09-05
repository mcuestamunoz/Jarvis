# Investigation Review — Structure B Physical Frame Model

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_b_physical_frame_model.md](investigation_contract_structure_b_physical_frame_model.md)  
**Report:** [investigation_report_structure_b_physical_frame_model.md](investigation_report_structure_b_physical_frame_model.md)  
**★ mandate:** [engineer_ratification_structure_b_physical_frame_model.md](engineer_ratification_structure_b_physical_frame_model.md)  
**Parent:** [investigation_report_structure_a_pass_meaning.md](investigation_report_structure_a_pass_meaning.md)

## Verdict

**PASS WITH NOTES**

Claude delivered a coherent **minimum KNOW+CLAIM model** that respects the
codebase (flat `ComponentSpec.properties`, no parts graph) and the locked
Structure A PASS ✓/✗ wall. Fase 1 = three optional declared scalars
(`configuration`, `arm_count`, `wheelbase_mm`) with **zero** Structure PASS
impact. Buy lean **(b)** honesty IC first, then separate model IC — sound
sequencing.

Ready for Engineer ★ on model + sequencing (not for silent implementation).

---

## Checklist

| Criterion | Result |
|---|---|
| KNOW/CLAIM/MEASURE matrix | **Pass** |
| Ontology (assembly vs parts; mass) | **Pass** — one frame spec; declared mass; no nesting |
| arm_count vs motor_count | **Pass** — forbid cross-check (resolves prior hazard) |
| Allowed/forbidden claim sentences | **Pass** — mapped to prior ✗ table |
| Structure PASS unchanged | **Pass** — confirmed vs `_structure_evidence` / `_frame_completeness` |
| Catalog implications (read-only) | **Pass** |
| Fase 1 + out | **Pass** — plates/standoffs deferred |
| Buy lean | **Pass** — (b) honesty then model |
| No code | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `ComponentSpec.properties` flat `dict[str, PropertyValue]` | **Confirmed** — `action_schema.py` |
| Motors use scalar `motor_count`, not N records | **Confirmed** — `aerial.py` extract |
| `_frame_completeness` = mass + material only | **Confirmed** — `aerial.py:262+` |
| `_structure_evidence` ignores new fields | **Confirmed** — no path to read them |
| `PropertyValue.source` three-state | **Confirmed** |
| Wheelbase **in** `library/frames/_datos.json` today | **Absent** — report claims sourcing *notes* from IC-1 pages, not seed rows (OK if read as groundwork, not “already seeded”) |

---

## Notes

### N1 — Engineer's “assembly of parts” narrowed to scalars

Contract asked ontology including “brazo as component?”. Claude’s answer
**No** (no nesting precedent) is correct for *minimum* Fase 1 and matches
motor_count precedent. Plates/standoffs/hardware stay out of Fase 1.

This is **not** the full “frame → arms → plates” tree you sketched — it is
the smallest honest enrichment of the *same* frame box. Engineer ★ must
accept that narrowing or explicitly demand a parts-graph (larger than
minimum, new subsystem risk).

### N2 — Write-only fields (same class as prior “layout params” critique)

Fase 1 fields have **no consumer** (display/BOM only). Value is mental-map /
identity richness — same category Claude once ranked low for B candidates.
Acceptable **if** Engineer wants KNOW asymmetry fixed without MEASURE; do
not sell as mechanical capability leap.

### N3 — Wheelbase sourcing vs seed

Report’s mm figures are investigator notes from IC-1 source pages, **not**
in seed JSON today. Future seed-enrichment IC still required to land them.

### N4 — Honesty IC vs model IC

Agree: ship `Structure PASS *` first (prior investigation), then model IC.
Different concerns; do not bundle.

---

## Next

Engineer ★:

1. Accept Fase 1 = 3 scalars (not parts graph)?  
2. Honesty IC before model IC?  
3. `configuration` vocabulary lock?  
4. Wheelbase seed later? Plates as named Fase 2 or drop?

Then Cursor drafts IC(s) only after ★ / `procede`.
