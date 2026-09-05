# Implementation Review — IDLE frame rebind (B2)

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_idle_frame_rebind_b2.md](implementation_contract_idle_frame_rebind_b2.md)  
**Report:** [implementation_report_idle_frame_rebind_b2.md](implementation_report_idle_frame_rebind_b2.md)  
**★:** [engineer_ratification_idle_component_reacquisition.md](engineer_ratification_idle_component_reacquisition.md)  
**Baseline:** Structure CLOSED @ 2229 · suite claimed **2250**

## Verdict

**PASS WITH NOTES**

B2 delivered as locked: sibling IDLE dispatch before bare help-choose, reuse of
IC-3 offer/apply, clear-all `parent_key=="frame"` children before upsert.
Scope clean (no B3, no name→SKU, no coherence Continuity, FN-014 not widened).

Ready for optional Engineer CLI smoke (`cambiar frame` → pick).

---

## Checklist

| Criterion | Result |
|---|---|
| `is_frame_rebind_phrase` requires noun + verb/help-choose | **Pass** — word-boundary `frame\|chasis`; bare help-choose False |
| IDLE dispatch before FN-005 | **Pass** — `orchestrator.py` ~904–927 then bare help-choose |
| Session shape DEFINE_MISSING + `["frame"]` | **Pass** — matches IC §3.2 |
| Direct `_offer_component_frame_catalog` (bypass `_wants_catalog_help`) | **Pass** |
| `clear_frame_part_children` then upsert on pick | **Pass** — `component_writers.py` + apply path |
| T1–T7 coverage | **Pass** — `tests/test_idle_frame_rebind_b2.py` |
| No Structure PASS / ERF edits | **Pass** — `engineering_readiness.py` not in this IC diff |
| FN-014 / other families untouched | **Pass** — report + code read |
| Full suite | **Pass** — Cursor re-ran targeted **21**; full suite **2250** (implementer) / reconfirm below |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest tests/test_idle_frame_rebind_b2.py -q` | **21 passed** |
| `pytest -q` full | **2250 passed** (Cursor reconfirm) |
| Detector true: locked phrases + chasis variants | **Pass** (parametrized) |
| Detector false: bare help-choose, batería/motores, estructura, material | **Pass** |
| T5 Armattan→TBS clears all `frame_*` | **Pass** — asserts `remaining == []` |
| T3 frame list without motor_suggestions | **Pass** |
| Continuity dirty-tree claim-hygiene hunk | **Unrelated** — pre-existing uncommitted Structure/claim-hygiene work; not B2 |

---

## Notes

### N1 — T6 assertion is soft on motor identity

`test_bare_ayudame_a_elegir_still_opens_motor_assist_not_frame` correctly
forbids `frame_suggestions`, but accepts any interactive result whose message
contains `"motor"` **or** mere `status==interactive`. Enough for this IC’s
regression gate (must not open frame). Optional harden later: assert
`motor_suggestions` non-empty when underspec fixture holds — **not** blocking.

### N2 — Free-text orphan half remains debt

Catalog re-pick clears children; free-text root rewrite still does not
(IC §3.5 / §6). Correct deferral — do not open a cleanup IC from this review.

### N3 — Optional DEFINE_MISSING bound help-choose polish skipped

IC §3.3 allowed optional in-wizard offer when `catalog_ref` already set.
Implementer correctly stayed on IDLE-only direct offer — minimum slice met.

---

## Engineer next

Optional smoke on ASSEMBLY READY project:

```text
cambiar frame
<pick Armattan or TBS>
estado
```

Expect numbered list; TBS → no `└`; Armattan → `└` parts + `[sku]`.
