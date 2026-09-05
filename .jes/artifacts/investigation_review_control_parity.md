# Investigation Review — Control parity

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_control_parity.md](investigation_contract_control_parity.md)  
**Report:** [investigation_report_control_parity.md](investigation_report_control_parity.md)  
**Base:** `v0.3.6` + claim hygiene live · suite **2160**

## Verdict

**PASS WITH NOTES**

Buy **B1** accepted. B2 correctly rejected as silent B3 (control could never
PASS → every ASSEMBLY_READY drone flips). Catalog not Buy.

**IC:** [implementation_contract_control_parity.md](implementation_contract_control_parity.md)  
Engineer ratifies by `procede` on that IC (no separate ratification artifact).

---

## Checklist

| Criterion | Result |
|---|---|
| Hypothesis + no control physics | **Pass** — writers docstring + zero calc/sim hits |
| Sensors unused by `_control_evidence` | **Pass** — only `flight_controller` for `defined` |
| Sensors never `"high"` / BOM ◇ honest | **Pass** |
| Cheapest over-claim `"pixhawk"`+`"gps"` | **Pass** — presence tier, not measurable |
| B1 vs B2/B3 analysis | **Pass** — B2 = permanent UNVERIFIABLE → NOT_ASSEMBLY_READY |
| No `src/` | **Pass** |

## Notes for IC

1. **B1 scope = CLI readiness + BOM FC line** — Continuity does not name control today; do not invent Continuity control copy in this IC.
2. **Arquitectura 4/4 counter unchanged** — copy honesty on Control PASS + BOM ✓ is enough for smallest slice.
3. **Locked strings live in the IC** — Engineer `procede` locks them; no parallel ★ doc.
4. **B2/ASSEMBLY_READY gate** remains a future Engineer decision, not this IC.
