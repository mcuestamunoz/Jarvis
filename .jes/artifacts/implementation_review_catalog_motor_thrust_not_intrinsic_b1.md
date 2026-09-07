# Implementation Review — Motor Thrust Not Intrinsic B1 (OP Durability + Copy Hygiene)

**Date:** 2026-09-07  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md](implementation_contract_catalog_motor_thrust_not_intrinsic_b1.md)  
**Report:** [implementation_report_catalog_motor_thrust_not_intrinsic_b1.md](implementation_report_catalog_motor_thrust_not_intrinsic_b1.md)  
**Buy:** ★ B1 — N1 `calculated` · CLI honesty · BOM tail §3.4

## Verdict

**PASS**

IC locks held. OP-mirrored thrust is `source="calculated"`; regression proves **13.4841** survives resolve/apply; CLI markers and BOM tails are additive honesty; no schema/seed/`resolve_operating_point` ladder spill. Suite **2350** (implementer); Cursor reconfirmed the **6** new tests **passed**.

---

## Checklist

| Criterion | Result |
|---|---|
| N1: exact/fallback mirror → `source="calculated"` | **Pass** |
| Regression: 13.4841 survives `resolve_propulsion_parameters` + `apply_to` | **Pass** |
| Fallback also `calculated`; legacy stays `declared` | **Pass** |
| §3.2 ★5 prop re-resolve confirmed, no orchestrator change | **Pass** |
| CLI candidate/chosen honesty markers | **Pass** |
| §3.4 BOM tail localized (legacy/fallback only) | **Pass** |
| `10.042` pins: triage, zero retarget needed | **Pass** (credible) |
| No seeds / ui / ESC / FC / version | **Pass** (`git diff --stat`) |
| Full suite | **2350** reported |

---

## Independent verification

| Check | Result |
|---|---|
| Diff: `declared` → `calculated` only on OP mirror write | **Confirmed** |
| CLI suffix `(pico catálogo)` / refine-with-prop marker | **Confirmed** |
| BOM motors tails via `propulsion_resolution` JSON | **Confirmed** |
| 6 named new tests | **6 passed** |
| No `library/**` / `ui/**` / `library.py` ladder edits | **Confirmed** |

---

## Notes

### N1 — Chosen-line still says “pico catálogo” after exact OP

Accepted per IC §3.3 “or” / report residual: formatters lack `project_state`. Follow-on only if Engineer wants resolution-aware chosen copy.

### N2 — Freeform propeller re-resolve

Deferred honestly (§3.2); catalog ★5 path unchanged.

### N3 — Board card `thrust_n` field

After exact OP, Board may show the **resolved** number with `calculated` provenance via generic `_fields` — better than silent declared peak; still no prop/V annotation on the glyph/card. Out of B1 unless Engineer opens a Board-copy slice.

---

## Phase

Implementation **closed**. Catalog hygiene cola (ESC mass + motor thrust semantics) is done at B1. Next = Engineer focus (idle / Geometry assembly / other).
