# Investigation Review — Structure Foundations

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_foundations.md](investigation_contract_structure_foundations.md)  
**Report:** [investigation_report_structure_foundations.md](investigation_report_structure_foundations.md)  
**★:** [engineer_ratification_structure_foundations.md](engineer_ratification_structure_foundations.md)  
**Base:** `v0.3.6` + claim hygiene + control parity · suite **2164**

## Verdict

**PASS WITH NOTES**

Primary Buy **claim/completeness copy** accepted. Structure A **not** reopened.
Catalog / layout / CAD correctly deferred or rejected.

**IC:** [implementation_contract_structure_foundations.md](implementation_contract_structure_foundations.md)  
Engineer ratifies with `procede` on that IC (no separate Buy ★ file).

---

## Checklist

| Criterion | Result |
|---|---|
| Structure A kept / no CAD | **Pass** |
| Vocabulary / CatalogRef.family | **Pass** — `"frame"` absent from Literal |
| `_frame_completeness` ignores class | **Pass** — `aerial.py:262-281` |
| Dual `_block_progress_status` / in-progress | **Pass** — shared helper; structure uses `frame_next_missing_question` |
| BOM ✓ vs GAP-FRAME live | **Pass** — reviewer reproduced |
| Situation “Diseño validado” vs class gap | **Pass with Note 1** |
| Buy claim-copy vs catalog/layout | **Pass** — catalog/layout not primary |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| BOM `✓ frame … (high)` with no `size_class_inch` + D known | **Confirmed** — `format_bom_lines` shows `(high)` while ERF has `GAP-FRAME-SIZE-MISSING`, structure `INCOMPLETE` |
| Architecture gated | **Confirmed** — `derive_architecture_progress` → `0/1` / pendiente Estructura |
| Live Continuity with real arch fields | **Confirmed** — situation = `Arquitectura 0/1: pendiente Estructura.` (honest); next-step names class |
| Continuity “Diseño validado” + class next-step | **Only when** `architecture_progress` is `None` or falsely complete — **not** the normal `build_startup_context` path |

---

## Notes

### N1 — Finding 2 scope (absorb in IC)

The report’s Continuity self-contradiction is **real for callers that omit
architecture progress**, but **not** the common CLI `estado` path: with live
arch progress, situation already says architecture pending while next-step
names the class gap (coherent, if less specific).

IC: **BOM suffix is the primary user-visible fix.** Continuity situation gate
for frame-class gaps is still in scope as **cheap defense-in-depth** (same
pattern as `margin_claim_weak`) so PASS + readiness frame gaps never print
“Diseño validado” when arch progress is missing or wrong — not framed as the
main walk bug.

### N2 — Do not change `_frame_completeness`

Agree with report: keep `classify_component` / completeness formula; suffix
only. Changing completeness would re-open Structure A’s BOM contract.

### N3 — Catalog / layout

Agree: later options, not this IC.
